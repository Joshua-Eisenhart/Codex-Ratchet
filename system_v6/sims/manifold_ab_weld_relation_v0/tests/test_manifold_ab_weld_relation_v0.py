"""Acceptance tests for manifold_ab_weld_relation_v0."""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_ID = "manifold_ab_weld_relation_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"

sys.path.insert(0, str(SIM_DIR))
sys.path.insert(0, str(ROOT / "scripts"))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


class ABWeldRelationPacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = importlib.import_module("manifold_ab_weld_relation_v0_common")
        cls.validator = importlib.import_module("validate_manifold_ab_weld_relation_v0")
        cls.envelope = json.loads((RESULT_DIR / f"{SIM_ID}_envelope_results.json").read_text(encoding="utf-8"))

    def test_pinned_state_objects_are_separate_and_hash_loaded(self) -> None:
        states = self.envelope["pinned_state_objects"]
        self.assertEqual(states["A"]["state_object_id"], self.common.EXPECTED_A_STATE_ID)
        self.assertEqual(states["B"]["state_object_id"], self.common.EXPECTED_B_STATE_ID)
        self.assertNotEqual(states["A"]["state_object_id"], states["B"]["state_object_id"])
        self.assertTrue(states["A"]["loaded_by_hash"])
        self.assertTrue(states["B"]["loaded_by_hash"])
        self.assertTrue(all(row["hash_verified"] for row in self.envelope["source_import_audit"]["source_hash_pins"].values()))

    def test_coordinate_map_and_weld_only_nonrecoverability(self) -> None:
        rows = self.envelope["coordinate_map"]
        self.assertEqual(len(rows), 8)
        self.assertLessEqual({row["classification"] for row in rows}, {"shared", "related", "independent"})
        self.assertLessEqual({"shared", "related", "independent"}, {row["classification"] for row in rows})
        self.assertTrue(all(row["classification_computed"] for row in rows))
        partition = {row["coordinate_id"]: row for row in rows}["partition_order"]
        self.assertEqual(partition["computed_relation_value"], 11)

        weld = {row["row_id"]: row for row in self.envelope["weld_only_rows"]}
        self.assertEqual(weld["WO2_partition_sum_relation"]["computed_value"], 11)
        self.assertEqual(weld["WO3_partition_product_relation"]["computed_value"], 24)
        self.assertTrue(weld["WO4_zero_pair_relation"]["computed_value"])
        self.assertEqual(weld["WO6_relation_polynomial_residual"]["computed_value"], 0)
        self.assertTrue(all(not row["recoverable_from_A_alone"] for row in weld.values()))
        self.assertTrue(all(not row["recoverable_from_B_alone"] for row in weld.values()))

        nonrecover = self.envelope["nonrecoverability_table"]
        self.assertEqual(len(nonrecover), 6)
        self.assertTrue(all(row["computed_nonrecoverable_from_either_alone"] for row in nonrecover))
        self.assertTrue(all(row["A_erased_status"] == "not_recoverable" for row in nonrecover))
        self.assertTrue(all(row["B_erased_status"] == "not_recoverable" for row in nonrecover))

    def test_cross_family_controls_and_smt_polarity(self) -> None:
        controls = self.envelope["cross_family_controls"]
        self.assertTrue(controls["all_pass"])
        self.assertTrue(controls["A_only_perturbation"]["moved_A_internal_rows"])
        self.assertEqual(controls["A_only_perturbation"]["moved_B_internal_rows"], [])
        self.assertTrue(controls["B_only_perturbation"]["moved_B_internal_rows"])
        self.assertEqual(controls["B_only_perturbation"]["moved_A_internal_rows"], [])
        self.assertTrue(controls["weld_only_perturbation"]["moved_weld_rows"])
        self.assertEqual(controls["weld_only_perturbation"]["moved_A_internal_rows"], [])
        self.assertEqual(controls["weld_only_perturbation"]["moved_B_internal_rows"], [])

        for row in self.envelope["weld_relation_smt"].values():
            self.assertEqual(row["verdict"], "unsat")
            self.assertEqual(row["erased_flip_verdict"], "sat")
            self.assertEqual(row["perturbed_A_flip_verdict"], "sat")
            self.assertEqual(row["perturbed_B_flip_verdict"], "sat")
            self.assertEqual(row["bound_family_a_value"], 3)
            self.assertEqual(row["bound_family_b_value"], 8)
            self.assertEqual(row["bound_weld_relation_value"], 11)
            self.assertFalse(row["asserted_precomputed_boolean"])

    def test_family_c_fence_and_builder_boundary(self) -> None:
        fence = self.envelope["family_c_fence"]
        self.assertEqual(fence["state_object_id"], self.common.EXPECTED_C_STATE_ID)
        self.assertFalse(fence["input_to_relation"])
        self.assertEqual(fence["consumed_as"], "fence_check_citation_only")
        self.assertTrue(fence["disallowed_claims_include_ab_weld_relation"])
        self.assertTrue(builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"))
        self.assertTrue(self.envelope["builder_gates"]["G_2a_idempotency_from_birth"])
        self.assertTrue(self.envelope["builder_gates"]["builder_self_assessment_present"])

    def test_trajectory_and_packet_validator(self) -> None:
        artifact = self.envelope["trajectory_artifact"]
        payload = json.loads((ROOT / artifact["path"]).read_text(encoding="utf-8"))
        self.assertTrue(artifact["sha_verified"])
        self.assertLessEqual({"A+B", "WELD", "CONTROL", "SMT"}, set(payload["family_scopes"]))
        self.assertGreaterEqual(len(payload["step_rows"]), 26)
        self.assertTrue(all(row["trajectory_step_id"] for row in payload["step_rows"]))
        self.assertTrue(all(row["row_step_lineage_id"] for row in payload["step_rows"]))
        errors = self.validator.validate_payload(self.envelope)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
