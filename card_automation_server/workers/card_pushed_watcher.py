from typing import Union

from sqlalchemy import select

from card_automation_server.config import Config
from card_automation_server.plugins.types import CommServerEventType
from card_automation_server.windsx.db.models import LocCards, LOC
from card_automation_server.windsx.lookup.access_card import AccessCardLookup
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.events import AcsDatabaseUpdated, AccessCardUpdated, AccessCardPushed, \
    LocCardUpdated, RawCommServerEvent
from card_automation_server.workers.utils import EventsWorker

# What events does this worker accept? Used for type hinting
_Events = Union[
    AcsDatabaseUpdated,
    AccessCardUpdated,
    LocCardUpdated,
    RawCommServerEvent,
]


class CardPushedWatcher(EventsWorker[_Events]):
    def __init__(self,
                 config: Config,
                 lookup_info: LookupInfo):
        self._logger = config.logger
        self._lookup_info = lookup_info
        self._loc_cards: dict[int, LocCardUpdated] = {}
        self._card_ids_to_location_updates: dict[int, set[int]] = {}

        with self._lookup_info.new_session() as session:
            self._locations = set(session.scalars(
                select(LOC.Loc)
                .where(LOC.LocGrp == self._lookup_info.location_group_id)
            ))

        super().__init__()

    def _handle_event(self, event: _Events):
        if isinstance(event, LocCardUpdated):
            # Watch the card directly
            self._maybe_watch_loc_card(event)

        # We need to see what LocCards need updates, in case we don't yet have them.
        self._bring_in_new_cards()

        # Go through all the LocCards we're waiting on to be updated
        self._update_pending_loc_cards()

        # If all locations for a card have been updated, we can tell others about it.
        self._notify_of_card_pushed()

    def _update_pending_loc_cards(self):
        if len(self._loc_cards) == 0:
            return

        with self._lookup_info.new_session() as session:
            dl_flags: dict[int, int] = {
                row.ID: row.DlFlag
                for row in session.scalars(
                    select(LocCards).where(LocCards.ID.in_(self._loc_cards.keys()))
                ).all()
            }

        for lc_id, lc_info in self._loc_cards.copy().items():
            card_location_updated = False
            # If it was deleted, then that's an update for a card losing access
            if lc_id not in dl_flags:
                self._logger.debug(f"LocCard {lc_id} (card {lc_info.card_id}) was deleted from DB")
                card_location_updated = True
            else:
                self._logger.debug(f"LocCard {lc_id} (card {lc_info.card_id}) DlFlag={dl_flags[lc_id]}")

                if dl_flags[lc_id] == 0:
                    card_location_updated = True

            if not card_location_updated:
                continue

            if lc_info.location_id in self._card_ids_to_location_updates[lc_info.card_id]:
                self._card_ids_to_location_updates[lc_info.card_id].remove(lc_info.location_id)

            del self._loc_cards[lc_id]

    def _notify_of_card_pushed(self):
        for card_id, locations in self._card_ids_to_location_updates.copy().items():
            if len(locations) > 0:
                self._logger.debug(f"Card {card_id} still waiting on locations {locations}")
                continue  # Not all locations have been updated yet

            card = AccessCardLookup(self._lookup_info).by_id(card_id)
            del self._card_ids_to_location_updates[card_id]

            if card is not None:
                self.outbound_queue.put(AccessCardPushed(card))

    def _bring_in_new_cards(self):
        with self._lookup_info.new_session() as session:
            pending_loc_cards = [
                LocCardUpdated(id=row.ID, card_id=row.CardID, location_id=row.Loc)
                for row in session.scalars(
                    select(LocCards)
                    .join(LOC, LOC.Loc == LocCards.Loc)
                    .where(LOC.LocGrp == self._lookup_info.location_group_id)
                    .where(LocCards.DlFlag != 0)
                ).all()
            ]

        for loc_card in pending_loc_cards:
            self._logger.debug(f"Found pending LocCard {loc_card.id} (card {loc_card.card_id})")
            self._maybe_watch_loc_card(loc_card)

    def _maybe_watch_loc_card(self, event: LocCardUpdated):
        if event.id in self._loc_cards:
            return  # No need to add it a second time, we're still waiting for it to be pushed

        if event.location_id not in self._locations:
            self._logger.debug(f"LocCard {event.id} skipped: location {event.location_id} not in watched locations {self._locations}")
            return  # We don't watch over this location, ignore it

        self._logger.debug(f"Watching LocCard {event.id} (card {event.card_id}, location {event.location_id})")
        self._loc_cards[event.id] = event

        if event.card_id not in self._card_ids_to_location_updates:
            self._card_ids_to_location_updates[event.card_id] = set()

        card_locations = self._card_ids_to_location_updates[event.card_id]
        if event.location_id not in card_locations:
            card_locations.add(event.location_id)
