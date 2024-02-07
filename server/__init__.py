import datetime as dt
import pickledb
import logging
from contextvars import ContextVar
from typing import Optional

from jinja2 import Environment, DebugUndefined, FileSystemLoader
import redis.asyncio as redis
from xkcdpass import xkcd_password as xp

from server.utils.loguru_handler import InterceptHandler

redis_storage = redis.Redis(host="dragonfly", port=6379, db=0)

jinja_env = Environment(enable_async=True)
jinja_safe_env = Environment(undefined=DebugUndefined)
template_env = Environment(loader=FileSystemLoader("./server/templates"), enable_async=True)
template_safe_env = Environment(loader=FileSystemLoader("./server/templates"), undefined=DebugUndefined)

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

url_correlation: ContextVar[Optional[str]] = ContextVar("url_correlation", default="UNKNOWN_URL")
home_page_process: ContextVar[Optional[list]] = ContextVar("home_page_process", default=[])
transponder_code_correlation: ContextVar[Optional[str]] = ContextVar("transponder_code_correlation", default="unknown transponder location... Beep!")

ban_db = pickledb.load('ban_post_list.db', True)

START_TIME = dt.datetime.now().strftime("%H-%M-%S")
WORDS_LIST_FILE = "xkcdpass/static/legac"

xkcd_passwd = xp.generate_wordlist(wordfile=WORDS_LIST_FILE, min_length=5, max_length=8)