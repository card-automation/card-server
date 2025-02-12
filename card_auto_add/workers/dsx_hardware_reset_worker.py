from datetime import datetime, timedelta
from typing import Optional

import requests
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from card_auto_add.data_signing import DataSigning
from card_auto_add.windsx.db.models import LOC
from card_auto_add.workers.events import AcsDatabaseUpdated
from card_auto_add.workers.utils import EventsWorker

_Events = [
    AcsDatabaseUpdated
]


class DSXHardwareResetWorker(EventsWorker[_Events]):
    def __init__(self,
                 dsx_pi_host: str,
                 dsx_pi_signing_secret: str,
                 acs_engine: Engine
                 ):
        super().__init__()
        self._dsx_pi_host = dsx_pi_host
        self._data_signing = DataSigning(dsx_pi_signing_secret)
        self._session = Session(acs_engine)
        self._location_to_pending_timestamps: dict[int, datetime] = {}
        self._last_check_time: Optional[datetime] = None

    def _post_event(self) -> None:
        if self._last_check_time is None:
            self._sync_locations_pending()

        # Force a recheck every 3 minutes anyway
        three_minutes_ago = datetime.now() - timedelta(minutes=3)
        if three_minutes_ago > self._last_check_time:
            self._sync_locations_pending()

        for update_started_timestamp in self._location_to_pending_timestamps.values():
            if three_minutes_ago > update_started_timestamp:
                self._reset_hardware()

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

        self._last_check_time = datetime.now()

    def _reset_hardware(self):
        signed_payload = self._data_signing.encode(10)
        url = f"{self._dsx_pi_host}/reset/{signed_payload}"
        response = requests.post(url)

        response.raise_for_status()
