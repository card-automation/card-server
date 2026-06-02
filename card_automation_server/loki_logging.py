import logging
from queue import Queue
from typing import Optional

from logging_loki import LokiQueueHandler


APP_LABEL = "card-server"
MAIN_MODULE = "card_automation_server"


class _KindAndServiceFilter(logging.Filter):
    """Tags each record with `service` (top-level module) and `kind` (main vs plugin).

    `record.name` is set by `logging.getLogger(...)` to the module name the
    caller chose. `BaseConfig` always uses the top-level module, but child
    loggers (`getLogger(__name__)`) can be deeper — so we collapse to the
    first dotted segment to keep label cardinality low.

    The Loki handler reads `record.tags` and merges it with the static
    `tags` dict passed at construction.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        top_module = record.name.split(".", 1)[0] or "root"
        kind = "main" if top_module == MAIN_MODULE else "plugin"
        existing = getattr(record, "tags", None) or {}
        record.tags = {**existing, "service": top_module, "kind": kind}
        return True


def configure_loki_logging(
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    level: int = logging.INFO,
) -> Optional[LokiQueueHandler]:
    """Attach a Loki handler to the root logger.

    Returns None and is a no-op if `url` is empty — that lets the call site
    stay unconditional while letting deployments without Loki keep working.

    All named loggers propagate to root, so installing the handler here
    captures both the main process and any plugin loggers without each
    plugin needing to know about Loki. The static `app` label lets the
    user query every card-server log with `{app="card-server"}`; the
    dynamic `kind` and `service` labels (set by `_KindAndServiceFilter`)
    let them narrow to main, plugins, or a specific plugin.
    """
    if not url:
        return None

    auth = (username, password) if username and password else None

    handler = LokiQueueHandler(
        Queue(-1),
        url=url,
        tags={"app": APP_LABEL},
        auth=auth,
        version="1",
    )
    handler.setLevel(level)
    handler.addFilter(_KindAndServiceFilter())

    logging.getLogger().addHandler(handler)
    return handler
