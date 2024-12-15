# freedium-library/src/freedium_library/api/config.py
from typing import Optional

from pydantic import Field

from freedium_library.utils.meta.pydantic import BaseConfig, BaseSettingsConfigDict


class ServerConfig(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="SERVER_")

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=7080)
    reload: bool = Field(default=False)
    workers: Optional[int] = Field(default=None)


class APIConfig(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="API_")

    DISABLED_DOCS: bool = Field(default=False)
    PREFIX_PATH: str = Field(default="/api")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=7080)
    MAX_WORKERS: int = Field(default=10)
