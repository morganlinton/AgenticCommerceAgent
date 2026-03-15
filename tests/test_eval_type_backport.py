from __future__ import annotations

import typing

from eval_type_backport import eval_type_backport


def test_eval_type_backport_supports_pipe_union_syntax() -> None:
    result = eval_type_backport(typing.ForwardRef("str | None"))

    assert result == typing.Optional[str]


def test_eval_type_backport_supports_nested_generics() -> None:
    result = eval_type_backport(typing.ForwardRef("List[str | int] | None"), {"List": typing.List})

    assert result == typing.Optional[typing.List[typing.Union[str, int]]]
