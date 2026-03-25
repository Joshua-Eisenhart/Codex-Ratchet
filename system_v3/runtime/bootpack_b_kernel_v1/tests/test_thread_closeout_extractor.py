import os
from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
WORK = BASE.parent / "work" / "audit_tmp" / "thread_closeout_packets"
sys.path.insert(0, str(TOOLS))

from append_thread_closeout_packet import _validate_packet  # noqa: E402
from extract_thread_closeout_packet import _build_packet  # noqa: E402


class TestThreadCloseoutExtractor(unittest.TestCase):
    def test_current_closeout_shape_extracts_and_validates(self) -> None:
        cases = {
            "A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1": {
                "role_label": "A2H Archived State",
                "outputs_len": 1,
                "output_suffix": "__return.txt",
                "handoff_contains": "thread_closeout_packets/A2_WORKER__RUNS_CLEANUP_PLAN__2026_03_15__v1.txt",
            },
            "A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1": {
                "role_label": "A2H Refined Fuel Non-Sims",
                "outputs_len": 1,
                "output_suffix": "__return.txt",
                "handoff_contains": "thread_closeout_packets/A2_WORKER__A2_INTAKE_BLOAT_TRIAGE__2026_03_15__v1.txt",
            },
            "A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1": {
                "role_label": "A2H Upgrade Docs",
                "outputs_len": 3,
                "output_suffix": "07_A2_OPERATIONS_SPEC.md",
                "handoff_contains": "thread_closeout_packets/A2_WORKER__DOCS_INTEGRATE_GRAPH_AND_PROVENANCE__2026_03_15__v1.txt",
            },
            "A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1": {
                "role_label": "A2M Contradiction Reprocess",
                "outputs_len": 1,
                "output_suffix": "__return.txt",
                "handoff_contains": "thread_closeout_packets/A2_WORKER__A2_STATE_BLOAT_AUDIT__2026_03_15__v1.txt",
            },
        }

        for label, expected in cases.items():
            with self.subTest(label=label):
                packet = _build_packet((WORK / f"{label}.txt").read_text(encoding="utf-8"), label)
                _validate_packet(packet)

                self.assertEqual("THREAD_CLOSEOUT_PACKET_v1", packet["schema"])
                self.assertEqual(label, packet["source_thread_label"])
                self.assertEqual("STOP", packet["final_decision"])
                self.assertEqual("healthy_but_ready_to_stop", packet["thread_diagnosis"])
                self.assertEqual(expected["role_label"], packet["role_and_scope"]["role_label"])
                self.assertEqual(expected["outputs_len"], len(packet["strongest_outputs"]))
                self.assertTrue(packet["strongest_outputs"][0]["artifact_path"].endswith(expected["output_suffix"]))
                self.assertEqual(
                    [os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/28_A2_THREAD_BOOT__v1.md"],
                    packet["handoff_packet"]["boot_files"],
                )
                self.assertTrue(
                    any(expected["handoff_contains"] in path for path in packet["handoff_packet"]["artifact_paths"])
                )
                self.assertEqual([], packet["keepers"])
                self.assertEqual([], packet["risks"])
                self.assertEqual("", packet["if_one_more_step"]["next_step"])
                self.assertEqual([], packet["if_one_more_step"]["touches"])
                self.assertTrue(packet["closed_statement"])

    def test_mixed_closeout_shapes_extract_and_validate(self) -> None:
        cases = {
            "A2_WORKER__WORKER_LAUNCH_PROCESS_FIX__2026_03_16__v1": {
                "decision": "STOP",
                "diagnosis": "healthy_but_ready_to_stop",
                "output_suffix": "A2_WORKER_LAUNCH_HANDOFF__NEXT_FOUR_SYSTEM_THREADS__2026_03_16__v1.md",
                "artifact_contains": "specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md",
            },
            "A2_WORKER__RUNS_ARCHIVE_REFERENCE_AUDIT__2026_03_16__v1": {
                "decision": "STOP",
                "diagnosis": "healthy_but_ready_to_stop",
                "output_suffix": "__return.txt",
                "artifact_contains": "thread_closeout_packets/A2_WORKER__RUNS_ARCHIVE_REFERENCE_AUDIT__2026_03_16__v1.txt",
            },
            "A2_WORKER__A2_INTAKE_COLD_INDEX_APPLICATION_PLAN__2026_03_16__v1": {
                "decision": "STOP",
                "diagnosis": "healthy_but_ready_to_stop",
                "output_suffix": "__return.txt",
                "artifact_contains": "thread_closeout_packets/A2_WORKER__A2_INTAKE_COLD_INDEX_APPLICATION_PLAN__2026_03_16__v1.txt",
            },
            "A2_WORKER__A1_QUEUE_ACTIVE_SURFACE_AUDIT__2026_03_16__v1": {
                "decision": "CONTINUE_ONE_BOUNDED_STEP",
                "diagnosis": "healthy_but_needs_one_bounded_final_step",
                "output_suffix": None,
                "artifact_contains": None,
            },
            "A2_WORKER__FIRST_CONTROLLER_GRAPH_USE_PLAN__2026_03_16__v1": {
                "decision": "CONTINUE_ONE_BOUNDED_STEP",
                "diagnosis": "healthy_but_needs_one_bounded_final_step",
                "output_suffix": None,
                "artifact_contains": None,
            },
        }

        for label, expected in cases.items():
            with self.subTest(label=label):
                packet = _build_packet((WORK / f"{label}.txt").read_text(encoding="utf-8"), label)
                _validate_packet(packet)

                self.assertEqual(expected["decision"], packet["final_decision"])
                self.assertEqual(expected["diagnosis"], packet["thread_diagnosis"])
                self.assertEqual(
                    [os.environ.get("CODEX_RATCHET_ROOT", ".") + "/system_v3/specs/28_A2_THREAD_BOOT__v1.md"],
                    packet["handoff_packet"]["boot_files"],
                )
                self.assertTrue(packet["closed_statement"])

                if expected["output_suffix"] is None:
                    self.assertEqual([], packet["strongest_outputs"])
                else:
                    self.assertTrue(packet["strongest_outputs"])
                    self.assertTrue(packet["strongest_outputs"][0]["artifact_path"].endswith(expected["output_suffix"]))

                if expected["artifact_contains"] is not None:
                    self.assertTrue(
                        any(expected["artifact_contains"] in path for path in packet["handoff_packet"]["artifact_paths"])
                    )

                if expected["decision"] == "CONTINUE_ONE_BOUNDED_STEP":
                    self.assertTrue(packet["if_one_more_step"]["next_step"])
                    self.assertIn(packet["if_one_more_step"]["next_step"], packet["handoff_packet"]["unresolved_question"])
                else:
                    self.assertEqual("", packet["if_one_more_step"]["next_step"])
                    self.assertIn("None inside this bounded lane", packet["handoff_packet"]["unresolved_question"])


if __name__ == "__main__":
    unittest.main()
