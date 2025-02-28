import threading
from typing import Union

import pytest

from card_automation_server.workers.events import AcsDatabaseUpdated, LogDatabaseUpdated, ApplicationRestartNeeded
from card_automation_server.workers.utils import ThreadedWorker, EventsWorker
from card_automation_server.workers.worker_event_loop import WorkerEventLoop


class EmittingWorker(ThreadedWorker[None]):
    def _run(self) -> None:
        self._outbound_event_queue.put(AcsDatabaseUpdated())


class AcceptingWorker(EventsWorker[AcsDatabaseUpdated]):
    def __init__(self):
        super().__init__()
        self.called = threading.Event()
        self.sent_event = None

    def _handle_event(self, event):
        self.sent_event = event
        self.called.set()


class UnacceptingWorker(EventsWorker[LogDatabaseUpdated]):
    def __init__(self):
        super().__init__()
        self.called = threading.Event()
        self.sent_event = None

    def _handle_event(self, event):
        self.sent_event = event
        self.called.set()


class UnionEventWorker(EventsWorker[Union[AcsDatabaseUpdated, LogDatabaseUpdated]]):
    def __init__(self):
        super().__init__()
        self.called = threading.Event()
        self.sent_event = None

    def _handle_event(self, event):
        self.sent_event = event
        self.called.set()


@pytest.fixture
def event_loop():
    worker = WorkerEventLoop()

    worker.start()

    yield worker

    worker.stop(3)  # Tests should timeout pretty fast


class TestWorkerEventLoop:
    @pytest.mark.long
    def test_will_propagate_wanted_event(self, event_loop: WorkerEventLoop):
        accepting = AcceptingWorker()
        emitting = EmittingWorker()

        # We add accepting first, since emitting will emit immediately.
        event_loop.add(accepting)
        event_loop.add(emitting)

        assert accepting.called.wait(1)
        assert isinstance(accepting.sent_event, AcsDatabaseUpdated)

    @pytest.mark.long
    def test_will_not_propagate_unwanted_event(self, event_loop: WorkerEventLoop):
        unaccepting = UnacceptingWorker()
        emitting = EmittingWorker()

        # We add unaccepting first, since emitting will emit immediately.
        event_loop.add(unaccepting)
        event_loop.add(emitting)

        assert not unaccepting.called.wait(1)
        assert unaccepting.sent_event is None

    @pytest.mark.long
    def test_can_handle_union_event_type(self, event_loop: WorkerEventLoop):
        union = UnionEventWorker()
        emitting = EmittingWorker()

        # We add accepting first, since emitting will emit immediately.
        event_loop.add(union)
        event_loop.add(emitting)

        assert union.called.wait(1)
        assert isinstance(union.sent_event, AcsDatabaseUpdated)

    @pytest.mark.long
    def test_add_all(self, event_loop: WorkerEventLoop):
        # Same setup as test_will_propagate_wanted_event, we're just adding them all in one call
        accepting = AcceptingWorker()
        emitting = EmittingWorker()

        # We add accepting first, since emitting will emit immediately.
        event_loop.add(
            accepting,
            emitting
        )

        assert accepting.called.wait(1)
        assert isinstance(accepting.sent_event, AcsDatabaseUpdated)

    @pytest.mark.long
    def test_getting_restart_event_kills_event_loop(self, event_loop: WorkerEventLoop):
        assert event_loop.is_alive

        event_loop.event(ApplicationRestartNeeded())

        assert event_loop._wait_on_events(3)

        assert not event_loop.is_alive