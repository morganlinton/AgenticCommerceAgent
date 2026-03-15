from __future__ import annotations

import argparse
import asyncio
import re
import sys
import threading
import time

from agentic_shopping_agent.models import ShoppingCriterion, ShoppingRequest
from agentic_shopping_agent.ranking import render_text_report
from agentic_shopping_agent.service import ShoppingAgentService


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Research products with Browser Use and return what the agent would buy."
    )
    parser.add_argument("query", nargs="?", help="What you want to buy.")
    parser.add_argument(
        "--budget",
        type=_parse_budget_arg,
        help="Maximum budget in the chosen currency. Accepts values like 500, $500, or 1,299.99.",
    )
    parser.add_argument(
        "--criterion",
        action="append",
        default=[],
        help="Preference that should influence the decision. Repeat for multiple items.",
    )
    parser.add_argument(
        "--must-have",
        action="append",
        default=[],
        help="Hard requirement. Repeat for multiple items.",
    )
    parser.add_argument(
        "--avoid",
        action="append",
        default=[],
        help="Trait the agent should avoid. Repeat for multiple items.",
    )
    parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Restrict browsing to specific domains. Repeat for multiple domains.",
    )
    parser.add_argument(
        "--allow-open-web",
        action="store_true",
        help="Allow browsing beyond the built-in trusted shopping and review domains.",
    )
    parser.add_argument("--notes", help="Extra context for the browsing task.")
    parser.add_argument("--location", default="United States", help="Shopping location.")
    parser.add_argument("--currency", default="USD", help="Preferred currency code.")
    parser.add_argument("--max-options", type=int, default=4, help="How many candidate products to research.")
    parser.add_argument("--proxy-country", help="Browser Use proxy country override such as gb or de.")
    parser.add_argument("--json", action="store_true", help="Print the final recommendation as JSON.")
    parser.add_argument(
        "--show-live-url",
        action="store_true",
        help="Create a Browser Use session and print the live browser URL.",
    )
    parser.add_argument(
        "--keep-session",
        action="store_true",
        help="Keep the Browser Use session alive after the run. Implies --show-live-url behavior.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    progress = ProgressIndicator(stream=sys.stderr)
    try:
        request = _request_from_args(args)
        progress.start("Preparing shopping research")
        decision = asyncio.run(
            ShoppingAgentService().research_and_recommend(
                request,
                show_live_url=args.show_live_url or args.keep_session,
                keep_session=args.keep_session,
                status_callback=progress.update,
            )
        )
    except Exception as exc:
        progress.finish(success=False, message="Research failed")
        raise SystemExit(f"Shopping agent failed: {exc}") from exc
    else:
        progress.finish(success=True, message="Research complete")

    if args.json:
        print(decision.model_dump_json(indent=2, exclude_none=True))
        return

    print(render_text_report(decision))


def _request_from_args(args: argparse.Namespace) -> ShoppingRequest:
    query = args.query or _prompt("What do you want to buy? ")
    notes = args.notes

    criteria = []
    criteria.extend(_criteria_from_values(args.criterion, "preference", 1.0))
    criteria.extend(_criteria_from_values(args.must_have, "must_have", 1.5))
    criteria.extend(_criteria_from_values(args.avoid, "avoid", 1.2))

    if not criteria:
        preferences = _split_csv(
            _prompt(
                "Optional preferences (comma separated, leave blank for none): ",
                required=False,
            )
        )
        criteria.extend(_criteria_from_values(preferences, "preference", 1.0))
        must_haves = _split_csv(
            _prompt(
                "Optional must-haves (comma separated, leave blank for none): ",
                required=False,
            )
        )
        criteria.extend(_criteria_from_values(must_haves, "must_have", 1.5))
        avoids = _split_csv(
            _prompt(
                "Optional avoid rules (comma separated, leave blank for none): ",
                required=False,
            )
        )
        criteria.extend(_criteria_from_values(avoids, "avoid", 1.2))

    budget = args.budget
    if budget is None:
        budget = _prompt_for_budget()

    if notes is None:
        notes = _prompt("Extra notes (leave blank for none): ", required=False) or None

    return ShoppingRequest(
        query=query,
        criteria=criteria,
        budget=budget,
        currency=args.currency,
        location=args.location,
        max_options=args.max_options,
        notes=notes,
        allowed_domains=args.domain,
        allow_open_web=args.allow_open_web,
        proxy_country_code=args.proxy_country,
    )


def _criteria_from_values(values: list[str], kind: str, weight: float) -> list[ShoppingCriterion]:
    return [ShoppingCriterion(name=value.strip(), kind=kind, weight=weight) for value in values if value.strip()]


def _prompt(label: str, required: bool = True) -> str:
    while True:
        value = input(label).strip()
        if value or not required:
            return value


def _split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _prompt_for_budget() -> float | None:
    while True:
        value = _prompt(
            "Optional budget in your chosen currency (leave blank for none): ",
            required=False,
        )
        if not value:
            return None
        try:
            return _parse_budget_value(value)
        except ValueError:
            print("Please enter a budget like 500, $500, or 1,299.99.")


def _parse_budget_arg(value: str) -> float:
    try:
        return _parse_budget_value(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Budget must look like 500, $500, or 1,299.99."
        ) from exc


def _parse_budget_value(value: str) -> float:
    cleaned = value.strip()
    match = re.fullmatch(
        r"(?ix)"
        r"(?:[A-Z]{3}\s*)?"
        r"(?:[$€£¥]\s*)?"
        r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
        r"(?:\s*[A-Z]{3})?",
        cleaned,
    )

    if not match:
        raise ValueError(f"Invalid budget: {value}")

    amount = float(match.group(1).replace(",", ""))
    if amount < 0:
        raise ValueError(f"Budget must be non-negative: {value}")
    return amount


class ProgressIndicator:
    def __init__(self, stream) -> None:
        self.stream = stream
        self.enabled = bool(getattr(stream, "isatty", lambda: False)())
        self._frames = "|/-\\"
        self._frame_index = 0
        self._message = ""
        self._last_printed_message = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None
        self._start_time = None

    def start(self, message: str) -> None:
        self._start_time = time.monotonic()
        self.update(message)
        if self.enabled:
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            self._print_once(f"[progress] {message}")

    def update(self, message: str) -> None:
        with self._lock:
            self._message = _sanitize_terminal_text(message)
        if not self.enabled:
            self._print_once(f"[progress] {self._message}")

    def finish(self, success: bool, message: str) -> None:
        if self._start_time is None:
            return

        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)

        elapsed = time.monotonic() - self._start_time
        prefix = "[done]" if success else "[error]"

        if self.enabled:
            self.stream.write("\r" + (" " * 120) + "\r")
            self.stream.write(f"{prefix} {_sanitize_terminal_text(message)} in {elapsed:.1f}s.\n")
            self.stream.flush()
        else:
            self._print_once(f"{prefix} {_sanitize_terminal_text(message)} in {elapsed:.1f}s.")

    def _spin(self) -> None:
        while not self._stop_event.wait(0.1):
            with self._lock:
                message = self._message
            elapsed = time.monotonic() - self._start_time if self._start_time is not None else 0.0
            frame = self._frames[self._frame_index % len(self._frames)]
            self._frame_index += 1
            self.stream.write(f"\r[{frame}] {message} ({elapsed:.1f}s)")
            self.stream.flush()

    def _print_once(self, message: str) -> None:
        if message == self._last_printed_message:
            return
        print(message, file=self.stream)
        self._last_printed_message = message


def _sanitize_terminal_text(value: str) -> str:
    value = ANSI_ESCAPE_RE.sub("", value)
    sanitized = []
    for char in value:
        codepoint = ord(char)
        if char in "\r\n\t":
            sanitized.append(" ")
            continue
        if codepoint < 32 or 127 <= codepoint <= 159:
            continue
        sanitized.append(char)
    return "".join(sanitized)
