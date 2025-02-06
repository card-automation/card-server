import abc
import threading
from queue import Queue, Empty
from typing import Optional, TypeVar, Generic

T = TypeVar('T')


class Worker(Generic[T], abc.ABC):
    def __init__(self):
        self._keep_running = threading.Event()
        self._wake_event = threading.Event()
        self._inbound_event_queue: Queue = Queue()
        self._outbound_event_queue: Queue = Queue()

        self._thread = threading.Thread(target=self._run, daemon=False)

    def start(self):
        if self._thread.is_alive():
            return  # Can't start an already started thread

        self._thread.start()

    def stop(self, timeout: Optional[float] = None):
        if not self._thread.is_alive():
            return  # Can't stop a thread that's not running

        self._keep_running.set()
        self._wake_event.set()

        self._thread.join(timeout)
        try:
            if self._thread.is_alive():
                # Thread timed out
                # TODO Handle this better as it's not necessarily the worker thread's fault that the timeout occurred
                raise Exception("Plugin worker thread timed out")
        finally:
            self._cleanup()

    def event(self, event: T):
        self._inbound_event_queue.put(event)
        self._wake_event.set()

    def _wait_on_events(self, timeout: int):
        """
        We shouldn't need to use this in production code, but it's essential for tests. It allows us to see if all the
        events sent to this worker have been processed by the worker.

        :param timeout: How long to wait until giving up
        :return: Whether all tasks were completed
        """
        with self._inbound_event_queue.all_tasks_done:
            return self._inbound_event_queue.all_tasks_done.wait(timeout)

    @property
    def outbound_queue(self) -> Queue:
        return self._outbound_event_queue

    @abc.abstractmethod
    def _run(self) -> None:
        pass

    def _cleanup(self) -> None:
        pass


class EventsWorker(Generic[T], Worker[T]):
    def _run(self) -> None:
        while not self._keep_running.is_set() or not self._inbound_event_queue.empty():
            # If our event queue isn't empty, we want to start the loop immediately. Yes, there's a race condition where
            # our event queue could be empty, then an item is put into the queue from another thread and notifying the
            # wake condition before we wait on it. That only delays execution by 1 second which is acceptable.
            if self._inbound_event_queue.empty() and self._wake_event.wait(1):
                self._wake_event.clear()

            event: Optional[T] = None
            try:
                event = self._inbound_event_queue.get_nowait()
                self._handle_event(event)
            except Empty:
                # No event to check.
                pass
            finally:
                if event is not None:
                    self._inbound_event_queue.task_done()

    @abc.abstractmethod
    def _handle_event(self, event: T):
        pass
