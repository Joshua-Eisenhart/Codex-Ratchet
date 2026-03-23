from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TOOLS = REPO_ROOT / "system_v3" / "tools"
ACTIVE_FAMILY_SLICE = (
    REPO_ROOT / "system_v3" / "a2_state" / "A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json"
)
COMMITTED_PYDANTIC_SCHEMA = (
    REPO_ROOT
    / "work"
    / "audit_tmp"
    / "spec_object_drafts"
    / "A2_TO_A1_FAMILY_SLICE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json"
)
SPEC_GRAPH_PYTHON = REPO_ROOT / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA2ToA1FamilySlicePydanticStack(unittest.TestCase):
    def test_schema_emit_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "family_slice.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_to_a1_family_slice_pydantic_schema.py"),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(str(out_json), payload["out_json"])
            schema_json = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual("object", schema_json["type"])
            self.assertIn("properties", schema_json)

    def test_pydantic_audit_passes_for_active_family_slice(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a2_to_a1_family_slice_pydantic.py"),
                "--family-slice-json",
                str(ACTIVE_FAMILY_SLICE),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["valid"])
        self.assertEqual("substrate_base_family", payload["family_id"])

    def test_graphml_export_passes_for_active_family_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graphml = Path(tmpdir) / "family_slice.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a2_to_a1_family_slice_graph.py"),
                    "--family-slice-json",
                    str(ACTIVE_FAMILY_SLICE),
                    "--out-graphml",
                    str(out_graphml),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(str(out_graphml), payload["out_graphml"])
            self.assertTrue(out_graphml.exists())
            graphml_text = out_graphml.read_text(encoding="utf-8")
            self.assertIn("family_slice", graphml_text)
            self.assertIn("requires_sim_family", graphml_text)

    def test_committed_pydantic_schema_matches_fresh_emit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_json = Path(tmpdir) / "family_slice.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_to_a1_family_slice_pydantic_schema.py"),
                    "--out-json",
                    str(out_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            committed = json.loads(COMMITTED_PYDANTIC_SCHEMA.read_text(encoding="utf-8"))
            fresh = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(committed, fresh)


if __name__ == "__main__":
    unittest.main()
