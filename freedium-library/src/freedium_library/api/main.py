import os
from typing import Optional

import uvicorn
from dependency_injector.wiring import Provide, inject
from loguru import logger

from freedium_library.api.config import APIConfig, ServerConfig
from freedium_library.api.container import APIContainer


def calculate_workers(
    requested_workers: Optional[int] = None, max_workers: int = 10
) -> int:
    if requested_workers is not None:
        return requested_workers

    cpu_count = os.cpu_count() or 1
    workers = min(cpu_count + 1, max_workers)

    if workers == 1:
        logger.warning("Only one worker, this is not recommended for production.")
    elif workers == max_workers:
        logger.warning(
            f"Using hardcoded maximum workers ({max_workers}), consider passing a lower number."
        )
    else:
        logger.info(f"Using {workers} workers based on CPU count.")

    return workers


@inject
def start_server(
    server_config: Optional[ServerConfig] = Provide[APIContainer.server_config],
    config: APIConfig = Provide[APIContainer.config],
) -> None:
    if server_config is None:
        logger.warning("No server config provided, using defaults.")
        server_config = ServerConfig(
            host=config.HOST,
            port=config.PORT,
        )

    workers = calculate_workers(server_config.workers, config.MAX_WORKERS)

    uvicorn.run(
        "freedium_library.api.app:app",
        host=server_config.host,
        port=server_config.port,
        reload=server_config.reload,
        workers=workers,
    )
