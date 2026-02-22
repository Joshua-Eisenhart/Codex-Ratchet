import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_adapter import load_strategy_artifact, validate_strategy_schema


class TestA1StrategySchema(unittest.TestCase):
    def test_sample_strategy_valid(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        artifact = load_strategy_artifact(strategy_path)
        errors = validate_strategy_schema(artifact["strategy"])
        self.assertEqual([], errors)

    def test_missing_required_field_invalid(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        strategy = json.loads(strategy_path.read_text(encoding="utf-8"))
        strategy.pop("candidate_families", None)
        errors = validate_strategy_schema(strategy)
        self.assertTrue(any("candidate_families" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
