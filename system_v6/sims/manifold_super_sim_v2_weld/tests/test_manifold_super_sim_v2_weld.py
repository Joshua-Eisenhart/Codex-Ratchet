"""Acceptance tests for manifold_super_sim_v2_weld."""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "manifold_super_sim_v2_weld"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(ROOT / "scripts"))


class WeldPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = importlib.import_module("manifold_super_sim_v2_weld_common")
        cls.validator = importlib.import_module("validate_manifold_super_sim_v2_weld")
        cls.envelope = json.loads((RESULT_DIR / f"{SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))

    def test_family_state_objects_are_separate_and_anchors_match(self) -> None:
        families = self.envelope["family_state_objects"]
        self.assertEqual(families["A"]["state_object_id"], self.common.EXPECTED_A_STATE_ID)
        self.assertEqual(families["B"]["state_object_id"], self.common.EXPECTED_B_STATE_ID)
        self.assertNotEqual(families["A"]["state_object_id"], families["B"]["state_object_id"])
        self.assertEqual(families["A"]["anchor_values"]["G1_terminal_class_sizes"], [1, 14, 18])
        self.assertEqual(families["B"]["anchor_values"]["deep_chain_final_denominator"], 16)
        self.assertEqual(families["B"]["anchor_values"]["compression_total_emitted_rows"], 288)
        self.assertEqual(families["B"]["anchor_values"]["compression_survivor_count"], 96)
        self.assertFalse(families["B"]["b_scoped_projection"]["axis0_leak_detected"])

    def test_weld_map_rows_and_controls(self) -> None:
        self.assertEqual(len(self.envelope["declared_weld_map"]), 8)
        self.assertTrue(all(row["pass"] for row in self.envelope["declared_weld_map"]))
        rows = {row["row_id"]: row for row in self.envelope["weld_row_table"]}
        self.assertEqual(rows["W3_partition_relation"]["family_a_value"], 3)
        self.assertEqual(rows["W3_partition_relation"]["family_b_value"], 8)
        self.assertEqual(rows["W3_partition_relation"]["computed_relation_value"], 11)
        controls = self.envelope["cross_family_controls"]
        self.assertTrue(controls["A_only_perturbation_control"]["family_b_anchors_unchanged"])
        self.assertTrue(controls["B_only_perturbation_control"]["family_a_anchors_unchanged"])
        self.assertEqual(controls["weld_only_perturbation_control"]["moved_weld_rows"], ["W3_partition_relation"])
        self.assertFalse(controls["decorative_weld_detector"]["decorative_change_detected"])

    def test_smt_rows_bind_a_b_and_weld_relation(self) -> None:
        smt = self.envelope["weld_smt_rows"]
        for row in smt.values():
            self.assertTrue(row["ran"])
            self.assertTrue(row["load_bearing"])
            self.assertEqual(row["verdict"], "unsat")
            self.assertEqual(row["erased_flip_verdict"], "sat")
            self.assertFalse(row["asserted_precomputed_boolean"])
        self.assertEqual(smt["z3_weld_relation"]["bound_family_a_value"], 3)
        self.assertEqual(smt["z3_weld_relation"]["bound_family_b_value"], 8)
        self.assertEqual(smt["z3_weld_relation"]["bound_weld_relation_value"], 11)

    def test_trajectory_lineage_and_builder_boundary(self) -> None:
        artifact = self.envelope["trajectory_artifact"]
        payload = json.loads((ROOT / artifact["path"]).read_text(encoding="utf-8"))
        self.assertTrue(artifact["sha_verified"])
        self.assertEqual(set(payload["family_scopes"]), {"A", "B", "WELD"})
        self.assertGreaterEqual(len(payload["step_rows"]), 29)
        self.assertTrue(all(row["trajectory_step_id"] for row in payload["step_rows"]))
        self.assertTrue(all(row["row_step_lineage_id"] for row in payload["step_rows"]))
        self.assertTrue(all(row["row_step_class_why"] for row in payload["step_rows"]))
        self.assertTrue(self.envelope["no_builder_audit_verdict"])
        self.assertTrue(self.envelope["no_builder_audit_verdict_envelope_gate"])
        self.assertFalse((SIM_DIR / "audit_verdict.md").exists())

    def test_packet_validator_accepts_envelope(self) -> None:
        errors = self.validator.validate_payload(self.envelope)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
