import asyncio
from enum import Enum

from loguru import logger

from server import good_bot, bad_bot, config

ADMIN_ID = config.TELEGRAM_ADMIN_ID


class MessageStatus(Enum):
    ERROR = "ERROR"
    GOOD = "GOOD"


async def send_message(text: str, silent: bool = False, status: MessageStatus = "ERROR") -> None:
    asyncio.create_task(task_send_message(text, silent, status))


async def task_send_message(text: str, silent: bool = False, status: MessageStatus = "ERROR") -> None:
    if not config.BAD_TELEGRAM_BOT_TOKEN or not config.GOOD_TELEGRAM_BOT_TOKEN or not ADMIN_ID:
        logger.warning("Can't send log messages, because of lack of some informations. Ignore....")
        return

    if status == MessageStatus.GOOD.value:
        bot = good_bot
    else:
        bot = bad_bot

    await bot.send_message(ADMIN_ID, text, parse_mode="HTML", disable_notification=silent)
