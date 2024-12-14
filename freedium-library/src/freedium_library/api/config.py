from pydantic import Field

from freedium_library.utils.meta.pydantic import BaseConfig, BaseSettingsConfigDict


class APIConfig(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="API_")

    DISABLED_DOCS: bool = Field(default=False)
    PREFIX_PATH: str = Field(default="/api")
