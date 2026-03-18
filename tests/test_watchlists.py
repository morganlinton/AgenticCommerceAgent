from __future__ import annotations

import os
import stat
import threading
import time

from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    ProductVerification,
    PurchaseDecision,
    RankedOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
    VerificationReport,
)
from agentic_shopping_agent.ranking import build_purchase_decision
from agentic_shopping_agent.watchlists import (
    MAX_WATCHLISTS,
    WatchlistDatabase,
    WatchlistLimitError,
    WatchlistManager,
    WatchlistRecord,
    WatchlistRun,
)


def test_watchlist_manager_persists_created_watchlist(tmp_path) -> None:
    manager = WatchlistManager(storage_path=tmp_path / "watchlists.json", service_factory=lambda: _FakeService([]))
    request = _build_request()

    snapshot = manager.create_watchlist(
        name="TV watch",
        request=request,
        request_payload={"query": request.query},
        schedule_minutes=180,
        target_price=999,
        enabled=False,
        run_immediately=False,
    )

    reloaded = WatchlistManager(storage_path=tmp_path / "watchlists.json", service_factory=lambda: _FakeService([]))
    dashboard = reloaded.list_watchlists_snapshot()

    assert snapshot["name"] == "TV watch"
    assert dashboard["watchlists"][0]["name"] == "TV watch"
    assert dashboard["watchlists"][0]["target_price"] == 999


def test_watchlist_manager_uses_restrictive_file_permissions(tmp_path) -> None:
    manager = WatchlistManager(storage_path=tmp_path / "watchlists.json", service_factory=lambda: _FakeService([]))
    request = _build_request()

    manager.create_watchlist(
        name="TV watch",
        request=request,
        request_payload={"query": request.query},
        schedule_minutes=180,
        target_price=999,
        enabled=False,
        run_immediately=False,
    )

    if os.name == "posix":
        mode = stat.S_IMODE((tmp_path / "watchlists.json").stat().st_mode)
        assert mode == 0o600


def test_watchlist_manager_generates_alerts_for_price_and_winner_changes(tmp_path) -> None:
    decisions = [
        _build_decision(
            winner_name="OLED A",
            winner_url="https://example.com/oled-a",
            winner_price=1199,
            winner_availability="Out of Stock",
            winner_score=92,
            runner_name="OLED B",
            runner_url="https://example.com/oled-b",
            runner_price=1149,
            runner_score=88,
        ),
        _build_decision(
            winner_name="OLED A",
            winner_url="https://example.com/oled-a",
            winner_price=899,
            winner_availability="In Stock",
            winner_score=92,
            runner_name="OLED B",
            runner_url="https://example.com/oled-b",
            runner_price=1099,
            runner_score=89,
        ),
        _build_decision(
            winner_name="OLED B",
            winner_url="https://example.com/oled-b",
            winner_price=849,
            winner_availability="In Stock",
            winner_score=95,
            runner_name="OLED A",
            runner_url="https://example.com/oled-a",
            runner_price=919,
            runner_score=90,
        ),
    ]

    manager = WatchlistManager(
        storage_path=tmp_path / "watchlists.json",
        service_factory=_SequentialServiceFactory(decisions),
    )
    watchlist = manager.create_watchlist(
        name="OLED tracker",
        request=_build_request(),
        request_payload={"query": "55-inch OLED TV"},
        schedule_minutes=60,
        target_price=900,
        enabled=False,
        run_immediately=False,
    )

    manager.trigger_run(watchlist["id"], trigger="manual")
    _wait_for_watchlist_state(manager, watchlist["id"], expected_state="succeeded")

    manager.trigger_run(watchlist["id"], trigger="manual")
    second_snapshot = _wait_for_watchlist_state(manager, watchlist["id"], expected_state="succeeded")
    second_changes = [change["change_type"] for change in second_snapshot["recent_runs"][0]["changes"]]

    manager.trigger_run(watchlist["id"], trigger="manual")
    third_snapshot = _wait_for_watchlist_state(manager, watchlist["id"], expected_state="succeeded")
    third_changes = [change["change_type"] for change in third_snapshot["recent_runs"][0]["changes"]]
    alerts = manager.list_alerts_snapshot()["alerts"]
    alert_titles = [alert["title"] for alert in alerts]

    assert "price_drop" in second_changes
    assert "back_in_stock" in second_changes
    assert "target_price_hit" in second_changes
    assert "winner_changed" in third_changes
    assert "Price drop" in alert_titles
    assert "Back in stock" in alert_titles
    assert "Target price hit" in alert_titles
    assert "Recommendation changed" in alert_titles


