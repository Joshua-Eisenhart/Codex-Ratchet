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


class TestPrepareCurrentA1QueueStatusFromCandidates(unittest.TestCase):
    def test_no_candidates_falls_back_to_no_work(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(0, payload["candidate_count"])
            self.assertEqual("", payload["selected_family_slice_json"])

    def test_empty_registry_falls_back_to_no_work(self) -> None:
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

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(0, payload["candidate_count"])
            self.assertEqual("", payload["selected_family_slice_json"])

    def test_single_candidate_is_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__CURRENT_SELECTOR__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(1, payload["candidate_count"])
            self.assertIn("A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD", payload["selected_family_slice_json"])
            self.assertEqual("auto", payload["family_slice_validation_requested_mode"])
            expected_mode = "local_pydantic" if SPEC_GRAPH_PYTHON.exists() else "jsonschema"
            expected_source = "local_pydantic_audit" if SPEC_GRAPH_PYTHON.exists() else "jsonschema_plus_runtime_semantics"
            self.assertEqual(expected_mode, payload["family_slice_validation_resolved_mode"])
            self.assertEqual(expected_source, payload["family_slice_validation_source"])

    def test_multiple_candidates_without_selection_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("ambiguous_family_slice_candidates", proc.stderr + proc.stdout)

    def test_registry_selected_candidate_is_used(self) -> None:
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

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__CURRENT_SELECTOR_REGISTRY__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD", payload["selected_family_slice_json"])

    def test_registry_single_unselected_candidate_auto_selects(self) -> None:
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
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__CURRENT_SELECTOR_REGISTRY_AUTO__2026_03_21__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(1, payload["candidate_count"])
            self.assertIn("A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD", payload["selected_family_slice_json"])

    def test_registry_single_candidate_missing_ready_inputs_fails_with_composite_error(self) -> None:
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
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--candidate-registry-json",
                    str(registry_json),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("missing_ready_queue_inputs:model,dispatch_id,out_dir", proc.stdout + proc.stderr)

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_single_candidate_can_use_local_pydantic_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__CURRENT_SELECTOR_PYDANTIC__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(1, payload["candidate_count"])
            self.assertIn("A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD", payload["selected_family_slice_json"])

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_single_candidate_defaults_to_auto_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            missing_schema = tmp_path / "missing.schema.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_current_a1_queue_status_from_candidates.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__CURRENT_SELECTOR_AUTO__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(tmp_path / "ready"),
                    "--out-json",
                    str(tmp_path / "queue_status.json"),
                    "--out-note",
                    str(tmp_path / "A1_QUEUE_STATUS__CURRENT__TEST__v1.md"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
