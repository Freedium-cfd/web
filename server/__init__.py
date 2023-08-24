import datetime as dt
import logging
from contextvars import ContextVar
from typing import Optional

import jinja2
import redis.asyncio as redis
from xkcdpass import xkcd_password as xp

from server import config
from server.utils.loguru_handler import InterceptHandler

redis_storage = redis.Redis(host="localhost", port=6379, db=0)

jinja_env = jinja2.Environment(enable_async=True)
template_env = jinja2.Environment(loader=jinja2.FileSystemLoader("./server/templates"), enable_async=True)

from server.toolkits.core.medium_parser import medium_parser_exceptions
from server.toolkits.core.medium_parser.core import MediumParser
from server.toolkits.core.medium_parser.utils import minify_html

base_template = template_env.get_template("base.html")
main_template = template_env.get_template("main.html")
error_template = template_env.get_template("error.html")

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
post_id_correlation: ContextVar[Optional[str]] = ContextVar("post_id_correlation", default="UNKNOWN_ID")
url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

START_TIME = dt.datetime.now().strftime("%H-%M-%S")
WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)

if config.TELEGRAM_BOT_TOKEN:
    from aiogram import Bot
    bot = Bot(config.TELEGRAM_BOT_TOKEN)
else:
    bot = None
