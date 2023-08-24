import asyncio

from server import bot, config

ADMIN_ID = config.TELEGRAM_ADMIN_ID


async def send_message(text: str) -> None:
    if config.TELEGRAM_BOT_TOKEN and ADMIN_ID:
        asyncio.create_task(bot.send_message(ADMIN_ID, text, parse_mode="HTML"))
