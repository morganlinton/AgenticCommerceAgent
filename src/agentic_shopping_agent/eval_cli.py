from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from agentic_shopping_agent.evals import (
    EvalRunner,
    LiveDecisionProvider,
    filter_scenarios,
    load_scenarios,
    write_report_files,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run benchmark scenarios against the shopping agent and write JSON/Markdown reports."
    )
    parser.add_argument(
        "--scenario-id",
        action="append",
        default=[],
        help="Run only the named scenario id. Repeat for multiple scenarios.",
    )
    parser.add_argument(
        "--scenario-file",
        type=Path,
        help="Optional JSON file containing custom eval scenarios.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_reports"),
        help="Directory where eval reports should be written.",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        help="Run only the first N scenarios after filtering.",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="Print available scenario ids and titles, then exit.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failing scenario or runtime error.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    scenarios = load_scenarios(args.scenario_file)
    scenarios = filter_scenarios(scenarios, scenario_ids=args.scenario_id, max_scenarios=args.max_scenarios)

    if args.list_scenarios:
        for scenario in scenarios:
            print(f"{scenario.id}: {scenario.title}")
        return

    if not scenarios:
        raise SystemExit("No eval scenarios matched the requested filters.")

    runner = EvalRunner(LiveDecisionProvider())
    report = asyncio.run(
        runner.run(
            scenarios,
            fail_fast=args.fail_fast,
            status_callback=lambda message: print(message),
        )
    )
    report_paths = write_report_files(report, args.output_dir)

    print("")
    print(f"Scenarios run: {report.summary.total_scenarios}")
    print(f"Passed: {report.summary.passed_scenarios}")
    print(f"Failed: {report.summary.failed_scenarios}")
    print(f"Pass rate: {report.summary.pass_rate:.0%}")
    print(f"Verification success rate: {report.summary.verification_success_rate:.0%}")
    print(f"Average sources per recommendation: {report.summary.average_sources_per_recommendation:.2f}")
    print(f"JSON report: {report_paths.json_path}")
    print(f"Markdown report: {report_paths.markdown_path}")


if __name__ == "__main__":
    main()
