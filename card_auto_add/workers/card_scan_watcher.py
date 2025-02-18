from sqlalchemy import select, func
from sqlalchemy.orm import Session

from card_auto_add.plugins.types import CardScanEventType, CardScan
from card_auto_add.windsx.db.models import EvnLog
from card_auto_add.windsx.engines import LogEngine
from card_auto_add.workers.events import LogDatabaseUpdated, CardScanned
from card_auto_add.workers.utils import EventsWorker

_Events = [
    LogDatabaseUpdated
]


class CardScanWatcher(EventsWorker[LogDatabaseUpdated]):
    def __init__(self, log_engine: LogEngine):
        super().__init__()
        self._log_session = Session(log_engine)
        self._last_timestamp = self._log_session.scalar(select(func.max(EvnLog.TimeDate)))

    def _handle_event(self, event: _Events):
        if isinstance(event, LogDatabaseUpdated):
            self._handle_log_database_update(event)

    def _handle_log_database_update(self, _: LogDatabaseUpdated):
        latest_events = self._log_session.scalars(
            select(EvnLog)
            .where(EvnLog.TimeDate > self._last_timestamp)
        ).all()

        event: EvnLog
        for event in latest_events:
            valid_event_codes = [x.value for x in CardScanEventType]
            if event.Event not in valid_event_codes:
                continue

            self._outbound_event_queue.put(
                CardScanned(
                    card_scan=CardScan(
                        name_id=int(event.Opr),
                        card_number=int(event.Code),
                        scan_time=event.TimeDate,
                        device=event.Dev,
                        event_type=CardScanEventType(event.Event)
                    )
                )
            )

            # We didn't order the event log for speed, so this just ensures processing the events out of order still
            # gets us the latest timestamp.
            self._last_timestamp = max(self._last_timestamp, event.TimeDate)
