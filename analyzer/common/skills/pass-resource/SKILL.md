# 角色技能包装说明

当前文件是 analyzer framework 的 role skill 入口。

该角色默认是 internal specialist。平台启动后不会自动进入该角色；只有用户手动召唤 `rdc-analyst` 并由它分派时，才进入当前 role。

先阅读：

1. common/skills/rdc-analyst/SKILL.md
2. common/skills/pass-resource/SKILL.md
3. common/agents/03_pass_resource.md

当前平台的 `coordination_mode = staged_handoff`，`sub_agent_mode = puppet_sub_agents`。

未先将顶层 `analyzer/common/` 拷入当前平台根目录的 `common/` 之前，不允许在宿主中使用当前平台模板。
运行时 case/run 现场与报告统一写入平台根目录下的 `workspace/`
