import abc
from functools import wraps
from typing import Optional, Callable, Any

from sqlalchemy import Engine


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


class LookupInfo:
    """
    All of our lookup classes require the same set of information, and they pass that information down to their first
    class objects. It's easier to store all of that information here than it is to pass each item individually.
    """

    def __init__(self,
                 acs_engine: Engine,
                 location_group_id: int,
                 updated_callback: Callable[[Any], None]
                 ):
        self._acs_engine = acs_engine
        self._location_group_id = location_group_id
        self._updated_callback = updated_callback

    @property
    def acs_engine(self) -> Engine:
        return self._acs_engine

    @property
    def location_group_id(self) -> int:
        return self._location_group_id

    @property
    def updated_callback(self) -> Callable[[Any], None]:
        return self._updated_callback
