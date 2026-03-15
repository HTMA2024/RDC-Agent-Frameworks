from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = REPO_ROOT / "debugger" / "common" / "hooks" / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from counterfactual_validator import validate_counterfactual  # noqa: E402


def _events() -> dict:
    return {
        "evt-submit": {
            "schema_version": "2",
            "event_type": "counterfactual_submitted",
            "payload": {
                "proposer_agent": "shader_ir_agent",
                "reference_contract_ref": "../workspace/cases/case-001/case_input.yaml#reference_contract",
                "verification_mode": "device_parity",
                "baseline_source": {"kind": "capture_baseline", "ref": "capture:baseline"},
                "probe_results": [{"probe_id": "hair_hotspot"}],
                "isolation_checks": {
                    "only_target_changed": True,
                    "same_scene_same_input": True,
                    "same_drawcall_count": True,
                },
                "measurements": {
                    "pixel_before": {"rgba": [0.1, 0.1, 0.1, 1.0]},
                    "pixel_after": {"rgba": [0.2, 0.2, 0.2, 1.0]},
                    "pixel_baseline": {"rgba": [0.21, 0.21, 0.21, 1.0]},
                },
                "scoring": {
                    "pixel_recovery": 0.9,
                    "variable_isolation": 1.0,
                    "symptom_coverage": 1.0,
                    "total": 0.9,
                },
            },
        },
        "evt-review": {
            "schema_version": "2",
            "event_type": "counterfactual_reviewed",
            "status": "approved",
            "payload": {
                "reviewer_agent": "skeptic_agent",
                "semantic_verdict": "strict_pass",
                "isolation_verdict": {"verdict": "isolated", "rationale": "ok"},
            },
        },
        "evt-tool": {
            "schema_version": "2",
            "event_type": "tool_execution",
            "payload": {},
        },
    }


def _snapshot() -> dict:
    return {
        "schema_version": "2",
        "hypotheses": [{"hypothesis_id": "H-001", "status": "VALIDATED"}],
        "conflicts": [],
        "counterfactual_reviews": [
            {
                "review_id": "CF-001",
                "hypothesis_id": "H-001",
                "proposer_agent": "shader_ir_agent",
                "reviewer_agent": "skeptic_agent",
                "status": "approved",
                "submission_event_id": "evt-submit",
                "review_event_id": "evt-review",
                "evidence_refs": ["evt-tool"],
            }
        ],
    }


class CounterfactualValidatorTests(unittest.TestCase):
    def test_strict_counterfactual_passes(self) -> None:
        ok, issues, _ = validate_counterfactual(_snapshot(), _events())
        self.assertTrue(ok, issues)

    def test_visual_comparison_cannot_be_approved(self) -> None:
        snapshot = _snapshot()
        events = _events()
        events["evt-submit"]["payload"]["verification_mode"] = "visual_comparison"
        ok, issues, _ = validate_counterfactual(snapshot, events)
        self.assertFalse(ok)
        self.assertTrue(any("visual_comparison" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
