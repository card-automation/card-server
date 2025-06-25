import logging
import re
import socket
import time
from logging.handlers import RotatingFileHandler

from platformdirs import PlatformDirs

from card_automation_server.config import Config
from card_automation_server.workers.events import RawCommServerMessage
from card_automation_server.workers.utils import ThreadedWorker


class CommServerSocketListener(ThreadedWorker[None]):
    def __init__(self, dirs: PlatformDirs, config: Config):
        super().__init__()
        self._a = 0
        self._b = 0
        self._c = 0
        self._d = 0
        self._cs_host = config.windsx.cs_host
        self._cs_port = config.windsx.cs_port

        log_root = dirs.user_data_path / "cs_raw"
        log_root.mkdir(parents=True, exist_ok=True)

        self._log = logging.getLogger('cs')
        self._log.setLevel(logging.DEBUG)

        log_file = log_root / "cs.log"
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        max_bytes = 1 * 1024 * 1024
        file_handler = RotatingFileHandler(log_file,
                                           maxBytes=max_bytes,
                                           backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        if log_file.exists():
            file_handler.doRollover()

        self._log.addHandler(file_handler)

        self._caught_up = False

    def _run(self) -> None:
        while not self._keep_running.is_set():
            result = self._send_request()

            for line in result:
                self._log.debug(f"< {line.rstrip('\r\n')}")

            if not self._caught_up:
                if len(result) > 0:
                    continue
                else:
                    self._caught_up = True
                    self._log.info("CS Socket caught up")

            for line in result:
                comm_server_message = RawCommServerMessage.parse(line)
                self._outbound_event_queue.put(comm_server_message)

                event = comm_server_message.event
                if event is not None:
                    self._outbound_event_queue.put(event)

            time.sleep(0.5)  # Tight loop, let us know about new events fast

    def _send_request(self) -> list[str]:
        result = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((self._cs_host, self._cs_port))
            # 0 is request
            # 80 is workstation
            # last 0 is unknown
            message = f"0 80 3 {self._a} {self._b} {self._c} {self._d} 0"
            s.sendall(f"{message}\r\n".encode('ascii'))
            s.shutdown(socket.SHUT_WR)
            content = bytearray()
            while True:
                response = s.recv(1024)
                if len(response) == 0:
                    break
                content.extend(response)

            lines = [x for x in content.decode('ascii').split('\r\n') if len(x) > 0]

            if len(lines) == 0:
                return []

            # Log it here instead of where we're sending it so we don't get a lot of empty traffic
            self._log.debug(f"> {message}")
            for line in lines:
                result.append(line)
                event_count_re = re.compile(r'(\d+) (\d+) .*')

                match = event_count_re.match(line)
                event = int(match.group(1))
                index = int(match.group(2))
                if event == 1:
                    self._a = index
                elif event == 2:
                    self._b = index
                elif event in (3, 4, 5):
                    self._c = index
                elif event == 8:
                    self._d = index
                elif event == 10:
                    pass  # No idea wh at this event is. Didn't seem to have an index to update.
                else:
                    raise Exception(f"Unknown event {event} with index {index}")
        return result
