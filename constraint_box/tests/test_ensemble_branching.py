from __future__ import annotations

import unittest

from constraintbox import BranchLedger, FiniteHistoryEnsemble, MergeEvidence, PruneEvidence
from constraintbox.branching import BranchStatus
from constraintbox.ensemble import diagonal_history_field, history_pair_field


class EnsembleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ensemble = FiniteHistoryEnsemble.from_mappings(
            [
                {"past": 0, "present": "a", "future": 0},
                {"past": 0, "present": "a", "future": 1},
                {"past": 1, "present": "b", "future": 1},
            ]
        )

    def test_present_is_projection_of_complete_histories(self) -> None:
        self.assertEqual(self.ensemble.project(("present",)), (("a",), ("b",)))

    def test_extension_fibre_capacity(self) -> None:
        a = self.ensemble.extension_fibre(("present",), ("a",))
        b = self.ensemble.extension_fibre(("present",), ("b",))
        empty = self.ensemble.extension_fibre(("present",), ("c",))
        self.assertEqual(a.count, 2)
        self.assertEqual(a.hartley_capacity_bits, 1.0)
        self.assertEqual(b.count, 1)
        self.assertEqual(b.hartley_capacity_bits, 0.0)
        self.assertEqual(empty.count, 0)
        self.assertIsNone(empty.hartley_capacity_bits)

    def test_complex_path_sum_can_cancel_without_deleting_histories(self) -> None:
        weights = {
            self.ensemble.histories[0]: 1 + 0j,
            self.ensemble.histories[1]: -1 + 0j,
            self.ensemble.histories[2]: 0 + 0j,
        }
        self.assertEqual(self.ensemble.finite_sum(weights), 0j)
        self.assertEqual(self.ensemble.count, 3)

    def test_history_pair_field_retains_off_diagonal(self) -> None:
        field = history_pair_field((1 / 2**0.5, 1j / 2**0.5))
        diagonal = diagonal_history_field(field)
        self.assertNotEqual(field[0][1], 0j)
        self.assertEqual(diagonal[0][1], 0j)
        self.assertEqual(field[0][0], diagonal[0][0])


class BranchLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = BranchLedger()
        self.ledger.add("A", {"candidate": "A"})
        self.ledger.add("B", {"candidate": "B"})

    def test_unearned_pruning_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "pruning_not_earned"):
            self.ledger.prune(
                "A",
                PruneEvidence("contract", 1, "BOUNDED_UNSAT", "evidence"),
            )
        self.assertEqual(self.ledger.branches["A"].status, BranchStatus.LIVE)

    def test_empty_fibre_unsat_prunes_but_preserves_record(self) -> None:
        self.ledger.prune(
            "A",
            PruneEvidence("contract", 0, "BOUNDED_UNSAT", "artifact:deadbeef"),
        )
        self.assertIn("A", self.ledger.branches)
        self.assertEqual(self.ledger.branches["A"].status, BranchStatus.PRUNED)

    def test_merge_requires_all_continuations_to_match(self) -> None:
        evidence = MergeEvidence(
            ("probe",),
            ("c0", "c1"),
            (("c0", (0,)), ("c1", (1,))),
            (("c0", (0,)), ("c1", (2,))),
            "contract",
        )
        with self.assertRaisesRegex(ValueError, "distinguishable"):
            self.ledger.merge("A", "B", "AB", {"merged": True}, evidence)

    def test_earned_merge_preserves_parent_lineage(self) -> None:
        observations = (("c0", (0,)), ("c1", (1,)))
        evidence = MergeEvidence(
            ("probe",),
            ("c0", "c1"),
            observations,
            observations,
            "contract",
        )
        merged = self.ledger.merge("A", "B", "AB", {"merged": True}, evidence)
        self.assertEqual(merged.parents, ("A", "B"))
        self.assertEqual(self.ledger.branches["A"].status, BranchStatus.MERGED)
        self.assertEqual(self.ledger.branches["B"].status, BranchStatus.MERGED)
        self.assertEqual(self.ledger.branches["AB"].status, BranchStatus.LIVE)


if __name__ == "__main__":
    unittest.main()
