from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "coratchet_recursive_foundations_v1.card.json"
SPEC = importlib.util.spec_from_file_location("ratchet_card_validator", ROOT / "validate_ratchet_card.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RatchetCardValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.card = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_proposal_card_passes(self) -> None:
        self.assertEqual(MODULE.validate_card(copy.deepcopy(self.card)), [])

    def test_mutation_battery_rejects_every_corruption(self) -> None:
        results = MODULE.mutation_selftest(copy.deepcopy(self.card))
        self.assertTrue(results)
        self.assertTrue(all(results.values()), results)

    def test_unresolved_is_not_removed_from_delta(self) -> None:
        card = copy.deepcopy(self.card)
        card["root_record"]["delta_codomain"] = ["DISTINGUISHABLE", "INDISTINGUISHABLE"]
        self.assertTrue(MODULE.validate_card(card))

    def test_acceptance_without_controls_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["decision"]["status"] = "ACCEPT_PROVISIONAL"
        card["promotion_allowed"] = True
        card["formal_admission_allowed"] = True
        self.assertTrue(MODULE.validate_card(card))

    def test_acceptance_without_earned_dependencies_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["decision"]["status"] = "ACCEPT_PROVISIONAL"
        card["classification"] = "ratchet_survivor"
        card["promotion_allowed"] = True
        card["formal_admission_allowed"] = True
        card["claim"]["required_earned_structures"] = []
        errors = MODULE.validate_card(card)
        self.assertTrue(any("earned-structure dependencies" in error for error in errors), errors)

    def test_probe_earned_without_evidence_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["root_record"]["probe_family_earned"] = True
        errors = MODULE.validate_card(card)
        self.assertTrue(any("probe_family_earned" in error for error in errors), errors)

    def test_empty_required_lanes_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["independent_recomputation"]["required_lanes"] = []
        errors = MODULE.validate_card(card)
        self.assertTrue(any("required_lanes" in error for error in errors), errors)

    def test_zero_recursive_passes_cannot_accept(self) -> None:
        card = copy.deepcopy(self.card)
        card["decision"]["status"] = "ACCEPT_PROVISIONAL"
        card["classification"] = "ratchet_survivor"
        card["promotion_allowed"] = True
        card["formal_admission_allowed"] = True
        errors = MODULE.validate_card(card)
        self.assertTrue(any("recursive passes" in error for error in errors), errors)

    def test_fake_mss_frontier_hash_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["decision"]["status"] = "ACCEPT_PROVISIONAL"
        card["classification"] = "ratchet_survivor"
        card["promotion_allowed"] = True
        card["formal_admission_allowed"] = True
        card["mss"]["frontier"] = ["candidate-a"]
        card["decision"]["mss_frontier_hash"] = "0" * 64
        errors = MODULE.validate_card(card)
        self.assertTrue(any("MSS frontier hash" in error for error in errors), errors)

    def test_ca_cannot_self_promote(self) -> None:
        card = copy.deepcopy(self.card)
        card["ca_hypothesis"]["status"] = "accept_provisional"
        errors = MODULE.validate_card(card)
        self.assertTrue(any("ca_hypothesis" in error for error in errors), errors)

    def test_narrow_candidate_search_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["candidate_search"]["candidate_families"] = ["a", "b"]
        errors = MODULE.validate_card(card)
        self.assertTrue(any("candidate_families" in error for error in errors), errors)

    def test_source_hash_substitution_fails(self) -> None:
        card = copy.deepcopy(self.card)
        card["source_manifest"][0]["sha256"] = "0" * 64
        errors = MODULE.validate_card(card)
        self.assertTrue(any("source hash mismatch" in error for error in errors), errors)

    def test_pass_control_needs_structured_flip_receipt(self) -> None:
        card = copy.deepcopy(self.card)
        card["controls"][0]["status"] = "PASS"
        card["controls"][0]["receipt"] = "not-a-receipt"
        errors = MODULE.validate_card(card)
        self.assertTrue(any("structured receipt" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
