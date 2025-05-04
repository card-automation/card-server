from datetime import datetime, date
from typing import Optional, Union, Callable, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import CARDS, LOC, AclGrpName, AclGrpCombo, AclGrp, DGRP, ACL, LocCards
from card_automation_server.windsx.lookup.acl_group_combo import AclGroupComboSet
from card_automation_server.windsx.lookup.person import Person
from card_automation_server.windsx.lookup.utils import LookupInfo, DbModel


class InvalidPersonForAccessCard(Exception):
    pass


class AccessCardLookup:
    def __init__(self,
                 lookup_info: LookupInfo):
        self._lookup_info: LookupInfo = lookup_info

    def by_card_number(self, card_number: Union[int, str]):
        session = Session(self._lookup_info.acs_engine)

        # The DB engine might do this for us, but just to be on the safe side, we convert it to an integer with leading
        # 0's removed.
        if isinstance(card_number, str):
            card_number = card_number.lstrip('0')

        valid_cards = session.scalars(
            select(CARDS)
            .where(CARDS.Code == card_number)
            .where(CARDS.LocGrp == self._lookup_info.location_group_id)
        ).all()

        if len(valid_cards) == 0:
            access_card = AccessCard(self._lookup_info, 0)
            access_card.card_number = card_number
            return access_card

        card: CARDS = valid_cards[0]
        return AccessCard(self._lookup_info, card.ID)


class AccessCard(DbModel):
    active_stop_date = datetime(year=9999, month=12, day=31)  # If we're setting a card to active, this is the stop date

    def __init__(self,
                 lookup_info: LookupInfo,
                 card_id: int
                 ):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = self._lookup_info.location_group_id
        self._session = Session(self._lookup_info.acs_engine)
        self._card_id: int = card_id
        self._card_number: Optional[int] = None
        self._name_id: Optional[int] = None
        self._active: Optional[bool] = None
        self._acl_group_combo: AclGroupComboSet = AclGroupComboSet(self._lookup_info, 0)
        super().__init__()

    @property
    def id(self) -> int:
        return self._card_id

    @property
    def card_number(self) -> int:
        return self._card_number

    @card_number.setter
    def card_number(self, value: Union[str, int]) -> None:
        self._card_number = value

    @property
    def active(self) -> bool:
        return self._active

    @property
    def person(self) -> Person:
        return Person(self._lookup_info, self._name_id)

    @person.setter
    def person(self, value: Union[Person, int]):
        if isinstance(value, Person):
            value = value.id

        self._name_id = value

    @property
    def access(self) -> frozenset[str]:
        return self._acl_group_combo.names

    def with_access(self, *names) -> 'AccessCard':
        self._acl_group_combo = self._acl_group_combo.with_names(*names)

        if len(self._acl_group_combo.names) > 0:
            self._active = True

        return self

    def without_access(self, *names) -> 'AccessCard':
        self._acl_group_combo = self._acl_group_combo.without_names(*names)

        if len(self._acl_group_combo.names) == 0:
            self._active = False

        return self

    def _get_card_from_db(self) -> Optional[CARDS]:
        return self._session.scalar(
            select(CARDS)
            .where(CARDS.ID == self._card_id)
            .where(CARDS.LocGrp == self._location_group_id)
        )

    def _populate_from_db(self):
        if self._card_id == 0:
            # Card number isn't set here as the only reason to look up a card id of 0 is to make a new card. We want to
            # let the consumer of this API set the card number, so we don't set it here.
            self._name_id = 0
            self._active = False
            self._in_db = False
            return

        card: CARDS = self._get_card_from_db()

        if card is None:
            # We shouldn't see this unless someone directly made an access card using a card id directly. Possible, but
            # not the advised route. Still, it doesn't hurt to explicitly protect from this mistake.
            self._name_id = 0
            self._active = False
            self._in_db = False
            return

        self._card_number = int(card.Code)
        self._name_id = card.NameID
        self._active = card.Status
        self._acl_group_combo = AclGroupComboSet(self._lookup_info, card.AclGrpComboID)
        self._in_db = True

    def write(self):
        if self._name_id == 0:
            raise InvalidPersonForAccessCard("The person must be set for an access card")

        if not self.person.in_db:
            raise InvalidPersonForAccessCard("The person for this card was not found")

        self._acl_group_combo.write()

        today = datetime.combine(date.today(), datetime.min.time())

        card: CARDS = self._get_card_from_db()
        if card is None:
            card = CARDS(
                LocGrp=self._location_group_id,
                Code=self._card_number,
                CardNum=str(self._card_number),
                StartDate=today,
            )

        card.NameID = self._name_id
        card.AclGrpComboID = self._acl_group_combo.id
        is_active: bool = len(self._acl_group_combo.names) > 0
        card.Status = is_active

        card.StopDate = AccessCard.active_stop_date if is_active else today

        self._session.add(card)
        self._session.commit()
        self._card_id = card.ID

        # Creating this object does everything we need it to.
        _AccessControlListUpdater(
            self._location_group_id,
            self._card_id,
            self._acl_group_combo.id,
            self._session,
            self._lookup_info.updated_callback
        )

        self._in_db = True
        self._lookup_info.updated_callback(self)


