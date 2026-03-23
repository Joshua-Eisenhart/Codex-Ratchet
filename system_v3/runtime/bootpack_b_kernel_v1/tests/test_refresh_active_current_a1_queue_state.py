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


class TestRefreshActiveCurrentA1QueueState(unittest.TestCase):
    def test_refresh_active_current_live_registry_is_coherent_with_queue_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(BASE / "a2_state" / "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            refreshed_packet = json.loads(queue_status_json.read_text(encoding="utf-8"))
            active_packet = json.loads(
                (BASE / "a2_state" / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(active_packet["queue_status"], refreshed_packet["queue_status"])
            self.assertEqual(active_packet["reason"], refreshed_packet["reason"])

    def test_refreshes_from_empty_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual("CREATED", payload["status"])
            packet = json.loads(queue_status_json.read_text(encoding="utf-8"))
            self.assertEqual("NO_WORK", packet["queue_status"])
            self.assertTrue(preview_note.exists())

    def test_refresh_single_candidate_missing_ready_inputs_fails_with_composite_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            family_slice = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(family_slice),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(tmp_path / "queue_status.json"),
                    "--preview-note",
                    str(tmp_path / "preview.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("missing_ready_queue_inputs:model,dispatch_id,out_dir", proc.stdout + proc.stderr)

    def test_can_write_active_current_note_when_explicitly_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            active_note = tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                    "--active-current-note",
                    str(active_note),
                    "--write-active-current-note",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual(str(active_note), payload["active_current_note"])
            self.assertTrue(active_note.exists())
            self.assertIn("A1_QUEUE_STATUS: NO_WORK", active_note.read_text(encoding="utf-8"))

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_refresh_can_use_local_pydantic_validation_for_ready_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            family_slice = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(family_slice),
                    "--selected-family-slice-json",
                    str(family_slice),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__ACTIVE_QUEUE_REFRESH_PYDANTIC__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            packet = json.loads(queue_status_json.read_text(encoding="utf-8"))
            self.assertEqual("READY_FROM_NEW_A2_HANDOFF", packet["queue_status"])
            self.assertEqual("A1_WORKER_LAUNCH_PACKET", packet["ready_surface_kind"])
            self.assertEqual("local_pydantic", payload["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", payload["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", payload["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "local_pydantic"},
                payload["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {"mode": "local_pydantic", "source": "local_pydantic_audit"},
                payload["family_slice_validation_resolved_provenance"],
            )

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_refresh_defaults_to_auto_mode_for_ready_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            missing_schema = tmp_path / "missing.schema.json"
            family_slice = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(family_slice),
                    "--selected-family-slice-json",
                    str(family_slice),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__ACTIVE_QUEUE_REFRESH_AUTO__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_refresh_bundle_mode_promotes_launch_spine_for_ready_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            registry_json = tmp_path / "registry.json"
            family_slice = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            create_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_queue_candidate_registry.py"),
                    "--family-slice-json",
                    str(family_slice),
                    "--selected-family-slice-json",
                    str(family_slice),
                    "--out-json",
                    str(registry_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, create_proc.returncode, create_proc.stdout + create_proc.stderr)

            queue_status_json = tmp_path / "queue_status.json"
            preview_note = tmp_path / "preview.md"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a1_queue_state.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--queue-status-packet-json",
                    str(queue_status_json),
                    "--preview-note",
                    str(preview_note),
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__ACTIVE_QUEUE_REFRESH_BUNDLE__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(tmp_path / "ready"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(queue_status_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_LAUNCH_BUNDLE", packet["ready_surface_kind"])
            self.assertTrue(Path(packet["ready_send_text_companion_json"]).exists())
            self.assertTrue(Path(packet["ready_launch_spine_json"]).exists())
            self.assertIn("ready_send_text_companion_json", preview_note.read_text(encoding="utf-8"))
            self.assertIn("ready_launch_spine_json", preview_note.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
