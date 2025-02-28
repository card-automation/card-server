import os
import signal
import subprocess
from datetime import datetime, timedelta
from typing import Optional

import psutil
from sentry_sdk import capture_exception

from card_automation_server.config import Config
from card_automation_server.workers.events import CommServerRestartRequested
from card_automation_server.workers.utils import EventsWorker

_Events = [
    CommServerRestartRequested
]


class CommServerRestarter(EventsWorker[_Events]):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        self._next_check_time = datetime.now()

    def _pre_event(self) -> None:
        if self._next_check_time < datetime.now():
            return

        process = self._get_cs_process()

        if process is None:
            self._start_comm_server()

        self._next_check_time = datetime.now() + timedelta(minutes=1)

    @staticmethod
    def _get_cs_process() -> Optional[psutil.Process]:
        _capture_exception = True
        while True:
            try:
                cs_processes = [p for p in psutil.process_iter() if p.name() == 'cs.exe']

                if len(cs_processes) == 0:
                    return None

                return cs_processes[0]
            except psutil.NoSuchProcess:
                # This can happen if we iterate over a process and check the name, but the process is gone. Rare, but it
                # happens and it's useless to report it. This technically means we could loop forever without restarting
                # the comm server and never know, but this issue has happened maybe twice in 4 years and is resolved by
                # the next loop.
                continue
            except BaseException as ex:
                # This one is a little more dangerous, just in case it's an issue that can happen every single time.
                # That's why we gate it behind a flag, so we don't have a tight loop that's reporting an exception. In
                # the entire time this program has been running, the only exception reported was the one above.
                if _capture_exception:
                    capture_exception(ex)
                    _capture_exception = False
                continue

    def _handle_event(self, event: _Events):
        if isinstance(event, CommServerRestartRequested):
            self._restart_comm_server(event)

    def _restart_comm_server(self, _: CommServerRestartRequested):
        self._kill_comm_server()

        self._start_comm_server()

    def _kill_comm_server(self):
        process = self._get_cs_process()

        if process is None:
            return

        os.kill(process.pid, signal.SIGTERM)

    def _start_comm_server(self):
        subprocess.Popen(os.path.join(self._config.windsx.root, 'CS.exe'))
