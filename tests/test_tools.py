import json

import pytest

from agent_starter.tools import ToolError, calculate, execute_tool, get_current_time


def test_calculate_respects_precedence() -> None:
    assert calculate("(18 + 7) * 3") == {"result": 75}


@pytest.mark.parametrize("expression", ["__import__('os')", "[1, 2, 3]", "2 ** 99"])
def test_calculate_rejects_unsafe_or_expensive_input(expression: str) -> None:
    with pytest.raises(ToolError):
        calculate(expression)


def test_get_current_time_uses_requested_timezone() -> None:
    result = get_current_time("Asia/Shanghai")
    assert result["timezone"] == "Asia/Shanghai"
    assert "+08:00" in result["iso_time"]


def test_dispatcher_returns_structured_errors() -> None:
    payload = json.loads(execute_tool("missing", "{}"))
    assert payload["ok"] is False
    assert "Unknown tool" in payload["error"]

