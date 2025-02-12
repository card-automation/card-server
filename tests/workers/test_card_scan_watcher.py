from datetime import datetime

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from card_auto_add.plugins.types import CardScanEventType
from card_auto_add.windsx.db.models import EvnLog
from card_auto_add.workers.card_scan_watcher import CardScanWatcher
from card_auto_add.workers.events import CardScanned, LogDatabaseUpdated
from tests.conftest import main_location_id


@pytest.fixture
def card_scan_watcher(log_engine: Engine):
    watcher = CardScanWatcher(log_engine)

    watcher.start()

    yield watcher

    watcher.stop(3)  # Tests should timeout pretty fast


class TestCardScanWatcher:
    def test_new_row_emits_card_scanned_event(self, log_session: Session, card_scan_watcher: CardScanWatcher):
        scan_time = datetime(2025, 1, 2)  # Doesn't matter that it's in the past, just that it's new
        event_log_entry = EvnLog(
            TimeDate=scan_time,
            Loc=main_location_id,
            Event=CardScanEventType.ACCESS_GRANTED.value,
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
        assert event.card_scan.event_type == CardScanEventType.ACCESS_GRANTED
        assert event.card_scan.name_id == 101
        assert event.card_scan.device == 0
