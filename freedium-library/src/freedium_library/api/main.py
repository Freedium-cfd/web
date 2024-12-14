import os
from typing import Optional

import uvicorn
from loguru import logger


def start_server(
    host: str = "0.0.0.0",
    port: int = 7080,
    reload: bool = False,
    workers: Optional[int] = None,
) -> None:
    if workers is None:
        workers = (os.cpu_count() or 1) + 1
        logger.warning(f"No workers specified, using CPU count {workers}")

    uvicorn.run(
        "freedium_library.api.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )
