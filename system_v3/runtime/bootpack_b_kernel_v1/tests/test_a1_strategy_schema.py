import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_strategy import validate_strategy


class TestA1StrategySchema(unittest.TestCase):
    def test_sample_strategy_valid(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_strategy(strategy))

    def test_missing_required_root_field_rejected(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        strategy.pop("targets")
        errors = validate_strategy(strategy)
        self.assertTrue(any("missing root field: targets" in row for row in errors))

    def test_forbidden_field_rejected(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        strategy["targets"][0]["raw_text"] = "forbidden"
        errors = validate_strategy(strategy)
        self.assertTrue(any("forbidden field present" in row for row in errors))

    def test_legacy_shape_rejected(self):
        legacy = {
            "strategy_id": "LEGACY",
            "version": "A1_STRATEGY_v1",
            "candidate_families": [],
        }
        errors = validate_strategy(legacy)
        self.assertTrue(any("missing root field: schema" in row for row in errors))


if __name__ == "__main__":
    unittest.main()
