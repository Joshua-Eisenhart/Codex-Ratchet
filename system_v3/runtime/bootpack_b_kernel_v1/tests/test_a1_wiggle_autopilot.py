from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from a1_wiggle_autopilot import (
    _append_jsonl,
    _apply_cycle_guards,
    _dir_size_bytes,
    _meaningful_progress,
)


class TestA1WiggleAutopilot(unittest.TestCase):
    def test_meaningful_progress_detects_real_ratchet_growth(self) -> None:
        before = {
            "canonical_term_count": 1,
            "evidence_token_count": 5,
            "graveyard_count": 1,
            "survivor_count": 13,
            "sim_registry_count": 5,
            "term_registry_count": 1,
        }
        after = {
            "canonical_term_count": 2,
            "evidence_token_count": 12,
            "graveyard_count": 2,
            "survivor_count": 25,
            "sim_registry_count": 12,
            "term_registry_count": 2,
        }

        self.assertEqual(
            [
                "canonical_term_count",
                "evidence_token_count",
                "graveyard_count",
                "survivor_count",
                "sim_registry_count",
                "term_registry_count",
            ],
            _meaningful_progress(before, after),
        )

    def test_meaningful_progress_ignores_flat_or_negative_metrics(self) -> None:
        before = {
            "canonical_term_count": 2,
            "evidence_token_count": 12,
            "graveyard_count": 2,
            "survivor_count": 25,
            "sim_registry_count": 12,
            "term_registry_count": 2,
        }
        after = {
            "canonical_term_count": 2,
            "evidence_token_count": 12,
            "graveyard_count": 2,
            "survivor_count": 24,
            "sim_registry_count": 12,
            "term_registry_count": 2,
        }

        self.assertEqual([], _meaningful_progress(before, after))

    def test_meaningful_progress_counts_clearing_pending_or_parked_work(self) -> None:
        before = {
            "canonical_term_count": 2,
            "evidence_token_count": 12,
            "graveyard_count": 2,
            "survivor_count": 25,
            "sim_registry_count": 12,
            "term_registry_count": 2,
            "park_count": 3,
            "evidence_pending_count": 4,
        }
        after = {
            "canonical_term_count": 2,
            "evidence_token_count": 12,
            "graveyard_count": 2,
            "survivor_count": 25,
            "sim_registry_count": 12,
            "term_registry_count": 2,
            "park_count": 1,
            "evidence_pending_count": 2,
        }

        self.assertEqual(
            ["park_count_reduced", "evidence_pending_count_reduced"],
            _meaningful_progress(before, after),
        )

    def test_dir_size_bytes_counts_nested_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "a").write_bytes(b"abc")
            (root / "nested").mkdir()
            (root / "nested" / "b").write_bytes(b"defgh")

            self.assertEqual(8, _dir_size_bytes(root))

    def test_append_jsonl_appends_multiple_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "logs" / "a1_wiggle_autopilot.000.jsonl"
            _append_jsonl(path, {"schema": "ROW", "sequence": 1})
            _append_jsonl(path, {"schema": "ROW", "sequence": 2})

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(2, len(lines))
            self.assertIn('"sequence": 1', lines[0])
            self.assertIn('"sequence": 2', lines[1])

    def test_apply_cycle_guards_preserves_primary_reason_and_projects_row_size(self) -> None:
        row, stop_reasons = _apply_cycle_guards(
            {
                "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                "run_id": "RUN_TEST",
                "inbox_sequence": 1,
            },
            run_dir_bytes=10,
            checkpoint_status="AUDIT_FAILED",
            stall_streak=3,
            stall_limit_cycles=3,
            max_run_bytes=1,
        )

        self.assertEqual(
            [
                "PROJECT_SAVE_CHECKPOINT_FAILED",
                "STALL_LIMIT_REACHED",
                "RUN_DIR_BYTES_LIMIT",
            ],
            stop_reasons,
        )
        self.assertEqual("PROJECT_SAVE_CHECKPOINT_FAILED", row["autopilot_stop_reason"])
        self.assertEqual(stop_reasons, row["autopilot_stop_reasons"])
        self.assertGreater(row["projected_run_dir_bytes"], row["run_dir_bytes"])


if __name__ == "__main__":
    unittest.main()
