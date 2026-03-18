from __future__ import annotations

import asyncio
import json
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from agentic_shopping_agent.models import PurchaseDecision, ShoppingCriterion, ShoppingRequest
from agentic_shopping_agent.ranking import render_text_report
from agentic_shopping_agent.watchlists import DEFAULT_SCHEDULE_MINUTES, WatchlistManager
from agentic_shopping_agent.web_ui import APP_HTML

if TYPE_CHECKING:
    from agentic_shopping_agent.service import ShoppingAgentService


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
MAX_PROGRESS_MESSAGES = 30
MAX_RETAINED_JOBS = 40


class ShoppingRequestPayloadBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    budget: Optional[float] = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=1)
    location: str = Field(default="United States", min_length=1)
    max_options: int = Field(default=4, ge=2, le=8)
    notes: Optional[str] = None
    preferences: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)
    avoids: list[str] = Field(default_factory=list)
    allowed_domains: list[str] = Field(default_factory=list)
    allow_open_web: bool = False
    proxy_country_code: Optional[str] = None
    show_live_url: bool = False
    keep_session: bool = False

    @field_validator("query", "location", mode="before")
    @classmethod
    def _clean_required_text(cls, value: object) -> str:
        text = _sanitize_text(str(value or "")).strip()
        if not text:
            raise ValueError("This field is required.")
        return text

    @field_validator("notes", "proxy_country_code", mode="before")
    @classmethod
    def _clean_optional_text(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        text = _sanitize_text(str(value)).strip()
        return text or None

    @field_validator("budget", mode="before")
    @classmethod
    def _parse_budget(cls, value: object) -> Optional[float]:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        match = re.fullmatch(
            r"(?ix)"
            r"(?:[A-Z]{3}\s*)?"
            r"(?:[$€£¥]\s*)?"
            r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)"
            r"(?:\s*[A-Z]{3})?",
            text,
        )
        if not match:
            raise ValueError("Budget must look like 500, $500, or 1,299.99.")
        return float(match.group(1).replace(",", ""))

    @field_validator("currency", mode="before")
    @classmethod
    def _normalize_currency(cls, value: object) -> str:
        text = _sanitize_text(str(value or "USD")).strip().upper()
        return text or "USD"

    @field_validator("preferences", "must_haves", "avoids", mode="before")
    @classmethod
    def _split_list_fields(cls, value: object) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def _normalize_domains(cls, value: object) -> list[str]:
        return [_normalize_domain(item) for item in _normalize_string_list(value)]

    def to_shopping_request(self) -> ShoppingRequest:
        criteria = []
        criteria.extend(
            ShoppingCriterion(name=item, kind="preference", weight=1.0)
            for item in self.preferences
        )
        criteria.extend(
            ShoppingCriterion(name=item, kind="must_have", weight=1.5)
            for item in self.must_haves
        )
        criteria.extend(
            ShoppingCriterion(name=item, kind="avoid", weight=1.2)
            for item in self.avoids
        )

        return ShoppingRequest(
            query=self.query,
            criteria=criteria,
            budget=self.budget,
            currency=self.currency,
            location=self.location,
            max_options=self.max_options,
            notes=self.notes,
            allowed_domains=self.allowed_domains,
            allow_open_web=self.allow_open_web,
            proxy_country_code=self.proxy_country_code,
        )


class WebShoppingRequestPayload(ShoppingRequestPayloadBase):
    model_config = ConfigDict(extra="forbid")

    show_live_url: bool = False
    keep_session: bool = False


class WebWatchlistPayload(ShoppingRequestPayloadBase):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    schedule_minutes: int = Field(default=DEFAULT_SCHEDULE_MINUTES, ge=15, le=10080)
    target_price: Optional[float] = Field(default=None, ge=0)
    enabled: bool = True
    run_immediately: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        text = _sanitize_text(str(value)).strip()
        return text or None

    def resolved_name(self) -> str:
        return self.name or self.query


@dataclass
class ProgressEntry:
    message: str
    recorded_at: str


@dataclass
class ShoppingJobRecord:
    job_id: str
    created_ts: float
    request_payload: dict
    request: ShoppingRequest
    show_live_url: bool
    keep_session: bool
    state: str = "queued"
    updated_ts: float = field(default_factory=time.time)
    progress_messages: list[ProgressEntry] = field(default_factory=list)
    decision: Optional[PurchaseDecision] = None
    report_text: Optional[str] = None
    error: Optional[str] = None


