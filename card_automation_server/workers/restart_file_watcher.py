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

        # Let's just clean up these files, if they happen to already exist on server start.
        for f in self._force_restart_files:
            f.unlink(missing_ok=True)

        super().__init__(
            config,
            *self._force_restart_files,
        )

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.event_type == "deleted":
            return
        # We only listen for our restart files, so this should be safe enough.
        event_path: Path = Path(event.src_path)
        self._log.info(f"File {event.event_type} suggesting we should restart: {event_path}")
        event_path.unlink(missing_ok=True)
        self._outbound_event_queue.put(ApplicationRestartNeeded())
