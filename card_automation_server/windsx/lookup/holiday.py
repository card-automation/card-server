from datetime import date, datetime
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import HOL, LOC
from card_automation_server.windsx.lookup.utils import LookupInfo


class HolidayNotInDatabase(Exception):
    pass


class NoLocationsInGroup(Exception):
    pass


class HolidayDateConflict(Exception):
    pass


class NoFreeHolidaySlotError(Exception):
    pass


class HolidayLookup:
    def __init__(self, lookup_info: LookupInfo):
        self._lookup_info: LookupInfo = lookup_info
        self._base_statement = (
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == lookup_info.location_group_id)
        )

    def new(self) -> "Holiday":
        return _Holiday(self._lookup_info)

    def all(self) -> list["Holiday"]:
        return self._collect(self._base_statement)

    def by_date(self, holiday_date: date) -> Optional["Holiday"]:
        target_dt = datetime.combine(holiday_date, datetime.min.time())
        results = self._collect(self._base_statement.where(HOL.HolDate == target_dt))
        return results[0] if results else None

    def by_slot(self, slot: int) -> list["Holiday"]:
        return self._collect(self._base_statement.where(HOL.Type == slot))

    def allocate(self,
                 holiday_date: date,
                 name: str,
                 *,
                 notes: str = "",
                 recurring: bool = False) -> "Holiday":
        target_dt = datetime.combine(holiday_date, datetime.min.time())
        today_dt = datetime.combine(date.today(), datetime.min.time())

        with self._lookup_info.new_session() as session:
            existing = session.scalar(
                self._base_statement.where(HOL.HolDate == target_dt)
            )
            if existing is not None:
                raise HolidayDateConflict(
                    f"A holiday already exists on {holiday_date.isoformat()} in slot {existing.Type}"
                )

            chosen_slot: Optional[int] = None
            for slot in (1, 2, 3):
                blocker = session.scalar(
                    self._base_statement
                        .where(HOL.Type == slot)
                        .where(HOL.HolDate >= today_dt)
                )
                if blocker is None:
                    chosen_slot = slot
                    break

            if chosen_slot is None:
                raise NoFreeHolidaySlotError(
                    "All three holiday slots are occupied by future-dated entries"
                )

        holiday = _Holiday(
            self._lookup_info,
            holiday_date=holiday_date,
            slot=chosen_slot,
            name=name,
            notes=notes,
            recurring=recurring,
        )
        holiday.write()
        return holiday

    def _collect(self, statement) -> list["Holiday"]:
        with self._lookup_info.new_session() as session:
            rows = list(session.scalars(statement).all())

        # Each (HolDate) maps to one logical Holiday spanning every Loc in the group.
        by_date: dict[datetime, list[HOL]] = {}
        for row in rows:
            by_date.setdefault(row.HolDate, []).append(row)

        return [
            _Holiday(
                self._lookup_info,
                holiday_date=hol_dt.date(),
                slot=group[0].Type,
                name=group[0].Name,
                notes=group[0].Notes,
                recurring=bool(group[0].ReOccurring),
                in_db=True,
            )
            for hol_dt, group in sorted(by_date.items())
        ]


class _Holiday:
    def __init__(self,
                 lookup_info: LookupInfo,
                 holiday_date: Optional[date] = None,
                 slot: Optional[int] = None,
                 name: Optional[str] = None,
                 notes: str = "",
                 recurring: bool = False,
                 in_db: bool = False):
        self._lookup_info: LookupInfo = lookup_info
        self._location_group_id: int = lookup_info.location_group_id
        self._date: Optional[date] = holiday_date
        self._slot: Optional[int] = slot
        self._name: Optional[str] = name
        self._notes: str = notes
        self._recurring: bool = recurring
        self._in_db: bool = in_db
        self._original_date: Optional[date] = holiday_date if in_db else None

    @property
    def in_db(self) -> bool:
        return self._in_db

    @property
    def date(self) -> Optional[date]:
        return self._date

    @date.setter
    def date(self, value: date):
        self._date = value

    @property
    def slot(self) -> Optional[int]:
        return self._slot

    @slot.setter
    def slot(self, value: int):
        self._slot = value

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
    def recurring(self) -> bool:
        return self._recurring

    @recurring.setter
    def recurring(self, value: bool):
        self._recurring = value

    def _locations(self, session: Session) -> list[LOC]:
        return list(session.scalars(
            select(LOC).where(LOC.LocGrp == self._location_group_id)
        ).all())

    def write(self):
        if self._date is None:
            raise Exception("Holiday requires a date before write")
        if self._slot is None:
            raise Exception("Holiday requires a slot before write")
        if self._name is None:
            raise Exception("Holiday requires a name before write")

        target_dt = datetime.combine(self._date, datetime.min.time())
        original_dt = (
            datetime.combine(self._original_date, datetime.min.time())
            if self._original_date is not None
            else None
        )

        with self._lookup_info.new_session() as session:
            locations = self._locations(session)
            if not locations:
                raise NoLocationsInGroup(
                    f"Location group {self._location_group_id} has no locations to write a holiday to"
                )

            for location in locations:
                hol: Optional[HOL] = None
                if original_dt is not None:
                    hol = session.scalar(
                        select(HOL)
                        .where(HOL.Loc == location.Loc)
                        .where(HOL.HolDate == original_dt)
                    )

                if hol is None:
                    hol = HOL(Loc=location.Loc, HolDate=target_dt)
                else:
                    hol.HolDate = target_dt

                hol.Type = self._slot
                hol.Name = self._name
                hol.Notes = self._notes
                hol.ReOccurring = self._recurring
                hol.DlFlag = 1
                hol.CkSum = 0
                session.add(hol)

                location.DlFlag = 1
                location.HolCs = 0
                location.PlFlag = True
                session.add(location)

            session.commit()

        self._in_db = True
        self._original_date = self._date
        self._lookup_info.updated_callback(self)

    def delete(self):
        if not self._in_db or self._original_date is None:
            raise HolidayNotInDatabase("Cannot delete a Holiday that is not in the database")

        original_dt = datetime.combine(self._original_date, datetime.min.time())

        with self._lookup_info.new_session() as session:
            locations = self._locations(session)
            for location in locations:
                hol = session.scalar(
                    select(HOL)
                    .where(HOL.Loc == location.Loc)
                    .where(HOL.HolDate == original_dt)
                )
                if hol is not None:
                    session.delete(hol)

                location.DlFlag = 2
                location.HolCs = 0
                location.PlFlag = True
                session.add(location)

            session.commit()

        self._in_db = False
        self._original_date = None
        self._lookup_info.updated_callback(self)


class _Unused:
    pass


Holiday = Union[_Holiday, _Unused]
