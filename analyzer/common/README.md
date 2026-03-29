# Analyzer Shared Common

`analyzer/common/` 是 `analyzer` framework 的共享运行时真相目录。

## 目录职责

- `AGENT_CORE.md`：framework 的硬约束与运行原则。
- `agents/`：角色正文与分工定义。
- `config/`：平台能力、model routing、binding 与 role policy 的唯一配置真相。
- `docs/`：共享运行时文档入口。
- `hooks/`：共享 gate、validator 与 runtime audit 逻辑。
- `knowledge/`：共享知识真相、spec store 与 session/library 结构。
- `project_plugin/`：项目特定的渲染管线结构与命名规范。
- `skills/`：共享 skill 正文。

## 使用要求

- 平台模板阶段的 `platforms/<platform>/common/README.md` 只是占位说明，不是运行时正文。
- 完成覆盖后，平台根目录 `common/README.md` 必须是当前文件。
- 平台内所有 agent、skill、hook、config 只允许引用当前平台根目录的 `common/`，不得跨级回指仓库源码。
