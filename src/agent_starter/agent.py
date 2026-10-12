"""A minimal Responses API tool-calling loop."""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from .tools import TOOL_SCHEMAS, execute_tool


DEFAULT_INSTRUCTIONS = """You are a concise, helpful assistant.
Use a tool whenever it is needed for an exact answer.
Never invent tool results. If a tool reports an error, explain it and ask for a corrected input.
Reply in the same language as the user.
"""


class Agent:
    """Stateful agent with an explicit, bounded tool loop."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
        instructions: str = DEFAULT_INSTRUCTIONS,
        max_tool_rounds: int = 8,
    ) -> None:
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1")
        self.client = client or OpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
        self.instructions = instructions
        self.max_tool_rounds = max_tool_rounds
        self.history: list[Any] = []

    def run(self, user_input: str) -> str:
        """Run one user turn, including any requested tools."""
        if not user_input.strip():
            raise ValueError("user_input cannot be empty")

        self.history.append({"role": "user", "content": user_input})
        for _ in range(self.max_tool_rounds):
            response = self.client.responses.create(
                model=self.model,
                instructions=self.instructions,
                input=self.history,
                tools=TOOL_SCHEMAS,
            )
            self.history.extend(response.output)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return response.output_text

            for call in calls:
                self.history.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": execute_tool(call.name, call.arguments),
                    }
                )

        raise RuntimeError("Agent stopped after reaching the tool-call safety limit.")

    def reset(self) -> None:
        """Clear local conversation state."""
        self.history.clear()

