# Analyzer Shared Common

`analyzer/common/` 是 `analyzer` framework 的最小 shared common 骨架。

当前 `analyzer` 仍是 `incubating`，所以这里只建立 framework-local SSOT 起点，不建立完整的平台模板、hooks 或 runtime contract。

## 当前目录职责

- `skills/rdc-analyst/`：`analyzer` 的 public main skill。

## 当前边界

- 不引用 `debugger/common/` 作为 analyzer 规则来源。
- 不把当前目录误写成已完成的 GA 运行时 common。
