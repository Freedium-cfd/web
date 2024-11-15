from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict
from pytest import MonkeyPatch

from freedium_library.utils.meta.pydantic import BaseConfig, BaseSettingsConfigDict


class SampleConfig(BaseConfig):
    model_config = BaseSettingsConfigDict()

    test_value: str
    another_value: int = 42


class SampleConfigPrefix(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="SAMPLE_")

    test_value: str
    another_value: int = 42


class NestedConfig(BaseConfig):
    model_config = BaseSettingsConfigDict()

    nested: SampleConfig
    list_value: list[int] = [1, 2, 3]


def test_base_settings_config_dict() -> None:
    config: SettingsConfigDict = BaseSettingsConfigDict()
    assert config["env_file"] == ".env"
    assert config["extra"] == "ignore"
    assert config["case_sensitive"] is False


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    env_content: str = """TEST_VALUE=hello
ANOTHER_VALUE=123
EXTRA_FIELD=ignored"""
    env_file: Path = tmp_path / ".env"
    env_file.write_text(env_content)
    return env_file


def test_base_config_env_file(env_file: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(env_file.parent)
    config: SampleConfig = SampleConfig()
    assert config.test_value == "hello"
    assert config.another_value == 123


def test_base_config_env_vars(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_VALUE", "from_env")
    monkeypatch.setenv("ANOTHER_VALUE", "456")
    config: SampleConfig = SampleConfig()
    assert config.test_value == "from_env"
    assert config.another_value == 456


def test_base_config_case_insensitive(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("test_value", "lower_case")
    config: SampleConfig = SampleConfig()
    assert config.test_value == "lower_case"


def test_base_config_missing_required() -> None:
    with pytest.raises(ValueError):
        SampleConfig()


def test_base_config_ignore_extra(env_file: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.chdir(env_file.parent)
    config: SampleConfig = SampleConfig()
    assert not hasattr(config, "extra_field")


def test_base_config_default_value(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_VALUE", "test")
    config = SampleConfig()
    assert config.another_value == 42


def test_base_config_type_conversion(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_VALUE", "test")
    monkeypatch.setenv("ANOTHER_VALUE", "123")
    config = SampleConfig()
    assert isinstance(config.another_value, int)
    assert config.another_value == 123


@pytest.fixture
def multiple_env_files(tmp_path: Path) -> tuple[Path, Path]:
    base_env = tmp_path / ".env"
    base_env.write_text("TEST_VALUE=base\nANOTHER_VALUE=100")

    override_env = tmp_path / ".env.override"
    override_env.write_text("TEST_VALUE=override")
    return base_env, override_env


def test_base_config_multiple_env_files(
    multiple_env_files: tuple[Path, Path], monkeypatch: MonkeyPatch
) -> None:
    base_env, override_env = multiple_env_files
    monkeypatch.chdir(base_env.parent)
    monkeypatch.setenv("ENV_FILE", ".env,.env.override")
    config = SampleConfig()
    assert config.test_value == "base"
    assert config.another_value == 100


def test_nested_config(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("NESTED", '{"test_value": "inner", "another_value": 789}')
    monkeypatch.setenv("LIST_VALUE", "[4,5,6]")
    config = NestedConfig()
    assert config.nested.test_value == "inner"
    assert config.nested.another_value == 789
    assert config.list_value == [4, 5, 6]


def test_nested_config_env(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("NESTED__TEST_VALUE", "inner")
    monkeypatch.setenv("NESTED__ANOTHER_VALUE", "789")
    monkeypatch.setenv("LIST_VALUE", "[4,5,6]")
    config = NestedConfig()
    assert config.nested.test_value == "inner"
    assert config.nested.another_value == 789
    assert config.list_value == [4, 5, 6]


def test_prefixed_config_env_vars(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("SAMPLE_TEST_VALUE", "prefixed")
    monkeypatch.setenv("SAMPLE_ANOTHER_VALUE", "789")
    config = SampleConfigPrefix()
    assert config.test_value == "prefixed"
    assert config.another_value == 789


def test_prefixed_config_env_file(env_file: Path, monkeypatch: MonkeyPatch) -> None:
    env_content = """SAMPLE_TEST_VALUE=from_file
SAMPLE_ANOTHER_VALUE=321"""
    env_file.write_text(env_content)
    monkeypatch.chdir(env_file.parent)
    config = SampleConfigPrefix()
    assert config.test_value == "from_file"
    assert config.another_value == 321
