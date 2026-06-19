#!/usr/bin/env python3
"""Acceptance tests for manifold_super_sim_v0."""

from __future__ import annotations

import importlib
import math
import sys
import unittest
from pathlib import Path


PACKET_DIR = Path(__file__).resolve().parents[1]
if str(PACKET_DIR) not in sys.path:
    sys.path.insert(0, str(PACKET_DIR))


class ManifoldSuperSimV0Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.common = importlib.import_module("manifold_super_sim_v0_common")
        cls.payload = cls.common.build_super_object(cls.common.scipy_expm)

    def test_weld_anchors_recomputed(self) -> None:
        anchors = self.payload["weld_anchors"]
        self.assertEqual(
            anchors["G0_transition_graph_sha256"]["computed"],
            anchors["G0_transition_graph_sha256"]["expected"],
        )
        self.assertEqual(
            anchors["G0_transition_graph_sha256"]["computed"],
            "bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0",
        )
        self.assertEqual(anchors["G1_partition"]["terminal_class_sizes"], [1, 14, 18])
        self.assertTrue(anchors["G1_partition"]["may_equals_must"])
        self.assertEqual(anchors["rotated_chart"]["rotated_terminal_class_count"], 2)
        self.assertEqual(anchors["rotated_chart"]["refined_terminal_counts"], {"2x": 3, "3x": 3})
        self.assertAlmostEqual(anchors["D_z_information"]["holevo_nats"], 0.411341122022618, places=15)
        self.assertAlmostEqual(anchors["D_z_information"]["killed_nats"], 0.28180605853732726, places=15)
        self.assertAlmostEqual(anchors["stage_word_endpoint"]["word_output_information_nats"], 0.0932927444282512, places=15)

    def test_layers_are_not_decorative(self) -> None:
        controls = self.payload["kill_controls"]
        self.assertTrue(controls["stale_import_control"]["fires"])
        self.assertTrue(controls["order_shuffled_N01"]["fires"])
        self.assertTrue(controls["root_off_similarity_only_guard"]["fires"])
        self.assertTrue(controls["quotient_erased"]["fires"])
        for layer, row in controls["decorative_layer_detector"].items():
            with self.subTest(layer=layer):
                self.assertTrue(row["fires"], row)

    def test_source_locks_pin_consumed_result_paths(self) -> None:
        pins = self.payload["source_import_audit"]["parent_hash_pins"]
        self.assertTrue(pins["geo_s4_operator_stage_v0"]["path"].endswith("_envelope_results.json"))
        self.assertTrue(pins["geo_s5_terrain_flows_v0"]["path"].endswith("_envelope_results.json"))
        self.assertNotIn("audit_verdict.md", pins["geo_s4_operator_stage_v0"]["path"])
        audit_context = self.payload["source_import_audit"]["audit_verdict_citation_context_hashes"]
        self.assertTrue(audit_context["geo_s4_operator_stage_v0"]["path"].endswith("audit_verdict.md"))

    def test_reduced_g1_fusion_rows_keep_chart_label(self) -> None:
        l4 = self.payload["layers"]["L4_FUSION"]
        for row_family in ["terminal_class_restricted_throughput", "basin_conditioned_may_must_flow"]:
            g1_rows = [row for row in l4[row_family] if row["set_id"] == "G1"]
            self.assertEqual(len(g1_rows), 3)
            for row in g1_rows:
                with self.subTest(row_family=row_family, row_id=row["row_id"]):
                    self.assertEqual(row["chart_relative_label"], "G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE")
                    self.assertIn("chart-relative terminal classes", row["chart_relative_note"])

    def test_ledger_typed_consistency(self) -> None:
        ledger = self.payload["layers"]["L5_LEDGER"]
        self.assertTrue(ledger["typed_consistency_matrix"]["all_rows_typed"])
        self.assertTrue(ledger["typed_consistency_matrix"]["cross_type_accounts_have_conventions"])
        self.assertFalse(ledger["typed_consistency_matrix"]["forbidden_cross_type_sum_found"])
        self.assertTrue(self.payload["all_pass"], self.payload["failures"])

    def test_trajectory_artifact_is_sha_verified(self) -> None:
        artifact = self.common.write_trajectory_artifact()
        self.assertTrue(artifact["sha_verified"])
        self.assertEqual(artifact["payload"]["state_object_id"], self.payload["state_object_id"])
        self.assertEqual(artifact["payload_sha256"], artifact["sidecar_sha256"])


if __name__ == "__main__":
    unittest.main()
