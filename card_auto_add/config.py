import abc
import inspect
from pathlib import Path
from typing import TypeVar, Generic, Union, Optional, Callable

import tomlkit
from platformdirs import PlatformDirs
from tomlkit import TOMLDocument
from tomlkit.items import Table

T = TypeVar('T')


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

        return raw_value

    def __set__(self, instance, value: Optional[T]):
        if not isinstance(value, self._type):
            raise Exception(f"Trying to assign to {self._name} an invalid type of {type(value)}. Expected {self._type}")

        # noinspection PyProtectedMember
        config = instance._config

        if value is None and self._name in config:
            del config[self._name]
            return

        if self._type == Path:
            value = str(value)

        config[self._name] = value


class _ConfigHolder(abc.ABC):
    def __init__(self, config: Union[TOMLDocument, Table]):
        self._config = config

        for attr_name, attr_type in self.__annotations__.items():
            if attr_name.startswith('_'):
                continue

            if inspect.isclass(attr_type):
                mro = inspect.getmro(attr_type)

                if _ConfigHolder in mro:
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


class _WinDSXConfig(_ConfigHolder):
    root: ConfigProperty[Path]
    acs_data_db_path: ConfigProperty[Path]
    log_db_path: ConfigProperty[Path]
    location_group: ConfigProperty[int]


class _SentryConfig(_ConfigHolder):
    dsn: ConfigProperty[str]


class _DSXPiConfig(_ConfigHolder):
    host: ConfigProperty[str]
    secret: ConfigProperty[str]


class _GitHubConfig(_ConfigHolder):
    api_key: ConfigProperty[str]


class Config(_ConfigHolder):
    def __init__(self, dirs: PlatformDirs):
        self._platformdirs = dirs
        self._config_path = self._platformdirs.site_config_path / "config.toml"

        config: TOMLDocument
        if self._config_path.exists():
            with self._config_path.open('r') as fh:
                config = tomlkit.load(fh)
        else:
            config = tomlkit.document()

        super().__init__(config)

    def write(self):
        self._platformdirs.site_config_path.mkdir(parents=True, exist_ok=True)
        with self._config_path.open('w') as fh:
            tomlkit.dump(self._config, fh)

    windsx: _WinDSXConfig
    sentry: _SentryConfig
    dsxpi: _DSXPiConfig
    github: _GitHubConfig
