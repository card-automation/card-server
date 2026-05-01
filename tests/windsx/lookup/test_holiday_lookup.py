from datetime import date, datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import HOL, LOC
from card_automation_server.windsx.lookup.holiday import (
    HolidayLookup,
    Holiday,
    HolidayDateConflict,
    HolidayNotInDatabase,
    NoFreeHolidaySlotError,
    NoLocationsInGroup,
)
from card_automation_server.windsx.lookup.utils import LookupInfo
from tests.conftest import (
    annex_location_id,
    bad_location_group,
    bad_main_location_id,
    location_group_id,
    main_location_id,
)


@pytest.fixture
def holiday_lookup(lookup_info: LookupInfo) -> HolidayLookup:
    return HolidayLookup(lookup_info)


class TestHolidayLookup:
    def test_all_returns_one_logical_entry_per_date_in_group(self, holiday_lookup: HolidayLookup):
        holidays = holiday_lookup.all()

        assert len(holidays) == 2
        dates = {h.date for h in holidays}
        assert dates == {date(2026, 7, 4), date(2026, 12, 25)}

    def test_by_date_returns_holiday_with_expected_fields(self, holiday_lookup: HolidayLookup):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))

        assert holiday is not None
        assert holiday.in_db
        assert holiday.date == date(2026, 12, 25)
        assert holiday.slot == 1
        assert holiday.name == "Christmas"
        assert holiday.notes == ""
        assert holiday.recurring is False

    def test_by_date_excludes_other_location_group(self, holiday_lookup: HolidayLookup):
        # The bad-group HOL row is on the same date with slot=3; reading from the main group must not see it.
        holiday = holiday_lookup.by_date(date(2026, 12, 25))

        assert holiday.slot == 1

    def test_by_date_returns_none_when_missing(self, holiday_lookup: HolidayLookup):
        assert holiday_lookup.by_date(date(2026, 1, 1)) is None

    def test_by_slot_returns_only_matching_slot(self, holiday_lookup: HolidayLookup):
        slot1 = holiday_lookup.by_slot(1)
        slot2 = holiday_lookup.by_slot(2)

        assert len(slot1) == 1
        assert slot1[0].name == "Christmas"
        assert len(slot2) == 1
        assert slot2[0].name == "Independence Day"

    def test_by_slot_excludes_other_location_group(self, holiday_lookup: HolidayLookup):
        # Slot 3 only exists in the bad group; main group must return empty.
        assert holiday_lookup.by_slot(3) == []


