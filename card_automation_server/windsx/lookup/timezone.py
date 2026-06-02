from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import LOC, TZ
from card_automation_server.windsx.lookup.utils import LookupInfo


class NoLocationsInGroup(Exception):
    pass


_DAY_HOLIDAY_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("sun", "SunStart", "SunStop"),
    ("mon", "MonStart", "MonStop"),
    ("tue", "TueStart", "TueStop"),
    ("wed", "WedStart", "WedStop"),
    ("thu", "ThuStart", "ThuStop"),
    ("fri", "FriStart", "FriStop"),
    ("sat", "SatStart", "SatStop"),
    ("hol1", "Hol1Start", "Hol1Stop"),
    ("hol2", "Hol2Start", "Hol2Stop"),
    ("hol3", "Hol3Start", "Hol3Stop"),
)


class _StartStop:
    def __init__(self, start: int = 0, stop: int = 0):
        self._start: int = start
        self._stop: int = stop

    @property
    def start(self) -> int:
        return self._start

    @start.setter
    def start(self, value: int):
        self._start = value

    @property
    def stop(self) -> int:
        return self._stop

    @stop.setter
    def stop(self, value: int):
        self._stop = value


class TimezoneLookup:
    def __init__(self, lookup_info: LookupInfo):
        self._lookup_info: LookupInfo = lookup_info
        self._base_statement = (
            select(TZ)
            .join(LOC, LOC.Loc == TZ.Loc)
            .where(LOC.LocGrp == lookup_info.location_group_id)
        )

    def new(self) -> "Timezone":
        return _Timezone(self._lookup_info)

    def all(self) -> list["Timezone"]:
        return self._collect(self._base_statement)

    def by_tz(self, tz_number: int) -> Optional["Timezone"]:
        results = self._collect(self._base_statement.where(TZ.TZ == tz_number))
        return results[0] if results else None

    def by_name(self, name: str) -> list["Timezone"]:
        return self._collect(self._base_statement.where(TZ.Name == name))

    def _collect(self, statement) -> list["Timezone"]:
        with self._lookup_info.new_session() as session:
            rows = list(session.scalars(statement).all())

        # Each TZ number maps to one logical Timezone spanning every Loc in the group.
        by_tz: dict[int, list[TZ]] = {}
        for row in rows:
            by_tz.setdefault(row.TZ, []).append(row)

        result: list["Timezone"] = []
        for tz_number, group in sorted(by_tz.items()):
            row = group[0]
            tz = _Timezone(
                self._lookup_info,
                tz_number=tz_number,
                name=row.Name,
                notes=row.Notes,
                in_db=True,
            )
            for field_name, start_col, stop_col in _DAY_HOLIDAY_FIELDS:
                sub: _StartStop = getattr(tz, field_name)
                sub.start = getattr(row, start_col)
                sub.stop = getattr(row, stop_col)
            result.append(tz)
        return result


class _Timezone:
    def __init__(self,
                 lookup_info: LookupInfo,
                 tz_number: Optional[int] = None,
                 name: Optional[str] = None,
                 notes: str = "",
                 in_db: bool = False):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = lookup_info.location_group_id
        self._tz_number: Optional[int] = tz_number
        self._name: Optional[str] = name
        self._notes: str = notes
        self._in_db: bool = in_db
        self._sun = _StartStop()
        self._mon = _StartStop()
        self._tue = _StartStop()
        self._wed = _StartStop()
        self._thu = _StartStop()
        self._fri = _StartStop()
        self._sat = _StartStop()
        self._hol1 = _StartStop()
        self._hol2 = _StartStop()
        self._hol3 = _StartStop()

    @property
    def in_db(self) -> bool:
        return self._in_db

    @property
    def tz_number(self) -> Optional[int]:
        return self._tz_number

    @property
    def name(self) -> Optional[str]:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def notes(self) -> str:
        return self._notes

    @notes.setter
    def notes(self, value: str):
        self._notes = value

    @property
    def sun(self) -> _StartStop:
        return self._sun

    @property
    def mon(self) -> _StartStop:
        return self._mon

    @property
    def tue(self) -> _StartStop:
        return self._tue

    @property
    def wed(self) -> _StartStop:
        return self._wed

    @property
    def thu(self) -> _StartStop:
        return self._thu

    @property
    def fri(self) -> _StartStop:
        return self._fri

    @property
    def sat(self) -> _StartStop:
        return self._sat

    @property
    def hol1(self) -> _StartStop:
        return self._hol1

    @property
    def hol2(self) -> _StartStop:
        return self._hol2

    @property
    def hol3(self) -> _StartStop:
        return self._hol3

    def _locations(self, session: Session) -> list[LOC]:
        return list(session.scalars(
            select(LOC).where(LOC.LocGrp == self._location_group_id)
        ).all())

    def _next_free_tz_number(self, session: Session) -> int:
        max_tz = session.scalar(
            select(TZ.TZ)
            .join(LOC, LOC.Loc == TZ.Loc)
            .where(LOC.LocGrp == self._location_group_id)
            .order_by(TZ.TZ.desc())
            .limit(1)
        )
        return (max_tz or 0) + 1

    def write(self):
        if self._name is None:
            raise Exception("Timezone requires a name before write")

        with self._lookup_info.new_session() as session:
            locations = self._locations(session)
            if not locations:
                raise NoLocationsInGroup(
                    f"Location group {self._location_group_id} has no locations to write a timezone to"
                )

            tz_number = self._tz_number
            if tz_number is None:
                tz_number = self._next_free_tz_number(session)

            for location in locations:
                row: Optional[TZ] = session.scalar(
                    select(TZ)
                    .where(TZ.Loc == location.Loc)
                    .where(TZ.TZ == tz_number)
                )
                if row is None:
                    row = TZ(Loc=location.Loc, TZ=tz_number)

                row.Name = self._name
                row.Notes = self._notes
                for field_name, start_col, stop_col in _DAY_HOLIDAY_FIELDS:
                    sub: _StartStop = getattr(self, field_name)
                    setattr(row, start_col, sub.start)
                    setattr(row, stop_col, sub.stop)
                row.DlFlag = 1
                row.CkSum = 0
                session.add(row)

                location.DlFlag = 1
                location.TzCs = 0
                location.PlFlag = True
                session.add(location)

            session.commit()

        self._tz_number = tz_number
        self._in_db = True
        self._lookup_info.updated_callback(self)


class _Unused:
    pass


Timezone = Union[_Timezone, _Unused]
