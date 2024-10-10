from argparse import ArgumentParser, Namespace

from loguru import logger


def cli():
    parser = ArgumentParser(prog="python3 -m server", description="Freedium server CLI")
    cmd_subparsers = parser.add_subparsers(dest="cmd", required=True)

    server_cmd_parser = cmd_subparsers.add_parser("server")
    server_cmd_parser.add_argument("--port", nargs="?", type=int, const=7080, help="Port number", default=7080)

    opts = parser.parse_args()
    logger.trace(opts)

    if opts.cmd == "server":
        server_cmd(server_cmd_parser, opts)


def server_cmd(cmd: ArgumentParser, opts: Namespace):
    from server.utils.utils import is_port_in_use

    if is_port_in_use(opts.port):
        cmd.error(f"Port {opts.port} is in use or permission denied")

    # from server.services.worker import execute_server_worker
    from server.services.uvicorn import execute_server

    # from server.utils.maintenance_scheduler import do_maintenance
    # threading.Thread(target=do_maintenance, daemon=True).start()
    # execute_server_worker(host="0.0.0.0", port=opts.port)
    execute_server(host="0.0.0.0", port=opts.port)
