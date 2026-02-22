import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import apply_repair_rules
from a1_adapter import load_strategy_artifact


class TestRepairLoopTags(unittest.TestCase):
    def test_missing_required_probe_repair(self):
        strategy = load_strategy_artifact(BASE / "a1_strategies" / "sample_strategy.json")["strategy"]
        repaired, actions = apply_repair_rules(strategy, ["MISSING_REQUIRED_PROBE"])
        self.assertTrue(any(a["tag"] == "MISSING_REQUIRED_PROBE" for a in actions))
        probes = {t["probe_id"] for f in repaired["candidate_families"] for t in f["candidate_templates"]}
        reqs = {t["requires_probe"] for f in repaired["candidate_families"] for t in f["candidate_templates"]}
        self.assertTrue(reqs.issubset(probes))

    def test_evidence_token_mismatch_repair(self):
        strategy = load_strategy_artifact(BASE / "a1_strategies" / "sample_strategy.json")["strategy"]
        strategy["candidate_families"][0]["candidate_templates"][0]["assert_evidence_token"] = "BAD_TOKEN"
        repaired, actions = apply_repair_rules(strategy, ["EVIDENCE_TOKEN_MISMATCH"])
        self.assertTrue(any(a["tag"] == "EVIDENCE_TOKEN_MISMATCH" for a in actions))
        template = repaired["candidate_families"][0]["candidate_templates"][0]
        self.assertEqual(template["evidence_token"], template.get("assert_evidence_token"))

    def test_probe_pressure_repair(self):
        strategy = load_strategy_artifact(BASE / "a1_strategies" / "sample_strategy.json")["strategy"]
        repaired, actions = apply_repair_rules(strategy, ["PROBE_PRESSURE"])
        self.assertTrue(any(a["tag"] == "PROBE_PRESSURE" for a in actions))
        templates = [t for f in repaired["candidate_families"] for t in f["candidate_templates"]]
        spec_count = len({t["spec_id"] for t in templates})
        probe_count = len({t["probe_id"] for t in templates})
        self.assertGreaterEqual(probe_count, max(1, (spec_count + 9) // 10))


if __name__ == "__main__":
    unittest.main()
