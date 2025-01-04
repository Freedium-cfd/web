import sentry_sdk

from server import config

if config.SENTRY_SDK_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_SDK_DSN,
        traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=config.SENTRY_PROFILES_SAMPLE_RATE,
    )


import time
from contextvars import ContextVar
from multiprocessing import Value
from typing import Optional

import pickledb
import redis.asyncio as redis
from database_lib import PostgreSQLCacheBackend, execute_migrate_to_postgres_in_thread, migrate_to_postgres
from loguru import logger
from medium_parser.api import MediumApi
from medium_parser.core import MediumParser
from psycopg2 import OperationalError, connect
from xkcdpass import xkcd_password as xp

from server.utils.logger import configure_logger


def wait_for_postgres(max_retries=5, retry_interval=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = connect(config.DATABASE_URL)
            conn.close()
            logger.info("Successfully connected to PostgreSQL")
            return
        except OperationalError:
            logger.warning(
                f"PostgreSQL is not ready. Retrying in {retry_interval} seconds... (Attempt {retries + 1}/{max_retries})"
            )
            time.sleep(retry_interval)
            retries += 1

    raise Exception("Failed to connect to PostgreSQL after multiple attempts")


wait_for_postgres()

# logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
configure_logger()

medium_cache = PostgreSQLCacheBackend(config.DATABASE_URL)
medium_cache.init_db()

logger.debug(f"Database length: {medium_cache.all_length()}")

medium_api = MediumApi(
    auth_cookies=config.MEDIUM_AUTH_COOKIES, timeout=config.REQUEST_TIMEOUT, proxy_list=config.PROXY_LIST
)
medium_parser = MediumParser(
    cache=medium_cache,
    medium_api=medium_api,
    timeout=config.REQUEST_TIMEOUT,
    host_address=config.HOST_ADDRESS,
    template_folder="server/templates",
)

redis_storage = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    socket_timeout=config.REDIS_TIMEOUT,
    socket_connect_timeout=config.REDIS_TIMEOUT,
    # decode_responses=True
)

url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar(
    "transponder_code_correlation", default="unknown transponder location... Beep!"
)

ban_db = pickledb.load("ban_post_list.db", True)

WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)

maintenance_mode = Value("b", False)
