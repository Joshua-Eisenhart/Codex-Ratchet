#!/usr/bin/env python3
import unittest

import manifold_ijk_engine_prototype as model


class PrototypeTests(unittest.TestCase):
    def test_finite_path_sum_is_bounded_and_interferes(self):
        result = model.finite_path_sum(model.idx(0, 0), +1)
        self.assertGreater(result["path_count"], 0)
        self.assertLessEqual(result["path_count"], 5 ** model.HORIZON)
        self.assertGreater(result["interference_l1"], 0.0)

    def test_axis0_is_local_ijk_field(self):
        result = model.run_engine(-1, ticks=4)
        self.assertEqual(len(result.axis0_ijk_final), model.N)
        self.assertEqual(set(result.axis0_ijk_final[0]), {"shell", "angle", "i", "j", "k"})

    def test_two_hands_run_and_differ(self):
        left = model.run_engine(-1, ticks=12)
        right = model.run_engine(+1, ticks=12)
        gap = sum((a-b) ** 2 for a, b in zip(left.final_probabilities, right.final_probabilities))
        self.assertGreater(gap, 1e-10)
        self.assertAlmostEqual(sum(left.final_probabilities), 1.0, places=10)
        self.assertAlmostEqual(sum(right.final_probabilities), 1.0, places=10)


if __name__ == "__main__":
    unittest.main()
