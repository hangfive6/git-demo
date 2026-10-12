"""Small, explicit tools exposed to the model."""

from __future__ import annotations

import ast
import json
import operator
from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ToolError(ValueError):
    """A safe-to-return tool execution error."""


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
MAX_EXPRESSION_LENGTH = 200
MAX_ABS_RESULT = 1e100
MAX_POWER = 12


def calculate(expression: str) -> dict[str, int | float]:
    """Evaluate arithmetic without executing arbitrary Python code."""
    if not expression.strip() or len(expression) > MAX_EXPRESSION_LENGTH:
        raise ToolError("Expression is empty or too long.")

    try:
        tree = ast.parse(expression, mode="eval")
        result = _evaluate_node(tree.body)
    except (SyntaxError, ZeroDivisionError, OverflowError) as exc:
        raise ToolError(f"Invalid arithmetic expression: {exc}") from exc

    if abs(result) > MAX_ABS_RESULT:
        raise ToolError("Result is outside the allowed range.")
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return {"result": result}


def _evaluate_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER:
            raise ToolError(f"Exponent must be between -{MAX_POWER} and {MAX_POWER}.")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    raise ToolError("Only numeric literals and arithmetic operators are allowed.")


def get_current_time(timezone: str) -> dict[str, str]:
    """Return the current time in an IANA timezone."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except ZoneInfoNotFoundError as exc:
        raise ToolError(f"Unknown IANA timezone: {timezone}") from exc
    return {"timezone": timezone, "iso_time": now.isoformat(timespec="seconds")}


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "calculate",
        "description": "Safely evaluate a basic arithmetic expression.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic using numbers, parentheses, +, -, *, /, //, %, or **.",
                }
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current time for an IANA timezone.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA timezone such as Asia/Shanghai or Europe/London.",
                }
            },
            "required": ["timezone"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def execute_tool(name: str, arguments_json: str) -> str:
    """Validate, dispatch, and JSON-encode one model-requested tool call."""
    try:
        arguments = json.loads(arguments_json)
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be a JSON object.")
        if name == "calculate":
            _require_exact_keys(arguments, {"expression"})
            result = calculate(str(arguments["expression"]))
        elif name == "get_current_time":
            _require_exact_keys(arguments, {"timezone"})
            result = get_current_time(str(arguments["timezone"]))
        else:
            raise ToolError(f"Unknown tool: {name}")
        return json.dumps({"ok": True, "data": result}, ensure_ascii=False)
    except (json.JSONDecodeError, ToolError) as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)


def _require_exact_keys(arguments: dict[str, Any], expected: set[str]) -> None:
    if set(arguments) != expected:
        raise ToolError(f"Expected exactly these arguments: {sorted(expected)}")

