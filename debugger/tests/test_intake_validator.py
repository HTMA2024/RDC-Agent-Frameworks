from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = REPO_ROOT / "debugger" / "common" / "hooks" / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from intake_validator import validate_case_input  # noqa: E402


def _base_case(mode: str = "single") -> dict:
    return {
        "schema_version": "1",
        "case_id": "case-001",
        "session": {"mode": mode, "goal": "validate fixture"},
        "symptom": {"summary": "fixture symptom"},
        "captures": [
            {
                "capture_id": "cap-anom-001",
                "role": "anomalous",
                "file_name": "broken.rdc",
                "source": "user_supplied",
                "provenance": {"device": "fixture"},
            }
        ],
        "environment": {"api": "Vulkan"},
        "reference_contract": {
            "source_kind": "external_image",
            "source_refs": ["reference:golden-001"],
            "verification_mode": "pixel_value_check",
            "probe_set": {"pixels": [{"name": "hair_hotspot", "x": 1, "y": 2}]},
            "acceptance": {"fallback_only": False, "max_channel_delta": 0.05},
        },
        "hints": {},
        "project": {"engine": "fixture"},
    }


class IntakeValidatorTests(unittest.TestCase):
    def test_single_with_quantitative_probe_passes(self) -> None:
        issues = validate_case_input(_base_case("single"))
        self.assertEqual(issues, [])

    def test_cross_device_requires_baseline_capture(self) -> None:
        data = _base_case("cross_device")
        data["reference_contract"]["source_kind"] = "capture_baseline"
        data["reference_contract"]["source_refs"] = ["capture:baseline"]
        data["reference_contract"]["verification_mode"] = "device_parity"
        issues = validate_case_input(data)
        self.assertTrue(any("baseline" in issue for issue in issues))

    def test_regression_requires_known_good_provenance(self) -> None:
        data = _base_case("regression")
        data["captures"].append(
            {
                "capture_id": "cap-base-001",
                "role": "baseline",
                "file_name": "good.rdc",
                "source": "historical_good",
                "provenance": {},
            }
        )
        data["reference_contract"]["source_kind"] = "capture_baseline"
        data["reference_contract"]["source_refs"] = ["capture:baseline"]
        data["reference_contract"]["verification_mode"] = "regression_check"
        issues = validate_case_input(data)
        self.assertTrue(any("build or revision" in issue for issue in issues))

    def test_visual_comparison_must_be_fallback_only(self) -> None:
        data = _base_case("single")
        data["reference_contract"]["verification_mode"] = "visual_comparison"
        data["reference_contract"]["acceptance"]["fallback_only"] = False
        issues = validate_case_input(data)
        self.assertTrue(any("visual_comparison" in issue for issue in issues))

    def test_single_visual_only_fallback_is_allowed(self) -> None:
        data = _base_case("single")
        data["reference_contract"]["verification_mode"] = "visual_comparison"
        data["reference_contract"]["probe_set"] = {"pixels": [], "regions": []}
        data["reference_contract"]["acceptance"]["fallback_only"] = True
        issues = validate_case_input(data)
        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
