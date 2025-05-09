from datetime import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from card_automation_server.config import Config
from card_automation_server.ioc import Resolver
from card_automation_server.plugins.types import CommServerEventType
from card_automation_server.windsx.db.models import EvnLog
from card_automation_server.workers.card_scan_watcher import CardScanWatcher
from card_automation_server.workers.events import CardScanned, LogDatabaseUpdated
from tests.conftest import main_location_id


@pytest.fixture
def card_scan_watcher(
        resolver: Resolver,
        # These aren't used directly, but are type hinted for the resolver's sake
        app_config: Config,
        acs_data_engine: Engine,
        log_engine: Engine
):
    watcher = resolver.singleton(CardScanWatcher)

    watcher.start()

    yield watcher

    watcher.stop(3)  # Tests should timeout pretty fast


class TestCardScanWatcher:
    def test_new_row_emits_card_scanned_event(self, log_session: Session, card_scan_watcher: CardScanWatcher):
        scan_time = datetime(2025, 1, 2)  # Doesn't matter that it's in the past, just that it's new
        event_log_entry = EvnLog(
            TimeDate=scan_time,
            Loc=main_location_id,
            Event=CommServerEventType.ACCESS_GRANTED.value,
            Dev=0,  # Main door
            IO=11,  # Company with access granted
            IOName="Main Door",
            Code=3000,  # Card number
            FName="BobThe",
            LName="BuildingManager",
            Opr="101"  # Name ID
        )

        log_session.add(event_log_entry)
        log_session.commit()

        card_scan_watcher.event(LogDatabaseUpdated())

        with card_scan_watcher.outbound_queue.not_empty:
            card_scan_watcher.outbound_queue.not_empty.wait(3)

        assert card_scan_watcher.outbound_queue.qsize() == 1

        event = card_scan_watcher.outbound_queue.get()

        assert isinstance(event, CardScanned)
        assert event.card_scan.scan_time == scan_time
        assert event.card_scan.card_number == 3000
        assert event.card_scan.event_type == CommServerEventType.ACCESS_GRANTED
        assert event.card_scan.name_id == 101
        assert event.card_scan.device == 0
