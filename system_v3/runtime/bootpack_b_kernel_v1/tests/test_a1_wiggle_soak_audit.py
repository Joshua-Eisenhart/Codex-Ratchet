from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"


class TestA1WiggleSoakAudit(unittest.TestCase):
    def test_wiggle_soak_audit_passes_on_append_first_run_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_WIGGLE_AUDIT_001"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(
                json.dumps({"run_id": "RUN_WIGGLE_AUDIT_001", "accepted_total": 13}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_001",
                    "inbox_sequence": 1,
                    "meaningful_progress": True,
                    "checkpoint_status": "PASS",
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_001",
                    "inbox_sequence": 2,
                    "meaningful_progress": True,
                    "checkpoint_status": "PASS",
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_001",
                    "cycles_completed": 2,
                    "cycles_with_progress": 2,
                    "cycles_without_progress": 0,
                    "project_save_every_cycles": 1,
                    "checkpoint_pass_count": 2,
                    "checkpoint_fail_count": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"
            log_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "run_a1_wiggle_soak_audit.py"),
                    "--run-dir",
                    str(run_dir),
                    "--forbid-duplicate-surfaces",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, proc.returncode, msg=proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual("PASS", payload["status"])
            report = json.loads((run_dir / "reports" / "a1_wiggle_soak_audit_report.json").read_text(encoding="utf-8"))
            self.assertEqual("A1_WIGGLE_SOAK_AUDIT_REPORT_v1", report["schema"])
            self.assertEqual("PASS", report["status"])

    def test_wiggle_soak_audit_fails_when_duplicate_surfaces_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_WIGGLE_AUDIT_002"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "snapshots").mkdir(parents=True, exist_ok=True)
            (run_dir / "snapshots" / "snapshot_0001.txt").write_text("dup\n", encoding="utf-8")
            (run_dir / "summary.json").write_text(
                json.dumps({"run_id": "RUN_WIGGLE_AUDIT_002", "accepted_total": 13}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_002",
                    "inbox_sequence": 1,
                    "meaningful_progress": True,
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_002",
                    "cycles_completed": 1,
                    "cycles_with_progress": 1,
                    "cycles_without_progress": 0,
                    "project_save_every_cycles": 0,
                    "checkpoint_pass_count": 0,
                    "checkpoint_fail_count": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"
            log_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "run_a1_wiggle_soak_audit.py"),
                    "--run-dir",
                    str(run_dir),
                    "--forbid-duplicate-surfaces",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(2, proc.returncode, msg=proc.stdout + proc.stderr)
            report = json.loads((run_dir / "reports" / "a1_wiggle_soak_audit_report.json").read_text(encoding="utf-8"))
            self.assertEqual("FAIL", report["status"])
            self.assertGreater(report["duplicate_surface_counts"]["snapshots"], 0)

    def test_wiggle_soak_audit_uses_latest_invocation_window_on_resumed_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_WIGGLE_AUDIT_003"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(
                json.dumps({"run_id": "RUN_WIGGLE_AUDIT_003", "accepted_total": 21}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_003",
                    "inbox_sequence": 1,
                    "meaningful_progress": True,
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_003",
                    "inbox_sequence": 2,
                    "meaningful_progress": True,
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_003",
                    "cycles_completed": 2,
                    "cycles_with_progress": 2,
                    "cycles_without_progress": 0,
                    "project_save_every_cycles": 0,
                    "checkpoint_pass_count": 0,
                    "checkpoint_fail_count": 0,
                    "autopilot_stop_reason": "",
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_003",
                    "inbox_sequence": 3,
                    "meaningful_progress": True,
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_WIGGLE_AUDIT_003",
                    "cycles_completed": 1,
                    "cycles_with_progress": 1,
                    "cycles_without_progress": 0,
                    "project_save_every_cycles": 0,
                    "checkpoint_pass_count": 0,
                    "checkpoint_fail_count": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            log_path = run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl"
            log_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "run_a1_wiggle_soak_audit.py"),
                    "--run-dir",
                    str(run_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, proc.returncode, msg=proc.stdout + proc.stderr)
            report = json.loads((run_dir / "reports" / "a1_wiggle_soak_audit_report.json").read_text(encoding="utf-8"))
            self.assertEqual("PASS", report["status"])
            cycle_consistency = next(row for row in report["checks"] if row["check_id"] == "WIGGLE_CYCLE_COUNT_CONSISTENT")
            self.assertEqual("PASS", cycle_consistency["status"])


if __name__ == "__main__":
    unittest.main()
