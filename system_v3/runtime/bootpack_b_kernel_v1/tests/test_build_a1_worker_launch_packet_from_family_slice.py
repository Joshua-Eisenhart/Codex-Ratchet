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

from build_a1_worker_send_text_from_packet import build_send_text  # noqa: E402
from validate_a1_worker_launch_packet import validate as validate_packet  # noqa: E402

DEFAULT_AUTO_RESOLVED_MODE = "local_pydantic" if SPEC_GRAPH_PYTHON.exists() else "jsonschema"
DEFAULT_AUTO_SOURCE = (
    "local_pydantic_audit" if SPEC_GRAPH_PYTHON.exists() else "jsonschema_plus_runtime_semantics"
)


class TestBuildA1WorkerLaunchPacketFromFamilySlice(unittest.TestCase):
    def test_cli_compiles_valid_packet_from_family_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            family_slice_schema = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(family_slice_json),
                    "--family-slice-schema-json",
                    str(family_slice_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_WORKER_LAUNCH_PACKET_v1", packet["schema"])
            self.assertEqual(
                "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1",
                packet["dispatch_id"],
            )
            self.assertEqual(
                str(family_slice_json),
                packet["source_a2_artifacts"][0],
            )
            self.assertEqual(
                [
                    str(BASE / "specs" / "77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md"),
                    str(BASE / "specs" / "78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md"),
                ],
                packet["a1_reload_artifacts"],
            )
            self.assertIn(str(family_slice_json), packet["prompt_to_send"])
            self.assertIn("required_lanes:", packet["prompt_to_send"])
            self.assertIn("required_negative_classes:", packet["prompt_to_send"])
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

            validation = validate_packet(packet)
            self.assertTrue(validation["valid"], validation["errors"])

            send_text = build_send_text(packet)
            self.assertIn("a1_reload_artifacts:", send_text)
            self.assertIn(str(family_slice_json), send_text)

    def test_cli_requires_dispatch_id_when_family_slice_is_draft_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            family_slice_schema = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(family_slice_json),
                    "--family-slice-schema-json",
                    str(family_slice_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn(
                "dispatch_id_required_for_family_slice_compilation",
                proc.stdout + proc.stderr,
            )

    def test_jsonschema_validation_rejects_unsupported_recovery_family_at_schema_level(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            family_slice_schema = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"
            broken_slice = json.loads(family_slice_json.read_text(encoding="utf-8"))
            broken_slice["sim_hooks"]["recovery_sim_families"] = ["ADVERSARIAL_NEG"]
            broken_slice_path = tmp_path / "broken_family_slice.json"
            broken_slice_path.write_text(json.dumps(broken_slice, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(broken_slice_path),
                    "--family-slice-schema-json",
                    str(family_slice_schema),
                    "--family-slice-validation-mode",
                    "jsonschema",
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__BROKEN_RECOVERY_FAMILY__2026_03_15__v1",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("family_slice_schema_validation_failed", proc.stdout + proc.stderr)
            self.assertIn("recovery_sim_families", proc.stdout + proc.stderr)

    def test_jsonschema_validation_rejects_unknown_sim_family_tier_family(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            family_slice_schema = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"
            broken_slice = json.loads(family_slice_json.read_text(encoding="utf-8"))
            broken_slice["sim_hooks"]["sim_family_tiers"] = {"UNKNOWN_FAMILY": "T1_COMPOUND"}
            broken_slice_path = tmp_path / "broken_family_slice.json"
            broken_slice_path.write_text(json.dumps(broken_slice, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(broken_slice_path),
                    "--family-slice-schema-json",
                    str(family_slice_schema),
                    "--family-slice-validation-mode",
                    "jsonschema",
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__BROKEN_SIM_FAMILY_TIER__2026_03_15__v1",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("family_slice_schema_validation_failed", proc.stdout + proc.stderr)
            self.assertIn("sim_family_tiers", proc.stdout + proc.stderr)

    def test_jsonschema_validation_rejects_invalid_sim_tier_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            out_json = tmp_path / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            family_slice_schema = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1.schema.json"
            broken_slice = json.loads(family_slice_json.read_text(encoding="utf-8"))
            broken_slice["sim_hooks"]["term_sim_tiers"]["probe_operator"] = "NOT_A_TIER"
            broken_slice_path = tmp_path / "broken_family_slice.json"
            broken_slice_path.write_text(json.dumps(broken_slice, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(broken_slice_path),
                    "--family-slice-schema-json",
                    str(family_slice_schema),
                    "--family-slice-validation-mode",
                    "jsonschema",
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__BROKEN_TIER_TOKEN__2026_03_15__v1",
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("family_slice_schema_validation_failed", proc.stdout + proc.stderr)
            self.assertIn("term_sim_tiers", proc.stdout + proc.stderr)

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_cli_can_validate_with_local_pydantic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "packet.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(family_slice_json),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__PYDANTIC__2026_03_15__v1",
                    "--family-slice-validation-mode",
                    "local_pydantic",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("A1_WORKER_LAUNCH_PACKET_v1", packet["schema"])
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
    def test_auto_validation_uses_local_stack_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "packet.json"
            missing_schema = Path(tmpdir) / "missing.schema.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(family_slice_json),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__AUTO__2026_03_15__v1",
                    "--family-slice-validation-mode",
                    "auto",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("auto", packet["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", packet["family_slice_validation_source"])

    @unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
    def test_default_validation_mode_uses_local_stack_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "packet.json"
            missing_schema = Path(tmpdir) / "missing.schema.json"
            family_slice_json = SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a1_worker_launch_packet_from_family_slice.py"),
                    "--family-slice-json",
                    str(family_slice_json),
                    "--family-slice-schema-json",
                    str(missing_schema),
                    "--model",
                    "GPT-5.4 Medium",
                    "--dispatch-id",
                    "A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__DEFAULT_AUTO__2026_03_15__v1",
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            packet = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("auto", packet["family_slice_validation_requested_mode"])
            self.assertEqual("local_pydantic", packet["family_slice_validation_resolved_mode"])
            self.assertEqual("local_pydantic_audit", packet["family_slice_validation_source"])


if __name__ == "__main__":
    unittest.main()
