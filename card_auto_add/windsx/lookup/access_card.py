from datetime import datetime, date
from typing import Optional, Union, Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session, InstrumentedAttribute

from card_auto_add.windsx.db.models import CARDS, LOC, AclGrpName, AclGrpCombo, AclGrp, DGRP, ACL, LocCards
from card_auto_add.windsx.lookup.acl_group_combo import AclGroupComboSet
from card_auto_add.windsx.lookup.person import Person
from card_auto_add.windsx.lookup.utils import LookupInfo, DbModel


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

        # TODO Handle len(valid_cards) > 1

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
        self._acl_group_combo.write()

        # TODO Handle card is None
        card: CARDS = self._get_card_from_db()
        card.NameID = self._name_id
        card.AclGrpComboID = self._acl_group_combo.id
        is_active: bool = len(self._acl_group_combo.names) > 0
        card.Status = is_active

        today = datetime.combine(date.today(), datetime.min.time())
        card.StopDate = AccessCard.active_stop_date if is_active else today

        self._session.add(card)
        self._session.commit()

        # Creating this object does everything we need it to.
        _AccessControlListUpdater(
            self._location_group_id,
            self._card_id,
            self._acl_group_combo.id,
            self._session
        )

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
                 session: Session):
        self._location_group_id = location_group_id
        self._card_id = card_id
        self._acl_group_combo_id = acl_group_combo_id
        self._session = session

        self._location_ids_to_update: set[int] = set()

        self._acl_group_name_ids: list[int] = self.__get_acl_group_name_ids()
        self._locations: list[int] = self.__get_locations()
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

                new_device_group: DGRP = DGRP(  # We make this just in case we need it later
                    Loc=location_id,
                    DlFlag=1,
                    CkSum=0
                )
                query = select(DGRP).where(DGRP.Loc == location_id)

                for i in range(128):
                    setattr(new_device_group, f"D{i}", (i in devices))

                    device_attr: InstrumentedAttribute = getattr(DGRP, f"D{i}")
                    query = query.where(device_attr == (i in devices))

                device_group: Optional[DGRP] = self._session.scalar(query)

                if device_group is not None:
                    result[location_id][timezone] = device_group
                    continue

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

            something_changed = False

            acl_names = ["Acl", "Acl1", "Acl2", "Acl3", "Acl4"]
            while len(acl_names) > 0:
                acl_name = acl_names.pop(0)

                current_acl = getattr(loc_cards, acl_name)

                if len(acl_ids) == 0:
                    # Set it to the default in case it was set to something else before.
                    if current_acl != -1:
                        something_changed = True
                        setattr(loc_cards, acl_name, -1)
                    continue

                acl = acl_ids.pop()

                if current_acl == acl:
                    continue

                something_changed = True
                setattr(loc_cards, acl_name, acl)

            if not something_changed:
                continue

            loc_cards.DlFlag = 1
            loc_cards.CkSum = 0

            self._session.add(loc_cards)
            self._session.commit()

            # We updated an LocCards, so update this location
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
