import threading

import pytest

from card_auto_add.workers.events import AcsDatabaseUpdated, LogDatabaseUpdated
from card_auto_add.workers.utils import ThreadedWorker, EventsWorker
from card_auto_add.workers.worker_event_loop import WorkerEventLoop


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

        # We add accepting first, since emitting will emit immediately.
        event_loop.add(unaccepting)
        event_loop.add(emitting)

        assert not unaccepting.called.wait(1)
        assert unaccepting.sent_event is None
