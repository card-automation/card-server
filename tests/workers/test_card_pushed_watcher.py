from typing import Generator, Protocol

import pytest
from sqlalchemy import select, Engine
from sqlalchemy.orm import Session

from card_auto_add.windsx.db.models import LocCards
from card_auto_add.windsx.lookup.access_card import AccessCard
from card_auto_add.windsx.lookup.utils import LookupInfo
from card_auto_add.workers.card_pushed_watcher import CardPushedWatcher
from card_auto_add.workers.events import AcsDatabaseUpdated, AccessCardUpdated, AccessCardPushed, LocCardUpdated
from tests.conftest import acs_data_session, main_location_id, bad_main_location_id


@pytest.fixture
def card_pushed_watcher(
        acs_data_engine: Engine,  # Unused, but it populates the tables
        lookup_info: LookupInfo
) -> Generator[CardPushedWatcher, None, None]:
    worker = CardPushedWatcher(lookup_info)
    worker.start()

    yield worker

    worker.stop(timeout=3)


class EmptyCallable(Protocol):
    def __call__(self, timeout: int = ..., /) -> bool:
        pass


@pytest.fixture
def outbound_event_queue_empty(card_pushed_watcher: CardPushedWatcher) -> EmptyCallable:
    # Wait (timeout) to make sure the worker didn't respond to that.
    def _inner(timeout: int = 1) -> bool:
        # noinspection PyProtectedMember
        assert card_pushed_watcher._wait_on_events(2)  # Make sure it process the event
        with card_pushed_watcher.outbound_queue.not_empty:
            card_pushed_watcher.outbound_queue.not_empty.wait(timeout)
        return card_pushed_watcher.outbound_queue.qsize() == 0

    return _inner


class TestCardPushedWatcher:
    @pytest.mark.long
    def test_by_default_worker_does_nothing_on_update(self,
                                                      card_pushed_watcher: CardPushedWatcher,
                                                      outbound_event_queue_empty: EmptyCallable):
        assert card_pushed_watcher.outbound_queue.empty()

        # Just to get an initial lay of the land, worker shouldn't do anything with this
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert outbound_event_queue_empty()

    @pytest.mark.long
    def test_worker_notifies_about_updated_cards_it_knows_about(self,
                                                                lookup_info: LookupInfo,
                                                                acs_data_session: Session,
                                                                card_pushed_watcher: CardPushedWatcher,
                                                                outbound_event_queue_empty: EmptyCallable):
        access_card = AccessCard(lookup_info, 5)
        card_pushed_watcher.event(AccessCardUpdated(access_card))

        assert outbound_event_queue_empty()

        loc_cards: LocCards = acs_data_session.scalar(
            select(LocCards).where(LocCards.ID == 900)
        )
        assert loc_cards is not None
        loc_cards.DlFlag = 1
        loc_cards.CkSum = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        # The card has been updated, but not written to the hardware yet
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert outbound_event_queue_empty()

        # Now update it to have been written out
        acs_data_session.refresh(loc_cards)
        loc_cards.DlFlag = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        # The card has been written to the hardware
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert not outbound_event_queue_empty()

        card_pushed_watcher.stop(3)  # No more events for you

        # Only 1 event got emitted
        assert card_pushed_watcher.outbound_queue.qsize() == 1

        event: AccessCardPushed = card_pushed_watcher.outbound_queue.get()
        assert isinstance(event, AccessCardPushed)
        assert event.access_card is not None
        assert event.access_card.id == 5
        assert event.access_card.card_number == 2002
        assert event.access_card is not access_card  # Worker should do their own lookup

    @pytest.mark.long
    def test_loc_cards_deleted(self,
                               lookup_info: LookupInfo,
                               acs_data_session: Session,
                               card_pushed_watcher: CardPushedWatcher,
                               outbound_event_queue_empty: EmptyCallable):
        access_card = AccessCard(lookup_info, 5)
        card_pushed_watcher.event(AccessCardUpdated(access_card))

        assert outbound_event_queue_empty()

        loc_cards: LocCards = acs_data_session.scalar(
            select(LocCards).where(LocCards.ID == 900)
        )
        assert loc_cards is not None
        loc_cards.DlFlag = 2
        loc_cards.CkSum = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        # The card has been updated, but not written to the hardware yet
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert outbound_event_queue_empty()

        # Now update it to have been written out
        acs_data_session.refresh(loc_cards)
        acs_data_session.delete(loc_cards)
        acs_data_session.commit()

        # The card has been written to the hardware
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert not outbound_event_queue_empty()

        card_pushed_watcher.stop(3)  # No more events for you

        # Only 1 event got emitted
        assert card_pushed_watcher.outbound_queue.qsize() == 1

        event: AccessCardPushed = card_pushed_watcher.outbound_queue.get()
        assert isinstance(event, AccessCardPushed)
        assert event.access_card is not None
        assert event.access_card.id == 5
        assert event.access_card.card_number == 2002
        assert event.access_card is not access_card  # Worker should do their own lookup

    @pytest.mark.long
    def test_worker_notifies_after_being_explicitly_told_about_loc_card_update(self,
                                                                               acs_data_session: Session,
                                                                               card_pushed_watcher: CardPushedWatcher,
                                                                               outbound_event_queue_empty: EmptyCallable):
        loc_cards: LocCards = acs_data_session.scalar(
            select(LocCards).where(LocCards.ID == 900)
        )
        assert loc_cards is not None
        loc_cards.DlFlag = 1
        loc_cards.CkSum = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        card_pushed_watcher.event(LocCardUpdated(
            id=900,
            card_id=5,
            location_id=main_location_id
        ))

        # Wait for the event to be processed and make sure the watcher doesn't react
        assert outbound_event_queue_empty()

        # Now update it to have been written out
        acs_data_session.refresh(loc_cards)
        loc_cards.DlFlag = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        # The card has been written to the hardware
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert not outbound_event_queue_empty()

        card_pushed_watcher.stop(3)  # No more events for you

        # Only 1 event got emitted
        assert card_pushed_watcher.outbound_queue.qsize() == 1

        event: AccessCardPushed = card_pushed_watcher.outbound_queue.get()
        assert isinstance(event, AccessCardPushed)
        assert event.access_card is not None
        assert event.access_card.id == 5
        assert event.access_card.card_number == 2002

    @pytest.mark.long
    def test_updated_to_bad_location_are_ignored(self,
                                                 acs_data_session: Session,
                                                 card_pushed_watcher: CardPushedWatcher,
                                                 outbound_event_queue_empty: EmptyCallable):
        loc_cards: LocCards = LocCards(
            ID=901,
            CardID=1001,
            Loc=bad_main_location_id
        )
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        card_pushed_watcher.event(LocCardUpdated(
            id=loc_cards.ID,
            card_id=loc_cards.CardID,
            location_id=loc_cards.Loc,
        ))

        # Wait for the event to be processed and make sure the watcher doesn't react
        assert outbound_event_queue_empty()

        # Now update it to have been written out
        acs_data_session.refresh(loc_cards)
        loc_cards.DlFlag = 0
        acs_data_session.add(loc_cards)
        acs_data_session.commit()

        # The card has been written to the hardware
        card_pushed_watcher.event(AcsDatabaseUpdated())

        assert card_pushed_watcher.outbound_queue.qsize() == 0
        assert outbound_event_queue_empty()

# TODO
# - Updates from a different location group are ignored
