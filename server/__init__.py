import nest_asyncio

nest_asyncio.apply()

from loguru import logger
import pickledb
from multiprocessing import Value
import logging
from contextvars import ContextVar
from typing import Optional

import redis.asyncio as redis
from xkcdpass import xkcd_password as xp

from server.utils.loguru_handler import InterceptHandler
from server.utils.logger import configure_logger
from database_lib import SQLiteCacheBackend

# logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
configure_logger()

medium_cache = SQLiteCacheBackend('medium_db_cache.sqlite')
medium_cache.init_db()
medium_cache.enable_zstd()

logger.debug(f"Database length: {medium_cache.all_length()}")

redis_storage = redis.Redis(host="dragonfly", port=6379, db=0)

url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

home_page_process = {}

ban_db = pickledb.load('ban_post_list.db', True)

WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)

maintenance_mode = Value('b', False)
