from datetime import datetime, date
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import CARDS
from card_auto_add.windsx.lookup.acl_group_combo import AclGroupComboSet
from card_auto_add.windsx.lookup.person import Person
from card_auto_add.windsx.lookup.utils import LookupInfo, DbModel, guard_db_populated


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
        super().__init__()
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = self._lookup_info.location_group_id
        self._session = Session(self._lookup_info.acs_engine)
        self._card_id: int = card_id
        self._card_number: Optional[int] = None
        self._name_id: Optional[int] = None
        self._active: Optional[bool] = None
        self._acl_group_combo: AclGroupComboSet = AclGroupComboSet(self._lookup_info, 0)

    @property
    def id(self) -> int:
        return self._card_id

    @property
    @guard_db_populated
    def card_number(self) -> int:
        return self._card_number

    @card_number.setter
    def card_number(self, value: Union[str, int]) -> None:
        self._card_number = value

    @property
    @guard_db_populated
    def active(self) -> bool:
        return self._active

    @property
    @guard_db_populated
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
        # TODO Test if this is in the DB and only write it if it's not
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

        self._lookup_info.updated_callback(self)
