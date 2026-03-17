from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from agentic_shopping_agent.eval_catalog import BUILTIN_EVAL_SCENARIOS
from agentic_shopping_agent.models import PurchaseDecision, ShoppingRequest

if TYPE_CHECKING:
    from agentic_shopping_agent.service import ShoppingAgentService


class ScenarioExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enforce_request_budget: bool = True
    max_recommended_price: Optional[float] = Field(default=None, ge=0)
    min_recommended_source_count: int = Field(default=2, ge=0)
    required_verification_status: Optional[str] = Field(default="verified")
    required_criterion_names: list[str] = Field(default_factory=list)
    required_final_answer_terms: list[str] = Field(default_factory=list)
    required_tradeoff_terms: list[str] = Field(default_factory=list)
    required_recommended_name_terms: list[str] = Field(default_factory=list)
    forbidden_recommended_name_terms: list[str] = Field(default_factory=list)
    forbidden_retailer_terms: list[str] = Field(default_factory=list)
    max_missing_information_count: Optional[int] = Field(default=3, ge=0)
    minimum_comparison_rows: int = Field(default=2, ge=1)
    require_recommended_url_in_allowed_domains: bool = True


class EvalScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    request: ShoppingRequest
    expectations: ScenarioExpectations = Field(default_factory=ScenarioExpectations)


class EvalCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    details: str


class ScenarioEvalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    title: str
    passed: bool
    duration_seconds: float = Field(ge=0)
    recommended_product_name: Optional[str] = None
    recommended_price: Optional[float] = Field(default=None, ge=0)
    verification_status: Optional[str] = None
    source_count: int = Field(default=0, ge=0)
    missing_information_count: int = Field(default=0, ge=0)
    checks: list[EvalCheckResult] = Field(default_factory=list)
    error: Optional[str] = None
    decision_snapshot: Optional[dict[str, Any]] = None


class EvalSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_scenarios: int = Field(ge=0)
    passed_scenarios: int = Field(ge=0)
    failed_scenarios: int = Field(ge=0)
    pass_rate: float = Field(ge=0, le=1)
    verification_success_rate: float = Field(ge=0, le=1)
    average_sources_per_recommendation: float = Field(ge=0)
    failure_reasons: dict[str, int] = Field(default_factory=dict)


class EvalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generated_at: str
    summary: EvalSummary
    scenarios: list[ScenarioEvalResult] = Field(default_factory=list)


class DecisionProvider(Protocol):
    async def get_decision(self, scenario: EvalScenario) -> PurchaseDecision:
        ...


class LiveDecisionProvider:
    def __init__(self, service: Optional["ShoppingAgentService"] = None) -> None:
        if service is None:
            from agentic_shopping_agent.service import ShoppingAgentService

            service = ShoppingAgentService()
        self.service = service

    async def get_decision(self, scenario: EvalScenario) -> PurchaseDecision:
        return await self.service.research_and_recommend(scenario.request)


@dataclass
class ReportPaths:
    json_path: Path
    markdown_path: Path
    latest_json_path: Path
    latest_markdown_path: Path


class EvalRunner:
    def __init__(self, provider: DecisionProvider) -> None:
        self.provider = provider

    async def run(
        self,
        scenarios: list[EvalScenario],
        *,
        fail_fast: bool = False,
        status_callback: Optional[Callable[[str], None]] = None,
    ) -> EvalReport:
        scenario_results: list[ScenarioEvalResult] = []

        for index, scenario in enumerate(scenarios, start=1):
            if status_callback is not None:
                status_callback(f"[{index}/{len(scenarios)}] Running {scenario.id}: {scenario.title}")

            started = monotonic()
            try:
                decision = await self.provider.get_decision(scenario)
                checks = evaluate_decision(scenario, decision)
                scenario_results.append(
                    ScenarioEvalResult(
                        scenario_id=scenario.id,
                        title=scenario.title,
                        passed=all(check.passed for check in checks),
                        duration_seconds=round(monotonic() - started, 2),
                        recommended_product_name=decision.recommended_option.product.name,
                        recommended_price=_resolved_recommended_price(decision),
                        verification_status=_resolved_verification_status(decision),
                        source_count=len(decision.recommended_option.product.source_urls),
                        missing_information_count=len(decision.missing_information),
                        checks=checks,
                        decision_snapshot=decision.model_dump(exclude_none=True),
                    )
                )
            except Exception as exc:
                scenario_results.append(
                    ScenarioEvalResult(
                        scenario_id=scenario.id,
                        title=scenario.title,
                        passed=False,
                        duration_seconds=round(monotonic() - started, 2),
                        error=str(exc),
                    )
                )
                if fail_fast:
                    break

        return EvalReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=_build_summary(scenario_results),
            scenarios=scenario_results,
        )


