from datetime import datetime, date
from typing import Optional
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import CARDS
from card_auto_add.windsx.lookup.access_card import AccessCardLookup, AccessCard
from card_auto_add.windsx.lookup.person import Person, PersonLookup
from card_auto_add.windsx.lookup.utils import LookupInfo

_acl_name_master_access_level = "Master Access Level"
_acl_name_main_building_access = "Main Building Access"
_acl_name_tenant_1_access = "Tenant 1"
_acl_name_tenant_2_access = "Tenant 2"


class DbHelper:
    def __init__(self, lookup_info: LookupInfo):
        self._lookup_info = lookup_info
        self._session = Session(lookup_info.acs_engine)

    def card_by_id(self, card_id: int) -> Optional[CARDS]:
        return self._session.scalar(
            select(CARDS)
            .where(CARDS.ID == card_id)
            .where(CARDS.LocGrp == self._lookup_info.location_group_id)
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

        acs_updated_callback.assert_called_once_with(access_card)
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

        acs_updated_callback.assert_called_once_with(access_card)
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

        acs_updated_callback.assert_called_once_with(access_card)

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

        acs_updated_callback.assert_called_once_with(access_card)

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

        acs_updated_callback.assert_called_once_with(access_card)

        access_card: AccessCard = access_card_lookup.by_card_number(2000)
        assert access_card.in_db
        assert access_card.person.id == 403


# TODO
# - I'm thinking we should get rid of guard_db_populated and just always call _populate_from_db in our __init__ method from the parent.
# - Does writing an access card write the person or vice-versa? I think no.
# - TODO figure out the flow of adding a card to a person or vice-versa to make sure everything saves properly.
# - We'll need to essentially test every other table that gets updated in activations.py
# - CARDS  (AclGrpComboID, StartDate, StopDate, Status)
# - LocCards (DlFlag, CkSum, Acl, Acl1, Acl2, Acl3, Acl4. One row per location, looks like.)
# - AclGrpCombo (Not updated, but AclGrp is fetched with it)
# - AclGrp (For a given group name, what doors do you get access to with what time zone. We don't ever need to update this)
# - LOC (PlFlag, DlFlag, FullDlFlag, NodeCs, CodeCs, AclCs, DGrpCs all get updated. I'm noticing that really we only need to update PlFlag and ignore DlFlag and FullDlFlag. See scratch_26.py)
# - DGRP (Lookup or create new one. For a given location, what doors do you have access to. New one sets DlFlag to 1 and CkSum to 0)
# - ACL (For a specific DGRP and timezone, this gives the ACL that gets updated in LocCards.)
# Basically, what we have in activations.py is close but butchers all the location/location group stuff.
# - Test our updated callback. Really, since we have the card id, whatever handles this can just wait for all the LocCards to be downloaded. We shouldn't have to care about location, but if we have a plugin per location group, then it'll be useful to use the location of the location card to find which location group to send it to.
