from __future__ import annotations

from typing import Optional

from pydantic import Field

from freedium_library.utils.meta import BaseConfig, BaseSettingsConfigDict


class MediumConfig(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="MEDIUM_")

    cookies: Optional[str] = Field(default=None)
