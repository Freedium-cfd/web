import datetime as dt
import pickledb
from multiprocessing import Value
import logging
from contextvars import ContextVar
from typing import Optional

import redis.asyncio as redis
from xkcdpass import xkcd_password as xp

from server.utils.loguru_handler import InterceptHandler

redis_storage = redis.Redis(host="dragonfly", port=6379, db=0)


logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

home_page_process = {}

ban_db = pickledb.load('ban_post_list.db', True)

START_TIME = dt.datetime.now().strftime("%H-%M-%S")
WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)

maintenance_mode = Value('b', False)