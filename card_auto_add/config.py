import configparser
from logging import Logger
from typing import Optional, Callable, TypeVar, Generic

from platformdirs import PlatformDirs

T = TypeVar('T')


class ConfigProperty(Generic[T]):
    def __init__(self, section, key, transform: Optional[Callable[[str], T]] = None):
        self._section = section
        self._key = key
        if transform is None:
            def transform(x):
                return x
        self._transform = transform

    def __get__(self, instance, owner) -> T:
        return self._transform(instance[self._section][self._key])


class Config(object):
    def __init__(self,
                 dirs: PlatformDirs,
                 logger: Logger
                 ):
        self._platformdirs = dirs
        self.logger: Logger = logger
        config_path = self._platformdirs.site_config_path / "config.toml"  # TODO Make our reader/writer actually be toml
        parser = configparser.ConfigParser()
        parser.read(config_path)
        self._config = parser

    def __getitem__(self, item):
        return self._config[item]

    acs_data_db_path = ConfigProperty('WINDSX', 'acs_data_db_path')
    log_db_path = ConfigProperty('WINDSX', 'log_db_path')
    windsx_path = ConfigProperty('WINDSX', 'root_path')

    sentry_dsn = ConfigProperty('SENTRY', 'dsn')

    dsxpi_host = ConfigProperty('DSXPI', 'host')
    dsxpi_signing_secret = ConfigProperty('DSXPI', 'signing_secret')
