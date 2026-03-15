# BugCard 模板（入库格式）

> 权威规范：`common/hooks/schemas/bugcard_required_fields.yaml`

```yaml
bugcard_id: BUG-XXX-001
title: "<一句话描述（10~120字）>"

symptom_tags: [washout]
trigger_tags: [Adreno_GPU, Vulkan]
violated_invariants: [I-PREC-01]
recommended_sop: SOP-PREC-01
causal_anchor_type: first_bad_event
causal_anchor_ref: "event:523"
causal_chain_summary: >
  <从 causal anchor 到根因表达式的因果链摘要，必须说明为什么它是首次引入，而不是首次明显可见。>

root_cause_summary: >
  <精确根因描述：必须包含代码位置或驱动版本或 API 调用。>

fingerprint:
  pattern: "<可疑表达式/调用签名>"
  risk_category: "<precision_overflow|precision_lowering|nan_propagation|...>"
  shader_stage: PS

fix_verified: true
verification:
  reference_contract_ref: "../workspace/cases/<case_id>/case_input.yaml#reference_contract"
  structural:
    status: passed
    artifact_ref: "../workspace/cases/<case_id>/runs/<run_id>/artifacts/fix_verification.yaml#structural_verification"
  semantic:
    status: passed
    artifact_ref: "../workspace/cases/<case_id>/runs/<run_id>/artifacts/fix_verification.yaml#semantic_verification"

skeptic_signed: true
bugcard_skeptic_signed: true

related_devices: []
action_chain_ref: ""
sop_improvement_notes: ""
```
