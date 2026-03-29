# 平台本地 `workspace/` 占位说明

当前目录是平台本地 `workspace/` 运行区骨架。

用途：

- 存放通过 `rdc-analyst` intake 之后的 `case_id/run_id` 级运行现场
- 承载 case 级 `inputs/captures/`、run 级 `artifacts/`、`notes/`、`screenshots/`
- 承载分析报告 `reports/<Project>_RenderAnalysis.md` 与 `reports/<Project>_*_DeepAnalysis.md`

约束：

- `workspace/` 是 Agent 运行区，不要求用户手工把 `.rdc` 预放到这里。
- 导入后的原始 `.rdc` 只允许落在 `cases/<case_id>/inputs/captures/`。
- 模板仓库只保留占位骨架，不提交真实运行产物。
