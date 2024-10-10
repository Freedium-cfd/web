from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

from starlette.middleware.cors import CORSMiddleware

from server.middlewares.logger import LoggerMiddleware

CORS_ALLOW_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
