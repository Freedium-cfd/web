import atexit
import multiprocessing
from multiprocessing.util import _exit_function

import gunicorn.app.base
import uvicorn
from loguru import logger

from server import config
from server.main import app
from server.utils.logger import GunicornLogger
from server.utils.logger_trace import trace

logger.trace(f"Uvicorn version: {uvicorn.__version__}")


def post_worker_init(worker):
    # Remove the atexit handler set up by the parent process
    # https://github.com/benoitc/gunicorn/issues/1391#issuecomment-467010209
    logger.trace("Removing atexit handler")
    atexit.unregister(_exit_function)


@trace
def number_of_workers():
    cores = multiprocessing.cpu_count()
    if cores >= 8:
        workers = cores
    else:
        workers = cores * 2
    # workers = (cores * 2) + 2
    logger.debug(f"Number of workers: {workers}")
    return workers


class GunicornStandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def execute_server_worker(host: str, port: int):
    options = {
        "bind": f"{host}:{port}",
        "workers": number_of_workers(),
        "logger_class": GunicornLogger,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "preload_app": True,
        "post_worker_init": post_worker_init,
        "timeout": config.WORKER_TIMEOUT,
    }
    GunicornStandaloneApplication(app, options).run()
