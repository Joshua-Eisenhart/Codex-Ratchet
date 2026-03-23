from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from build_a1_autoratchet_controller_result import build_result


class TestBuildA1AutoratchetControllerResult(unittest.TestCase):
    def test_build_result_continues_when_audit_passes_and_budget_remains(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 3}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 3,
                        "halt_reason": "MAX_STEPS_REACHED",
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "state_metrics": {
                            "killed_unique_count": 9,
                            "sim_registry_count": 20,
                            "canonical_term_count": 4,
                        },
                        "a1_semantic_gate": {"status": "FAIL"},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json").write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "family_slice_expected": True,
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_obligations_status": "PASS",
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="DISPATCH",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=3,
            )
            self.assertEqual("CONTINUE_ONE_BOUNDED_STEP", payload["controller_decision"])
            self.assertEqual(3, payload["steps_completed"])
            self.assertEqual(9, payload["graveyard_count"])
            self.assertEqual("family_slice_controlled", payload["planning_mode"])
            self.assertFalse(payload["legacy_goal_profile_mode"])
            self.assertEqual(
                ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"],
                payload["operator_policy_sources"],
            )

    def test_build_result_does_not_stop_on_semantic_gate_pass_when_family_slice_obligations_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 3}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 3,
                        "halt_reason": "MAX_STEPS_REACHED",
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "state_metrics": {
                            "killed_unique_count": 9,
                            "sim_registry_count": 20,
                            "canonical_term_count": 4,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json").write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "family_slice_expected": True,
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_obligations_status": "FAIL",
                    }
                ),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="DISPATCH",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=3,
            )
            self.assertEqual("MANUAL_REVIEW_REQUIRED", payload["controller_decision"])
            self.assertEqual("family_slice_obligations_failed", payload["controller_decision_reason"])

    def test_build_result_requires_manual_review_for_legacy_goal_profile_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 3}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 3,
                        "halt_reason": "MAX_STEPS_REACHED",
                        "goal_source": "goal_profile",
                        "planning_mode": "compatibility_profile_scaffold",
                        "compatibility_goal_profile": "refined_fuel",
                        "state_metrics": {
                            "killed_unique_count": 9,
                            "sim_registry_count": 20,
                            "canonical_term_count": 4,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "reports" / "a1_autoratchet_cycle_audit_report.json").write_text(
                json.dumps({"status": "PASS", "family_slice_expected": False}),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="DISPATCH",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=3,
            )
            self.assertEqual("MANUAL_REVIEW_REQUIRED", payload["controller_decision"])
            self.assertEqual("legacy_goal_profile_mode", payload["controller_decision_reason"])
            self.assertEqual("compatibility_profile_scaffold", payload["planning_mode"])
            self.assertEqual("refined_fuel", payload["compatibility_goal_profile"])
            self.assertTrue(payload["legacy_goal_profile_mode"])


if __name__ == "__main__":
    unittest.main()
