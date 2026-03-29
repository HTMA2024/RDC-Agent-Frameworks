# RDC-Analyst 设计框架（Draft v3）

> 状态：待最终确认
> 基于：Reference/hpwater-render-analysis + debugger framework 组织方式
> v2 变更：三级分析粒度、两层文档结构、多 capture 对比延后、知识共享确认、自动验证确认
> v3 变更：补充 Write Scope 定义、错误处理策略、明确 coarse 模式 L1 不含资源总览

---

## 1. 定位与边界

### 1.1 Analyst 是什么

Analyst 的使命是**从一份或多份 .rdc capture 中，系统化地重建渲染管线结构、追踪资源生命周期、逆向关键 Shader 算法，并输出结构化的分析文档与可复用的知识库条目**。

核心价值：把未知的渲染系统变成可解释、可检索、可复用的结构化知识。

### 1.2 Analyst 不是什么

| 不做 | 由谁做 |
|------|--------|
| 找 Bug、定根因、验修复 | `rdc-debugger` |
| 性能分析、瓶颈归因、优化实验 | `rdc-optimizer` |
| 修改 Shader、apply patch | `rdc-debugger` 的 patch engine |
| 替代 RenderDoc UI 做实时交互 | 人类 + qrenderdoc |

### 1.3 与 Debugger 的关键差异

| 维度 | Debugger | Analyst |
|------|----------|---------|
| 目标 | 找到根因并验证修复 | 理解系统并沉淀知识 |
| 核心产物 | BugCard + fix_verification | 结构化分析文档 + 知识库条目 |
| 状态追踪 | hypothesis_board（假设板） | coverage_board（覆盖率板） |
| 质量门 | skeptic 对抗审查 + fix verification | completeness gate + 文档结构验证 |
| 因果链 | causal_anchor → root_expression | 无因果归因，只做结构描述 |
| A/B 语义 | A/B 是证据方法 | A/B 是对比分析主体（v2 feature，当前不实现） |

---

## 2. 三级分析粒度

用户发起分析时，`rdc-analyst` 先确认分析粒度：

### 2.1 粗粒度分析（coarse）

- 执行范围：Phase 1 only
- 产物：L1 整体架构文档
- 用途：快速理解渲染管线全貌，作为后续专项分析的基础
- 典型场景："帮我看看这个截帧的渲染管线长什么样"

### 2.2 细粒度全量分析（detailed）

- 执行范围：Phase 1 + Phase 2 + Phase 3 + Phase 4（所有模块）
- 产物：L1 整体架构文档 + 所有模块的 L2 深入分析文档
- 用途：完整逆向整个渲染管线
- 典型场景："帮我完整分析这个截帧的所有渲染技术"

### 2.3 专项模块分析（focused）

- 前置条件：同一 capture 必须已有 coarse 分析结果（L1 文档）
- 执行范围：在已有 L1 基础上，对指定模块执行 Phase 2 + Phase 3 + Phase 4
- 产物：指定模块的 L2 深入分析文档
- 典型场景："我之前分析过整体架构了，现在帮我深入分析水体渲染部分"

### 2.4 粒度选择流程

```
用户发起分析请求
    │
    ▼
rdc-analyst 询问分析粒度（若用户未指定）
    │
    ├── coarse → 执行 Phase 1 → 输出 L1
    │
    ├── detailed → 执行 Phase 1+2+3+4 → 输出 L1 + 所有 L2
    │
    └── focused → 检查是否有 L1
                    │
                    ├── 有 L1 → 复用 L1，对指定模块执行 Phase 2+3+4 → 输出 L2
                    │
                    └── 无 L1 → 先执行 Phase 1 生成 L1，再对指定模块执行 Phase 2+3+4
```

---

## 3. 两层文档结构

### 3.1 L1：整体架构文档

文件名：`<Project>_RenderAnalysis.md`

