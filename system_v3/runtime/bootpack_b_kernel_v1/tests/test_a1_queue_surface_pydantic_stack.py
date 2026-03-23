from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
A2_STATE = BASE / "a2_state"
SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_object_drafts"
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA1QueueSurfacePydanticStack(unittest.TestCase):
    def test_registry_audit_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a1_queue_surfaces_pydantic.py"),
                "--registry-json",
                str(A2_STATE / "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("candidate_registry", payload["surface_kind"])

    def test_queue_status_packet_audit_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a1_queue_surfaces_pydantic.py"),
                "--packet-json",
                str(A2_STATE / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("queue_status_packet", payload["surface_kind"])

    def test_registry_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "registry.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a1_queue_surfaces_graph.py"),
                    "--registry-json",
                    str(A2_STATE / "A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"),
                    "--out-graphml",
                    str(out_graph),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(out_graph.exists())

    def test_queue_status_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "queue_status.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a1_queue_surfaces_graph.py"),
                    "--packet-json",
                    str(A2_STATE / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json"),
                    "--out-graphml",
                    str(out_graph),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(out_graph.exists())

    def test_queue_surface_schema_emit_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry_schema = Path(tmpdir) / "registry.schema.json"
            queue_packet_schema = Path(tmpdir) / "queue_packet.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a1_queue_surface_pydantic_schemas.py"),
                    "--registry-schema-out",
                    str(registry_schema),
                    "--queue-packet-schema-out",
                    str(queue_packet_schema),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(registry_schema.exists())
            self.assertTrue(queue_packet_schema.exists())
            schema = json.loads(queue_packet_schema.read_text(encoding="utf-8"))
            self.assertIn("family_slice_validation_requested_provenance", schema["properties"])
            self.assertIn("family_slice_validation_resolved_provenance", schema["properties"])
            self.assertIn("ready_send_text_companion_json", schema["properties"])
            self.assertIn("ready_launch_spine_json", schema["properties"])

    def test_bundle_ready_packet_with_launch_spine_audits(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            packet_json = tmp_path / "queue_status.json"
            build_proc = subprocess.run(
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
                    "A1_DISPATCH__QUEUE_SURFACE_STACK_BUNDLE__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(tmp_path / "bundle"),
                    "--out-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, build_proc.returncode, build_proc.stdout + build_proc.stderr)

            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "audit_a1_queue_surfaces_pydantic.py"),
                    "--packet-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual("queue_status_packet", payload["surface_kind"])
            self.assertTrue(payload["has_ready_send_text_companion"])
            self.assertTrue(payload["has_ready_launch_spine"])
            self.assertTrue(payload["ready_artifact_integrity_verified"])

    def test_bundle_ready_packet_with_mismatched_spine_fails_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            packet_json = tmp_path / "queue_status.json"
            build_proc = subprocess.run(
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
                    "A1_DISPATCH__QUEUE_SURFACE_STACK_BAD_SPINE__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(tmp_path / "bundle"),
                    "--out-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, build_proc.returncode, build_proc.stdout + build_proc.stderr)

            packet = json.loads(packet_json.read_text(encoding="utf-8"))
            bad_spine_json = tmp_path / "bad_spine.json"
            spine = json.loads(Path(packet["ready_launch_spine_json"]).read_text(encoding="utf-8"))
            spine["dispatch_id"] = "BROKEN_DISPATCH"
            bad_spine_json.write_text(json.dumps(spine, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            packet["ready_launch_spine_json"] = str(bad_spine_json)
            packet_json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "audit_a1_queue_surfaces_pydantic.py"),
                    "--packet-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("ready_launch_spine_dispatch_id_mismatch", proc.stdout + proc.stderr)

    def test_queue_status_packet_with_invalid_validation_provenance_fails_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            packet_json = tmp_path / "queue_status.json"
            build_proc = subprocess.run(
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
                    "A1_DISPATCH__QUEUE_SURFACE_STACK_BAD_PROVENANCE__2026_03_15__v1",
                    "--preparation-mode",
                    "bundle",
                    "--out-dir",
                    str(tmp_path / "bundle"),
                    "--out-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, build_proc.returncode, build_proc.stdout + build_proc.stderr)

            packet = json.loads(packet_json.read_text(encoding="utf-8"))
            packet["family_slice_validation_requested_mode"] = "jsonschema"
            packet["family_slice_validation_resolved_mode"] = "local_pydantic"
            packet_json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "audit_a1_queue_surfaces_pydantic.py"),
                    "--packet-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("family_slice_validation_mode_mismatch", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
