import abc
from functools import wraps
from typing import Optional


def guard_db_populated(func):
    @wraps(func)
    def inner(self: 'DbModel', *args):
        if self._in_db is None:
            self._populate_from_db()

        return func(self, *args)

    return inner


class DbModel(abc.ABC):
    def __init__(self):
        self._in_db: Optional[bool] = None

    @abc.abstractmethod
    def _populate_from_db(self):
        pass

    @property
    @guard_db_populated
    def in_db(self) -> bool:
        return self._in_db
