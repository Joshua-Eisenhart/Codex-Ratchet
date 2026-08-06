from __future__ import annotations

import unittest

from constraintbox import ObservationBundle, derive_candidate, ratchet_frontier
from constraintbox.ratchet import continuation_congruent


class RatchetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = ObservationBundle.build(
            presentations=("h0", "h1", "h2", "h3"),
            probe_ids=("p0", "p1", "p2", "q"),
            outcomes=(
                (0, 0, 0, 0),
                (0, 1, 0, 1),
                (1, 0, 0, 0),
                (1, 0, 1, 1),
            ),
        )
        witness = "nest-witness"
        self.c0 = derive_candidate(
            self.bundle,
            "C0",
            ("p0",),
            chain_id="P",
            nesting_witness_sha256=witness,
        )
        self.c1 = derive_candidate(
            self.bundle,
            "C1",
            ("p0", "p1"),
            chain_id="P",
            nesting_witness_sha256=witness,
        )
        self.c2 = derive_candidate(
            self.bundle,
            "C2",
            ("p0", "p1", "p2"),
            chain_id="P",
            nesting_witness_sha256=witness,
        )
        self.q = derive_candidate(
            self.bundle,
            "Q",
            ("q",),
            chain_id=None,
            nesting_witness_sha256=None,
        )

    def test_expected_partitions(self) -> None:
        self.assertEqual(self.c0.partition, (0, 0, 1, 1))
        self.assertEqual(self.c1.partition, (0, 1, 2, 2))
        self.assertEqual(self.c2.partition, (0, 1, 2, 3))
        self.assertEqual(self.q.partition, (0, 1, 0, 1))

    def test_empty_demand_holds(self) -> None:
        result = ratchet_frontier((self.c0, self.c1, self.c2), ())
        self.assertEqual(result.verdict, "HOLD")
        self.assertEqual(result.hold_reason, "EMPTY_DEMAND")

    def test_frontier_is_packet_relative_and_plural(self) -> None:
        result = ratchet_frontier(
            (self.c0, self.c1, self.c2, self.q),
            ((0, 1),),
        )
        self.assertEqual(result.verdict, "PACKET_RELATIVE_FRONTIER")
        self.assertEqual(result.survivors, ("C1", "C2", "Q"))
        self.assertEqual(result.frontier, ("C1",))
        self.assertEqual(result.uncompared_live, ("Q",))
        self.assertFalse(result.absolute_mss_claimed)
        self.assertIsNone(result.winner)

    def test_flat_candidates_are_not_silently_ranked(self) -> None:
        left = derive_candidate(
            self.bundle,
            "L",
            ("p0", "p1"),
            chain_id=None,
            nesting_witness_sha256=None,
        )
        right = derive_candidate(
            self.bundle,
            "R",
            ("p0", "p1", "p2"),
            chain_id=None,
            nesting_witness_sha256=None,
        )
        result = ratchet_frontier((left, right), ((0, 1),))
        self.assertEqual(result.verdict, "HOLD")
        self.assertEqual(result.hold_reason, "NO_COMPARABLE_NEST")

    def test_candidate_cannot_change_probe_contract(self) -> None:
        other = ObservationBundle.build(
            presentations=("h0", "h1", "h2", "h3"),
            probe_ids=("other",),
            outcomes=((0,), (1,), (0,), (1,)),
        )
        rival = derive_candidate(
            other,
            "R",
            ("other",),
            chain_id="P",
            nesting_witness_sha256="nest-witness",
        )
        result = ratchet_frontier((self.c1, rival), ((0, 1),))
        self.assertEqual(result.verdict, "HOLD")
        self.assertEqual(result.hold_reason, "CONTRACT_MISMATCH")

    def test_continuation_mutation_breaks_congruence(self) -> None:
        good, witness = continuation_congruent(self.c1.partition, (1, 0, 2, 3))
        self.assertTrue(good)
        self.assertIsNone(witness)
        good, witness = continuation_congruent(self.c1.partition, (1, 0, 0, 3))
        self.assertFalse(good)
        self.assertEqual(witness, (2, 3))


if __name__ == "__main__":
    unittest.main()
