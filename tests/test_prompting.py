from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    RankedOption,
    ShoppingCriterion,
    ShoppingRequest,
)
from agentic_shopping_agent.prompting import (
    build_shopping_task,
    build_verification_task,
    ensure_effective_criteria,
)


def test_build_shopping_task_includes_key_instructions() -> None:
    request = ShoppingRequest(
        query="espresso machine",
        criteria=[ShoppingCriterion(name="easy cleaning", kind="must_have", weight=1.5)],
        budget=600,
        allowed_domains=["amazon.com", "bestbuy.com"],
    )

    prompt = build_shopping_task(request, ensure_effective_criteria(request.criteria))

    assert "espresso machine" in prompt
    assert "easy cleaning" in prompt
    assert "amazon.com, bestbuy.com" in prompt
    assert "Do not attempt checkout" in prompt


def test_build_verification_task_includes_candidate_context() -> None:
    request = ShoppingRequest(
        query="portable charger",
        criteria=[ShoppingCriterion(name="battery life", kind="preference", weight=1.0)],
    )
    ranked_options = [
        RankedOption(
            product=ProductOption(
                name="Charger A",
                retailer="Retailer A",
                product_url="https://example.com/a",
                price=99,
                currency="USD",
                availability="In Stock",
                summary="Solid charger.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="battery life",
                        score=8,
                        evidence="Good battery life.",
                    )
                ],
                source_urls=["https://example.com/a"],
            ),
            total_score=82.0,
            criterion_score=40.0,
            budget_score=12.0,
            quality_score=15.0,
            trust_score=10.0,
            verification_score=5.0,
        )
    ]

    prompt = build_verification_task(request, ranked_options)

    assert "portable charger" in prompt
    assert "Charger A" in prompt
    assert "https://example.com/a" in prompt
    assert "Open each exact product URL first" in prompt
