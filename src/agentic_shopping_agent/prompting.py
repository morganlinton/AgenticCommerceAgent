from __future__ import annotations

from agentic_shopping_agent.models import RankedOption, ShoppingCriterion, ShoppingRequest


DEFAULT_CRITERIA = [
    ShoppingCriterion(name="overall value for money", kind="preference", weight=1.0),
    ShoppingCriterion(name="product quality and durability", kind="preference", weight=1.0),
    ShoppingCriterion(name="retailer trust and current availability", kind="must_have", weight=1.5),
]


def ensure_effective_criteria(criteria: list[ShoppingCriterion]) -> list[ShoppingCriterion]:
    if criteria:
        return criteria
    return list(DEFAULT_CRITERIA)


def build_shopping_task(request: ShoppingRequest, criteria: list[ShoppingCriterion]) -> str:
    budget_text = (
        f"Stay at or under {request.budget:.2f} {request.currency} when realistic."
        if request.budget is not None
        else "There is no hard budget, but value still matters."
    )
    notes_text = request.notes or "No extra notes were provided."
    domains_text = (
        ", ".join(request.allowed_domains)
        if request.allowed_domains
        else "No retailer restrictions. Use reputable stores and trusted review sources."
    )

    criteria_lines = "\n".join(
        f"- {criterion.name} ({criterion.kind}, weight {criterion.weight:.1f})"
        for criterion in criteria
    )

    return f"""
You are helping a shopper decide what to buy.

Shopper request: {request.query}
Location: {request.location}
Currency preference: {request.currency}
Budget guidance: {budget_text}
Allowed domains: {domains_text}
Additional notes: {notes_text}

Decision criteria:
{criteria_lines}

Research instructions:
1. Browse reputable retailer pages and, when useful, trustworthy review sites.
2. Find {request.max_options} distinct products that are realistically purchasable now.
3. Prioritize current product pages with pricing and availability over generic listicles.
4. Do not attempt checkout, login, or payment.
5. Capture direct product URLs and source URLs for every option.
6. For each decision criterion, provide a 0-10 score where:
   - 10 means the product strongly satisfies that requirement.
   - 0 means it clearly fails the requirement.
   - For avoid rules, 10 means the product clearly avoids the undesired trait.
7. If a fact is uncertain, note that uncertainty in confidence_notes or missing_information.
8. The final options should be meaningfully different, not duplicate listings of the same item.

Output expectations:
- Keep summaries concise and factual.
- Prefer products with enough evidence to justify a confident recommendation.
- Include useful pros, cons, and tradeoffs.
""".strip()


def build_verification_task(
    request: ShoppingRequest,
    ranked_options: list[RankedOption],
) -> str:
    candidate_lines = []
    for index, ranked_option in enumerate(ranked_options, start=1):
        product = ranked_option.product
        candidate_lines.append(
            "\n".join(
                [
                    f"{index}. Product name: {product.name}",
                    f"   Retailer: {product.retailer}",
                    f"   Product URL: {product.product_url}",
                    f"   Original price: {_format_price(product.price, product.currency or request.currency)}",
                    f"   Original availability: {product.availability or 'Unknown'}",
                ]
            )
        )

    candidates_text = "\n".join(candidate_lines)

    return f"""
You are verifying previously researched shopping options before the final recommendation.

Shopper request: {request.query}
Location: {request.location}
Currency preference: {request.currency}

Products to verify:
{candidates_text}

Verification instructions:
1. Open each exact product URL first. Do not search for new products unless the page is broken.
2. Confirm whether the page still matches the same product.
3. Verify current price, currency, and availability if the page shows them.
4. Compare those facts against the original research and report whether price or availability changed.
5. Include short notes and the URLs you used.
6. Do not attempt checkout, login, or payment.

Output expectations:
- Keep notes factual and concise.
- If a fact cannot be confirmed, say so clearly.
- Focus on whether the current listing still supports the recommendation.
""".strip()


def _format_price(price: float | None, currency: str) -> str:
    if price is None:
        return f"Unknown ({currency})"
    return f"{price:.2f} {currency}"
