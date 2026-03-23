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
sys.path.insert(0, str(TOOLS))

from validate_a1_queue_status_packet import validate as validate_queue_packet  # noqa: E402

DEFAULT_AUTO_RESOLVED_MODE = "local_pydantic" if SPEC_GRAPH_PYTHON.exists() else "jsonschema"
DEFAULT_AUTO_SOURCE = (
    "local_pydantic_audit" if SPEC_GRAPH_PYTHON.exists() else "jsonschema_plus_runtime_semantics"
)


class TestA1QueueStatusPacket(unittest.TestCase):
    def test_no_work_packet_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "a1_queue_status.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--no-work-reason",
                    "no bounded A1 family slice is currently prepared",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("NO_WORK", packet["queue_status"])
            self.assertTrue(validate_queue_packet(packet)["valid"])

    def test_ready_packet_mode_builds_valid_queue_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "packet_mode"
            out_json = Path(tmpdir) / "a1_queue_status_packet_mode.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_PACKET__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("READY_FROM_NEW_A2_HANDOFF", packet["queue_status"])
            self.assertEqual("A1_WORKER_LAUNCH_PACKET", packet["ready_surface_kind"])
            self.assertTrue(Path(packet["ready_packet_json"]).exists())
            self.assertEqual("", packet.get("ready_send_text_companion_json", ""))
            self.assertEqual("", packet.get("ready_launch_spine_json", ""))
            self.assertEqual("auto", packet["family_slice_validation_requested_mode"])
            self.assertEqual(DEFAULT_AUTO_RESOLVED_MODE, packet["family_slice_validation_resolved_mode"])
            self.assertEqual(DEFAULT_AUTO_SOURCE, packet["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "auto"},
                packet["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {
                    "mode": DEFAULT_AUTO_RESOLVED_MODE,
                    "source": DEFAULT_AUTO_SOURCE,
                },
                packet["family_slice_validation_resolved_provenance"],
            )
            self.assertTrue(validate_queue_packet(packet)["valid"])

    def test_ready_packet_requires_model_dispatch_id_and_out_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "a1_queue_status_missing_inputs.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("missing_model", proc.stdout + proc.stderr)

    def test_ready_bundle_mode_builds_valid_queue_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "bundle_mode"
            out_json = Path(tmpdir) / "a1_queue_status_bundle_mode.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_BUNDLE__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_LAUNCH_BUNDLE", packet["ready_surface_kind"])
            self.assertTrue(Path(packet["ready_packet_json"]).exists())
            self.assertTrue(Path(packet["ready_bundle_result_json"]).exists())
            self.assertTrue(Path(packet["ready_send_text_companion_json"]).exists())
            self.assertTrue(Path(packet["ready_launch_spine_json"]).exists())
            self.assertEqual("auto", packet["family_slice_validation_requested_mode"])
            self.assertEqual(DEFAULT_AUTO_RESOLVED_MODE, packet["family_slice_validation_resolved_mode"])
            self.assertEqual(DEFAULT_AUTO_SOURCE, packet["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "auto"},
                packet["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {
                    "mode": DEFAULT_AUTO_RESOLVED_MODE,
                    "source": DEFAULT_AUTO_SOURCE,
                },
                packet["family_slice_validation_resolved_provenance"],
            )
            self.assertTrue(validate_queue_packet(packet)["valid"])

    def test_bundle_mode_rejects_mismatched_send_text_companion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "bundle_mode"
            out_json = Path(tmpdir) / "a1_queue_status_bundle_mode.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_BUNDLE_MISMATCH__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(out_json.read_text(encoding="utf-8"))
            bad_companion_json = Path(tmpdir) / "bad_send_text_companion.json"
            companion = json.loads(Path(packet["ready_send_text_companion_json"]).read_text(encoding="utf-8"))
            companion["dispatch_id"] = "BROKEN_DISPATCH"
            bad_companion_json.write_text(json.dumps(companion, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            packet["ready_send_text_companion_json"] = str(bad_companion_json)

            validation = validate_queue_packet(packet)
            self.assertFalse(validation["valid"])
            self.assertIn("ready_send_text_companion_dispatch_id_mismatch", validation["errors"])

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_ready_packet_mode_can_use_local_pydantic_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "packet_mode_pydantic"
            out_json = Path(tmpdir) / "a1_queue_status_packet_mode_pydantic.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_PACKET_PYDANTIC__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_WORKER_LAUNCH_PACKET", packet["ready_surface_kind"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", packet["family_slice_validation_source"])
            self.assertEqual(
                {"mode": "local_pydantic"},
                packet["family_slice_validation_requested_provenance"],
            )
            self.assertEqual(
                {"mode": "local_pydantic", "source": "local_pydantic_audit"},
                packet["family_slice_validation_resolved_provenance"],
            )

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_ready_packet_mode_defaults_to_auto_validation_when_local_stack_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "packet_mode_default_auto"
            out_json = Path(tmpdir) / "a1_queue_status_packet_mode_default_auto.json"
            missing_schema = Path(tmpdir) / "missing.schema.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_queue_status_packet.py"),
                    "--family-slice-json",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__QUEUE_PACKET_DEFAULT_AUTO__2026_03_15__v1",
                    "--preparation-mode",
                    "packet",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-dir",
                    str(out_dir),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_WORKER_LAUNCH_PACKET", packet["ready_surface_kind"])
            self.assertEqual("auto", packet["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", packet["family_slice_validation_source"])


if __name__ == "__main__":
    unittest.main()
