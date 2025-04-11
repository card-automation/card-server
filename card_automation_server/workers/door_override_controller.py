import socket
from datetime import datetime, timedelta
from typing import Union, Tuple

from card_automation_server.config import Config
from card_automation_server.plugins.types import DoorOverrideEvent, CommServerEventType
from card_automation_server.workers.events import DoorStateUpdate, DoorState, RawCommServerEvent
from card_automation_server.workers.utils import EventsWorker

_Events = Union[
    DoorStateUpdate,
    RawCommServerEvent,
]

LocationDoor = Tuple[int, int]


class DoorOverrideController(EventsWorker[_Events]):
    def __init__(self,
                 config: Config,
                 ):
        self._log = config.logger
        self._workstation_number = config.windsx.workstation_number
        self._comm_server_host = config.windsx.cs_host
        self._comm_server_port = config.windsx.cs_port

        self._timeout_map: dict[LocationDoor, datetime] = {}
        self._pending_updates: dict[LocationDoor, DoorState] = {}
        self._last_update_time: dict[LocationDoor, datetime] = {}

        super().__init__()

    def _post_event(self) -> None:
        # _post_event is inconsistent and can get called faster than once a second if we receive multiple events. We
        # must use an actual timestamp for comparison instead of number of seconds.
        now = datetime.now()

        for location_door, timezone_at in self._timeout_map.copy().items():
            if now < timezone_at:
                continue

            del self._timeout_map[location_door]
            self._set_state(location_door, DoorState.TIMEZONE)

        # This should be the only place that's calling _send_state directly. Everywhere else should be calling
        # _set_state and waiting for this to check our pending updates.
        now = datetime.now()
        for location_door, state in self._pending_updates.items():
            past_time = now - timedelta(seconds=5)
            if (
                    location_door not in self._last_update_time
                    or self._last_update_time[location_door] < past_time
            ):
                self._send_state(location_door, state)

    def _handle_event(self, event: _Events):
        if isinstance(event, DoorStateUpdate):
            self._handle_door_state_update(event)

        if isinstance(event, RawCommServerEvent):
            self._handle_comm_server_event(event)

    def _handle_door_state_update(self, event: DoorStateUpdate):
        location_door: LocationDoor = event.location_id, event.door_number
        self._set_state(location_door, event.state)

        if event.timeout is not None:
            now = datetime.now()
            then = now + event.timeout
            self._timeout_map[location_door] = then
        elif location_door in self._timeout_map:
            del self._timeout_map[location_door]

    def _set_state(self,
                   location_door: LocationDoor,
                   state: DoorState) -> None:
        self._pending_updates[location_door] = state
        if location_door in self._last_update_time:
            del self._last_update_time[location_door]

    def _send_state(self,
                    location_door: LocationDoor,
                    state: DoorState) -> None:
        # Just in case this call fails, we'll try to get it back into this state in the future
        self._pending_updates[location_door] = state
        self._last_update_time[location_door] = datetime.now()

        self._log.info(f"Setting door ({location_door}) to {state.name}")
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
                str(location_door[0]),
                str(location_door[1]),
                "0",  # Unsure what this is for
                str(state_map[state]),
                "3830202337",  # No idea where this value comes from
                "11",  # The "Comm Server" string is 11 characters
                "*Comm Server\r\n",
            ]).encode('ascii'))
            # s.sendall(b"\r\n")  #Unsure if this extra newline is needed
            s.shutdown(socket.SHUT_WR)  # We're done writing, now to listen

            response: str = s.recv(1024).decode('ascii')
            if len(response) == 0 or response == "\r\n":
                return

            raise Exception(f"Unexpected Comm Server response: {response}")

    def _handle_comm_server_event(self, event: RawCommServerEvent):
        if not event.is_any_event(DoorOverrideEvent):
            return

        location_id = event.data[2]
        door_number = event.data[3]
        location_door: LocationDoor = (location_id, door_number)
        self._handle_door_override(location_door, event.type)

    def _handle_door_override(self,
                              location_door: LocationDoor,
                              event_type: CommServerEventType
                              ):
        if location_door not in self._pending_updates:
            return

        single_door_overrides: dict[DoorOverrideEvent, DoorState] = {
            CommServerEventType.OPR_SET_OUTPUT_SECURE: DoorState.SECURE,
            CommServerEventType.OPR_SET_OUTPUT_OPEN: DoorState.OPEN,
            CommServerEventType.OPR_SET_OUTPUT_TZ: DoorState.TIMEZONE,
        }

        if event_type in single_door_overrides:
            wanted_state: DoorState = self._pending_updates[location_door]
            updated_state: DoorState = single_door_overrides[event_type]

            if wanted_state == updated_state:
                # Yay, we did it!
                if location_door in self._pending_updates:
                    del self._pending_updates[location_door]
                return

            # The operator overrode whatever state we were trying to get to. We ignore whatever timeout we had and make
            # sure we're not trying to switch it back to something else
            if location_door in self._pending_updates:
                del self._pending_updates[location_door]
            if location_door in self._timeout_map:
                del self._timeout_map[location_door]
            return

        # Multiple event -> single door event
        multiple_door_overrides: dict[DoorOverrideEvent, DoorOverrideEvent] = {
            CommServerEventType.OPR_SET_OUTPUT_ALL_OPEN: DoorOverrideEvent.OPR_SET_OUTPUT_OPEN,
            CommServerEventType.OPR_SET_OUTPUT_ALL_TIME_ZONE: DoorOverrideEvent.OPR_SET_OUTPUT_OPEN,
        }

        if event_type in multiple_door_overrides:
            # Let's apply the single override to every door we know or care about
            single_override = multiple_door_overrides[event_type]
            for location_door in self._pending_updates.keys():
                self._handle_door_override(location_door, single_override)

            for location_door in self._timeout_map.keys():
                self._handle_door_override(location_door, single_override)

            return

        raise Exception(f"Unexpected event type {event_type}")
