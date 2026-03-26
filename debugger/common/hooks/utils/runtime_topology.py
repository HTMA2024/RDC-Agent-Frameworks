#!/usr/bin/env python3
"""Run-level runtime topology artifact builder."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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
    print("missing dependency 'PyYAML'", file=sys.stderr)
    print(f"install with: python -m pip install -r {req}", file=sys.stderr)
    raise SystemExit(2)


RUNTIME_TOPOLOGY_SCHEMA = "1"


def _debugger_root(default: Path | None = None) -> Path:
    return default.resolve() if default else Path(__file__).resolve().parents[3]


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def _norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_action_chain(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in _read_text(path).splitlines():
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _extract_session_id(run_data: dict[str, Any], session_marker: Path) -> str:
    for value in (
        run_data.get("session_id"),
        (run_data.get("debug") or {}).get("session_id") if isinstance(run_data.get("debug"), dict) else None,
        (run_data.get("runtime") or {}).get("session_id") if isinstance(run_data.get("runtime"), dict) else None,
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    if session_marker.is_file():
        value = session_marker.read_text(encoding="utf-8").lstrip("\ufeff").strip()
        if value and value != "session-unset":
            return value
    return ""


def _payload_str(event: dict[str, Any], key: str) -> str:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return ""
    return str(payload.get(key) or "").strip()


def _mode_key(entry_mode: str, backend: str) -> str:
    if backend == "remote":
        return "remote_mcp" if entry_mode == "mcp" else "remote_daemon"
    return "local_mcp" if entry_mode == "mcp" else "local_cli"


def build_runtime_topology_payload(root: Path, run_root: Path, platform: str | None = None) -> dict[str, Any]:
    run_yaml = run_root / "run.yaml"
    run_data = _read_yaml(run_yaml) if run_yaml.is_file() else {}
    if not isinstance(run_data, dict):
        run_data = {}
    case_root = run_root.parent.parent
    entry_gate = case_root / "artifacts" / "entry_gate.yaml"
    entry_data = _read_yaml(entry_gate) if entry_gate.is_file() else {}
    if not isinstance(entry_data, dict):
        entry_data = {}
    platform_caps_path = root / "common" / "config" / "platform_capabilities.json"
    runtime_truth_path = root / "common" / "config" / "runtime_mode_truth.snapshot.json"
    platform_caps = _read_json(platform_caps_path) if platform_caps_path.is_file() else {"platforms": {}}
    runtime_truth = _read_json(runtime_truth_path) if runtime_truth_path.is_file() else {"modes": {}}
    session_marker = root / "common" / "knowledge" / "library" / "sessions" / ".current_session"
    session_id = _extract_session_id(run_data, session_marker)
    action_chain = (
        root / "common" / "knowledge" / "library" / "sessions" / session_id / "action_chain.jsonl"
        if session_id
        else root / "common" / "knowledge" / "library" / "sessions" / "action_chain.jsonl"
    )
    events = _load_action_chain(action_chain) if action_chain.is_file() else []
    contexts = sorted({value for value in (_payload_str(event, "context_id") for event in events) if value}) or ["default"]
    owners = sorted({value for value in (_payload_str(event, "runtime_owner") for event in events) if value})
    baton_refs = sorted({value for value in (_payload_str(event, "baton_ref") for event in events) if value})
    entry_mode = str(entry_data.get("entry_mode") or (run_data.get("debug") or {}).get("entry_mode") or "cli").strip()
    backend = str(entry_data.get("backend") or (run_data.get("runtime") or {}).get("backend") or "local").strip()
    coordination_mode = str(run_data.get("coordination_mode") or (run_data.get("runtime") or {}).get("coordination_mode") or "").strip()
    platform_key = str(platform or run_data.get("platform") or "").strip()
    platform_row = dict(((platform_caps.get("platforms") or {}).get(platform_key) or {}))
    sub_agent_mode = str(platform_row.get("sub_agent_mode") or "").strip()
    peer_communication = str(platform_row.get("peer_communication") or "").strip()
    agent_description_mode = str(platform_row.get("agent_description_mode") or "").strip()
    dispatch_topology = str(platform_row.get("dispatch_topology") or "").strip()
    local_live_runtime_policy = str(platform_row.get("local_live_runtime_policy") or "").strip()
    remote_live_runtime_policy = str(platform_row.get("remote_live_runtime_policy") or "").strip()
    mode_key = _mode_key(entry_mode, backend)
    mode_truth = dict(((runtime_truth.get("modes") or {}).get(mode_key) or {}))
    runtime_parallelism_ceiling = str(mode_truth.get("runtime_parallelism_ceiling") or "").strip()
    applied_live_runtime_policy = remote_live_runtime_policy if backend == "remote" else local_live_runtime_policy
    checks = [
        {
            "id": "entry_mode",
            "result": "pass" if entry_mode in {"cli", "mcp"} else "fail",
            "detail": "entry_mode must be cli or mcp",
        },
        {
            "id": "backend",
            "result": "pass" if backend in {"local", "remote"} else "fail",
            "detail": "backend must be local or remote",
        },
        {
            "id": "coordination_mode",
            "result": "pass" if bool(coordination_mode) else "fail",
            "detail": "coordination_mode must be recorded in run.yaml",
        },
        {
            "id": "platform_contract",
            "result": "pass" if bool(platform_row) else "fail",
            "detail": "platform_capabilities.json must define the platform agentic profile",
        },
        {
            "id": "runtime_mode_truth",
            "result": "pass" if bool(mode_truth) and bool(runtime_parallelism_ceiling) else "fail",
            "detail": "runtime_mode_truth.snapshot.json must define runtime_parallelism_ceiling for the selected mode",
        },
        {
            "id": "applied_live_runtime_policy",
            "result": "pass" if bool(applied_live_runtime_policy) else "fail",
            "detail": "platform_capabilities.json must define the applied live runtime policy for this backend",
        },
        {
            "id": "contexts",
            "result": "pass" if bool(contexts) else "fail",
            "detail": "runtime topology must contain at least one context",
            "refs": contexts[:8],
        },
    ]
    status = "passed" if all(item["result"] == "pass" for item in checks) else "failed"
    return {
        "schema_version": RUNTIME_TOPOLOGY_SCHEMA,
        "generated_by": "runtime_topology",
        "generated_at": _now_iso(),
        "status": status,
        "platform": platform_key,
        "run_id": str(run_data.get("run_id") or "").strip(),
        "session_id": session_id,
        "coordination_mode": coordination_mode,
        "sub_agent_mode": sub_agent_mode,
        "peer_communication": peer_communication,
        "agent_description_mode": agent_description_mode,
        "dispatch_topology": dispatch_topology,
        "entry_mode": entry_mode,
        "backend": backend,
        "runtime_parallelism_ceiling": runtime_parallelism_ceiling,
        "applied_live_runtime_policy": applied_live_runtime_policy,
        "contexts": contexts,
        "owners": owners,
        "baton_refs": baton_refs,
        "checks": checks,
        "paths": {
            "entry_gate": _norm(entry_gate),
            "action_chain": _norm(action_chain),
            "platform_capabilities": _norm(platform_caps_path),
            "runtime_mode_truth": _norm(runtime_truth_path),
            "run_root": _norm(run_root),
        },
    }


def _dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def run_runtime_topology(root: Path, run_root: Path, platform: str | None = None) -> dict[str, Any]:
    payload = build_runtime_topology_payload(root, run_root, platform=platform)
    _dump_yaml(run_root / "artifacts" / "runtime_topology.yaml", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build debugger runtime topology artifact")
    parser.add_argument("--run-root", type=Path, required=True, help="workspace run root")
    parser.add_argument("--platform", default=None, help="platform key override")
    parser.add_argument("--root", type=Path, default=None, help="debugger root override")
    parser.add_argument("--strict", action="store_true", help="return non-zero on failed topology")
    args = parser.parse_args()

    payload = run_runtime_topology(_debugger_root(args.root), args.run_root.resolve(), platform=args.platform)
    print(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), end="")
    if args.strict and payload["status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