```markdown
# <Project> 截帧渲染分析

> 截帧文件：<filename>.rdc
> 图形 API：<API>
> 帧统计：N actions / M draw calls / K dispatches / T textures / B buffers
> 渲染分辨率：WxH
> 引擎类型：<如可识别>
> 分析粒度：coarse / detailed

## 1. 整体图形架构
  - 渲染管线架构流程图（ASCII / Mermaid）
  - 帧级统计摘要

## 2. Pass 分组与渲染流程
  - 全部 Marker Pass 功能映射表（名称、类型、子 Action 数、功能推测、渲染阶段归类）
  - 渲染阶段归类表（预处理/几何/光照/后处理/合成）

## 3. 逐 Pass 概要
  - 每个 Pass 的一段话概要（功能、RT 数量、子 Action 数）
  - [仅 detailed/focused] 链接到对应的 L2 深入分析

## 4. 模块索引
  - 已识别的渲染模块列表（水体、后处理、光照、阴影等）
  - 每个模块关联的 Pass 列表
  - [仅 detailed/focused] 链接到对应的 L2 深入分析

## 5. 技术关键词索引
  - 所有已识别的渲染技术关键词（基于 Pass 名称和类型的初步推测）

## 6. Pass 覆盖率检查表
  - 全部 Marker Pass 的分析状态（coarse 下全部标记为"概要完成"）
```

注意：coarse 模式的 L1 不包含"纹理资源总览"和"Buffer 资源总览"章节。这两个章节需要 Phase 2 的逐 Pass 资源绑定分析才能准确填充。coarse 只做 Phase 1（帧统计 + Pass 映射 + 架构流程图），不深入到资源级别。

纹理/Buffer 总览在以下情况出现：
- detailed 模式：作为 L1 的补充章节，在 Phase 4 resource_tracker 完成后回填
- focused 模式：仅在 L2 的"资源追踪"章节中出现，限定在目标模块范围内

### 3.2 L2：模块深入分析文档

文件名：`<Project>_<Module>_DeepAnalysis.md`

例如：`HPWater_Water_DeepAnalysis.md`、`HPWater_PostProcess_DeepAnalysis.md`

```markdown
# <Project> <Module> 深入分析

> 关联整体分析：<Project>_RenderAnalysis.md
> 分析模块：<Module>
> 关联 Pass：<Pass 列表>

## 1. 模块概述
  - 模块在整体管线中的位置
  - 关联的 Pass 列表与执行顺序

## 2. 逐 Pass 详细分析
  - 每个关联 Pass 的完整分析：
    - RT 配置表
    - 纹理输入表
    - CB 绑定表
    - 管线状态（深度/模板/混合/光栅化）
    - Shader 信息表
    - [Compute Pass] 逐 Dispatch 分析表
    - [子 Action > 10] 功能子组划分

## 3. Shader 逆向分析
  - 关键 Shader 反汇编与伪代码重建
  - 标准算法识别与标注
  - CB 偏移量 → 变量名映射

## 4. 专项技术分析
  - 模块特定的技术深入（如水体：几何生成、着色模型、反射/折射、Compute 模拟等）
  - 技术完整流程图

## 5. 资源追踪
  - 模块内纹理资源表（ResourceId、格式、分辨率、Mip 数、首次写入 Pass、读取 Pass 列表、推测用途）
  - 模块内 Buffer 资源表（ResourceId、大小、类型、推测用途）
  - 跨模块资源依赖（本模块消费了哪些上游模块的输出）
  - 读写冲突检测（同时作为 SRV 和 UAV 的资源标记）
```

### 3.3 文档间关系

