from starlette.config import Config

config = Config(".env")

HOST_ADDRESS = config("HOST_ADDRESS", default="https://freedium.cfd")
TELEGRAM_ADMIN_ID = config("TELEGRAM_ADMIN_ID", cast=int, default=0)
SECRET_KEY = config("SECRET_KEY")
GOOD_TELEGRAM_BOT_TOKEN = config("GOOD_TELEGRAM_BOT_TOKEN", default=None)
BAD_TELEGRAM_BOT_TOKEN = config("BAD_TELEGRAM_BOT_TOKEN", default=None)
LOG_LEVEL_NAME = config("LOG_LEVEL_NAME", default="INFO")
IS_DEV = config("IS_DEV", cast=bool, default=False)
TIMEOUT = config("TIMEOUT", cast=int, default=20)
REQUEST_TIMEOUT = config("REQUEST_TIMEOUT", cast=int, default=40)
WORKER_TIMEOUT = config("WORKER_TIMEOUT", cast=int, default=60)
SENTRY_SDK_DSN = config("SENTRY_SDK_DSN", default=None)
ENABLE_ADS_BANNER = config("ENABLE_ADS_BANNER", cast=bool, default=True)
