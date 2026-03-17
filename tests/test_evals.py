from __future__ import annotations

import asyncio

from agentic_shopping_agent.evals import (
    EvalRunner,
    EvalScenario,
    ScenarioExpectations,
    evaluate_decision,
    filter_scenarios,
    load_scenarios,
    render_markdown_report,
    write_report_files,
)
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


def test_load_scenarios_returns_builtin_catalog() -> None:
    scenarios = load_scenarios()

    assert len(scenarios) >= 10
    assert any(scenario.id == "travel-headphones" for scenario in scenarios)
    assert any(scenario.id == "hiking-backpack" for scenario in scenarios)


def test_filter_scenarios_respects_ids_and_max_count() -> None:
    scenarios = load_scenarios()

    filtered = filter_scenarios(
        scenarios,
        scenario_ids=["travel-headphones", "portable-charger", "missing-id"],
        max_scenarios=1,
    )

    assert len(filtered) == 1
    assert filtered[0].id == "travel-headphones"


def test_evaluate_decision_uses_verified_price_and_allowed_domains() -> None:
    scenario = EvalScenario(
        id="custom-hiking-pack",
        title="Restricted hiking pack scenario",
        request=ShoppingRequest(
            query="hiking backpack",
            budget=180,
            criteria=[
                ShoppingCriterion(name="comfortable fit", kind="must_have", weight=1.5),
                ShoppingCriterion(name="hydration compatibility", kind="preference", weight=1.0),
            ],
            allowed_domains=["rei.com", "backcountry.com"],
        ),
        expectations=ScenarioExpectations(
            max_recommended_price=180,
            min_recommended_source_count=2,
            required_verification_status="verified",
            required_criterion_names=["comfortable fit", "hydration compatibility"],
            require_recommended_url_in_allowed_domains=True,
            minimum_comparison_rows=2,
        ),
    )

    decision = _build_decision(
        request=scenario.request,
        recommended_url="https://www.rei.com/product/pack-1",
        recommended_price=175,
        verified_price=169,
        runner_up_url="https://www.backcountry.com/product/pack-2",
    )

    checks = evaluate_decision(scenario, decision)
    check_lookup = {check.name: check for check in checks}

    assert all(check.passed for check in checks)
    assert check_lookup["price_within_budget"].details == "Recommended price was 169.0 against a max of 180.0."
    assert check_lookup["allowed_domain_respected"].passed is True


def test_eval_runner_and_report_writer_capture_failures(tmp_path) -> None:
    scenario = EvalScenario(
        id="budget-failure",
        title="Fails when verified price exceeds budget",
        request=ShoppingRequest(
            query="desk lamp",
            budget=100,
            criteria=[ShoppingCriterion(name="brightness", kind="preference", weight=1.0)],
        ),
        expectations=ScenarioExpectations(
            max_recommended_price=100,
            required_verification_status="verified",
        ),
    )
    decision = _build_decision(
        request=scenario.request,
        recommended_url="https://example.com/lamp-1",
        recommended_price=95,
        verified_price=129,
        runner_up_url="https://example.com/lamp-2",
    )

    class _FakeProvider:
        async def get_decision(self, incoming_scenario: EvalScenario):
            assert incoming_scenario.id == "budget-failure"
            return decision

    report = asyncio.run(EvalRunner(_FakeProvider()).run([scenario]))
    report_paths = write_report_files(report, tmp_path)
    markdown_text = render_markdown_report(report)

    assert report.summary.total_scenarios == 1
    assert report.summary.failed_scenarios == 1
    assert report.summary.failure_reasons["price_within_budget"] == 1
    assert report_paths.json_path.exists()
    assert report_paths.markdown_path.exists()
    assert report_paths.latest_json_path.exists()
    assert report_paths.latest_markdown_path.exists()
    assert "price_within_budget" in markdown_text
    assert "budget-failure" in markdown_text


def _build_decision(
    *,
    request: ShoppingRequest,
    recommended_url: str,
    recommended_price: float,
    verified_price: float,
    runner_up_url: str,
):
    research = ShoppingResearch(
        search_summary="Compared several products with retailer and review coverage.",
        options=[
            ProductOption(
                name="Pack One",
                retailer="REI",
                product_url=recommended_url,
                price=recommended_price,
                currency="USD",
                availability="In Stock",
                rating=4.7,
                review_count=240,
                summary="Best overall fit.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name=request.criteria[0].name,
                        score=9,
                        evidence="Strong fit for the primary requirement.",
                    ),
                    CriterionAssessment(
                        criterion_name=request.criteria[-1].name,
                        score=8,
                        evidence="Solid secondary fit.",
                    ),
                ],
                source_urls=[recommended_url, "https://reviews.example.com/pack-one"],
            ),
            ProductOption(
                name="Pack Two",
                retailer="Backcountry",
                product_url=runner_up_url,
                price=recommended_price + 10,
                currency="USD",
                availability="In Stock",
                rating=4.5,
                review_count=180,
                summary="Solid runner-up.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name=request.criteria[0].name,
                        score=8,
                        evidence="Good primary fit.",
                    ),
                    CriterionAssessment(
                        criterion_name=request.criteria[-1].name,
                        score=8,
                        evidence="Good secondary fit.",
                    ),
                ],
                source_urls=[runner_up_url, "https://reviews.example.com/pack-two"],
            ),
        ],
        notable_tradeoffs=["The lighter option has slightly less structure."],
    )
    verification = ProductVerification(
        product_name="Pack One",
        product_url=recommended_url,
        retailer="REI",
        product_still_matches=True,
        verified_price=verified_price,
        verified_currency="USD",
        verified_availability="In Stock",
        price_matches_original=(verified_price == recommended_price),
        availability_matches_original=True,
        notes="Current listing still matches the researched product.",
        source_urls=[recommended_url],
    )
    verification_report = VerificationReport(
        summary="Top candidate still matches the live listing.",
        checks=[verification],
    )

    ranked = rank_options(
        request,
        request.criteria,
        research,
        verifications={recommended_url.casefold(): verification},
    )
    return build_purchase_decision(
        request,
        research,
        ranked,
        verification_report=verification_report,
        missing_information=[],
    )
