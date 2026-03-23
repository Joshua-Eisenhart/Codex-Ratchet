from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from build_a1_wiggle_controller_result import build_result


class TestBuildA1WiggleControllerResult(unittest.TestCase):
    def test_progress_and_budget_remaining_recommend_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_A1_WIGGLE_CONTROLLER_001"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(
                json.dumps({"run_id": "RUN_A1_WIGGLE_CONTROLLER_001", "accepted_total": 5}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            (run_dir / "reports" / "a1_wiggle_soak_audit_report.json").write_text(
                json.dumps({"schema": "A1_WIGGLE_SOAK_AUDIT_REPORT_v1", "status": "PASS"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1",
                    "run_id": "RUN_A1_WIGGLE_CONTROLLER_001",
                    "inbox_sequence": 1,
                    "meaningful_progress": True,
                    "checkpoint_status": "PASS",
                    "project_save_doc_path": "/tmp/checkpoint1.json",
                    "project_save_doc_audit_path": "/tmp/checkpoint1.audit.json",
                },
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_A1_WIGGLE_CONTROLLER_001",
                    "cycles_completed": 1,
                    "cycles_with_progress": 1,
                    "cycles_without_progress": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            (run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="A1_DISPATCH__TEST__v1",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=3,
            )

            self.assertEqual("CONTINUE_ONE_BOUNDED_STEP", payload["controller_decision"])
            self.assertEqual("go on", payload["controller_message_to_send"])
            self.assertEqual(0, payload["go_on_count"])
            self.assertEqual(3, payload["go_on_remaining"])

    def test_incremented_go_on_count_exhausts_budget_and_stops(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_A1_WIGGLE_CONTROLLER_002"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(json.dumps({"run_id": "RUN_A1_WIGGLE_CONTROLLER_002"}) + "\n", encoding="utf-8")
            (run_dir / "reports" / "a1_wiggle_soak_audit_report.json").write_text(
                json.dumps({"schema": "A1_WIGGLE_SOAK_AUDIT_REPORT_v1", "status": "PASS"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {"schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1", "run_id": "RUN_A1_WIGGLE_CONTROLLER_002", "inbox_sequence": 2},
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_A1_WIGGLE_CONTROLLER_002",
                    "cycles_completed": 1,
                    "cycles_with_progress": 1,
                    "cycles_without_progress": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            (run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="A1_DISPATCH__TEST__v2",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=1,
                previous_result={"go_on_count": 0, "result_json_path": "/tmp/prev.json"},
                increment_go_on_count=True,
            )

            self.assertEqual("STOP", payload["controller_decision"])
            self.assertEqual("go_on_budget_exhausted", payload["controller_decision_reason"])
            self.assertEqual(1, payload["go_on_count"])
            self.assertEqual(0, payload["go_on_remaining"])

    def test_failed_soak_audit_forces_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_A1_WIGGLE_CONTROLLER_003"
            (run_dir / "logs").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "summary.json").write_text(json.dumps({"run_id": "RUN_A1_WIGGLE_CONTROLLER_003"}) + "\n", encoding="utf-8")
            (run_dir / "reports" / "a1_wiggle_soak_audit_report.json").write_text(
                json.dumps({"schema": "A1_WIGGLE_SOAK_AUDIT_REPORT_v1", "status": "FAIL"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            rows = [
                {"schema": "A1_WIGGLE_AUTOPILOT_CYCLE_v1", "run_id": "RUN_A1_WIGGLE_CONTROLLER_003", "inbox_sequence": 1},
                {
                    "schema": "A1_WIGGLE_AUTOPILOT_RESULT_v1",
                    "run_id": "RUN_A1_WIGGLE_CONTROLLER_003",
                    "cycles_completed": 1,
                    "cycles_with_progress": 1,
                    "cycles_without_progress": 0,
                    "autopilot_stop_reason": "",
                },
            ]
            (run_dir / "logs" / "a1_wiggle_autopilot.000.jsonl").write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )

            payload = build_result(
                dispatch_id="A1_DISPATCH__TEST__v3",
                role_type="A1_PROPOSAL",
                run_dir=run_dir,
                go_on_budget=4,
            )

            self.assertEqual("MANUAL_REVIEW_REQUIRED", payload["controller_decision"])
            self.assertEqual("soak_audit_failed", payload["controller_decision_reason"])


if __name__ == "__main__":
    unittest.main()
