import signal
import sys
import time
from typing import Optional

import sentry_sdk
from platformdirs import PlatformDirs
from sentry_sdk import capture_exception

from card_automation_server.config import Config
from card_automation_server.ioc import Resolver
from card_automation_server.plugin_loader import PluginLoader
from card_automation_server.windsx.db.engine_factory import EngineFactory
from card_automation_server.windsx.engines import AcsEngine, LogEngine
from card_automation_server.windsx.lookup.access_card import AccessCardLookup
from card_automation_server.windsx.lookup.acl_group_combo import AclGroupComboLookup
from card_automation_server.windsx.lookup.person import PersonLookup
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.card_pushed_watcher import CardPushedWatcher
from card_automation_server.workers.card_scan_watcher import CardScanWatcher
from card_automation_server.workers.comm_server_restarter import CommServerRestarter
from card_automation_server.workers.database_file_watcher import DatabaseFileWatcher
from card_automation_server.workers.door_override_controller import DoorOverrideController
from card_automation_server.workers.dsx_hardware_reset_worker import DSXHardwareResetWorker
from card_automation_server.workers.update_callback_watcher import UpdateCallbackWatcher
from card_automation_server.workers.worker_event_loop import WorkerEventLoop


class CardAutomationServer:
    def __init__(self):
        self._resolver = Resolver()
        self._platformdirs: PlatformDirs = PlatformDirs("card-server", "card-automation")
        self._resolver.singleton(self._platformdirs)

        self._config = self._resolver.singleton(Config)
        sentry_sdk.init(self._config.sentry.dsn)

        self._worker_event_loop = self._resolver.singleton(WorkerEventLoop)
        self._worker_event_loop.start()

        # Create our type hinted engines
        acs_engine = EngineFactory.microsoft_access(self._config.windsx.acs_data_db_path)
        self._resolver.singleton(AcsEngine, acs_engine)
        log_engine = EngineFactory.microsoft_access(self._config.windsx.log_db_path)
        self._resolver.singleton(LogEngine, log_engine)

        # Needed to create LookupInfo object
        update_callback_watcher = self._resolver.singleton(UpdateCallbackWatcher)

        lookup_info: LookupInfo = self._resolver(LookupInfo,
                                                 location_group_id=self._config.windsx.location_group,
                                                 updated_callback=update_callback_watcher.acs_updated_callback,
                                                 )
        self._resolver.singleton(lookup_info)

        # These get carried over to the plugins directly, might as well make them now
        self._resolver.singleton(AccessCardLookup)
        self._resolver.singleton(AclGroupComboLookup)
        self._resolver.singleton(PersonLookup)

        database_file_watcher = self._resolver(DatabaseFileWatcher,
                                               acs_db_path=self._config.windsx.acs_data_db_path,
                                               log_db_path=self._config.windsx.log_db_path,
                                               )

        door_override_controller = self._resolver(DoorOverrideController,
                                                  workstation_number=self._config.windsx.workstation_number,
                                                  comm_server_host=self._config.windsx.cs_host,
                                                  comm_server_port=self._config.windsx.cs_port)

        self._worker_event_loop.add(
            # When someone updates a data model.
            self._resolver.singleton(update_callback_watcher),
            # When the comm server isn't running, we restart it
            self._resolver.singleton(CommServerRestarter),
            # When the card can't be pushed, and we have to give the hardware a little nudge
            self._resolver.singleton(DSXHardwareResetWorker),
            # When our databases on disk updates
            self._resolver.singleton(database_file_watcher),
            # When someone badges in
            self._resolver.singleton(CardScanWatcher),
            # We want to provide updates for when we see a card is pushed out
            self._resolver.singleton(CardPushedWatcher),
            # Allow plugins to override their doors
            self._resolver.singleton(door_override_controller),
        )

        for owner_repo, plugin in self._config.plugins.items():
            if plugin.commit is None:
                continue  # We're not ready to load this plugin

            owner, repo = owner_repo.split("/")
            # Resolve the plugin loader to load the plugin. We only need to specify the owner and repo, everything else
            # is type hinted.
            try:
                self._resolver(PluginLoader, owner=owner, repo=repo)
            except BaseException as ex:
                capture_exception(ex)

    @property
    def is_alive(self) -> bool:
        return self._worker_event_loop.is_alive

    def stop(self):
        self._worker_event_loop.stop()


cas: Optional[CardAutomationServer] = None


def main():
    global cas
    cas = CardAutomationServer()
    while cas.is_alive:
        time.sleep(1)


def handle_interrupt(_, __):
    global cas
    if cas is not None:
        cas.stop()
    sys.exit(1)  # Exit with an error code so our calling function doesn't try to restart us


signal.signal(signal.SIGINT, handle_interrupt)

if __name__ == '__main__':
    main()
