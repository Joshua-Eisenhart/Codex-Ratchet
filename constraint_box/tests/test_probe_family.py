from __future__ import annotations

import unittest

from constraintbox.probe_family import ProbeFamily, evaluate_probe_family


class ProbeFamilyTest(unittest.TestCase):
    def test_boundary_requires_exactly_one_changed_field(self) -> None:
        family = ProbeFamily.from_dict({
            "gate_id": "test:gate",
            "probes": [
                {"probe_id": "a", "input_ref": {"x": 0, "y": 0}, "expected": "admitted"},
                {"probe_id": "b", "input_ref": {"x": 1, "y": 0}, "expected": "bad_x"},
            ],
            "boundary_pairs": [{"probe_a": "a", "probe_b": "b", "differing_field": "x", "expected_flip": True}],
            "deciders": [{"decider_id": "one", "tool": "one", "how_it_decides": "x"}, {"decider_id": "two", "tool": "two", "how_it_decides": "x"}],
        })
        result = evaluate_probe_family(family, {"one": lambda x: "admitted" if x["x"] == 0 else "bad_x", "two": lambda x: "admitted" if x["x"] == 0 else "bad_x"})
        self.assertTrue(result["non_constant"])
        self.assertTrue(result["boundary_mapped"])

    def test_disagreement_is_first_class_and_blocks_mapping(self) -> None:
        family = ProbeFamily.from_dict({
            "gate_id": "test:gate",
            "probes": [{"probe_id": "a", "input_ref": {"x": 0}, "expected": "admitted"}],
            "boundary_pairs": [],
            "deciders": [{"decider_id": "one", "tool": "one", "how_it_decides": "x"}, {"decider_id": "two", "tool": "two", "how_it_decides": "x"}],
        })
        result = evaluate_probe_family(family, {"one": lambda _: "admitted", "two": lambda _: "bad"})
        self.assertEqual(len(result["disagreements"]), 1)
        self.assertFalse(result["boundary_mapped"])

    def test_expected_verdict_is_checked(self) -> None:
        family = ProbeFamily.from_dict({
            "gate_id": "test:gate",
            "probes": [{"probe_id": "a", "input_ref": {"x": 0}, "expected": "wrong"}],
            "boundary_pairs": [],
            "deciders": [{"decider_id": "one", "tool": "one", "how_it_decides": "x"}, {"decider_id": "two", "tool": "two", "how_it_decides": "x"}],
        })
        result = evaluate_probe_family(family, {"one": lambda _: "admitted", "two": lambda _: "admitted"})
        self.assertEqual(result["expected_mismatches"][0]["probe_id"], "a")


if __name__ == "__main__":
    unittest.main()
