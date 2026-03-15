from agentic_shopping_agent.models import ShoppingCriterion, ShoppingRequest
from agentic_shopping_agent.prompting import build_shopping_task, ensure_effective_criteria


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
