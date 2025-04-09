import enum
from pathlib import Path
from typing import Callable

import pytest

from card_automation_server.plugins.config import ConfigHolder, BaseConfig, ConfigProperty, ConfigPath, LogPath


class TestEnum(enum.Enum):
    APPLE = "apple"
    PEAR = enum.auto()


class InheritanceConfig(ConfigHolder):
    inherited_property: ConfigProperty[str]


class NestedConfig(InheritanceConfig, ConfigHolder):
    nested_int_property: ConfigProperty[int]
    default_int_property: ConfigProperty[int] = 3
    nested_list_property: ConfigProperty[list[int]]

    def _manual_config_setup(self) -> None:
        self.manual_config_was_run = True


class ConfigUnderTest(BaseConfig):
    def __init__(self, root: Path):
        self.manual_config_was_run = False

        super().__init__(
            ConfigPath(root / "config.toml"),
            LogPath(root / "test.log")
        )

    def _manual_config_setup(self) -> None:
        self.manual_config_was_run = True

    int_property: ConfigProperty[int]
    str_property: ConfigProperty[str]

    list_int_property: ConfigProperty[list[int]]
    list_str_property: ConfigProperty[list[str]]

    set_int_property: ConfigProperty[set[int]]
    set_str_property: ConfigProperty[set[str]]

    path_property: ConfigProperty[Path]

    default_int_property: ConfigProperty[int] = 5
    default_list_property: ConfigProperty[list[int]] = [1, 2, 3]

    enum_property: ConfigProperty[TestEnum]
    default_enum_property: ConfigProperty[TestEnum] = TestEnum.PEAR
    list_enum_property: ConfigProperty[list[TestEnum]]

    nested: NestedConfig

    # TODO
    # - Key Value stored property (research needed on the API)
    # - Optional type


ConfigFactory = Callable[[], ConfigUnderTest]


@pytest.fixture
def config_factory(tmp_path: Path) -> ConfigFactory:
    # Return a factory with the same path so that we can reload the config
    def inner():
        return ConfigUnderTest(tmp_path)

    return inner


class TestConfig:
    def test_reloading_config_works(self, config_factory: ConfigFactory):
        # This test is less about the class under test and more about the config factory and some assumptions it makes
        # about reloading the configuration.
        config = config_factory()
        config2 = config_factory()

        # They should not be the same object
        assert config is not config2
        # They should have the same configuration path
        assert config._config_path == config2._config_path

    def test_manual_setup_is_run(self, config_factory: ConfigFactory):
        config = config_factory()

        # This is only set to True in the manual config setup method
        assert config.manual_config_was_run

    def test_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.int_property is None

    def test_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.int_property = 3
        config.write()

        config = config_factory()
        assert config.int_property == 3

    def test_str_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.str_property is None

    def test_str_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.str_property = "Hello"
        config.write()

        config = config_factory()
        assert config.str_property == "Hello"

    def test_list_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.list_int_property is None

    def test_list_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.list_int_property = [7, 8, 9]
        config.write()

        config = config_factory()
        assert config.list_int_property == [7, 8, 9]

    def test_list_str_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.list_str_property is None

    def test_list_str_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.list_str_property = ["Hello, World"]
        config.write()

        config = config_factory()
        assert config.list_str_property == ["Hello, World"]

    def test_set_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.set_int_property is None

    def test_set_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.set_int_property = {1, 2, 3}
        config.write()

        config = config_factory()
        assert config.set_int_property == {1, 2, 3}

    def test_set_str_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.set_str_property is None

    def test_set_str_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.set_str_property = {"Hello", "World"}
        config.write()

        config = config_factory()
        assert config.set_str_property == {"Hello", "World"}

    def test_path_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.path_property is None

    def test_path_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.path_property = Path.home()
        config.write()

        config = config_factory()
        assert config.path_property == Path.home()

    def test_default_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.default_int_property == 5

    def test_default_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.default_int_property = 3
        config.write()

        config = config_factory()
        assert config.default_int_property == 3

    def test_default_list_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.default_list_property == [1, 2, 3]

    def test_default_list_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.default_list_property = [4, 5, 6]
        config.write()

        config = config_factory()
        assert config.default_list_property == [4, 5, 6]

    def test_enum_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.enum_property is None

    def test_enum_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.enum_property = TestEnum.APPLE
        config.write()

        config = config_factory()
        assert config.enum_property == TestEnum.APPLE

    def test_default_enum_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.default_enum_property == TestEnum.PEAR

    def test_default_enum_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.default_enum_property = TestEnum.APPLE
        config.write()

        config = config_factory()
        assert config.default_enum_property == TestEnum.APPLE

    def test_list_enum_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.list_enum_property is None

    def test_list_enum_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.list_enum_property = [TestEnum.APPLE, TestEnum.PEAR]
        config.write()

        config = config_factory()
        assert config.list_enum_property == [TestEnum.APPLE, TestEnum.PEAR]

    def test_nested_nested_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.nested.nested_int_property is None

    def test_nested_nested_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.nested.nested_int_property = 4
        config.write()

        config = config_factory()
        assert config.nested.nested_int_property == 4

    def test_nested_default_int_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.nested.default_int_property == 3

    def test_nested_default_int_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.nested.default_int_property = 6
        config.write()

        config = config_factory()
        assert config.nested.default_int_property == 6

    def test_nested_nested_list_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.nested.nested_list_property is None

    def test_nested_nested_list_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.nested.nested_list_property = [1, 2, 3]
        config.write()

        config = config_factory()
        assert config.nested.nested_list_property == [1, 2, 3]

    def test_nested_inherited_property_default(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.nested.inherited_property is None

    def test_nested_inherited_property_update(self, config_factory: ConfigFactory):
        config = config_factory()
        config.nested.inherited_property = "I'm adopted!"
        config.write()

        config = config_factory()
        assert config.nested.inherited_property == "I'm adopted!"

    def test_nested_manual_setup_is_run(self, config_factory: ConfigFactory):
        config = config_factory()
        assert config.nested.manual_config_was_run
