from datetime import datetime, date
from typing import Optional, Sequence, Union
from unittest.mock import Mock, call

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, InstrumentedAttribute, Mapped

from card_auto_add.windsx.db.models import CARDS, DGRP, ACL, LocCards, LOC
from card_auto_add.windsx.lookup.access_card import AccessCardLookup, AccessCard, InvalidPersonForAccessCard
from card_auto_add.windsx.lookup.person import Person, PersonLookup
from card_auto_add.windsx.lookup.utils import LookupInfo
from tests.conftest import main_location_id, annex_location_id

_acl_name_master_access_level = "Master Access Level"
_acl_name_main_building_access = "Main Building Access"
_acl_name_tenant_1_access = "Tenant 1"
_acl_name_tenant_2_access = "Tenant 2"
_acl_name_tenant_3_access = "Tenant 3"


class DbHelper:
    def __init__(self, lookup_info: LookupInfo):
        self._lookup_info = lookup_info

    @property
    def _session(self) -> Session:
        # Using a property and a new session means we avoid caching issues in the test
        return Session(self._lookup_info.acs_engine)

    def card_by_id(self, card_id: int) -> Optional[CARDS]:
        return self._session.scalar(
            select(CARDS)
            .where(CARDS.ID == card_id)
            .where(CARDS.LocGrp == self._lookup_info.location_group_id)
        )

    def device_group_by_devices(self, location_id: int, *attributes: InstrumentedAttribute) -> Sequence[DGRP]:
        query = select(DGRP).where(DGRP.Loc == location_id)

        for i in range(128):
            device_attr: InstrumentedAttribute = getattr(DGRP, f"D{i}")
            query = query.where(device_attr == (device_attr in attributes))

        return self._session.scalars(query).all()

    def acl(self, location_id: int, dgrp: int, timezone: int) -> Optional[ACL]:
        return self._session.scalar(
            select(ACL)
            .where(ACL.Loc == location_id)
            .where(ACL.Tz == timezone)
            .where(ACL.DGrp == dgrp)
        )

    def loc_cards(self, card_id: int, location_id: int, acl: Union[int, Mapped[int]]) -> Optional[LocCards]:
        return self._session.scalar(
            select(LocCards)
            .where(LocCards.CardID == card_id)
            .where(LocCards.Loc == location_id)
            .where(LocCards.Acl == acl)
        )

    def loc(self, location_id: int) -> Optional[LOC]:
        return self._session.scalar(
            select(LOC)
            .where(LOC.LocGrp == self._lookup_info.location_group_id)
            .where(LOC.Loc == location_id)
        )


@pytest.fixture
def db_helper(lookup_info: LookupInfo) -> DbHelper:
    return DbHelper(lookup_info)


