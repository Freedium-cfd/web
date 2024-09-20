import pickle
from server import redis_storage
from functools import wraps
from loguru import logger
from server.utils.utils import safe_check_redis_connection


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
