from unittest.mock import Mock

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import LOC, TZ
from card_automation_server.windsx.lookup.timezone import (
    NoLocationsInGroup,
    Timezone,
    TimezoneLookup,
)
from card_automation_server.windsx.lookup.utils import LookupInfo
from tests.conftest import (
    annex_location_id,
    bad_main_location_id,
    location_group_id,
    main_location_id,
)


class TestTimezoneLookup:
    def test_all_returns_one_logical_entry_per_tz_number(self, timezone_lookup: TimezoneLookup):
        timezones = timezone_lookup.all()

        tz_numbers = {tz.tz_number for tz in timezones}
        assert tz_numbers == {1, 2, 3}

    def test_by_tz_returns_timezone_with_expected_fields(self, timezone_lookup: TimezoneLookup):
        tz = timezone_lookup.by_tz(2)

        assert tz is not None
        assert tz.in_db
        assert tz.tz_number == 2
        assert tz.name == "Front Door Auto Unlock"
        assert tz.sun.start == 1300
        assert tz.sun.stop == 945
        assert tz.mon.start == 1400
        assert tz.mon.stop == 1100
        assert tz.sat.start == 2300
        assert tz.sat.stop == 1930
        assert tz.hol1.start == 0
        assert tz.hol1.stop == 2400

    def test_by_tz_returns_none_when_missing(self, timezone_lookup: TimezoneLookup):
        assert timezone_lookup.by_tz(99) is None

    def test_by_tz_excludes_other_location_group(self, timezone_lookup: TimezoneLookup):
        tz = timezone_lookup.by_tz(1)

        # Bad-group row also has TZ=1 with a different name; the read must not see it.
        assert tz is not None
        assert tz.name == "Always(24x7)"

    def test_by_name_returns_matching_timezones(self, timezone_lookup: TimezoneLookup):
        results = timezone_lookup.by_name("Work hours only")

        assert len(results) == 1
        assert results[0].tz_number == 3

    def test_by_name_excludes_other_location_group(self, timezone_lookup: TimezoneLookup):
        assert timezone_lookup.by_name("Bad Group Always") == []


