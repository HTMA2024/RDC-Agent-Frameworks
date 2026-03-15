# 反事实评分与独立复核规范

反事实评分不再只回答“修复后是不是看起来更好了”，而是同时回答三件事：

1. 干预是否量化地改善了结构异常；
2. 干预是否量化地对齐了 `reference_contract`；
3. 变量隔离是否经过独立复核，而不是由提出修复的人自己判自己通过。

## 核心原则

- `counterfactual_submitted` 只负责提交结构化实验事实。
- `counterfactual_reviewed` 才负责给出独立复核结论。
- proposer 与 reviewer 必须是不同 agent。
- 缺少 `reference_contract_ref`、缺少 baseline source、或 `verification_mode=visual_comparison` 时，不得产出 strict approved。

## 评分维度与权重

### Dimension 1：像素级恢复度（Pixel Recovery Score）

`S_pixel = 1 - ||pixel_after - pixel_baseline|| / ||pixel_before - pixel_baseline||`

### Dimension 2：变量隔离度（Variable Isolation Score）

| 检查项 | 通过得 1 分，失败得 0 分 |
|--------|----------------------|
| `only_target_changed` | 仅改变目标变量，没有引入其他逻辑修改 |
| `same_scene_same_input` | 修复前后在同一场景、同一输入下对比 |
| `same_drawcall_count` | 渲染结构未变形，DrawCall 数量一致 |

### Dimension 3：症状覆盖度（Symptom Coverage Score）

`S_coverage = 修复后消失的目标症状数 / 目标症状总数`

### Dimension 4：跨场景稳定性（Stability Score，可选）

`S_stability = 通过验证的场景数 / 总验证场景数`

## 语义验证等级

严格语义验证要求：

- `reference_contract.acceptance.fallback_only = false`
- `verification_mode != visual_comparison`
- 至少存在一个量化 probe（pixel 或 region）

Fallback 语义验证：

- 允许记录症状改善
- 不允许 strict approved
- 不允许驱动 `fix_verified=true`

## 综合评分

`S_counterfactual = 0.50 * S_pixel + 0.25 * S_isolation + 0.20 * S_coverage + 0.05 * S_stability`

当 `stability` 不可用时，权重重分配为 `0.50 / 0.25 / 0.25 / 0.00`。

## Ledger 记录方式

### `counterfactual_submitted`

必须至少包含：

```json
{
  "event_type": "counterfactual_submitted",
  "status": "submitted",
  "payload": {
    "review_id": "CF-001",
    "hypothesis_id": "H-001",
    "proposer_agent": "shader_ir_agent",
    "intervention": "half diffuse -> float diffuse",
    "target_variable": "shader precision",
    "reference_contract_ref": "../workspace/cases/case-001/case_input.yaml#reference_contract",
    "verification_mode": "device_parity",
    "baseline_source": {
      "kind": "capture_baseline",
      "ref": "capture:baseline"
    },
    "probe_results": [
      {
        "probe_id": "hair_hotspot",
        "probe_type": "pixel",
        "pixel_before": {"x": 512, "y": 384, "rgba": [0.21, 0.19, 0.18, 1.0]},
        "pixel_after": {"x": 512, "y": 384, "rgba": [0.37, 0.34, 0.32, 1.0]},
        "pixel_baseline": {"x": 512, "y": 384, "rgba": [0.38, 0.35, 0.33, 1.0]}
      }
    ],
    "isolation_checks": {
      "only_target_changed": true,
      "same_scene_same_input": true,
      "same_drawcall_count": true
    },
    "measurements": {
      "pixel_before": {"x": 512, "y": 384, "rgba": [0.21, 0.19, 0.18, 1.0]},
      "pixel_after": {"x": 512, "y": 384, "rgba": [0.37, 0.34, 0.32, 1.0]},
      "pixel_baseline": {"x": 512, "y": 384, "rgba": [0.38, 0.35, 0.33, 1.0]}
    },
    "scoring": {
      "pixel_recovery": 0.94,
      "variable_isolation": 1.0,
      "symptom_coverage": 1.0,
      "total": 0.97
    }
  }
}
```

### `counterfactual_reviewed`

严格批准前必须额外给出：

```json
{
  "event_type": "counterfactual_reviewed",
  "status": "approved",
  "payload": {
    "review_id": "CF-001",
    "hypothesis_id": "H-001",
    "reviewer_agent": "skeptic_agent",
    "semantic_verdict": "strict_pass",
    "isolation_verdict": {
      "verdict": "isolated",
      "rationale": "只修改了目标变量，且 probe 结果满足 reference_contract"
    }
  }
}
```

## Snapshot 记录方式

`session_evidence.yaml` 中必须保留：

```yaml
reference_contract:
  ref: "../workspace/cases/case-001/case_input.yaml#reference_contract"
  source_kind: capture_baseline
  verification_mode: device_parity
  fallback_only: false

fix_verification:
  ref: "../workspace/cases/case-001/runs/run-001/artifacts/fix_verification.yaml"
  structural_status: passed
  semantic_status: passed
  overall_status: passed
```

## 与质量 Hook 的集成

`counterfactual_validator.py` 必须检查：

- `reference_contract_ref` 存在
- `baseline_source.kind/ref` 存在
- `probe_results` 非空
- `verification_mode=visual_comparison` 时不得批准 strict approved
- `scoring.total >= 0.80`
- proposer 与 reviewer 不同
