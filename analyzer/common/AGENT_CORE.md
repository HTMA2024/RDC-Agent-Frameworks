# RenderDoc/RDC Render Analysis Agent Core（框架核心约束）

本文件是 `RenderDoc/RDC Render Analysis` framework 的全局约束入口。

职责边界：

- `RDC-Agent Tools` 负责平台真相：tool catalog、共享响应契约、runtime 生命周期、context/session/remote/event 语义与错误面。
- 本文件只负责 framework 如何消费这些平台真相，不重新定义平台语义。
- 角色职责正文以 `common/agents/*.md` 为准；平台适配物只允许改宿主入口、frontmatter 与少量宿主接入说明。

## 1. Framework 与 Tools 的边界

以下内容必须回到已解析的 `RDC-Agent Tools` 判定：

- `rd.*` tools 的能力面与参数语义
- 共享响应契约
- `.rdc -> capture_file_id -> session_id -> frame/event context` 的最小状态链路
- `context`、daemon、artifact、context snapshot 的平台语义
- `spec/runtime_mode_truth.json` 对应的 transport/runtime 模式真相
- 错误分类与恢复面

以下内容属于 framework：

- 角色拓扑与协作关系
- intake、粒度确认、分派、阶段推进与质量门
- `analysis_plan.yaml`、`coverage_board.yaml` 的合同
- workspace、artifact/gate 的硬约束
- 两层文档结构（L1/L2）的产物定义

## 2. Mandatory Intent Gate

所有进入 `analyzer` 的正式请求，在做 analyzer-specific preflight、capture intake、case/run 初始化与 specialist 分派之前，必须先由 `rdc-analyst` 执行 `intent_gate`。

硬规则：

- `rdc-analyst` 是唯一 framework classifier。
- specialist 不得重做 framework 判定。
- `intent_gate` 只能由主入口 LLM 按显式 rubric 执行。
- 若任务主要在问"为什么渲染错了"且有明确 bug 症状，必须 reject + redirect 到 `rdc-debugger`。
- 若任务主要在问性能、预算、瓶颈、收益，必须 reject + redirect 到 `rdc-optimizer`。
- ambiguity 允许多轮澄清，且多轮期间不创建 case/run。

只有当 `intent_gate.decision=analyst` 时，后续 analyzer-specific preflight、capture、handoff 才允许继续。

## 3. Mandatory Entry Gate

`intent_gate` 通过后，先执行 case 级 `entry_gate`。

硬规则：

- `entry_gate` 固定落盘到 `../workspace/cases/<case_id>/artifacts/entry_gate.yaml`
- 它负责裁决当前平台的 `entry_mode`、capture 是否已提供、分析粒度是否已确认
- `entry_gate` 未通过时，不得进入 accepted intake，不得创建 `run_id`，也不得进入 live `rd.*`
- `entry_gate` 的阻断码为：
  - `BLOCKED_MISSING_CAPTURE`
  - `BLOCKED_ENTRY_PREFLIGHT`
  - `BLOCKED_L1_MISSING`（focused 模式下找不到已有 L1）

## 4. Formal Workflow State Machine

主流程固定为：

1. `preflight_pending`
2. `intent_gate_passed`
3. `entry_gate_passed`
4. `accepted_intake_initialized`
5. `intake_gate_passed`
6. `phase1_pipeline_overview`
7. `phase1_checkpoint_passed`
8. `phase2_per_pass_analysis`
9. `phase2_checkpoint_passed`
10. `phase3_shader_reverse`
11. `phase3_checkpoint_passed`
12. `phase4_specialized_analysis`
13. `phase4_resource_tracking`
14. `completeness_gate_passed`
15. `report_generation`
16. `finalized`

粒度缩减规则：

- coarse：1 → 7 → 16（跳过 8-15）
- detailed：1 → 16（全部执行）
- focused：检查 L1 存在 → 8 → 16（从 Phase 2 开始，仅针对指定模块）

硬规则：

- 阶段切换必须可审计地写入 `coverage_board.yaml`
- 无 `phase1_checkpoint` 不进 Phase 2
- 无 `phase2_checkpoint` 不进 Phase 3
- 无 `phase3_checkpoint` 不进 Phase 4
- 无 `completeness_gate` 不进 report generation
- 无 `report_compliance` 不算 finalized

## 5. Mandatory Setup Verification

所有需要平台真相的工作在开始前，必须先验证以下两项均已就绪：

**检查 1：`common/` 已正确覆盖**

- 验证 `common/AGENT_CORE.md` 是否存在。
- 不存在则说明 `common/` 仍是占位目录。

**检查 2：`tools/` 已正确覆盖**

- 验证 `tools/spec/tool_catalog.json` 是否存在。
- 不存在则说明 `tools/` 仍是占位目录。

任一项不存在时：

- 立即停止，不得继续任何工作。
- 向用户输出缺失项与补齐动作。

## 6. Write Scope 边界

| Scope | 可写路径 |
|-------|---------|
| `workspace_control` | `case.yaml`, `case_input.yaml`, `inputs/captures/manifest.yaml`, `run.yaml`, `capture_refs.yaml`, `notes/analysis_plan.yaml`, `artifacts/coverage_board.yaml` |
| `workspace_notes` | `runs/<run_id>/artifacts/**`, `runs/<run_id>/notes/**`, `runs/<run_id>/screenshots/**` |
| `workspace_reports` | `reports/<Project>_RenderAnalysis.md`, `reports/<Project>_*_DeepAnalysis.md`, `reports/<Project>_ShaderAnalysis.md` |
| `session_artifacts` | `common/knowledge/library/sessions/<session_id>/**` |
| `knowledge_library` | `common/knowledge/library/**` |

角色边界：

- `rdc-analyst` 只写 `workspace_control`
- specialists 只写 `workspace_notes`
- `report_curator` 只写 `workspace_reports`、`session_artifacts` 与 `knowledge_library`
