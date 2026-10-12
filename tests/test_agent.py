from types import SimpleNamespace

from agent_starter.agent import Agent


class FakeResponses:
    def __init__(self) -> None:
        self.requests = []
        self.responses = [
            SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="calculate",
                        arguments='{"expression":"6 * 7"}',
                        call_id="call_test",
                    )
                ],
                output_text="",
            ),
            SimpleNamespace(output=[SimpleNamespace(type="message")], output_text="42"),
        ]

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)


def test_agent_round_trips_tool_output() -> None:
    fake_responses = FakeResponses()
    fake_client = SimpleNamespace(responses=fake_responses)
    agent = Agent(client=fake_client, model="test-model")

    assert agent.run("What is 6 * 7?") == "42"
    second_input = fake_responses.requests[1]["input"]
    tool_outputs = [item for item in second_input if isinstance(item, dict) and item.get("type") == "function_call_output"]
    assert len(tool_outputs) == 1
    assert '"result": 42' in tool_outputs[0]["output"]

