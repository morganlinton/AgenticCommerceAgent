from __future__ import annotations

import re
from typing import Optional

from agentic_shopping_agent.models import (
    ComparisonCriterionRow,
    ComparisonRow,
    ProductOption,
    ProductVerification,
    PurchaseDecision,
    RankedOption,
    ShoppingCriterion,
    ShoppingRequest,
    ShoppingResearch,
    VerificationReport,
)

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def rank_options(
    request: ShoppingRequest,
    criteria: list[ShoppingCriterion],
    research: ShoppingResearch,
    verifications: Optional[dict[str, ProductVerification]] = None,
) -> list[RankedOption]:
    ranked_options: list[RankedOption] = []

    for option in research.options:
        criterion_score, rationale = _criterion_component(option, criteria)
        budget_score = _budget_component(request.budget, option.price)
        quality_score = _quality_component(option)
        trust_score = _trust_component(option)
        verification = _lookup_verification(option, verifications or {})
        verification_score, verification_rationale = _verification_component(option, verification)
        total_score = round(
            criterion_score + budget_score + quality_score + trust_score + verification_score,
            2,
        )

        ranked_options.append(
            RankedOption(
                product=option,
                total_score=total_score,
                criterion_score=round(criterion_score, 2),
                budget_score=round(budget_score, 2),
                quality_score=round(quality_score, 2),
                trust_score=round(trust_score, 2),
                verification_score=round(verification_score, 2),
                rationale=(rationale + verification_rationale)[:5],
                verification=verification,
            )
        )

    ranked_options.sort(key=lambda item: item.total_score, reverse=True)
    return ranked_options


