from pathlib import Path

from watchdog.events import FileSystemEvent

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

    def on_any_event(self, event: FileSystemEvent) -> None:
        # We only listen for our restart files, so this should be safe enough.
        event_path: Path = Path(event.src_path)
        self._log.info(f"File {event.event_type} suggesting we should restart: {event_path}")
        event_path.unlink()
        self._outbound_event_queue.put(ApplicationRestartNeeded())
