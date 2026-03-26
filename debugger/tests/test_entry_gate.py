from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEBUGGER_ROOT = REPO_ROOT / "debugger"
ENTRY_GATE_SCRIPT = DEBUGGER_ROOT / "common" / "hooks" / "utils" / "entry_gate.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _copy(path: Path, source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source.read_text(encoding="utf-8-sig"), encoding="utf-8")


class EntryGateTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _copy(root / "common" / "config" / "platform_capabilities.json", DEBUGGER_ROOT / "common" / "config" / "platform_capabilities.json")
        _copy(root / "common" / "config" / "runtime_mode_truth.snapshot.json", REPO_ROOT.parent / "RDC-Agent-Tools" / "spec" / "runtime_mode_truth.json")
        return root

    def test_entry_gate_blocks_missing_capture(self) -> None:
        module = _load_module(ENTRY_GATE_SCRIPT, "entry_gate_module_missing_capture")
        root = self._temp_root()
        case_root = root / "workspace" / "cases" / "case_001"
        payload = module.run_entry_gate(
            root,
            case_root,
            platform="codex",
            entry_mode="cli",
            backend="local",
            capture_paths=[],
            mcp_configured=False,
            remote_transport="",
        )
        self.assertEqual(payload["status"], "blocked")
        blocker_codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("BLOCKED_MISSING_CAPTURE", blocker_codes)
        self.assertTrue((case_root / "artifacts" / "entry_gate.yaml").is_file())

    def test_entry_gate_blocks_when_mcp_not_configured(self) -> None:
        module = _load_module(ENTRY_GATE_SCRIPT, "entry_gate_module_mcp")
        root = self._temp_root()
        case_root = root / "workspace" / "cases" / "case_001"
        capture = case_root / "incoming" / "sample.rdc"
        capture.parent.mkdir(parents=True, exist_ok=True)
        capture.write_text("fixture", encoding="utf-8")
        payload = module.build_entry_gate_payload(
            root,
            case_root,
            platform="claude-code",
            entry_mode="mcp",
            backend="local",
            capture_paths=[str(capture)],
            mcp_configured=False,
            remote_transport="",
        )
        self.assertEqual(payload["status"], "blocked")
        blocker_codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("BLOCKED_ENTRY_PREFLIGHT", blocker_codes)

    def test_entry_gate_blocks_unsupported_platform_mode(self) -> None:
        module = _load_module(ENTRY_GATE_SCRIPT, "entry_gate_module_unsupported")
        root = self._temp_root()
        case_root = root / "workspace" / "cases" / "case_001"
        capture = case_root / "incoming" / "sample.rdc"
        capture.parent.mkdir(parents=True, exist_ok=True)
        capture.write_text("fixture", encoding="utf-8")
        caps_path = root / "common" / "config" / "platform_capabilities.json"
        caps = json.loads(caps_path.read_text(encoding="utf-8"))
        caps["platforms"]["codex"]["remote_support"] = "unsupported"
        caps_path.write_text(json.dumps(caps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload = module.build_entry_gate_payload(
            root,
            case_root,
            platform="codex",
            entry_mode="cli",
            backend="remote",
            capture_paths=[str(capture)],
            mcp_configured=False,
            remote_transport="adb_android",
        )
        self.assertEqual(payload["status"], "blocked")
        blocker_codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("BLOCKED_PLATFORM_MODE_UNSUPPORTED", blocker_codes)

    def test_entry_gate_blocks_remote_without_transport(self) -> None:
        module = _load_module(ENTRY_GATE_SCRIPT, "entry_gate_module_remote")
        root = self._temp_root()
        case_root = root / "workspace" / "cases" / "case_001"
        capture = case_root / "incoming" / "sample.rdc"
        capture.parent.mkdir(parents=True, exist_ok=True)
        capture.write_text("fixture", encoding="utf-8")
        payload = module.build_entry_gate_payload(
            root,
            case_root,
            platform="codex",
            entry_mode="cli",
            backend="remote",
            capture_paths=[str(capture)],
            mcp_configured=False,
            remote_transport="",
        )
        self.assertEqual(payload["status"], "blocked")
        blocker_codes = {item["code"] for item in payload["blockers"]}
        self.assertIn("BLOCKED_REMOTE_PREREQUISITE", blocker_codes)

    def test_entry_gate_passes_with_local_cli_capture(self) -> None:
        module = _load_module(ENTRY_GATE_SCRIPT, "entry_gate_module_pass")
        root = self._temp_root()
        case_root = root / "workspace" / "cases" / "case_001"
        capture = case_root / "incoming" / "sample.rdc"
        capture.parent.mkdir(parents=True, exist_ok=True)
        capture.write_text("fixture", encoding="utf-8")
        payload = module.build_entry_gate_payload(
            root,
            case_root,
            platform="claude-code",
            entry_mode="cli",
            backend="local",
            capture_paths=[str(capture)],
            mcp_configured=False,
            remote_transport="",
        )
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["platform_contract"]["sub_agent_mode"], "team_agents")
        self.assertEqual(payload["runtime_mode_truth"]["runtime_parallelism_ceiling"], "multi_context_multi_owner")


if __name__ == "__main__":
    unittest.main()
