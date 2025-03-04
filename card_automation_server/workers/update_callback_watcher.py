from typing import Callable, Any, Optional

from card_automation_server.windsx.db.models import LocCards
from card_automation_server.windsx.lookup.access_card import AccessCard
from card_automation_server.workers.events import LocCardUpdated, AccessCardUpdated
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
        print(f"Got an update  callback: {value}")
        if isinstance(value, LocCards):
            self.__loc_cards(value)

        if isinstance(value, AccessCard):
            self.__access_card(value)

    def __loc_cards(self, value: LocCards):
        self._outbound_event_queue.put(LocCardUpdated(
            id=value.ID,
            card_id=value.CardID,
            location_id=value.Loc
        ))

    def __access_card(self, value: AccessCard):
        self._outbound_event_queue.put(AccessCardUpdated(
            access_card=value
        ))
