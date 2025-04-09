from pathlib import Path
from typing import Union

from watchdog.events import FileCreatedEvent, DirCreatedEvent

from card_automation_server.config import Config
from card_automation_server.workers.events import ApplicationRestartNeeded
from card_automation_server.workers.utils import FileWatcherWorker


class RestartFileWatcher(FileWatcherWorker):
    def __init__(self, config: Config):
        self._log = config.logger

        self._force_restart_files: list[Path] = [
            config.config_root / "restart.txt",
            config.config_root / "restart",
        ]

        super().__init__(
            config,
            *self._force_restart_files,
        )

    def on_created(self, event: Union[FileCreatedEvent, DirCreatedEvent]) -> None:
        if not isinstance(event, FileCreatedEvent):
            return

        event_path: Path = Path(event.src_path)
        self._log.info(f"File found suggesting we should restart: {event_path}")
        event_path.unlink()
        self._outbound_event_queue.put(ApplicationRestartNeeded())