```
L1: <Project>_RenderAnalysis.md（coarse = 6 章节）
  │
  │  [detailed 模式额外回填]
  │  ├── 附录 A：纹理资源总览（Phase 4 resource_tracker 完成后回填）
  │  └── 附录 B：Buffer 资源总览（Phase 4 resource_tracker 完成后回填）
  │
  ├── 链接 → L2: <Project>_Water_DeepAnalysis.md
  ├── 链接 → L2: <Project>_PostProcess_DeepAnalysis.md
  ├── 链接 → L2: <Project>_Lighting_DeepAnalysis.md
  └── 链接 → L2: <Project>_Shadow_DeepAnalysis.md
```

细粒度全量分析 = L1（含资源附录）+ 所有已识别模块的 L2
专项分析 = 复用已有 L1 + 指定模块的 L2（资源追踪限定在模块范围内）

---

## 4. 四阶段工作流

### 4.1 阶段定义

```
Phase 1: Pipeline Overview（全局概览）— 所有粒度都执行
  ├── 帧统计获取
  ├── Action 树构建 + Pass 功能映射
  ├── 渲染阶段归类 + 模块识别
  └── 架构流程图生成
  → 产物：L1 文档

Phase 2: Per-Pass Deep Analysis（逐 Pass 深入分析）— detailed / focused
  ├── 管线状态查询（RT/纹理/CB/深度/混合/光栅化）
  ├── Compute Dispatch 逐一分析
  ├── 大型 Pass 功能子组划分
  └── 阶段检查点验证
  → 产物：L2 文档的"逐 Pass 详细分析"章节

Phase 3: Shader Reverse Engineering（Shader 逆向分析）— detailed / focused
  ├── 关键 Shader 识别与反汇编
  ├── 算法逆向 + 伪代码重建
  ├── CB 偏移量 → 变量名映射
  └── 标准图形学算法标注
  → 产物：L2 文档的"Shader 逆向分析"章节

Phase 4: Specialized Analysis & Documentation（专项分析与文档输出）— detailed / focused
  ├── 专项技术深入（按模块动态选择）
  ├── 资源全局追踪表
  ├── 文档生成 + 覆盖率验证
  └── 知识库条目沉淀
  → 产物：L2 文档的"专项技术分析"和"资源追踪"章节
```

### 4.2 Formal Workflow State Machine

```
1.  preflight_pending
2.  intent_gate_passed
3.  entry_gate_passed
4.  accepted_intake_initialized
5.  intake_gate_passed
6.  phase1_pipeline_overview
7.  phase1_checkpoint_passed          ← coarse 模式到此结束
8.  phase2_per_pass_analysis
9.  phase2_checkpoint_passed
10. phase3_shader_reverse
11. phase3_checkpoint_passed
12. phase4_specialized_analysis
13. phase4_resource_tracking
14. completeness_gate_passed
15. report_generation
16. finalized
```

coarse 模式：1 → 7 → 16（跳过 8-15）
detailed 模式：1 → 16（全部执行）
focused 模式：检查 L1 存在 → 8 → 16（从 Phase 2 开始，仅针对指定模块）

---

## 5. 角色体系

### 5.1 角色总览

| 编号 | Agent ID | 角色名 | 职责 | 对标 Debugger |
|------|----------|--------|------|--------------|
| 01 | `rdc-analyst` | 主入口/编排者 | intent gate、intake、粒度确认、阶段编排、质量门 | `rdc-debugger` |
| 02 | `pipeline_overview` | 渲染管线概览专家 | Phase 1：帧统计、Pass 映射、模块识别、架构流程图 | `triage_agent` |
| 03 | `pass_resource` | Pass 资源绑定分析专家 | Phase 2：逐 Pass 管线状态、RT/纹理/CB/Compute | `pass_graph_pipeline` |
| 04 | `shader_reverse` | Shader 逆向分析专家 | Phase 3：反汇编、算法逆向、伪代码重建 | `shader_ir` |
| 05 | `resource_tracker` | 资源生命周期追踪专家 | Phase 4a：纹理/Buffer 全局追踪、读写冲突检测 | 新角色 |
| 06 | `technique_analyst` | 专项技术分析专家 | Phase 4b：按模块动态配置的专项深入分析 | 新角色 |
| 07 | `report_curator` | 文档生成与知识沉淀专家 | L1/L2 文档输出、知识库条目、覆盖率验证 | `report_knowledge_curator` |

