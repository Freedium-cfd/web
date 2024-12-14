import click


@click.command()
@click.option("--host", default="0.0.0.0", help="Host address to bind to")
@click.option("--port", default=7080, type=int, help="Port to listen on")
@click.option(
    "--hot-reload",
    is_flag=True,
    help="Reload the server on code changes",
    default=False,
)
def cli(host: str, port: int, hot_reload: bool):
    from freedium_library.api.main import start_server

    start_server(host=host, port=port, reload=hot_reload)
