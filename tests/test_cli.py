import argparse

import pytest

from agentic_shopping_agent.cli import _parse_budget_arg, _parse_budget_value


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("500", 500.0),
        ("$500", 500.0),
        ("1,299.99", 1299.99),
        ("USD 250", 250.0),
        ("250 USD", 250.0),
    ],
)
def test_parse_budget_value_accepts_common_money_formats(raw_value: str, expected: float) -> None:
    assert _parse_budget_value(raw_value) == expected


@pytest.mark.parametrize("raw_value", ["about 500", "500-700", "five hundred"])
def test_parse_budget_value_rejects_ambiguous_formats(raw_value: str) -> None:
    with pytest.raises(ValueError):
        _parse_budget_value(raw_value)


def test_parse_budget_arg_raises_argparse_error_for_invalid_budget() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_budget_arg("about 500")
