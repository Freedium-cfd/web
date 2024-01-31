import asyncio
import time
from functools import wraps

from loguru import logger


def trace(func):
    if asyncio.iscoroutinefunction(func):
        logger.trace(f"{func.__name__!r} function is a coroutine")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_ts = time.time()
            logger.trace(f"Calling {func.__name__}() with {args}, {kwargs}")
            original_result = await func(*args, **kwargs)
            logger.trace(f"Result: {original_result}")
            logger.trace(f"Result type: {type(original_result)}")
            duration_ts = time.time() - start_ts
            result = f"{original_result[:42]}..." if type(original_result).__name__ in ["str", "bytes"] else original_result
            logger.trace(f"{func.__name__!r}() returned {result!r} in {duration_ts:.2} seconds")
            return original_result

    else:
        logger.trace(f"{func.__name__!r} is not a coroutine")

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_ts = time.time()
            logger.trace(f"Calling {func.__name__}() with {args}, {kwargs}")
            original_result = func(*args, **kwargs)
            logger.trace(f"Result: {original_result}")
            logger.trace(f"Result type: {type(original_result)}")
            duration_ts = time.time() - start_ts
            result = f"{original_result[:42]}..." if type(original_result).__name__ in ["str", "bytes"] else original_result
            logger.trace(f"{func.__name__!r}() returned {result!r} in {duration_ts:.2} seconds")
            return original_result

    return wrapper