### 5.2 角色间数据流

```
用户请求 + .rdc
    │
    ▼
rdc-analyst（intent gate + intake + 粒度确认 + 编排）
    │
    ▼
pipeline_overview ──→ L1 文档（Pass 映射 + 架构流程图 + 模块识别）
    │                      │
    │              [coarse 到此结束]
    │                      │
    ▼                      ▼
pass_resource ──→ 逐 Pass 资源绑定表 + Compute 分析
    │                      │
    ▼                      ▼
shader_reverse ──→ 关键 Shader 伪代码 + 算法识别
    │                      │
    ├──→ resource_tracker ──→ 纹理/Buffer 全局追踪表
    │
    ├──→ technique_analyst ──→ 模块级专项技术分析
    │
    ▼
report_curator ──→ L2 文档 + 知识库条目
```

### 5.3 technique_analyst 的动态配置

`technique_analyst` 是一个通用角色，通过 `analysis_plan.specializations` 动态配置分析内容：

```yaml
# analysis_plan.yaml 中的 specializations 示例
specializations:
  - module: water
    focus: [geometry_generation, shading_model, reflection, refraction, compute_simulation, caustics, foam]
    related_passes: ["Compute Pass #1", "Compute Pass #2", "Colour Pass #2", "Colour Pass #3"]

  - module: post_process
    focus: [tone_mapping, bloom, color_grading, fxaa, sharpening]
    related_passes: ["Compute Pass #4", "Compute Pass #5", "Compute Pass #6", "Compute Pass #7", "Colour Pass #4"]
```

模块类型不是固定枚举，而是由 Phase 1 的 pipeline_overview 根据 Pass 功能映射自动识别 + 用户指定的组合。

---

## 6. 主入口 rdc-analyst 设计

### 6.1 Intent Gate

与 debugger 共享同一套评分维度（在 `rdc-debugger` 的 intent gate 中已定义），但方向相反：

**analyst 正向信号**：
- `+4` 主要目标是"理解这个截帧的渲染管线"
- `+4` 主要目标是 pass graph / dependency / module abstraction / knowledge extraction
- `+4` 主要目标是 Shader 逆向 / 算法识别（不以修 bug 为目的）
- `+3` 主要目标是重建结构、归纳模式、沉淀知识
- `+3` 主要目标是 compare / diff / A-B 差异解释（v2 feature）

**analyst 负向信号**：
- `-4` 明确要求 root-cause verdict 或 fix verdict
- `-3` 明确要求 causal_anchor
- `-4` 明确要求性能优化 / 瓶颈归因

**硬排除**：
- 若任务主要在问"为什么渲染错了"且有明确的 bug 症状 → 转 `rdc-debugger`
- 若任务主要在问性能/预算/瓶颈 → 转 `rdc-optimizer`

### 6.2 Intake 要求

必须确认：
- 至少一份 `.rdc`（硬前置，缺失时 `BLOCKED_MISSING_CAPTURE`）
- 分析粒度（coarse / detailed / focused）
- [focused] 指定模块名称
- [focused] 检查同一 capture 是否已有 L1 分析结果

可选输入：
- 引擎/材质约定（若已知）
- 资源命名规则
- 已知模块线索
- 参考基准文档（格式参考）

### 6.3 Workspace 结构

