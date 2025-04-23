from datetime import datetime, timedelta
from typing import Union

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from card_automation_server.config import Config
from card_automation_server.data_signing import DataSigning
from card_automation_server.windsx.db.models import LOC
from card_automation_server.windsx.engines import AcsEngine
from card_automation_server.workers.events import AcsDatabaseUpdated, CommServerRestartRequested
from card_automation_server.workers.utils import EventsWorker

_Events = Union[
    AcsDatabaseUpdated
]


class DSXHardwareResetWorker(EventsWorker[_Events]):
    def __init__(self,
                 config: Config,
                 acs_engine: AcsEngine
                 ):
        super().__init__()
        self._dsx_pi_host = config.dsxpi.host
        self._data_signing = DataSigning(config.dsxpi.secret)
        self._session = Session(acs_engine)
        self._location_to_pending_timestamps: dict[int, datetime] = {}
        self._next_allowed_reset: datetime = datetime.now()

        # Even if we don't see the AcsDatabaseUpdated event, we're going to manually check. Normally it should only take
        # max 40 seconds to update, so checking every minute and failing every 3 minute handles all the worst cases.
        self._call_every(timedelta(minutes=1), self._sync_locations_pending)

    def _post_event(self) -> None:
        now = datetime.now()
        three_minutes_ago = now - timedelta(minutes=3)

        for update_started_timestamp in self._location_to_pending_timestamps.values():
            if three_minutes_ago > update_started_timestamp and now > self._next_allowed_reset:
                self._reset()

    def _handle_event(self, event: _Events):
        if isinstance(event, AcsDatabaseUpdated):
            self._sync_locations_pending()

    def _sync_locations_pending(self):
        locations_pending = self._session.scalars(
            select(LOC).where(LOC.PlFlag)
        ).all()

        for location in locations_pending:
            location_id = location.Loc
            is_downloading = location.PlFlag

            # If we're downloading this location and aren't currently watching for this timestamp, start watching it
            if is_downloading and location_id not in self._location_to_pending_timestamps:
                self._location_to_pending_timestamps[location_id] = datetime.now()

            # If we aren't downloading anymore but were watching for this timestamp, stop watching it
            if not is_downloading and location_id in self._location_to_pending_timestamps:
                del self._location_to_pending_timestamps[location_id]

    def _reset(self):
        # Don't restart again any sooner than 10 minutes from now
        self._next_allowed_reset = datetime.now() + timedelta(minutes=10)
        # Tell the hardware to restart
        signed_payload = self._data_signing.encode(10)
        url = f"{self._dsx_pi_host}/reset/{signed_payload}"
        response = requests.post(url)

        response.raise_for_status()

        # Request that the comm server software restart
        self._outbound_event_queue.put(CommServerRestartRequested())
