import abc
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from queue import Queue, Empty
from typing import Optional, TypeVar, Generic, Callable

T = TypeVar('T')


class Worker(abc.ABC):
    def __init__(self):
        self._outbound_event_queue: Queue = Queue()

    @property
    def outbound_queue(self) -> Queue:
        return self._outbound_event_queue

    @abc.abstractmethod
    def start(self):
        pass

    @abc.abstractmethod
    def stop(self, timeout: Optional[float] = None):
        pass


class ThreadedWorker(Generic[T], Worker):
    def __init__(self):
        super().__init__()
        self._keep_running = threading.Event()
        self._wake_event = threading.Event()
        self._inbound_event_queue: Queue = Queue()

        self._thread = threading.Thread(target=self._run, daemon=True)

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def start(self):
        if self._thread.is_alive():
            return  # Can't start an already started thread

        self._thread.start()

    def stop(self, timeout: Optional[float] = None):
        if not self._thread.is_alive():
            return  # Can't stop a thread that's not running

        self._keep_running.set()
        self._wake_event.set()

        try:
            # Only call join if we're stopping it from a different thread. This has the caveat of no exceptions being
            # sent if a thread stops itself, but the only thread that does that is the worker event loop.
            if self._thread.ident != threading.current_thread().ident:
                self._thread.join(timeout)

                if self._thread.is_alive():
                    # Thread timed out
                    # TODO Handle this better as it's not necessarily the worker thread's fault that the timeout occurred
                    raise Exception("Worker thread timed out")
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

    @abc.abstractmethod
    def _run(self) -> None:
        pass

    def _cleanup(self) -> None:
        pass


@dataclass
class _CallAfterTime:
    callback: Callable[[], None]
    how_often: timedelta
    next_call: Optional[datetime] = field(default=None)


class EventsWorker(ThreadedWorker[T]):
    def __init__(self):
        super().__init__()
        self._call_after_time: list[_CallAfterTime] = []

    def _call_every(self, how_often: timedelta, callback: Callable[[], None]):
        self._call_after_time.append(_CallAfterTime(
            callback=callback,
            how_often=how_often
        ))

    def _run(self) -> None:
        self._pre_run()

        while not self._keep_running.is_set() or not self._inbound_event_queue.empty():
            # If our event queue isn't empty, we want to start the loop immediately. Yes, there's a race condition where
            # our event queue could be empty, then an item is put into the queue from another thread and notifying the
            # wake condition before we wait on it. That only delays execution by 1 second which is acceptable.
            if self._inbound_event_queue.empty() and self._wake_event.wait(1):
                self._wake_event.clear()

            now = datetime.now()
            for to_call in self._call_after_time:
                if to_call.next_call is not None and to_call.next_call > now:
                    continue

                to_call.callback()
                to_call.next_call = now + to_call.how_often

            self._pre_event()

            # There is a small race condition where we can have either two events submitted or an event and an exit
            # request that would both set the _wake_event flag. In other words, regardless of the wake event state, we
            # still want to check our _keep_running flag and see if there are any events to process.

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

            if self._keep_running.is_set() and event is None:
                # We were told to exit and have no more events to process
                break

            self._post_event()

        self._post_run()

    @abc.abstractmethod
    def _handle_event(self, event: T):
        pass

    def _pre_run(self) -> None:
        """
        Called before the event loop is started.
        """
        pass

    def _post_run(self) -> None:
        """
        Called after the event loop finishes.
        """
        pass

    def _pre_event(self) -> None:
        """
        Called before every event, regardless of if an event is available. Note that checking the queue is empty at this
        point does not guarantee that the next `get` called on the queue won't return an event.
        """
        pass

    def _post_event(self) -> None:
        """
        Called after every event, regardless of if there was an event to process. However, if the worker has been
        requested to stop and there was no event, this method will not be called.
        """
        pass
