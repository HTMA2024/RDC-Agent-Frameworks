# Kiro Workspace Instructions（工作区约束）— Analyzer

当前目录是 Kiro 的 analyzer platform-local 模板。所有角色在进入 role-specific 行为前，都必须先服从本文件与共享 `common/` 约束。

## 前置检查（必须先于任何其他步骤执行）

在执行任何工作前，必须验证以下两项均已就绪：

1. `common/` 已正确覆盖：检查 `common/AGENT_CORE.md` 是否存在。
2. `tools/` 已正确覆盖：检查 `tools/spec/tool_catalog.json` 是否存在。

任一文件不存在时：

- 立即停止，不得继续任何工作。
- 向用户输出：

```
前置环境未就绪：请确认 (1) 已将 analyzer/common/ 整包覆盖到平台根 common/；(2) 已将 RDC-Agent-Tools 整包覆盖到平台根 tools/；然后再重新发起任务。
```

验证通过后，按顺序阅读：

1. common/AGENT_CORE.md
2. common/config/platform_adapter.json
3. common/skills/rdc-analyst/SKILL.md
4. common/docs/workspace-layout.md

强制规则：

- 平台启动后默认保持普通对话态；只有用户手动召唤 `rdc-analyst`，才进入分析框架
- 除 `rdc-analyst` 之外，其他 specialist 默认都是 internal，只能由 `rdc-analyst` 在框架内分派
- 用户尚未提供可导入的 `.rdc` 时，必须以 `BLOCKED_MISSING_CAPTURE` 停止
- 当前平台的 `coordination_mode = staged_handoff`，`sub_agent_mode = puppet_sub_agents`

运行时工作区固定为平台根目录下的 `workspace/`