class _AccessControlListUpdater:
    """
    Updating the ACL stuff requires a lot of the same variables repeatedly. Instead of making it one long function or
    making several functions that pass things from one function to another, I made this helper class. Creating this
    class ensures that everything is set up correctly. You don't need to access or do anything with the class after it's
    created. All functions that need to be called are called in the correct order in __init__.
    """

    def __init__(self,
                 location_group_id: int,
                 card_id: int,
                 acl_group_combo_id: int,
                 session: Session,
                 updated_callback: Callable[[Any], None]):
        self._location_group_id = location_group_id
        self._card_id = card_id
        self._acl_group_combo_id = acl_group_combo_id
        self._session = session
        self._update_callback = updated_callback

        self._location_ids_to_update: set[int] = set()

        self._locations: list[int] = self.__get_locations()
        self._acl_group_name_ids: list[int] = self.__get_acl_group_name_ids()

        if len(self._acl_group_name_ids) == 0:
            self._deactivate_loc_cards()
            self.__update_locations()
            return

        update_to_master = any(self._session.scalars(
            select(AclGrpName.IsMaster)
            .where(AclGrpName.LocGrp == self._location_group_id)
            .where(AclGrpName.ID.in_(self._acl_group_name_ids))
        ).all())

        if update_to_master:
            self.__update_loc_cards_to_master()
            self.__update_locations()
            return

        self._acl_groups: list[AclGrp] = self.__get_acl_groups()
        # The next two dictionaries are {location_id -> {timezone -> X}}
        self._acl_groups_grouped: dict[int, dict[int, list[AclGrp]]] = self.__get_acl_groups_grouped()
        self._device_groups: dict[int, dict[int, DGRP]] = self.__get_device_groups()
        # This one is {location_id -> [ACL]}
        self._acls: dict[int, list[ACL]] = self.__get_acls()
        self._loc_cards: list[LocCards] = self.__get_loc_cards()

        self.__update_locations()

    def __get_acl_group_name_ids(self) -> list[int]:
        return list(self._session.scalars(
            select(AclGrpName.ID)
            .join(AclGrpCombo, AclGrpCombo.AclGrpNameID == AclGrpName.ID)
            .where(AclGrpName.LocGrp == self._location_group_id)
            .where(AclGrpCombo.LocGrp == self._location_group_id)
            .where(AclGrpCombo.ComboID == self._acl_group_combo_id)
        ).all())

    def __get_locations(self) -> list[int]:
        return list(self._session.scalars(
            select(LOC.Loc)
            .where(LOC.LocGrp == self._location_group_id)
        ).all())

    def __get_acl_groups(self) -> list[AclGrp]:
        return list(self._session.scalars(
            select(AclGrp)
            .where(AclGrp.Loc.in_(self._locations))
            .where(AclGrp.AclGrpNameID.in_(self._acl_group_name_ids))
        ).all())

    def __get_acl_groups_grouped(self) -> dict[int, dict[int, list[AclGrp]]]:
        result: dict[int, dict[int, list[AclGrp]]] = {}

        for acl_group in self._acl_groups:
            if acl_group.Loc not in result:
                result[acl_group.Loc] = {}

            timezones = [acl_group.Tz1, acl_group.Tz2, acl_group.Tz3, acl_group.Tz4]
            for tz in set(timezones):
                if tz is None or tz == 0:
                    continue

                if tz not in result[acl_group.Loc]:
                    result[acl_group.Loc][tz] = []

                result[acl_group.Loc][tz].append(acl_group)

        return result

    def __get_device_groups(self) -> dict[int, dict[int, DGRP]]:
        result: dict[int, dict[int, DGRP]] = {}
        acl_groups: list[AclGrp]
        for location_id, timezone_acl_groups in self._acl_groups_grouped.items():
            result[location_id] = {}
            for timezone, acl_groups in timezone_acl_groups.items():  # The timezone doesn't matter here
                devices = set(x.Dev for x in acl_groups)

                # We grab all the DGRP rows for this location. Trying to limit on the devices can cause an error in the
                # MDB database.
                device_groups = self._session.scalars(
                    select(DGRP)
                    .where(DGRP.Loc == location_id)
                ).all()

                device_group: Optional[DGRP] = None
                for group in device_groups:
                    mismatch = False

                    for i in range(128):
                        device_enabled: bool = getattr(group, f"D{i}")
                        if device_enabled != (i in devices):
                            mismatch = True
                            break

                    if not mismatch:
                        device_group = group
                        break

                if device_group is not None:
                    result[location_id][timezone] = device_group
                    continue

                new_device_group: DGRP = DGRP(
                    Loc=location_id,
                    DlFlag=1,
                    CkSum=0
                )

                for i in range(128):
                    setattr(new_device_group, f"D{i}", (i in devices))

                new_device_group.DGrp = self._session.scalar(select(func.max(DGRP.DGrp))) + 1  # Grab the next one
                self._session.add(new_device_group)
                self._session.commit()
                result[location_id][timezone] = new_device_group
                # We added a new DGrp, so update this location
                self._location_ids_to_update.add(location_id)

        return result

    def __get_acls(self) -> dict[int, list[ACL]]:
        result: dict[int, list[ACL]] = {}

        for location_id, timezone_device_groups in self._device_groups.items():
            result[location_id] = []
            for timezone, device_group in timezone_device_groups.items():
                acl: Optional[ACL] = self._session.scalar(
                    select(ACL)
                    .where(ACL.Loc == location_id)
                    .where(ACL.Tz == timezone)
                    .where(ACL.DGrp == device_group.DGrp)
                )

                if acl is None:
                    acl = ACL(
                        Loc=location_id,
                        Tz=timezone,
                        DGrp=device_group.DGrp,
                        Acl=self._session.scalar(select(func.max(ACL.Acl))) + 1,  # Grab the next one
                        DlFlag=1,
                        CkSum=0
                    )
                    self._session.add(acl)
                    self._session.commit()

                    # We added a new ACL, so update this location
                    self._location_ids_to_update.add(location_id)

                result[location_id].append(acl)

        return result

    def __get_loc_cards(self) -> list[LocCards]:
        result: list[LocCards] = []

        for location_id, acls in self._acls.items():
            acl_ids = set(x.Acl for x in acls)
            loc_cards = self._session.scalar(
                select(LocCards)
                .where(LocCards.CardID == self._card_id)
                .where(LocCards.Loc == location_id)
            )

            if loc_cards is None:
                loc_cards = LocCards(
                    Loc=location_id,
                    CardID=self._card_id,
                )

            acl = acl_ids.pop() if acl_ids else -1
            acl1 = acl_ids.pop() if acl_ids else -1
            acl2 = acl_ids.pop() if acl_ids else -1
            acl3 = acl_ids.pop() if acl_ids else -1
            acl4 = acl_ids.pop() if acl_ids else -1

            self.__set_loc_cards_acls(loc_cards, acl, acl1, acl2, acl3, acl4)
            self._location_ids_to_update.add(location_id)

        return result

    def __update_locations(self):
        for location_id in self._location_ids_to_update:
            location = self._session.scalar(
                select(LOC)
                .where(LOC.LocGrp == self._location_group_id)
                .where(LOC.Loc == location_id)
            )
            location.PlFlag = True
            location.TzCs = 0
            location.AclCs = 0
            location.DGrpCs = 0
            location.CodeCs = 0
            self._session.add(location)

            self._session.commit()

    def _deactivate_loc_cards(self):
        for location_id in self._locations:
            loc_cards = self._session.scalar(
                select(LocCards)
                .where(LocCards.CardID == self._card_id)
                .where(LocCards.Loc == location_id)
            )

            if loc_cards is None:
                continue

            self.__set_loc_cards_acls(loc_cards)
            self._location_ids_to_update.add(location_id)

    def __update_loc_cards_to_master(self):
        for location_id in self._locations:
            loc_cards = self._session.scalar(
                select(LocCards)
                .where(LocCards.CardID == self._card_id)
                .where(LocCards.Loc == location_id)
            )

            if loc_cards is None:
                loc_cards = LocCards(
                    Loc=location_id,
                    CardID=self._card_id,
                )

            self.__set_loc_cards_acls(
                    loc_cards,
                    0  # This is what sets the Acl to master
            )
            self._location_ids_to_update.add(location_id)

    def __set_loc_cards_acls(self,
                             loc_cards: LocCards,
                             acl: int = -1,
                             acl1: int = -1,
                             acl2: int = -1,
                             acl3: int = -1,
                             acl4: int = -1
                             ) -> None:
        acl_names = ["Acl", "Acl1", "Acl2", "Acl3", "Acl4"]
        acl_ids = [acl, acl1, acl2, acl3, acl4]
        for id_, name in zip(acl_ids, acl_names):
            current_acl = getattr(loc_cards, name)

            if current_acl == id_:
                continue

            setattr(loc_cards, name, id_)

        # 2 means delete, 1 means update. If they're all "no access" of -1, then we just delete the row.
        download = 2 if all(x == -1 for x in acl_ids) else 1
        loc_cards.DlFlag = download
        loc_cards.CkSum = 0

        self._session.add(loc_cards)
        self._session.commit()

        self._update_callback(loc_cards)
