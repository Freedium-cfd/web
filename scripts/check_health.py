import asyncio
import aiohttp
import os

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
            async with aiohttp.ClientSession() as session:
                async with session.get("https://freedium.cfd", timeout=3) as response:
                    response_status = response.status
        except Exception as ex:
            logger.exception(ex)
            response_status = "ERROR"
        finally:
            if response_status != 200:
                await bot.send_message(ADMIN_CHAT_ID, "EMERGENCY! SITE IS DOWN!!!")

        logger.debug("Sleeping ...")
        await asyncio.sleep(SLEEP_TIME)


asyncio.run(main())
