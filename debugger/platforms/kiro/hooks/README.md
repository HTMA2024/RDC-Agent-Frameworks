# Kiro Platform Quality Hooks

Kiro 平台的 RenderDoc/RDC GPU Debug 框架质量门槛 Hooks 系统。

## 概述

Kiro IDE 支持原生 hooks 系统（`.kiro/hooks/`），本实现通过以下方式实现质量门槛检查：

1. **`.kiro/hooks/*.json`** - Kiro 原生 hook 定义，支持 preToolUse / postToolUse 事件
2. **验证脚本** - 包装了 common/hooks 中的验证器
3. **工具脚本** - 提供 Kiro 特定的 hook 分发和审计功能
4. **Schema 定义** - Kiro 平台特定的验证 schema

## 目录结构

```
hooks/
├── hooks.json                          # Hooks 配置文件
├── README.md                           # 本文件
├── validators/                         # 验证脚本
│   ├── bugcard_validator.py           # BugCard 完整性检查
│   ├── counterfactual_validator.py    # 反事实验证检查
│   ├── skeptic_signoff_checker.py     # Skeptic 签署验证
│   └── causal_anchor_validator.py     # 因果锚点验证
├── utils/                              # 工具脚本
│   ├── kiro_hook_dispatch.py          # Hook 分发器
│   ├── run_compliance_audit.py        # 运行合规审计
│   ├── validate_tool_contract_runtime.py  # 工具契约验证
│   └── resolve_session_artifact.py    # Session 产物解析
└── schemas/                            # Schema 定义
    ├── bugcard_required_fields.yaml   # BugCard 必填字段
    ├── skeptic_signoff_schema.yaml    # Skeptic 签署格式
    └── run_compliance_schema.yaml     # 运行合规 Schema
```

## Kiro Native Hooks

Kiro 原生 hooks 位于 `.kiro/hooks/` 目录：

- `bugcard-write-gate.json` - BugCard 写入前验证
- `finalization-gate.json` - 结案前合规检查

## 与 Common Hooks 的关系

本目录下的验证脚本都是 `common/hooks` 中对应脚本的包装器。
实际验证逻辑位于 `common/hooks/validators/` 和 `common/hooks/utils/`。

## 退出码规范

| 退出码 | 含义 |
|--------|------|
| 0 | 验证通过 |
| 1 | 验证失败 |
| 2 | 文件/依赖错误 |
| 3 | 产物不存在 |

## 依赖

- Python 3.8+
- PyYAML (`pip install pyyaml`)