class TestHolidayWrite:
    def test_new_holiday_starts_not_in_db(self, holiday_lookup: HolidayLookup):
        holiday = holiday_lookup.new()
        assert not holiday.in_db
        assert holiday.date is None
        assert holiday.slot is None
        assert holiday.name is None

    def test_writing_a_new_holiday_inserts_a_row_per_loc_in_group(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
        acs_updated_callback: Mock,
    ):
        holiday: Holiday = holiday_lookup.new()
        holiday.date = date(2026, 5, 1)
        holiday.slot = 3
        holiday.name = "May Day Open House"
        holiday.notes = "One-off"
        holiday.recurring = False

        assert not holiday.in_db
        holiday.write()
        assert holiday.in_db

        acs_updated_callback.assert_called_once_with(holiday)

        rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime(2026, 5, 1))
        ).all()
        assert len(rows) == 2
        assert {r.Loc for r in rows} == {main_location_id, annex_location_id}
        for row in rows:
            assert row.Type == 3
            assert row.Name == "May Day Open House"
            assert row.Notes == "One-off"
            assert row.ReOccurring is False
            assert row.DlFlag == 1
            assert row.CkSum == 0

    def test_writing_a_new_holiday_bumps_loc_dirty_flags(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
    ):
        holiday: Holiday = holiday_lookup.new()
        holiday.date = date(2026, 5, 1)
        holiday.slot = 3
        holiday.name = "May Day"
        holiday.write()

        locations = acs_data_session.scalars(
            select(LOC).where(LOC.LocGrp == location_group_id)
        ).all()
        assert len(locations) == 2
        for loc in locations:
            assert loc.DlFlag == 1
            assert loc.HolCs == 0
            assert loc.PlFlag is True

    def test_writing_a_new_holiday_does_not_touch_other_groups(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
    ):
        holiday: Holiday = holiday_lookup.new()
        holiday.date = date(2026, 5, 1)
        holiday.slot = 3
        holiday.name = "May Day"
        holiday.write()

        bad_loc = acs_data_session.scalar(
            select(LOC).where(LOC.Loc == bad_main_location_id)
        )
        assert bad_loc.DlFlag == 0
        assert bad_loc.HolCs == 0
        assert bad_loc.PlFlag is False

        bad_rows = acs_data_session.scalars(
            select(HOL).where(HOL.Loc == bad_main_location_id).where(HOL.HolDate == datetime(2026, 5, 1))
        ).all()
        assert bad_rows == []

    def test_writing_an_existing_holiday_updates_in_place(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
        acs_updated_callback: Mock,
    ):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))
        holiday.name = "Christmas Day"
        holiday.notes = "Updated"
        holiday.recurring = True
        holiday.write()

        acs_updated_callback.assert_called_once_with(holiday)

        rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime(2026, 12, 25))
        ).all()
        assert len(rows) == 2
        for row in rows:
            assert row.Name == "Christmas Day"
            assert row.Notes == "Updated"
            assert row.ReOccurring is True
            assert row.DlFlag == 1
            assert row.CkSum == 0

    def test_writing_an_existing_holiday_with_a_new_date_rekeys_rows(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
    ):
        holiday = holiday_lookup.by_date(date(2026, 7, 4))
        holiday.date = date(2026, 7, 5)
        holiday.write()

        old_rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime(2026, 7, 4))
        ).all()
        assert old_rows == []

        new_rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime(2026, 7, 5))
        ).all()
        assert len(new_rows) == 2

    def test_writing_a_holiday_without_required_fields_raises(self, holiday_lookup: HolidayLookup):
        holiday = holiday_lookup.new()
        with pytest.raises(Exception):
            holiday.write()


class TestHolidayDelete:
    def test_delete_removes_rows_in_every_loc(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
        acs_updated_callback: Mock,
    ):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))
        holiday.delete()

        acs_updated_callback.assert_called_once_with(holiday)
        assert not holiday.in_db

        rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime(2026, 12, 25))
        ).all()
        assert rows == []

    def test_delete_bumps_loc_dirty_flags(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
    ):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))
        holiday.delete()

        locations = acs_data_session.scalars(
            select(LOC).where(LOC.LocGrp == location_group_id)
        ).all()
        for loc in locations:
            assert loc.DlFlag == 2
            assert loc.HolCs == 0
            assert loc.PlFlag is True

    def test_delete_leaves_other_group_rows_alone(
        self,
        holiday_lookup: HolidayLookup,
        acs_data_session: Session,
    ):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))
        holiday.delete()

        bad_row = acs_data_session.scalar(
            select(HOL)
            .where(HOL.Loc == bad_main_location_id)
            .where(HOL.HolDate == datetime(2026, 12, 25))
        )
        assert bad_row is not None

        bad_loc = acs_data_session.scalar(select(LOC).where(LOC.Loc == bad_main_location_id))
        assert bad_loc.DlFlag == 0

    def test_delete_on_new_holiday_raises(self, holiday_lookup: HolidayLookup):
        holiday = holiday_lookup.new()
        holiday.date = date(2026, 5, 1)
        holiday.slot = 3
        holiday.name = "May Day"

        with pytest.raises(HolidayNotInDatabase):
            holiday.delete()

    def test_delete_twice_raises_second_time(self, holiday_lookup: HolidayLookup):
        holiday = holiday_lookup.by_date(date(2026, 12, 25))
        holiday.delete()

        with pytest.raises(HolidayNotInDatabase):
            holiday.delete()


