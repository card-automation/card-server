import threading
import time
from datetime import datetime
from typing import Optional

import pytest

from card_auto_add.plugins.interfaces import PluginStartup, PluginShutdown, PluginCardScanned, PluginLoop, \
    PluginCardDataPushed
from card_auto_add.plugins.types import CardScan, CardScanEventType
from card_auto_add.windsx.lookup.access_card import AccessCard, AccessCardLookup
from card_auto_add.workers.events import AccessCardPushed, CardScanned
from tests.conftest import PluginWorkerFactory, main_location_id


class HasAssertableFlag:
    def __init__(self):
        self.called = threading.Event()


class TestPluginWorker:
    def test_startup(self, plugin_worker_factory: PluginWorkerFactory):
        class _Started(HasAssertableFlag, PluginStartup):
            def startup(self):
                self.called.set()

        plugin = _Started()

        assert not plugin.called.is_set()

        plugin_worker_factory(plugin)

        assert plugin.called.is_set()

    def test_shutdown(self, plugin_worker_factory: PluginWorkerFactory):
        class _Shutdown(HasAssertableFlag, PluginShutdown):
            def shutdown(self):
                self.called.set()

        plugin = _Shutdown()
        worker = plugin_worker_factory(plugin)

        assert not plugin.called.is_set()

        worker.stop(3)

        assert plugin.called.is_set()

    def test_card_scanned(self, plugin_worker_factory: PluginWorkerFactory):
        class _CardScanned(HasAssertableFlag, PluginCardScanned):
            def __init__(self):
                super().__init__()
                self.scan_data: Optional[CardScan] = None

            def card_scanned(self, scan_data: CardScan):
                self.called.set()
                self.scan_data = scan_data

        plugin = _CardScanned()
        worker = plugin_worker_factory(plugin)

        assert not plugin.called.is_set()

        card_scan = CardScan(
            name_id=101,
            card_number=3000,
            scan_time=datetime.now(),
            device=0,
            event_type=CardScanEventType.ACCESS_GRANTED,
            location_id=main_location_id
        )
        event = CardScanned(
            card_scan=card_scan
        )
        worker.event(event)

        assert plugin.called.wait(1)
        assert plugin.scan_data is card_scan

    def test_card_data_pushed(self,
                              plugin_worker_factory: PluginWorkerFactory,
                              access_card_lookup: AccessCardLookup
                              ):
        class _CardDataPushed(HasAssertableFlag, PluginCardDataPushed):
            def __init__(self):
                super().__init__()
                self.access_card: Optional[AccessCard] = None

            def card_data_pushed(self, access_card: AccessCard) -> None:
                self.called.set()
                self.access_card = access_card

        plugin = _CardDataPushed()
        worker = plugin_worker_factory(plugin)

        assert not plugin.called.is_set()

        access_card = access_card_lookup.by_card_number(2002)
        event = AccessCardPushed(
            access_card=access_card
        )
        worker.event(event)

        assert plugin.called.wait(1)
        assert plugin.access_card is access_card

    @pytest.mark.long  # This test takes ~7 seconds if successful, ~15 worst case if unsuccessful.
    def test_loop_timing(self, plugin_worker_factory: PluginWorkerFactory):
        class _Loop(HasAssertableFlag, PluginLoop):
            def __init__(self):
                super().__init__()
                self.loop_call_times = []

            # Return value is 1, 2, 3, and 100 in order. After that, we set called so the test can stop the worker with
            # no more calls to loop.
            def loop(self) -> int:
                if self.called.is_set():
                    raise Exception("loop should not have been called after the called flag was set")

                self.loop_call_times.append(time.monotonic_ns())

                if len(self.loop_call_times) == 4:
                    self.called.set()
                    return 4

                return len(self.loop_call_times)

        plugin = _Loop()
        worker = plugin_worker_factory(plugin)

        assert plugin.called.wait(15)
        worker.stop(3)

        assert len(plugin.loop_call_times) == 4  # The code above should verify this indirectly, but better be explicit
        timings = []
        for i in range(len(plugin.loop_call_times) - 1):
            timing = (plugin.loop_call_times[i + 1] - plugin.loop_call_times[i]) // 1_000_000_000
            timings.append(timing)

        # This is the part that actually checks we didn't call loop again until requested.
        assert timings == [1, 2, 3]

    @pytest.mark.long  # We push 5 events, so this test takes ~6 seconds, ~10 worst case if unsuccessful.
    def test_all_events_get_processed_before_exiting(self, plugin_worker_factory: PluginWorkerFactory):
        class _CardScanned(HasAssertableFlag, PluginCardScanned):
            def __init__(self):
                super().__init__()
                self.called_times = 0

            def card_scanned(self, scan_data: CardScan):
                self.called.set()
                self.called_times += 1
                time.sleep(0.25)

        plugin = _CardScanned()
        worker = plugin_worker_factory(plugin)

        card_scan = CardScan(
            name_id=101,
            card_number=3000,
            scan_time=datetime.now(),
            device=0,
            event_type=CardScanEventType.ACCESS_GRANTED,
            location_id=main_location_id
        )
        event = CardScanned(card_scan)
        # Queue that event 5 times. It shouldn't matter what event it is, just that we've queued it faster than the
        # events can be processed. We will process an event faster than once per second if the wait event flag is set
        # and cleared in time for the next event to be submitted. That potentially could happen after the first event
        # submitted, but for the third and onward the event would have to be processed first. We sleep for 0.25 seconds
        # on each event to ensure that can't happen too quickly.
        for i in range(5):
            worker.event(event)

        # Assert that we haven't yet been called 5 times, just as a safety net
        assert plugin.called_times < 5

        worker.stop(10)

        # 5 events, should have been called 5 times. If it exits early, this won't be called 5 times.
        assert plugin.called_times == 5
