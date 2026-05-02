from datetime import date, timedelta

from card_automation_server.config import Config
from card_automation_server.windsx.lookup.holiday import HolidayLookup
from card_automation_server.workers.utils import ThreadedWorker

_CLEANUP_INTERVAL = timedelta(hours=1)


class ExpiredHolidayCleaner(ThreadedWorker[None]):
    def __init__(self, config: Config, holiday_lookup: HolidayLookup):
        super().__init__()
        self._log = config.logger
        self._holiday_lookup = holiday_lookup

    def cleanup_expired(self) -> int:
        today = date.today()
        deleted = 0
        for holiday in self._holiday_lookup.all():
            if holiday.date < today:
                holiday.delete()
                deleted += 1
        return deleted

    def _run(self) -> None:
        while not self._keep_running.is_set():
            try:
                count = self.cleanup_expired()
                if count > 0:
                    self._log.info(f"Cleaned up {count} expired holiday(s)")
            except Exception as ex:
                self._log.exception(ex)

            self._wake_event.wait(_CLEANUP_INTERVAL.seconds)
            self._wake_event.clear()
