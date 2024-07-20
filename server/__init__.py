from contextvars import ContextVar
from multiprocessing import Value
from typing import Optional

import pickledb
import redis.asyncio as redis
import time
from psycopg2 import OperationalError, connect
from database_lib import PostgreSQLCacheBackend, migrate_to_postgres, execute_migrate_to_postgres_in_thread
from loguru import logger
from xkcdpass import xkcd_password as xp

from server import config
from server.utils.logger import configure_logger
from server.utils.loguru_handler import InterceptHandler


def wait_for_postgres(max_retries=5, retry_interval=5):
    retries = 0
    while retries < max_retries:
        try:
            conn = connect("postgresql://postgres:postgres@postgres:5432/postgres")
            conn.close()
            logger.info("Successfully connected to PostgreSQL")
            return
        except OperationalError as e:
            logger.warning(f"PostgreSQL is not ready. Retrying in {retry_interval} seconds... (Attempt {retries + 1}/{max_retries})")
            time.sleep(retry_interval)
            retries += 1

    raise Exception("Failed to connect to PostgreSQL after multiple attempts")


wait_for_postgres()

# logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
configure_logger()

medium_cache = PostgreSQLCacheBackend("postgresql://postgres:postgres@postgres:5432/postgres")
medium_cache.init_db()

# migrate_to_postgres_thread = execute_migrate_to_postgres_in_thread("medium_db_cache.sqlite", "postgresql://postgres:postgres@postgres:5432/postgres")

logger.debug(f"Database length: {medium_cache.all_length()}")

redis_storage = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)

url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

home_page_process = {}

ban_db = pickledb.load('ban_post_list.db', True)

WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)

maintenance_mode = Value('b', False)
