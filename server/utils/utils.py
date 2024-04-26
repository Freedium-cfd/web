import random
import socket

from server.utils.logger_trace import trace


def string_to_number_ascii(input_str: str, key_number: int = None):
    if not key_number:
        key_number = random.randint(0, 100)
    input_str = input_str.upper()
    result = sum(ord(char) for char in input_str)
    result *= key_number
    return result


def is_negative(num: int) -> bool:
    return num < 0


async def safe_check_redis_connection(connection):
    try:
        response = await connection.ping()
    except Exception:
        return False
    else:
        return response


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0
