from __future__ import annotations

import unittest

from constraintbox.campaign_path_mass import (
    EXPECTED_GATE_ROWS,
    EXPECTED_PROBE_ROWS,
    OPERATION,
    load_campaign,
    mutation_graph,
    run_campaign_path_mass,
)


class CampaignPathMassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = run_campaign_path_mass()

    def test_uses_replayed_campaign_hashes(self) -> None:
        gen = self.receipt["generator"]
        self.assertEqual(gen["probe_rows_sha256"], EXPECTED_PROBE_ROWS)
        self.assertEqual(gen["gate_rows_sha256"], EXPECTED_GATE_ROWS)
        self.assertEqual(gen["n_probe_rows"], 6144)
        self.assertEqual(gen["n_qit_pass"], 2048)
        self.assertEqual(gen["n_both_pass"], 972)

    def test_reconstructed_map_matches_campaign_compact_map(self) -> None:
        replay = self.receipt["map_replay"]
        self.assertTrue(replay["matches_compact_map"])
        self.assertEqual(replay["n_nodes"], 972)
        self.assertEqual(replay["n_edges"], 3354)
        self.assertEqual(replay["components"], 2)
        self.assertEqual(replay["component_sizes"], [836, 136])
        self.assertEqual(replay["boundary_edge_count"], 40)

    def test_minilev_ratchet_contracts_support_and_graph(self) -> None:
        steps = {item["step"]: item for item in self.receipt["ratchet"]}
        self.assertEqual(steps["minilev_topology_pass"]["n_rows"], 6144)
        self.assertEqual(steps["minilev_proposal_gate"]["n_rows"], 2048)
        self.assertEqual(steps["minilev_claim_gate"]["n_rows"], 972)
        self.assertTrue(steps["minilev_proposal_gate"]["changes_entropy"])
        self.assertTrue(steps["minilev_proposal_gate"]["changes_topology"])
        self.assertTrue(steps["minilev_claim_gate"]["changes_entropy"])
        self.assertTrue(steps["minilev_claim_gate"]["changes_topology"])

    def test_probe_restriction_splits_entropy_from_topology(self) -> None:
        restriction = self.receipt["probe_restriction"]
        self.assertTrue(restriction["changes_entropy"])
        self.assertFalse(restriction["changes_topology"])

    def test_erased_bond_has_no_gated_survivor(self) -> None:
        erased = next(
            item for item in self.receipt["independent"] if item["id"] == "erase_bond"
        )
        self.assertEqual(erased["selected_survivors"], 0)
        self.assertEqual(erased["n_rows"], 1536)

    def test_smt_writes_disposition_on_the_real_rows(self) -> None:
        receipt = self.receipt
        self.assertEqual(receipt["operation"], OPERATION)
        self.assertEqual(receipt["status"], "PASS")
        self.assertFalse(receipt["promotion_allowed"])
        self.assertEqual(receipt["smt"]["real_memory"]["z3"], "BOUNDED_SAT")
        self.assertEqual(receipt["smt"]["erased_memory"]["z3"], "BOUNDED_UNSAT")
        self.assertTrue(receipt["smt"]["real_memory"]["agree"])
        self.assertEqual(receipt["disposition"]["admit_hostile"], 0)
        self.assertEqual(receipt["disposition"]["admit_same_object"], 0)
        self.assertEqual(receipt["recall"]["erased"]["survivors"]["hash_lookup"], 0)
        masses = receipt["ratchet"][-1]["mass"]
        self.assertTrue(masses)
        self.assertEqual(sum(item["size"] for item in masses), 972)

    def test_named_dof_graph_not_json_key_order(self) -> None:
        campaign = load_campaign(
            __import__("pathlib").Path(
                "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/receipts/manifold_capability/v1/rerun1"
            )
        )
        both = [
            row
            for row in campaign["rows"]
            if row["observation"]["qit_validity"] == "PASS"
            and row["observation"]["spinor_memory"] == "PASS"
        ]
        graph = mutation_graph(both)
        self.assertEqual(graph["n_edges"], 3354)


if __name__ == "__main__":
    unittest.main()
