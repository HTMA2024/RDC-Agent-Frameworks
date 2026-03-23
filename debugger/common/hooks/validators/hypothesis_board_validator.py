#!/usr/bin/env python3
"""Validate debugger hypothesis_board.yaml artifacts."""

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


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "hypothesis_board_schema.yaml"


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_hypothesis_board(data: Any) -> list[str]:
    issues: list[str] = []
    schema = _load_yaml(SCHEMA_PATH)
    if not isinstance(data, dict):
        return ["hypothesis_board must be a YAML object"]
    if not isinstance(schema, dict):
        return [f"unable to load schema: {SCHEMA_PATH}"]

    root = data.get("hypothesis_board")
    if not isinstance(root, dict):
        return ["hypothesis_board root object must exist"]

    board_schema = schema.get("hypothesis_board") if isinstance(schema.get("hypothesis_board"), dict) else {}
    for field in board_schema.get("required_fields", []):
        if field not in root or root.get(field) is None:
            issues.append(f"hypothesis_board.{field} must be present")

    if "entry_skill" in root and str(root.get("entry_skill", "")).strip() not in set(board_schema.get("entry_skill_allowed", [])):
        issues.append(f"invalid hypothesis_board.entry_skill: {root.get('entry_skill')!r}")
    if "intake_state" in root and str(root.get("intake_state", "")).strip() not in set(board_schema.get("intake_state_allowed", [])):
        issues.append(f"invalid hypothesis_board.intake_state: {root.get('intake_state')!r}")
    if "current_phase" in root and str(root.get("current_phase", "")).strip() not in set(board_schema.get("current_phase_allowed", [])):
        issues.append(f"invalid hypothesis_board.current_phase: {root.get('current_phase')!r}")

    for field in ("session_id", "user_goal", "current_task", "active_owner", "last_updated"):
        value = root.get(field)
        if value is not None and not _nonempty_str(value):
            issues.append(f"hypothesis_board.{field} must be a non-empty string")

    for field in ("pending_requirements", "blocking_issues", "progress_summary", "next_actions", "hypotheses"):
        value = root.get(field)
        if value is not None and not isinstance(value, list):
            issues.append(f"hypothesis_board.{field} must be a list")

    intent_gate = root.get("intent_gate")
    intent_schema = board_schema.get("intent_gate") if isinstance(board_schema.get("intent_gate"), dict) else {}
    if not isinstance(intent_gate, dict):
        issues.append("hypothesis_board.intent_gate must be an object")
        return issues

    for field in intent_schema.get("required_fields", []):
        if field not in intent_gate or intent_gate.get(field) is None:
            issues.append(f"hypothesis_board.intent_gate.{field} must be present")

    classifier_version = intent_gate.get("classifier_version")
    if classifier_version is not None and (not isinstance(classifier_version, int) or classifier_version < 1):
        issues.append("hypothesis_board.intent_gate.classifier_version must be an integer >= 1")

    clarification_rounds = intent_gate.get("clarification_rounds")
    if clarification_rounds is not None and (not isinstance(clarification_rounds, int) or clarification_rounds < 0):
        issues.append("hypothesis_board.intent_gate.clarification_rounds must be an integer >= 0")

    for field in ("judged_by", "normalized_user_goal", "primary_completion_question", "rationale"):
        value = intent_gate.get(field)
        if value is not None and not _nonempty_str(value):
            issues.append(f"hypothesis_board.intent_gate.{field} must be a non-empty string")

    enums = (
        ("judged_by", "judged_by_allowed"),
        ("dominant_operation", "dominant_operation_allowed"),
        ("requested_artifact", "requested_artifact_allowed"),
        ("ab_role", "ab_role_allowed"),
        ("decision", "decision_allowed"),
        ("confidence", "confidence_allowed"),
        ("redirect_target", "redirect_target_allowed"),
    )
    for field, schema_key in enums:
        if field in intent_gate:
            value = str(intent_gate.get(field, "")).strip()
            allowed = set(str(item).strip() for item in intent_schema.get(schema_key, []))
            if value not in allowed:
                issues.append(f"invalid hypothesis_board.intent_gate.{field}: {intent_gate.get(field)!r}")

    scores = intent_gate.get("scores")
    if not isinstance(scores, dict):
        issues.append("hypothesis_board.intent_gate.scores must be an object")
    else:
        for field in intent_schema.get("score_fields", []):
            value = scores.get(field)
            if not isinstance(value, (int, float)):
                issues.append(f"hypothesis_board.intent_gate.scores.{field} must be numeric")

    hard_signals = intent_gate.get("hard_signals")
    if not isinstance(hard_signals, dict):
        issues.append("hypothesis_board.intent_gate.hard_signals must be an object")
    else:
        for field in intent_schema.get("hard_signal_fields", []):
            value = hard_signals.get(field)
            if not isinstance(value, list):
                issues.append(f"hypothesis_board.intent_gate.hard_signals.{field} must be a list")
                continue
            if any(not _nonempty_str(item) for item in value):
                issues.append(f"hypothesis_board.intent_gate.hard_signals.{field} must contain non-empty strings")

    return issues


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python3 hypothesis_board_validator.py <hypothesis_board.yaml>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"错误：文件不存在 — {path}")
        return 2
    try:
        data = _load_yaml(path)
    except Exception as exc:  # noqa: BLE001
        print(f"错误：解析失败 — {exc}")
        return 2
    issues = validate_hypothesis_board(data)
    if not issues:
        print(f"✅ hypothesis_board 验证通过 — {path.name}")
        return 0
    print("❌ hypothesis_board 验证失败")
    for issue in issues:
        print(f" - {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