class TestHolidayAllocate:
    @pytest.fixture
    def empty_holiday_calendar(self, acs_data_session: Session) -> None:
        acs_data_session.execute(delete(HOL))
        acs_data_session.commit()

    @pytest.fixture
    def today(self) -> date:
        return date.today()

    @pytest.fixture
    def future_a(self, today: date) -> date:
        return today + timedelta(days=300)

    @pytest.fixture
    def future_b(self, today: date) -> date:
        return today + timedelta(days=400)

    @pytest.fixture
    def future_c(self, today: date) -> date:
        return today + timedelta(days=500)

    @staticmethod
    def _seed_holiday(session: Session, holiday_date: date, slot: int) -> None:
        for loc in (main_location_id, annex_location_id):
            session.add(HOL(
                Loc=loc,
                HolDate=datetime.combine(holiday_date, datetime.min.time()),
                Type=slot,
                Name=f"Seed slot {slot}",
                Notes="",
                ReOccurring=False,
            ))
        session.commit()

    def test_allocate_picks_slot_1_when_calendar_is_empty(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        future_a: date,
    ):
        holiday = holiday_lookup.allocate(future_a, "Open House A")

        assert holiday.in_db
        assert holiday.slot == 1
        assert holiday.date == future_a
        assert holiday.name == "Open House A"

    def test_allocate_picks_first_free_slot(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        future_a: date,
        future_b: date,
        future_c: date,
    ):
        self._seed_holiday(acs_data_session, future_a, slot=1)
        self._seed_holiday(acs_data_session, future_b, slot=2)

        holiday = holiday_lookup.allocate(future_c, "Open House C")

        assert holiday.slot == 3

    def test_allocate_raises_when_all_three_slots_future_occupied(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        today: date,
        future_a: date,
        future_b: date,
        future_c: date,
    ):
        self._seed_holiday(acs_data_session, future_a, slot=1)
        self._seed_holiday(acs_data_session, future_b, slot=2)
        self._seed_holiday(acs_data_session, future_c, slot=3)

        with pytest.raises(NoFreeHolidaySlotError):
            holiday_lookup.allocate(today + timedelta(days=42), "Won't fit")

    def test_allocate_raises_on_same_date_conflict(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        future_a: date,
    ):
        self._seed_holiday(acs_data_session, future_a, slot=2)

        with pytest.raises(HolidayDateConflict):
            holiday_lookup.allocate(future_a, "Same day, different request")

    def test_allocate_reuses_slot_with_only_past_entries(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        today: date,
        future_a: date,
    ):
        past = today - timedelta(days=30)
        self._seed_holiday(acs_data_session, past, slot=1)

        holiday = holiday_lookup.allocate(future_a, "Reuse stale slot")

        assert holiday.slot == 1

    def test_allocate_writes_a_row_per_loc_in_group(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        future_a: date,
    ):
        holiday = holiday_lookup.allocate(future_a, "Open House")

        rows = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(HOL.HolDate == datetime.combine(future_a, datetime.min.time()))
        ).all()
        assert {r.Loc for r in rows} == {main_location_id, annex_location_id}
        for row in rows:
            assert row.Name == "Open House"
            assert row.Type == holiday.slot
            assert row.DlFlag == 1
            assert row.CkSum == 0

        roundtrip = holiday_lookup.by_date(future_a)
        assert roundtrip is not None
        assert roundtrip.slot == holiday.slot
        assert roundtrip.name == "Open House"

    def test_allocate_ignores_other_location_group(
        self,
        holiday_lookup: HolidayLookup,
        empty_holiday_calendar: None,
        acs_data_session: Session,
        future_a: date,
    ):
        # An entry in a different location group must not block allocation in our group.
        acs_data_session.add(HOL(
            Loc=bad_main_location_id,
            HolDate=datetime.combine(future_a, datetime.min.time()),
            Type=1,
            Name="Other Group",
            Notes="",
            ReOccurring=False,
        ))
        acs_data_session.commit()

        holiday = holiday_lookup.allocate(future_a, "Mine")

        assert holiday.in_db
        assert holiday.slot == 1


class TestHolidayEmptyGroup:
    def test_writing_into_a_group_with_no_locations_raises(
        self,
        acs_data_engine: Engine,
        acs_updated_callback: Mock,
    ):
        # A location group with no LOC rows is impossible in practice but the model raises explicitly.
        # noinspection PyTypeChecker
        empty_group_info = LookupInfo(
            acs_engine=acs_data_engine,
            location_group_id=999,
            updated_callback=acs_updated_callback,
        )
        lookup = HolidayLookup(empty_group_info)
        holiday = lookup.new()
        holiday.date = date(2026, 5, 1)
        holiday.slot = 1
        holiday.name = "May Day"

        with pytest.raises(NoLocationsInGroup):
            holiday.write()
