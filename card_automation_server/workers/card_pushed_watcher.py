from dataclasses import dataclass
from typing import Union, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from card_automation_server.windsx.db.models import LocCards, LOC
from card_automation_server.windsx.lookup.access_card import AccessCard
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.events import AcsDatabaseUpdated, AccessCardUpdated, AccessCardPushed, LocCardUpdated
from card_automation_server.workers.utils import EventsWorker

# What events does this worker accept? Used for type hinting
_CardPushedWatcherEvents = Union[
    AcsDatabaseUpdated,
    AccessCardUpdated,
    LocCardUpdated
]


@dataclass(frozen=True)
class LocCardInfo:
    id: int
    card_id: int
    location_id: int


class CardPushedWatcher(EventsWorker[_CardPushedWatcherEvents]):
    def __init__(self,
                 lookup_info: LookupInfo):
        self._lookup_info = lookup_info
        self._acs_session = Session(self._lookup_info.acs_engine)
        self._loc_cards: dict[int, LocCardInfo] = {}
        self._card_ids_to_location_updates: dict[int, set[int]] = {}

        self._locations = set(self._acs_session.scalars(
            select(LOC.Loc)
            .where(LOC.LocGrp == self._lookup_info.location_group_id)
        ))

        super().__init__()

    def _cleanup(self) -> None:
        self._acs_session.close()

    def _handle_event(self, event: _CardPushedWatcherEvents):
        if isinstance(event, LocCardUpdated):
            loc_card_info = LocCardInfo(
                id=event.id,
                card_id=event.card_id,
                location_id=event.location_id,
            )

            self._maybe_watch_loc_card(loc_card_info)

        # Go through all the LocCards we're waiting on to be updated
        self._update_pending_loc_cards()

        # If all locations for a card have been updated, we can tell others about it.
        self._notify_of_card_pushed()

        # Now we need to see what LocCards need updates, in case we don't yet have them.
        self._bring_in_new_cards()

    def _update_pending_loc_cards(self):
        if len(self._loc_cards) == 0:
            return

        loc_cards: Sequence[LocCards] = self._acs_session.scalars(
            select(LocCards).where(LocCards.ID.in_(self._loc_cards.keys()))
        ).all()
        retrieved_cards = set(x.ID for x in loc_cards)

        for lc_id, lc_info in self._loc_cards.copy().items():
            card_location_updated = False
            # If it was deleted, then that's an update for a card losing access
            if lc_id not in retrieved_cards:
                card_location_updated = True
            else:
                loc_card = [x for x in loc_cards if x.ID == lc_id][0]

                if loc_card.DlFlag == 0:
                    card_location_updated = True

            if not card_location_updated:
                continue

            if lc_info.location_id in self._card_ids_to_location_updates[lc_info.card_id]:
                self._card_ids_to_location_updates[lc_info.card_id].remove(lc_info.location_id)

            del self._loc_cards[lc_id]

    def _notify_of_card_pushed(self):
        for card_id, locations in self._card_ids_to_location_updates.items():
            if len(locations) > 0:
                continue  # Not all locations have been updated yet

            self.outbound_queue.put(
                AccessCardPushed(
                    AccessCard(self._lookup_info, card_id)
                )
            )

    def _bring_in_new_cards(self):
        pending_loc_cards = self._acs_session.scalars(
            select(LocCards)
            .join(LOC, LOC.Loc == LocCards.Loc)
            .where(LOC.LocGrp == self._lookup_info.location_group_id)
            .where(LocCards.DlFlag != 0)
        ).all()
        for loc_card in pending_loc_cards:
            loc_card_info = LocCardInfo(
                id=loc_card.ID,
                card_id=loc_card.CardID,
                location_id=loc_card.Loc
            )

            self._maybe_watch_loc_card(loc_card_info)

    def _maybe_watch_loc_card(self, loc_card_info: LocCardInfo):
        if loc_card_info.id in self._loc_cards:
            return  # No need to add it a second time, we're still waiting for it to be pushed

        if loc_card_info.location_id not in self._locations:
            return  # We don't watch over this location, ignore it

        self._loc_cards[loc_card_info.id] = loc_card_info

        if loc_card_info.card_id not in self._card_ids_to_location_updates:
            self._card_ids_to_location_updates[loc_card_info.card_id] = set()

        card_locations = self._card_ids_to_location_updates[loc_card_info.card_id]
        if loc_card_info.location_id not in card_locations:
            card_locations.add(loc_card_info.location_id)
