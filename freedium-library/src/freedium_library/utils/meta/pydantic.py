from functools import partial
from typing import cast

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings): ...


BaseSettingsConfigDict: SettingsConfigDict = cast(
    SettingsConfigDict,
    partial(
        SettingsConfigDict,
        env_file=".env",
        extra="ignore",
        env_nested_delimiter="__",
        case_sensitive=False,
    ),
)
