from __future__ import annotations

import ast
import builtins
import typing
from typing import Any, Mapping


def eval_type_backport(
    value: Any,
    globalns: Mapping[str, Any] | None = None,
    localns: Mapping[str, Any] | None = None,
    try_default: bool = True,
) -> Any:
    """Evaluate a forward reference that may use Python 3.10 union syntax.

    This is a narrow compatibility shim for Python 3.9 so pydantic can import
    libraries that emit annotations such as ``str | None`` or ``List[str | int]``.
    """

    if isinstance(value, typing.ForwardRef):
        expression = value.__forward_arg__
    elif isinstance(value, str):
        expression = value
    else:
        return value

    namespace = _build_namespace(globalns, localns)
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body, namespace)


def _build_namespace(
    globalns: Mapping[str, Any] | None,
    localns: Mapping[str, Any] | None,
) -> dict[str, Any]:
    namespace: dict[str, Any] = {"typing": typing}
    namespace.update(vars(typing))
    namespace.update(vars(builtins))
    if globalns:
        namespace.update(globalns)
    if localns:
        namespace.update(localns)
    return namespace


def _eval_node(node: ast.AST, namespace: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        members = [_normalize_union_member(_eval_node(part, namespace)) for part in _flatten_union(node)]
        return typing.Union[tuple(members)]

    if isinstance(node, ast.Name):
        if node.id == "None":
            return None
        try:
            return namespace[node.id]
        except KeyError as exc:
            raise NameError(f"Unknown type name {node.id!r}") from exc

    if isinstance(node, ast.Attribute):
        return getattr(_eval_node(node.value, namespace), node.attr)

    if isinstance(node, ast.Subscript):
        base = _eval_node(node.value, namespace)
        subscript = _eval_slice(node.slice, namespace)
        return base[subscript]

    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(element, namespace) for element in node.elts)

    if isinstance(node, ast.List):
        return [_eval_node(element, namespace) for element in node.elts]

    if isinstance(node, ast.Constant):
        return node.value

    raise TypeError(f"Unsupported type annotation syntax: {ast.dump(node)}")


def _eval_slice(node: ast.AST, namespace: Mapping[str, Any]) -> Any:
    value = _eval_node(node, namespace)
    return tuple(value) if isinstance(value, list) else value


def _flatten_union(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _flatten_union(node.left) + _flatten_union(node.right)
    return [node]


def _normalize_union_member(value: Any) -> Any:
    return type(None) if value is None else value
