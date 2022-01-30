import os
import subprocess
import time
from ctypes import Structure, windll, c_uint, sizeof, byref
from glob import glob
from threading import Thread

from sentry_sdk import capture_exception
from pywinauto.application import Application, ProcessNotFoundError

from card_auto_add.config import Config


class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


class DSXApiWatcher(object):
    def __init__(self, config: Config):
        self.dsx_path = config.windsx_path
        self._no_interaction_delay = config.no_interaction_delay
        self.db_path = os.path.join(self.dsx_path, "DB.exe")
        self.dsx_username = config.windsx_username
        self.dsx_password = config.windsx_password
        self._need_to_run_windsx = False
        self._logger = config.logger

    def start(self):
        thread = Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        attempt_count = 0
        max_attempts = 100

        while attempt_count < max_attempts:
            try:
                if not self._need_to_run_windsx:
                    api_files = glob(self.dsx_path + os.path.sep + "^IMP[0-9][0-9].txt")

                    if len(api_files) > 0:
                        for api in api_files:
                            self._logger.info(f"WinDSX Api file Found: {api}")

                        self._need_to_run_windsx = True

                no_interaction_time = self._current_no_interaction_time
                if self._need_to_run_windsx:
                    if no_interaction_time > self._no_interaction_delay:
                        self._login_and_close_windsx()
                        return
                    else:
                        sleep_time = self._no_interaction_delay - no_interaction_time + 1

                        self._logger.info("We need to run DSX, but someone has interacted with the computer too recently")
                        self._logger.info(f"Will sleep for {sleep_time} seconds and check again.")

                        time.sleep(sleep_time)
                        attempt_count += 1
                        if attempt_count >= max_attempts:
                            raise Exception(f"We've tried to submit this card {max_attempts} times but can't because the computer is in use.")
                else:
                    time.sleep(60)

            except Exception as e:
                self._logger.info("Oh no, something happened!")
                self._logger.info(e)
                capture_exception(e)

    @property
    def _current_no_interaction_time(self):
        last_input_info = LASTINPUTINFO()
        last_input_info.cbSize = sizeof(last_input_info)
        windll.user32.GetLastInputInfo(byref(last_input_info))
        millis = windll.kernel32.GetTickCount() - last_input_info.dwTime
        return millis / 1000.0

    def _login_and_close_windsx(self):
        # TODO Handle being on the lock screen
        app = self._get_windsx_app()

        for window in app.windows():
            self._logger.info(window)

        # TODO Handle Login window not being open/visible
        app.Login.Edit0.set_edit_text(self.dsx_username)
        app.Login.Edit1.set_edit_text(self.dsx_password)
        app.Login.OK.click()
        time.sleep(60)
        # TODO Handle Database window not being open/visible
        app.Database.close(60)

        self._need_to_run_windsx = False

    def _open_windsx(self):
        subprocess.Popen([self.db_path])
        time.sleep(5)

    def _get_windsx_app(self):
        app = None
        attempts = 0
        TOTAL_ATTEMPTS = 5
        while app is None:
            try:
                attempts = attempts + 1
                self._logger.info("Trying to get reference to windsx app")
                app = Application().connect(path=self.db_path)
                self._logger.info("Got it!")
            except ProcessNotFoundError:
                attempts_remaining = TOTAL_ATTEMPTS - attempts
                self._logger.info(
                    f"Failed to connect to WinDSX, trying to open, {attempts_remaining} attempt(s) remaining...")
                self._open_windsx()

                if attempts == TOTAL_ATTEMPTS:
                    raise

        return app
