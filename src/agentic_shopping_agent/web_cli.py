from __future__ import annotations

import argparse

from agentic_shopping_agent.webapp import ShoppingWebAppServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Agentic Shopping Agent web app with live progress and comparison output."
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host for the local web server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind port for the local web server.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    server = ShoppingWebAppServer(host=args.host, port=args.port)
    print(f"Agentic Shopping Agent web app running at {server.server_url}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("Shutting down web app.")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
