# Claude Code Entry（宿主入口）

@../AGENTS.md
@../common/AGENT_CORE.md
@../common/docs/platform-capability-model.md
@../common/docs/model-routing.md

当前目录是 Claude Code 的 platform-local 模板。Agent 的目标是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。

当前项目的 public main skill 是 `.claude/skills/rdc-debugger/`。若 `.claude/settings.json` 仍保留 session-wide `team-lead` agent，它只承担 host bootstrap / orchestrator 语义；正常用户请求不应绕过 `rdc-debugger` 直接把 `team_lead` 或 specialist 当正式入口。

Claude Code 平台上的 live RenderDoc 访问统一走已配置的 MCP server；不要把 `python ...run_cli.py` 一类 Bash 包装视为正式入口。

未先将顶层 `debugger/common/` 拷入当前平台根目录的 `common/` 之前，不允许在宿主中使用当前平台模板。

运行时工作区固定为：`../workspace`
