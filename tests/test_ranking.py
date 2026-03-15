from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
)
from agentic_shopping_agent.ranking import build_purchase_decision, rank_options


def test_rank_options_prefers_budget_and_criteria_fit() -> None:
    request = ShoppingRequest(
        query="wireless headphones",
        budget=300,
        criteria=[
            ShoppingCriterion(name="sound quality", kind="preference", weight=1.0),
            ShoppingCriterion(name="active noise cancellation", kind="must_have", weight=1.5),
        ],
    )
    research = ShoppingResearch(
        search_summary="Compared two popular noise-cancelling headphones.",
        options=[
            ProductOption(
                name="Headphones A",
                retailer="Retailer A",
                product_url="https://example.com/a",
                price=249,
                currency="USD",
                availability="In Stock",
                rating=4.7,
                review_count=500,
                summary="Better balance of price and quality.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="sound quality",
                        score=9,
                        evidence="Review sources consistently praised the tuning.",
                    ),
                    CriterionAssessment(
                        criterion_name="active noise cancellation",
                        score=8,
                        evidence="ANC performance is strong for flights and commuting.",
                    ),
                ],
                source_urls=["https://example.com/a", "https://reviews.example.com/a"],
            ),
            ProductOption(
                name="Headphones B",
                retailer="Retailer B",
                product_url="https://example.com/b",
                price=379,
                currency="USD",
                availability="In Stock",
                rating=4.8,
                review_count=300,
                summary="Excellent quality but over budget.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="sound quality",
                        score=9,
                        evidence="Very strong audio quality.",
                    ),
                    CriterionAssessment(
                        criterion_name="active noise cancellation",
                        score=9,
                        evidence="Class-leading ANC.",
                    ),
                ],
                source_urls=["https://example.com/b", "https://reviews.example.com/b"],
            ),
        ],
    )

    ranked = rank_options(request, request.criteria, research)

    assert ranked[0].product.name == "Headphones A"
    decision = build_purchase_decision(request, research, ranked)
    assert "Headphones A" in decision.final_answer

