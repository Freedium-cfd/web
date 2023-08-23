import asyncio
import os
import time

import requests
from aiogram import Bot
from loguru import logger

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("No bot token!")

bot = Bot(BOT_TOKEN)

ADMIN_CHAT_ID = "1621425349"
SLEEP_TIME = 15 * 60


async def main():
    while True:
        logger.debug("Checking health of freedium.cfd")
        try:
            response = requests.get("https://freedium.cfd")
            response_status = response.status_code
        except Exception as ex:
            logger.exception(ex)
            response_status = "ERROR"
        finally:
            if response_status != 200:
                await bot.send_message(ADMIN_CHAT_ID, "EMERGENCY! SITE IS DOWN!!!")

        logger.debug("Sleeping ...")
        time.sleep(SLEEP_TIME)


asyncio.run(main())
