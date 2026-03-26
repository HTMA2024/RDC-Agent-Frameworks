from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit(f"PyYAML is required for tests: {exc}")


REPO_ROOT = Path(__file__).resolve().parents[2]
DEBUGGER_ROOT = REPO_ROOT / "debugger"
INTAKE_GATE_SCRIPT = DEBUGGER_ROOT / "common" / "hooks" / "utils" / "intake_gate.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _seed_case(root: Path, *, intent_decision: str = "debugger") -> Path:
    case_root = root / "workspace" / "cases" / "case_001"
    run_root = case_root / "runs" / "run_01"
    _write(root / "common" / "knowledge" / "library" / "sessions" / ".current_session", "sess_fixture_001\n")
    _write(case_root / "case.yaml", "case_id: case_001\ncurrent_run: run_01\n")
    _write(
        case_root / "case_input.yaml",
        yaml.safe_dump(
            {
                "schema_version": "1",
                "case_id": "case_001",
                "session": {"mode": "cross_device", "goal": "validate fixture"},
                "symptom": {"summary": "fixture"},
                "captures": [
                    {
                        "capture_id": "cap-anomalous-001",
                        "role": "anomalous",
                        "file_name": "broken.rdc",
                        "source": "user_supplied",
                        "provenance": {"device": "fixture-a"},
                    },
                    {
                        "capture_id": "cap-baseline-001",
                        "role": "baseline",
                        "file_name": "good.rdc",
                        "source": "historical_good",
                        "provenance": {"build": "1487"},
                    },
                ],
                "environment": {"api": "Vulkan"},
                "reference_contract": {
                    "source_kind": "capture_baseline",
                    "source_refs": ["capture:baseline"],
                    "verification_mode": "device_parity",
                    "probe_set": {"pixels": [{"name": "probe", "x": 1, "y": 2}]},
                    "acceptance": {"fallback_only": False, "max_channel_delta": 0.05},
                },
                "hints": {},
                "project": {"engine": "fixture"},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    )
    _write(
        case_root / "inputs" / "captures" / "manifest.yaml",
        yaml.safe_dump(
            {
                "captures": [
                    {
                        "capture_id": "cap-anomalous-001",
                        "capture_role": "anomalous",
                        "file_name": "broken.rdc",
                        "source": "user_supplied",
                        "import_mode": "path",
                        "imported_at": "2026-03-24T00:00:00Z",
                        "sha256": "sha-broken",
                        "source_path": "C:/captures/broken.rdc",
                    },
                    {
                        "capture_id": "cap-baseline-001",
                        "capture_role": "baseline",
                        "file_name": "good.rdc",
                        "source": "historical_good",
                        "import_mode": "path",
                        "imported_at": "2026-03-24T00:00:00Z",
                        "sha256": "sha-good",
                        "source_path": "C:/captures/good.rdc",
                    },
                ]
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    )
    _write(case_root / "inputs" / "captures" / "broken.rdc", "broken")
    _write(case_root / "inputs" / "captures" / "good.rdc", "good")
    _write(
        run_root / "run.yaml",
        yaml.safe_dump({"run_id": "run_01", "session_id": "sess_fixture_001"}, sort_keys=False, allow_unicode=True),
    )
    _write(
        run_root / "capture_refs.yaml",
        yaml.safe_dump(
            {
                "captures": [
                    {"capture_id": "cap-anomalous-001", "capture_role": "anomalous"},
                    {"capture_id": "cap-baseline-001", "capture_role": "baseline"},
                ]
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    )
    _write(
        run_root / "notes" / "hypothesis_board.yaml",
        yaml.safe_dump(
            {
                "hypothesis_board": {
                    "session_id": "sess_fixture_001",
                    "entry_skill": "rdc-debugger",
                    "user_goal": "validate fixture",
                    "intake_state": "accepted",
                    "current_phase": "triage",
                    "current_task": "seeded test",
                    "active_owner": "rdc-debugger",
                    "pending_requirements": [],
                    "blocking_issues": [],
                    "progress_summary": ["seeded"],
                    "next_actions": ["run intake gate"],
                    "last_updated": "2026-03-24T00:00:00Z",
                    "intent_gate": {
                        "judged_by": "rdc-debugger",
                        "decision": intent_decision,
                        "scores": {"debugger": 9, "analyst": 0, "optimizer": 0},
                        "rationale": "fixture",
                        "redirect_target": "",
                    },
                    "hypotheses": [],
                }
            },
            sort_keys=False,
            allow_unicode=True,
        ),
    )
    return run_root


class IntakeGateTests(unittest.TestCase):
    def _temp_root(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_intake_gate_passes_when_required_artifacts_exist(self) -> None:
        root = self._temp_root()
        run_root = _seed_case(root)
        module = _load_module(INTAKE_GATE_SCRIPT, "intake_gate_test_module_pass")

        payload = module.run_intake_gate(root, run_root)

        self.assertEqual(payload["status"], "passed")
        self.assertTrue((run_root / "artifacts" / "intake_gate.yaml").is_file())

    def test_missing_capture_manifest_fails(self) -> None:
        root = self._temp_root()
        run_root = _seed_case(root)
        (run_root.parent.parent / "inputs" / "captures" / "manifest.yaml").unlink()
        module = _load_module(INTAKE_GATE_SCRIPT, "intake_gate_test_module_manifest")

        payload = module.build_intake_gate_payload(root, run_root)

        self.assertEqual(payload["status"], "failed")
        failing = {item["id"] for item in payload["checks"] if item["result"] == "fail"}
        self.assertIn("captures_manifest", failing)

    def test_missing_capture_refs_fails(self) -> None:
        root = self._temp_root()
        run_root = _seed_case(root)
        (run_root / "capture_refs.yaml").unlink()
        module = _load_module(INTAKE_GATE_SCRIPT, "intake_gate_test_module_refs")

        payload = module.build_intake_gate_payload(root, run_root)

        self.assertEqual(payload["status"], "failed")
        failing = {item["id"] for item in payload["checks"] if item["result"] == "fail"}
        self.assertIn("capture_refs", failing)
        self.assertIn("capture_refs_schema", failing)

    def test_non_debugger_intent_gate_fails(self) -> None:
        root = self._temp_root()
        run_root = _seed_case(root, intent_decision="analyst")
        module = _load_module(INTAKE_GATE_SCRIPT, "intake_gate_test_module_intent")

        payload = module.build_intake_gate_payload(root, run_root)

        self.assertEqual(payload["status"], "failed")
        failing = {item["id"] for item in payload["checks"] if item["result"] == "fail"}
        self.assertIn("intent_gate_acceptance", failing)


if __name__ == "__main__":
    unittest.main()
