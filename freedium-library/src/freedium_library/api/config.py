from freedium_library.utils.meta.pydantic import BaseConfig, BaseSettingsConfigDict


class APIConfig(BaseConfig):
    model_config = BaseSettingsConfigDict(env_prefix="API_")

    DISABLE_DOCS: bool = True
    PREFIX_PATH: str = "/api"
