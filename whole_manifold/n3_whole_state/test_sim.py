from __future__ import annotations

import unittest

import numpy as np

from manifold_sim import (
    Diagram,
    WholeCandidate,
    derived_marginals,
    global_marginal_witness,
    instrument_records,
    make_initial_state,
    pareto_frontier,
    partial_trace,
    run_campaign,
    same_boundary_different_bulk_control,
    sbs_diagnostics,
    sbs_falsification_controls,
)


class CoreMathTests(unittest.TestCase):
    def test_three_qubit_partial_trace(self) -> None:
        rho = make_initial_state()
        self.assertEqual(rho.shape, (8, 8))
        self.assertEqual(partial_trace(rho, (0,)).shape, (2, 2))
        self.assertEqual(partial_trace(rho, (0, 2)).shape, (4, 4))
        self.assertAlmostEqual(float(np.trace(partial_trace(rho, (0, 2))).real), 1.0, places=12)

    def test_instrument_is_explicit_and_complete(self) -> None:
        receipt = instrument_records(make_initial_state())
        self.assertLess(receipt["completeness_error"], 1.0e-12)
        self.assertAlmostEqual(receipt["probability_sum"], 1.0, places=12)

    def test_broadcast_seed_has_fragment_information(self) -> None:
        sbs = sbs_diagnostics(make_initial_state())
        self.assertGreater(sbs["min_fragment_guessing_probability"], 0.95)
        # The deliberately added 1.5% white noise makes exact orthogonality
        # false; the fragments remain strongly distinguishable.
        self.assertLess(sbs["max_fragment_root_fidelity"], 0.2)

    def test_global_witness_rejects_declared_marginal_lie(self) -> None:
        rho = make_initial_state()
        declared = derived_marginals(rho)
        declared["S"] = np.array([[0.5, 0], [0, 0.5]], dtype=complex)
        diagram = Diagram(
            "ok", ((0, 1), (1, 2), (0, 2)), 5,
            {(0, 1): 1, (1, 2): 1, (0, 2): 2},
        )
        result = global_marginal_witness(
            WholeCandidate("bad", diagram, rho, "control", declared_marginals=declared)
        )
        self.assertFalse(result["globally_consistent"])

    def test_z5_obstruction_and_renesting(self) -> None:
        bad = Diagram(
            "bad", ((0, 1), (1, 2), (0, 2)), 5,
            {(0, 1): 1, (1, 2): 1, (0, 2): 0},
        )
        path = Diagram("path", ((0, 1), (1, 2)), 5, {(0, 1): 1, (1, 2): 1})
        self.assertEqual(bad.obstruction(), 2)
        self.assertFalse(bad.compatible())
        self.assertTrue(path.compatible())

    def test_sbs_falsification_controls_move_expected_diagnostics(self) -> None:
        controls = sbs_falsification_controls(make_initial_state())
        self.assertTrue(controls["all_checks_pass"])
        self.assertAlmostEqual(
            controls["record_erasure_both_fragments"]["min_fragment_guessing_probability"],
            controls["prior_only_guessing_probability"],
            places=10,
        )
        self.assertLess(
            controls["phase_scramble_system_pointer_basis"]["system_dephasing_trace_distance"],
            1.0e-10,
        )
        guesses = controls["single_fragment_guessing_probabilities"]
        self.assertGreater(max(guesses) - min(guesses), 0.25)

    def test_same_boundary_different_bulk_probe(self) -> None:
        control = same_boundary_different_bulk_control()
        self.assertTrue(control["boundary_indistinguishable"])
        self.assertTrue(control["interior_probe_distinguishes"])
        self.assertAlmostEqual(control["epsilon_Pi"], 2.0, places=12)
        self.assertFalse(control["compression_sufficient_for_interior_probe"])

    def test_pareto_keeps_incomparables_and_default(self) -> None:
        def row(cid: str, a: float, guess: float, default: bool = False):
            return {
                "candidate_id": cid,
                "admitted": True,
                "is_default": default,
                "sbs": {
                    "system_dephasing_trace_distance": a,
                    "max_fragment_root_fidelity": a,
                    "conditional_mutual_information_E1_E2_given_S": a,
                    "min_fragment_guessing_probability": guess,
                },
                "topology": {"structural_charge": 0},
            }
        result = pareto_frontier([row("a", 0.1, 0.5, True), row("b", 0.2, 0.9)])
        self.assertEqual(set(result["frontier_ids"]), {"a", "b"})
        self.assertIn("a", result["runnable_ids"])
        self.assertFalse(result["scalarization_used"])


class CampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.receipt = run_campaign()

    def test_campaign_checks(self) -> None:
        failed = [name for name, value in self.receipt["checks"].items() if not value]
        self.assertEqual(failed, [])
        self.assertTrue(self.receipt["all_checks_pass"])

    def test_ordered_and_coherent_semantics_separate(self) -> None:
        self.assertEqual(
            set(self.receipt["ordered_hypotheses"]),
            {"H_native", "H_select", "H_all4", "H_mix"},
        )
        coherent = self.receipt["coherent_history_candidate"]
        self.assertFalse(coherent["trace_preserving"])
        self.assertFalse(coherent["ordered_channel_replacement"])

    def test_full_resettlement_has_renested_candidate(self) -> None:
        rows = self.receipt["settlement"]["iteration_1_full_resettlement"]
        renested = next(row for row in rows if row["candidate_id"] == "H_native_renested")
        torn = next(row for row in rows if row["candidate_id"] == "H_native_torn")
        self.assertTrue(renested["admitted"])
        self.assertFalse(torn["admitted"])

    def test_preregistered_controls_are_in_receipt(self) -> None:
        controls = self.receipt["controls"]
        self.assertTrue(controls["sbs_falsification_controls"]["all_checks_pass"])
        bulk = controls["same_boundary_different_interior_bulk"]
        self.assertGreater(bulk["epsilon_Pi"], bulk["tolerance"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
