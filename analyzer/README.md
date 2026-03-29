# Analyzer（分析与重建框架）

## 定位

> 当前状态：`alpha`

Analyzer 的目标不是修 bug，而是**把未知系统结构化为可解释模型**。

它的使命是：从一份或多份 capture 中，重建渲染管线与资源依赖，逆向关键 Shader 算法，并生成可检索的知识库条目（供 Debug/Optimization 复用）。

## 三级分析粒度

- **粗粒度（coarse）**：整体管线框架结构分析，快速概览
- **细粒度全量（detailed）**：整体框架 + 所有模块最细粒度分析
- **专项模块（focused）**：在已有粗粒度基础上，对指定模块做最细粒度分析

## 四阶段工作流

1. **Phase 1: Pipeline Overview** — 帧统计、Pass 功能映射、架构流程图
2. **Phase 2: Per-Pass Deep Analysis** — 逐 Pass 管线状态、资源绑定、Compute 分析
3. **Phase 3: Shader Reverse Engineering** — 反汇编、算法逆向、伪代码重建
4. **Phase 4: Specialized Analysis** — 专项技术深入、资源追踪、文档输出

## 两层文档结构

- **L1**：`<Project>_RenderAnalysis.md` — 整体架构文档
- **L2**：`<Project>_<Module>_DeepAnalysis.md` — 模块深入分析文档

## 角色体系

| Agent | 职责 |
|-------|------|
| `rdc-analyst` | 主入口/编排者 |
| `pipeline_overview` | Phase 1：渲染管线概览 |
| `pass_resource` | Phase 2：逐 Pass 资源绑定分析 |
| `shader_reverse` | Phase 3：Shader 逆向分析 |
| `resource_tracker` | Phase 4a：资源生命周期追踪 |
| `technique_analyst` | Phase 4b：专项技术分析 |
| `report_curator` | 文档生成与知识沉淀 |

## 目录结构

- `common/`：平台无关的核心约束、角色定义、配置与知识库
- `platforms/`：不同宿主的适配层（待建设）
- `DESIGN_DRAFT.md`：设计框架文档

## 当前入口

- `common/skills/rdc-analyst/SKILL.md` — public main skill
- `common/AGENT_CORE.md` — 框架核心约束
