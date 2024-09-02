from typing import Optional

from card_auto_add.windsx.db.company import Company
from card_auto_add.windsx.db.connection.connection import Connection


class FieldValueInvalid(Exception):
    def __init__(self, message: str, field_name: str):
        super().__init__(message)
        self._field_name = field_name

    @property
    def field_name(self) -> str:
        return self._field_name


class Name:
    def __init__(self,
                 connection: Connection,
                 location_group_id: int,
                 name_id: int
                 ):
        self._connection: Connection = connection
        self._location_group_id = location_group_id
        self._name_id = name_id
        self._first_name: Optional[str] = None
        self._last_name: Optional[str] = None
        self._company_id: Optional[int] = None
        self._company: Optional[Company] = None
        self._in_db: Optional[bool] = None

    @property
    def id(self) -> int:
        return self._name_id

    @property
    def first_name(self) -> str:
        if self._first_name is None:
            self._populate_from_db()

        return self._first_name

    @first_name.setter
    def first_name(self, value: str):
        if self.in_db:
            if len(value) == 0:
                raise FieldValueInvalid("first_name field cannot be empty", "first_name")

            self._connection.execute(
                "UPDATE NAMES SET FName = ? WHERE ID = ?",
                value, self._name_id
            )

        self._first_name = value

    @property
    def last_name(self) -> str:
        if self._last_name is None:
            self._populate_from_db()

        return self._last_name

    @last_name.setter
    def last_name(self, value: str):
        if self.in_db:
            if len(value) == 0:
                raise FieldValueInvalid("last_name field cannot be empty", "last_name")

            self._connection.execute(
                "UPDATE NAMES SET LName = ? WHERE ID = ?",
                value, self._name_id
            )

        self._last_name = value

    @property
    def company_id(self) -> int:
        if self._company_id is None:
            self._populate_from_db()

        return self._company_id

    @company_id.setter
    def company_id(self, value: int):
        if self.in_db:
            if value == 0:
                raise FieldValueInvalid("company_id field cannot be empty", "company_id")

            self._connection.execute(
                "UPDATE NAMES SET Company = ? WHERE ID = ?",
                value, self._name_id
            )

        self._company_id = value
        # TODO self._company = None

    @property
    def company(self) -> Optional[Company]:
        if self._company is None:
            company_row = self._connection.execute(
                "SELECT ID FROM COMPANY WHERE Company = ? AND LocGrp = ?",
                self._company_id, self._location_group_id
            ).fetchone()

            if company_row is None:
                return None
            else:
                self._company = Company(self._connection, self._location_group_id, company_row[0])

        return self._company

    @company.setter
    def company(self, value: Company):
        if self.in_db:
            if not value.in_db:
                raise FieldValueInvalid("company field must be in db", "company")

            self._connection.execute(
                "UPDATE NAMES SET Company = ? WHERE ID = ?",
                value.company, self._name_id
            )

        self._company = value
        self._company_id = value.company

    @property
    def in_db(self) -> bool:
        if self._in_db is None:
            self._populate_from_db()

        return self._in_db

    def _populate_from_db(self):
        name_row = self._connection.execute(
            "SELECT FName, LName, Company FROM NAMES WHERE ID = ?",
            self._name_id
        ).fetchone()

        if name_row is None:
            self._first_name = self._first_name or ''
            self._last_name = self._last_name or ''
            self._company_id = self._company_id or 0
            self._company = None
            self._in_db = False
            return

        self._first_name = name_row[0]
        self._last_name = name_row[1]
        self._company_id = name_row[2]
        self._in_db = True

    def write(self):
        if self.in_db:
            return

        if len(self._first_name) == 0:
            raise FieldValueInvalid("Cannot insert empty first_name into the database", 'first_name')

        if len(self._last_name) == 0:
            raise FieldValueInvalid("Cannot insert empty first_name into the database", 'last_name')

        if self._company_id == 0:
            raise FieldValueInvalid("Cannot insert invalid company_id into the database", 'company_id')

        self._connection.execute(
            "INSERT INTO NAMES(LocGrp, FName, LName, Company) VALUES(?, ?, ?, ?)",
            self._location_group_id, self._first_name, self._last_name, self._company_id
        )

        self._in_db = True