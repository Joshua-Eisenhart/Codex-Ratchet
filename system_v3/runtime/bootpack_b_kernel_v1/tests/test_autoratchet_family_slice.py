import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))

from tools.autoratchet import (  # noqa: E402
    _compatibility_goal_terms_for_profile,
    _required_probe_terms_for_profile,
    _required_probe_terms_for_family_slice,
    _resolve_debate_strategy_from_family_slice,
)


class TestAutoratchetFamilySlice(unittest.TestCase):
    def test_required_probe_terms_for_family_slice_use_sim_hooks(self) -> None:
        family_slice = {
            "sim_hooks": {
                "required_probe_terms": [
                    "finite_dimensional_hilbert_space",
                    "density_matrix",
                    "probe_operator",
                ]
            }
        }
        self.assertEqual(
            (
                "finite_dimensional_hilbert_space",
                "density_matrix",
                "probe_operator",
            ),
            _required_probe_terms_for_family_slice(family_slice),
        )

    def test_scaffold_proof_forces_balanced_debate_strategy(self) -> None:
        family_slice = {"run_mode": "SCAFFOLD_PROOF"}
        self.assertEqual(
            "balanced",
            _resolve_debate_strategy_from_family_slice(family_slice, "graveyard_first_then_recovery"),
        )

    def test_graveyard_validity_upgrades_balanced_debate_strategy(self) -> None:
        family_slice = {"run_mode": "GRAVEYARD_VALIDITY"}
        self.assertEqual(
            "graveyard_first_then_recovery",
            _resolve_debate_strategy_from_family_slice(family_slice, "balanced"),
        )

    def test_compatibility_goal_terms_for_profile_use_reduced_refined_fuel_scaffold(self) -> None:
        self.assertIn("density_matrix", _compatibility_goal_terms_for_profile("refined_fuel"))
        self.assertIn("probe_operator", _compatibility_goal_terms_for_profile("refined_fuel"))
        self.assertNotIn("qit_master_conjunction", _compatibility_goal_terms_for_profile("refined_fuel"))

    def test_required_probe_terms_for_profile_keep_entropy_bookkeeping_bridge_narrow(self) -> None:
        self.assertEqual(
            ("correlation_polarity", "density_entropy"),
            _required_probe_terms_for_profile("entropy_bookkeeping_bridge"),
        )


if __name__ == "__main__":
    unittest.main()
