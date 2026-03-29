# Workspace Layout

本文定义 analyzer framework 的 `workspace/` 合同。

## 1. 分层

- `common/` — 共享真相与平台配置
- `workspace/` — case/run 运行区

硬规则：

- 运行期截图、capture、notes、reports 不回写 `common/`（知识库条目除外）
- 共享 spec、role、config 不写进 `workspace/`
- 并行 case 只能共享仓库，不得共享同一条 live `context`

## 2. Case / Run 目录

```text
workspace/
  cases/
    <case_id>/
      case.yaml
      artifacts/
        entry_gate.yaml
      inputs/
        captures/
          manifest.yaml
          <capture>.rdc
      runs/
        <run_id>/
          run.yaml
          capture_refs.yaml
          artifacts/
            intake_gate.yaml
            coverage_board.yaml
            phase1_checkpoint.yaml
            phase2_checkpoint.yaml
            phase3_checkpoint.yaml
            completeness_gate.yaml
            report_compliance.yaml
          logs/
          notes/
            analysis_plan.yaml
          screenshots/
          reports/
            <Project>_RenderAnalysis.md
            <Project>_<Module>_DeepAnalysis.md
            <Project>_ShaderAnalysis.md
```

## 3. Gate Artifact Rules

- `.rdc` 是创建 case 的硬前置；未拿到 `.rdc` 不创建 case/run
- `entry_gate.yaml` 是 case 级 preflight 权威 gate
- `intake_gate.yaml` 是 run 级 accepted intake 权威 gate
- `coverage_board.yaml` 是 run 级分析进度唯一权威 artifact
- `phase{N}_checkpoint.yaml` 是阶段完成验证 artifact
- `completeness_gate.yaml` 是全局覆盖率验证 artifact
- `report_compliance.yaml` 是文档合规验证 artifact

## 4. Write Scope

| Scope | 可写路径 | 角色 |
|-------|---------|------|
| `workspace_control` | case.yaml, case_input.yaml, manifest, run.yaml, capture_refs, analysis_plan, coverage_board | `rdc-analyst` |
| `workspace_notes` | artifacts/**, notes/**, screenshots/** | specialists |
| `workspace_reports` | reports/** | `report_curator` |
| `session_artifacts` | common/knowledge/library/sessions/** | `report_curator` |
| `knowledge_library` | common/knowledge/library/** | `report_curator` |
