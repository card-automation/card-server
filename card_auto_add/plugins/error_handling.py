import abc

from sentry_sdk import Client, Scope
from sentry_sdk.integrations import Integration
from sentry_sdk.scope import ScopeType


class ErrorHandler(abc.ABC):
    @abc.abstractmethod
    def capture_exception(self, exception):
        pass


class _SentryFakeExceptHook(Integration):
    identifier = "excepthook"

    @staticmethod
    def setup_once():
        pass


class _SentryFakeAtExit(Integration):
    identifier = "atexit"

    @staticmethod
    def setup_once():
        pass


class SentryErrorHandler(ErrorHandler):
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._client = Client(dsn, integrations=[
            _SentryFakeExceptHook(),
            _SentryFakeAtExit(),
        ])
        self._scope = Scope(ty=ScopeType.CURRENT, client=self._client)

    def capture_exception(self, exception):
        self._scope.capture_exception(exception)

    def __del__(self):
        self._scope.end_session()
        self._client.close()
