# Claude Code Entry

@../AGENTS.md
@../common/AGENT_CORE.md
@../common/docs/platform-capability-model.md
@../common/docs/model-routing.md

Current directory is the Claude Code platform-local template for the RenderDoc/RDC GPU debugger framework.

Entry contract:

- startup stays in ordinary chat mode; do not auto-enter the debugger framework
- public main skill: `.claude/skills/rdc-debugger/`
- enter the debugger framework only when the user explicitly invokes `rdc-debugger`
- default entry mode is local-first `CLI`
- switch to `MCP` only when the user explicitly asks for `MCP`
- a configured `MCP` server is an optional surface, not a default live-access mandate

Runtime contract:

- standalone `python ...run_cli.py` or `rdx capture open` only establish tools-layer session state
- standalone tools-layer session bootstrap does not create framework `workspace/case/run`
- accepted manual `rdc-debugger` intake is the only path that may initialize framework workspace state
- runtime workspace is fixed to platform-root `workspace/`

Prerequisite:

- do not use this template until top-level `debugger/common/` has been copied into platform-root `common/`
