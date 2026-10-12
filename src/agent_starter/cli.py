"""Interactive command-line interface."""

from __future__ import annotations

from dotenv import load_dotenv

from .agent import Agent


def main() -> None:
    load_dotenv()
    agent = Agent()
    print("Mini Agent Lab（输入 /reset 清空对话，/quit 退出）")

    while True:
        try:
            message = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            return

        if message == "/quit":
            print("再见！")
            return
        if message == "/reset":
            agent.reset()
            print("对话已清空。")
            continue
        if not message:
            continue

        try:
            print(f"Agent: {agent.run(message)}")
        except Exception as exc:  # CLI boundary: present SDK/network errors cleanly.
            print(f"请求失败: {exc}")


if __name__ == "__main__":
    main()

