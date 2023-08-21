from server.middlewares.logger import LoggerMiddleware


def register_middlewares(app):
    app.add_middleware(LoggerMiddleware)
