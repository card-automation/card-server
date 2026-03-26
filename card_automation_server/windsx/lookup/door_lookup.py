from datetime import timedelta
from typing import Optional

from sqlalchemy import select

from card_automation_server.plugins.types import CardScan
from card_automation_server.windsx.db.models import DEV, LOC
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.events import DoorStateUpdate, DoorState


class DoorLookup:
    def __init__(self,
                 lookup_info: LookupInfo,
                 *door_ids: int):
        self._lookup_info: LookupInfo = lookup_info
        self._base_statement = (
            select(DEV)
            .join(LOC, LOC.Loc == DEV.Loc)
            .where(LOC.LocGrp == lookup_info.location_group_id)
        )

        if door_ids:
            self._base_statement = self._base_statement.where(DEV.ID.in_(door_ids))

    def all(self) -> list['Door']:
        with self._lookup_info.new_session() as session:
            devs = session.scalars(self._base_statement).all()
            return [Door(self._lookup_info, d.ID, d.Name, d.Device, d.Loc) for d in devs]

    def by_id(self, id_: int) -> Optional['Door']:
        statement = self._base_statement.where(DEV.ID == id_)

        with self._lookup_info.new_session() as session:
            dev = session.scalar(statement)
            return Door(self._lookup_info, dev.ID, dev.Name, dev.Device, dev.Loc) if dev is not None else None

    def by_device_info(self, location_id: int, device_id: int) -> Optional['Door']:
        statement = (
            self._base_statement
            .where(DEV.Loc == location_id)
            .where(DEV.Device == device_id)
        )

        with self._lookup_info.new_session() as session:
            dev = session.scalar(statement)
            return Door(self._lookup_info, dev.ID, dev.Name, dev.Device, dev.Loc) if dev is not None else None

    def by_card_scan(self, card_scan: CardScan) -> Optional['Door']:
        statement = (
            self._base_statement
            .where(DEV.Loc == card_scan.location_id)
            .where(DEV.Device == card_scan.device)
        )

        with self._lookup_info.new_session() as session:
            dev = session.scalar(statement)
            return Door(self._lookup_info, dev.ID, dev.Name, dev.Device, dev.Loc) if dev is not None else None


class Door:
    def __init__(self,
                 lookup_info: LookupInfo,
                 dev_id: int,
                 name: str,
                 device_id: int,
                 location_id: int):
        self._lookup_info: LookupInfo = lookup_info
        self._id = dev_id
        self._name: str = name
        self._device_id: int = device_id
        self._location_id: int = location_id

    @property
    def in_db(self) -> bool:
        return True

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def device_id(self) -> int:
        return self._device_id

    @property
    def location_id(self) -> int:
        return self._location_id

    def open(self, timeout: Optional[timedelta] = None):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            door_number=self.device_id,
            state=DoorState.OPEN,
            timeout=timeout
        ))

    def secure(self, timeout: Optional[timedelta] = None):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            door_number=self.device_id,
            state=DoorState.SECURE,
            timeout=timeout
        ))

    def timezone(self):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            door_number=self.device_id,
            state=DoorState.TIMEZONE,
            timeout=None
        ))
