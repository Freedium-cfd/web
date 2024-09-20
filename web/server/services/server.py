import uvicorn


def execute_server(host: str = "0.0.0.0", port: int = 7080) -> None:
    uvicorn.run("server.main:app", host=host, port=port)
