import os
import sys
import time
from loguru import logger
import docker
import requests

logger.remove()
logger.add(sys.stdout, level="DEBUG")

error_msg = "[Cloudflare proxy] Freedium proxy is not working, restarting containers..."

USER_NAME = os.getenv("USER_NAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")
PROXY_HOST = os.getenv("PROXY_HOST", "localhost")
PROXY_PORT = os.getenv("PROXY_PORT", "9681")  # 1080

_AUTH_DATA = [USER_NAME, USER_PASSWORD]
AUTH_FORMATED = ":".join(filter(bool, _AUTH_DATA))

if not PROXY_HOST or not PROXY_PORT:
    raise ValueError("PROXY_HOST and PROXY POER must be set")

containers_to_restart = ["dante_1", "wgcf1"]


def restart_containers():
    # client = docker.from_env()
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    for container_name in containers_to_restart:
        try:
            container = client.containers.get(container_name)
            logger.info(f"Restarting {container_name}...")
            container.restart()
            logger.info(f"{container_name} restarted successfully.")
        except docker.errors.NotFound:
            logger.error(f"Container {container_name} not found.")
        except Exception as e:
            logger.error(f"Error restarting {container_name}: {str(e)}")


def send_msg(text: str, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            tg_token = os.getenv("TG_TOKEN")
            chat_id = os.getenv("TG_CHAT_ID")
            url_req = "https://api.telegram.org/bot" + tg_token + "/sendMessage" + "?chat_id=" + chat_id + "&text=" + text
            results = requests.get(url_req)
            logger.debug(results.json())
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error sending message: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in 5 seconds...")
                time.sleep(5)
        else:
            logger.info("Message sent successfully.")
            return True

    logger.error("All retry attempts failed. Message not sent.")
    return False


def check_proxy(max_retries=3, retry_delay=5) -> bool:
    auth_str = f"{AUTH_FORMATED}@" if AUTH_FORMATED else ""

    proxy_url = f"socks5://{auth_str}{PROXY_HOST}:{PROXY_PORT}"
    proxy_test_url = "http://ipinfo.io"
    logger.info(f"Checking proxy: {proxy_url}")
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                proxy_test_url,
                proxies=dict(
                    http=proxy_url,
                    https=proxy_url,
                ),
                timeout=5,
            )
            logger.info(f"Proxy is working: {resp.status_code}")
            return True
        except Exception as e:
            logger.exception(e)
            logger.error(f"Error checking proxy (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    logger.error("All retry attempts failed. Proxy is not working.")
    return False


if __name__ == "__main__":
    while True:
        time.sleep(75)
        # time.sleep(10)
        try:
            logger.info("Checking proxy...")
            if not check_proxy():
                logger.info(error_msg)
                send_msg(error_msg)
                restart_containers()
        except Exception as e:
            logger.error(f"Error checking proxy: {str(e)}")
