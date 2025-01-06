import abc
import enum
from typing import Optional, Union, Any, Sequence

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.helpers import DbModel, guard_db_populated
from card_auto_add.windsx.db.models import NAMES, UDF, UdfName, CARDS, UdfSel


class InvalidUdfName(Exception):
    def __init__(self, message: str, invalid_udf_key: str):
        super().__init__(message)
        self.invalid_key = invalid_udf_key


class MissingRequiredUserDefinedField(Exception):
    def __init__(self, message: str, missing_field: str):
        super().__init__(message)
        self.missing_field = missing_field


class InvalidUdfSelection(Exception):
    def __init__(self, message: str, invalid_udf_key: str, invalid_value: str):
        super().__init__(message)
        self.invalid_key = invalid_udf_key
        self.invalid_value = invalid_value


class _SearchCriteria(enum.Enum):
    FIRST_NAME = enum.auto()
    LAST_NAME = enum.auto()
    UDF = enum.auto()
    CARD_CODE = enum.auto()
    COMPANY_ID = enum.auto()


class _PersonSearchBase(abc.ABC):
    def __init__(self, engine: Engine, location_group_id: int):
        self._location_group_id = location_group_id
        self._engine = engine
        self._session = Session(engine)
        self._criteria: dict[_SearchCriteria, Any] = {}
        self._udf_criteria: dict[str, str] = {}

    @abc.abstractmethod
    def _search_object(self) -> 'PersonSearch':
        # This method allows the same methods to be on PersonHelper and PersonSearch while allowing them to be chained
        # like a builder pattern and ensuring the PersonHelper can be re-used to find multiple people.
        pass

    def by_name(self, first_name: str, last_name: str) -> 'PersonSearch':
        search: PersonSearch = self._search_object()

        search._criteria[_SearchCriteria.FIRST_NAME] = first_name
        search._criteria[_SearchCriteria.LAST_NAME] = last_name

        return search

    def by_udf(self, udf_name: str, udf_text: str) -> 'PersonSearch':
        search: PersonSearch = self._search_object()

        if _SearchCriteria.UDF not in search._criteria:
            search._criteria[_SearchCriteria.UDF] = set()

        search._criteria[_SearchCriteria.UDF].add(udf_name)
        search._udf_criteria[udf_name] = udf_text

        return search

    def by_card(self, code: int) -> 'PersonSearch':
        search: PersonSearch = self._search_object()

        search._criteria[_SearchCriteria.CARD_CODE] = code

        return search

    def by_company(self, company: int) -> 'PersonSearch':
        search: PersonSearch = self._search_object()

        search._criteria[_SearchCriteria.COMPANY_ID] = company

        return search

    def __get_udf_name_ids(self) -> Optional[set[int]]:
        udf_names_and_ids = self._session.execute(
            select(UdfName.UdfNum, UdfName.Name) \
                .where(UdfName.LocGrp == self._location_group_id) \
                .where(UdfName.Name.in_(self._udf_criteria.keys()))
        ).all()

        names_to_ids = {}
        for udf_name in self._udf_criteria.keys():
            valid_rows = [r.UdfNum for r in udf_names_and_ids if r.Name == udf_name]
            if len(valid_rows) == 0:
                raise InvalidUdfName(f"User defined field \"{udf_name}\" not found in the database", udf_name)
            if len(valid_rows) > 1:
                raise Exception(
                    "More than one row found for the same UDF Name. This shouldn't be valid in the database.")

            names_to_ids[udf_name] = valid_rows[0]

        base_statement = select(NAMES.ID) \
            .join(UDF, UDF.NameID == NAMES.ID) \
            .where(UDF.LocGrp == self._location_group_id)

        name_ids_result: Optional[set[int]] = None

        # TODO test outer join on UdfSel where Combo is true?
        for udf_name, udf_text in self._udf_criteria.items():
            statement = base_statement \
                .where(UDF.UdfNum == names_to_ids[udf_name]) \
                .where(UDF.UdfText == udf_text)

            name_ids = self._session.scalars(statement).all()

            if name_ids_result is None:
                name_ids_result = set(name_ids)
            else:
                name_ids_result = name_ids_result.intersection(name_ids)

        return name_ids_result

    def find(self) -> list['Person']:
        statement = select(NAMES.ID) \
            .where(NAMES.LocGrp == self._location_group_id)

        criteria_key: _SearchCriteria
        for criteria_key, criteria in self._criteria.items():
            if criteria_key == _SearchCriteria.FIRST_NAME:
                statement = statement.where(NAMES.FName == criteria)
            elif criteria_key == _SearchCriteria.LAST_NAME:
                statement = statement.where(NAMES.LName == criteria)
            elif criteria_key == _SearchCriteria.UDF:
                udf_name_ids = self.__get_udf_name_ids()
                if udf_name_ids is not None:
                    statement = statement.where(NAMES.ID.in_(udf_name_ids))
            elif criteria_key == _SearchCriteria.CARD_CODE:
                statement = statement.join(CARDS, CARDS.NameID == NAMES.ID) \
                    .where(CARDS.Code == criteria) \
                    .where(CARDS.LocGrp == self._location_group_id)
            elif criteria_key == _SearchCriteria.COMPANY_ID:
                statement = statement.where(NAMES.Company == criteria)
            else:
                raise Exception("Unknown search criteria")

        name_ids = self._session.scalars(statement).all()

        return [Person(self._engine, self._location_group_id, name_id) for name_id in name_ids]


class PersonSearch(_PersonSearchBase):
    def _search_object(self) -> 'PersonSearch':
        return self


