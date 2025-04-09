import abc
import enum
import inspect
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import NewType, TypeVar, Generic, Optional, Union, Tuple

import tomlkit
import tomlkit.items

ConfigPath = NewType('ConfigPath', Path)
LogPath = NewType('LogPath', Path)

T = TypeVar('T')
TomlConfigType = Union[tomlkit.TOMLDocument, tomlkit.items.Table]


class ConfigProperty(Generic[T]):
    def __init__(self, name: str,
                 type_: type[T],
                 default_value: Optional[T] = None):
        self._name = name
        self._type = type_
        self._default_value = default_value

    @staticmethod
    def _base_and_arg_type(t) -> Tuple[type, Optional[type]]:
        if hasattr(t, '__origin__') and hasattr(t, '__args__'):
            return t.__origin__, t.__args__[0]

        return t, None

    @classmethod
    def _from_serializable_type(cls, value, base_type, arg_type):
        if base_type == Path:
            return Path(value)

        if isinstance(base_type, enum.EnumType):
            return base_type(value)

        if base_type == list:
            if arg_type is None:
                raise Exception(f"Cannot resolve argument type of {base_type} and it is required here")

            new_base_type, new_arg_type = cls._base_and_arg_type(arg_type)
            return [cls._from_serializable_type(x, new_base_type, new_arg_type) for x in value]


        if base_type == set:
            return set(value)

        return value

    def __get__(self, instance, owner) -> Optional[T]:
        # noinspection PyProtectedMember
        config = instance._config

        if self._name not in config:
            return self._default_value
        value = config[self._name]

        base_type, arg_type = self._base_and_arg_type(self._type)

        return self._from_serializable_type(value, base_type, arg_type)

    @classmethod
    def _to_serializable_type(cls, value: Optional[T], base_type, arg_type):
        if base_type == Path:
            return str(value)

        if isinstance(base_type, enum.EnumType):
            return value.value

        if base_type == set:
            value = list(value)

        if type(value) == list:
            if arg_type is None:
                raise Exception(f"Cannot resolve argument type of {base_type} and it is required here")

            new_base_type, new_arg_type = cls._base_and_arg_type(arg_type)
            return [cls._to_serializable_type(x, new_base_type, new_arg_type) for x in value]

        return value

    def __set__(self, instance, value: Optional[T]):
        is_valid_type = True
        base_type, arg_type = self._base_and_arg_type(self._type)
        if self._type != base_type:
            if not isinstance(value, base_type):
                is_valid_type = False
            else:
                if not all(isinstance(x, arg_type) for x in value):
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

        config[self._name] = self._to_serializable_type(value, base_type, arg_type)


class ConfigHolder(abc.ABC):
    def __init__(self, config: TomlConfigType):
        self._config = config

        self._manual_config_setup()

        annotations = self._get_all_annotations()
        for attr_name, attr_type in annotations.items():
            if attr_name.startswith('_'):
                continue

            is_config_property = hasattr(attr_type, '__origin__') and attr_type.__origin__ == ConfigProperty
            is_config_holder = inspect.isclass(attr_type) and ConfigHolder in inspect.getmro(attr_type)

            if is_config_holder:
                if hasattr(self, attr_name):
                    continue  # ConfigHolder's that are already defined get ignored

                if attr_name not in self._config:
                    self._config[attr_name] = tomlkit.table()

                setattr(self, attr_name, attr_type(self._config[attr_name]))
            elif is_config_property and hasattr(attr_type, '__args__'):
                # If it has __origin__, it has __args__. The hasattr check is to get the linter to be quiet.
                args = attr_type.__args__
                if len(args) != 1:
                    raise Exception("Config property must have exactly one argument type")

                default_value = None
                if hasattr(self, attr_name):
                    default_value = getattr(self, attr_name)

                # First set the descriptor instance
                config_property = ConfigProperty(attr_name, args[0], default_value)
                setattr(self.__class__, attr_name, config_property)
                # Then set the value of that descriptor
                if default_value is not None:
                    setattr(self, attr_name, default_value)

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
        self._logger.setLevel(logging.DEBUG)

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
        file_handler.setLevel(logging.DEBUG)
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

    @property
    def config_path(self) -> Path:
        return self._config_path

    def write(self):
        with self._config_path.open('w') as fh:
            tomlkit.dump(self._config, fh)

    @property
    def logger(self) -> Logger:
        return self._logger
