from typing import List, Optional

import pytest

from card_auto_add.windsx.db.acs_data import AcsData
from card_auto_add.windsx.db.name import Name, FieldValueInvalid
from tests.conftest import acs_data


class TestName:
    def test_can_retrieve_by_first_and_last_name(self, acs_data: AcsData):
        names: List[Name] = acs_data.names.by_name("Ray", "Securitay")

        assert len(names) == 1
        name: Name = names[0]

        assert name.id == 3
        assert name.first_name == "Ray"
        assert name.last_name == "Securitay"
        assert name.company_id == 2
        assert name.company is not None
        assert name.company.id == 2
        assert name.in_db

    def test_cannot_retrieve_missing_by_first_and_last_name(self, acs_data: AcsData):
        names: List[Name] = acs_data.names.by_name("Missing", "Person")

        assert len(names) == 0

    def test_can_retrieve_by_id(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(2)

        assert name.id == 2
        assert name.first_name == "Fire"
        assert name.last_name == "Key"
        assert name.company_id == 1
        assert name.company is not None
        assert name.company.id == 1
        assert name.in_db

    @staticmethod
    def assert_empty_name(name: Name, name_id: int):
        assert name.id == name_id
        assert name.first_name == ''
        assert name.last_name == ''
        assert name.company_id == 0
        assert name.company is None
        assert not name.in_db

    def test_cannot_retrieve_by_invalid_id(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(100)

        self.assert_empty_name(name, 100)

    def test_list_by_company_id(self, acs_data: AcsData):
        names: List[Name] = acs_data.names.by_company(4)

        assert len(names) == 2

        best_employee: Optional[Name] = next((n for n in names if n.id == 6), None)
        assert best_employee is not None
        assert best_employee.id == 6
        assert best_employee.first_name == "Best"
        assert best_employee.last_name == "Employee"
        assert best_employee.company_id == 4
        assert best_employee.company is not None
        assert best_employee.company.id == 4
        assert best_employee.in_db

        to_be_fired: Optional[Name] = next((n for n in names if n.id == 7), None)
        assert to_be_fired is not None
        assert to_be_fired.id == 7
        assert to_be_fired.first_name == "ToBe"
        assert to_be_fired.last_name == "Fired"
        assert to_be_fired.company_id == 4
        assert to_be_fired.company is not None
        assert to_be_fired.company.id == 4
        assert to_be_fired.in_db

    def test_updating_first_name_updates_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.first_name = "Improving"

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(5)

        assert fresh_name.id == 5
        assert fresh_name.first_name == "Improving"
        assert fresh_name.last_name == "Employee"
        assert fresh_name.company_id == 3
        assert fresh_name.company is not None
        assert fresh_name.company.id == 3
        assert fresh_name.in_db

    def test_updating_last_name_updates_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.last_name = "Person"

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(5)

        assert fresh_name.id == 5
        assert fresh_name.first_name == "Worst"
        assert fresh_name.last_name == "Person"
        assert fresh_name.company_id == 3
        assert fresh_name.company is not None
        assert fresh_name.company.id == 3
        assert fresh_name.in_db

    def test_updating_company_id_updates_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.company_id = 4

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(5)

        assert fresh_name.id == 5
        assert fresh_name.first_name == "Worst"
        assert fresh_name.last_name == "Employee"
        assert fresh_name.company_id == 4
        assert fresh_name.company is not None
        assert fresh_name.company.id == 4
        assert fresh_name.in_db

    def test_updating_company_updates_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.company = acs_data.company.by_id(4)

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(5)

        assert fresh_name.id == 5
        assert fresh_name.first_name == "Worst"
        assert fresh_name.last_name == "Employee"
        assert fresh_name.company_id == 4
        assert fresh_name.company is not None
        assert fresh_name.company.id == 4
        assert fresh_name.in_db

    def test_updating_first_name_does_not_update_when_not_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(99)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.first_name = "Improving"

        assert name.id == 99
        assert name.first_name == "Improving"
        assert name.last_name == ""
        assert name.company_id == 0
        assert name.company is None
        assert not name.in_db

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(99)
        self.assert_empty_name(fresh_name, 99)

    def test_updating_last_name_does_not_update_when_not_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(99)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.last_name = "Person"

        assert name.id == 99
        assert name.first_name == ""
        assert name.last_name == "Person"
        assert name.company_id == 0
        assert name.company is None
        assert not name.in_db

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(99)
        self.assert_empty_name(fresh_name, 99)

    def test_updating_company_id_does_not_update_when_not_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(99)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        name.company_id = 4

        assert name.id == 99
        assert name.first_name == ""
        assert name.last_name == ""
        assert name.company_id == 4
        assert name.company is not None
        assert name.company.id == 4
        assert not name.in_db

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(99)
        self.assert_empty_name(fresh_name, 99)

    def test_updating_company_does_not_update_when_not_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(99)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        new_company = acs_data.company.by_id(4)
        name.company = new_company

        assert name.id == 99
        assert name.first_name == ""
        assert name.last_name == ""
        assert name.company_id == 4
        assert name.company is new_company
        assert not name.in_db

        # Fetch the name fresh from the DB
        fresh_name: Name = acs_data.names.by_id(99)
        self.assert_empty_name(fresh_name, 99)

    def test_updating_first_name_invalid_fails_to_update_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        with pytest.raises(FieldValueInvalid) as ex:
            name.first_name = ""

        assert ex.value.field_name == "first_name"

    def test_updating_last_name_invalid_fails_to_update_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        with pytest.raises(FieldValueInvalid) as ex:
            name.last_name = ""

        assert ex.value.field_name == "last_name"

    def test_updating_company_id_invalid_fails_to_update_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        with pytest.raises(FieldValueInvalid) as ex:
            name.company_id = 0

        assert ex.value.field_name == "company_id"

    def test_updating_company_invalid_fails_to_update_when_in_db(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(5)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        with pytest.raises(FieldValueInvalid) as ex:
            name.company = acs_data.company.by_id(0)

        assert ex.value.field_name == "company"

    def test_writing_name_from_bad_id(self, acs_data: AcsData):
        name: Name = acs_data.names.empty()
        assert not name.in_db
        name.first_name = "Test"
        name.last_name = "User"
        name.company_id = 4

        name.write()

        assert name.in_db
        assert name.first_name == "Test"
        assert name.last_name == "User"
        assert name.company_id == 4

    def test_writing_first_name_invalid_fails(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(0)
        assert not name.in_db
        name.first_name = ""
        name.last_name = "User"
        name.company_id = 4

        with pytest.raises(FieldValueInvalid) as ex:
            name.write()

        assert ex.value.field_name == "first_name"

    def test_writing_last_name_invalid_fails(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(0)
        assert not name.in_db
        name.first_name = "Test"
        name.last_name = ""
        name.company_id = 4

        with pytest.raises(FieldValueInvalid) as ex:
            name.write()

        assert ex.value.field_name == "last_name"

    def test_writing_company_id_invalid_fails(self, acs_data: AcsData):
        name: Name = acs_data.names.by_id(0)
        assert not name.in_db
        name.first_name = "Test"
        name.last_name = "User"
        name.company_id = 0

        with pytest.raises(FieldValueInvalid) as ex:
            name.write()

        assert ex.value.field_name == "company_id"
