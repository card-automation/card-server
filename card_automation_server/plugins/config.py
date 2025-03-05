import abc
import enum
import inspect
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import NewType, TypeVar, Generic, Optional, Union

import tomlkit
import tomlkit.items

ConfigPath = NewType('ConfigPath', Path)
LogPath = NewType('LogPath', Path)

T = TypeVar('T')
TomlConfigType = Union[tomlkit.TOMLDocument, tomlkit.items.Table]


class ConfigProperty(Generic[T]):
    def __init__(self, name: str, type_: type[T]):
        self._name = name
        self._type = type_

    def __get__(self, instance, owner) -> Optional[T]:
        # noinspection PyProtectedMember
        config = instance._config

        if self._name not in config:
            return None
        raw_value = config[self._name]

        if self._type == Path:
            return Path(raw_value)
        if isinstance(self._type, enum.EnumType):
            return self._type(raw_value)

        return raw_value

    def __set__(self, instance, value: Optional[T]):
        is_valid_type = True
        if hasattr(self._type, '__origin__') and hasattr(self._type, '__args__'):
            if not isinstance(value, self._type.__origin__):
                is_valid_type = False
            else:
                arg = self._type.__args__[0]
                if not all(isinstance(x, arg) for x in value):
                    is_valid_type = False
        elif not isinstance(value, self._type):
            is_valid_type = False

        if not is_valid_type:
            raise Exception(f"Trying to assign to {self._name} an invalid type of {type(value)}. Expected {self._type}")

        # noinspection PyProtectedMember
        config = instance._config

        if value is None and self._name in config:
            del config[self._name]
            return

        if self._type == Path:
            value = str(value)

        config[self._name] = value


class ConfigHolder(abc.ABC):
    def __init__(self, config: TomlConfigType):
        self._config = config

        self._manual_config_setup()

        annotations = self._get_all_annotations()
        for attr_name, attr_type in annotations.items():
            if attr_name.startswith('_'):
                continue

            if hasattr(self, attr_name):
                continue  # It's already been defined, so we ignore it.

            if inspect.isclass(attr_type):
                mro = inspect.getmro(attr_type)

                if ConfigHolder in mro:
                    if attr_name not in self._config:
                        self._config[attr_name] = tomlkit.table()

                    setattr(self, attr_name, attr_type(self._config[attr_name]))
                else:
                    continue  # It was a class, but not a config holder. Not ours to mess with.
            elif hasattr(attr_type, '__origin__') and attr_type.__origin__ == ConfigProperty:
                args = attr_type.__args__
                if len(args) != 1:
                    raise Exception("Config property must have exactly one argument type")

                setattr(self.__class__, attr_name, ConfigProperty(attr_name, args[0]))

    def __repr__(self):
        return repr(self._config)

    def _get_all_annotations(self) -> dict:
        result = {}

        for cls in inspect.getmro(self.__class__):
            annotations = cls.__annotations__ if hasattr(cls, '__annotations__') else {}
            for name, value in annotations.items():
                if name in result:
                    continue

                result[name] = value

        return result

    def _manual_config_setup(self) -> None:
        """
        This method is useful for when you need the config object to define a config property/holder after the
        configuration is available but before the properties get automatically generated.
        """
        pass


class BaseConfig(ConfigHolder, abc.ABC):
    def __init__(self, config_path: ConfigPath, log_path: LogPath):
        self._config_path: Path = config_path

        module_name = self.__module__
        if '.' in module_name:
            module_name = module_name[:module_name.index('.')]
        self._logger = logging.getLogger(module_name)
        self._logger.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console logging handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # File logging handler
        max_bytes = 1 * 1024 * 1024
        file_handler = RotatingFileHandler(log_path,
                                           maxBytes=max_bytes,
                                           backupCount=10)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        config: tomlkit.TOMLDocument
        if self._config_path.exists():
            with self._config_path.open('r') as fh:
                config = tomlkit.load(fh)
        else:
            config = tomlkit.document()

        super().__init__(config)

        if not self._config_path.exists():
            self.write()

    def write(self):
        with self._config_path.open('w') as fh:
            tomlkit.dump(self._config, fh)

    @property
    def logger(self) -> Logger:
        return self._logger
