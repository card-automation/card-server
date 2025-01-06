from typing import Required

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import UDF, UdfName
from card_auto_add.windsx.db.person import PersonHelper, Person, InvalidUdfName, MissingRequiredUserDefinedField, \
    InvalidUdfSelection
from tests.conftest import location_group_id


class TestPerson:
    @pytest.fixture
    def person_helper(self, acs_data_engine: Engine) -> PersonHelper:
        return PersonHelper(acs_data_engine, location_group_id)

    @pytest.fixture
    def bob_the_building_manager(self, person_helper: PersonHelper) -> Person:
        people = person_helper.by_name('BobThe', 'BuildingManager').find()

        assert len(people) == 1

        return people[0]

    @pytest.fixture
    def required_udf_name(self, acs_data_session: Session) -> UdfName:
        udf_name: UdfName = UdfName(
            LocGrp=location_group_id,
            UdfNum=3,
            Name="Required_Name",
            Required=True,
            Combo=False
        )
        acs_data_session.add(udf_name)
        acs_data_session.commit()

        return udf_name

    @pytest.fixture
    def fruit_combo_only(self, acs_data_session: Session) -> UdfName:
        udf_name: UdfName = acs_data_session.scalar(select(UdfName).where(UdfName.UdfNum == 2))
        udf_name.ComboOnly = True
        acs_data_session.add(udf_name)
        acs_data_session.commit()

        return udf_name

    @staticmethod
    def _assert_bob_the_building_manager(person: Person):
        assert person.in_db
        assert person.id == 101
        assert person.first_name == 'BobThe'
        assert person.last_name == 'BuildingManager'
        assert person.company_id == 1

        assert len(person.user_defined_fields) == 2
        assert 'ID' in person.user_defined_fields
        assert person.user_defined_fields['ID'] == "5000"
        assert 'Fruit' in person.user_defined_fields
        assert person.user_defined_fields['Fruit'] == "Apple"
        # TODO assert cards

    @staticmethod
    def _assert_ray_securitay(person: Person):
        assert person.in_db
        assert person.id == 201
        assert person.first_name == 'Ray'
        assert person.last_name == 'Securitay'
        assert person.company_id == 2

        assert len(person.user_defined_fields) == 0
        # TODO assert cards

    def test_lookup_by_name(self, person_helper: PersonHelper):
        people = person_helper.by_name('BobThe', 'BuildingManager').find()

        assert len(people) == 1

        person = people[0]
        self._assert_bob_the_building_manager(person)

    def test_lookup_by_udf(self, person_helper: PersonHelper):
        people = person_helper.by_udf("ID", "5000").find()

        assert len(people) == 1

        person = people[0]
        self._assert_bob_the_building_manager(person)

    def test_lookup_by_udf_select(self, person_helper: PersonHelper):
        people = person_helper.by_udf("Fruit", "Apple").find()

        assert len(people) == 1

        person = people[0]
        self._assert_bob_the_building_manager(person)

    def test_lookup_by_multiple_udf(self, person_helper: PersonHelper):
        people = person_helper \
            .by_udf("ID", "5000") \
            .by_udf("Fruit", "Apple") \
            .find()

        assert len(people) == 1

        person = people[0]
        self._assert_bob_the_building_manager(person)

    def test_lookup_by_card(self, person_helper: PersonHelper):
        people = person_helper.by_card(3000).find()

        assert len(people) == 1

        person = people[0]
        self._assert_bob_the_building_manager(person)

    def test_lookup_by_company_id(self, person_helper: PersonHelper):
        people = person_helper.by_company(2).find()

        assert len(people) == 1

        person = people[0]
        self._assert_ray_securitay(person)

    def test_lookup_on_invalid_udf_name(self, person_helper: PersonHelper):
        with pytest.raises(InvalidUdfName) as ex:
            person_helper.by_udf("INVALID_UDF", "").find()

        assert ex.value.invalid_key == "INVALID_UDF"

    def test_writing_an_existing_person(self, bob_the_building_manager: Person, person_helper: PersonHelper):
        bob_the_building_manager.first_name = "Greg"
        bob_the_building_manager.last_name = "Gregory"
        bob_the_building_manager.company_id = 3
        bob_the_building_manager.user_defined_fields['ID'] = "6000"
        bob_the_building_manager.user_defined_fields['Fruit'] = "Pear"

        bob_the_building_manager.write()

        people = person_helper.by_name("Greg", "Gregory").find()
        assert len(people) == 1
        new_person = people[0]

        assert bob_the_building_manager.first_name == new_person.first_name
        assert bob_the_building_manager.last_name == new_person.last_name
        assert bob_the_building_manager.company_id == new_person.company_id
        assert bob_the_building_manager.user_defined_fields == new_person.user_defined_fields

    def test_new_person(self, person_helper: PersonHelper):
        person: Person = person_helper.new()

        assert not person.in_db
        assert person.first_name is None
        assert person.last_name is None
        assert person.company_id is None
        assert person.user_defined_fields == {}

    def test_writing_a_new_person(self, person_helper: PersonHelper):
        person: Person = person_helper.new()
        person.first_name = "Greg"
        person.last_name = "Gregory"
        person.company_id = 3
        person.user_defined_fields['ID'] = "6000"

        person.write()

        people = person_helper.by_name("Greg", "Gregory").find()
        assert len(people) == 1
        new_person = people[0]

        assert person.first_name == new_person.first_name
        assert person.last_name == new_person.last_name
        assert person.company_id == new_person.company_id
        assert person.user_defined_fields == new_person.user_defined_fields

    def test_writing_a_required_udf(self, required_udf_name: UdfName, bob_the_building_manager: Person):
        assert required_udf_name.Name not in bob_the_building_manager.user_defined_fields

        with pytest.raises(MissingRequiredUserDefinedField) as ex:
            bob_the_building_manager.write()

        assert ex.value.missing_field == required_udf_name.Name

    def test_writing_an_invalid_udf(self, bob_the_building_manager: Person):
        bad_udf_name = "spaghetti"
        bob_the_building_manager.user_defined_fields[bad_udf_name] = "meatballs"

        with pytest.raises(InvalidUdfName) as ex:
            bob_the_building_manager.write()

        assert ex.value.invalid_key == bad_udf_name

    def test_removing_a_udf(self, bob_the_building_manager: Person, person_helper: PersonHelper):
        del bob_the_building_manager.user_defined_fields['ID']

        bob_the_building_manager.write()

        people = person_helper.by_name(bob_the_building_manager.first_name, bob_the_building_manager.last_name).find()
        assert len(people) == 1
        new_person = people[0]

        assert len(new_person.user_defined_fields) == 1
        assert 'ID' not in new_person.user_defined_fields

    def test_removing_a_required_udf(self, required_udf_name: UdfName, bob_the_building_manager: Person):
        assert required_udf_name.Name not in bob_the_building_manager.user_defined_fields
        bob_the_building_manager.user_defined_fields[required_udf_name.Name] = "some value"

        bob_the_building_manager.write()  # Required field is there, should write out the UDF

        del bob_the_building_manager.user_defined_fields[required_udf_name.Name]

        with pytest.raises(MissingRequiredUserDefinedField) as ex:
            bob_the_building_manager.write()

        assert ex.value.missing_field == required_udf_name.Name

    def test_writing_an_invalid_udf_select(self, bob_the_building_manager: Person):
        bob_the_building_manager.user_defined_fields["Fruit"] = "Ketchup"

        # This works without exception because the Fruit isn't ComboOnly
        bob_the_building_manager.write()

    def test_writing_an_invalid_udf_select_combo_only(self,
                                                      bob_the_building_manager: Person,
                                                      fruit_combo_only: UdfName):
        bob_the_building_manager.user_defined_fields["Fruit"] = "Ketchup"

        with pytest.raises(InvalidUdfSelection) as ex:
            bob_the_building_manager.write()

        assert ex.value.invalid_key == "Fruit"
        assert ex.value.invalid_value == "Ketchup"

    def test_writing_an_valid_udf_select_combo_only(self, bob_the_building_manager: Person, fruit_combo_only: UdfName):
        bob_the_building_manager.user_defined_fields["Fruit"] = "Pear"

        # This works without exception because the Fruit is a valid combo fruit
        bob_the_building_manager.write()

    # TODO Tests
    # - Explicit lookups for bad location groups (udf, udf sel, udf name, company, name, card)
    #  - Writing a name needs to look up location group?
    # - Lookup by company (we would need to make a first class object)
    # - Lookup on UdfSel where ComboOnly is set and UdfSel value isn't valid?