def build_purchase_decision(
    request: ShoppingRequest,
    research: ShoppingResearch,
    ranked_options: list[RankedOption],
    verification_report: Optional[VerificationReport] = None,
    missing_information: Optional[list[str]] = None,
    live_url: Optional[str] = None,
) -> PurchaseDecision:
    recommended = ranked_options[0]
    alternatives = ranked_options[1:3]
    comparison_rows = _build_comparison_rows(ranked_options, request.criteria)

    option = recommended.product
    display_price, display_currency = _resolved_option_price(recommended, request.currency)
    price_text = _price_text(display_price, display_currency)
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
    if recommended.verification is not None:
        final_answer += f" Final verification: {recommended.verification.notes}"

    return PurchaseDecision(
        request=request,
        research_summary=research.search_summary,
        recommended_option=recommended,
        alternatives=alternatives,
        comparison_rows=comparison_rows,
        final_answer=final_answer,
        notable_tradeoffs=research.notable_tradeoffs,
        missing_information=missing_information if missing_information is not None else research.missing_information,
        verification_summary=verification_report.summary if verification_report is not None else None,
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
    recommended_price, recommended_currency = _resolved_option_price(recommended, decision.request.currency)
    lines.append(
        f"- I would buy: {_sanitize_terminal_text(product.name)} from {_sanitize_terminal_text(product.retailer)} for {_price_text(recommended_price, recommended_currency)}"
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

    if recommended.verification is not None:
        lines.append(
            f"- Verification: {_verification_status(recommended.verification)} | {_sanitize_terminal_text(recommended.verification.notes)}"
        )
        if recommended.verification.verified_price is not None:
            lines.append(
                f"- Verified price: {_price_text(recommended.verification.verified_price, recommended.verification.verified_currency or decision.request.currency)}"
            )
        if recommended.verification.verified_availability:
            lines.append(
                f"- Verified availability: {_sanitize_terminal_text(recommended.verification.verified_availability)}"
            )

    lines.append("")
    lines.append("Runner-ups")
    if decision.alternatives:
        for alternative in decision.alternatives:
            alt_product = alternative.product
            alt_price, alt_currency = _resolved_option_price(alternative, decision.request.currency)
            lines.append(
                f"- {_sanitize_terminal_text(alt_product.name)} from {_sanitize_terminal_text(alt_product.retailer)} at {_price_text(alt_price, alt_currency)} ({alternative.total_score:.1f}/100)"
            )
    else:
        lines.append("- No runner-ups were strong enough to keep.")

    if decision.notable_tradeoffs:
        lines.append("")
        lines.append("Tradeoffs")
        for tradeoff in decision.notable_tradeoffs:
            lines.append(f"- {_sanitize_terminal_text(tradeoff)}")

    if decision.verification_summary:
        lines.append("")
        lines.append("Verification")
        lines.append(f"- {_sanitize_terminal_text(decision.verification_summary)}")

    if decision.comparison_rows:
        lines.append("")
        lines.append("Comparison")
        for row in decision.comparison_rows:
            lines.append(
                f"- {row.rank}. {_sanitize_terminal_text(row.product_name)} | total {row.total_score:.1f} | criteria {row.criterion_score:.1f} | budget {row.budget_score:.1f} | quality {row.quality_score:.1f} | trust {row.trust_score:.1f} | verification {row.verification_score:.1f} | {_sanitize_terminal_text(row.verification_status)}"
            )
            if row.price is not None:
                lines.append(
                    f"  Price: {_price_text(row.price, row.currency or decision.request.currency)} | Availability: {_sanitize_terminal_text(row.availability or 'Unknown')} | Sources: {row.source_count}"
                )
            else:
                lines.append(
                    f"  Price: unknown | Availability: {_sanitize_terminal_text(row.availability or 'Unknown')} | Sources: {row.source_count}"
                )
            if row.criterion_breakdown:
                criteria_text = "; ".join(
                    _sanitize_terminal_text(
                        f"{criterion.criterion_name} ({criterion.criterion_kind}) {criterion.score if criterion.score is not None else '?'}"
                    )
                    for criterion in row.criterion_breakdown
                )
                lines.append(f"  Criteria: {criteria_text}")
            if row.verification_notes:
                lines.append(f"  Verification notes: {_sanitize_terminal_text(row.verification_notes)}")

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

    normalized = (weighted_total / (weight_sum * 10.0)) * 50.0
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


def _verification_component(
    option: ProductOption,
    verification: Optional[ProductVerification],
) -> tuple[float, list[str]]:
    if verification is None:
        return 5.0, ["verification not completed"]

    status = _verification_status(verification)
    rationale: list[str] = []

    if status == "verified":
        rationale.append("final verification confirmed the listing")
    elif status == "changed":
        rationale.append("final verification found changes in the listing")
    else:
        rationale.append("final verification was inconclusive")

    score = 5.0
    if verification.product_still_matches:
        score += 2.0
    else:
        score -= 5.0

    if verification.price_matches_original is True:
        score += 1.5
    elif verification.price_matches_original is False:
        score -= 2.0

    if verification.verified_availability:
        if "out of stock" in verification.verified_availability.casefold():
            score -= 4.0
        else:
            score += 1.5

    if verification.availability_matches_original is True:
        score += 1.0
    elif verification.availability_matches_original is False:
        score -= 1.5

    return max(0.0, min(10.0, score)), rationale


def _price_text(price: Optional[float], currency: str) -> str:
    if price is None:
        return f"an unknown price in {currency}"
    return f"{price:.2f} {currency}"


def _resolved_option_price(
    ranked_option: RankedOption,
    fallback_currency: str,
) -> tuple[Optional[float], str]:
    verification = ranked_option.verification
    if verification is not None and verification.verified_price is not None:
        return verification.verified_price, verification.verified_currency or fallback_currency

    product = ranked_option.product
    return product.price, product.currency or fallback_currency


def _join_reasons(reasons: list[str]) -> str:
    if not reasons:
        return "the option had the best overall evidence"
    if len(reasons) == 1:
        return reasons[0]
    return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"


def _lookup_verification(
    option: ProductOption,
    verifications: dict[str, ProductVerification],
) -> Optional[ProductVerification]:
    direct_key = _verification_key(option.product_url)
    if direct_key in verifications:
        return verifications[direct_key]

    fallback_key = _verification_key(option.name)
    return verifications.get(fallback_key)


def _verification_key(value: str) -> str:
    return value.strip().casefold()


def _verification_status(verification: ProductVerification) -> str:
    if not verification.product_still_matches:
        return "changed"
    if verification.price_matches_original is False or verification.availability_matches_original is False:
        return "changed"
    if verification.price_matches_original is None and verification.availability_matches_original is None:
        return "uncertain"
    return "verified"


def _build_comparison_rows(
    ranked_options: list[RankedOption],
    criteria: list[ShoppingCriterion],
) -> list[ComparisonRow]:
    comparison_rows: list[ComparisonRow] = []

    for rank, ranked_option in enumerate(ranked_options, start=1):
        product = ranked_option.product
        verification = ranked_option.verification
        comparison_rows.append(
            ComparisonRow(
                rank=rank,
                product_name=product.name,
                retailer=product.retailer,
                price=verification.verified_price if verification is not None and verification.verified_price is not None else product.price,
                currency=verification.verified_currency if verification is not None and verification.verified_currency is not None else product.currency,
                availability=verification.verified_availability if verification is not None and verification.verified_availability is not None else product.availability,
                total_score=ranked_option.total_score,
                criterion_score=ranked_option.criterion_score,
                budget_score=ranked_option.budget_score,
                quality_score=ranked_option.quality_score,
                trust_score=ranked_option.trust_score,
                verification_score=ranked_option.verification_score,
                verification_status=_verification_status(verification) if verification is not None else "not_run",
                verification_notes=verification.notes if verification is not None else None,
                source_count=len(product.source_urls),
                criterion_breakdown=_build_criterion_breakdown(product, criteria),
            )
        )

    return comparison_rows


def _build_criterion_breakdown(
    product: ProductOption,
    criteria: list[ShoppingCriterion],
) -> list[ComparisonCriterionRow]:
    lookup = {assessment.criterion_name.casefold(): assessment for assessment in product.criterion_assessments}
    rows: list[ComparisonCriterionRow] = []

    for criterion in criteria:
        assessment = lookup.get(criterion.name.casefold())
        rows.append(
            ComparisonCriterionRow(
                criterion_name=criterion.name,
                criterion_kind=criterion.kind,
                score=assessment.score if assessment is not None else None,
                evidence=assessment.evidence if assessment is not None else None,
            )
        )

    return rows


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
