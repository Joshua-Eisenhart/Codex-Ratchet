#!/usr/bin/env python3
"""Acceptance tests for manifold_family_b_integrated_v0."""

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


EXPECTED_PARENT_CAVEATS = {
    "ratchet_deep_chain_v0:G1_COMPOSITE_GROUP_NOT_EARNED",
    "ratchet_deep_chain_v0:G2_SECOND_Z2_ACTION_UNSPECIFIED",
    "compression_flow_radiated_record_v0:F1_REGISTER_BASIS_SEMANTICS_UNDERPINNED",
    "compression_flow_radiated_record_v0:F2_SMT_ROW_SET_NOT_PAYLOAD_HASH_PROOF",
    "z4_syndrome_record_v0:CAVEAT_JULIA_RECORD_COUNTS_LITERAL",
    "z4_syndrome_record_v0:CAVEAT_SMT_BINDS_COEFFICIENTS_NOT_RAW_TABLES",
    "manifold_entropy_ledger_v0:CAVEAT_SIGNED_LENS_DELTA_LABEL",
    "manifold_unified_run_v0:CAVEAT_Q4_PARENT_RIGIDITY",
}


def has_key_prefix(value, prefix: str) -> bool:
    if isinstance(value, dict):
        return any(str(key).startswith(prefix) or has_key_prefix(item, prefix) for key, item in value.items())
    if isinstance(value, list):
        return any(has_key_prefix(item, prefix) for item in value)
    return False