def load_scenarios(path: Optional[Path] = None) -> list[EvalScenario]:
    adapter = TypeAdapter(list[EvalScenario])
    if path is None:
        return adapter.validate_python(BUILTIN_EVAL_SCENARIOS)

    data = json.loads(path.read_text())
    return adapter.validate_python(data)


def filter_scenarios(
    scenarios: list[EvalScenario],
    scenario_ids: Optional[list[str]] = None,
    max_scenarios: Optional[int] = None,
) -> list[EvalScenario]:
    filtered = scenarios
    if scenario_ids:
        allowed = {scenario_id.casefold() for scenario_id in scenario_ids}
        filtered = [scenario for scenario in filtered if scenario.id.casefold() in allowed]
    if max_scenarios is not None:
        filtered = filtered[:max_scenarios]
    return filtered


def evaluate_decision(scenario: EvalScenario, decision: PurchaseDecision) -> list[EvalCheckResult]:
    expectations = scenario.expectations
    checks: list[EvalCheckResult] = []

    recommended = decision.recommended_option
    recommended_product = recommended.product
    comparison_row = decision.comparison_rows[0] if decision.comparison_rows else None
    recommended_name = recommended_product.name.casefold()
    recommended_retailer = recommended_product.retailer.casefold()
    final_answer = decision.final_answer.casefold()
    tradeoffs_text = " ".join(decision.notable_tradeoffs).casefold()
    missing_information_count = len(decision.missing_information)
    resolved_price = _resolved_recommended_price(decision)
    verification_status = _resolved_verification_status(decision)

    checks.append(
        EvalCheckResult(
            name="comparison_rows_present",
            passed=len(decision.comparison_rows) >= expectations.minimum_comparison_rows,
            details=f"Found {len(decision.comparison_rows)} comparison rows.",
        )
    )

    max_price = expectations.max_recommended_price
    if max_price is None and expectations.enforce_request_budget and scenario.request.budget is not None:
        max_price = scenario.request.budget
    if max_price is not None:
        checks.append(
            EvalCheckResult(
                name="price_within_budget",
                passed=resolved_price is not None and resolved_price <= max_price,
                details=(
                    f"Recommended price was {resolved_price if resolved_price is not None else 'unknown'} "
                    f"against a max of {max_price}."
                ),
            )
        )

    checks.append(
        EvalCheckResult(
            name="sufficient_sources",
            passed=len(recommended_product.source_urls) >= expectations.min_recommended_source_count,
            details=(
                f"Recommended option had {len(recommended_product.source_urls)} sources; "
                f"expected at least {expectations.min_recommended_source_count}."
            ),
        )
    )

    if expectations.required_verification_status is not None:
        checks.append(
            EvalCheckResult(
                name="verification_completed",
                passed=verification_status == expectations.required_verification_status,
                details=(
                    f"Verification status was {verification_status}; "
                    f"expected {expectations.required_verification_status}."
                ),
            )
        )

    if expectations.required_criterion_names:
        present_criteria = {
            row.criterion_name.casefold()
            for row in (comparison_row.criterion_breakdown if comparison_row is not None else [])
            if row.score is not None
        }
        missing_criteria = [
            criterion
            for criterion in expectations.required_criterion_names
            if criterion.casefold() not in present_criteria
        ]
        checks.append(
            EvalCheckResult(
                name="criteria_scored",
                passed=not missing_criteria,
                details=(
                    "All required criteria were scored."
                    if not missing_criteria
                    else f"Missing scored criteria: {', '.join(missing_criteria)}."
                ),
            )
        )

    if expectations.required_recommended_name_terms:
        missing_terms = [
            term for term in expectations.required_recommended_name_terms if term.casefold() not in recommended_name
        ]
        checks.append(
            EvalCheckResult(
                name="required_name_terms",
                passed=not missing_terms,
                details=(
                    "Recommended product name contained all required terms."
                    if not missing_terms
                    else f"Missing required name terms: {', '.join(missing_terms)}."
                ),
            )
        )

    if expectations.forbidden_recommended_name_terms:
        forbidden_hits = [
            term for term in expectations.forbidden_recommended_name_terms if term.casefold() in recommended_name
        ]
        checks.append(
            EvalCheckResult(
                name="forbidden_name_terms",
                passed=not forbidden_hits,
                details=(
                    "Recommended product name avoided all forbidden terms."
                    if not forbidden_hits
                    else f"Forbidden name terms present: {', '.join(forbidden_hits)}."
                ),
            )
        )

    if expectations.forbidden_retailer_terms:
        retailer_hits = [
            term for term in expectations.forbidden_retailer_terms if term.casefold() in recommended_retailer
        ]
        checks.append(
            EvalCheckResult(
                name="forbidden_retailer_terms",
                passed=not retailer_hits,
                details=(
                    "Recommended retailer avoided all forbidden terms."
                    if not retailer_hits
                    else f"Forbidden retailer terms present: {', '.join(retailer_hits)}."
                ),
            )
        )

    if expectations.required_final_answer_terms:
        missing_answer_terms = [
            term for term in expectations.required_final_answer_terms if term.casefold() not in final_answer
        ]
        checks.append(
            EvalCheckResult(
                name="final_answer_terms",
                passed=not missing_answer_terms,
                details=(
                    "Final answer contained all required terms."
                    if not missing_answer_terms
                    else f"Missing final answer terms: {', '.join(missing_answer_terms)}."
                ),
            )
        )

    if expectations.required_tradeoff_terms:
        missing_tradeoff_terms = [
            term for term in expectations.required_tradeoff_terms if term.casefold() not in tradeoffs_text
        ]
        checks.append(
            EvalCheckResult(
                name="tradeoff_terms",
                passed=not missing_tradeoff_terms,
                details=(
                    "Tradeoff text contained all required terms."
                    if not missing_tradeoff_terms
                    else f"Missing tradeoff terms: {', '.join(missing_tradeoff_terms)}."
                ),
            )
        )

    if scenario.request.allowed_domains and expectations.require_recommended_url_in_allowed_domains:
        allowed_domain_match = _url_matches_allowed_domains(
            recommended_product.product_url,
            scenario.request.allowed_domains,
        )
        checks.append(
            EvalCheckResult(
                name="allowed_domain_respected",
                passed=allowed_domain_match,
                details=(
                    f"Recommended URL was {recommended_product.product_url}; "
                    f"allowed domains were {', '.join(scenario.request.allowed_domains)}."
                ),
            )
        )

    if expectations.max_missing_information_count is not None:
        checks.append(
            EvalCheckResult(
                name="missing_information_bounded",
                passed=missing_information_count <= expectations.max_missing_information_count,
                details=(
                    f"Missing information count was {missing_information_count}; "
                    f"max allowed is {expectations.max_missing_information_count}."
                ),
            )
        )

    return checks


