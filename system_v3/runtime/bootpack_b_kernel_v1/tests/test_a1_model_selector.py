import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_model_selector import find_latest_benchmark_summary, select_best_model, select_best_model_across_runs


class TestA1ModelSelector(unittest.TestCase):
    def test_select_best_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bench_a = root / "A1_MODEL_BENCH_0001"
            bench_a.mkdir(parents=True, exist_ok=True)
            summary_a = {
                "results": [
                    {"model": "m1", "needs_real_llm": True, "id_churn_signal": False, "accepted_total": 0, "parked_total": 0, "rejected_total": 0},
                    {"model": "m2", "needs_real_llm": False, "id_churn_signal": True, "accepted_total": 10, "parked_total": 1, "rejected_total": 0},
                ]
            }
            (bench_a / "benchmark_summary.json").write_text(json.dumps(summary_a), encoding="utf-8")

            bench_b = root / "A1_MODEL_BENCH_0002"
            bench_b.mkdir(parents=True, exist_ok=True)
            summary_b = {
                "results": [
                    {"model": "m3", "needs_real_llm": False, "id_churn_signal": False, "accepted_total": 7, "parked_total": 2, "rejected_total": 0},
                    {"model": "m4", "needs_real_llm": False, "id_churn_signal": False, "accepted_total": 5, "parked_total": 0, "rejected_total": 0},
                ]
            }
            (bench_b / "benchmark_summary.json").write_text(json.dumps(summary_b), encoding="utf-8")

            latest = find_latest_benchmark_summary(root)
            self.assertIsNotNone(latest)
            self.assertTrue(str(latest).endswith("A1_MODEL_BENCH_0002/benchmark_summary.json"))
            best = select_best_model(latest)
            self.assertEqual("m4", best)

    def test_select_best_model_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bench_old = root / "A1_MODEL_BENCH_0001"
            bench_old.mkdir(parents=True, exist_ok=True)
            (bench_old / "benchmark_summary.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "model": "phi4-mini:latest",
                                "needs_real_llm": False,
                                "id_churn_signal": False,
                                "accepted_total": 12,
                                "parked_total": 1,
                                "rejected_total": 0,
                                "unique_export_structural_digest_count": 5,
                                "unique_strategy_digest_count": 5,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            bench_new = root / "A1_MODEL_BENCH_0002"
            bench_new.mkdir(parents=True, exist_ok=True)
            (bench_new / "benchmark_summary.json").write_text(
                json.dumps(
                    {
                        "results": [
                            {
                                "model": "qwen2.5-coder:7b",
                                "needs_real_llm": False,
                                "id_churn_signal": False,
                                "accepted_total": 7,
                                "parked_total": 5,
                                "rejected_total": 0,
                                "unique_export_structural_digest_count": 1,
                                "unique_strategy_digest_count": 1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            best_model, source = select_best_model_across_runs(root)
            self.assertEqual("phi4-mini:latest", best_model)
            self.assertTrue(source.endswith("A1_MODEL_BENCH_0001/benchmark_summary.json"))


if __name__ == "__main__":
    unittest.main()
