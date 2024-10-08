# Source: https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
# This code taken from comment by GroverChouT

import datetime as dt
import logging
import os
import sys
from pprint import pprint
from typing import Any

from gunicorn.glogging import Logger
from loguru import logger
from loguru._datetime import datetime as loguru_datetime

from server import config

START_TIME = dt.datetime.now().strftime("%H-%M-%S")

# Python's logging module is not supporting TRACE level
# https://bugs.python.org/issue31732
# https://betterstack.com/community/guides/logging/how-to-start-logging-with-python/
logging.addLevelName(5, "TRACE")

ENQUEUE = False  # True # https://github.com/Delgan/loguru/issues/1118
BACKTRACE = True
DIAGNOSE = True
LOG_LEVEL = logging.getLevelName(config.LOG_LEVEL_NAME)

LOG_FORMAT = " | ".join(
    [
        "[{process.id}]",
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>",
        "<level>{level}</level>",
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>",
        "<level>[{extra[id]}] - {message}</level>",
    ]
)
LOG_FOLDER_PATH = f"server/user_data/logs/{{time:YYYY-MM-DD}}/{START_TIME}"
LOG_FOLDER_PATH_FORMATED = LOG_FOLDER_PATH.format(time=loguru_datetime.now())


def logger_register() -> bool:
    pid: int = os.getpid()
    handlers: list[dict[str, Any]] = [
        {
            "sink": sys.stdout,
            "level": LOG_LEVEL,
            "format": LOG_FORMAT,
            "enqueue": ENQUEUE,
            "backtrace": BACKTRACE,
            "diagnose": DIAGNOSE,
        },
    ]
    # handlers.append(
    #     {
    #         "sink": f"{LOG_FOLDER_PATH}/standart_{pid}_log_server",
    #         "level": LOG_LEVEL,
    #         "format": LOG_FORMAT,
    #         "enqueue": ENQUEUE,
    #     }
    # )

    if config.MORE_LOGS:
        handlers.append(
            {
                "sink": f"{LOG_FOLDER_PATH}/debug_{pid}_log_server",
                "level": "DEBUG",
                "format": LOG_FORMAT,
                "enqueue": ENQUEUE,
            }
        )
        handlers.append(
            {
                "sink": f"{LOG_FOLDER_PATH}/trace_{pid}_log_server",
                "level": "TRACE",
                "format": LOG_FORMAT,
                "enqueue": ENQUEUE,
            }
        )

    logger.configure(
        handlers=handlers,
        extra={"id": None},
    )
    return True


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:  # type: ignore
            frame = frame.f_back  # type: ignore
            depth += 1

        raw_message = record.getMessage()  # type: ignore

        try:
            logger.opt(depth=depth, exception=record.exc_info).log(level, raw_message)
        except Exception as ex:
            pprint(raw_message)
            print(raw_message)
            raise ex

        return None


class GunicornLogger(Logger):
    def setup(self, cfg: Any) -> None:
        handler: InterceptHandler = InterceptHandler()
        # logging.getLogger("gunicorn.error").handlers = [InterceptHandler()]
        # logging.getLogger("gunicorn.access").handlers = [InterceptHandler()]
        # Add log handler to logger and set log level
        self.error_log.addHandler(handler)
        self.error_log.setLevel(LOG_LEVEL)
        self.access_log.addHandler(handler)
        self.access_log.setLevel(LOG_LEVEL)

        # Configure logger before gunicorn starts logging
        logger_register()


def configure_logger() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # Remove all log handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure logger (again) if gunicorn is not used
    logger_register()
