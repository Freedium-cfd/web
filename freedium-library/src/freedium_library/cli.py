import asyncclick as click


@click.command()
@click.option("--host", default="0.0.0.0", help="Host address to bind to")
@click.option("--port", default=7080, type=int, help="Port to listen on")
async def cli(host: str, port: int):
    from freedium_library.api.main import start_server

    start_server(host=host, port=port)
