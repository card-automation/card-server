from typing import Optional

from card_auto_add.windsx.db.connection.connection import Connection
from card_auto_add.windsx.db.model import FieldValueInvalid


class Company:
    def __init__(self,
                 connection: Connection,
                 location_group_id: int,
                 id: int
                 ):
        self._connection: Connection = connection
        self._location_group_id = location_group_id
        self._id = id
        self._company_id: Optional[int] = None
        self._name: Optional[str] = None
        self._in_db: Optional[bool] = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        if self._name is None:
            self._populate_from_db()

        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if self.in_db:
            if len(value) == 0:
                raise FieldValueInvalid("Cannot update the company name to be empty in the database", "name")

            self._connection.execute(
                "UPDATE COMPANY SET Name = ? WHERE ID = ?",
                value, self._id
            )

        self._name = value

    @property
    def company(self) -> int:
        if self._company_id is None:
            self._populate_from_db()

        return self._company_id

    @company.setter
    def company(self, value: int) -> None:
        if self.in_db:
            if value == 0:
                raise FieldValueInvalid("Cannot update the company to be empty in the database", "name")

            self._connection.execute(
                "UPDATE COMPANY SET Company = ? WHERE ID = ?",
                value, self._id
            )

        self._company_id = value

    @property
    def in_db(self) -> bool:
        if self._in_db is None:
            self._populate_from_db()

        return self._in_db

    def _populate_from_db(self):
        company_row = self._connection.execute(
            "SELECT Name, Company FROM COMPANY WHERE ID = ?",
            self._id
        ).fetchone()

        if company_row is None:
            self._name = self._name or ''
            self._company_id = self._company_id or 0
            self._in_db = False
        else:
            self._name = company_row[0]
            self._company_id = company_row[1]
            self._in_db = True

    def write(self):
        if self.in_db:
            return

        if len(self._name) == 0:
            raise FieldValueInvalid("Cannot insert empty company name into the database", "name")

        existing_company_rows = self._connection.execute("SELECT Company FROM COMPANY").fetchall()
        self._company_id = max([int(row[0]) for row in existing_company_rows]) + 1

        with self._connection as conn:
            conn.execute(
                "INSERT INTO COMPANY(LocGrp, Company, Name) VALUES(?, ?, ?)",
                self._location_group_id, self._company_id, self._name
            )

            self._id = conn.last_row_id

        self._in_db = True
