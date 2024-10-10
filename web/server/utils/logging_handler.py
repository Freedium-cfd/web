# Based on: https://stackoverflow.com/a/72735401/13452914
import logging
import sys
from types import FrameType

from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Add logging handler to augment python stdlib logging.

    Logs which would otherwise go to stdlib logging are redirected through
    loguru.
    """

    @logger.catch(default=True, onerror=lambda _: sys.exit(1))
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore

        # Find caller from where originated the logged message.
        frame: FrameType | None = sys._getframe(6)  # type: ignore
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
