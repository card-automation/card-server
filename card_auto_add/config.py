import sys
from pathlib import Path
from typing import Union, Optional, Tuple

import tomlkit
from platformdirs import PlatformDirs
from tomlkit import TOMLDocument
from tomlkit.items import Table

from card_auto_add.plugins.config import ConfigHolder, ConfigProperty, BaseConfig, ConfigPath


class _WinDSXConfig(ConfigHolder):
    root: ConfigProperty[Path]
    acs_data_db_path: ConfigProperty[Path]
    log_db_path: ConfigProperty[Path]

    location_group: ConfigProperty[int]

    cs_host: ConfigProperty[str]
    cs_port: ConfigProperty[int]
    workstation_number: ConfigProperty[int]


class _SentryConfig(ConfigHolder):
    dsn: ConfigProperty[str]


class _DSXPiConfig(ConfigHolder):
    host: ConfigProperty[str]
    secret: ConfigProperty[str]


class _GitHubConfig(ConfigHolder):
    api_key: ConfigProperty[str]
    private_key_path: ConfigProperty[Path]
    app_id: ConfigProperty[int]


class _PluginConfig(ConfigHolder):
    def __init__(self,
                 config: Union[TOMLDocument, Table],
                 plugin_root: Path):
        super().__init__(config)
        self._plugin_root: Path = plugin_root

    name: ConfigProperty[str]
    github_org: ConfigProperty[str]
    github_repo: ConfigProperty[str]
    commit: ConfigProperty[str]

    @property
    def current_path(self) -> Optional[Path]:
        path = self._plugin_root / "current"

        # This allows us to break the symlink but still use the path
        if not path.exists(follow_symlinks=False) and self.versioned_path.exists():
            path.symlink_to(self.versioned_path, target_is_directory=True)

        return path

    @property
    def versioned_path(self) -> Path:
        return self._plugin_root / "versions" / self.commit

    @property
    def config_path(self) -> Path:
        return self._plugin_root / "config.toml"


class _PluginsConfig(ConfigHolder):
    def __init__(self,
                 config: Union[TOMLDocument, Table],
                 dirs: PlatformDirs):
        super().__init__(config)
        self._plugins: dict[Tuple[str, str], _PluginConfig] = {}

        self._data_root = dirs.user_data_path if sys.platform == "darwin" else dirs.site_data_path
        self._data_root.mkdir(parents=True, exist_ok=True)

    def keys(self):
        return self._plugins.keys()

    def values(self):
        return self._plugins.values()

    def items(self):
        return self._plugins.items()

    def __len__(self):
        return len(self._plugins)

    def __getitem__(self, owner: str, repo: str) -> _PluginConfig:
        item = (owner, repo)
        if item not in self._plugins:
            table = tomlkit.table()
            self._config[item] = table
            plugin_root = self._data_root / owner / repo
            plugin_root.mkdir(parents=True, exist_ok=True)
            self._plugins[item] = _PluginConfig(table, plugin_root)

        return self._plugins[item]

    def __contains__(self, item: Tuple[str, str]) -> bool:
        return item in self._plugins

    def __repr__(self):
        return self._plugins.__repr__()


class Config(BaseConfig):
    def __init__(self, dirs: PlatformDirs):
        self._platformdirs = dirs

        # Mac hates using the system path, so we just use the user path for testing.
        config_root = dirs.user_config_path if sys.platform == "darwin" else dirs.site_config_path
        config_root.mkdir(parents=True, exist_ok=True)
        config_path = config_root / "config.toml"

        super().__init__(ConfigPath(config_path))

    def _manual_config_setup(self):
        self.plugins = _PluginsConfig(self._config, self._platformdirs)

    def write(self):
        with self._config_path.open('w') as fh:
            tomlkit.dump(self._config, fh)

    windsx: _WinDSXConfig
    sentry: _SentryConfig
    dsxpi: _DSXPiConfig
    github: _GitHubConfig
    plugins: _PluginsConfig
