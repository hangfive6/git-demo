# Mini Agent Lab

一个小而完整的 Agent 开发示例，基于 OpenAI Responses API 实现可测试的工具调用循环。

## 它展示了什么

- Agent 如何把用户请求交给模型
- 模型如何选择并调用本地工具
- 应用如何执行工具，并把结果送回模型
- 如何限制工具参数、计算能力和循环次数
- 如何用假的模型响应测试 Agent，而不消耗 API 额度

内置两个只读工具：安全算术计算和 IANA 时区时间查询。

## 请求流程

```text
用户 -> Agent -> Responses API
                  |
                  v
              function_call
                  |
                  v
           本地工具注册表执行
                  |
                  v
        function_call_output -> Responses API -> 最终回答
```

## 快速开始

需要 Python 3.11 或更高版本。

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env  # Windows；macOS/Linux 使用 cp
```

在 `.env` 中填写你的 API 密钥。密钥只从 `OPENAI_API_KEY` 环境变量读取，`.env` 已被 Git 忽略，不要把真实密钥提交到仓库。

启动交互式 Agent：

```bash
mini-agent
```

示例问题：

```text
计算 (18 + 7) * 3
现在上海几点？
```

运行测试：

```bash
pytest
```

## 代码结构

```text
src/agent_starter/agent.py   Agent 循环与 Responses API 编排
src/agent_starter/tools.py   工具定义、安全实现与分发
src/agent_starter/cli.py     命令行入口
tests/                       无需网络和密钥的单元测试
```

## 安全设计

- 不在代码或日志中存储 API 密钥。
- 计算器使用受限 AST，不调用 `eval`。
- 函数 schema 启用严格模式，并拒绝额外参数。
- Agent 设置最大工具调用轮数，避免无限循环。
- 工具分发采用显式白名单，未知工具不会被执行。

## 延伸练习

1. 添加数据库查询工具，并使用只读数据库账号。
2. 为有副作用的工具加入人工确认。
3. 记录延迟、token 使用量和工具错误，用于评估。
4. 添加检索工具，把团队文档接入 Agent。

实现遵循 OpenAI 官方的五步工具调用流程：发送工具定义、接收调用、在应用侧执行、回传工具输出、获取最终回答。参考 [Function calling 文档](https://developers.openai.com/api/docs/guides/function-calling) 与 [GPT-5.4 Mini 模型页](https://developers.openai.com/api/docs/models/gpt-5.4-mini)。


