from datetime import datetime
from typing import Union

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from card_automation_server.config import Config
from card_automation_server.plugins.types import CardScanEventType, CardScan
from card_automation_server.windsx.db.models import EvnLog, NAMES, CARDS
from card_automation_server.windsx.engines import LogEngine, AcsEngine
from card_automation_server.workers.events import LogDatabaseUpdated, CardScanned, RawCommServerMessage
from card_automation_server.workers.utils import EventsWorker

_Events = Union[
    LogDatabaseUpdated,
    RawCommServerMessage,
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

        if isinstance(event, RawCommServerMessage):
            self._handle_raw_comm_server_message(event)

    def _handle_log_database_update(self, _: LogDatabaseUpdated):
        latest_events = self._db_log_session.scalars(
            select(EvnLog)
            .where(EvnLog.TimeDate > self._last_timestamp)
            .order_by(EvnLog.TimeDate)
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
                        event_type=CardScanEventType(event.Event),
                        location_id=int(event.Loc)
                    )
                )
            )

            # This ensures processing the events out of order still gets us the latest timestamp.
            self._last_timestamp = max(self._last_timestamp, event.TimeDate)

    def _handle_raw_comm_server_message(self, message: RawCommServerMessage):
        if message.type != 1:
            return  # We only handle log events for card scans

        if len(message.data) < 7:
            return  # Can't get the event type to see if it's one we care about

        event_type = message.data[6]

        if event_type not in [x.value for x in CardScanEventType]:
            return  # Not a card scan event, safe to ignore

        timestamp = datetime(
            year=message.data[10],
            month=message.data[11],
            day=message.data[12],
            hour=message.data[13],
            minute=message.data[14],
            second=message.data[15],
        )

        if timestamp < self._last_timestamp:
            return  # Probably already seen it via DB update, ignore it (though this one is always faster)

        location_id = message.data[2]
        device_id = message.data[3]
        card_number = message.data[21]

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
                    event_type=CardScanEventType(event_type),
                    location_id=location_id
                )
            )
        )

        self._last_timestamp = max(self._last_timestamp, timestamp)
