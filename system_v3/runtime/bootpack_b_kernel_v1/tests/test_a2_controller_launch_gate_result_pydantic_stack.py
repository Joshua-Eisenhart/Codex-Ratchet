from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
A2_STATE = BASE / "a2_state"
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA2ControllerLaunchGateResultPydanticStack(unittest.TestCase):
    def test_audit_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a2_controller_launch_gate_result_pydantic.py"),
                "--gate-result-json",
                str(A2_STATE / "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("LAUNCH_READY", payload["status"])
        self.assertTrue(payload["valid"])

    def test_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "a2_controller_launch_gate_result.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a2_controller_launch_gate_result_graph.py"),
                    "--gate-result-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json"),
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
            out_schema = Path(tmpdir) / "a2_controller_launch_gate_result.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_controller_launch_gate_result_pydantic_schema.py"),
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
