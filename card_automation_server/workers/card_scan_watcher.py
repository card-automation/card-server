from typing import Union

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from card_automation_server.config import Config
from card_automation_server.plugins.types import CardScan, CommServerEventType, CardScanEvent
from card_automation_server.windsx.db.models import EvnLog, NAMES, CARDS
from card_automation_server.windsx.engines import LogEngine, AcsEngine
from card_automation_server.workers.events import LogDatabaseUpdated, CardScanned, RawCommServerEvent
from card_automation_server.workers.utils import EventsWorker

_Events = Union[
    LogDatabaseUpdated,
    RawCommServerEvent,
]


class CardScanWatcher(EventsWorker[_Events]):
    def __init__(self,
                 acs_engine: AcsEngine,
                 log_engine: LogEngine,
                 config: Config,
                 ):
        super().__init__()
        self._log = config.logger
        self._db_log_session = Session(log_engine)
        self._db_acs_session = Session(acs_engine)
        self._last_timestamp = self._db_log_session.scalar(select(func.max(EvnLog.TimeDate)))

    def _handle_event(self, event: _Events):
        if isinstance(event, LogDatabaseUpdated):
            self._handle_log_database_update(event)

        if isinstance(event, RawCommServerEvent):
            self._handle_raw_comm_server_event(event)

    def _handle_log_database_update(self, _: LogDatabaseUpdated):
        latest_events = self._db_log_session.scalars(
            select(EvnLog)
            .where(EvnLog.TimeDate > self._last_timestamp)
            .order_by(EvnLog.TimeDate)
        ).all()

        event: EvnLog
        for event in latest_events:
            valid_event_codes = [x.value for x in CardScanEvent.__args__]
            if event.Event not in valid_event_codes:
                continue

            self._outbound_event_queue.put(
                CardScanned(
                    card_scan=CardScan(
                        name_id=int(event.Opr),
                        card_number=int(event.Code),
                        scan_time=event.TimeDate,
                        device=event.Dev,
                        event_type=CommServerEventType(event.Event),
                        location_id=int(event.Loc)
                    )
                )
            )

            # This ensures processing the events out of order still gets us the latest timestamp.
            self._last_timestamp = max(self._last_timestamp, event.TimeDate)

    def _handle_raw_comm_server_event(self, event: RawCommServerEvent):
        timestamp = event.timestamp

        if timestamp < self._last_timestamp:
            return  # Probably already seen it via DB update, ignore it (though this one is always faster)

        if not event.is_any_event(CardScanEvent):
            return

        location_id = event.data[2]
        device_id = event.data[3]
        card_number = event.data[21]

        name_id = self._db_acs_session.scalar(
            select(NAMES.ID)
            .join(CARDS, CARDS.NameID == NAMES.ID)
            .where(CARDS.Code == float(card_number))
        )

        self._outbound_event_queue.put(
            CardScanned(
                card_scan=CardScan(
                    name_id=name_id,
                    card_number=card_number,
                    scan_time=timestamp,
                    device=device_id,
                    event_type=event.type,
                    location_id=location_id
                )
            )
        )

        self._last_timestamp = max(self._last_timestamp, timestamp)
