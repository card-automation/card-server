import abc
import sys
from pathlib import Path
from typing import Optional, Tuple

import tomlkit
from platformdirs import PlatformDirs

from card_automation_server.plugins.config import ConfigHolder, ConfigProperty, BaseConfig, ConfigPath, TomlConfigType, \
    LogPath


class _HasCommitVersions(ConfigHolder):
    commit: ConfigProperty[str]

    @property
    @abc.abstractmethod
    def root_path(self) -> Path:
        pass

    @property
    def current_path(self) -> Optional[Path]:
        path = self.root_path / "current"

        # This allows us to break the symlink but still use the path
        if not path.exists(follow_symlinks=False) and self.versioned_path.exists():
            path.symlink_to(self.versioned_path, target_is_directory=True)

        return path

    @property
    def versioned_path(self) -> Path:
        return self.root_path / "versions" / self.commit


class _DeployConfig(_HasCommitVersions, ConfigHolder):
    @property
    def root_path(self) -> Path:
        return self.root

    root: ConfigProperty[Path]
    environment: ConfigProperty[str]


class _WinDSXConfig(ConfigHolder):
    root: ConfigProperty[Path]
    acs_data_db_path: ConfigProperty[Path]
    log_db_path: ConfigProperty[Path]

    location_group: ConfigProperty[int]

    cs_host: ConfigProperty[str]
    cs_port: ConfigProperty[int]
    workstation_number: ConfigProperty[int]

    common_doors: ConfigProperty[list[int]]


class _SentryConfig(ConfigHolder):
    dsn: ConfigProperty[str]


class _DSXPiConfig(ConfigHolder):
    host: ConfigProperty[str]
    secret: ConfigProperty[str]


class _GitHubConfig(ConfigHolder):
    private_key_path: ConfigProperty[Path]
    app_id: ConfigProperty[int]
    self_installation_id: ConfigProperty[int]


class _PluginConfig(_HasCommitVersions, ConfigHolder):
    def __init__(self,
                 config: TomlConfigType,
                 plugin_root: Path):
        super().__init__(config)
        self._plugin_path: Path = plugin_root

    @property
    def root_path(self) -> Path:
        return self._plugin_path

    @property
    def config_path(self) -> Path:
        return self._plugin_path / "config.toml"

    @property
    def log_path(self) -> Path:
        return self._plugin_path / "plugin.log"

    doors: ConfigProperty[list[int]]


class _PluginsConfig(ConfigHolder):
    def __init__(self,
                 config: TomlConfigType,
                 dirs: PlatformDirs):
        super().__init__(config)
        self._data_root = dirs.user_data_path
        self._data_root.mkdir(parents=True, exist_ok=True)

        self._plugins: dict[str, _PluginConfig] = {
            key: _PluginConfig(value, self._data_root / "plugins" / key)
            for (key, value) in config.items()
        }

    def keys(self):
        return self._plugins.keys()

    def values(self):
        return self._plugins.values()

    def items(self):
        return self._plugins.items()

    def __len__(self):
        return len(self._plugins)

    def __getitem__(self, item: Tuple[str, str]) -> _PluginConfig:
        owner, repo = item
        key = f"{owner}/{repo}"
        if key not in self._plugins:
            table = tomlkit.table()
            self._config[key] = table
            plugin_root = self._data_root / "plugins" / owner / repo
            plugin_root.mkdir(parents=True, exist_ok=True)
            self._plugins[key] = _PluginConfig(table, plugin_root)

        return self._plugins[key]

    def __contains__(self, item: Tuple[str, str]) -> bool:
        owner, repo = item
        key = f"{owner}/{repo}"
        return key in self._plugins

    def __repr__(self):
        return self._plugins.__repr__()


class Config(BaseConfig):
    def __init__(self, dirs: PlatformDirs):
        self._platformdirs = dirs

        config_root = dirs.user_config_path
        config_root.mkdir(parents=True, exist_ok=True)
        config_path = config_root / "config.toml"

        log_path: Path = config_root / "card-server.log"

        super().__init__(ConfigPath(config_path), LogPath(log_path))

    def _manual_config_setup(self):
        if "plugins" not in self._config:
            self._config["plugins"] = tomlkit.table()
        self.plugins = _PluginsConfig(self._config["plugins"], self._platformdirs)

    deploy: _DeployConfig
    windsx: _WinDSXConfig
    sentry: _SentryConfig
    dsxpi: _DSXPiConfig
    github: _GitHubConfig
    plugins: _PluginsConfig
