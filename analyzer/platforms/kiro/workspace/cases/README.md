# `workspace/cases/` 占位说明

当前目录用于承载运行时 case。

目录约定：

```text
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
```

规则：

- `.rdc` 是创建 case 的硬前置条件
- 用户只负责提供 `.rdc`；intake 通过后由 Agent 导入到 `inputs/captures/`
