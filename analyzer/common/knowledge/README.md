# Analyzer Knowledge Store

## 目录结构

- `library/sessions/<session_id>/` — 分析会话产物
  - `analysis_evidence.yaml` — 分析过程的结构化证据
  - `pass_graph.yaml` — Pass 依赖图
  - `resource_map.yaml` — 资源生命周期映射
  - `shader_fingerprints.yaml` — Shader 算法指纹库
  - `technique_registry.yaml` — 已识别的渲染技术注册表
- `templates/` — 文档模板
- `spec/` — 分析规范

## 知识共享

Debugger 可以消费 Analyst 产出的知识条目：
- `pass_graph.yaml` → debugger 的 pass_graph_pipeline agent 可复用 Pass 结构
- `shader_fingerprints.yaml` → debugger 的 shader_ir agent 可用指纹库定位已知算法
- `technique_registry.yaml` → debugger 的 triage_agent 可用技术栈辅助分类
