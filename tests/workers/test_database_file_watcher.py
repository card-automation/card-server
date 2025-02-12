from pathlib import Path

import pytest

from card_auto_add.workers.database_file_watcher import DatabaseFileWatcher
from card_auto_add.workers.events import AcsDatabaseUpdated, LogDatabaseUpdated


@pytest.fixture
def database_file_watcher(
        acs_db_path: Path,
        log_db_path: Path
):
    watcher = DatabaseFileWatcher(
        acs_db_path,
        log_db_path
    )

    watcher.start()

    yield watcher

    watcher.stop(3)  # Tests should timeout pretty fast


class TestDatabaseFileWatcher:
    @pytest.mark.long  # Only long if it times out, really
    def test_emits_acs_updated_event(self,
                                     acs_db_path: Path,
                                     database_file_watcher: DatabaseFileWatcher):
        print(acs_db_path)

        with acs_db_path.open('w+') as fh:
            fh.writelines("Fake DB update")  # Our watcher doesn't care about the contents, only the file update

        with database_file_watcher.outbound_queue.not_empty:
            database_file_watcher.outbound_queue.not_empty.wait(3)

        assert database_file_watcher.outbound_queue.qsize() == 1

        event = database_file_watcher.outbound_queue.get()
        assert isinstance(event, AcsDatabaseUpdated)

    @pytest.mark.long  # Only long if it times out, really
    def test_emits_log_updated_event(self,
                                     log_db_path: Path,
                                     database_file_watcher: DatabaseFileWatcher):
        print(log_db_path)

        with log_db_path.open('w+') as fh:
            fh.writelines("Fake DB update")  # Our watcher doesn't care about the contents, only the file update

        with database_file_watcher.outbound_queue.not_empty:
            database_file_watcher.outbound_queue.not_empty.wait(3)

        assert database_file_watcher.outbound_queue.qsize() == 1

        event = database_file_watcher.outbound_queue.get()
        assert isinstance(event, LogDatabaseUpdated)
