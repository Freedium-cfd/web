from contextlib import suppress
from datetime import datetime

from server import maintenance_mode
from server.utils.notify import send_message
from server import medium_cache

from time import sleep
from loguru import logger


def enable_maintenance_mode():
    global maintenance_mode
    maintenance_mode.value = True

    logger.debug("Maintenance mode enabled")
    send_message("Maintenance mode enabled")

    now = datetime.now()
    logger.debug(f"Current time: {now}")
    send_message(f"Current time: {now}")

    with suppress(Exception):
        medium_cache.maintenance()

    maintenance_mode.value = False
    logger.debug("Maintenance mode disabled")
    send_message("Maintenance mode disabled")


def do_maintenance(sleep_time: int = 60 * 60 * 24):
    while True:
        sleep(sleep_time)
        try:
            enable_maintenance_mode()
        except Exception as e:
            logger.error(f"Error enabling maintenance mode: {e}")
            send_message(f"Error enabling maintenance mode: {e}")
