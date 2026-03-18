from __future__ import annotations

import argparse
from pathlib import Path

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
    parser.add_argument(
        "--storage-path",
        type=Path,
        default=Path("runtime/watchlists.json"),
        help="Path used to persist watchlists, alerts, and run history.",
    )
    parser.add_argument(
        "--scheduler-poll-seconds",
        type=float,
        default=30.0,
        help="How often the watchlist scheduler checks for due reruns.",
    )
    parser.add_argument(
        "--unsafe-listen",
        action="store_true",
        help="Allow binding the web app to a non-loopback host. Use only on a trusted network.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    server = ShoppingWebAppServer(
        host=args.host,
        port=args.port,
        storage_path=args.storage_path,
        scheduler_interval_seconds=args.scheduler_poll_seconds,
        unsafe_listen=args.unsafe_listen,
    )
    if args.unsafe_listen:
        print("Warning: remote clients can reach the web app on this bind host.")
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