```
workspace/
  cases/
    <case_id>/
      case.yaml
      inputs/
        captures/
          manifest.yaml
          <capture_id>.rdc
      runs/
        <run_id>/
          run.yaml
          capture_refs.yaml
          artifacts/
            entry_gate.yaml
            intake_gate.yaml
            coverage_board.yaml
            phase1_checkpoint.yaml
            phase2_checkpoint.yaml       # detailed / focused only
            phase3_checkpoint.yaml       # detailed / focused only
            completeness_gate.yaml       # detailed / focused only
            report_compliance.yaml
          logs/
          notes/
            analysis_plan.yaml
          reports/
            <Project>_RenderAnalysis.md                  # L1（所有模式）
            <Project>_<Module>_DeepAnalysis.md            # L2（detailed / focused）
            <Project>_ShaderAnalysis.md                   # Shader 汇总（detailed only，可选）
```

### 6.4 Coverage Board

```yaml
# coverage_board.yaml
case_id: <case_id>
run_id: <run_id>
analysis_mode: coarse | detailed | focused
focused_modules: []              # focused 模式下指定的模块列表

capture_summary:
  api: D3D11
  total_actions: 438
  draw_calls: 294
  dispatches: 92
  textures: 124
  buffers: 139
  marker_passes: 14

pass_coverage:
  - pass_name: "Depth-only Pass #1"
    l1_done: true                # Phase 1 概要
    l2_done: false               # Phase 2+3+4 深入
  # ... 全部 Pass

module_coverage:
  - module: water
    identified: true
    l2_done: false
    related_passes: ["Compute Pass #1", "Compute Pass #2"]
  - module: post_process
    identified: true
    l2_done: false
    related_passes: ["Compute Pass #4", "Compute Pass #5"]

action_coverage:
  total: 438
  analyzed: 0
  percentage: 0.0%

current_phase: phase1_pipeline_overview
current_task: "获取帧统计信息"
active_owner: pipeline_overview
last_updated: "2026-03-29T10:00:00Z"
```

---

## 7. 质量门体系

所有 gate 均为自动验证，不需要人工确认。

### 7.1 Gate 总览

| Gate | 时机 | 检查内容 | 失败行为 |
|------|------|---------|---------|
| `entry_gate` | intake 后 | .rdc 存在、分析粒度已确认、入口模式确认 | 阻断，不创建 case/run |
| `intake_gate` | case/run 创建后 | capture 已导入、analysis_plan 已写出 | 阻断，不进入 Phase 1 |
| `phase1_checkpoint` | Phase 1 完成后 | 全部 Marker Pass 已识别、架构流程图已生成、L1 文档已写出 | 阻断，不进入 Phase 2 |
| `phase2_checkpoint` | Phase 2 完成后 | 目标 Pass 的 RT/纹理/CB/管线状态已记录 | 阻断，不进入 Phase 3 |
| `phase3_checkpoint` | Phase 3 完成后 | 关键 Shader 已反汇编、核心算法已识别 | 阻断，不进入 Phase 4 |
| `completeness_gate` | Phase 4 完成后 | Action 覆盖率达标、文档结构完整 | 阻断，不进入 report generation |
| `report_compliance` | 报告生成后 | 文档包含全部必需章节、表格格式正确 | 阻断，不算 finalized |

### 7.2 按粒度的 Gate 适用性

| Gate | coarse | detailed | focused |
|------|--------|----------|---------|
| entry_gate | ✓ | ✓ | ✓ |
| intake_gate | ✓ | ✓ | ✓ |
| phase1_checkpoint | ✓ | ✓ | ✓（检查 L1 已存在） |
| phase2_checkpoint | — | ✓ | ✓ |
| phase3_checkpoint | — | ✓ | ✓ |
| completeness_gate | — | ✓ | ✓（仅检查目标模块） |
| report_compliance | ✓（仅 L1） | ✓（L1 + 所有 L2） | ✓（L2） |

---

## 8. Write Scope 定义

### 8.1 Scope 分类