class TestAccessCardLookup:
    def test_can_lookup_card_by_card_number_int(self,
                                                access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(3000)

        assert access_card.in_db
        assert access_card.id == 1
        assert access_card.card_number == 3000
        assert access_card.active
        assert access_card.access == frozenset({_acl_name_master_access_level})
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 101

    def test_can_lookup_card_by_card_number_string(self,
                                                   access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number("3000")

        assert access_card.in_db
        assert access_card.id == 1
        assert access_card.card_number == 3000
        assert access_card.active
        assert access_card.access == frozenset({_acl_name_master_access_level})
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 101

    def test_lookup_strips_leading_zeros(self,
                                         access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number("00200")

        assert access_card.in_db
        assert access_card.id == 2
        assert access_card.card_number == 200
        assert access_card.active
        assert access_card.access == frozenset({_acl_name_master_access_level})
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 110

    def test_lookup_missing_card(self,
                                 access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(10000)

        assert not access_card.in_db
        assert access_card.id == 0
        assert access_card.card_number == 10000
        assert not access_card.active
        assert access_card.access == frozenset()
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 0
        assert not access_card.person.in_db

    def test_lookup_bad_location_group(self,
                                       access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(3001)

        # This does exist in the DB, but only in an incorrect location group, so we treat it like it's not in the DB.
        assert not access_card.in_db
        assert access_card.id == 0
        assert access_card.card_number == 3001
        assert not access_card.active
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 0
        assert not access_card.person.in_db

    def test_direct_access_bad_location_group(self, lookup_info: LookupInfo):
        access_card: AccessCard = AccessCard(lookup_info, 1002)  # Card # 3001, bad location group

        # This does exist in the DB, but only in an incorrect location group, so we treat it like it's not in the DB.
        assert not access_card.in_db
        assert access_card.id == 1002
        assert access_card.card_number is None  # We never set it, so it should remain None
        assert not access_card.active
        assert isinstance(access_card.person, Person)
        assert access_card.person.id == 0
        assert not access_card.person.in_db


class TestAccessCardWrite:
    today = datetime.combine(date.today(), datetime.min.time())

    def test_adding_access_level(self,
                                 acs_updated_callback: Mock,
                                 access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(2001)

        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({_acl_name_main_building_access})

        # "new" just to verify the builder pattern updates and returns the same object
        new_access_card = access_card.with_access(_acl_name_tenant_1_access)
        assert new_access_card is access_card

        # It has a card id so it's still in the db even if it hasn't been updated
        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({
            _acl_name_main_building_access,
            _acl_name_tenant_1_access
        })

        acs_updated_callback.assert_not_called()

        access_card.write()

        assert acs_updated_callback.call_count == 2
        # Second call would be the loc_cards
        acs_updated_callback.assert_called_with(access_card)

        access_card = access_card_lookup.by_card_number(2001)

        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({
            _acl_name_main_building_access,
            _acl_name_tenant_1_access
        })

    def test_adding_access_level_to_card_that_has_no_access(self,
                                                            acs_updated_callback: Mock,
                                                            access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        assert access_card.in_db
        assert not access_card.active
        assert access_card.access == frozenset()

        # "new" just to verify the builder pattern updates and returns the same object
        new_access_card = access_card.with_access(_acl_name_main_building_access, _acl_name_tenant_2_access)
        assert new_access_card is access_card

        # It has a card id so it's still in the db even if it hasn't been updated.
        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({
            _acl_name_main_building_access,
            _acl_name_tenant_2_access
        })

        acs_updated_callback.assert_not_called()

        access_card.write()

        assert acs_updated_callback.call_count == 3
        # Second and third call would be the loc_cards
        acs_updated_callback.assert_called_with(access_card)

        access_card = access_card_lookup.by_card_number(2002)

        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({
            _acl_name_main_building_access,
            _acl_name_tenant_2_access
        })

    def test_removing_all_access_levels(self,
                                        acs_updated_callback: Mock,
                                        access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(2000)

        assert access_card.in_db
        assert access_card.active
        assert access_card.access == frozenset({
            _acl_name_main_building_access,
            _acl_name_tenant_2_access
        })

        # "new" just to verify the builder pattern updates and returns the same object
        new_access_card = access_card.without_access(_acl_name_main_building_access, _acl_name_tenant_2_access)
        assert new_access_card is access_card

        # It has a card id so it's still in the db even if it hasn't been updated.
        assert access_card.in_db
        assert not access_card.active
        assert access_card.access == frozenset()

        acs_updated_callback.assert_not_called()

        access_card.write()

        acs_updated_callback.assert_called_once_with(access_card)
        access_card = access_card_lookup.by_card_number(2000)

        assert access_card.in_db
        assert not access_card.active
        assert access_card.access == frozenset()

    def test_activating_a_card_sets_stop_date_to_forever(self,
                                                         acs_updated_callback: Mock,
                                                         access_card_lookup: AccessCardLookup,
                                                         db_helper: DbHelper):
        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        assert access_card.in_db
        assert not access_card.active

        access_card \
            .with_access(_acl_name_main_building_access) \
            .write()

        assert acs_updated_callback.call_count == 2
        # Second call would be the loc_cards
        acs_updated_callback.assert_called_with(access_card)

        card: CARDS = db_helper.card_by_id(access_card.id)
        assert card.Status
        assert card.StartDate < self.today  # We don't care what it is, just that it's earlier than today
        assert card.StopDate == AccessCard.active_stop_date

    def test_deactivating_a_card_sets_stop_date_to_forever(self,
                                                           acs_updated_callback: Mock,
                                                           access_card_lookup: AccessCardLookup,
                                                           db_helper: DbHelper):
        access_card: AccessCard = access_card_lookup.by_card_number(2000)

        assert access_card.in_db
        assert access_card.active

        access_card \
            .without_access(_acl_name_main_building_access) \
            .without_access(_acl_name_tenant_2_access) \
            .write()

        acs_updated_callback.assert_called_once_with(access_card)

        card: CARDS = db_helper.card_by_id(access_card.id)
        assert not card.Status
        assert card.StartDate < self.today  # We don't care what it is, just that it's earlier than today
        assert card.StopDate == self.today

    def test_can_update_person(self,
                               acs_updated_callback: Mock,
                               access_card_lookup: AccessCardLookup,
                               person_lookup: PersonLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(2000)  # ToBe Fired

        assert access_card.in_db
        assert access_card.person.id == 402

        person: Person = person_lookup.by_card(2002).find()[0]  # ToBe Hired
        assert person.id == 403

        access_card.person = person
        access_card.write()

        assert acs_updated_callback.call_count == 3
        # Second and third call would be the loc_cards
        acs_updated_callback.assert_called_with(access_card)

        access_card: AccessCard = access_card_lookup.by_card_number(2000)
        assert access_card.in_db
        assert access_card.person.id == 403

    def test_can_update_person_by_id(self,
                                     acs_updated_callback: Mock,
                                     access_card_lookup: AccessCardLookup,
                                     person_lookup: PersonLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(2000)  # ToBe Fired

        assert access_card.in_db
        assert access_card.person.id == 402

        person: Person = person_lookup.by_card(2002).find()[0]  # ToBe Hired
        assert person.id == 403

        access_card.person = person.id
        access_card.write()

        assert acs_updated_callback.call_count == 3
        # Second and third call would be the loc_cards
        acs_updated_callback.assert_called_with(access_card)

        access_card: AccessCard = access_card_lookup.by_card_number(2000)
        assert access_card.in_db
        assert access_card.person.id == 403

    def test_writing_card_creates_needed_device_groups(self,
                                                       db_helper: DbHelper,
                                                       access_card_lookup: AccessCardLookup):
        # Device groups:
        # Main location, door 0 - In db
        # Main location, door 2 - NOT in db
        # Annex location, door 1 - NOT in db
        device_groups = db_helper.device_group_by_devices(main_location_id, DGRP.D0)
        assert len(device_groups) == 1
        device_group: DGRP = device_groups[0]
        assert device_group.ID == 5001
        assert device_group.DGrp == 1
        device_groups = db_helper.device_group_by_devices(main_location_id, DGRP.D2)
        assert len(device_groups) == 0
        device_groups = db_helper.device_group_by_devices(annex_location_id, DGRP.D1)
        assert len(device_groups) == 0

        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        access_card \
            .with_access(_acl_name_tenant_2_access) \
            .write()

        # Now we should have a new DGRP with those doors in each location
        device_groups = db_helper.device_group_by_devices(main_location_id, DGRP.D0)
        assert len(device_groups) == 1
        device_group: DGRP = device_groups[0]
        assert device_group.ID == 5001
        assert device_group.DGrp == 1
        assert device_group.DlFlag == 0  # We didn't set it to download

        device_groups = db_helper.device_group_by_devices(main_location_id, DGRP.D2)
        assert len(device_groups) == 1
        device_group: DGRP = device_groups[0]
        assert device_group.DlFlag == 1
        assert device_group.CkSum == 0

        device_groups = db_helper.device_group_by_devices(annex_location_id, DGRP.D1)
        assert len(device_groups) == 1
        device_group: DGRP = device_groups[0]
        assert device_group.DlFlag == 1
        assert device_group.CkSum == 0

    def test_writing_card_creates_needed_acl_entries(self,
                                                     db_helper: DbHelper,
                                                     access_card_lookup: AccessCardLookup):
        assert db_helper.acl(main_location_id, 3, 1) is not None
        assert db_helper.acl(annex_location_id, 4, 1) is None
        assert db_helper.acl(annex_location_id, 5, 3) is None

        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        access_card \
            .with_access(_acl_name_tenant_3_access) \
            .write()

        acl = db_helper.acl(main_location_id, 3, 1)
        assert acl is not None
        assert acl.DlFlag == 0  # Already existed, so we shouldn't set it to download

        acl = db_helper.acl(annex_location_id, 4, 1)
        assert acl is not None
        assert acl.Acl != 0  # Should just be incremented, but as long as it's not 0 as that becomes master access level
        assert acl.DlFlag == 1
        assert acl.CkSum == 0

        acl = db_helper.acl(annex_location_id, 5, 3)
        assert acl is not None
        assert acl.Acl != 0
        assert acl.DlFlag == 1
        assert acl.CkSum == 0

    def test_writing_card_creates_needed_loc_cards_entries(self,
                                                           acs_data_session: Session,
                                                           db_helper: DbHelper,
                                                           acs_updated_callback: Mock,
                                                           access_card_lookup: AccessCardLookup):
        assert db_helper.loc_cards(5, main_location_id, 11) is not None
        starting_rows = acs_data_session.scalars(select(LocCards)).all()

        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        access_card \
            .with_access(_acl_name_tenant_3_access) \
            .write()

        ending_rows = acs_data_session.scalars(select(LocCards)).all()
        assert len(starting_rows) + 1 == len(ending_rows)

        loc_cards = db_helper.loc_cards(5, main_location_id, 11)
        assert loc_cards is not None
        assert loc_cards.DlFlag == 0

        new_loc_cards = None
        for ending_row in ending_rows:
            if any(x.ID == ending_row.ID for x in starting_rows):
                continue
            new_loc_cards = ending_row
            break

        assert new_loc_cards is not None
        assert new_loc_cards.DlFlag == 1
        assert new_loc_cards.CkSum == 0

        acl_a = db_helper.acl(annex_location_id, 4, 1)
        assert acl_a is not None  # Previous test should verify more details
        acl_b = db_helper.acl(annex_location_id, 5, 3)
        assert acl_b is not None  # Previous test should verify more details

        # We don't know what order these will be in, but either is valid
        ab_match = new_loc_cards.Acl == acl_a.Acl \
                   and new_loc_cards.Acl1 == acl_b.Acl \
                   and new_loc_cards.Acl2 == -1 \
                   and new_loc_cards.Acl3 == -1 \
                   and new_loc_cards.Acl4 == -1

        ba_match = new_loc_cards.Acl == acl_b.Acl \
                   and new_loc_cards.Acl1 == acl_a.Acl \
                   and new_loc_cards.Acl2 == -1 \
                   and new_loc_cards.Acl3 == -1 \
                   and new_loc_cards.Acl4 == -1

        assert ab_match or ba_match

        assert acs_updated_callback.call_count == 2
        # Called with new_loc_cards and access_card
        acs_updated_callback.assert_called_with(access_card)
        loc_cards_calls = [x
                           for x in acs_updated_callback.call_args_list
                           if len(x.args) == 1 and isinstance(x.args[0], LocCards)]
        assert len(loc_cards_calls) == 1
        loc_cards_arg: LocCards = loc_cards_calls[0].args[0]
        assert loc_cards_arg.ID == new_loc_cards.ID
        assert loc_cards_arg.CardID == new_loc_cards.CardID
        assert loc_cards_arg.Loc == new_loc_cards.Loc

    def test_removing_card_access_sets_loc_cards_row_for_deletion(self,
                                                                  acs_data_session: Session,
                                                                  db_helper: DbHelper,
                                                                  acs_updated_callback: Mock,
                                                                  access_card_lookup: AccessCardLookup):
        assert db_helper.loc_cards(5, main_location_id, 11) is not None
        starting_rows = acs_data_session.scalars(select(LocCards)).all()

        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        access_card \
            .without_access(*access_card.access) \
            .write()

        assert not access_card.active

        ending_rows = acs_data_session.scalars(select(LocCards)).all()
        assert len(starting_rows) == len(ending_rows)

        # Acl -1 because the card is set for deactivation
        loc_cards = db_helper.loc_cards(5, main_location_id, -1)
        assert loc_cards is not None
        # When de-activating a card, we only signal that the LocCards row will be deleted. We don't do it ourselves.
        assert loc_cards.DlFlag == 2
        assert loc_cards.Acl == -1
        assert loc_cards.Acl1 == -1
        assert loc_cards.Acl2 == -1
        assert loc_cards.Acl3 == -1
        assert loc_cards.Acl4 == -1

        assert acs_updated_callback.call_count == 2
        # Called with loc_cards and access_card
        acs_updated_callback.assert_called_with(access_card)
        loc_cards_calls = [x
                           for x in acs_updated_callback.call_args_list
                           if len(x.args) == 1 and isinstance(x.args[0], LocCards)]
        assert len(loc_cards_calls) == 1
        loc_cards_arg: LocCards = loc_cards_calls[0].args[0]
        assert loc_cards_arg.ID == loc_cards.ID
        assert loc_cards_arg.CardID == loc_cards.CardID
        assert loc_cards_arg.Loc == loc_cards.Loc

    def test_giving_master_access_level_sets_acl_to_zero(self,
                                                         acs_data_session: Session,
                                                         db_helper: DbHelper,
                                                         acs_updated_callback: Mock,
                                                         access_card_lookup: AccessCardLookup):
        starting_dgrp_rows = acs_data_session.scalars(select(DGRP)).all()
        starting_acl_rows = acs_data_session.scalars(select(ACL)).all()
        starting_loc_cards_rows = acs_data_session.scalars(select(LocCards)).all()

        assert db_helper.loc_cards(6, main_location_id, 0) is None
        assert db_helper.loc_cards(6, annex_location_id, 0) is None

        access_card: AccessCard = access_card_lookup.by_card_number(2003)
        access_card \
            .with_access(_acl_name_master_access_level) \
            .write()

        ending_dgrp_rows = acs_data_session.scalars(select(DGRP)).all()
        assert len(starting_dgrp_rows) == len(ending_dgrp_rows)
        ending_acl_rows = acs_data_session.scalars(select(ACL)).all()
        assert len(starting_acl_rows) == len(ending_acl_rows)
        ending_loc_cards_rows = acs_data_session.scalars(select(LocCards)).all()
        assert len(starting_loc_cards_rows) + 2 == len(ending_loc_cards_rows)

        # These are the extra 2 rows
        main_loc_cards = db_helper.loc_cards(6, main_location_id, 0)
        assert main_loc_cards is not None
        assert main_loc_cards.DlFlag == 1
        assert main_loc_cards.CkSum == 0
        assert main_loc_cards.Acl == 0  # Master access level
        assert main_loc_cards.Acl1 == -1
        assert main_loc_cards.Acl2 == -1
        assert main_loc_cards.Acl3 == -1
        assert main_loc_cards.Acl4 == -1

        annex_loc_cards = db_helper.loc_cards(6, annex_location_id, 0)
        assert annex_loc_cards is not None
        assert annex_loc_cards.DlFlag == 1
        assert annex_loc_cards.CkSum == 0
        assert annex_loc_cards.Acl == 0  # Master access level
        assert annex_loc_cards.Acl1 == -1
        assert annex_loc_cards.Acl2 == -1
        assert annex_loc_cards.Acl3 == -1
        assert annex_loc_cards.Acl4 == -1

        assert acs_updated_callback.call_count == 3
        # Called with main_loc_cards, annex_loc_cards, and access_card
        acs_updated_callback.assert_called_with(access_card)

        for loc_cards in [main_loc_cards, annex_loc_cards]:
            loc_cards_calls = [
                x for x in acs_updated_callback.call_args_list
                if len(x.args) == 1 \
                   and isinstance(x.args[0], LocCards) \
                   and x.args[0].ID == loc_cards.ID
            ]
            assert len(loc_cards_calls) == 1
            loc_cards_arg: LocCards = loc_cards_calls[0].args[0]
            assert loc_cards_arg.ID == loc_cards.ID
            assert loc_cards_arg.CardID == loc_cards.CardID
            assert loc_cards_arg.Loc == loc_cards.Loc

    def test_writing_card_updates_location_table_to_download(self,
                                                             db_helper: DbHelper,
                                                             access_card_lookup: AccessCardLookup):
        # This is the same setup as test_writing_card_creates_needed_loc_cards_entries
        # We expect the main location not to need an update, because every step of the way the main building has had its
        # DGRP, ACL, LocCards entries all pre-populated. The only side that got changed was the annex.

        main_building = db_helper.loc(main_location_id)
        assert main_building is not None
        assert not main_building.PlFlag

        annex = db_helper.loc(annex_location_id)
        assert annex is not None
        assert not annex.PlFlag

        access_card: AccessCard = access_card_lookup.by_card_number(2002)

        access_card \
            .with_access(_acl_name_tenant_3_access) \
            .write()

        main_building = db_helper.loc(main_location_id)
        assert not main_building.PlFlag  # Still no updates for you
        annex = db_helper.loc(annex_location_id)
        assert annex.PlFlag
        assert annex.TzCs == 0
        assert annex.AclCs == 0
        assert annex.DGrpCs == 0
        assert annex.CodeCs == 0

    def test_writing_new_card(self,
                              acs_updated_callback: Mock,
                              access_card_lookup: AccessCardLookup,
                              person_lookup: PersonLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(9999)
        assert not access_card.in_db

        person: Person = person_lookup.by_name("JaneThe", "BuildingManager").find()[0]

        access_card.person = person
        access_card.write()

        acs_updated_callback.assert_called_once_with(access_card)

        assert access_card.in_db
        assert access_card.id != 0

    def test_writing_new_card_with_no_person(self,
                                             access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(9999)
        assert not access_card.in_db

        with pytest.raises(InvalidPersonForAccessCard):
            access_card.write()

    def test_writing_missing_person(self,
                                    access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(9999)
        assert not access_card.in_db

        access_card.person = 5555  # This ID doesn't exist

        with pytest.raises(InvalidPersonForAccessCard):
            access_card.write()

    def test_writing_missing_person_with_different_location_group(self,
                                                                  access_card_lookup: AccessCardLookup):
        access_card: AccessCard = access_card_lookup.by_card_number(9999)
        assert not access_card.in_db

        access_card.person = 1101  # BobThe BuildingManager with bad location group

        with pytest.raises(InvalidPersonForAccessCard):
            access_card.write()
