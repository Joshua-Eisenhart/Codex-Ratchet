import unittest

from contract import CandidatePackage, Carrier, ControlSet, NestInterface
from gates import (
    Verdict,
    distinction_adequacy_gate,
    gauge_rejection_gate,
    operational_reidentification_gate,
    order_honesty_gate,
)


class _BaseCandidate(CandidatePackage):
    @property
    def carrier(self):
        return Carrier("finite test carrier", ("inc", "double"))

    def states(self):
        return (0, 1, 2)

    def probes(self):
        return ("observe",)

    def apply(self, op, state):
        if op == "observe":
            return state
        if op == "inc":
            return state + 1
        if op == "double":
            return state * 2
        raise ValueError(op)

    def reidentify(self, record, current_state):
        return record == current_state

    def persist(
        self, state, *, perturbation=None, delay=0,
        partial_access=None, relabeled=False,
    ):
        return state

    def evolve(self, new_constraint):
        return self

    def nest_interface(self):
        return NestInterface()

    def declared_primitives(self):
        return ()

    def controls(self):
        return ControlSet()


class _MergedOrderCandidate(_BaseCandidate):
    def reidentify(self, record, current_state):
        return True


class _CollapsedCandidate(_BaseCandidate):
    def reidentify(self, record, current_state):
        return True


class _IntransitiveCandidate(_BaseCandidate):
    def reidentify(self, record, current_state):
        return abs(record - current_state) <= 1


class _GaugeCandidate(_BaseCandidate):
    @property
    def carrier(self):
        return Carrier("value quotient with raw labels", ("noop",))

    def states(self):
        return ((0, "red"), (2, "red"), (1, "blue"))

    def probes(self):
        return ("read_value",)

    def apply(self, op, state):
        if op == "read_value":
            return state[-1]
        if op == "noop":
            return state
        raise ValueError(op)

    def reidentify(self, record, current_state):
        return record[-1] == current_state[-1]

    def persist(
        self, state, *, perturbation=None, delay=0,
        partial_access=None, relabeled=False,
    ):
        if relabeled:
            return ("gauge", state[0] + 100, state[1])
        return state


class _GaugeRefiningCandidate(_GaugeCandidate):
    def reidentify(self, record, current_state):
        if record[0] == "gauge" and current_state[0] == "gauge":
            return record[1] == current_state[1]
        return record[-1] == current_state[-1]


class _GaugeCollapsingCandidate(_GaugeCandidate):
    def reidentify(self, record, current_state):
        if record[0] == "not-a-bijection" and current_state[0] == "not-a-bijection":
            return True
        return super().reidentify(record, current_state)

    def persist(
        self, state, *, perturbation=None, delay=0,
        partial_access=None, relabeled=False,
    ):
        if relabeled:
            return ("not-a-bijection", state[0], state[1])
        return state


class MissingGateTests(unittest.TestCase):
    def test_order_honesty_pass(self):
        result = order_honesty_gate(_BaseCandidate(), (1,), ())
        self.assertEqual(result.verdict, Verdict.PASS)
        self.assertEqual(result.reasons["observably_noncommuting_words"], 1)

    def test_order_honesty_fail_has_concrete_word(self):
        result = order_honesty_gate(_MergedOrderCandidate(), (1,), ())
        self.assertEqual(result.verdict, Verdict.FAIL)
        witness = result.reasons["silently_merged_noncommuting_orders"][0]
        self.assertEqual(witness["state"], "1")
        self.assertEqual(witness["order_ab"], ["'inc'", "'double'"])
        self.assertEqual(witness["order_ba"], ["'double'", "'inc'"])
        self.assertEqual(witness["result_ab"], "4")
        self.assertEqual(witness["result_ba"], "3")
        self.assertEqual(witness["fingerprint_ab"], "(4,)")
        self.assertEqual(witness["fingerprint_ba"], "(3,)")

    def test_distinction_adequacy_pass(self):
        result = distinction_adequacy_gate(_BaseCandidate(), (0, 1), ((0, 1),))
        self.assertEqual(result.verdict, Verdict.PASS)
        self.assertEqual(result.reasons["collapsed"], 0)

    def test_distinction_adequacy_fail_has_collapsed_edge(self):
        result = distinction_adequacy_gate(_CollapsedCandidate(), (0, 1), ((0, 1),))
        self.assertEqual(result.verdict, Verdict.FAIL)
        self.assertEqual(
            result.reasons["collapsed_distinction_demand_edges"],
            [["0", "1"]],
        )

    def test_operational_reidentification_pass(self):
        result = operational_reidentification_gate(_BaseCandidate(), (0, 1, 2), ())
        self.assertEqual(result.verdict, Verdict.PASS)
        self.assertEqual(result.reasons["reidentify_internal_contradictions"], [])

    def test_operational_reidentification_fail_has_denied_pair(self):
        result = operational_reidentification_gate(
            _IntransitiveCandidate(), (0, 1, 2), ()
        )
        self.assertEqual(result.verdict, Verdict.FAIL)
        self.assertIn(
            ["0", "2"],
            result.reasons["reidentify_internal_contradictions"],
        )

    def test_gauge_rejection_pass(self):
        candidate = _GaugeCandidate()
        X = candidate.states()
        result = gauge_rejection_gate(candidate, X, ((X[0], X[2]),))
        self.assertEqual(result.verdict, Verdict.PASS)
        self.assertEqual(result.reasons["base_partition"], [0, 0, 1])
        self.assertEqual(result.reasons["relabeled_partition"], [0, 0, 1])

    def test_gauge_rejection_fail_has_changed_pair(self):
        candidate = _GaugeRefiningCandidate()
        X = candidate.states()
        result = gauge_rejection_gate(candidate, X, ((X[0], X[2]),))
        self.assertEqual(result.verdict, Verdict.FAIL)
        witness = result.reasons["relabeling_changed_partition_relations"][0]
        self.assertEqual(
            witness["original_pair"],
            ["(0, 'red')", "(2, 'red')"],
        )
        self.assertEqual(
            witness["relabeled_pair"],
            ["('gauge', 100, 'red')", "('gauge', 102, 'red')"],
        )
        self.assertTrue(witness["base_same_block"])
        self.assertFalse(witness["relabeled_same_block"])

    def test_gauge_rejection_holds_when_declared_relabeling_is_not_injective(self):
        candidate = _GaugeCollapsingCandidate()
        X = candidate.states()
        result = gauge_rejection_gate(candidate, X, ((X[0], X[2]),))
        self.assertEqual(result.verdict, Verdict.HOLD)
        self.assertEqual(
            result.reasons["colliding_relabelings"],
            [{
                "relabeled_states": [
                    "('not-a-bijection', 0, 'red')",
                    "('not-a-bijection', 2, 'red')",
                    "('not-a-bijection', 1, 'blue')",
                ],
                "original_states": [
                    "(0, 'red')", "(2, 'red')", "(1, 'blue')",
                ],
                "original_partition_blocks": [0, 1],
                "relabeled_partition_block": 0,
            }],
        )
        self.assertEqual(result.reasons["relabeled_distinct_state_count"], 1)
        self.assertEqual(result.reasons["original_distinct_state_count"], 2)


if __name__ == "__main__":
    unittest.main()