def test_watchlist_scheduler_runs_due_watchlist(tmp_path) -> None:
    manager = WatchlistManager(
        storage_path=tmp_path / "watchlists.json",
        service_factory=_SequentialServiceFactory(
            [
                _build_decision(
                    winner_name="Lamp A",
                    winner_url="https://example.com/lamp-a",
                    winner_price=89,
                    winner_availability="In Stock",
                    winner_score=90,
                    runner_name="Lamp B",
                    runner_url="https://example.com/lamp-b",
                    runner_price=99,
                    runner_score=85,
                )
            ]
        ),
        poll_interval_seconds=0.5,
    )
    manager.start()
    try:
        watchlist = manager.create_watchlist(
            name="Desk lamp tracker",
            request=_build_request(query="desk lamp"),
            request_payload={"query": "desk lamp"},
            schedule_minutes=60,
            target_price=None,
            enabled=True,
            run_immediately=False,
        )

        snapshot = _wait_for_watchlist_state(manager, watchlist["id"], expected_state="succeeded", timeout=3)
        assert snapshot["recent_runs"][0]["trigger"] == "scheduled"
        assert snapshot["last_recommended_product"] == "Lamp A"
    finally:
        manager.stop()


def test_watchlist_manager_recovers_interrupted_runs_on_restart(tmp_path) -> None:
    request = _build_request()
    db = WatchlistDatabase(
        watchlists=[
            WatchlistRecord(
                id="watch-1",
                name="Recovered watchlist",
                request=request,
                request_payload={"query": request.query},
                schedule_minutes=60,
                target_price=None,
                enabled=True,
                created_at="2026-03-17T00:00:00+00:00",
                updated_at="2026-03-17T00:00:00+00:00",
                next_run_at=None,
                last_run_at="2026-03-17T00:00:00+00:00",
                last_run_state="running",
                last_run_id="run-1",
            )
        ],
        runs=[
            WatchlistRun(
                id="run-1",
                watchlist_id="watch-1",
                trigger="scheduled",
                state="running",
                started_at="2026-03-17T00:00:00+00:00",
                progress_messages=["Preparing shopping brief"],
            )
        ],
        alerts=[],
    )
    path = tmp_path / "watchlists.json"
    path.write_text(db.model_dump_json(indent=2, exclude_none=True) + "\n")

    recovered = WatchlistManager(storage_path=path, service_factory=lambda: _FakeService([]))
    snapshot = recovered.get_watchlist_snapshot("watch-1")
    alerts = recovered.list_alerts_snapshot()["alerts"]

    assert snapshot is not None
    assert snapshot["last_run_state"] == "failed"
    assert snapshot["recent_runs"][0]["state"] == "failed"
    assert snapshot["next_run_at"] is not None
    assert alerts[0]["title"] == "Watchlist recovered after restart"


def test_watchlist_manager_enforces_watchlist_limit(tmp_path) -> None:
    manager = WatchlistManager(storage_path=tmp_path / "watchlists.json", service_factory=lambda: _FakeService([]))
    request = _build_request()

    for index in range(MAX_WATCHLISTS):
        manager.create_watchlist(
            name=f"Watch {index}",
            request=request,
            request_payload={"query": request.query},
            schedule_minutes=180,
            target_price=None,
            enabled=False,
            run_immediately=False,
        )

    try:
        manager.create_watchlist(
            name="Overflow",
            request=request,
            request_payload={"query": request.query},
            schedule_minutes=180,
            target_price=None,
            enabled=False,
            run_immediately=False,
        )
    except WatchlistLimitError:
        return
    raise AssertionError("Expected WatchlistLimitError when exceeding the watchlist cap.")


class _FakeService:
    def __init__(self, decisions: list[PurchaseDecision]) -> None:
        self.decisions = decisions

    async def research_and_recommend(self, request, status_callback=None, **kwargs):
        if status_callback is not None:
            status_callback("Preparing shopping brief")
        if not self.decisions:
            raise RuntimeError("No fake decisions configured")
        return self.decisions.pop(0)