| Scope | 可写路径 | 说明 |
|-------|---------|------|
| `workspace_control` | `case.yaml`, `case_input.yaml`, `inputs/captures/manifest.yaml`, `run.yaml`, `capture_refs.yaml`, `notes/analysis_plan.yaml`, `artifacts/coverage_board.yaml` | 主入口编排者专属 |
| `workspace_notes` | `runs/<run_id>/artifacts/**`, `runs/<run_id>/notes/**`, `runs/<run_id>/screenshots/**` | specialist 工作产物 |
| `workspace_reports` | `reports/<Project>_RenderAnalysis.md`, `reports/<Project>_*_DeepAnalysis.md`, `reports/<Project>_ShaderAnalysis.md` | 文档生成专属 |
| `session_artifacts` | `common/knowledge/library/sessions/<session_id>/analysis_evidence.yaml`, `common/knowledge/library/sessions/<session_id>/action_chain.jsonl` | 分析证据沉淀 |
| `knowledge_library` | `common/knowledge/library/**` | 知识库条目写入 |

### 8.2 角色 → Scope 映射

| 角色 | 可写 Scope |
|------|-----------|
| `rdc-analyst` | `workspace_control` |
| `pipeline_overview` | `workspace_notes` |
| `pass_resource` | `workspace_notes` |
| `shader_reverse` | `workspace_notes` |
| `resource_tracker` | `workspace_notes` |
| `technique_analyst` | `workspace_notes` |
| `report_curator` | `workspace_reports`, `session_artifacts`, `knowledge_library` |

硬规则：
- `rdc-analyst` 不写分析内容，只写控制文件（case/run/plan/coverage）
- specialist 只写 `workspace_notes`，不碰控制文件和报告
- `report_curator` 是唯一能写最终报告和知识库的角色
- 任何角色都不得反向改写 `common/config/` 或 `common/agents/`

---

## 9. 错误处理策略

### 9.1 rd.* 工具调用错误

| 错误场景 | 处理策略 |
|---------|---------|
| `rd.event.get_actions` 返回空 | 确认 capture 已正确加载，检查 session 状态；若仍失败，标记 `BLOCKED_TOOL_FAILURE` 并在 coverage_board 记录 |
| `rd.pipeline.get_state` 对某个 Event ID 失败 | 记录该 Event ID 为不可查询，尝试相邻 Event ID；在 L2 文档中标注"该 Action 管线状态不可查询" |
| `rd.shader.get_source` / `rd.shader.get_disassembly` 返回空 | 可能是 Clear/Copy 操作无 Shader；在文档中标注为"非 Shader Action"，不算分析遗漏 |
| `rd.resource.get_info` 对某个 ResourceId 失败 | 可能是已释放的临时资源；在文档中标注为"不可查询资源"，纹理/Buffer 总表中保留条目但标记状态 |
| MCP 连接失败 / 工具超时 | 重试一次；若仍失败则跳过该查询，在文档中标注，并在 coverage_board 中记录为 `tool_error` |

### 9.2 数据不一致

| 错误场景 | 处理策略 |
|---------|---------|
| Pass 子 Action 数与 `rd.event.get_actions` 返回不一致 | 以 `rd.event.get_actions` 的实际数据为准，在文档中标注差异 |
| 纹理 ResourceId 在不同 Pass 中格式不同 | 可能是资源重用/别名；记录所有观察到的格式并标注 |
| Shader ResourceId 在多个 Pass 中出现但管线状态不同 | 分别记录每种配置，标注为同一 Shader 的不同使用场景 |
| Compute Dispatch 维度为 0 | 可能是 Indirect Dispatch；记录为"GPU 端决定的 Dispatch 维度" |

### 9.3 文档输出错误

| 错误场景 | 处理策略 |
|---------|---------|
| L2 文档过长（>5000 行） | 将 Shader 详细分析拆分到独立的 `<Project>_ShaderAnalysis.md` |
| 表格列数不一致 | 使用固定模板确保所有表格列数统一 |
| Mermaid 图表语法错误 | 回退到 ASCII 流程图 |
| 中文/英文混排格式问题 | 技术术语保留英文，描述性文字使用中文 |

