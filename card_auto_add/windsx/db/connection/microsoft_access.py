from typing import Iterable, Any, Optional

import pyodbc
from pathlib import Path

from sqlalchemy import URL, create_engine

from card_auto_add.windsx.db.connection.connection import Connection


class MicrosoftAccessDatabaseConnection(Connection):
    def __init__(self, db_path: Path):
        connection_string = (
                r'DRIVER={Microsoft Access Driver (*.mdb)};'
                r"ExtendedAnsiSQL=1;"
                r'DBQ=' + str(db_path) + ";"
        )
        connection_url = URL.create(
            "access+pyodbc",
            query={"odbc_connect": connection_string}
        )
        engine = create_engine(connection_url)
        super().__init__(engine)

        connection = pyodbc.connect(
            connection_string,
            autocommit=True
        )
        self._cursor = connection.cursor()

    def execute(self, sql, *params) -> pyodbc.Cursor:
        return self._cursor.execute(sql, params)

    def executemany(self, sql, params: Iterable[Any]) -> None:
        self._cursor.execute(sql, params)

    @property
    def last_row_id(self) -> Optional[int]:
        return self._cursor.execute("SELECT @@IDENTITY").fetchval()

    def __enter__(self) -> 'MicrosoftAccessDatabaseConnection':
        new_result = MicrosoftAccessDatabaseConnection.__new__(MicrosoftAccessDatabaseConnection)
        new_result._cursor = self._cursor.connection.cursor()  # Create a new cursor for our scoped connection
        return new_result
