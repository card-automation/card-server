from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileModifiedEvent
from watchdog.observers import Observer

from card_auto_add.config import Config
from card_auto_add.workers.events import AcsDatabaseUpdated, LogDatabaseUpdated
from card_auto_add.workers.utils import Worker


class DatabaseFileWatcher(Worker, FileSystemEventHandler):
    def __init__(self,
                 config: Config
                 ):
        super().__init__()
        self._acs_db_path = config.windsx.acs_data_db_path
        self._log_db_path = config.windsx.log_db_path

        paths = self._get_observed_paths(
            self._acs_db_path,
            self._log_db_path
        )

        self._observer = Observer()
        for path in paths:
            self._observer.schedule(self, path)

    @staticmethod
    def _get_observed_paths(*paths: Path) -> list[Path]:
        result = []

        for path in paths:
            parent = path.parent

            if parent not in result:
                result.append(parent)

        return result

    def start(self):
        self._observer.start()

    def stop(self, timeout: Optional[float] = None):
        self._observer.stop()

        self._observer.join(timeout)

        if self._observer.is_alive():
            raise Exception("Database file watcher thread timed out")

    def on_modified(self, event: FileSystemEvent) -> None:
        if not isinstance(event, FileModifiedEvent):
            return

        event_path: Path = Path(event.src_path)
        if event_path == self._acs_db_path:
            self.outbound_queue.put(AcsDatabaseUpdated())

        if event_path == self._log_db_path:
            self.outbound_queue.put(LogDatabaseUpdated())