def write_report_files(report: EvalReport, output_dir: Path) -> ReportPaths:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / f"eval-report-{timestamp}.json"
    markdown_path = output_dir / f"eval-report-{timestamp}.md"
    latest_json_path = output_dir / "latest.json"
    latest_markdown_path = output_dir / "latest.md"

    json_text = report.model_dump_json(indent=2, exclude_none=True)
    markdown_text = render_markdown_report(report)

    json_path.write_text(json_text + "\n")
    markdown_path.write_text(markdown_text)
    latest_json_path.write_text(json_text + "\n")
    latest_markdown_path.write_text(markdown_text)

    return ReportPaths(
        json_path=json_path,
        markdown_path=markdown_path,
        latest_json_path=latest_json_path,
        latest_markdown_path=latest_markdown_path,
    )


def render_markdown_report(report: EvalReport) -> str:
    lines = [
        "# Agentic Shopping Agent Eval Report",
        "",
        f"Generated at: {report.generated_at}",
        "",
        "## Summary",
        "",
        f"- Total scenarios: {report.summary.total_scenarios}",
        f"- Passed: {report.summary.passed_scenarios}",
        f"- Failed: {report.summary.failed_scenarios}",
        f"- Pass rate: {report.summary.pass_rate:.0%}",
        f"- Verification success rate: {report.summary.verification_success_rate:.0%}",
        f"- Average sources per recommendation: {report.summary.average_sources_per_recommendation:.2f}",
        "",
    ]

    if report.summary.failure_reasons:
        lines.extend(["## Failure Reasons", "", "| Check | Count |", "| --- | ---: |"])
        for name, count in sorted(report.summary.failure_reasons.items()):
            lines.append(f"| {name} | {count} |")
        lines.append("")

    lines.extend(
        [
            "## Scenario Results",
            "",
            "| Scenario | Pass | Verification | Sources | Duration (s) | Recommended Product |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for scenario in report.scenarios:
        recommended_product = scenario.recommended_product_name or "n/a"
        verification_status = scenario.verification_status or "n/a"
        lines.append(
            f"| {scenario.scenario_id} | {'PASS' if scenario.passed else 'FAIL'} | {verification_status} | {scenario.source_count} | {scenario.duration_seconds:.2f} | {recommended_product} |"
        )
    lines.append("")

    failed_scenarios = [scenario for scenario in report.scenarios if not scenario.passed]
    if failed_scenarios:
        lines.extend(["## Failures", ""])
        for scenario in failed_scenarios:
            lines.append(f"### {scenario.scenario_id}")
            lines.append("")
            lines.append(f"- Title: {scenario.title}")
            if scenario.error:
                lines.append(f"- Error: {scenario.error}")
            failed_checks = [check for check in scenario.checks if not check.passed]
            for check in failed_checks:
                lines.append(f"- {check.name}: {check.details}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_summary(scenarios: list[ScenarioEvalResult]) -> EvalSummary:
    total = len(scenarios)
    passed = sum(1 for scenario in scenarios if scenario.passed)
    failed = total - passed
    verification_successes = sum(1 for scenario in scenarios if scenario.verification_status == "verified")
    average_sources = (
        sum(scenario.source_count for scenario in scenarios) / total
        if total
        else 0.0
    )

    failure_reasons: Counter[str] = Counter()
    for scenario in scenarios:
        if scenario.error:
            failure_reasons["scenario_error"] += 1
        for check in scenario.checks:
            if not check.passed:
                failure_reasons[check.name] += 1

    return EvalSummary(
        total_scenarios=total,
        passed_scenarios=passed,
        failed_scenarios=failed,
        pass_rate=(passed / total) if total else 0.0,
        verification_success_rate=(verification_successes / total) if total else 0.0,
        average_sources_per_recommendation=round(average_sources, 2),
        failure_reasons=dict(sorted(failure_reasons.items())),
    )


def _resolved_recommended_price(decision: PurchaseDecision) -> Optional[float]:
    if decision.comparison_rows:
        return decision.comparison_rows[0].price

    verification = decision.recommended_option.verification
    if verification is not None and verification.verified_price is not None:
        return verification.verified_price

    return decision.recommended_option.product.price


def _resolved_verification_status(decision: PurchaseDecision) -> str:
    if decision.comparison_rows:
        return decision.comparison_rows[0].verification_status
    if decision.recommended_option.verification is None:
        return "not_run"
    verification = decision.recommended_option.verification
    if not verification.product_still_matches:
        return "changed"
    if verification.price_matches_original is False or verification.availability_matches_original is False:
        return "changed"
    if verification.price_matches_original is None and verification.availability_matches_original is None:
        return "uncertain"
    return "verified"


def _url_matches_allowed_domains(url: str, allowed_domains: list[str]) -> bool:
    host = urlparse(url).netloc.casefold()
    if not host:
        return False

    for allowed_domain in allowed_domains:
        normalized = allowed_domain.casefold()
        if host == normalized or host.endswith(f".{normalized}"):
            return True
    return False
