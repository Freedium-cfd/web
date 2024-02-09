import asyncio
import aiohttp
from enum import Enum

from loguru import logger

from server import config


class MessageStatus(Enum):
    ERROR = "ERROR"
    GOOD = "GOOD"


def send_message(text: str, silent: bool = False, status: MessageStatus = "ERROR") -> None:
    asyncio.create_task(task_send_message(text, silent, status))


async def task_send_message(text: str, silent: bool = False, status: MessageStatus = "ERROR") -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_ADMIN_ID:
        logger.warning("Can't send log messages, because of lack of some informations. Ignore....")
        return

    if status == MessageStatus.GOOD.value:
        return True

    if len(text) > 4000:
        logger.warning(f"Message is too long ({len(text)}): {text}")
        text = text[:4000]

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": config.TELEGRAM_ADMIN_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": silent
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            if response.status == 200:
                logger.info("Message sent successfully")
            else:
                logger.warning(f"Failed to send message. Status: {response.status}")