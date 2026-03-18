from __future__ import annotations

import asyncio
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from agentic_shopping_agent.models import PurchaseDecision, ShoppingRequest
from agentic_shopping_agent.ranking import render_text_report

if TYPE_CHECKING:
    from agentic_shopping_agent.service import ShoppingAgentService


DEFAULT_SCHEDULE_MINUTES = 360
MAX_RUNS_PER_WATCHLIST = 20
MAX_ALERTS = 120
MAX_WATCHLISTS = 25
MODEL_TOKEN_RE = re.compile(r"\b[A-Z0-9]{4,}\b")
GENERIC_NAME_TOKENS = {
    "the",
    "with",
    "for",
    "and",
    "from",
    "inch",
    "inches",
    "wireless",
    "edition",
    "model",
    "gen",
    "generation",
}


class TrackedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity_key: str
    product_name: str
    retailer: str
    product_url: Optional[str] = None
    rank: int = Field(ge=1)
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    availability: Optional[str] = None
    total_score: float
    verification_status: str


class WatchlistChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_type: str
    summary: str
    product_name: Optional[str] = None
    product_key: Optional[str] = None
    previous_value: Optional[str] = None
    current_value: Optional[str] = None


class WatchlistRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    watchlist_id: str
    trigger: str
    state: str
    started_at: str
    completed_at: Optional[str] = None
    recommended_product_key: Optional[str] = None
    recommended_product_name: Optional[str] = None
    recommended_price: Optional[float] = Field(default=None, ge=0)
    recommended_currency: Optional[str] = None
    recommended_availability: Optional[str] = None
    verification_status: Optional[str] = None
    progress_messages: list[str] = Field(default_factory=list)
    tracked_products: list[TrackedProduct] = Field(default_factory=list)
    changes: list[WatchlistChange] = Field(default_factory=list)
    alert_summaries: list[str] = Field(default_factory=list)
    report_text: Optional[str] = None
    decision_snapshot: Optional[dict] = None
    error: Optional[str] = None


class WatchlistAlert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    watchlist_id: str
    watchlist_name: str
    run_id: str
    created_at: str
    severity: str
    event_type: str
    title: str
    summary: str


class WatchlistRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    request: ShoppingRequest
    request_payload: dict
    schedule_minutes: int = Field(ge=1, le=10080)
    target_price: Optional[float] = Field(default=None, ge=0)
    enabled: bool = True
    created_at: str
    updated_at: str
    next_run_at: Optional[str] = None
    last_run_at: Optional[str] = None
    last_run_state: Optional[str] = None
    last_run_id: Optional[str] = None
    last_recommended_product: Optional[str] = None
    last_recommended_price: Optional[float] = Field(default=None, ge=0)
    last_recommended_currency: Optional[str] = None
    last_verification_status: Optional[str] = None
    last_alert_summary: Optional[str] = None


class WatchlistDatabase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    watchlists: list[WatchlistRecord] = Field(default_factory=list)
    runs: list[WatchlistRun] = Field(default_factory=list)
    alerts: list[WatchlistAlert] = Field(default_factory=list)


class WatchlistLimitError(RuntimeError):
    pass


