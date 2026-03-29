# Kiro Template（平台模板）— Analyzer

当前目录是 Kiro 的 analyzer platform-local 模板。Agent 的目标是使用 RenderDoc/RDC platform tools 分析渲染管线结构、逆向 Shader 算法、追踪资源生命周期并输出结构化分析文档。

## 入口规则

- 当前宿主支持 native steering、skills、hooks 与 MCP，但平台启动后默认保持普通对话态；只有用户手动召唤 `rdc-analyst`，才进入分析框架。
- 当前宿主可直接访问本地进程、文件系统与 workspace，默认采用 local-first。
- 默认入口是 daemon-backed CLI；只有用户明确要求按 MCP 接入时，才切换到 MCP。
- 任务开始时，Agent 必须向用户说明当前采用的是 CLI 还是 MCP。
- 若用户要求 MCP，但宿主未配置对应 MCP server，必须直接阻断并提示配置。
- 当前模板默认不预注册 MCP；若要启用，使用 `.kiro/settings/mcp.opt-in.json` 的示例配置显式接入。

## 使用方式

1. 将仓库根目录 `analyzer/common/` 整体拷贝到当前平台根目录的 `common/`，覆盖占位内容。
2. 将 RDC-Agent-Tools 根目录整包拷贝到当前平台根目录的 `tools/`，覆盖占位内容。
3. 确认 `tools/` 下存在 `validation.required_paths` 列出的必需文件。
4. 正式发起分析前，用户必须先提供至少一份 `.rdc`。
5. 使用当前平台根目录下的 `workspace/` 作为运行区。
6. 完成覆盖后，再在 Kiro 中打开当前平台根目录。
7. 平台启动后默认保持普通对话态；只有用户手动召唤 `rdc-analyst`，才进入分析框架。

## 约束

- `common/` 默认只保留一个占位文件；正式共享正文仍由顶层 `analyzer/common/` 提供。
- 未完成 `analyzer/common/` 覆盖前，当前平台模板不可用。
- 未完成 `analyzer/common/` 覆盖、`tools/` 覆盖前，Agent 必须拒绝执行依赖平台真相的工作。
- 未提供可导入的 `.rdc` 时，Agent 必须以 `BLOCKED_MISSING_CAPTURE` 直接阻断。
- 当前平台的 `coordination_mode = staged_handoff`，`sub_agent_mode = puppet_sub_agents`。
