from __future__ import annotations

import json
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    ProductVerification,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
    VerificationReport,
)
from agentic_shopping_agent.ranking import build_purchase_decision, rank_options
from agentic_shopping_agent.webapp import (
    MAX_REQUEST_BYTES,
    ShoppingJobManager,
    ShoppingWebAppServer,
    WebShoppingRequestPayload,
    _validate_bind_host,
)


def test_web_request_payload_builds_shopping_request() -> None:
    payload = WebShoppingRequestPayload.model_validate(
        {
            "query": " wireless headphones ",
            "budget": "$300",
            "currency": "usd",
            "preferences": "sound quality, battery life",
            "must_haves": ["active noise cancellation"],
            "avoids": "refurbished\nused",
            "allowed_domains": "https://www.amazon.com/path, bestbuy.com",
        }
    )

    request = payload.to_shopping_request()

    assert request.query == "wireless headphones"
    assert request.budget == 300.0
    assert request.currency == "USD"
    assert request.allowed_domains == ["amazon.com", "bestbuy.com"]
    assert [criterion.kind for criterion in request.criteria] == [
        "preference",
        "preference",
        "must_have",
        "avoid",
        "avoid",
    ]


def test_job_manager_completes_and_returns_result() -> None:
    decision = _build_decision()

    class _FakeService:
        async def research_and_recommend(
            self,
            request: ShoppingRequest,
            show_live_url: bool = False,
            keep_session: bool = False,
            status_callback=None,
        ):
            if status_callback is not None:
                status_callback("Preparing shopping brief")
                status_callback("Finalizing recommendation")
            return decision

    manager = ShoppingJobManager(service_factory=lambda: _FakeService())
    job_id = manager.start_job(
        WebShoppingRequestPayload(
            query="desk lamp",
            preferences=["brightness"],
        )
    )

    snapshot = _wait_for_terminal_state(manager, job_id)

    assert snapshot["state"] == "succeeded"
    assert snapshot["result"]["final_answer"] == decision.final_answer
    assert any(item["message"] == "Preparing shopping brief" for item in snapshot["progress_messages"])
    assert snapshot["report_text"] is not None


def test_job_manager_captures_failure() -> None:
    class _FailingService:
        async def research_and_recommend(
            self,
            request: ShoppingRequest,
            show_live_url: bool = False,
            keep_session: bool = False,
            status_callback=None,
        ):
            if status_callback is not None:
                status_callback("Preparing shopping brief")
            raise RuntimeError("browser session failed")

    manager = ShoppingJobManager(service_factory=lambda: _FailingService())
    job_id = manager.start_job(WebShoppingRequestPayload(query="desk lamp"))

    snapshot = _wait_for_terminal_state(manager, job_id)

    assert snapshot["state"] == "failed"
    assert "browser session failed" in snapshot["error"]


def test_web_server_health_endpoint(tmp_path) -> None:
    server = ShoppingWebAppServer(
        host="127.0.0.1",
        port=0,
        job_manager=ShoppingJobManager(),
        storage_path=tmp_path / "watchlists.json",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen(f"{server.server_url}/api/health", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload == {"status": "ok"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_validate_bind_host_rejects_non_loopback_without_explicit_opt_in() -> None:
    try:
        _validate_bind_host("0.0.0.0", unsafe_listen=False)
    except ValueError:
        return
    raise AssertionError("Expected non-loopback bind to be rejected without explicit opt-in.")


def test_web_server_rejects_oversized_request_body(tmp_path) -> None:
    server = ShoppingWebAppServer(
        host="127.0.0.1",
        port=0,
        job_manager=ShoppingJobManager(),
        storage_path=tmp_path / "watchlists.json",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        payload = json.dumps({"query": "desk lamp", "notes": "x" * MAX_REQUEST_BYTES}).encode("utf-8")
        request = Request(
            f"{server.server_url}/api/watchlists",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=2)
        except HTTPError as exc:
            assert exc.code == 413
            return
        raise AssertionError("Expected oversized request to be rejected.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def _wait_for_terminal_state(manager: ShoppingJobManager, job_id: str) -> dict:
    deadline = time.time() + 3
    while time.time() < deadline:
        snapshot = manager.get_snapshot(job_id)
        if snapshot is not None and snapshot["state"] in {"succeeded", "failed"}:
            return snapshot
        time.sleep(0.02)
    raise AssertionError("Job did not finish in time.")


def _build_decision():
    request = ShoppingRequest(
        query="desk lamp",
        budget=100,
        criteria=[ShoppingCriterion(name="brightness", kind="preference", weight=1.0)],
    )
    research = ShoppingResearch(
        search_summary="Compared several desk lamps.",
        options=[
            ProductOption(
                name="Lamp One",
                retailer="Store A",
                product_url="https://example.com/lamp-one",
                price=79,
                currency="USD",
                availability="In Stock",
                rating=4.6,
                review_count=200,
                summary="Strong overall option.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="brightness",
                        score=9,
                        evidence="Very bright for a desk setup.",
                    )
                ],
                source_urls=["https://example.com/lamp-one", "https://reviews.example.com/lamp-one"],
            ),
            ProductOption(
                name="Lamp Two",
                retailer="Store B",
                product_url="https://example.com/lamp-two",
                price=89,
                currency="USD",
                availability="In Stock",
                rating=4.4,
                review_count=140,
                summary="Good runner-up.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="brightness",
                        score=8,
                        evidence="Still bright, but slightly weaker.",
                    )
                ],
                source_urls=["https://example.com/lamp-two", "https://reviews.example.com/lamp-two"],
            ),
        ],
        notable_tradeoffs=["Lamp One has a wider base than the runner-up."],
    )
    verification = ProductVerification(
        product_name="Lamp One",
        product_url="https://example.com/lamp-one",
        retailer="Store A",
        product_still_matches=True,
        verified_price=74,
        verified_currency="USD",
        verified_availability="In Stock",
        price_matches_original=False,
        availability_matches_original=True,
        notes="Price dropped since the initial research.",
        source_urls=["https://example.com/lamp-one"],
    )

    ranked = rank_options(
        request,
        request.criteria,
        research,
        verifications={"https://example.com/lamp-one": verification},
    )
    return build_purchase_decision(
        request,
        research,
        ranked,
        verification_report=VerificationReport(
            summary="Winner still matches the live listing.",
            checks=[verification],
        ),
        missing_information=[],
    )
