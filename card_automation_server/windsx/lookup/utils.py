from typing import Callable, Any

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from card_automation_server.windsx.engines import AcsEngine


class LookupInfo:
    """
    All of our lookup classes require the same set of information, and they pass that information down to their first
    class objects. It's easier to store all of that information here than it is to pass each item individually.
    """

    def __init__(self,
                 acs_engine: AcsEngine,
                 location_group_id: int,
                 updated_callback: Callable[[Any], None]
                 ):
        self._acs_engine: Engine = acs_engine
        self._location_group_id = location_group_id
        self._updated_callback = updated_callback

    def new_session(self) -> Session:
        return Session(self._acs_engine)

    @property
    def acs_engine(self) -> Engine:
        return self._acs_engine

    @property
    def location_group_id(self) -> int:
        return self._location_group_id

    @property
    def updated_callback(self) -> Callable[[Any], None]:
        return self._updated_callback
