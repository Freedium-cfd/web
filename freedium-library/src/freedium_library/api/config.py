from typing import Literal, Optional

from pydantic import AliasChoices, Field

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
    PDF_INTERNAL_SECRET: str = Field(
        default="dev-pdf-secret-change-in-prod",
        description="Shared secret required on POST /internal/pdf via X-Internal-Secret header.",
    )


class ImageProxyConfig(BaseConfig):
    """Operational settings for the /img/{width}/{id} image proxy.

    Security boundaries (allowlisted widths, content-type safelist, image-id
    regex) are hardcoded in images.py — they should never be relaxed via env.
    """

    model_config = BaseSettingsConfigDict(env_prefix="IMAGE_")

    SERVE_MODE: Literal["cache", "redirect"] = Field(
        default="cache",
        description="'cache' = Mongo-backed proxy; 'redirect' = 307 to CDN.",
    )
    CDN_BASE: str = Field(
        default="https://miro.medium.com/v2/resize:fit",
        description="Base URL for redirect mode (width/id appended as /{w}/{id}).",
    )
    MAX_BYTES: int = Field(
        default=15 * 1024 * 1024,
        description="Hard byte cap for upstream fetches on cache miss.",
    )
    UA: str = Field(
        default="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/146 Safari/537.36",
        description="User-Agent for upstream CDN fetches on cache miss.",
    )


class RenderConfig(BaseConfig):
    """Article-render concurrency cap. Bounds simultaneous (CPU-heavy) renders
    per process so a burst of uncached-article traffic can't saturate the box."""

    model_config = BaseSettingsConfigDict(env_prefix="RENDER_")

    CONCURRENCY: int = Field(
        default=3,
        description="Max concurrent renders per process (uvicorn worker / TaskIQ worker).",
    )


class MediumConfig(BaseConfig):
    """Medium service toggle (on by default — it's the core source)."""

    model_config = BaseSettingsConfigDict(env_prefix="MEDIUM_")

    ENABLED: bool = Field(default=True)


class NytConfig(BaseConfig):
    """New York Times service. Disabled by default — flip NYT_ENABLED=true
    once NYT_SIGNING_KEY (env, never committed) is set + smoke-tested.
    Egress uses PROXY_LIST[0] (WARP); content via the reverse-engineered
    mobile API; HTML→markdown via the mdream sidecar."""

    model_config = BaseSettingsConfigDict(env_prefix="NYT_")

    ENABLED: bool = Field(default=False)
    MDREAM_URL: str = Field(default="http://mdream:8085")


class AthleticConfig(BaseConfig):
    """The Athletic. Off by default — flip ATHLETIC_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="ATHLETIC_")

    ENABLED: bool = Field(default=False)
    MDREAM_URL: str = Field(default="http://mdream:8085")


class FtConfig(BaseConfig):
    """Financial Times service. Off by default — flip FT_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="FT_")

    ENABLED: bool = Field(default=False)


class EconomistConfig(BaseConfig):
    """The Economist service. Off by default — flip ECONOMIST_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="ECONOMIST_")

    ENABLED: bool = Field(default=False)


class ReutersConfig(BaseConfig):
    """Reuters service. Off by default — flip REUTERS_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="REUTERS_")

    ENABLED: bool = Field(default=False)


class BloombergConfig(BaseConfig):
    """Bloomberg service. Off by default — flip BBG_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="BBG_")

    ENABLED: bool = Field(default=False)


class WapoConfig(BaseConfig):
    """Washington Post service. Off by default — flip WAPO_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="WAPO_")

    ENABLED: bool = Field(default=False)


class QuoraConfig(BaseConfig):
    """Quora service. Off by default — flip QUORA_ENABLED=true."""

    model_config = BaseSettingsConfigDict(env_prefix="QUORA_")

    ENABLED: bool = Field(default=False)
    FLARESOLVERR_URL: str = Field(
        default="http://flaresolverr:8191",
        validation_alias="FLARESOLVERR_URL",
    )


class CacheConfig(BaseConfig):
    """Mongo-backed post-cache settings.

    The cache sits in front of Medium's GraphQL endpoint: on hit, we skip
    the upstream call entirely. CACHE_ENABLED=false disables the path so
    dev/CI environments without a Mongo instance can run cleanly.
    """

    model_config = BaseSettingsConfigDict(env_prefix="")

    CACHE_ENABLED: bool = Field(default=True)
    MONGO_URL: str = Field(default="mongodb://localhost:27017")
    MONGO_DB: str = Field(default="freedium_cache")
    MONGO_COLLECTION: str = Field(default="post_cache")
