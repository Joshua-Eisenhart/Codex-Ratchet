import json
import sys
import tempfile
import unittest
from pathlib import Path
import zipfile

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_a0_b_sim_runner import run_loop
from a1_strategy import validate_strategy
from zip_protocol_v2_validator import validate_zip_protocol_v2


class TestA1A0BSimIntegration(unittest.TestCase):
    def _first_export_block(self, run_dir: Path) -> str:
        packets = sorted((run_dir / "zip_packets").glob("*_A0_TO_B_EXPORT_BATCH_ZIP.zip"))
        self.assertTrue(packets)
        with zipfile.ZipFile(packets[0], "r") as zf:
            return zf.read("EXPORT_BLOCK.txt").decode("utf-8")

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
            out_a = self._first_export_block(run_a)
            out_b = self._first_export_block(run_b)
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
