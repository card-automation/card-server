from pathlib import Path
from typing import Union

from watchdog.events import FileModifiedEvent, DirModifiedEvent

from card_automation_server.config import Config
from card_automation_server.workers.events import AcsDatabaseUpdated, LogDatabaseUpdated
from card_automation_server.workers.utils import FileWatcherWorker


class DatabaseFileWatcher(FileWatcherWorker):
    def __init__(self,
                 config: Config
                 ):
        self._acs_db_path = config.windsx.acs_data_db_path
        self._log_db_path = config.windsx.log_db_path

        super().__init__(
            self._acs_db_path,
            self._log_db_path
        )

    def on_modified(self, event: Union[FileModifiedEvent, DirModifiedEvent]) -> None:
        if not isinstance(event, FileModifiedEvent):
            return

        event_path: Path = Path(event.src_path)
        if event_path == self._acs_db_path:
            self.outbound_queue.put(AcsDatabaseUpdated())

        if event_path == self._log_db_path:
            self.outbound_queue.put(LogDatabaseUpdated())
