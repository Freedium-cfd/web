import urllib3
from enum import Enum

from loguru import logger

from server import config


class MessageStatus(Enum):
    ERROR = "ERROR"
    GOOD = "GOOD"


def send_message(text: str, silent: bool = False, status: MessageStatus = "ERROR") -> None:
    return True
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_ADMIN_ID:
        logger.warning("Can't send log messages, because of lack of some informations. Ignore....")
        return

    if status == MessageStatus.GOOD.value:
        logger.warning(f"Ignoring sending GOOD message")
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

    http = urllib3.PoolManager()
    response = http.request("POST", url, fields=data)
    if response.status == 200:
        logger.info("Message sent successfully")
    else:
        logger.warning(f"Failed to send message. Status: {response.status}")
