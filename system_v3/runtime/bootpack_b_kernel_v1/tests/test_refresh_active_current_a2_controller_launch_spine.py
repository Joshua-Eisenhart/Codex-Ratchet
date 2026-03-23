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
class TestRefreshActiveCurrentA2ControllerLaunchSpine(unittest.TestCase):
    def test_refresh_builds_spine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            spine_json = tmp_path / "a2_controller_launch_spine.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a2_controller_launch_spine.py"),
                    "--packet-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
                    "--gate-result-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json"),
                    "--send-text-companion-json",
                    str(A2_STATE / "A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json"),
                    "--handoff-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json"),
                    "--spine-json",
                    str(spine_json),
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual("CREATED", payload["status"])
            self.assertTrue(spine_json.exists())
            spine = json.loads(spine_json.read_text(encoding="utf-8"))
            self.assertEqual("A2_CONTROLLER_LAUNCH_SPINE_v1", spine["schema"])
            self.assertEqual("LAUNCH_READY", spine["launch_gate_status"])

    def test_refresh_can_emit_graphml_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            spine_json = tmp_path / "a2_controller_launch_spine.json"
            graphml = tmp_path / "a2_controller_launch_spine.graphml"
            schema_json = tmp_path / "a2_controller_launch_spine.schema.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "refresh_active_current_a2_controller_launch_spine.py"),
                    "--packet-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json"),
                    "--gate-result-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_GATE_RESULT__CURRENT__2026_03_12__v1.json"),
                    "--send-text-companion-json",
                    str(A2_STATE / "A2_CONTROLLER_SEND_TEXT_COMPANION__CURRENT__2026_03_15__v1.json"),
                    "--handoff-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.json"),
                    "--spine-json",
                    str(spine_json),
                    "--spec-graph-python",
                    str(SPEC_GRAPH_PYTHON),
                    "--emit-graphml",
                    "--out-graphml",
                    str(graphml),
                    "--emit-schema",
                    "--out-schema-json",
                    str(schema_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(str(graphml), payload["graphml"])
            self.assertEqual(str(schema_json), payload["schema_json"])
            self.assertTrue(graphml.exists())
            self.assertTrue(schema_json.exists())


if __name__ == "__main__":
    unittest.main()
