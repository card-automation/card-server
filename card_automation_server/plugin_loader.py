import importlib
import inspect
import sys
from pathlib import Path
from typing import Optional

from card_automation_server.config import Config
from card_automation_server.ioc import Resolver
from card_automation_server.plugins.config import ConfigPath, LogPath
from card_automation_server.plugins.error_handling import ErrorHandler
from card_automation_server.plugins.interfaces import Plugin
from card_automation_server.plugins.setup import PluginSetup, HasErrorHandler
from card_automation_server.windsx.engines import AcsEngine, LogEngine
from card_automation_server.windsx.lookup.access_card import AccessCardLookup
from card_automation_server.windsx.lookup.acl_group_combo import AclGroupComboLookup
from card_automation_server.windsx.lookup.door_lookup import DoorLookup
from card_automation_server.windsx.lookup.person import PersonLookup
from card_automation_server.windsx.lookup.utils import LookupInfo
from card_automation_server.workers.plugin_worker import PluginWorker
from card_automation_server.workers.worker_event_loop import WorkerEventLoop


class PluginLoader:
    def __init__(self,
                 owner: str,
                 repo: str,
                 config: Config,
                 resolver: Resolver,
                 worker_event_loop: WorkerEventLoop
                 ):
        self._owner = owner
        self._repo = repo
        self._config = config
        self._worker_event_loop = worker_event_loop

        self._sub_resolver = resolver.clone(
            AcsEngine,
            LogEngine,
            LookupInfo,
            AccessCardLookup,
            AclGroupComboLookup,
            PersonLookup,
        )

        self._plugin_config = config.plugins[self._owner, self._repo]
        self._sub_resolver.singleton(ConfigPath, self._plugin_config.config_path)
        self._sub_resolver.singleton(LogPath, self._plugin_config.log_path)

        doors = self._config.windsx.common_doors if self._config.windsx.common_doors is not None else []
        doors.extend(self._plugin_config.doors if self._plugin_config.doors is not None else [])
        door_lookup = DoorLookup(resolver(LookupInfo), *doors)
        self._sub_resolver.singleton(door_lookup)

        self._error_handler: Optional[ErrorHandler] = None

        # First, we need to find this plugin and add it to sys.paths
        print(self._owner, self._repo, self._plugin_config.config_path)

        plugin_path = self._plugin_config.versioned_path
        sys.path.append(str(plugin_path))

        # Let's go find plugin modules
        modules = []
        f: Path
        for f in plugin_path.glob("**/__init__.py"):
            module_name = f.relative_to(plugin_path).parent.name

            plugin_file = plugin_path / module_name / "plugin.py"
            if not plugin_file.exists():
                continue  # This is a module, but not one we care about

            modules.append(module_name)

        print("Found plugin modules: ", modules)

        for module_name in modules:
            import_name = f"{module_name}.plugin"

            module = importlib.import_module(import_name)

            for attr_name in dir(module):
                if attr_name.startswith('_'):
                    continue

                attr = getattr(module, attr_name)
                if not hasattr(attr, '__module__'):
                    continue

                if not attr.__module__.startswith(f"{module_name}."):
                    continue

                if not inspect.isclass(attr):
                    continue

                if not hasattr(attr, '__mro__'):
                    continue

                if PluginSetup not in attr.__mro__:
                    continue

                # attr is the class that is our plugin setup.

                instance: PluginSetup = self._sub_resolver(attr)
                print(attr_name, instance)

                if ErrorHandler in attr.__mro__:
                    instance: HasErrorHandler
                    self._error_handler = instance.error_handler()

                plugins_method = self._wrap_errors(instance.plugins)

                for plugin in plugins_method():
                    if not hasattr(plugin.__class__, '__mro__'):
                        continue  # Shouldn't happen, but if it does, we didn't get a plugin back

                    for parent in plugin.__class__.__mro__:
                        if not parent.__module__.startswith('card_automation_server.plugins.interfaces'):
                            continue

                        if Plugin == parent:
                            continue

                        methods_to_wrap = [x for x in dir(parent) if not x.startswith('_')]
                        for method in methods_to_wrap:
                            setattr(plugin, method, self._wrap_errors(getattr(plugin, method)))

                    print(f"Found plugin file {plugin.__class__}")

                    worker_event_loop.add(
                        PluginWorker(plugin)
                    )

    def _wrap_errors(self, func):
        def _inner(*args, **kwargs):
            # noinspection PyBroadException
            try:
                return func(*args, **kwargs)
            except BaseException as ex:
                if self._error_handler is not None:
                    self._error_handler.capture_exception(ex)

        return _inner
