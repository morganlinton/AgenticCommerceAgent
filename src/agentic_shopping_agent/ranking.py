from __future__ import annotations

import re
from typing import Optional

from agentic_shopping_agent.models import (
    ProductOption,
    PurchaseDecision,
    RankedOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
)

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def rank_options(
    request: ShoppingRequest,
    criteria: list[ShoppingCriterion],
    research: ShoppingResearch,
) -> list[RankedOption]:
    ranked_options: list[RankedOption] = []

    for option in research.options:
        criterion_score, rationale = _criterion_component(option, criteria)
        budget_score = _budget_component(request.budget, option.price)
        quality_score = _quality_component(option)
        trust_score = _trust_component(option)
        total_score = round(criterion_score + budget_score + quality_score + trust_score, 2)

        ranked_options.append(
            RankedOption(
                product=option,
                total_score=total_score,
                criterion_score=round(criterion_score, 2),
                budget_score=round(budget_score, 2),
                quality_score=round(quality_score, 2),
                trust_score=round(trust_score, 2),
                rationale=rationale,
            )
        )

    ranked_options.sort(key=lambda item: item.total_score, reverse=True)
    return ranked_options


def build_purchase_decision(
    request: ShoppingRequest,
    research: ShoppingResearch,
    ranked_options: list[RankedOption],
    live_url: Optional[str] = None,
) -> PurchaseDecision:
    recommended = ranked_options[0]
    alternatives = ranked_options[1:3]

    option = recommended.product
    price_text = _price_text(option.price, option.currency or request.currency)
    alternative_text = ", ".join(
        f"{alternative.product.name} ({alternative.total_score:.1f})" for alternative in alternatives
    )
    alternative_clause = (
        f" Runner-ups were {alternative_text}."
        if alternative_text
        else ""
    )

    final_answer = (
        f"I would buy {option.name} from {option.retailer} for {price_text}. "
        f"It scored highest on the criteria that matter here: {_join_reasons(recommended.rationale)}."
        f"{alternative_clause}"
    )

    return PurchaseDecision(
        request=request,
        research_summary=research.search_summary,
        recommended_option=recommended,
        alternatives=alternatives,
        final_answer=final_answer,
        notable_tradeoffs=research.notable_tradeoffs,
        missing_information=research.missing_information,
        live_url=live_url,
    )


def render_text_report(decision: PurchaseDecision) -> str:
    recommended = decision.recommended_option
    product = recommended.product
    lines = []

    if decision.live_url:
        lines.append(f"Live browser: {_sanitize_terminal_text(decision.live_url)}")
        lines.append("")

    lines.append("Recommendation")
    lines.append(f"- Research summary: {_sanitize_terminal_text(decision.research_summary)}")
    lines.append(
        f"- I would buy: {_sanitize_terminal_text(product.name)} from {_sanitize_terminal_text(product.retailer)} for {_price_text(product.price, product.currency or decision.request.currency)}"
    )
    lines.append(f"- Why: {_sanitize_terminal_text(_join_reasons(recommended.rationale))}")
    lines.append(f"- Product page: {_sanitize_terminal_text(product.product_url)}")
    lines.append(f"- Score: {recommended.total_score:.1f}/100")

    if product.summary:
        lines.append(f"- Summary: {_sanitize_terminal_text(product.summary)}")

    if product.pros:
        lines.append(f"- Pros: {_sanitize_terminal_text(', '.join(product.pros))}")

    if product.cons:
        lines.append(f"- Cons: {_sanitize_terminal_text(', '.join(product.cons))}")

    lines.append("")
    lines.append("Runner-ups")
    if decision.alternatives:
        for alternative in decision.alternatives:
            alt_product = alternative.product
            lines.append(
                f"- {_sanitize_terminal_text(alt_product.name)} from {_sanitize_terminal_text(alt_product.retailer)} at {_price_text(alt_product.price, alt_product.currency or decision.request.currency)} ({alternative.total_score:.1f}/100)"
            )
    else:
        lines.append("- No runner-ups were strong enough to keep.")

    if decision.notable_tradeoffs:
        lines.append("")
        lines.append("Tradeoffs")
        for tradeoff in decision.notable_tradeoffs:
            lines.append(f"- {_sanitize_terminal_text(tradeoff)}")

    if decision.missing_information:
        lines.append("")
        lines.append("Missing information")
        for item in decision.missing_information:
            lines.append(f"- {_sanitize_terminal_text(item)}")

    lines.append("")
    lines.append("Final answer")
    lines.append(f"- {_sanitize_terminal_text(decision.final_answer)}")
    return "\n".join(lines)


def _criterion_component(
    option: ProductOption,
    criteria: list[ShoppingCriterion],
) -> tuple[float, list[str]]:
    lookup = {assessment.criterion_name.casefold(): assessment for assessment in option.criterion_assessments}
    weighted_total = 0.0
    weight_sum = 0.0
    rationale: list[str] = []

    for criterion in criteria:
        assessment = lookup.get(criterion.name.casefold())
        weight = criterion.weight
        weight_sum += weight

        if assessment is None:
            score = 4
            rationale.append(f"limited evidence on {criterion.name}")
        else:
            score = assessment.score
            if score >= 8:
                rationale.append(f"strong fit on {criterion.name}")
            elif score <= 4:
                rationale.append(f"weak fit on {criterion.name}")

        weighted_total += score * weight

    if weight_sum == 0:
        return 0.0, rationale

    normalized = (weighted_total / (weight_sum * 10.0)) * 60.0
    return normalized, rationale[:4]


def _budget_component(budget: Optional[float], price: Optional[float]) -> float:
    if budget is None:
        return 7.0 if price is not None else 4.0

    if price is None:
        return 3.0

    if price <= budget:
        savings_ratio = 1 - (price / budget) if budget else 0.0
        return 8.0 + min(7.0, savings_ratio * 7.0)

    overspend_ratio = (price - budget) / budget if budget else 1.0
    return max(0.0, 6.0 - (overspend_ratio * 18.0))


def _quality_component(option: ProductOption) -> float:
    if option.rating is None:
        return 6.0

    rating_score = (option.rating / 5.0) * 10.0
    review_bonus = 5.0 if option.review_count and option.review_count >= 100 else 2.5 if option.review_count else 0.0
    return min(15.0, rating_score + review_bonus)


def _trust_component(option: ProductOption) -> float:
    score = 0.0

    if option.product_url:
        score += 4.0
    if option.availability and "out of stock" not in option.availability.casefold():
        score += 3.0
    if len(option.source_urls) >= 2:
        score += 5.0
    elif option.source_urls:
        score += 3.0
    if option.confidence_notes:
        score -= 1.0

    return max(0.0, min(10.0, score))


def _price_text(price: Optional[float], currency: str) -> str:
    if price is None:
        return f"an unknown price in {currency}"
    return f"{price:.2f} {currency}"


def _join_reasons(reasons: list[str]) -> str:
    if not reasons:
        return "the option had the best overall evidence"
    if len(reasons) == 1:
        return reasons[0]
    return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"


def _sanitize_terminal_text(value: str) -> str:
    value = ANSI_ESCAPE_RE.sub("", value)
    sanitized = []
    for char in value:
        codepoint = ord(char)
        if char in "\r\n\t":
            sanitized.append(" ")
            continue
        if codepoint < 32 or 127 <= codepoint <= 159:
            continue
        sanitized.append(char)
    return "".join(sanitized)
