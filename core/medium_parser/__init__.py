
from aiohttp_retry import ExponentialRetry
from loguru import logger

import jinja2
from database_lib import SQLiteCacheBackend

cache = SQLiteCacheBackend('medium_db_cache.sqlite')
cache.init_db()
cache.enable_zstd()

logger.debug(f"Database length: {cache.all_length()}")

retry_options = ExponentialRetry(attempts=3)

from . import exceptions as exceptions
from . import exceptions as medium_parser_exceptions

jinja_env = jinja2.Environment(enable_async=True)