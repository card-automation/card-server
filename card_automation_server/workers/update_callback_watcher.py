from typing import Callable, Any, Optional

from card_automation_server.windsx.lookup.access_card import AccessCard
from card_automation_server.workers.events import LocCardUpdated, AccessCardUpdated, DoorStateUpdate
from card_automation_server.workers.utils import Worker


class UpdateCallbackWatcher(Worker):
    def __init__(self):
        super().__init__()

    def start(self):
        pass  # No thread to start

    def stop(self, timeout: Optional[float] = None):
        pass  # No thread to stop

    @property
    def acs_updated_callback(self) -> Callable[[Any], None]:
        return self._acs_updated_callback

    def _acs_updated_callback(self, value: Any) -> None:
        if isinstance(value, LocCardUpdated):
            self._outbound_event_queue.put(value)

        if isinstance(value, AccessCard):
            self._outbound_event_queue.put(AccessCardUpdated(access_card=value))

        if isinstance(value, DoorStateUpdate):
            self._outbound_event_queue.put(value)
