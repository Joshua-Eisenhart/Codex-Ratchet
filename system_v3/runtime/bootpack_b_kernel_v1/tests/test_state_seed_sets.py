import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from state import DERIVED_ONLY_TERMS, L0_LEXEME_SET  # noqa: E402


class TestStateSeedSets(unittest.TestCase):
    def test_l0_lexeme_set_matches_thread_b_contract_seed(self) -> None:
        # Thread B v3.9.13 enforceable contract extract (system_v3/specs/17...) defines
        # a tiny bootstrap L0 set. This must not silently expand (implicit ontology admission).
        expected = {
            "finite",
            "dimensional",
            "hilbert",
            "space",
            "density",
            "matrix",
            "operator",
            "channel",
            "cptp",
            "unitary",
            "lindblad",
            "hamiltonian",
            "commutator",
            "anticommutator",
            "trace",
            "partial",
            "tensor",
            "superoperator",
            "generator",
        }
        self.assertEqual(expected, set(L0_LEXEME_SET))

    def test_derived_only_terms_matches_thread_b_contract_seed(self) -> None:
        expected = {
            "equal",
            "equality",
            "same",
            "identity",
            "coordinate",
            "cartesian",
            "origin",
            "center",
            "frame",
            "metric",
            "distance",
            "norm",
            "angle",
            "radius",
            "time",
            "before",
            "after",
            "past",
            "future",
            "cause",
            "because",
            "therefore",
            "implies",
            "results",
            "leads",
            "optimize",
            "maximize",
            "minimize",
            "utility",
            "map",
            "maps",
            "mapping",
            "mapped",
            "apply",
            "applies",
            "applied",
            "application",
            "uniform",
            "uniformly",
            "unique",
            "uniquely",
            "real",
            "integer",
            "integers",
            "natural",
            "naturals",
            "number",
            "numbers",
            "count",
            "counting",
            "probability",
            "random",
            "ratio",
            "proportion",
            "statistics",
            "statistical",
            "platonic",
            "platon",
            "platonism",
            "one",
            "two",
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "function",
            "functions",
            "mapping_of",
            "implies_that",
            "complex",
            "quaternion",
            "quaternions",
            "imaginary",
            "i_unit",
            "j_unit",
            "k_unit",
            "set",
            "relation",
            "domain",
            "codomain",
        }
        self.assertEqual(expected, set(DERIVED_ONLY_TERMS))


if __name__ == "__main__":
    unittest.main()

