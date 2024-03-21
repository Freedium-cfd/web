from contextlib import suppress
from datetime import datetime

from server import maintenance_mode, scheduler
from server.utils.notify import send_message
from medium_parser import cache as medium_cache

from loguru import logger


def enable_maintenance_mode():
    global maintenance_mode
    maintenance_mode = True
    logger.debug("Maintenance mode enabled")

    send_message("Maintenance mode enabled")

    now = datetime.now()
    logger.debug(f"Current time: {now}")
    send_message(f"Current time: {now}")

    with suppress(Exception):
        medium_cache.maintenance()

    maintenance_mode = False
    logger.debug("Maintenance mode disabled")
    send_message("Maintenance mode disabled")

scheduler.add_job(enable_maintenance_mode, 'cron', hour='*/2')

scheduler.start()