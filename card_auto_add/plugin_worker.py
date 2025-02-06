import queue
import threading
import time
from queue import Queue
from threading import Thread
from typing import Optional, Union

from card_auto_add.plugins.interfaces import Plugin, PluginStartup, PluginShutdown, PluginCardScanned, PluginLoop
from card_auto_add.plugins.types import CardScan

PluginEvent = Union[CardScan]


class PluginWorker:
    def __init__(self, plugin: Plugin):
        self._plugin: Plugin = plugin

        self._keep_running = threading.Event()
        self._wake_event = threading.Event()
        self._event_queue: Queue = Queue()

        self._thread = Thread(target=self._run, daemon=False)

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
        if self._thread.is_alive():
            # Thread timed out
            # TODO Handle this better as it's not necessarily the worker thread's fault that the timeout occurred
            raise Exception("Plugin worker thread timed out")

    def event(self, event: PluginEvent):
        self._event_queue.put(event)
        self._wake_event.set()

    def _run(self):
        # TODO None of these methods we're calling touch error handling atm. I'm thinking we make a new object that's
        # a monkey patched version of the plugin we're given that implements the same classes but otherwise just
        # delegates to the plugin itself with error handling wrapped. Makes the code below simpler.

        if isinstance(self._plugin, PluginStartup):
            self._plugin.startup()

        next_loop_call_time = time.monotonic_ns()

        # If we've been told to exit, but still have events to send, we won't exit yet.
        while not self._keep_running.is_set() or not self._event_queue.empty():
            # Wait max of 1 second before continuing the loop. This balances delaying the thread's exit when requested
            # and handling events vs running a very tight CPU heavy loop.
            if self._wake_event.wait(1):
                self._wake_event.clear()

            # There is a small race condition where we can have either two events submitted or an event and an exit
            # request that would both set the _wake_event flag. In other words, regardless of the wake event state, we
            # still want to check our _keep_running flag and see if there are any events to process.

            event: Optional[PluginEvent] = None
            try:
                event = self._event_queue.get_nowait()
                self._handle_event(event)
            except queue.Empty:
                # No event to check.
                pass
            finally:
                if event is not None:
                    self._event_queue.task_done()

            if self._keep_running.is_set() and event is None:
                # We were told to exit and have no more events to process
                break

            current_time_ns = time.monotonic_ns()
            if isinstance(self._plugin, PluginLoop) and current_time_ns > next_loop_call_time:
                time_to_wait = self._plugin.loop()
                if time_to_wait is None:
                    time_to_wait = 0

                # Must be >= 0
                time_to_wait = max(time_to_wait, 0)

                next_loop_call_time = current_time_ns + (time_to_wait * 1_000_000_000)

        if isinstance(self._plugin, PluginShutdown):
            self._plugin.shutdown()

    def _handle_event(self, event: PluginEvent):
        if isinstance(event, CardScan) and isinstance(self._plugin, PluginCardScanned):
            self._plugin.card_scanned(event)
