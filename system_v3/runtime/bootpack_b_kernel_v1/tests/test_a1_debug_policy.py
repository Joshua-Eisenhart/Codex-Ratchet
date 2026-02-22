import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_debug_policy import evaluate_escalation


class TestA1DebugPolicy(unittest.TestCase):
    def test_no_escalation_when_below_limits(self):
        decision = evaluate_escalation(
            a1_generation_fail_count=1,
            repeated_schema_fail=1,
            recent_reject_tags=["PROBE_PRESSURE"],
        )
        self.assertFalse(decision.escalate)
        self.assertEqual([], decision.reasons)

    def test_escalation_on_generation_fail_limit(self):
        decision = evaluate_escalation(
            a1_generation_fail_count=3,
            repeated_schema_fail=0,
            recent_reject_tags=[],
        )
        self.assertTrue(decision.escalate)
        self.assertIn("A1_GENERATION_FAIL_LIMIT", decision.reasons)

    def test_escalation_on_schema_fail_limit(self):
        decision = evaluate_escalation(
            a1_generation_fail_count=0,
            repeated_schema_fail=5,
            recent_reject_tags=["SCHEMA_FAIL"],
        )
        self.assertTrue(decision.escalate)
        self.assertIn("REPEATED_SCHEMA_FAIL_LIMIT", decision.reasons)

    def test_escalation_on_hard_tag_cluster(self):
        decision = evaluate_escalation(
            a1_generation_fail_count=0,
            repeated_schema_fail=0,
            recent_reject_tags=["SCHEMA_FAIL", "UNDEFINED_TERM_USE", "DERIVED_ONLY_PRIMITIVE_USE"],
        )
        self.assertTrue(decision.escalate)
        self.assertIn("HARD_TAG_CLUSTER", decision.reasons)


if __name__ == "__main__":
    unittest.main()
