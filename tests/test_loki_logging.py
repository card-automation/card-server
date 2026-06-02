import logging
from unittest.mock import MagicMock, patch

import pytest

from card_automation_server.loki_logging import (
    APP_LABEL,
    MAIN_MODULE,
    _KindAndServiceFilter,
    configure_loki_logging,
)


@pytest.fixture(autouse=True)
def _clean_root_handlers():
    """Snapshot and restore root handlers so each test gets a clean slate."""
    root = logging.getLogger()
    saved = list(root.handlers)
    yield
    for h in list(root.handlers):
        if h not in saved:
            root.removeHandler(h)


def _make_record(name: str) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="msg",
        args=(),
        exc_info=None,
    )


class TestKindAndServiceFilter:
    def test_main_module_tagged_as_main(self):
        f = _KindAndServiceFilter()
        record = _make_record(MAIN_MODULE)
        f.filter(record)
        assert record.tags == {"service": MAIN_MODULE, "kind": "main"}

    def test_main_submodule_tagged_as_main(self):
        f = _KindAndServiceFilter()
        record = _make_record(f"{MAIN_MODULE}.workers.foo")
        f.filter(record)
        assert record.tags["kind"] == "main"
        assert record.tags["service"] == MAIN_MODULE

    def test_plugin_module_tagged_as_plugin(self):
        f = _KindAndServiceFilter()
        record = _make_record("some_plugin")
        f.filter(record)
        assert record.tags == {"service": "some_plugin", "kind": "plugin"}

    def test_plugin_submodule_collapsed_to_top_level(self):
        f = _KindAndServiceFilter()
        record = _make_record("some_plugin.handlers.thing")
        f.filter(record)
        assert record.tags == {"service": "some_plugin", "kind": "plugin"}

    def test_preexisting_tags_are_preserved(self):
        f = _KindAndServiceFilter()
        record = _make_record(MAIN_MODULE)
        record.tags = {"existing": "value"}
        f.filter(record)
        assert record.tags == {
            "existing": "value",
            "service": MAIN_MODULE,
            "kind": "main",
        }

    def test_empty_name_falls_back_to_root(self):
        f = _KindAndServiceFilter()
        record = _make_record("")
        f.filter(record)
        assert record.tags == {"service": "root", "kind": "plugin"}


class TestConfigureLokiLogging:
    def test_empty_url_is_noop(self):
        root = logging.getLogger()
        before = list(root.handlers)
        result = configure_loki_logging(url="", username="u", password="p")
        assert result is None
        assert root.handlers == before

    def test_none_url_is_noop(self):
        root = logging.getLogger()
        before = list(root.handlers)
        result = configure_loki_logging(url=None, username="u", password="p")
        assert result is None
        assert root.handlers == before

    @patch("card_automation_server.loki_logging.LokiQueueHandler")
    def test_handler_attached_with_basic_auth(self, mock_handler_cls):
        mock_handler = MagicMock(spec=logging.Handler)
        mock_handler_cls.return_value = mock_handler

        result = configure_loki_logging(
            url="https://loki.example/loki/api/v1/push",
            username="loki",
            password="secret",
            level=logging.WARNING,
        )

        assert result is mock_handler
        kwargs = mock_handler_cls.call_args.kwargs
        assert kwargs["url"] == "https://loki.example/loki/api/v1/push"
        assert kwargs["tags"] == {"app": APP_LABEL}
        assert kwargs["auth"] == ("loki", "secret")
        assert kwargs["version"] == "1"
        mock_handler.setLevel.assert_called_once_with(logging.WARNING)
        mock_handler.addFilter.assert_called_once()
        assert mock_handler in logging.getLogger().handlers

    @patch("card_automation_server.loki_logging.LokiQueueHandler")
    def test_no_auth_when_creds_missing(self, mock_handler_cls):
        mock_handler_cls.return_value = MagicMock(spec=logging.Handler)
        configure_loki_logging(
            url="https://loki.example/loki/api/v1/push",
            username=None,
            password=None,
        )
        kwargs = mock_handler_cls.call_args.kwargs
        assert kwargs["auth"] is None
