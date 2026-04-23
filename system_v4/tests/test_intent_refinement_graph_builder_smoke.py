"""Smoke test for graph-native intent/context/refinement materialization."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.intent_refinement_graph_builder import build_intent_refinement_graph
from system_v4.skills.witness_recorder import WitnessRecorder


def test_intent_refinement_graph_builder_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        recorder = WitnessRecorder(root / "system_v4" / "a2_state" / "witness_corpus_v1.json")
        recorder.record_intent(
            "Preserve maker intent in the graph.",
            source="maker",
            tags={"phase": "DESIGN_PRINCIPLE", "topic": "intent_preservation"},
        )
        recorder.record_context(
            "Controller gate is launch ready and queue is paused.",
            source="system",
            tags={"phase": "CONTROL_SNAPSHOT", "topic": "queue_controller_state"},
        )
        recorder.flush()

        result = build_intent_refinement_graph(td)
        assert result["raw_intent_nodes"] == 1
        assert result["raw_context_nodes"] == 1
        assert result["refined_intent_nodes"] == 1

        graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = graph.get("nodes", {})
        counts = {}
        for node in nodes.values():
            counts[node.get("node_type", "?")] = counts.get(node.get("node_type", "?"), 0) + 1
        assert counts.get("INTENT_SIGNAL", 0) == 1
        assert counts.get("CONTEXT_SIGNAL", 0) == 1
        assert counts.get("INTENT_REFINEMENT", 0) == 1
        intent_signal = next(node for node in nodes.values() if node.get("node_type") == "INTENT_SIGNAL")
        context_signal = next(node for node in nodes.values() if node.get("node_type") == "CONTEXT_SIGNAL")
        refined_node = next(node for node in nodes.values() if node.get("node_type") == "INTENT_REFINEMENT")
        assert intent_signal.get("witness_refs") == ["WITNESS_CORPUS::0"]
        assert context_signal.get("witness_refs") == ["WITNESS_CORPUS::1"]
        assert refined_node.get("witness_refs") == ["WITNESS_CORPUS::0"]

        refine_edges = [e for e in graph.get("edges", []) if e.get("relation") == "REFINES_INTENT"]
        assert len(refine_edges) == 1

    print("PASS: test_intent_refinement_graph_builder_smoke")


if __name__ == "__main__":
    test_intent_refinement_graph_builder_smoke()
