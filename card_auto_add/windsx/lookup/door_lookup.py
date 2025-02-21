from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import DEV, LOC
from card_auto_add.windsx.lookup.utils import LookupInfo, DbModel
from card_auto_add.workers.events import DoorStateUpdate, DoorState


class DoorLookup:
    def __init__(self,
                 lookup_info: LookupInfo,
                 *door_ids: int):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = lookup_info.location_group_id
        self._session = Session(lookup_info.acs_engine)
        self._door_ids = list(door_ids)

    def all(self) -> list['Door']:
        statement = (
            select(DEV)
            .join(LOC, LOC.Loc == DEV.Loc)
            .where(LOC.LocGrp == self._location_group_id)
        )
        if len(self._door_ids) > 0:
            statement = statement.where(DEV.ID.in_(self._door_ids))

        dev = self._session.scalars(statement).all()
        return [Door(self._lookup_info, d.ID) for d in dev]

    def by_id(self, id_: int) -> Optional['Door']:
        doors = [d for d in self.all() if d.id == id_]

        if len(doors) == 0:
            return None

        return doors[0]

    def by_device_info(self, location_id: int, device_id: int) -> Optional['Door']:
        doors = [
            d for d in self.all()
            if d.location_id == location_id and d.device_id == device_id
        ]

        if len(doors) == 0:
            return None

        return doors[0]


class Door(DbModel):
    def __init__(self,
                 lookup_info: LookupInfo,
                 dev_id: int):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = lookup_info.location_group_id
        self._session = Session(lookup_info.acs_engine)
        self._id = dev_id
        self._name: Optional[str] = None
        self._device_id: Optional[int] = None
        self._location_id: Optional[int] = None
        super().__init__()

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

    def _populate_from_db(self):
        dev: DEV = self._session.scalar(
            select(DEV)
            .join(LOC, LOC.Loc == DEV.Loc)
            .where(LOC.LocGrp == self._location_group_id)
            .where(DEV.ID == self._id)
        )

        self._name = dev.Name
        self._device_id = dev.Device
        self._location_id = dev.Loc
        self._in_db = True

    def open(self, timeout: Optional[int] = None):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            device_id=self.device_id,
            state=DoorState.OPEN,
            timeout=timeout
        ))

    def secure(self, timeout: Optional[int] = None):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            device_id=self.device_id,
            state=DoorState.SECURE,
            timeout=timeout
        ))

    def timezone(self):
        self._lookup_info.updated_callback(DoorStateUpdate(
            location_id=self.location_id,
            device_id=self.device_id,
            state=DoorState.TIMEZONE,
            timeout=None
        ))