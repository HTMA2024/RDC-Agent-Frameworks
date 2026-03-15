#!/usr/bin/env python3
"""Validate debugger case_input.yaml intake artifacts."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ModuleNotFoundError:
    req = Path(__file__).resolve().parents[1] / "requirements.txt"
    print("错误：缺少依赖 'PyYAML'，无法解析 YAML。")
    print(f"请先安装依赖：python3 -m pip install -r {req}")
    sys.exit(2)


ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RESET = "\033[0m"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "intake_case_input_schema.yaml"


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_capture_entry(entry: Any, schema: dict[str, Any], mode: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(entry, dict):
        return ["captures entry must be an object"]
    role = str(entry.get("role", "")).strip()
    source = str(entry.get("source", "")).strip()
    if role not in set(schema.get("capture_role", {}).get("allowed_values", [])):
        issues.append(f"invalid capture role: {role!r}")
    if source not in set(schema.get("capture_source", {}).get("allowed_values", [])):
        issues.append(f"invalid capture source: {source!r}")
    if not _nonempty_str(entry.get("capture_id")):
        issues.append("capture_id must be non-empty")
    if not _nonempty_str(entry.get("file_name")):
        issues.append("file_name must be non-empty")
    provenance = entry.get("provenance")
    if provenance is not None and not isinstance(provenance, dict):
        issues.append("provenance must be an object when present")
    if mode == "regression" and role == "baseline":
        if source != "historical_good":
            issues.append("regression baseline must use source=historical_good")
        if not isinstance(provenance, dict) or not (_nonempty_str(provenance.get("build")) or _nonempty_str(provenance.get("revision"))):
            issues.append("regression baseline provenance must include build or revision")
    return issues


def _validate_reference_contract(contract: Any, schema: dict[str, Any], mode: str, capture_roles: set[str]) -> list[str]:
    issues: list[str] = []
    if not isinstance(contract, dict):
        return ["reference_contract must be an object"]
    ref_schema = schema.get("reference_contract", {})
    source_kind = str(contract.get("source_kind", "")).strip()
    verification_mode = str(contract.get("verification_mode", "")).strip()
    if source_kind not in set(ref_schema.get("source_kind_allowed", [])):
        issues.append(f"invalid reference_contract.source_kind: {source_kind!r}")
    if verification_mode not in set(ref_schema.get("verification_mode_allowed", [])):
        issues.append(f"invalid reference_contract.verification_mode: {verification_mode!r}")

    source_refs = contract.get("source_refs")
    if not isinstance(source_refs, list) or not source_refs:
        issues.append("reference_contract.source_refs must be a non-empty list")
    else:
        allowed_prefixes = tuple(ref_schema.get("source_ref_prefix_allowed", []))
        for item in source_refs:
            ref = str(item).strip()
            if not ref:
                issues.append("reference_contract.source_refs contains empty ref")
                continue
            if not ref.startswith(allowed_prefixes):
                issues.append(f"reference_contract.source_refs has invalid ref: {ref!r}")
                continue
            if ref.startswith("capture:"):
                role = ref.split(":", 1)[1]
                if role not in capture_roles:
                    issues.append(f"reference_contract.source_refs references missing capture role: {ref!r}")

    probe_set = contract.get("probe_set")
    if not isinstance(probe_set, dict):
        issues.append("reference_contract.probe_set must be an object")

    acceptance = contract.get("acceptance")
    if not isinstance(acceptance, dict):
        issues.append("reference_contract.acceptance must be an object")
    else:
        if not isinstance(acceptance.get("fallback_only"), bool):
            issues.append("reference_contract.acceptance.fallback_only must be boolean")
        for field in ref_schema.get("acceptance_optional_numeric", []):
            value = acceptance.get(field)
            if value is not None and not isinstance(value, (int, float)):
                issues.append(f"reference_contract.acceptance.{field} must be numeric when present")
        fallback_only = acceptance.get("fallback_only")
        if verification_mode == "visual_comparison" and fallback_only is not True:
            issues.append("visual_comparison requires acceptance.fallback_only=true")

    if mode == "cross_device":
        if source_kind != "capture_baseline":
            issues.append("cross_device requires reference_contract.source_kind=capture_baseline")
        if "baseline" not in capture_roles:
            issues.append("cross_device requires a baseline capture role")
        if "capture:baseline" not in [str(item).strip() for item in source_refs or []]:
            issues.append("cross_device requires reference_contract.source_refs to include capture:baseline")
        if verification_mode != "device_parity":
            issues.append("cross_device requires verification_mode=device_parity")

    if mode == "regression":
        if "baseline" not in capture_roles:
            issues.append("regression requires a baseline capture role")
        if verification_mode != "regression_check":
            issues.append("regression requires verification_mode=regression_check")

    if mode == "single" and not capture_roles.intersection({"baseline"}):
        acceptance = contract.get("acceptance") if isinstance(contract, dict) else {}
        probe_set = contract.get("probe_set") if isinstance(contract, dict) else {}
        has_pixels = isinstance(probe_set, dict) and bool(probe_set.get("pixels"))
        has_regions = isinstance(probe_set, dict) and bool(probe_set.get("regions"))
        if not has_pixels and not has_regions and (not isinstance(acceptance, dict) or acceptance.get("fallback_only") is not True):
            issues.append("single mode without baseline capture must either provide quantitative probes or mark fallback_only=true")

    return issues


def validate_case_input(data: Any) -> list[str]:
    issues: list[str] = []
    schema = _load_yaml(SCHEMA_PATH)
    if not isinstance(data, dict):
        return ["case_input must be a YAML object"]
    if not isinstance(schema, dict):
        return [f"unable to load schema: {SCHEMA_PATH}"]

    for item in schema.get("required_fields", []):
        if not isinstance(item, dict):
            issues.append("schema.required_fields contains non-object entry")
            continue
        field = str(item.get("field", "")).strip()
        if not field:
            continue
        value = data.get(field)
        if value is None:
            issues.append(f"missing required field: {field}")
            continue
        expected_type = str(item.get("type", "")).strip()
        if expected_type == "string" and not _nonempty_str(value):
            issues.append(f"{field} must be a non-empty string")
        elif expected_type == "list" and not isinstance(value, list):
            issues.append(f"{field} must be a list")
        elif expected_type == "object" and not isinstance(value, dict):
            issues.append(f"{field} must be an object")
        if isinstance(item.get("required_subfields"), list) and isinstance(value, dict):
            for sub in item["required_subfields"]:
                if value.get(sub) in (None, "", [], {}):
                    issues.append(f"{field}.{sub} must be present")

    session = data.get("session")
    mode = ""
    if isinstance(session, dict):
        mode = str(session.get("mode", "")).strip()
        if mode not in set(schema.get("session_mode", {}).get("allowed_values", [])):
            issues.append(f"invalid session.mode: {mode!r}")
    else:
        issues.append("session must be an object")

    captures = data.get("captures")
    capture_roles: set[str] = set()
    if isinstance(captures, list):
        for entry in captures:
            issues.extend(_validate_capture_entry(entry, schema, mode))
            if isinstance(entry, dict):
                role = str(entry.get("role", "")).strip()
                if role:
                    capture_roles.add(role)
        if "anomalous" not in capture_roles:
            issues.append("captures must include role=anomalous")
        if mode in {"cross_device", "regression"} and "baseline" not in capture_roles:
            issues.append(f"{mode} mode requires role=baseline capture")
    else:
        issues.append("captures must be a list")

    issues.extend(_validate_reference_contract(data.get("reference_contract"), schema, mode, capture_roles))
    return issues


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python3 intake_validator.py <case_input.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"{ANSI_RED}错误：文件不存在 — {path}{ANSI_RESET}")
        return 2
    try:
        data = _load_yaml(path)
    except Exception as exc:  # noqa: BLE001
        print(f"{ANSI_RED}错误：解析失败 — {exc}{ANSI_RESET}")
        return 2
    issues = validate_case_input(data)
    if not issues:
        print(f"{ANSI_GREEN}✅ intake 验证通过 — {path.name}{ANSI_RESET}")
        return 0
    print(f"{ANSI_RED}❌ intake 验证失败{ANSI_RESET}\n")
    for issue in issues:
        print(f"  - {issue}")
    print(f"\n{ANSI_YELLOW}请修正 case_input.yaml 后重试。{ANSI_RESET}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
