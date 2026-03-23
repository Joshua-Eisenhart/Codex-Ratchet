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
DEFAULT_AUTO_SOURCE = (
    "local_pydantic_audit" if SPEC_GRAPH_PYTHON.exists() else "jsonschema_plus_runtime_semantics"
)


class TestPrepareA1LaunchBundleFromFamilySlice(unittest.TestCase):
    def test_cli_prepares_ready_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_launch_bundle_from_family_slice.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1",
                    "--out-dir",
                    str(out_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual("READY", payload["status"])

            packet_json = Path(payload["packet_json"])
            bundle_result_json = Path(payload["bundle_result_json"])
            send_text_companion_json = Path(payload["send_text_companion_json"])
            launch_spine_json = Path(payload["launch_spine_json"])
            self.assertTrue(packet_json.exists())
            self.assertTrue(bundle_result_json.exists())
            self.assertTrue(send_text_companion_json.exists())
            self.assertTrue(launch_spine_json.exists())

            bundle_result = json.loads(bundle_result_json.read_text(encoding="utf-8"))
            self.assertEqual("READY", bundle_result["status"])
            self.assertEqual("A1_WORKER", bundle_result["thread_class"])
            self.assertEqual("auto", bundle_result["family_slice_validation_requested_mode"])
            self.assertEqual(DEFAULT_AUTO_RESOLVED_MODE, bundle_result["family_slice_validation_resolved_mode"])
            self.assertEqual(DEFAULT_AUTO_SOURCE, bundle_result["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "auto"},
                bundle_result["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {
                    "mode": DEFAULT_AUTO_RESOLVED_MODE,
                    "source": DEFAULT_AUTO_SOURCE,
                },
                bundle_result["family_slice_validation_resolved_provenance"],
            )
            self.assertEqual("auto", payload["family_slice_validation_requested_mode"])
            self.assertEqual(DEFAULT_AUTO_RESOLVED_MODE, payload["family_slice_validation_resolved_mode"])
            self.assertEqual(DEFAULT_AUTO_SOURCE, payload["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "auto"},
                payload["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {
                    "mode": DEFAULT_AUTO_RESOLVED_MODE,
                    "source": DEFAULT_AUTO_SOURCE,
                },
                payload["family_slice_validation_resolved_provenance"],
            )
            launch_spine = json.loads(launch_spine_json.read_text(encoding="utf-8"))
            self.assertEqual("LAUNCH_READY", launch_spine["launch_gate_status"])

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_cli_can_use_local_pydantic_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_launch_bundle_from_family_slice.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE_PYDANTIC__2026_03_15__v1",
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-dir",
                    str(out_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
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
    def test_cli_defaults_to_auto_validation_when_local_stack_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            missing_schema = out_dir / "missing.schema.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "prepare_a1_launch_bundle_from_family_slice.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE_DEFAULT_AUTO__2026_03_15__v1",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-dir",
                    str(out_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual("auto", payload["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", payload["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", payload["family_slice_validation_source"])


if __name__ == "__main__":
    unittest.main()