class TestTimezoneWrite:
    def test_new_timezone_starts_not_in_db(self, timezone_lookup: TimezoneLookup):
        tz = timezone_lookup.new()
        assert not tz.in_db
        assert tz.tz_number is None
        assert tz.name is None
        for field_name in ("sun", "mon", "tue", "wed", "thu", "fri", "sat", "hol1", "hol2", "hol3"):
            sub = getattr(tz, field_name)
            assert sub.start == 0
            assert sub.stop == 0

    def test_writing_a_new_timezone_assigns_next_free_number(
        self,
        timezone_lookup: TimezoneLookup,
        acs_data_session: Session,
        acs_updated_callback: Mock,
    ):
        tz: Timezone = timezone_lookup.new()
        tz.name = "Open House Auto Unlock"
        tz.sun.start = 1800
        tz.sun.stop = 2100

        tz.write()

        assert tz.in_db
        assert tz.tz_number == 4  # max existing in group is 3
        acs_updated_callback.assert_called_once_with(tz)

        rows = acs_data_session.scalars(
            select(TZ)
            .join(LOC, LOC.Loc == TZ.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(TZ.TZ == 4)
        ).all()
        assert {r.Loc for r in rows} == {main_location_id, annex_location_id}
        for row in rows:
            assert row.Name == "Open House Auto Unlock"
            assert row.SunStart == 1800
            assert row.SunStop == 2100
            assert row.DlFlag == 1
            assert row.CkSum == 0

    def test_writing_an_existing_timezone_updates_every_loc(
        self,
        timezone_lookup: TimezoneLookup,
        acs_data_session: Session,
        acs_updated_callback: Mock,
    ):
        tz = timezone_lookup.by_tz(2)
        tz.sun.start = 800
        tz.sun.stop = 2200
        tz.hol1.start = 1000
        tz.hol1.stop = 1700
        tz.notes = "Updated"

        tz.write()

        acs_updated_callback.assert_called_once_with(tz)

        rows = acs_data_session.scalars(
            select(TZ)
            .join(LOC, LOC.Loc == TZ.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(TZ.TZ == 2)
        ).all()
        assert {r.Loc for r in rows} == {main_location_id, annex_location_id}
        for row in rows:
            assert row.SunStart == 800
            assert row.SunStop == 2200
            assert row.Hol1Start == 1000
            assert row.Hol1Stop == 1700
            assert row.Notes == "Updated"
            assert row.DlFlag == 1
            assert row.CkSum == 0

    def test_writing_fills_in_missing_loc_rows(
        self,
        timezone_lookup: TimezoneLookup,
        acs_data_session: Session,
    ):
        # Drop the annex copy of TZ 1 so the write must insert it.
        annex_row = acs_data_session.scalar(
            select(TZ).where(TZ.Loc == annex_location_id).where(TZ.TZ == 1)
        )
        acs_data_session.delete(annex_row)
        acs_data_session.commit()

        tz = timezone_lookup.by_tz(1)
        tz.notes = "Re-fan-out"
        tz.write()

        rows = acs_data_session.scalars(
            select(TZ)
            .join(LOC, LOC.Loc == TZ.Loc)
            .where(LOC.LocGrp == location_group_id)
            .where(TZ.TZ == 1)
        ).all()
        assert {r.Loc for r in rows} == {main_location_id, annex_location_id}
        for row in rows:
            assert row.Notes == "Re-fan-out"

    def test_writing_bumps_loc_dirty_flags(
        self,
        timezone_lookup: TimezoneLookup,
        acs_data_session: Session,
    ):
        tz = timezone_lookup.by_tz(1)
        tz.sun.start = 100
        tz.write()

        locations = acs_data_session.scalars(
            select(LOC).where(LOC.LocGrp == location_group_id)
        ).all()
        for loc in locations:
            assert loc.DlFlag == 1
            assert loc.TzCs == 0
            assert loc.PlFlag is True

    def test_writing_does_not_touch_other_location_groups(
        self,
        timezone_lookup: TimezoneLookup,
        acs_data_session: Session,
    ):
        tz = timezone_lookup.by_tz(1)
        tz.sun.start = 555
        tz.write()

        bad_loc = acs_data_session.scalar(
            select(LOC).where(LOC.Loc == bad_main_location_id)
        )
        assert bad_loc.DlFlag == 0
        assert bad_loc.TzCs == 0
        assert bad_loc.PlFlag is False

        bad_row = acs_data_session.scalar(
            select(TZ).where(TZ.Loc == bad_main_location_id).where(TZ.TZ == 1)
        )
        assert bad_row.SunStart == 0  # untouched

    def test_round_trip_preserves_all_fields(
        self,
        timezone_lookup: TimezoneLookup,
    ):
        tz: Timezone = timezone_lookup.new()
        tz.name = "Full Coverage"
        tz.sun.start = 100; tz.sun.stop = 110
        tz.mon.start = 200; tz.mon.stop = 210
        tz.tue.start = 300; tz.tue.stop = 310
        tz.wed.start = 400; tz.wed.stop = 410
        tz.thu.start = 500; tz.thu.stop = 510
        tz.fri.start = 600; tz.fri.stop = 610
        tz.sat.start = 700; tz.sat.stop = 710
        tz.hol1.start = 800; tz.hol1.stop = 810
        tz.hol2.start = 900; tz.hol2.stop = 910
        tz.hol3.start = 1000; tz.hol3.stop = 1010

        tz.write()

        round_trip = timezone_lookup.by_tz(tz.tz_number)
        assert round_trip is not None
        assert round_trip.name == "Full Coverage"
        assert (round_trip.sun.start, round_trip.sun.stop) == (100, 110)
        assert (round_trip.mon.start, round_trip.mon.stop) == (200, 210)
        assert (round_trip.tue.start, round_trip.tue.stop) == (300, 310)
        assert (round_trip.wed.start, round_trip.wed.stop) == (400, 410)
        assert (round_trip.thu.start, round_trip.thu.stop) == (500, 510)
        assert (round_trip.fri.start, round_trip.fri.stop) == (600, 610)
        assert (round_trip.sat.start, round_trip.sat.stop) == (700, 710)
        assert (round_trip.hol1.start, round_trip.hol1.stop) == (800, 810)
        assert (round_trip.hol2.start, round_trip.hol2.stop) == (900, 910)
        assert (round_trip.hol3.start, round_trip.hol3.stop) == (1000, 1010)

    def test_writing_without_a_name_raises(self, timezone_lookup: TimezoneLookup):
        tz = timezone_lookup.new()
        with pytest.raises(Exception):
            tz.write()


class TestTimezoneEmptyGroup:
    def test_writing_into_a_group_with_no_locations_raises(
        self,
        acs_data_engine: Engine,
        acs_updated_callback: Mock,
    ):
        # noinspection PyTypeChecker
        empty_group_info = LookupInfo(
            acs_engine=acs_data_engine,
            location_group_id=999,
            updated_callback=acs_updated_callback,
        )
        lookup = TimezoneLookup(empty_group_info)
        tz = lookup.new()
        tz.name = "Will fail"

        with pytest.raises(NoLocationsInGroup):
            tz.write()