class ShoppingJobManager:
    def __init__(
        self,
        service_factory: Optional[Callable[[], "ShoppingAgentService"]] = None,
    ) -> None:
        self._service_factory = service_factory or _default_service_factory
        self._jobs: dict[str, ShoppingJobRecord] = {}
        self._lock = threading.Lock()

    def start_job(self, payload: WebShoppingRequestPayload) -> str:
        request = payload.to_shopping_request()
        job_id = uuid.uuid4().hex[:12]
        now = time.time()
        record = ShoppingJobRecord(
            job_id=job_id,
            created_ts=now,
            updated_ts=now,
            request_payload=payload.model_dump(exclude_none=True),
            request=request,
            show_live_url=payload.show_live_url or payload.keep_session,
            keep_session=payload.keep_session,
        )

        with self._lock:
            self._jobs[job_id] = record
            self._prune_jobs_locked()

        worker = threading.Thread(
            target=self._run_job,
            args=(job_id,),
            name=f"shopping-job-{job_id}",
            daemon=True,
        )
        worker.start()
        return job_id

    def get_snapshot(self, job_id: str) -> Optional[dict]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return None
            return self._snapshot_locked(record)

    def _run_job(self, job_id: str) -> None:
        record = self._require_record(job_id)
        self._set_state(job_id, "running")
        self._append_progress(job_id, "Starting shopping job")

        try:
            service = self._service_factory()
            decision = asyncio.run(
                service.research_and_recommend(
                    record.request,
                    show_live_url=record.show_live_url,
                    keep_session=record.keep_session,
                    status_callback=lambda message: self._append_progress(job_id, message),
                )
            )
            report_text = render_text_report(decision)

            with self._lock:
                current = self._jobs[job_id]
                current.decision = decision
                current.report_text = _sanitize_text(report_text, preserve_newlines=True)
                current.error = None
                current.state = "succeeded"
                current.updated_ts = time.time()
                self._append_progress_locked(current, "Recommendation ready")
        except Exception as exc:
            message = _sanitize_text(str(exc)).strip() or "Unknown error"
            with self._lock:
                current = self._jobs[job_id]
                current.state = "failed"
                current.error = message
                current.updated_ts = time.time()
                self._append_progress_locked(current, f"Run failed: {message}")

    def _require_record(self, job_id: str) -> ShoppingJobRecord:
        with self._lock:
            return self._jobs[job_id]

    def _set_state(self, job_id: str, state: str) -> None:
        with self._lock:
            record = self._jobs[job_id]
            record.state = state
            record.updated_ts = time.time()

    def _append_progress(self, job_id: str, message: str) -> None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                return
            self._append_progress_locked(record, message)
            record.updated_ts = time.time()

    @staticmethod
    def _append_progress_locked(record: ShoppingJobRecord, message: str) -> None:
        cleaned = _sanitize_text(message).strip()
        if not cleaned:
            return
        record.progress_messages.append(
            ProgressEntry(
                message=cleaned,
                recorded_at=_utc_isoformat(),
            )
        )
        if len(record.progress_messages) > MAX_PROGRESS_MESSAGES:
            del record.progress_messages[:-MAX_PROGRESS_MESSAGES]

    def _snapshot_locked(self, record: ShoppingJobRecord) -> dict:
        return {
            "job_id": record.job_id,
            "state": record.state,
            "created_at": _isoformat_from_ts(record.created_ts),
            "updated_at": _isoformat_from_ts(record.updated_ts),
            "elapsed_seconds": round(max(0.0, time.time() - record.created_ts), 2),
            "last_message": record.progress_messages[-1].message if record.progress_messages else None,
            "progress_messages": [
                {
                    "message": entry.message,
                    "recorded_at": entry.recorded_at,
                }
                for entry in record.progress_messages
            ],
            "request": record.request_payload,
            "result": record.decision.model_dump(exclude_none=True) if record.decision is not None else None,
            "report_text": record.report_text,
            "error": record.error,
        }

    def _prune_jobs_locked(self) -> None:
        if len(self._jobs) <= MAX_RETAINED_JOBS:
            return

        completed = [
            record
            for record in self._jobs.values()
            if record.state in {"succeeded", "failed"}
        ]
        completed.sort(key=lambda item: item.updated_ts)

        for record in completed:
            if len(self._jobs) <= MAX_RETAINED_JOBS:
                break
            self._jobs.pop(record.job_id, None)


