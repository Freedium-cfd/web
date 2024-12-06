import uvicorn


def start_server(host: str = "0.0.0.0", port: int = 7080) -> None:
    uvicorn.run("freedium_library.api.app:app", host=host, port=port)
