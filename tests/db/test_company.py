import pytest

from card_auto_add.windsx.db.acs_data import AcsData
from card_auto_add.windsx.db.company import Company, CompanyNameCannotBeEmpty
from tests.conftest import acs_data


class TestCompany:
    def test_by_name(self, acs_data: AcsData):
        company: Company = acs_data.company.by_name("Security Company")

        assert company.id == 2
        assert company.name == "Security Company"
        assert company.in_db

    def test_by_name_not_in_db(self, acs_data: AcsData):
        company: Company = acs_data.company.by_name("Blorgh")

        assert company.id == 0
        assert company.name == "Blorgh"
        assert not company.in_db

    def test_can_write_to_db(self, acs_data: AcsData):
        company: Company = acs_data.company.by_name("Blorgh")

        assert not company.in_db

        company.write()

        assert company.in_db
        assert company.id == 6  # Last one in the list + 1
        assert company.name == "Blorgh"

    def test_by_id(self, acs_data: AcsData):
        company: Company = acs_data.company.by_id(3)

        assert company.id == 3
        assert company.name == "Tenant 1"
        assert company.in_db

    def test_by_id_not_in_db(self, acs_data: AcsData):
        company: Company = acs_data.company.by_id(99)

        assert company.id == 99
        assert company.name == ''
        assert not company.in_db

    def test_changing_name_when_in_db_updates_db(self, acs_data: AcsData):
        company: Company = acs_data.company.by_id(1)
        # We know this is in the DB, but we don't check here to make sure the code verifies first

        company.name = "New Company Name"

        # Fetch the company fresh from the DB and check the name
        fresh_company: Company = acs_data.company.by_id(1)

        assert fresh_company.name == "New Company Name"

    def test_changing_name_when_not_in_db(self, acs_data: AcsData):
        company: Company = acs_data.company.by_id(99)

        company.name = "New Company Name"

        # No writes should have happened, so we should have no name if we try to fetch it again
        fresh_company: Company = acs_data.company.by_id(99)

        assert company.name == "New Company Name"
        assert fresh_company.name == ""

    def test_cannot_update_to_empty_company_name(self, acs_data: AcsData):
        company: Company = acs_data.company.by_id(1)
        # This company exists, but giving it an empty name should throw an exception when writing

        with pytest.raises(CompanyNameCannotBeEmpty):
            company.name = ''

    def test_cannot_write_empty_company_name(self, acs_data: AcsData):
        company: Company = acs_data.company.by_name('')

        assert not company.in_db
        assert company.name == ''

        with pytest.raises(CompanyNameCannotBeEmpty):
            company.write()
