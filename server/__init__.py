import datetime as dt
from multiprocessing import Lock, Manager
import logging
from contextvars import ContextVar
from typing import Optional

from jinja2 import Environment, DebugUndefined, FileSystemLoader
import redis.asyncio as redis
from xkcdpass import xkcd_password as xp

from server import config
from server.utils.loguru_handler import InterceptHandler

redis_storage = redis.Redis(host="localhost", port=6379, db=0)

jinja_env = Environment(enable_async=True)
jinja_safe_env = Environment(undefined=DebugUndefined)
template_env = Environment(loader=FileSystemLoader("./server/templates"), enable_async=True)
template_safe_env = Environment(loader=FileSystemLoader("./server/templates"), undefined=DebugUndefined)

from server.toolkits.core.medium_parser import medium_parser_exceptions
from server.toolkits.core.medium_parser.core import MediumParser
from server.toolkits.core.medium_parser.utils import minify_html, is_valid_medium_post_id_hexadecimal

base_template = template_env.get_template("base.html")
url_line_template = template_env.get_template("url_line.html").render()
main_template_raw = template_safe_env.get_template("main.html")
postleter_template = template_env.get_template("postleter.html")
error_template_raw = template_safe_env.get_template("error.html")

main_template_raw_rendered = main_template_raw.render(url_line=url_line_template)
main_template = jinja_env.from_string(main_template_raw_rendered)

error_template_raw_rendered = error_template_raw.render(url_line=url_line_template)
error_template = jinja_env.from_string(error_template_raw_rendered)

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
post_id_correlation: ContextVar[Optional[str]] = ContextVar("post_id_correlation", default="UNKNOWN_ID")
url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

manager = Manager()

# TODO: workaround
db_backup_startup_correlation = manager.dict(registered=False)
db_backup_startup_lock = Lock()

START_TIME = dt.datetime.now().strftime("%H-%M-%S")
WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)


if config.TELEGRAM_BOT_TOKEN:
    from aiogram import Bot
    bot = Bot(config.TELEGRAM_BOT_TOKEN)
else:
    bot = None