class ManifoldFamilyBIntegratedV0Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = importlib.import_module("manifold_family_b_integrated_v0_common")
        cls.payload = cls.common.build_family_b_object()

    def test_weld_anchors_recomputed(self) -> None:
        anchors = self.payload["weld_anchors"]
        self.assertEqual(anchors["deep_chain"]["final_denominator"], 16)
        self.assertEqual(anchors["deep_chain"]["composite_order"], 8)
        self.assertEqual(anchors["deep_chain"]["entropy_deltas_exact"], ["-log(4)", "-log(2)", "-log(2)"])
        self.assertAlmostEqual(anchors["deep_chain"]["final_volume_float"], math.pi**2 / 4.0, places=15)
        self.assertEqual(anchors["compression_flow"]["initial_size"], 384)
        self.assertEqual(anchors["compression_flow"]["step0"], {"P_t_size": 384, "P_t_plus_1_size": 288, "Delta_R_t_size": 96})
        self.assertEqual(anchors["compression_flow"]["total_emitted_rows"], 288)
        self.assertEqual(anchors["compression_flow"]["P_T_size"], 96)
        self.assertEqual(anchors["compression_flow"]["max_conservation_defect"], 0)
        self.assertEqual(anchors["conservation"]["defect_nats"], 0.0)
        self.assertAlmostEqual(anchors["conservation"]["state_loss_nats"], math.log(4), places=15)
        self.assertAlmostEqual(anchors["conservation"]["record_retained_nats"], math.log(4), places=15)
        for row in anchors["SMT_rows"].values():
            with self.subTest(row=row["solver"]):
                self.assertEqual(row["verdict"], "unsat")
                self.assertEqual(row["erased_flip_verdict"], "sat")
                self.assertFalse(row["asserted_precomputed_boolean"])

    def test_b1_consumes_pinned_ratchet_row_ledger(self) -> None:
        b1 = self.payload["layers"]["B1_RATCHET_CHAIN"]
        pin = b1["pinned_ratchet_row_ledger"]
        self.assertEqual(pin["source_path"], "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json")
        self.assertEqual(pin["source_json_pointer"], "/ratchet_sequence/per_step_ledger/rows")
        self.assertRegex(pin["pin_block_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual([row["constraint"] for row in b1["reduced_rows"]], [row["constraint"] for row in pin["derived_pin_rows"]])
        self.assertEqual([row["effective_denominator"] for row in b1["reduced_rows"]], [row["effective_denominator"] for row in pin["derived_pin_rows"]])

        control = self.payload["kill_controls"]["stale_import_control"]
        self.assertEqual(control["pin_mutation_surface"], "B1.pinned_ratchet_row_ledger.derived_pin_rows[1].factor")
        self.assertTrue(control["dependent_anchor_mismatches"]["deep_chain_denominator_changed"])
        self.assertNotEqual(control["baseline_b1_pin_block_sha256"], control["mutated_b1_pin_block_sha256"])

    def test_parent_hash_pins_are_consumed_results_only(self) -> None:
        pins = self.payload["source_import_audit"]["parent_hash_pins"]
        for name, row in pins.items():
            with self.subTest(parent=name):
                self.assertIn("results/", row["path"])
                self.assertTrue(row["path"].endswith(".json"))
                self.assertNotIn("audit_verdict.md", row["path"])
                self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")
        audit_context = self.payload["source_import_audit"]["audit_verdict_citation_context_hashes"]
        self.assertTrue(audit_context["ratchet_deep_chain_v0"]["path"].endswith("audit_verdict.md"))

    def test_parent_caveats_are_carried_in_every_reduced_row(self) -> None:
        for layer_name, layer in self.payload["layers"].items():
            reduced_rows = layer["reduced_rows"]
            self.assertGreater(len(reduced_rows), 0, layer_name)
            for row in reduced_rows:
                with self.subTest(layer=layer_name, row=row["row_id"]):
                    caveats = set(row["parent_caveats"])
                    self.assertTrue(EXPECTED_PARENT_CAVEATS <= caveats)
                    self.assertEqual(row["claim_ceiling"], "scratch_diagnostic")

    def test_b2_emits_b_scoped_rows_without_axis0_leakage(self) -> None:
        b2 = self.payload["layers"]["B2_COMPRESSION_RECORD"]
        self.assertFalse(has_key_prefix(b2, "axis0_"))
        self.assertNotIn("axis0_", json.dumps(b2, sort_keys=True))
        first_raw = b2["raw_flow"]["record_entries"][0]
        self.assertIn("b_scoped_support_row", first_raw)
        self.assertIn("b_scoped_probe_row", first_raw)
        self.assertNotIn("canonical_support_row", first_raw)
        self.assertNotIn("canonical_probe_row", first_raw)

    def test_b3_record_rows_carry_row_local_z4_cocitation(self) -> None:
        b3 = self.payload["layers"]["B3_CONSERVATION_ACCOUNTS"]
        expected = "system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json"
        for row in b3["reduced_rows"]:
            with self.subTest(row=row["row_id"]):
                self.assertEqual(row["co_citation"], expected)
                self.assertEqual(row["state_plus_record_convention_label"], "finite_counting_state_plus_record")

    def test_trajectory_artifact_has_one_state_object_and_verified_step_rows(self) -> None:
        artifact = self.common.write_trajectory_artifact(self.payload)
        self.assertTrue(artifact["sha_verified"])
        self.assertRegex(artifact["content_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(artifact["artifact_file_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(artifact["artifact_file_sha256"], artifact["sidecar_file_sha256"])
        self.assertEqual(artifact["payload"]["state_object_id"], self.payload["state_object_id"])
        step_rows = artifact["payload"]["step_rows"]
        self.assertEqual(len({row["state_object_id"] for row in step_rows}), 1)
        classes = {row["row_step_class"] for row in step_rows}
        self.assertIn("STEP_DEPENDENT", classes)
        self.assertIn("CARRIED", classes)
        for row in step_rows:
            with self.subTest(step=row["step_index"], family=row["row_family"]):
                self.assertRegex(row["row_payload_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(row["sha_verified"])
                self.assertRegex(row["trajectory_step_id"], r"^manifold_family_b_integrated_v0:step:[0-9]{4}$")
                self.assertRegex(row["row_step_lineage_id"], r"^[0-9a-f]{64}$")
                self.assertTrue(row["row_step_class_why"])

    def test_layers_are_not_decorative(self) -> None:
        controls = self.payload["kill_controls"]["decorative_layer_detector"]
        self.assertEqual(sorted(controls), ["B1_RATCHET_CHAIN", "B2_COMPRESSION_RECORD", "B3_CONSERVATION_ACCOUNTS", "B4_TYPED_LEDGER"])
        for layer, row in controls.items():
            with self.subTest(layer=layer):
                self.assertTrue(row["fires"], row)
                self.assertNotEqual(row["baseline_row_signature"], row["perturbed_row_signature"])
                self.assertEqual(row["changed_layer"], layer)

    def test_honest_mode_and_fences(self) -> None:
        self.assertEqual(self.payload["engine_mode"], "julia_orbit_counts_plus_shared_python_common_builder")
        self.assertEqual(self.payload["classification"], "scratch_diagnostic")
        self.assertFalse(self.payload["promotion_allowed"])
        self.assertFalse(self.payload["formal_admission_allowed"])
        self.assertFalse(self.payload["family_a_rows_used"])
        self.assertFalse(self.payload["two_engine_rows_used"])
        self.assertTrue(self.payload["all_pass"], self.payload["failures"])


if __name__ == "__main__":
    unittest.main()
