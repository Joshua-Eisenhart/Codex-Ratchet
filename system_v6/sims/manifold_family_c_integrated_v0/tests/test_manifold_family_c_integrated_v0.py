#!/usr/bin/env python3
"""Acceptance tests for manifold_family_c_integrated_v0."""

from __future__ import annotations

import importlib
import json
import math
import sys
import unittest
from pathlib import Path


PACKET_DIR = Path(__file__).resolve().parents[1]
if str(PACKET_DIR) not in sys.path:
    sys.path.insert(0, str(PACKET_DIR))


class ManifoldFamilyCIntegratedV0Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = importlib.import_module("manifold_family_c_integrated_v0_common")
        cls.payload = cls.common.build_family_c_object()

    def test_live_rungs_and_boundary_context_are_pinned(self) -> None:
        self.assertEqual(self.payload["family"], "Family_C_qubit_ladder_flux")
        self.assertEqual(self.payload["live_rungs"], ["n3", "n4"])
        self.assertEqual(self.payload["floor_anchor"]["sim_id"], "geo_s1_three_qubit_floor_exact_v0")
        self.assertEqual(self.payload["floor_anchor"]["commit"], "6ed5e961e")
        self.assertEqual(self.payload["floor_anchor"]["hilbert_dim"], 8)
        self.assertEqual(self.payload["boundary_stress_context"]["sim_id"], "geo_s1_scaling_stress_678q_exact_v0")
        self.assertEqual(self.payload["boundary_stress_context"]["commit"], "b27d22317")
        self.assertEqual(self.payload["boundary_stress_context"]["run_role"], "BOUNDARY_STRESS_CONTEXT_ONLY")
        self.assertFalse(self.payload["boundary_stress_context"]["run_in_this_packet"])
        self.assertFalse(self.payload["n5_behavior_continuation_claimed"])
        self.assertFalse(self.payload["behavior_class_growth_claimed"])
        self.assertFalse(self.payload["raw_stage_lifted_rows_used"])

    def test_integrated_state_object_consumes_terrain_packets_by_hash(self) -> None:
        state = self.payload["integrated_state_object"]
        self.assertEqual(state["state_object_id"], "manifold_family_c_integrated_v0:C8_floor_plus_n3_n4_terrain")
        self.assertEqual(state["floor_anchor"]["dimension"], 8)
        self.assertEqual(state["n3"]["carrier_dimension"], 8)
        self.assertEqual(state["n4"]["carrier_dimension"], 16)
        self.assertEqual(state["n3"]["source_commit"], "1b36e4a3c")
        self.assertEqual(state["n4"]["source_commit"], "c36a80f6b")
        for rung in ("n3", "n4"):
            with self.subTest(rung=rung):
                row = state[rung]
                self.assertRegex(row["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(row["source_path"].endswith("_envelope_results.json"))
                self.assertTrue(row["continuity_pass"])
                self.assertTrue(row["conditioned_continuity_pass"])
                self.assertGreater(row["conditioned_total_abs_current"], 0.0)
                self.assertEqual(row["carrier_source_kind"], "reconstructed_from_committed_stage_site_spinors")
                self.assertFalse(row["parent_state_vector_row_copied"])

    def test_unified_mechanism_is_instantiated_on_family_c_rows(self) -> None:
        artifact = self.common.write_trajectory_artifact(self.payload)
        self.assertTrue(artifact["sha_verified"])
        self.assertRegex(artifact["content_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(artifact["artifact_file_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(artifact["artifact_file_sha256"], artifact["sidecar_file_sha256"])
        self.assertEqual(artifact["payload"]["state_object_id"], self.payload["integrated_state_object"]["state_object_id"])
        rows = artifact["payload"]["step_rows"]
        self.assertEqual(len({row["state_object_id"] for row in rows}), 1)
        self.assertIn("STEP_DEPENDENT", {row["row_step_class"] for row in rows})
        self.assertIn("INVARIANT", {row["row_step_class"] for row in rows})
        for row in rows:
            with self.subTest(row=row["row_id"]):
                self.assertRegex(row["trajectory_step_id"], r"^manifold_family_c_integrated_v0:step:[0-9]{4}$")
                self.assertRegex(row["row_payload_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(row["row_step_lineage_id"], r"^[0-9a-f]{64}$")
                self.assertTrue(row["sha_verified"])
                self.assertTrue(row["row_step_class_why"])

    def test_surviving_mechanics_and_controls_are_recomputed(self) -> None:
        mechanics = self.payload["surviving_mechanics"]
        self.assertTrue(mechanics["flux_continuity_same_trajectory"]["survives_composition"])
        self.assertTrue(mechanics["conditioned_total_abs_current"]["recomputed_in_run"])
        for rung in ("n3", "n4"):
            with self.subTest(rung=rung):
                current = mechanics["conditioned_total_abs_current"]["per_rung"][rung]
                self.assertGreater(current["recomputed"], 0.0)
                self.assertTrue(math.isclose(current["recomputed"], current["committed"], rel_tol=0.0, abs_tol=1.0e-12))

        controls = self.payload["integration_controls"]
        for name in ("zero_terrain_network", "decoupled_leaf", "scrambled_coupling"):
            with self.subTest(control=name):
                self.assertTrue(controls[name]["fires"], json.dumps(controls[name], sort_keys=True))
                self.assertTrue(controls[name]["moves_named_rows"], controls[name])
                self.assertTrue(controls[name]["demotes_if_not_firing"], controls[name])

    def test_caveats_scope_and_ceiling_are_fenced(self) -> None:
        boundaries = self.payload["carried_boundaries"]
        self.assertIn("G3", boundaries)
        self.assertIn("no committed bare-current parent-row comparison", boundaries["G3"])
        self.assertIn("G4", boundaries)
        self.assertIn("carrier reconstructed, not copied", boundaries["G4"])
        self.assertEqual(self.payload["classification"], "scratch_diagnostic")
        self.assertFalse(self.payload["promotion_allowed"])
        self.assertFalse(self.payload["formal_admission_allowed"])
        for forbidden in ("A+B weld relation", "cross-family weld controls", "flux-carrying L/R asymmetric engine object"):
            self.assertIn(forbidden, self.payload["out_of_scope"])
        self.assertTrue(self.payload["all_pass"], self.payload["failures"])


if __name__ == "__main__":
    unittest.main()
