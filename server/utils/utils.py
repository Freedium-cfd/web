import pickle
import random
import re
import socket
from functools import wraps
from urllib.parse import urlparse

from loguru import logger

from server import redis_storage
from server.utils.logger_trace import trace

DEFAULT_PROTOCOL = "https://"

@trace
def correct_url(url: str) -> str:
    url = re.sub(r"https?://?", DEFAULT_PROTOCOL, url)

    parsed_url = urlparse(url)
    if not bool(parsed_url.netloc and parsed_url.scheme):
        return DEFAULT_PROTOCOL + "://" + url

    # if not re.match(r'http[s]?://', url):
    #     url = DEFAULT_PROTOCOL + '://' + url

    return url

def string_to_number_ascii(input_str: str, key_number: int = None):
    if not key_number:
        key_number = random.randint(0, 100)
    input_str = input_str.upper()
    result = sum(ord(char) for char in input_str)
    result *= key_number
    return result


def is_negative(num: int) -> bool:
    return num < 0


async def safe_check_redis_connection(connection):
    try:
        response = await connection.ping()
    except Exception:
        return False
    else:
        return response


def aio_redis_cache(expire_time: int = 60 * 10):  # enable_pickle: bool = False
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await safe_check_redis_connection(redis_storage):
                logger.error("REDIS is not available!")
                return await func(*args, **kwargs)
            # logger.trace(f"{enable_pickle=}, {expire_time=}")
            logger.trace(f"{expire_time=}")
            # Serialize the arguments and function name as a key for Redis
            key = "{}-{}".format(func.__name__, ",".join(str(arg) for arg in args))
            logger.trace(f"REDIS key: {key}")
            result = await redis_storage.get(key)

            if result is not None:
                # If the result is found in Redis cache, deserialize and return it
                # if enable_pickle:  # type(result).__name__ != "str"
                result_raw = pickle.loads(result)
                # else:
                #     result = result.decode("utf-8")
                logger.trace("Result found in REDIS")
            else:
                logger.trace("Result not found in REDIS")
                # If the result is not found in Redis cache, call the original function
                result_raw = await func(*args, **kwargs)
                # if enable_pickle:
                result = pickle.dumps(result_raw)
                # else:
                #     result = result.encode("utf-8")
                # Store the result in Redis with an expiration time
                await redis_storage.setex(key, expire_time, result)

            return result_raw

        return wrapper

    return decorator


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0