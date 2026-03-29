# `RDC Analyst` 主技能包装说明

当前文件是 Kiro 的 public main skill 入口。

平台启动后默认保持普通对话态。只有用户手动召唤 `rdc-analyst`，才进入分析框架。

进入 `rdc-analyst` 后，本 skill 负责：

- `intent_gate`
- 分析粒度确认（coarse / detailed / focused）
- `entry_gate`
- preflight
- capture 导入 + case/run 初始化
- 四阶段工作流编排
- checkpoint / completeness gate / report compliance

本 skill 只引用当前平台根目录的 `common/`：

- common/skills/rdc-analyst/SKILL.md
- common/config/platform_adapter.json

未先将顶层 `analyzer/common/` 拷入当前平台根目录的 `common/` 之前，不允许在宿主中使用当前平台模板。

运行时 case/run 现场与报告统一写入平台根目录下的 `workspace/`
