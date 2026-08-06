# S2 TEST_CANNOT_FAIL — expected clean: assertRaises is a real assertion.
import unittest

class TestFailure(unittest.TestCase):
    def test_failure(self):
        with self.assertRaises(ValueError):
            int("not-an-int")
