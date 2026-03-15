from agentic_shopping_agent.models import (
    CriterionAssessment,
    ProductOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
)
from agentic_shopping_agent.ranking import build_purchase_decision, rank_options, render_text_report


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


def test_render_text_report_strips_terminal_control_sequences() -> None:
    request = ShoppingRequest(query="monitor", criteria=[ShoppingCriterion(name="image quality", kind="preference", weight=1.0)])
    research = ShoppingResearch(
        search_summary="Compared monitors \x1b[31mwith review coverage.",
        options=[
            ProductOption(
                name="Display\x1b[31m One",
                retailer="Retailer\r\nA",
                product_url="https://example.com/\x1b[31mmonitor",
                price=499,
                currency="USD",
                availability="In Stock",
                rating=4.6,
                review_count=220,
                summary="Great panel.\x1b[0m",
                pros=["Accurate colors\t", "Bright panel"],
                cons=["Mediocre speakers"],
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="image quality",
                        score=9,
                        evidence="Strong review consensus.",
                    )
                ],
                source_urls=["https://example.com/monitor", "https://reviews.example.com/monitor"],
            ),
            ProductOption(
                name="Display Two",
                retailer="Retailer B",
                product_url="https://example.com/monitor-2",
                price=549,
                currency="USD",
                availability="In Stock",
                rating=4.4,
                review_count=180,
                summary="Solid alternative.",
                criterion_assessments=[
                    CriterionAssessment(
                        criterion_name="image quality",
                        score=8,
                        evidence="Good image quality.",
                    )
                ],
                source_urls=["https://example.com/monitor-2", "https://reviews.example.com/monitor-2"],
            ),
        ],
        notable_tradeoffs=["Glossy finish\x1b[7m may reflect light"],
    )

    decision = build_purchase_decision(request, research, rank_options(request, request.criteria, research))
    report = render_text_report(decision)

    assert "\x1b" not in report
    assert "\r" not in report
    assert "Retailer A" in report
