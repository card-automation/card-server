import abc
import importlib
import inspect
import pkgutil
from abc import ABC
from pathlib import Path
from typing import Optional

from card_automation_server.ioc import Resolver
from card_automation_server.plugins.error_handling import ErrorHandler
from card_automation_server.plugins.interfaces import Plugin


class PluginSetup(abc.ABC):
    @abc.abstractmethod
    def plugins(self) -> list[Plugin]:
        pass


class HasErrorHandler(abc.ABC):
    @abc.abstractmethod
    def error_handler(self) -> ErrorHandler:
        pass


# TODO Unit test this
class AutoDiscoverPlugins(PluginSetup):
    def __init__(self, resolver: Resolver):
        self._resolver = resolver

        module_name = self.__module__
        plugin_suffix = '.plugin'
        if not module_name.endswith(plugin_suffix):
            raise Exception(f"Could not automatically load plugins from module {module_name}")

        module_name = module_name[:-len(plugin_suffix)]
        root_module = importlib.import_module(module_name)
        init_file = Path(root_module.__file__)

        self._plugin_classes = []
        for m in pkgutil.iter_modules([str(init_file.parent)]):
            if m.name == 'plugin':  # Ignore the setup file
                continue

            module = importlib.import_module(f"{module_name}.{m.name}")

            for name in dir(module):
                if name[0] == '_':
                    continue

                item = getattr(module, name)
                mro = inspect.getmro(item)
                if Plugin not in mro:
                    continue  # Not a plugin at all

                if inspect.isabstract(item):
                    continue  # Abstract, we can't make it (it might be our interfaces being imported)

                self._plugin_classes.append(item)

    def plugins(self) -> list[Plugin]:
        result = []

        for cls in self._plugin_classes:
            result.append(self._resolver.singleton(cls))

        return result
