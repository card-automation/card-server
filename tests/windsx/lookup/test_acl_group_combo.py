from typing import List

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.windsx.lookup.acl_group_combo import AclGroupComboSet, AclGroupNameNotInCombo, AclGroupNameNotInDatabase, \
    AclGroupComboLookup
from card_auto_add.windsx.db.models import AclGrpCombo
from tests.conftest import acs_data_engine, location_group_id


class TestAclGroupCombo:
    """
    The data used in this test is set up via conftest.py.
    """

    # These names are in the AclGrpName table
    _master_access_level = "Master Access Level"
    _main_building_access = "Main Building Access"
    _tenant_1 = "Tenant 1"
    _tenant_2 = "Tenant 2"
    _tenant_3 = "Tenant 3"

    @pytest.fixture
    def acl_group_combo_lookup(self, acs_data_engine: Engine) -> AclGroupComboLookup:
        return AclGroupComboLookup(acs_data_engine, location_group_id)

    def test_empty(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.empty()
        assert acl_group_combo.id == 0
        assert acl_group_combo.names == frozenset()
        assert not acl_group_combo.in_db

    def test_lookup_by_id(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(106)
        assert acl_group_combo.id == 106
        assert acl_group_combo.names == frozenset({self._tenant_3, self._main_building_access})
        assert acl_group_combo.in_db

    def test_lookup_by_id_that_does_not_exist(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(99)
        assert acl_group_combo.id == 99
        assert len(acl_group_combo.names) == 0
        assert not acl_group_combo.in_db

    def test_lookup_by_name(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_names(self._tenant_1)
        assert acl_group_combo.id == 108
        assert acl_group_combo.names == frozenset({self._tenant_1})
        assert acl_group_combo.in_db

    def test_lookup_by_names(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_names(self._main_building_access, self._tenant_1)
        assert acl_group_combo.id == 102
        assert acl_group_combo.names == frozenset({self._tenant_1, self._main_building_access})
        assert acl_group_combo.in_db

    def test_by_name_that_is_not_in_our_names_table(self, acl_group_combo_lookup: AclGroupComboLookup):
        invalid_name = "Blorgh"

        with pytest.raises(AclGroupNameNotInDatabase) as ex:
            acl_group_combo_lookup.by_names(invalid_name)

        assert ex.value.missing_name == invalid_name

    def test_lookup_by_name_with_group_that_does_not_exist(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_names(self._tenant_1, self._tenant_2)
        assert acl_group_combo.id == 0
        assert acl_group_combo.names == frozenset({self._tenant_1, self._tenant_2})
        assert not acl_group_combo.in_db

    def test_writing_non_existent_acl_combo_to_db(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_names(self._tenant_1, self._tenant_2)
        assert not acl_group_combo.in_db

        acl_group_combo.write()

        assert acl_group_combo.id != 0
        assert acl_group_combo.names == frozenset({self._tenant_1, self._tenant_2})
        assert acl_group_combo.in_db

        # Now to make sure we would generate the same acl group combo based on the id:
        new_acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(acl_group_combo.id)
        assert new_acl_group_combo.id == acl_group_combo.id
        assert new_acl_group_combo.names == acl_group_combo.names
        assert new_acl_group_combo.in_db == acl_group_combo.in_db

    def test_nothing_writes_if_in_db_already(self, acs_data_engine: Engine,
                                             acl_group_combo_lookup: AclGroupComboLookup):
        session = Session(acs_data_engine)
        starting_rows = session.execute(select(AclGrpCombo)).all()

        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_names(self._tenant_1)
        # We know this one is in the db, but we don't want to check it here to make sure our code checks it in write

        acl_group_combo.write()

        ending_rows = session.execute(select(AclGrpCombo)).all()

        assert starting_rows == ending_rows

    def test_nothing_writes_if_empty(self, acs_data_engine: Engine, acl_group_combo_lookup: AclGroupComboLookup):
        session = Session(acs_data_engine)
        starting_rows = session.execute(select(AclGrpCombo)).all()

        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.empty()

        acl_group_combo.write()

        ending_rows = session.execute(select(AclGrpCombo)).all()

        assert starting_rows == ending_rows

    def test_using_with_method_to_get_new_combos(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(101)  # Main building by itself
        # We intentionally don't check names or in_db on acl_group_combo to make sure our code does it on our behalf
        new_acl_group_combo: AclGroupComboSet = acl_group_combo.with_names("Tenant 2")

        assert new_acl_group_combo.id == 104  # Main building + Tenant 2
        assert new_acl_group_combo.names == frozenset({self._main_building_access, self._tenant_2})
        assert new_acl_group_combo.in_db

    def test_using_without_method_to_get_new_combos(self, acl_group_combo_lookup: AclGroupComboLookup):
        # This is essentially the inverse of the test test_using_with_method_to_get_new_combos
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(104)  # Main building + Tenant 2
        # We intentionally don't check names or in_db on acl_group_combo to make sure our code does it on our behalf
        new_acl_group_combo: AclGroupComboSet = acl_group_combo.without_names("Tenant 2")

        assert new_acl_group_combo.id == 101
        assert new_acl_group_combo.names == frozenset({self._main_building_access})
        assert new_acl_group_combo.in_db

    def test_using_without_method_to_remove_all_names(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(101)  # Main building by itself

        new_acl_group_combo: AclGroupComboSet = acl_group_combo.without_names(self._main_building_access)

        assert new_acl_group_combo.id == 0
        assert new_acl_group_combo.names == frozenset()
        assert not new_acl_group_combo.in_db

    def test_without_removing_a_name_that_is_not_in_our_table(self, acl_group_combo_lookup: AclGroupComboLookup):
        acl_group_combo: AclGroupComboSet = acl_group_combo_lookup.by_id(101)  # Main building by itself

        invalid_name = "Blorgh"
        with pytest.raises(AclGroupNameNotInCombo) as ex:
            acl_group_combo.without_names(invalid_name)

        assert ex.value.missing_name == invalid_name

    def test_retrieving_all_group_combos(self, acl_group_combo_lookup: AclGroupComboLookup):
        all_combos: List[AclGroupComboSet] = acl_group_combo_lookup.all()

        assert len(all_combos) == 8  # Update this value and add entries below if you add new entries in conftest.py

        def assertions(_id: int, _names: frozenset[str]):
            _combo_we_want = None
            for _combo in all_combos:
                if _combo.id == _id:
                    _combo_we_want = _combo
                    break

            if _combo_we_want is None:
                assert False, f"Combo for id {_id} was None"

            # No ID assertion as we retrieved it by the ID
            assert _combo_we_want.in_db
            assert _combo_we_want.names == _names

        assertions(100, frozenset({self._master_access_level}))
        assertions(101, frozenset({self._main_building_access}))
        assertions(102, frozenset({self._main_building_access, self._tenant_1}))
        assertions(104, frozenset({self._main_building_access, self._tenant_2}))
        assertions(106, frozenset({self._main_building_access, self._tenant_3}))
        assertions(108, frozenset({self._tenant_1}))
        assertions(109, frozenset({self._tenant_2}))
        assertions(110, frozenset({self._tenant_3}))
