import logging
from logging import Logger
from logging.handlers import RotatingFileHandler

import sentry_sdk
from platformdirs import PlatformDirs

from card_auto_add.config import Config
from card_auto_add.ioc import Resolver
from card_auto_add.windsx.db.engine_factory import EngineFactory
from card_auto_add.windsx.engines import AcsEngine, LogEngine
from card_auto_add.windsx.lookup.utils import LookupInfo
from card_auto_add.workers.card_pushed_watcher import CardPushedWatcher
from card_auto_add.workers.card_scan_watcher import CardScanWatcher
from card_auto_add.workers.comm_server_restarter import CommServerRestarter
from card_auto_add.workers.database_file_watcher import DatabaseFileWatcher
from card_auto_add.workers.door_override_controller import DoorOverrideController
from card_auto_add.workers.dsx_hardware_reset_worker import DSXHardwareResetWorker
from card_auto_add.workers.update_callback_watcher import UpdateCallbackWatcher
from card_auto_add.workers.worker_event_loop import WorkerEventLoop


class CardAutomationServer:
    def __init__(self, logger: Logger):
        self._resolver = Resolver()
        self._platformdirs: PlatformDirs = PlatformDirs("card-server", "card-automation")
        self._logger = self._resolver.singleton(Logger, logger)
        self._config = self._resolver(Config)
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


def main():
    logger = logging.getLogger("card_access")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console logging handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File logging handler
    max_bytes = 1 * 1024 * 1024
    file_handler = RotatingFileHandler("C:/Users/700 Kalamath/.cards/card_access.log",
                                       maxBytes=max_bytes,
                                       backupCount=10)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    cas = CardAutomationServer(logger)
    # TODO Keep thread alive


# TODO Support OS signal for termination

if __name__ == '__main__':
    main()
