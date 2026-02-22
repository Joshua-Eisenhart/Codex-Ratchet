import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_a0_b_sim_runner import run_loop
from a1_strategy import validate_strategy
from zip_protocol_v2_validator import validate_zip_protocol_v2


class TestA1A0BSimIntegration(unittest.TestCase):
    def test_sample_strategy_schema(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        strategy = json.loads(strategy_path.read_text(encoding="utf-8"))
        errors = validate_strategy(strategy)
        self.assertEqual([], errors)

    def test_runner_determinism_replay(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_run_id_a = "TEST_DET_A"
            temp_run_id_b = "TEST_DET_B"
            run_a, hash_a = run_loop(
                strategy_path=strategy_path,
                steps=5,
                run_id=temp_run_id_a,
                a1_source="replay",
                a1_model="",
                a1_timeout_sec=1,
                clean=True,
            )
            run_b, hash_b = run_loop(
                strategy_path=strategy_path,
                steps=5,
                run_id=temp_run_id_b,
                a1_source="replay",
                a1_model="",
                a1_timeout_sec=1,
                clean=True,
            )
            self.assertEqual(hash_a, hash_b)
            out_a = (run_a / "outbox" / "export_block_0001.txt").read_text(encoding="utf-8")
            out_b = (run_b / "outbox" / "export_block_0001.txt").read_text(encoding="utf-8")
            self.assertEqual(out_a, out_b)
            summary = json.loads((run_a / "summary.json").read_text(encoding="utf-8"))
            self.assertIn("unique_strategy_digest_count", summary)
            self.assertIn("unique_export_content_digest_count", summary)
            self.assertIn("unique_export_structural_digest_count", summary)
            self.assertIn("id_churn_signal", summary)
            self.assertIn("master_sim_status", summary)
            self.assertIn("promotion_counts_by_tier", summary)
            self.assertIn("unresolved_promotion_blocker_count", summary)
            self.assertFalse(summary["id_churn_signal"])

            zips = sorted((run_a / "zip_packets").glob("*.zip"))
            self.assertTrue(zips)
            # At least one emitted capsule must validate under ZIP_PROTOCOL_v2.
            result = validate_zip_protocol_v2(str(zips[0]), {})
            self.assertIn(result["outcome"], {"OK", "PARK", "REJECT"})


if __name__ == "__main__":
    unittest.main()
