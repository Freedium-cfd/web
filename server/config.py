from starlette.config import Config

config = Config(".env")

LOG_LEVEL_NAME = config("LOG_LEVEL_NAME", default="INFO")
TIMEOUT = config("TIMEOUT", cast=int, default=3)
SENTRY_SDK_DSN = config("SENTRY_SDK_DSN", default=None)
ENABLE_ADS_BANNER = config("ENABLE_ADS_BANNER", cast=bool, default=True)