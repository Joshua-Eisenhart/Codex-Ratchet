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
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA2ControllerSendTextCompanionPydanticStack(unittest.TestCase):
    def test_build_and_audit_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            companion_json = Path(tmpdir) / "a2_controller_send_text_companion.json"
            build_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a2_controller_send_text_companion.py"),
                    "--packet-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
                    "--send-text",
                    str(A2_STATE / "A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md"),
                    "--out-json",
                    str(companion_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, build_proc.returncode, build_proc.stdout + build_proc.stderr)

            audit_proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "audit_a2_controller_send_text_companion_pydantic.py"),
                    "--companion-json",
                    str(companion_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, audit_proc.returncode, audit_proc.stdout + audit_proc.stderr)
            payload = json.loads(audit_proc.stdout)
            self.assertEqual("A2_CONTROLLER", payload["thread_class"])

    def test_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            companion_json = Path(tmpdir) / "a2_controller_send_text_companion.json"
            graph_path = Path(tmpdir) / "a2_controller_send_text_companion.graphml"
            build_proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "build_a2_controller_send_text_companion.py"),
                    "--packet-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
                    "--send-text",
                    str(A2_STATE / "A2_CONTROLLER_SEND_TEXT__CURRENT__2026_03_12__v1.md"),
                    "--out-json",
                    str(companion_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, build_proc.returncode, build_proc.stdout + build_proc.stderr)

            export_proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a2_controller_send_text_companion_graph.py"),
                    "--companion-json",
                    str(companion_json),
                    "--out-graphml",
                    str(graph_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, export_proc.returncode, export_proc.stdout + export_proc.stderr)
            self.assertTrue(graph_path.exists())

    def test_schema_emit_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_schema = Path(tmpdir) / "a2_controller_send_text_companion.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_controller_send_text_companion_pydantic_schema.py"),
                    "--out-json",
                    str(out_schema),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(out_schema.exists())


if __name__ == "__main__":
    unittest.main()