### 9.4 阶段性阻断

| 阻断码 | 触发条件 | 恢复方式 |
|--------|---------|---------|
| `BLOCKED_MISSING_CAPTURE` | 未提供 .rdc | 用户提供 .rdc 后重新 intake |
| `BLOCKED_TOOL_FAILURE` | 关键 rd.* 调用持续失败 | 检查 daemon 状态，必要时重启 session |
| `BLOCKED_CHECKPOINT_FAILED` | 阶段检查点未通过 | 补充缺失的分析项后重新验证 |
| `BLOCKED_L1_MISSING` | focused 模式下找不到已有 L1 | 先执行 coarse 生成 L1 |

---

## 10. 知识共享

### 10.1 Analyst 产出的知识条目

分析完成后，沉淀到 `common/knowledge/library/` 的条目：

- `sessions/<session_id>/analysis_evidence.yaml` — 分析过程的结构化证据
- `sessions/<session_id>/pass_graph.yaml` — Pass 依赖图的结构化表示
- `sessions/<session_id>/resource_map.yaml` — 资源生命周期映射
- `sessions/<session_id>/shader_fingerprints.yaml` — Shader 算法指纹库
- `sessions/<session_id>/technique_registry.yaml` — 已识别的渲染技术注册表

### 10.2 Debugger 消费 Analyst 知识

Debugger 可以消费 Analyst 产出的知识条目：

- `pass_graph.yaml` → debugger 的 `pass_graph_pipeline` agent 可以直接复用 Pass 结构，不需要重新构建 Event 树
- `shader_fingerprints.yaml` → debugger 的 `shader_ir` agent 可以用指纹库快速定位已知算法模式
- `technique_registry.yaml` → debugger 的 `triage_agent` 可以用已识别的技术栈辅助症状分类

共享规则：
- 两个 framework 通过 `common/knowledge/library/` 共享知识条目
- 两个 framework 不互相引用对方的 `common/` 配置或 agent 定义
- 知识条目的格式由各自 framework 定义，但 `session_id` 命名空间共享

---

## 11. 与 Tools 层的交互

Analyst 使用的 rd.* tools 子集（按阶段）：

### Phase 1
- `rd.event.get_actions` — 获取完整 Action 树
- `rd.capture.get_frame_info` — 帧统计
- `rd.vfs.ls` / `rd.vfs.tree` — 结构浏览

### Phase 2
- `rd.event.set_active` — 切换到目标 Event
- `rd.pipeline.get_state` / `rd.pipeline.get_state_summary` — 管线状态
- `rd.pipeline.get_output_targets` — RT 配置
- `rd.resource.get_info` — 资源详情
- `rd.resource.get_usage` / `rd.resource.get_history` — 资源使用追踪

### Phase 3
- `rd.shader.get_source` — Shader 源码/反汇编
- `rd.shader.get_disassembly` — 反汇编输出
- `rd.shader.get_reflection` — Shader 反射信息（输入/输出/CB 布局）

### Phase 4
- `rd.export.texture` — 纹理图片导出（用于文档配图）
- `rd.export.screenshot` — RT 截图
- `rd.texture.get_data` — 数值 readback（用于精确数据分析）
- `rd.macro.*` — 高阶分析工作流

---

## 12. 延后决策

### 12.1 多 Capture 对比分析（v2 feature）

当前版本聚焦单 capture 分析。后续如果需要多 capture 对比：
- 在 `rdc-analyst` 主入口加 `comparison_mode`
- 每个 specialist 在自己的维度做 A/B 对比
- 产物增加 `<Project>_Comparison.md` 对比文档

### 12.2 与 Optimizer 的知识共享

Analyst 产出的 pass_graph 和 resource_map 对 Optimizer 同样有价值。
待 Optimizer framework 启动后再定义共享接口。