class PersonHelper(_PersonSearchBase):
    def __init__(self, engine: Engine, location_group_id: int):
        super().__init__(engine, location_group_id)

    def _search_object(self) -> 'PersonSearch':
        return PersonSearch(self._engine, self._location_group_id)

    def new(self) -> 'Person':
        return Person(
            self._engine,
            self._location_group_id,
            0
        )


class Person(DbModel):
    def __init__(self,
                 engine: Engine,
                 location_group_id: int,
                 name_id: int):
        super().__init__()
        self._location_group_id = location_group_id
        self._engine = engine
        self._session = Session(engine)
        self._name_id: int = name_id
        self._first_name: Optional[str] = None
        self._last_name: Optional[str] = None
        self._company_id: Optional[int] = None
        self._user_defined_fields: Optional[dict[str, str]] = None

    @property
    @guard_db_populated
    def id(self) -> int:
        return self._name_id

    @property
    @guard_db_populated
    def first_name(self) -> Optional[str]:
        return self._first_name

    @first_name.setter
    @guard_db_populated
    def first_name(self, value: str):
        self._first_name = value

    @property
    @guard_db_populated
    def last_name(self) -> Optional[str]:
        return self._last_name

    @last_name.setter
    @guard_db_populated
    def last_name(self, value: str):
        self._last_name = value

    @property
    @guard_db_populated
    def company_id(self) -> Optional[int]:
        return self._company_id

    @company_id.setter
    @guard_db_populated
    def company_id(self, value: int):
        self._company_id = value

    @property
    @guard_db_populated
    def user_defined_fields(self) -> Optional[dict[str, str]]:
        return self._user_defined_fields

    def _populate_from_db(self):
        if self._name_id == 0:
            self._user_defined_fields = {}
            self._in_db = False
            return

        name: Optional[NAMES] = self._session.scalar(select(NAMES).where(NAMES.ID == self._name_id))

        # TODO check name not found

        self._first_name = name.FName
        self._last_name = name.LName
        self._company_id = name.Company

        user_defined_fields = self._session.execute(
            select(UdfName.Name, UDF.UdfText)
            .join(UDF, UDF.UdfNum == UdfName.UdfNum) \
            .where(UdfName.LocGrp == self._location_group_id) \
            .where(UDF.LocGrp == self._location_group_id) \
            .where(UDF.NameID == name.ID)
        ).all()

        self._user_defined_fields = {}
        for name, value in user_defined_fields:
            self._user_defined_fields[name] = value

        self._in_db = True

    def write(self):
        name: Optional[NAMES] = self._session.scalar(
            select(NAMES).where(NAMES.ID == self._name_id)
        )

        if name is None:
            name = NAMES(
                LocGrp=self._location_group_id,
            )

        name.FName = self._first_name
        name.LName = self._last_name
        name.Company = self._company_id

        self._session.add(name)
        self._session.commit()
        # noinspection PyTypeChecker
        self._name_id: int = name.ID

        known_udf_names: Sequence[UdfName] = self._session.scalars(
            select(UdfName).where(UdfName.LocGrp == self._location_group_id)
        ).all()
        udf_selection_options: dict[str, set[str]] = {}
        udf_name: UdfName
        for udf_name in known_udf_names:
            if not udf_name.Combo:
                continue

            if not udf_name.ComboOnly:
                continue

            udf_selection_options[udf_name.Name] = set(self._session.scalars(
                select(UdfSel.SelText) \
                    .where(UdfSel.UdfNum == udf_name.UdfNum) \
                    .where(UdfSel.LocGrp == self._location_group_id)
            ).all())

        known_udfs: Sequence[UDF] = self._session.scalars(
            select(UDF) \
                .where(UDF.NameID == self._name_id) \
                .where(UDF.LocGrp == self._location_group_id) \
                .where(UDF.UdfNum.in_([n.UdfNum for n in known_udf_names]))
        ).all()
        id_to_udf: dict[int, UDF] = {}
        for udf in known_udfs:
            id_to_udf[udf.UdfNum] = udf

        user_defined_fields_copy = dict(self._user_defined_fields)
        for udf_name in known_udf_names:
            udf_name_str: str = udf_name.Name
            udf_num: int = udf_name.UdfNum

            if udf_num in id_to_udf:
                udf: UDF = id_to_udf[udf_num]
            else:
                udf: UDF = UDF(
                    UdfNum=udf_num,
                    NameID=self._name_id,
                    LocGrp=self._location_group_id,
                )

            if udf_name_str in user_defined_fields_copy:
                udf_text = user_defined_fields_copy[udf_name_str]

                if udf_name_str in udf_selection_options and udf_text not in udf_selection_options[udf_name_str]:
                    # ComboOnly and this isn't a valid value
                    raise InvalidUdfSelection(
                        f"{udf_text} is not a valid option for the UDF {udf_name_str}",
                        invalid_udf_key=udf_name_str,
                        invalid_value=udf_text
                    )

                udf.UdfText = udf_text
                del user_defined_fields_copy[udf_name_str]
                self._session.add(udf)
            elif udf_name.Required:
                raise MissingRequiredUserDefinedField(
                    f"Required user defined field {udf_name_str} not found.",
                    udf_name_str
                )
            elif udf.ID is not None:  # Is it even in the database?
                self._session.delete(udf)

        # Did we have any keys we couldn't write out?
        if len(user_defined_fields_copy) > 0:
            invalid_key = list(user_defined_fields_copy.keys())[0]
            raise InvalidUdfName(
                f"User Defined Field {invalid_key} cannot be written because it is not defined in the database.",
                invalid_key
            )

        self._session.commit()
        # self._in_db = True
