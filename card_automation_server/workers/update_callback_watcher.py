from typing import Callable, Any, Optional

from card_automation_server.windsx.lookup.access_card import AccessCard, LocCardUpdate
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
        if isinstance(value, LocCardUpdate):
            self.__loc_cards(value)

        if isinstance(value, AccessCard):
            self.__access_card(value)

        if isinstance(value, DoorStateUpdate):
            self._outbound_event_queue.put(value)

    def __loc_cards(self, value: LocCardUpdate):
        self._outbound_event_queue.put(LocCardUpdated(
            id=value.id,
            card_id=value.card_id,
            location_id=value.loc
        ))

    def __access_card(self, value: AccessCard):
        self._outbound_event_queue.put(AccessCardUpdated(
            access_card=value
        ))
