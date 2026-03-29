---
inclusion: auto
---

# Kiro Project Rules — Analyzer

## Identity

- 项目：RenderDoc/RDC Render Analysis Framework
- 平台：Kiro
- 目标：使用 RenderDoc/RDC platform tools 分析渲染管线结构、逆向 Shader 算法、追踪资源生命周期

## Required Reads

1. `AGENTS.md`
2. `common/AGENT_CORE.md`
3. `common/config/platform_adapter.json`
4. `common/docs/workspace-layout.md`

## Hard Rules

- 平台启动后默认保持普通对话态；只有用户手动召唤 `rdc-analyst`，才进入分析框架
- 除 `rdc-analyst` 之外，其他 specialist 默认都是 internal，只能由 `rdc-analyst` 在框架内分派
- 进入平台真相相关工作前，必须先校验 `tools/` 存在
- 用户未提供至少一份可导入的 `.rdc` 前，必须以 `BLOCKED_MISSING_CAPTURE` 直接阻断
- 分析粒度（coarse / detailed / focused）必须在 intake 阶段确认

## Workspace

- 运行区固定为 `workspace/`，按 `cases/<case_id>/runs/<run_id>/` 组织
- 结案时以 `artifacts/report_compliance.yaml(status=passed)` 作为统一合规裁决
