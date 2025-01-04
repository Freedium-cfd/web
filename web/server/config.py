from starlette.config import Config

config: Config = Config(".env")

HOST_ADDRESS: str = config("HOST_ADDRESS", default="https://freedium.cfd")

MEDIUM_AUTH_COOKIES: str | None = config("MEDIUM_AUTH_COOKIES", default=None)

ADMIN_SECRET_KEY: str = config("ADMIN_SECRET_KEY")

TELEGRAM_ADMIN_ID: int = config("TELEGRAM_ADMIN_ID", cast=int, default=0)
TELEGRAM_BOT_TOKEN: str | None = config("TELEGRAM_BOT_TOKEN", default=None)

LOG_LEVEL_NAME: str = config("LOG_LEVEL_NAME", default="INFO")
MORE_LOGS: bool = config("MORE_LOGS", cast=bool, default=False)

DISABLE_EXTERNAL_DOCS: bool = config("DISABLE_EXTERNAL_DOCS", cast=bool, default=True)

TIMEOUT: int = config("TIMEOUT", cast=int, default=38)
REQUEST_TIMEOUT: int = config("REQUEST_TIMEOUT", cast=int, default=12)
WORKER_TIMEOUT: int = config("WORKER_TIMEOUT", cast=int, default=85)

CACHE_LIFE_TIME: int = config("CACHE_LIFE_TIME", cast=int, default=60 * 60 * 5)

HOME_PAGE_MAX_POSTS: int = config("HOME_PAGE_MAX_POSTS", cast=int, default=45)
ENABLE_ADS_BANNER: bool = config("ENABLE_ADS_BANNER", cast=bool, default=False)

REDIS_HOST: str = config("REDIS_HOST", default="redis_service")
REDIS_PORT: int = config("REDIS_PORT", cast=int, default=6379)
REDIS_TIMEOUT: float = config("REDIS_TIMEOUT", cast=float, default=1.75)

DATABASE_URL: str = config("DATABASE_URL", default="postgresql://postgres:postgres@postgres_freedium:5432/postgres")

SENTRY_SDK_DSN: str | None = config("SENTRY_SDK_DSN", default=None)
SENTRY_TRACES_SAMPLE_RATE: float = config("SENTRY_TRACES_SAMPLE_RATE", cast=float, default=0.2)
SENTRY_PROFILES_SAMPLE_RATE: float = config("SENTRY_PROFILES_SAMPLE_RATE", cast=float, default=0.2)

PROXY_LIST_RAW: str = config("PROXY_LIST", cast=str, default="")
PROXY_LIST: list[str] = PROXY_LIST_RAW.split(",") if PROXY_LIST_RAW else []

LOGSTASH_HOST: str = config("LOGSTASH_HOST", default="logstash")
LOGSTASH_PORT: int = config("LOGSTASH_PORT", cast=int, default=5000)
LOGSTASH_PERSISTANCE_DATABASE: str = config("LOGSTASH_PERSISTANCE_DATABASE", default="/user_data/logstash.sqlite3")
