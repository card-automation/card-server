import threading
from queue import Empty
from typing import Any

from card_automation_server.config import Config
from card_automation_server.workers.events import WorkerEvent, ApplicationRestartNeeded
from card_automation_server.workers.utils import Worker, EventsWorker


class _WorkerMonitorThread:
    def __init__(self,
                 event_loop: 'WorkerEventLoop',
                 worker: Worker
                 ):
        self._event_loop = event_loop
        self._worker = worker
        self.stop_running = threading.Event()

        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        while not self.stop_running.is_set():
            try:
                event = self._worker.outbound_queue.get(timeout=1)

                if not isinstance(event, WorkerEvent):
                    continue

                self._event_loop.event(event)
            except Empty:
                pass

        # We're done now, the worker can be stopped
        self._worker.stop(30)


class WorkerEventLoop(EventsWorker[Any]):
    def __init__(self, config: Config):
        super().__init__()
        self._log = config.logger
        self._worker_threads: list[_WorkerMonitorThread] = []
        self._event_to_workers: dict[WorkerEvent, list[EventsWorker]] = {}

    def add(self, *workers: Worker):
        for worker in workers:
            self._add(worker)

    def _add(self, worker: Worker):
        if isinstance(worker, EventsWorker):
            bases = worker.__orig_bases__  # noqa
            event_worker_base = [b for b in bases if b.__origin__ == EventsWorker][0]

            def _yield_args(_args):
                for _arg in _args:
                    if hasattr(_arg, '__args__'):
                        for _a in _yield_args(_arg.__args__):
                            yield _a
                    elif hasattr(_arg, '__mro__'):
                        if WorkerEvent not in _arg.__mro__:
                            continue
                        yield _arg  # Yield only worker events

            args = list(_yield_args(event_worker_base.__args__))
            for arg in args:
                if arg not in self._event_to_workers:
                    self._event_to_workers[arg] = []

                self._event_to_workers[arg].append(worker)

        self._worker_threads.append(_WorkerMonitorThread(self, worker))

        worker.start()

    def _cleanup(self) -> None:
        for worker_thread in self._worker_threads:
            worker_thread.stop_running.set()

    def _handle_event(self, event: Any):
        self._log.debug(f"Event: {event.__class__.__name__}")
        if event.__class__ == ApplicationRestartNeeded:
            self._log.info("Stopping Worker Event Loop to restart app")
            self.stop()
            return

        if event.__class__ not in self._event_to_workers:
            return

        workers = self._event_to_workers[event.__class__]
        worker: EventsWorker
        for worker in workers:
            self._log.debug(f"Sending to {worker.__class__.__name__}")
            worker.event(event)