class ShoppingWebRequestHandler(BaseHTTPRequestHandler):
    job_manager: ShoppingJobManager
    watchlist_manager: WatchlistManager

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(APP_HTML)
            return

        if parsed.path == "/api/health":
            self._send_json({"status": "ok"})
            return

        if parsed.path == "/api/dashboard":
            self._send_json(self.watchlist_manager.get_dashboard_snapshot())
            return

        if parsed.path == "/api/alerts":
            self._send_json(self.watchlist_manager.list_alerts_snapshot())
            return

        if parsed.path == "/api/watchlists":
            self._send_json(self.watchlist_manager.list_watchlists_snapshot())
            return

        if parsed.path.startswith("/api/watchlists/"):
            watchlist_id = parsed.path.removeprefix("/api/watchlists/").strip("/")
            snapshot = self.watchlist_manager.get_watchlist_snapshot(watchlist_id)
            if snapshot is None:
                self._send_json({"error": "Watchlist not found."}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(snapshot)
            return

        if parsed.path.startswith("/api/jobs/"):
            job_id = parsed.path.removeprefix("/api/jobs/").strip("/")
            snapshot = self.job_manager.get_snapshot(job_id)
            if snapshot is None:
                self._send_json({"error": "Job not found."}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(snapshot)
            return

        self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            raw_body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            data = json.loads(raw_body.decode("utf-8") or "{}")

            if parsed.path == "/api/jobs":
                payload = WebShoppingRequestPayload.model_validate(data)
                job_id = self.job_manager.start_job(payload)
                snapshot = self.job_manager.get_snapshot(job_id)
                self._send_json(
                    {
                        "job_id": job_id,
                        "job_url": f"/api/jobs/{job_id}",
                        "snapshot": snapshot,
                    },
                    status=HTTPStatus.ACCEPTED,
                )
                return

            if parsed.path == "/api/watchlists":
                payload = WebWatchlistPayload.model_validate(data)
                snapshot = self.watchlist_manager.create_watchlist(
                    name=payload.resolved_name(),
                    request=payload.to_shopping_request(),
                    request_payload=payload.model_dump(exclude_none=True),
                    schedule_minutes=payload.schedule_minutes,
                    target_price=payload.target_price,
                    enabled=payload.enabled,
                    run_immediately=payload.run_immediately,
                )
                self._send_json(snapshot, status=HTTPStatus.CREATED)
                return

            if parsed.path.startswith("/api/watchlists/"):
                remainder = parsed.path.removeprefix("/api/watchlists/").strip("/")
                parts = remainder.split("/")
                if len(parts) == 2 and parts[1] == "run":
                    snapshot = self.watchlist_manager.trigger_run(parts[0], trigger="manual")
                    if snapshot is None:
                        self._send_json({"error": "Watchlist not found."}, status=HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(snapshot, status=HTTPStatus.ACCEPTED)
                    return

                if len(parts) == 2 and parts[1] == "toggle":
                    enabled = bool(data.get("enabled"))
                    snapshot = self.watchlist_manager.set_enabled(parts[0], enabled=enabled)
                    if snapshot is None:
                        self._send_json({"error": "Watchlist not found."}, status=HTTPStatus.NOT_FOUND)
                        return
                    self._send_json(snapshot)
                    return

            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
        except json.JSONDecodeError:
            self._send_json(
                {"error": "Request body must be valid JSON."},
                status=HTTPStatus.BAD_REQUEST,
            )
        except ValidationError as exc:
            self._send_json(
                {
                    "error": "Request payload failed validation.",
                    "details": json.loads(exc.json()),
                },
                status=HTTPStatus.BAD_REQUEST,
            )

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class ShoppingWebAppServer:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        job_manager: Optional[ShoppingJobManager] = None,
        watchlist_manager: Optional[WatchlistManager] = None,
        storage_path: Optional[Path] = None,
        scheduler_interval_seconds: float = 30.0,
    ) -> None:
        self.job_manager = job_manager or ShoppingJobManager()
        self.watchlist_manager = watchlist_manager or WatchlistManager(
            storage_path=storage_path or Path("runtime/watchlists.json"),
            poll_interval_seconds=scheduler_interval_seconds,
        )
        self.watchlist_manager.start()

        manager = self.job_manager
        watchlist_manager_instance = self.watchlist_manager

        class BoundHandler(ShoppingWebRequestHandler):
            job_manager = manager
            watchlist_manager = watchlist_manager_instance

        self._httpd = ThreadingHTTPServer((host, port), BoundHandler)

    @property
    def server_url(self) -> str:
        host, port = self._httpd.server_address[:2]
        public_host = "127.0.0.1" if host in {"0.0.0.0", ""} else host
        return f"http://{public_host}:{port}"

    def serve_forever(self) -> None:
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        self._httpd.shutdown()
        self.watchlist_manager.stop()

    def server_close(self) -> None:
        self._httpd.server_close()


def _default_service_factory() -> "ShoppingAgentService":
    from agentic_shopping_agent.service import ShoppingAgentService

    return ShoppingAgentService()


def _utc_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat()


def _isoformat_from_ts(value: float) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _sanitize_text(value: str, preserve_newlines: bool = False) -> str:
    value = ANSI_ESCAPE_RE.sub("", value)
    cleaned = []
    for char in value:
        codepoint = ord(char)
        if char == "\r":
            continue
        if char == "\n":
            cleaned.append("\n" if preserve_newlines else " ")
            continue
        if char == "\t":
            cleaned.append(" ")
            continue
        if codepoint < 32 or 127 <= codepoint <= 159:
            continue
        cleaned.append(char)
    return "".join(cleaned)


def _normalize_string_list(value: object) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        items = re.split(r"[\n,]+", value)
    elif isinstance(value, list):
        items = [str(item) for item in value]
    else:
        items = [str(value)]

    normalized = []
    for item in items:
        text = _sanitize_text(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_domain(value: str) -> str:
    candidate = value.strip().lower()
    if not candidate:
        return candidate

    if "://" in candidate:
        parsed = urlparse(candidate)
        candidate = parsed.netloc or parsed.path

    candidate = candidate.split("/")[0]
    candidate = candidate.lstrip(".")
    if candidate.startswith("www."):
        candidate = candidate[4:]
    return candidate