class _SequentialServiceFactory:
    def __init__(self, decisions: list[PurchaseDecision]) -> None:
        self._decisions = list(decisions)
        self._lock = threading.Lock()

    def __call__(self):
        factory = self

        class _Service:
            async def research_and_recommend(self, request, status_callback=None, **kwargs):
                if status_callback is not None:
                    status_callback("Preparing shopping brief")
                    status_callback("Finalizing recommendation")
                with factory._lock:
                    if not factory._decisions:
                        raise RuntimeError("No fake decisions left for watchlist test")
                    return factory._decisions.pop(0)

        return _Service()


def _wait_for_watchlist_state(
    manager: WatchlistManager,
    watchlist_id: str,
    *,
    expected_state: str,
    timeout: float = 2.0,
) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        snapshot = manager.get_watchlist_snapshot(watchlist_id)
        if snapshot is None:
            raise AssertionError("Watchlist disappeared during test.")
        recent_runs = snapshot.get("recent_runs", [])
        if recent_runs and recent_runs[0]["state"] == expected_state and not snapshot["is_running"]:
            return snapshot
        time.sleep(0.02)
    raise AssertionError("Watchlist did not reach the expected state in time.")


def _build_request(query: str = "55-inch OLED TV") -> ShoppingRequest:
    return ShoppingRequest(
        query=query,
        budget=1300,
        currency="USD",
        location="United States",
        criteria=[
            ShoppingCriterion(name="picture quality", kind="must_have", weight=1.5),
        ],
    )


def _build_decision(
    *,
    winner_name: str,
    winner_url: str,
    winner_price: float,
    winner_availability: str,
    winner_score: float,
    runner_name: str,
    runner_url: str,
    runner_price: float,
    runner_score: float,
) -> PurchaseDecision:
    request = _build_request()
    winner = ProductOption(
        name=winner_name,
        retailer="Retailer One",
        product_url=winner_url,
        price=winner_price,
        currency="USD",
        availability=winner_availability,
        rating=4.8,
        review_count=420,
        summary=f"{winner_name} is the current top pick.",
        criterion_assessments=[
            CriterionAssessment(
                criterion_name="picture quality",
                score=9,
                evidence="Strong review consensus.",
            )
        ],
        source_urls=[winner_url, "https://reviews.example.com/" + winner_name.casefold().replace(" ", "-")],
    )
    runner = ProductOption(
        name=runner_name,
        retailer="Retailer Two",
        product_url=runner_url,
        price=runner_price,
        currency="USD",
        availability="In Stock",
        rating=4.5,
        review_count=300,
        summary=f"{runner_name} is the runner-up.",
        criterion_assessments=[
            CriterionAssessment(
                criterion_name="picture quality",
                score=8,
                evidence="Still strong overall.",
            )
        ],
        source_urls=[runner_url, "https://reviews.example.com/" + runner_name.casefold().replace(" ", "-")],
    )
    winner_verification = ProductVerification(
        product_name=winner_name,
        product_url=winner_url,
        retailer="Retailer One",
        product_still_matches=True,
        verified_price=winner_price,
        verified_currency="USD",
        verified_availability=winner_availability,
        price_matches_original=True,
        availability_matches_original=True,
        notes="Winner listing still matches.",
        source_urls=[winner_url],
    )
    runner_verification = ProductVerification(
        product_name=runner_name,
        product_url=runner_url,
        retailer="Retailer Two",
        product_still_matches=True,
        verified_price=runner_price,
        verified_currency="USD",
        verified_availability="In Stock",
        price_matches_original=True,
        availability_matches_original=True,
        notes="Runner-up listing still matches.",
        source_urls=[runner_url],
    )
    ranked = [
        RankedOption(
            product=winner,
            total_score=winner_score,
            criterion_score=44.0,
            budget_score=15.0,
            quality_score=15.0,
            trust_score=10.0,
            verification_score=10.0,
            rationale=["strong fit on picture quality"],
            verification=winner_verification,
        ),
        RankedOption(
            product=runner,
            total_score=runner_score,
            criterion_score=40.0,
            budget_score=12.0,
            quality_score=14.0,
            trust_score=10.0,
            verification_score=10.0,
            rationale=["solid alternative"],
            verification=runner_verification,
        ),
    ]
    research = ShoppingResearch(
        search_summary="Tracked the strongest currently purchasable OLED options.",
        options=[winner, runner],
        notable_tradeoffs=["The cheapest option gives up some brightness."],
        missing_information=[],
    )
    verification_report = VerificationReport(
        summary="Top candidates were re-checked against live listings.",
        checks=[winner_verification, runner_verification],
    )
    return build_purchase_decision(
        request,
        research,
        ranked,
        verification_report=verification_report,
        missing_information=[],
    )
