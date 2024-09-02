from typing import Optional

from card_auto_add.windsx.db.connection.connection import Connection


class CompanyNameCannotBeEmpty(Exception):
    pass


class Company:
    def __init__(self,
                 connection: Connection,
                 location_group_id: int,
                 company_id: int
                 ):
        self._connection: Connection = connection
        self._location_group_id = location_group_id
        self._company_id = company_id
        self._name: Optional[str] = None
        self._in_db: Optional[bool] = None

    @property
    def id(self) -> int:
        return self._company_id

    @property
    def name(self) -> str:
        if self._name is None:
            self._populate_from_db()

        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if self.in_db:
            if len(value) == 0:
                raise CompanyNameCannotBeEmpty("Cannot update the company name to be empty in the database")

            self._connection.execute(
                "UPDATE COMPANY SET Name = ? WHERE Company = ?",
                value, self._company_id
            )

        self._name = value

    @property
    def in_db(self) -> bool:
        if self._in_db is None:
            self._populate_from_db()

        return self._in_db

    def _populate_from_db(self):
        company_row = self._connection.execute(
            "SELECT Name FROM COMPANY WHERE Company = ?",
            self._company_id
        ).fetchone()

        if company_row is None:
            self._name = self._name or ''
            self._in_db = False
        else:
            self._name = company_row[0]
            self._in_db = True

    def write(self):
        if self.in_db:
            return

        if len(self._name) == 0:
            raise CompanyNameCannotBeEmpty("Cannot insert empty company name into the database")

        existing_company_rows = self._connection.execute("SELECT Company FROM COMPANY").fetchall()
        self._company_id = max([int(row[0]) for row in existing_company_rows]) + 1

        self._connection.execute(
            "INSERT INTO COMPANY(LocGrp, Company, Name) VALUES(?, ?, ?)",
            self._location_group_id, self._company_id, self._name
        )

        self._in_db = True
