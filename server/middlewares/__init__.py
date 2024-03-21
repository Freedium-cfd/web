from starlette.middleware.cors import CORSMiddleware
from server.middlewares.logger import LoggerMiddleware
from server.middlewares.maintenance_mode import MaintenanceModeMiddleware

origins = ["*"]

def register_middlewares(app):
    app.add_middleware(MaintenanceModeMiddleware)
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
