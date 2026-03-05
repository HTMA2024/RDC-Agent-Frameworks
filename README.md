# RDC-Agent Frameworks

本仓库包含多个面向 RenderDoc/RDC 工作流的 Agent 框架实现与骨架，用于将复杂工程任务拆解为可复用、可审计、可演进的多 Agent 协作流程。

## 目录

- `debug-agent/`：AIRD（AI-Driven Invariant-Reasoning Debugger），面向 GPU 渲染 Bug 的多 Agent 调试框架。
  - 入口：`debug-agent/README.md`
- `reverse-agent/`：Reverse Agent（骨架），面向逆向/还原（Reverse / Reconstruction）类任务的多 Agent 框架占位。
  - 入口：`reverse-agent/README.md`
- `optimization-agent/`：Optimization Agent（骨架），面向性能/质量/成本优化类任务的多 Agent 框架占位。
  - 入口：`optimization-agent/README.md`

## 约定（对齐 debug-agent 的关键原则）

- 将平台/工具的适配层与平台无关的核心 Prompt 分离；优先建立单一真相来源（SSOT）。
- 保持目录结构清晰可扩展：核心定义、平台适配、知识库/产物、质量门槛/校验等分层组织。