import asyncio

from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
)
from agentic_shopping_agent.config import Settings
from agentic_shopping_agent.service import DEFAULT_SAFE_DOMAINS, ShoppingAgentService


class _FakeRunResult:
    def __init__(self, output):
        self.output = output


class _FakeSessions:
    def __init__(self) -> None:
        self.create_calls = []
        self.stop_calls = []

    async def create(self, **kwargs):
        self.create_calls.append(kwargs)
        return type("Session", (), {"id": "session-123", "live_url": "https://live.example/session-123"})()

    async def stop(self, session_id: str) -> None:
        self.stop_calls.append(session_id)


class _FakeBrowserUse:
    last_instance = None

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.sessions = _FakeSessions()
        self.run_calls = []
        self.next_output = ShoppingResearch(
            search_summary="Found strong options across trusted stores.",
            options=[
                ProductOption(
                    name="Safe Option",
                    retailer="Trusted Store",
                    product_url="https://example.com/safe",
                    price=199,
                    currency="USD",
                    availability="In Stock",
                    rating=4.5,
                    review_count=250,
                    summary="Well reviewed and in stock.",
                    criterion_assessments=[
                        CriterionAssessment(
                            criterion_name="battery life",
                            score=9,
                            evidence="Strong battery life from review coverage.",
                        )
                    ],
                    source_urls=["https://example.com/safe", "https://reviews.example.com/safe"],
                ),
                ProductOption(
                    name="Runner Up",
                    retailer="Trusted Store",
                    product_url="https://example.com/runner-up",
                    price=249,
                    currency="USD",
                    availability="In Stock",
                    rating=4.3,
                    review_count=150,
                    summary="More expensive but still solid.",
                    criterion_assessments=[
                        CriterionAssessment(
                            criterion_name="battery life",
                            score=8,
                            evidence="Good battery life.",
                        )
                    ],
                    source_urls=["https://example.com/runner-up", "https://reviews.example.com/runner-up"],
                ),
            ],
        )
        _FakeBrowserUse.last_instance = self

    async def run(self, task: str, **kwargs):
        self.run_calls.append({"task": task, **kwargs})
        return _FakeRunResult(self.next_output)


def test_effective_allowed_domains_defaults_to_safe_allowlist() -> None:
    request = ShoppingRequest(query="desk lamp")

    assert ShoppingAgentService._effective_allowed_domains(request) == list(DEFAULT_SAFE_DOMAINS)


def test_effective_allowed_domains_respects_open_web_and_custom_domains() -> None:
    unrestricted_request = ShoppingRequest(query="desk lamp", allow_open_web=True)
    custom_request = ShoppingRequest(query="desk lamp", allowed_domains=["rei.com"])

    assert ShoppingAgentService._effective_allowed_domains(unrestricted_request) == []
    assert ShoppingAgentService._effective_allowed_domains(custom_request) == ["rei.com"]


def test_proxy_country_does_not_create_live_session_without_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.setattr("agentic_shopping_agent.service.AsyncBrowserUse", _FakeBrowserUse)
    service = ShoppingAgentService(Settings(browser_use_api_key="test-key"))
    request = ShoppingRequest(
        query="portable charger",
        criteria=[ShoppingCriterion(name="battery life", kind="preference", weight=1.0)],
        proxy_country_code="gb",
    )

    decision = asyncio.run(service.research_and_recommend(request))
    fake_client = _FakeBrowserUse.last_instance

    assert fake_client is not None
    assert fake_client.sessions.create_calls == []
    assert fake_client.run_calls[0]["proxy_country_code"] == "gb"
    assert fake_client.run_calls[0]["allowed_domains"] == list(DEFAULT_SAFE_DOMAINS)
    assert decision.live_url is None


def test_show_live_url_creates_session_and_returns_live_url(monkeypatch) -> None:
    monkeypatch.setattr("agentic_shopping_agent.service.AsyncBrowserUse", _FakeBrowserUse)
    service = ShoppingAgentService(Settings(browser_use_api_key="test-key"))
    request = ShoppingRequest(
        query="portable charger",
        criteria=[ShoppingCriterion(name="battery life", kind="preference", weight=1.0)],
    )

    decision = asyncio.run(service.research_and_recommend(request, show_live_url=True))
    fake_client = _FakeBrowserUse.last_instance

    assert fake_client is not None
    assert len(fake_client.sessions.create_calls) == 1
    assert fake_client.run_calls[0]["session_id"] == "session-123"
    assert "proxy_country_code" not in fake_client.run_calls[0]
    assert decision.live_url == "https://live.example/session-123"