class WatchlistManager:
    def __init__(
        self,
        storage_path: Path,
        service_factory: Optional[Callable[[], "ShoppingAgentService"]] = None,
        poll_interval_seconds: float = 30.0,
    ) -> None:
        self.storage_path = storage_path
        self._service_factory = service_factory or _default_service_factory
        self._poll_interval_seconds = max(0.5, poll_interval_seconds)
        self._lock = threading.Lock()
        self._db = self._load_database()
        self._active_watchlists: set[str] = set()
        self._stop_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        with self._lock:
            if self._recover_incomplete_runs_locked():
                self._persist_locked()

    def start(self) -> None:
        if self._scheduler_thread is not None:
            return

        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="watchlist-scheduler",
            daemon=True,
        )
        self._scheduler_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=1.0)
            self._scheduler_thread = None
        self._stop_event.clear()

    def create_watchlist(
        self,
        *,
        name: str,
        request: ShoppingRequest,
        request_payload: dict,
        schedule_minutes: int,
        target_price: Optional[float],
        enabled: bool = True,
        run_immediately: bool = True,
    ) -> dict:
        now = _utc_isoformat()
        watchlist = WatchlistRecord(
            id=uuid.uuid4().hex[:12],
            name=_sanitize_text(name).strip() or _sanitize_text(request.query).strip(),
            request=request,
            request_payload=request_payload,
            schedule_minutes=schedule_minutes or DEFAULT_SCHEDULE_MINUTES,
            target_price=target_price,
            enabled=enabled,
            created_at=now,
            updated_at=now,
            next_run_at=now if enabled and not run_immediately else None,
        )

        with self._lock:
            if len(self._db.watchlists) >= MAX_WATCHLISTS:
                raise WatchlistLimitError(
                    f"Watchlist limit reached ({MAX_WATCHLISTS}). Delete or pause old watchlists before creating more."
                )
            self._db.watchlists.append(watchlist)
            self._persist_locked()

        if enabled and run_immediately:
            self.trigger_run(watchlist.id, trigger="initial")

        snapshot = self.get_watchlist_snapshot(watchlist.id)
        if snapshot is None:
            raise RuntimeError("Watchlist was created but could not be loaded.")
        return snapshot

    def list_watchlists_snapshot(self) -> dict:
        with self._lock:
            watchlists = [self._watchlist_snapshot_locked(record) for record in self._sorted_watchlists_locked()]
            return {
                "watchlists": watchlists,
                "active_watchlists": sorted(self._active_watchlists),
            }

    def list_alerts_snapshot(self, limit: int = 20) -> dict:
        with self._lock:
            alerts = sorted(self._db.alerts, key=lambda item: item.created_at, reverse=True)[:limit]
            return {
                "alerts": [alert.model_dump(exclude_none=True) for alert in alerts],
            }

    def get_dashboard_snapshot(self) -> dict:
        data = self.list_watchlists_snapshot()
        data.update(self.list_alerts_snapshot())
        return data

    def get_watchlist_snapshot(self, watchlist_id: str) -> Optional[dict]:
        with self._lock:
            record = self._get_watchlist_locked(watchlist_id)
            if record is None:
                return None
            return self._watchlist_snapshot_locked(record, include_full_history=True)

    def set_enabled(self, watchlist_id: str, enabled: bool) -> Optional[dict]:
        with self._lock:
            record = self._get_watchlist_locked(watchlist_id)
            if record is None:
                return None
            record.enabled = enabled
            record.updated_at = _utc_isoformat()
            if enabled and record.next_run_at is None and watchlist_id not in self._active_watchlists:
                record.next_run_at = _utc_isoformat()
            if not enabled:
                record.next_run_at = None
            self._persist_locked()
            return self._watchlist_snapshot_locked(record, include_full_history=True)

    def trigger_run(self, watchlist_id: str, trigger: str = "manual") -> Optional[dict]:
        with self._lock:
            record = self._get_watchlist_locked(watchlist_id)
            if record is None:
                return None
            if watchlist_id in self._active_watchlists:
                return self._watchlist_snapshot_locked(record, include_full_history=True)

            self._active_watchlists.add(watchlist_id)
            run = WatchlistRun(
                id=uuid.uuid4().hex[:12],
                watchlist_id=watchlist_id,
                trigger=trigger,
                state="running",
                started_at=_utc_isoformat(),
                progress_messages=["Starting watchlist run"],
            )
            self._db.runs.append(run)
            record.last_run_id = run.id
            record.last_run_state = "running"
            record.last_run_at = run.started_at
            record.updated_at = run.started_at
            record.next_run_at = None
            self._trim_runs_locked(watchlist_id)
            self._persist_locked()

        worker = threading.Thread(
            target=self._run_watchlist,
            args=(watchlist_id, run.id),
            name=f"watchlist-run-{watchlist_id}",
            daemon=True,
        )
        worker.start()
        return self.get_watchlist_snapshot(watchlist_id)

    def _scheduler_loop(self) -> None:
        while not self._stop_event.wait(self._poll_interval_seconds):
            due_watchlist_ids = self._due_watchlist_ids()
            for watchlist_id in due_watchlist_ids:
                self.trigger_run(watchlist_id, trigger="scheduled")

    def _due_watchlist_ids(self) -> list[str]:
        now_ts = time.time()
        due_ids: list[str] = []
        with self._lock:
            for record in self._db.watchlists:
                if not record.enabled or record.id in self._active_watchlists:
                    continue
                if record.next_run_at is None:
                    continue
                if _parse_iso(record.next_run_at) <= now_ts:
                    due_ids.append(record.id)
        return due_ids

    def _run_watchlist(self, watchlist_id: str, run_id: str) -> None:
        with self._lock:
            record = self._get_watchlist_locked(watchlist_id)
            run = self._get_run_locked(run_id)
            if record is None or run is None:
                self._active_watchlists.discard(watchlist_id)
                return
            request = record.request
            previous_run = self._latest_successful_run_locked(watchlist_id, exclude_run_id=run_id)

        try:
            service = self._service_factory()
            decision = asyncio.run(
                service.research_and_recommend(
                    request,
                    status_callback=lambda message: self._append_run_progress(watchlist_id, run_id, message),
                )
            )
            report_text = render_text_report(decision)
            tracked_products = _tracked_products_from_decision(decision)
            changes = _build_run_changes(previous_run, tracked_products, decision, target_price=record.target_price)
            alerts = _build_alerts(record, run_id, changes)

            with self._lock:
                current_record = self._get_watchlist_locked(watchlist_id)
                current_run = self._get_run_locked(run_id)
                if current_record is None or current_run is None:
                    return

                current_run.state = "succeeded"
                current_run.completed_at = _utc_isoformat()
                current_run.tracked_products = tracked_products
                current_run.report_text = _sanitize_text(report_text, preserve_newlines=True)
                current_run.decision_snapshot = decision.model_dump(exclude_none=True)
                current_run.changes = changes
                current_run.alert_summaries = [alert.summary for alert in alerts]
                current_run.recommended_product_key = tracked_products[0].identity_key if tracked_products else None
                current_run.recommended_product_name = tracked_products[0].product_name if tracked_products else None
                current_run.recommended_price = tracked_products[0].price if tracked_products else None
                current_run.recommended_currency = tracked_products[0].currency if tracked_products else None
                current_run.recommended_availability = tracked_products[0].availability if tracked_products else None
                current_run.verification_status = tracked_products[0].verification_status if tracked_products else None

                current_record.last_run_id = current_run.id
                current_record.last_run_state = current_run.state
                current_record.last_run_at = current_run.completed_at
                current_record.last_recommended_product = current_run.recommended_product_name
                current_record.last_recommended_price = current_run.recommended_price
                current_record.last_recommended_currency = current_run.recommended_currency
                current_record.last_verification_status = current_run.verification_status
                current_record.last_alert_summary = alerts[0].summary if alerts else None
                current_record.updated_at = current_run.completed_at
                current_record.next_run_at = (
                    _future_iso(minutes=current_record.schedule_minutes)
                    if current_record.enabled
                    else None
                )

                self._db.alerts.extend(alerts)
                self._trim_runs_locked(watchlist_id)
                self._trim_alerts_locked()
                self._active_watchlists.discard(watchlist_id)
                self._persist_locked()
        except Exception as exc:
            message = _sanitize_text(str(exc)).strip() or "Unknown error"
            with self._lock:
                current_record = self._get_watchlist_locked(watchlist_id)
                current_run = self._get_run_locked(run_id)
                if current_record is None or current_run is None:
                    return

                current_run.state = "failed"
                current_run.completed_at = _utc_isoformat()
                current_run.error = message
                current_run.changes = [
                    WatchlistChange(
                        change_type="run_failed",
                        summary=f"Watchlist run failed: {message}",
                    )
                ]
                current_record.last_run_id = current_run.id
                current_record.last_run_state = "failed"
                current_record.last_run_at = current_run.completed_at
                current_record.updated_at = current_run.completed_at
                current_record.last_alert_summary = f"Run failed: {message}"
                current_record.next_run_at = (
                    _future_iso(minutes=current_record.schedule_minutes)
                    if current_record.enabled
                    else None
                )

                self._db.alerts.append(
                    WatchlistAlert(
                        id=uuid.uuid4().hex[:12],
                        watchlist_id=current_record.id,
                        watchlist_name=current_record.name,
                        run_id=current_run.id,
                        created_at=current_run.completed_at,
                        severity="warning",
                        event_type="run_failed",
                        title="Watchlist run failed",
                        summary=message,
                    )
                )
                self._trim_runs_locked(watchlist_id)
                self._trim_alerts_locked()
                self._active_watchlists.discard(watchlist_id)
                self._persist_locked()

    def _append_run_progress(self, watchlist_id: str, run_id: str, message: str) -> None:
        cleaned = _sanitize_text(message).strip()
        if not cleaned:
            return
        with self._lock:
            run = self._get_run_locked(run_id)
            if run is None:
                return
            run.progress_messages.append(cleaned)
            if len(run.progress_messages) > 25:
                del run.progress_messages[:-25]
            record = self._get_watchlist_locked(watchlist_id)
            if record is not None:
                record.updated_at = _utc_isoformat()

    def _load_database(self) -> WatchlistDatabase:
        if not self.storage_path.exists():
            return WatchlistDatabase()
        try:
            return WatchlistDatabase.model_validate_json(self.storage_path.read_text())
        except Exception:
            return WatchlistDatabase()

    def _persist_locked(self) -> None:
        parent_path = self.storage_path.parent
        existed_before = parent_path.exists()
        parent_path.mkdir(parents=True, exist_ok=True)
        if not existed_before:
            try:
                os.chmod(parent_path, 0o700)
            except OSError:
                pass

        temp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        payload = self._db.model_dump_json(indent=2, exclude_none=True) + "\n"
        fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_path, self.storage_path)
            try:
                os.chmod(self.storage_path, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _sorted_watchlists_locked(self) -> list[WatchlistRecord]:
        return sorted(
            self._db.watchlists,
            key=lambda item: (
                item.next_run_at or "",
                item.updated_at,
            ),
        )

    def _watchlist_snapshot_locked(
        self,
        record: WatchlistRecord,
        *,
        include_full_history: bool = False,
    ) -> dict:
        runs = [
            run
            for run in self._db.runs
            if run.watchlist_id == record.id
        ]
        runs.sort(key=lambda item: item.started_at, reverse=True)
        alerts = [
            alert
            for alert in self._db.alerts
            if alert.watchlist_id == record.id
        ]
        alerts.sort(key=lambda item: item.created_at, reverse=True)

        run_limit = len(runs) if include_full_history else 3
        alert_limit = len(alerts) if include_full_history else 3
        data = record.model_dump(exclude_none=True)
        data.update(
            {
                "is_running": record.id in self._active_watchlists,
                "recent_runs": [run.model_dump(exclude_none=True) for run in runs[:run_limit]],
                "recent_alerts": [alert.model_dump(exclude_none=True) for alert in alerts[:alert_limit]],
            }
        )
        return data

    def _latest_successful_run_locked(
        self,
        watchlist_id: str,
        *,
        exclude_run_id: Optional[str] = None,
    ) -> Optional[WatchlistRun]:
        candidates = [
            run
            for run in self._db.runs
            if run.watchlist_id == watchlist_id
            and run.state == "succeeded"
            and run.id != exclude_run_id
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.completed_at or item.started_at, reverse=True)
        return candidates[0]

    def _get_watchlist_locked(self, watchlist_id: str) -> Optional[WatchlistRecord]:
        for record in self._db.watchlists:
            if record.id == watchlist_id:
                return record
        return None

    def _get_run_locked(self, run_id: str) -> Optional[WatchlistRun]:
        for run in self._db.runs:
            if run.id == run_id:
                return run
        return None

    def _trim_runs_locked(self, watchlist_id: str) -> None:
        watchlist_runs = [
            run
            for run in self._db.runs
            if run.watchlist_id == watchlist_id
        ]
        if len(watchlist_runs) <= MAX_RUNS_PER_WATCHLIST:
            return

        watchlist_runs.sort(key=lambda item: item.started_at, reverse=True)
        keep_ids = {run.id for run in watchlist_runs[:MAX_RUNS_PER_WATCHLIST]}
        self._db.runs = [
            run
            for run in self._db.runs
            if run.watchlist_id != watchlist_id or run.id in keep_ids
        ]

    def _trim_alerts_locked(self) -> None:
        if len(self._db.alerts) <= MAX_ALERTS:
            return

        self._db.alerts.sort(key=lambda item: item.created_at, reverse=True)
        self._db.alerts = self._db.alerts[:MAX_ALERTS]

    def _recover_incomplete_runs_locked(self) -> bool:
        changed = False
        recovery_time = _utc_isoformat()

        for run in self._db.runs:
            if run.state != "running":
                continue
            changed = True
            run.state = "failed"
            run.completed_at = recovery_time
            run.error = "Interrupted by process restart."
            run.changes = [
                WatchlistChange(
                    change_type="run_failed",
                    summary="A previous watchlist run was interrupted by process restart.",
                )
            ]
            run.alert_summaries = ["Previous watchlist run interrupted by process restart."]

        for watchlist in self._db.watchlists:
            if watchlist.last_run_state != "running":
                continue
            changed = True
            watchlist.last_run_state = "failed"
            watchlist.updated_at = recovery_time
            watchlist.last_alert_summary = "Previous watchlist run interrupted by process restart."
            watchlist.next_run_at = _future_iso(minutes=watchlist.schedule_minutes) if watchlist.enabled else None
            self._db.alerts.append(
                WatchlistAlert(
                    id=uuid.uuid4().hex[:12],
                    watchlist_id=watchlist.id,
                    watchlist_name=watchlist.name,
                    run_id=watchlist.last_run_id or "recovery",
                    created_at=recovery_time,
                    severity="warning",
                    event_type="run_interrupted",
                    title="Watchlist recovered after restart",
                    summary="A previous watchlist run was interrupted before completion.",
                )
            )

        if changed:
            self._trim_alerts_locked()
        return changed


def _build_run_changes(
    previous_run: Optional[WatchlistRun],
    current_products: list[TrackedProduct],
    decision: PurchaseDecision,
    *,
    target_price: Optional[float],
) -> list[WatchlistChange]:
    changes: list[WatchlistChange] = []
    if not current_products:
        return changes

    current_winner = current_products[0]
    previous_products = previous_run.tracked_products if previous_run is not None else []
    previous_winner = previous_products[0] if previous_products else None

    if previous_winner is not None and previous_winner.identity_key != current_winner.identity_key:
        changes.append(
            WatchlistChange(
                change_type="winner_changed",
                summary=(
                    f"Recommended winner changed from {previous_winner.product_name} to "
                    f"{current_winner.product_name}."
                ),
                product_name=current_winner.product_name,
                product_key=current_winner.identity_key,
                previous_value=previous_winner.product_name,
                current_value=current_winner.product_name,
            )
        )

    previous_match = _match_previous_product(current_winner, previous_products)
    if previous_match is not None:
        if current_winner.price is not None and previous_match.price is not None:
            delta = round(current_winner.price - previous_match.price, 2)
            if delta < 0:
                changes.append(
                    WatchlistChange(
                        change_type="price_drop",
                        summary=(
                            f"{current_winner.product_name} dropped by {abs(delta):.2f} "
                            f"{current_winner.currency or decision.request.currency} since the last run."
                        ),
                        product_name=current_winner.product_name,
                        product_key=current_winner.identity_key,
                        previous_value=str(previous_match.price),
                        current_value=str(current_winner.price),
                    )
                )
            elif delta > 0:
                changes.append(
                    WatchlistChange(
                        change_type="price_increase",
                        summary=(
                            f"{current_winner.product_name} increased by {delta:.2f} "
                            f"{current_winner.currency or decision.request.currency} since the last run."
                        ),
                        product_name=current_winner.product_name,
                        product_key=current_winner.identity_key,
                        previous_value=str(previous_match.price),
                        current_value=str(current_winner.price),
                    )
                )

        previous_availability = (previous_match.availability or "Unknown").casefold()
        current_availability = (current_winner.availability or "Unknown").casefold()
        if previous_availability != current_availability:
            change_type = "availability_changed"
            summary = (
                f"Availability changed for {current_winner.product_name}: "
                f"{previous_match.availability or 'Unknown'} -> {current_winner.availability or 'Unknown'}."
            )
            if "out of stock" in previous_availability and "out of stock" not in current_availability:
                change_type = "back_in_stock"
                summary = f"{current_winner.product_name} appears to be back in stock."
            changes.append(
                WatchlistChange(
                    change_type=change_type,
                    summary=summary,
                    product_name=current_winner.product_name,
                    product_key=current_winner.identity_key,
                    previous_value=previous_match.availability,
                    current_value=current_winner.availability,
                )
            )

        if previous_match.rank != current_winner.rank:
            direction = "improved" if current_winner.rank < previous_match.rank else "fell"
            changes.append(
                WatchlistChange(
                    change_type="rank_changed",
                    summary=(
                        f"{current_winner.product_name} {direction} from rank "
                        f"{previous_match.rank} to rank {current_winner.rank}."
                    ),
                    product_name=current_winner.product_name,
                    product_key=current_winner.identity_key,
                    previous_value=str(previous_match.rank),
                    current_value=str(current_winner.rank),
                )
            )
    elif previous_run is not None:
        changes.append(
            WatchlistChange(
                change_type="new_candidate",
                summary=f"{current_winner.product_name} is a new candidate leading the watchlist.",
                product_name=current_winner.product_name,
                product_key=current_winner.identity_key,
            )
        )

    if target_price is not None and current_winner.price is not None and current_winner.price <= target_price:
        changes.append(
            WatchlistChange(
                change_type="target_price_hit",
                summary=(
                    f"{current_winner.product_name} reached the target price threshold at "
                    f"{current_winner.price:.2f} {current_winner.currency or decision.request.currency}."
                ),
                product_name=current_winner.product_name,
                product_key=current_winner.identity_key,
                current_value=str(current_winner.price),
            )
        )

    for product in current_products[1:]:
        previous_product = _match_previous_product(product, previous_products)
        if previous_product is None and previous_run is not None and product.rank <= 2:
            changes.append(
                WatchlistChange(
                    change_type="new_candidate",
                    summary=f"New high-ranking candidate detected: {product.product_name}.",
                    product_name=product.product_name,
                    product_key=product.identity_key,
                )
            )

    return _deduplicate_changes(changes)


def _build_alerts(
    watchlist: WatchlistRecord,
    run_id: str,
    changes: list[WatchlistChange],
) -> list[WatchlistAlert]:
    alerts: list[WatchlistAlert] = []
    for change in changes:
        severity = _change_severity(change.change_type)
        if severity is None:
            continue
        alerts.append(
            WatchlistAlert(
                id=uuid.uuid4().hex[:12],
                watchlist_id=watchlist.id,
                watchlist_name=watchlist.name,
                run_id=run_id,
                created_at=_utc_isoformat(),
                severity=severity,
                event_type=change.change_type,
                title=_change_title(change.change_type),
                summary=change.summary,
            )
        )
    return alerts


def _tracked_products_from_decision(decision: PurchaseDecision) -> list[TrackedProduct]:
    ranked_options = [decision.recommended_option] + list(decision.alternatives)
    comparison_lookup = {
        row.rank: row for row in decision.comparison_rows
    }
    tracked: list[TrackedProduct] = []

    for index, ranked in enumerate(ranked_options, start=1):
        row = comparison_lookup.get(index)
        product = ranked.product
        tracked.append(
            TrackedProduct(
                identity_key=_product_identity_key(
                    product.product_url,
                    product.name,
                    product.retailer,
                ),
                product_name=product.name,
                retailer=product.retailer,
                product_url=product.product_url,
                rank=index,
                price=row.price if row is not None else product.price,
                currency=row.currency if row is not None else product.currency,
                availability=row.availability if row is not None else product.availability,
                total_score=ranked.total_score,
                verification_status=row.verification_status if row is not None else "not_run",
            )
        )

    return tracked


def _match_previous_product(
    current_product: TrackedProduct,
    previous_products: list[TrackedProduct],
) -> Optional[TrackedProduct]:
    previous_lookup = {item.identity_key: item for item in previous_products}
    if current_product.identity_key in previous_lookup:
        return previous_lookup[current_product.identity_key]

    current_models = _extract_model_tokens(current_product.product_name)
    current_name_tokens = _normalized_name_tokens(current_product.product_name)
    current_retailer = _normalized_retailer(current_product.retailer)

    best_match = None
    best_score = 0.0
    for previous in previous_products:
        score = 0.0
        if _normalized_retailer(previous.retailer) == current_retailer:
            score += 0.3

        previous_models = _extract_model_tokens(previous.product_name)
        if current_models and previous_models:
            overlap = len(current_models & previous_models) / len(current_models | previous_models)
            score += overlap * 0.5

        previous_name_tokens = _normalized_name_tokens(previous.product_name)
        if current_name_tokens and previous_name_tokens:
            overlap = len(current_name_tokens & previous_name_tokens) / len(current_name_tokens | previous_name_tokens)
            score += overlap * 0.4

        if score > best_score:
            best_match = previous
            best_score = score

    return best_match if best_score >= 0.55 else None


def _product_identity_key(
    product_url: Optional[str],
    product_name: str,
    retailer: str,
) -> str:
    if product_url:
        parsed = urlparse(product_url)
        host = parsed.netloc.casefold()
        if host.startswith("www."):
            host = host[4:]
        path = parsed.path.rstrip("/")
        if host and path:
            return f"url::{host}{path}"

    retailer_key = _normalized_retailer(retailer)
    model_tokens = _extract_model_tokens(product_name)
    if model_tokens:
        return f"model::{retailer_key}::{'-'.join(sorted(model_tokens))}"
    return f"name::{retailer_key}::{'-'.join(sorted(_normalized_name_tokens(product_name)))}"


def _extract_model_tokens(product_name: str) -> set[str]:
    return {token for token in MODEL_TOKEN_RE.findall(product_name.upper()) if any(char.isdigit() for char in token)}


def _normalized_name_tokens(value: str) -> set[str]:
    raw_tokens = re.findall(r"[A-Za-z0-9]+", value.casefold())
    return {
        token
        for token in raw_tokens
        if len(token) >= 3 and token not in GENERIC_NAME_TOKENS
    }


def _normalized_retailer(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _deduplicate_changes(changes: list[WatchlistChange]) -> list[WatchlistChange]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[WatchlistChange] = []
    for change in changes:
        key = (change.change_type, change.product_key or "", change.summary)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(change)
    return deduped


def _change_severity(change_type: str) -> Optional[str]:
    if change_type in {"price_drop", "target_price_hit", "back_in_stock"}:
        return "success"
    if change_type in {"winner_changed", "new_candidate"}:
        return "info"
    if change_type == "run_failed":
        return "warning"
    return None


def _change_title(change_type: str) -> str:
    return {
        "price_drop": "Price drop",
        "target_price_hit": "Target price hit",
        "back_in_stock": "Back in stock",
        "winner_changed": "Recommendation changed",
        "new_candidate": "New strong candidate",
        "run_failed": "Watchlist run failed",
    }.get(change_type, "Watchlist update")


def _default_service_factory() -> "ShoppingAgentService":
    from agentic_shopping_agent.service import ShoppingAgentService

    return ShoppingAgentService()


def _utc_isoformat() -> str:
    return datetime.now(timezone.utc).isoformat()


def _future_iso(*, minutes: int) -> str:
    return _iso_from_ts(time.time() + (minutes * 60))


def _iso_from_ts(value: float) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()


def _parse_iso(value: str) -> float:
    return datetime.fromisoformat(value).timestamp()


def _sanitize_text(value: str, preserve_newlines: bool = False) -> str:
    sanitized = []
    for char in value:
        codepoint = ord(char)
        if char == "\r":
            continue
        if char == "\n":
            sanitized.append("\n" if preserve_newlines else " ")
            continue
        if char == "\t":
            sanitized.append(" ")
            continue
        if codepoint < 32 or 127 <= codepoint <= 159:
            continue
        sanitized.append(char)
    return "".join(sanitized)
