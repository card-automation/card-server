import sqlite3
from pathlib import Path
from sqlite3 import Cursor
from typing import Union, Any, Iterable, Optional

from card_auto_add.windsx.db.connection.connection import Connection


class SqliteConnection(Connection):
    def __init__(self, db_path: Union[str, Path]):
        connection = sqlite3.connect(db_path)
        connection.autocommit = True
        self._cursor = connection.cursor()

    def execute(self, sql, *params) -> Cursor:
        return self._cursor.execute(sql, params)

    def executemany(self, sql, params: Iterable[Any]) -> None:
        self._cursor.executemany(sql, params)

    @property
    def last_row_id(self) -> Optional[int]:
        return self._cursor.lastrowid

    def __enter__(self) -> 'SqliteConnection':
        new_result = SqliteConnection.__new__(SqliteConnection)
        new_result._cursor = self._cursor.connection.cursor()
        return new_result
