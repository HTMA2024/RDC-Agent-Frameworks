# 平台本地 `tools/` 占位说明

当前目录是平台本地 `tools/` 的最小占位目录，不是正式运行时内容。

使用方式：

1. 将 RDC-Agent-Tools 根目录整包拷贝到该平台根目录的 `tools/`，覆盖当前目录。
2. 完成覆盖后，再在对应宿主中打开该平台根目录使用。

约束：

- `tools/` 只表示 source payload；live runtime 由 daemon-owned worker 物化。
- 未完成覆盖前，当前平台模板不可用。
