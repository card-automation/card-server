import abc
import enum
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from card_automation_server.plugins.types import CardScan
from card_automation_server.windsx.lookup.access_card import AccessCard


class WorkerEvent(abc.ABC):
    pass


class AcsDatabaseUpdated(WorkerEvent):
    pass


class LogDatabaseUpdated(WorkerEvent):
    pass


class CommServerRestartRequested(WorkerEvent):
    pass


class CardScanned(WorkerEvent):
    def __init__(self, card_scan: CardScan):
        self._card_scan = card_scan

    @property
    def card_scan(self) -> CardScan:
        return self._card_scan


class AccessCardUpdated(WorkerEvent):
    """
    This event is fired when the access card is updated in the Acs database.
    """

    def __init__(self, access_card: AccessCard):
        self._access_card = access_card

    @property
    def access_card(self) -> AccessCard:
        return self._access_card


class LocCardUpdated(WorkerEvent):
    """
    This event is fired when an LocCard entry is written. A worker listening to just AcsDatabaseUpdated might miss a
    change to the LocCards table, so this allows us to be explicit about what was changed by a plugin.
    """

    def __init__(self,
                 id: int,  # noqa
                 card_id: int,
                 location_id: int):
        self._id = id
        self._card_id = card_id
        self._location_id = location_id

    @property
    def id(self) -> int:
        return self._id

    @property
    def card_id(self) -> int:
        return self._card_id

    @property
    def location_id(self) -> int:
        return self._location_id


class AccessCardPushed(WorkerEvent):
    """
    This event is fired after the card has been written to the hardware.
    """

    def __init__(self, access_card: AccessCard):
        self._access_card = access_card

    @property
    def access_card(self) -> AccessCard:
        return self._access_card


class DoorState(enum.Enum):
    OPEN = enum.auto()
    SECURE = enum.auto()
    TIMEZONE = enum.auto()


@dataclass(frozen=True)
class DoorStateUpdate(WorkerEvent):
    location_id: int
    device_id: int
    state: DoorState
    timeout: Optional[timedelta]


class ApplicationRestartNeeded(WorkerEvent):
    pass
