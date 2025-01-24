import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Union, Sequence, Optional, Iterable

import requests
from sqlalchemy import select, Engine, func
from sqlalchemy.orm import Session

from card_auto_add.config import Config
from card_auto_add.data_signing import DataSigning
from card_auto_add.loops.comm_server_watcher import CommServerWatcher
from card_auto_add.windsx.db.acl_group_combo import AclGroupComboSet, AclGroupComboHelper
from card_auto_add.windsx.db.models import COMPANY, UdfName, UDF, NAMES, CARDS, LocCards, AclGrpCombo, AclGrp, LOC, \
    DGRP, ACL


class CardInfo(object):
    def __init__(self,
                 first_name,
                 last_name,
                 company,
                 woo_id,
                 card):
        self.first_name = first_name
        self.last_name = last_name
        self.company = company
        self.user_id = woo_id
        self.card = card


class WinDSXCardActivations(object):
    _date_never = datetime(9999, 12, 31)

    def __init__(self,
                 config: Config,
                 acs_engine: Engine,
                 comm_server_watcher: CommServerWatcher,
                 ):
        self._config: Config = config
        self._acs_engine: Engine = acs_engine
        self._session: Session = Session(acs_engine)
        self._acl_group_combo_helper: AclGroupComboHelper = AclGroupComboHelper(acs_engine,
                                                                                3)  # TODO Don't hardcode location id
        self._default_acl = config.windsx_acl
        self._log = config.logger
        self._slack_log = config.slack_logger
        self._data_signing = DataSigning(config.dsxpi_signing_secret)
        self._comm_server_watcher = comm_server_watcher

        self._loc_grp = 3  # TODO Look this up based on the name
        self._udf_name = "ID"  # TODO Look this up in config

    def activate(self, card_info: CardInfo):
        self._log.info(f"Activating card {card_info.card}")
        self._slack_log.info(f"Activating card {card_info.card} for {card_info.first_name} {card_info.last_name}")

        to_add_group_combo: AclGroupComboSet = self._acl_group_combo_helper.by_names(
            self._default_acl)  # TODO This shouldn't be hardcoded

        name_id = self._find_or_create_name(card_info)

        card_id, card_combo_id = self._get_card_combo_id(card_info.card)

        if card_id is None:
            # This should give us the card combo id with just our acl
            card_combo_id = to_add_group_combo.id
            card_id = self._create_card(name_id, card_info.card, card_combo_id)
        else:
            existing_group_combo: AclGroupComboSet = self._acl_group_combo_helper.by_id(card_combo_id)
            new_group_combo: AclGroupComboSet = existing_group_combo.with_names(to_add_group_combo.names)

            # We check the DB just in case the existing card combo id is 0 but the new group is different
            if not new_group_combo.in_db or card_combo_id != new_group_combo.id:
                self._log.info(f"Updating card combo id from {card_combo_id} to {new_group_combo.id}")
                new_group_combo.write()  # Make sure it's in the DB
                self._update_card_combo_id(card_id, new_group_combo.id)
                card_combo_id = new_group_combo.id

            self._set_card_active(card_id, name_id)

        acl_ids = self._find_or_create_acl_id(card_combo_id)
        self._log.info(f"Using ACL IDs: {acl_ids}")

        self._create_or_update_loc_cards(card_id, acl_ids)

        self._encourage_system_update()

        self._slack_log.info(f"Card {card_info.card} activated for {card_info.first_name} {card_info.last_name}")

    def deactivate(self, card_info: CardInfo):
        self._log.info(f"Deactivating card {card_info.card}")
        self._slack_log.info(f"Deactivating card {card_info.card} for {card_info.first_name} {card_info.last_name}")

        card_id, _ = self._get_card_combo_id(card_info.card)

        if card_id is None:
            self._log.info(f"Card id not found for {card_info.card}, so it's safe to assume it never was activated")
            return

        self._set_card_inactive(card_id)

        self._encourage_system_update()

        self._slack_log.info(f"Card {card_info.card} deactivated for {card_info.first_name} {card_info.last_name}")

    def _find_or_create_name(self, card_info: CardInfo):
        # First, let's try to find it via uuid5
        customer_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, str(card_info.user_id)))

        udf_num = self._session.execute(select(UdfName.UdfNum).where(UdfName.Name == self._udf_name)).scalar()

        if udf_num is None:
            raise ValueError(f"Failed to find UDF Name ID {self._udf_name}")

        name_id = self._session.execute(
            select(UDF.NameID).where(UDF.UdfNum == udf_num).where(UDF.UdfText == customer_uuid)
        ).scalar()

        if name_id is not None:
            self._log.info(f"Found name id {name_id} based on customer id {card_info.user_id}")
            return name_id

        company_id = self._session.execute(select(COMPANY.Company).where(COMPANY.Name == card_info.company)).scalar()

        if company_id is None:
            raise ValueError(f"No company found for company name '{card_info.company}'")

        name_id = self._session.execute(
            select(NAMES.ID) \
                .where(NAMES.FName == card_info.first_name)
                .where(NAMES.LName == card_info.last_name)
                .where(NAMES.Company == company_id)
        ).scalar()

        if name_id is not None:
            self._log.info(f"Found name id {name_id} based on customer's first/last name and company")
            # We couldn't look it up via UUID for some reason, so make sure to update it so we can next time
            self._create_or_update_udf_text(udf_num, name_id, customer_uuid)
            return name_id

        self._log.info(f"No name ID found for customer {card_info.user_id}, will make one")

        new_name = NAMES(
            LocGrp=self._loc_grp,
            FName=card_info.first_name,
            LName=card_info.last_name,
            Company=company_id
        )
        self._session.add(new_name)
        self._session.commit()
        name_id = new_name.ID

        if name_id is None:
            raise ValueError("Didn't get name ID on insert")

        self._create_or_update_udf_text(udf_num, name_id, customer_uuid)

        return name_id

    def _create_or_update_udf_text(self, udf_num, name_id: int, customer_uuid):
        udf: UDF = self._session.execute(
            select(UDF).where(UDF.NameID == name_id).where(UDF.UdfNum == udf_num)
        ).scalar()

        if udf is not None:
            udf.UdfText = customer_uuid
        else:
            udf = UDF(
                LocGrp=self._loc_grp,
                NameID=name_id,
                UdfNum=udf_num,
                UdfText=customer_uuid
            )
            self._session.add(udf)

        self._session.commit()

    def _get_card_combo_id(self, card_num: Union[str, int]):
        if not isinstance(card_num, str):
            card_num = str(card_num)

        card = self._session.execute(select(CARDS).where(CARDS.Code == card_num.lstrip('0'))).scalar()

        if card is None:
            self._log.info(f"No existing card was found for card {card_num}")
            return None, None
        else:
            card_id = card.ID
            card_combo_id = card.AclGrpComboID
            self._log.info(f"Found card id {card_id} and combo id {card_combo_id} for card {card_num}")

            return card_id, card_combo_id

    def _create_card(self, name_id, card_num, card_combo_id):
        # This function assumes that you're creating a card to be activated, so it sets the start/stop date and status
        # accordingly.

        now = datetime.now()
        card = CARDS(
            NameID=name_id,
            LocGrp=self._loc_grp,
            Code=card_num.lstrip('0'),
            StartDate=now,
            StopDate=self._date_never,
            Status=True,
            CardNum=card_num,
            DlFlag=0,
            AclGrpComboID=card_combo_id
        )
        self._session.add(card)

        card_id = card.ID
        if card_id is None:
            raise ValueError(f"Card ID could not be retrieved on created card for card {card_num}")

        self._log.info(f"Created card with card id {card_id}")

        return card_id

    def _update_card_combo_id(self, card_id, new_card_combo_id):
        card = self._session.execute(select(CARDS).where(CARDS.ID == card_id)).scalar()
        card.AclGrpComboID = new_card_combo_id
        self._session.add(card)
        self._session.commit()

    def _set_card_active(self, card_id, name_id):
        card = self._session.execute(select(CARDS).where(CARDS.ID == card_id)).scalar()
        card.NameID = name_id
        card.StartDate = datetime.now()
        card.StopDate = self._date_never
        card.Status = True
        self._session.add(card)
        self._session.commit()

    def _set_card_inactive(self, card_id):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        card = self._session.execute(select(CARDS).where(CARDS.ID == card_id)).scalar()
        card.StopDate = today
        card.Status = False
        self._session.add(card)

        loc_card = self._session.execute(select(LocCards).where(LocCards.CardID == card_id)).scalar()
        loc_card.DlFlag = 1
        loc_card.CkSum = 0
        self._session.add(loc_card)

        self._session.commit()

    def _find_or_create_acl_id(self, card_combo_id):
        query = select(AclGrp) \
            .join(AclGrpCombo, AclGrp.AclGrpNameID == AclGrpCombo.AclGrpNameID) \
            .where(AclGrpCombo.ComboID == card_combo_id)
        device_access: list[AclGrp] = [row[0] for row in self._session.execute(query).fetchall()]

        tz_to_dev_list = defaultdict(lambda: set())
        for access in device_access:
            if access.Tz1 != 0:
                tz_to_dev_list[access.Tz1].add(access.Dev)
            if access.Tz2 != 0:
                tz_to_dev_list[access.Tz2].add(access.Dev)
            if access.Tz3 != 0:
                tz_to_dev_list[access.Tz3].add(access.Dev)
            if access.Tz4 != 0:
                tz_to_dev_list[access.Tz4].add(access.Dev)
        tz_to_device_group: dict[int, int] = {}
        for tz, dev_list in tz_to_dev_list.items():
            tz_to_device_group[tz] = self._find_or_create_matching_device_group(dev_list)

        acls = set()
        for tz, device_group in tz_to_device_group.items():
            acl: ACL = self._find_or_create_matching_acl(tz, device_group)
            acls.add(acl.Acl)

        return acls

    def _find_or_create_matching_device_group(self, dev_list):
        device_groups: Sequence[DGRP] = self._session.scalars(select(DGRP)).all()

        for group in device_groups:
            valid_group = True
            for dev in range(128):
                device_on = dev in dev_list  # Do we need this device
                group_device_on = getattr(group, f"D{dev}")  # Is this device set to true

                if device_on != group_device_on:  # Those values must match for a valid group
                    valid_group = False
                    break

            if valid_group:
                self._log.info(f"Found a valid device group {group.DGrp}")
                return group.DGrp

        self._log.info("No valid device group found, creating one")

        # Grab the next one by whatever the highest one is plus one.
        new_device_group_num = max([int(x.DGrp) for x in device_groups if float.is_integer(x.DGrp)]) + 1

        new_device_group = DGRP(
            DGrp=new_device_group_num,
            DlFlag=1,
            CkSum=0,
        )

        for dev in range(128):
            setattr(new_device_group, f"D{dev}", dev in dev_list)

        self._session.add(new_device_group)
        self._session.commit()

        return new_device_group_num

    def _find_or_create_matching_acl(self, tz: int, device_group: int) -> ACL:
        acl: Optional[ACL] = self._session.scalar(select(ACL).where(ACL.Tz == tz).where(ACL.DGrp == device_group))

        if acl is not None:
            return acl

        self._log.info(f"Acl not found for Tz {tz} and device group {device_group}, creating one")

        new_acl_id = self._session.scalar(select(func.max(ACL.Acl))) + 1  # Grab the next one

        acl = ACL(
            Loc=self._loc_grp,  # TODO Technically the group isn't the location. They're the same for my system.
            Acl=new_acl_id,
            Tz=tz,
            DGrp=device_group,
            DlFlag=1,
            CkSum=0,
        )
        self._session.add(acl)
        self._session.commit()

        return acl

    def _create_or_update_loc_cards(self, card_id: int, acl_ids: Iterable[int]):
        loc_card: Optional[LocCards] = self._session.scalar(
            select(LocCards)
            .where(LocCards.CardID == card_id)
            .where(LocCards.Loc == self._loc_grp)  # TODO loc_grp vs loc
        )

        acl_ids: list = list(acl_ids)

        acl = acl1 = acl2 = acl3 = acl4 = -1
        if acl_ids:
            acl = acl_ids.pop()
        if acl_ids:
            acl1 = acl_ids.pop()
        if acl_ids:
            acl2 = acl_ids.pop()
        if acl_ids:
            acl3 = acl_ids.pop()
        if acl_ids:
            acl4 = acl_ids.pop()

        if loc_card is None:
            self._log.info("LocCard not found, creating one")
            loc_card = LocCards(
                Loc=self._loc_grp,  # TODO loc_grp vs loc
                CardID=card_id,
            )
        else:
            self._log.info(f"Found LocCard id {loc_card.ID}, updating ACLs")

        loc_card.Acl = acl
        loc_card.Acl1 = acl1
        loc_card.Acl2 = acl2
        loc_card.Acl3 = acl3
        loc_card.Acl4 = acl4
        loc_card.DlFlag = 1
        loc_card.CkSum = 0

        self._session.add(loc_card)
        self._session.commit()

    def _encourage_system_update(self):
        locations = self._session.scalars(select(LOC).where(LOC.LocGrp == self._loc_grp)).all()
        for location in locations:
            location.PlFlag = True
            location.DlFlag = 1
            location.FullDlFlag = True
            location.NodeCs = 0
            location.CodeCs = 0
            location.AclCs = 0
            location.DGrpCs = 0
            self._session.add(location)

        self._session.commit()

        self._log.info("Comm Server update requested")
        for j in range(5):  # We'll endure up to 5 attempts
            for i in range(18):  # We'll endure 18 * 10 == 180 seconds to wait for the update before resetting
                downloading = self._session.scalar(select(LOC.PlFlag))

                if not downloading:
                    self._log.info("Looks like everything updated!")
                    return

                self._log.info("Update doesn't look like it's gone through yet, waiting 10 seconds")
                time.sleep(10)

            self._log.info("Update timed out")
            self._slack_log.info("Card update timed out, will attempt to reset and try again.")
            self._reset_card_access_hardware()

            self._comm_server_watcher.restart_comm_server()

        self._log.info("Card update failed after too many attempts")
        self._slack_log.info("Card update failed after too many attempts")

        raise Exception("Comm Server update timed out")

    def _reset_card_access_hardware(self):
        signed_payload = self._data_signing.encode(10)
        url = f"{self._config.dsxpi_host}/reset/{signed_payload}"
        response = requests.post(url)

        self._slack_log.info(response.content.decode('ascii'))

        if not response.ok:
            self._slack_log.info("DSXPI hardware failed to restart")
        else:
            self._slack_log.info("DSXPI hardware looks like it restarted!")
