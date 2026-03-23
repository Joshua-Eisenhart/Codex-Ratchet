from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_object_drafts"
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"
DEFAULT_AUTO_RESOLVED_MODE = "local_pydantic" if SPEC_GRAPH_PYTHON.exists() else "jsonschema"


class TestPrepareA1QueueStatusSurfaces(unittest.TestCase):
    def test_no_work_surfaces_are_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "queue_status.json"
            out_note = Path(tmpdir) / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_queue_status_surfaces.py"),
                    "--no-work-reason",
                    "no bounded A1 family slice is currently prepared",
                    "--out-json",
                    str(out_json),
                    "--out-note",
                    str(out_note),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual("CREATED", payload["status"])
            self.assertTrue(out_json.exists())
            self.assertTrue(out_note.exists())
            self.assertIn("A1_QUEUE_STATUS: NO_WORK", out_note.read_text(encoding="utf-8"))

    def test_ready_surfaces_are_created_from_family_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "queue_status.json"
            out_note = tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"
            out_dir = tmp_path / "bundle"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_queue_status_surfaces.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_STATUS_SURFACES__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                    "--out-note",
                    str(out_note),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual("CREATED", payload["status"])
            self.assertEqual("auto", payload["family_slice_validation_requested_mode"])
            self.assertEqual(DEFAULT_AUTO_RESOLVED_MODE, payload["family_slice_validation_resolved_mode"])
            expected_source = "local_pydantic_audit" if DEFAULT_AUTO_RESOLVED_MODE == "local_pydantic" else "jsonschema_plus_runtime_semantics"
            self.assertEqual(expected_source, payload["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "auto"},
                payload["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {"mode": DEFAULT_AUTO_RESOLVED_MODE, "source": expected_source},
                payload["family_slice_validation_resolved_provenance"],
            )
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_LAUNCH_BUNDLE", packet["ready_surface_kind"])
            note_text = out_note.read_text(encoding="utf-8")
            self.assertIn("A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF", note_text)
            self.assertIn("ready_bundle_result_json", note_text)
            self.assertIn("ready_send_text_companion_json", note_text)
            self.assertIn("ready_launch_spine_json", note_text)
            self.assertIn(
                f"family_slice_validation_resolved_mode: {DEFAULT_AUTO_RESOLVED_MODE}",
                note_text,
            )
            self.assertIn("family_slice_validation_requested_provenance", note_text)
            self.assertIn("family_slice_validation_resolved_provenance", note_text)

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_ready_surfaces_can_use_local_pydantic_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "queue_status.json"
            out_note = tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"
            out_dir = tmp_path / "packet"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_queue_status_surfaces.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_STATUS_SURFACES_PYDANTIC__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                    "--out-note",
                    str(out_note),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_WORKER_LAUNCH_PACKET", packet["ready_surface_kind"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_resolved_mode"])
            self.assertEqual(
                {"mode": "local_pydantic"},
                packet["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {"mode": "local_pydantic", "source": "local_pydantic_audit"},
                packet["family_slice_validation_resolved_provenance"],
            )


if __name__ == "__main__":
    unittest.main()
