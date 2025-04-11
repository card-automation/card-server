import abc
import enum
import typing
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, Union

from card_automation_server.plugins.types import CardScan, CommServerMessageType, CommServerEventType
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
    door_number: int
    state: DoorState
    timeout: Optional[timedelta]


class ApplicationRestartNeeded(WorkerEvent):
    pass


class MessageParseException(Exception):
    pass


class RawCommServerEvent(WorkerEvent):
    def __init__(self, data: list[Union[int, str]]):
        self._data = data

    @property
    def data(self):
        return self._data

    @property
    def timestamp(self) -> datetime:
        return datetime(
            year=self.data[10],
            month=self.data[11],
            day=self.data[12],
            hour=self.data[13],
            minute=self.data[14],
            second=self.data[15],
        )

    @property
    def type(self) -> CommServerEventType:
        return CommServerEventType(self.data[6])

    def is_any_event(self, *event_types: CommServerEventType) -> bool:
        event_types = list(self._unwrap_nested_event_types(list(event_types)))

        for _type in event_types:
            if self._data[6] == _type:
                return True

        return False

    @staticmethod
    def _unwrap_nested_event_types(event_types: list[CommServerEventType]):
        for _type in event_types:
            could_not_handle = False

            if isinstance(_type, CommServerEventType):
                yield _type
            elif hasattr(_type, "__origin__") and hasattr(_type, "__args__"):
                origin = _type.__origin__
                args = _type.__args__

                if origin == typing.Literal:
                    for arg in args:
                        yield arg
                else:
                    could_not_handle = True
            else:
                could_not_handle = True

            if could_not_handle:
                raise Exception(f"Unsure how to handle event type: {type(_type)}")


class RawCommServerMessage(WorkerEvent):
    def __init__(self, data: list[Union[int, str]]):
        self._data = data

    @staticmethod
    def parse(packet: str) -> 'RawCommServerMessage':
        packet = packet.strip()
        if len(packet) == 0:
            raise MessageParseException("Cannot parse empty string")

        if '*' in packet:
            star_index = packet.index('*')
            left = packet[:star_index].strip(' ')
            right = packet[star_index + 1:].strip(' ')
        else:
            left, right = packet, None

        if len(left) == 0:
            raise MessageParseException("Cannot parse packet with no numeric data")

        data: list[Union[int, str]] = [int(x) for x in left.split(' ')]

        if right is not None:
            data.append(right)

        return RawCommServerMessage(data)

    @property
    def data(self):
        return self._data

    @property
    def type(self) -> int:
        return self._data[0]

    def is_type(self, _type: CommServerMessageType) -> bool:
        return self.type == _type

    @property
    def event(self) -> Optional[RawCommServerEvent]:
        if not self.is_type(CommServerMessageType.EVENT):
            return None

        return RawCommServerEvent(self._data)
