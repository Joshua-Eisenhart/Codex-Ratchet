from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
A2_STATE = BASE / "a2_state"
SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_object_drafts"
COMMITTED_PYDANTIC_SCHEMA = (
    SPEC_DRAFTS / "A2_CONTROLLER_LAUNCH_PACKET_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json"
)
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA2ControllerLaunchPacketPydanticStack(unittest.TestCase):
    def test_audit_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a2_controller_launch_packet_pydantic.py"),
                "--packet-json",
                str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("A2_CONTROLLER", payload["thread_class"])
        self.assertEqual("CONTROLLER_ONLY", payload["mode"])

    def test_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "a2_controller_launch_packet.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a2_controller_launch_packet_graph.py"),
                    "--packet-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
                    "--out-graphml",
                    str(out_graph),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(out_graph.exists())

    def test_schema_emit_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_schema = Path(tmpdir) / "a2_controller_launch_packet.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_controller_launch_packet_pydantic_schema.py"),
                    "--out-json",
                    str(out_schema),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertTrue(out_schema.exists())
            committed = json.loads(COMMITTED_PYDANTIC_SCHEMA.read_text(encoding="utf-8"))
            fresh = json.loads(out_schema.read_text(encoding="utf-8"))
            self.assertEqual(committed, fresh)


if __name__ == "__main__":
    unittest.main()
