import socket
import time
from datetime import datetime
from typing import Union

from card_automation_server.config import Config
from card_automation_server.workers.events import DoorStateUpdate, DoorState
from card_automation_server.workers.utils import EventsWorker

_Events = Union[
    DoorStateUpdate
]


class DoorOverrideController(EventsWorker[_Events]):
    def __init__(self,
                 config: Config,
                 ):
        self._workstation_number = config.windsx.workstation_number
        self._comm_server_host = config.windsx.cs_host
        self._comm_server_port = config.windsx.cs_port

        self._timeout_map: dict[(int, int), datetime] = {}

        super().__init__()

    def _post_event(self) -> None:
        # _post_event is inconsistent and can get called faster than once a second if we receive multiple events. We
        # must use an actual timestamp for comparison instead of number of seconds.
        now = datetime.now()

        for (location_id, door_number), timezone_at in self._timeout_map.copy().items():
            if now < timezone_at:
                continue

            self._set_state_with_retries(location_id, door_number, DoorState.TIMEZONE)
            del self._timeout_map[location_id, door_number]

            time.sleep(0.5)  # Just in case we're closing multiple doors in a row in quick succession

    def _handle_event(self, event: _Events):
        if isinstance(event, DoorStateUpdate):
            self._handle_door_state_update(event)

    def _handle_door_state_update(self, event: DoorStateUpdate):
        self._set_state_with_retries(event.location_id, event.device_id, event.state)

        if event.timeout is not None:
            now = datetime.now()
            then = now + event.timeout
            self._timeout_map[event.location_id, event.device_id] = then

    def _set_state_with_retries(self,
                                location_id: int,
                                door_number: int,
                                state: DoorState) -> bool:
        for i in range(2):  # Try up to 2 times
            if self._set_state_internal(location_id, door_number, state):
                return True

            time.sleep(0.5)  # Pause between retries
        return False

    def _set_state_internal(self,
                            location_id: int,
                            door_number: int,
                            state: DoorState) -> bool:
        state_map = {
            DoorState.OPEN: 1,
            DoorState.SECURE: 2,
            DoorState.TIMEZONE: 3
        }

        if state not in state_map:
            raise Exception(f"Unknown door state {state}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((self._comm_server_host, self._comm_server_port))
            s.sendall(" ".join([
                "6",  # Pretty sure this is the command id
                str(self._workstation_number),
                str(location_id),
                str(door_number),
                "0",  # Unsure what this is for
                str(state_map[state]),
                "3830202337",  # No idea where this value comes from
                "11",  # The "Comm Server" string is 11 characters
                "*Comm Server\r\n",
            ]).encode('ascii'))
            # s.sendall(b"\r\n")  #Unsure if this extra newline is needed
            s.shutdown(socket.SHUT_WR)  # We're done writing, now to listen

            response: str = s.recv(1024).decode('ascii')
            if len(response) == 0:
                return False

            if response == "\r\n":
                return True

            raise Exception(f"Unexpected Comm Server response: {response}")
