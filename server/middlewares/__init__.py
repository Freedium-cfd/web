from starlette.middleware.cors import CORSMiddleware
from server.middlewares.logger import LoggerMiddleware


def register_middlewares(app):
    app.add_middleware(LoggerMiddleware)

    origins = [
        "http://localhost:7080",
    ]

    app.add_middleware(
       CORSMiddleware,
       allow_origins=origins,
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
    )

