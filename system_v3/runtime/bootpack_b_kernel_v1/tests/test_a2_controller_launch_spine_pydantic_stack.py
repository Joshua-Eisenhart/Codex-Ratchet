from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import networkx as nx

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
A2_STATE = BASE / "a2_state"
SPEC_DRAFTS = BASE.parent / "work" / "audit_tmp" / "spec_object_drafts"
COMMITTED_PYDANTIC_SCHEMA = (
    SPEC_DRAFTS / "A2_CONTROLLER_LAUNCH_SPINE_v1__PYDANTIC_SCHEMA__2026_03_15__v1.json"
)
FIRST_CONTROLLER_SUBSET_GRAPH = (
    SPEC_DRAFTS / "FIRST_CONTROLLER_A1_LAUNCH_SUBSET__CURRENT_AND_SUBSTRATE_BASE__2026_03_15__v1.graphml"
)
SPEC_GRAPH_PYTHON = BASE.parent / ".venv_spec_graph" / "bin" / "python"


@unittest.skipUnless(SPEC_GRAPH_PYTHON.exists(), "local spec-graph venv not installed")
class TestA2ControllerLaunchSpinePydanticStack(unittest.TestCase):
    def test_audit_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_a2_controller_launch_spine_pydantic.py"),
                "--spine-json",
                str(A2_STATE / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual("A2_CONTROLLER", payload["thread_class"])
        self.assertEqual("LAUNCH_READY", payload["launch_gate_status"])

    def test_graph_export_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "a2_controller_launch_spine.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "export_a2_controller_launch_spine_graph.py"),
                    "--spine-json",
                    str(A2_STATE / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.json"),
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
            out_schema = Path(tmpdir) / "a2_controller_launch_spine.schema.json"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "emit_a2_controller_launch_spine_pydantic_schema.py"),
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

    def test_first_controller_a1_launch_subset_compile_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_graph = Path(tmpdir) / "first_controller_subset.graphml"
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "compile_first_controller_a1_launch_subset_graph.py"),
                    "--family-slice-graphml",
                    str(SPEC_DRAFTS / "A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"),
                    "--queue-status-graphml",
                    str(SPEC_DRAFTS / "A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.graphml"),
                    "--a1-launch-packet-graphml",
                    str(SPEC_DRAFTS / "A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"),
                    "--a1-send-text-companion-graphml",
                    str(
                        SPEC_DRAFTS / "A1_WORKER_SEND_TEXT_COMPANION__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"
                    ),
                    "--a1-launch-handoff-graphml",
                    str(SPEC_DRAFTS / "A1_WORKER_LAUNCH_HANDOFF__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"),
                    "--a1-launch-spine-graphml",
                    str(SPEC_DRAFTS / "A1_WORKER_LAUNCH_SPINE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.graphml"),
                    "--a2-controller-launch-packet-graphml",
                    str(SPEC_DRAFTS / "A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.graphml"),
                    "--a2-controller-launch-handoff-graphml",
                    str(SPEC_DRAFTS / "A2_CONTROLLER_LAUNCH_HANDOFF__CURRENT__2026_03_12__v1.graphml"),
                    "--a2-controller-launch-spine-graphml",
                    str(SPEC_DRAFTS / "A2_CONTROLLER_LAUNCH_SPINE__CURRENT__2026_03_15__v1.graphml"),
                    "--out-graphml",
                    str(out_graph),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(9, payload["graph_count"])
            self.assertGreater(payload["artifact_bridge_count"], 0)
            self.assertGreater(payload["queue_status_bridge_count"], 0)
            self.assertTrue(out_graph.exists())

            graph = nx.read_graphml(out_graph)
            self.assertIn("first_controller_a1_launch_subset", graph.nodes)
            self.assertIn("queue_status_value:NO_WORK", graph.nodes)
            self.assertIn(
                "artifact_path:/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_LAUNCH_PACKET__CURRENT__2026_03_12__v1.json",
                graph.nodes,
            )
            self.assertTrue(
                graph.has_edge(
                    "current_a1_queue_status:A1_QUEUE_STATUS: NO_WORK",
                    "queue_status_value:NO_WORK",
                )
            )

    def test_refresh_first_controller_a1_launch_subset_graph_rebuilds_fixed_artifact(self) -> None:
        original_text = FIRST_CONTROLLER_SUBSET_GRAPH.read_text(encoding="utf-8")
        try:
            FIRST_CONTROLLER_SUBSET_GRAPH.write_text("<graphml />\n", encoding="utf-8")
            proc = subprocess.run(
                [
                    str(SPEC_GRAPH_PYTHON),
                    str(TOOLS / "refresh_first_controller_a1_launch_subset_graph.py"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(
                "ACTIVE_FIRST_CONTROLLER_A1_LAUNCH_SUBSET_REFRESH_RESULT_v1",
                payload["schema"],
            )
            self.assertEqual(str(FIRST_CONTROLLER_SUBSET_GRAPH), payload["out_graphml"])
            self.assertEqual(9, payload["compile_result"]["graph_count"])

            rebuilt_text = FIRST_CONTROLLER_SUBSET_GRAPH.read_text(encoding="utf-8")
            self.assertNotEqual("<graphml />\n", rebuilt_text)
            graph = nx.read_graphml(FIRST_CONTROLLER_SUBSET_GRAPH)
            self.assertIn("first_controller_a1_launch_subset", graph.nodes)
            self.assertIn("queue_status_value:NO_WORK", graph.nodes)
        finally:
            FIRST_CONTROLLER_SUBSET_GRAPH.write_text(original_text, encoding="utf-8")

    def test_audit_first_controller_a1_launch_subset_graph_succeeds(self) -> None:
        proc = subprocess.run(
            [
                str(SPEC_GRAPH_PYTHON),
                str(TOOLS / "audit_first_controller_a1_launch_subset_graph.py"),
                "--graphml",
                str(FIRST_CONTROLLER_SUBSET_GRAPH),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(
            "FIRST_CONTROLLER_A1_LAUNCH_SUBSET_GRAPH_AUDIT_RESULT_v1",
            payload["schema"],
        )
        self.assertEqual("first_controller_a1_launch_subset", payload["subset_root"])
        self.assertEqual(9, payload["compiled_from_count"])
        self.assertEqual(43, payload["artifact_bridge_count"])
        self.assertEqual(5, payload["queue_status_bridge_count"])


if __name__ == "__main__":
    unittest.main()
