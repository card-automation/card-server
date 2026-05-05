import logging
from datetime import date, datetime, timedelta
from typing import Generator
from unittest.mock import Mock

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import HOL, LOC
from card_automation_server.windsx.lookup.holiday import HolidayLookup
from card_automation_server.workers.expired_holiday_cleaner import ExpiredHolidayCleaner
from tests.conftest import (
    annex_location_id,
    bad_main_location_id,
    location_group_id,
    main_location_id,
)


@pytest.fixture
def cleaner(holiday_lookup: HolidayLookup) -> Generator[ExpiredHolidayCleaner, None, None]:
    config = Mock()
    config.logger = logging.getLogger("test_expired_holiday_cleaner")
    worker = ExpiredHolidayCleaner(config, holiday_lookup)
    try:
        yield worker
    finally:
        worker.stop(2)


@pytest.fixture
def empty_holiday_calendar(acs_data_session: Session) -> None:
    acs_data_session.execute(delete(HOL))
    acs_data_session.commit()


def _seed_holiday(session: Session, holiday_date: date, slot: int) -> None:
    for loc in (main_location_id, annex_location_id):
        session.add(HOL(
            Loc=loc,
            HolDate=datetime.combine(holiday_date, datetime.min.time()),
            Type=slot,
            Name=f"Slot {slot}",
            Notes="",
            ReOccurring=False,
        ))
    session.commit()


def _run_one_cleanup(cleaner: ExpiredHolidayCleaner) -> None:
    cleaner.start()
    cleaner.stop(2)


@pytest.mark.long
class TestExpiredHolidayCleaner:
    def test_running_worker_removes_past_holidays(
        self,
        cleaner: ExpiredHolidayCleaner,
        empty_holiday_calendar: None,
        acs_data_session: Session,
    ):
        today = date.today()
        _seed_holiday(acs_data_session, today - timedelta(days=10), slot=1)
        _seed_holiday(acs_data_session, today - timedelta(days=1), slot=2)
        _seed_holiday(acs_data_session, today + timedelta(days=10), slot=3)

        _run_one_cleanup(cleaner)

        remaining = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
        ).all()
        assert {r.Type for r in remaining} == {3}
        assert len(remaining) == 2  # one row per Loc

    def test_running_worker_keeps_today(
        self,
        cleaner: ExpiredHolidayCleaner,
        empty_holiday_calendar: None,
        acs_data_session: Session,
    ):
        _seed_holiday(acs_data_session, date.today(), slot=1)

        _run_one_cleanup(cleaner)

        remaining = acs_data_session.scalars(
            select(HOL)
            .join(LOC, LOC.Loc == HOL.Loc)
            .where(LOC.LocGrp == location_group_id)
        ).all()
        assert len(remaining) == 2

    def test_running_worker_with_empty_calendar_completes(
        self,
        cleaner: ExpiredHolidayCleaner,
        empty_holiday_calendar: None,
    ):
        _run_one_cleanup(cleaner)

    def test_running_worker_ignores_other_location_groups(
        self,
        cleaner: ExpiredHolidayCleaner,
        empty_holiday_calendar: None,
        acs_data_session: Session,
    ):
        acs_data_session.add(HOL(
            Loc=bad_main_location_id,
            HolDate=datetime.combine(date.today() - timedelta(days=5), datetime.min.time()),
            Type=1,
            Name="Other group expired",
            Notes="",
            ReOccurring=False,
        ))
        acs_data_session.commit()

        _run_one_cleanup(cleaner)

        remaining = acs_data_session.scalars(select(HOL)).all()
        assert len(remaining) == 1
        assert remaining[0].Loc == bad_main_location_id

    def test_running_worker_bumps_loc_dirty_flags_for_deleted(
        self,
        cleaner: ExpiredHolidayCleaner,
        empty_holiday_calendar: None,
        acs_data_session: Session,
    ):
        _seed_holiday(acs_data_session, date.today() - timedelta(days=1), slot=1)

        _run_one_cleanup(cleaner)

        locations = acs_data_session.scalars(
            select(LOC).where(LOC.LocGrp == location_group_id)
        ).all()
        for loc in locations:
            assert loc.DlFlag == 2
            assert loc.HolCs == 0
            assert loc.PlFlag is True
