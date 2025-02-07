import time
from typing import Union

from card_auto_add.plugins.interfaces import Plugin, PluginStartup, PluginShutdown, PluginCardScanned, PluginLoop
from card_auto_add.plugins.types import CardScan
from card_auto_add.workers.utils import EventsWorker

_PluginEvent = Union[CardScan]


class PluginWorker(EventsWorker[_PluginEvent]):
    def __init__(self, plugin: Plugin):
        self._plugin: Plugin = plugin
        self._next_loop_call_time = time.monotonic_ns()
        super().__init__()

    # TODO None of these methods we're calling touch error handling atm. I'm thinking we make a new object that's
    # a monkey patched version of the plugin we're given that implements the same classes but otherwise just
    # delegates to the plugin itself with error handling wrapped. Makes the code below simpler.

    def _pre_run(self) -> None:
        if isinstance(self._plugin, PluginStartup):
            self._plugin.startup()

    def _post_event(self) -> None:
        current_time_ns = time.monotonic_ns()
        if isinstance(self._plugin, PluginLoop) and current_time_ns > self._next_loop_call_time:
            time_to_wait = self._plugin.loop()
            if time_to_wait is None:
                time_to_wait = 0

            # Must be >= 0
            time_to_wait = max(time_to_wait, 0)

            self._next_loop_call_time = current_time_ns + (time_to_wait * 1_000_000_000)

    def _post_run(self) -> None:
        if isinstance(self._plugin, PluginShutdown):
            self._plugin.shutdown()

    def _handle_event(self, event: _PluginEvent):
        if isinstance(event, CardScan) and isinstance(self._plugin, PluginCardScanned):
            self._plugin.card_scanned(event)
