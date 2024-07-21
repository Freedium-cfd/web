from starlette.config import Config

config = Config(".env")

HOST_ADDRESS = config("HOST_ADDRESS", default="https://freedium.cfd")

MEDIUM_AUTH_COOKIES = config("MEDIUM_AUTH_COOKIES", default=None)

ADMIN_SECRET_KEY = config("ADMIN_SECRET_KEY")

TELEGRAM_ADMIN_ID = config("TELEGRAM_ADMIN_ID", cast=int, default=0)
TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default=None)

LOG_LEVEL_NAME = config("LOG_LEVEL_NAME", default="INFO")
MORE_LOGS = config("MORE_LOGS", cast=bool, default=False)

DISABLE_EXTERNAL_DOCS = config("DISABLE_EXTERNAL_DOCS", cast=bool, default=True)
DISABLE_RATE_LIMITER = config("DISABLE_RATE_LIMITER", cast=bool, default=True)

TIMEOUT = config("TIMEOUT", cast=int, default=25)
REQUEST_TIMEOUT = config("REQUEST_TIMEOUT", cast=int, default=40)
WORKER_TIMEOUT = config("WORKER_TIMEOUT", cast=int, default=120)

CACHE_LIFE_TIME = config("CACHE_LIFE_TIME", cast=int, default=60 * 60 * 5)

HOME_PAGE_MAX_POSTS = config("HOME_PAGE_MAX_POSTS", cast=int, default=15)
ENABLE_ADS_BANNER = config("ENABLE_ADS_BANNER", cast=bool, default=False)

REDIS_HOST = config("REDIS_HOST", default="redis_service")
REDIS_PORT = config("REDIS_PORT", cast=int, default=6379)
REDIS_TIMEOUT = config("REDIS_TIMEOUT", cast=int, default=1.75)

SENTRY_SDK_DSN = config("SENTRY_SDK_DSN", default=None)
SENTRY_TRACES_SAMPLE_RATE = config("SENTRY_TRACES_SAMPLE_RATE", cast=float, default=0.2)
SENTRY_PROFILES_SAMPLE_RATE = config("SENTRY_PROFILES_SAMPLE_RATE", cast=float, default=0.2)
