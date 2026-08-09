import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("verify_stack_v9", ROOT / "system_v9" / "verify_stack.py")
VERIFY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = VERIFY
SPEC.loader.exec_module(VERIFY)


class StackBoundaryTests(unittest.TestCase):
    def test_structural_verifier_has_no_failures(self):
        report = VERIFY.verify()
        self.assertEqual(report["failures"], [])
        self.assertGreaterEqual(report["check_count"], 40)
        self.assertFalse(report["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
