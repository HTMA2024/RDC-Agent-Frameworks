# Common Copy Contract

此目录必须放置从根目录 `debugger/common/` 复制来的共享运行时内容。

使用方式：

1. 将根目录 `debugger/common/` 整体复制到当前模板根的 `common/`。
2. 通过 `common/AGENT_CORE.md`、`common/agents/*.md`、`common/skills/renderdoc-rdc-gpu-debug/SKILL.md` 与 `common/docs/*.md` 进入共享运行时文档。

注意：

- 当前平台目录只是宿主薄包装模板，不是自包含运行包。
- Agent 的目标始终是使用 RenderDoc/RDC platform tools 调试 GPU 渲染问题。
