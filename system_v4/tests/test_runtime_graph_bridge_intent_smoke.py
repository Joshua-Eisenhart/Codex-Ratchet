"""Smoke test for bridging intent/context witnesses into the refinery graph."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.runtime_graph_bridge import bridge_runtime_to_graph


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_runtime_graph_bridge_intent_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
        witness_path = root / "system_v4" / "a2_state" / "witness_corpus_v1.json"

        _write_json(graph_path, {"nodes": {}, "edges": []})
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-20T00:00:00Z",
                    "witness": {
                        "kind": "intent",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:00Z",
                                "op": "intent:maker",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["Preserve maker intent as first-class graph memory."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "batch": "BATCH_TEST",
                        "phase": "STARTUP",
                        "topic": "intent_preservation",
                    },
                },
                {
                    "recorded_at": "2026-03-20T00:00:00Z",
                    "witness": {
                        "kind": "intent",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:00Z",
                                "op": "intent:maker",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["Queue notes should remain distinct intent evidence."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "batch": "BATCH_TEST",
                        "phase": "STARTUP",
                        "type": "queue_notes",
                    },
                },
                {
                    "recorded_at": "2026-03-20T00:00:01Z",
                    "witness": {
                        "kind": "context",
                        "passed": True,
                        "violations": [],
                        "touched_boundaries": [],
                        "trace": [
                            {
                                "at": "2026-03-20T00:00:01Z",
                                "op": "context:system",
                                "before_hash": "",
                                "after_hash": "",
                                "notes": ["Batch startup context should persist."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "system",
                        "batch": "BATCH_TEST",
                        "phase": "STARTUP",
                    },
                },
            ],
        )

        stats = bridge_runtime_to_graph(str(root), clean=True)
        assert stats["intent_context_nodes_added"] == 3
        assert stats["intent_context_edges_added"] == 2

        bridged = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = bridged["nodes"]
        edges = bridged["edges"]
        intent_nodes = [n for n in nodes.values() if n.get("node_type") == "INTENT_SIGNAL"]
        context_nodes = [n for n in nodes.values() if n.get("node_type") == "CONTEXT_SIGNAL"]
        assert len(intent_nodes) == 2
        assert len(context_nodes) == 1
        assert intent_nodes[0]["source_class"] == "DERIVED"
        assert context_nodes[0]["source_class"] == "DERIVED"
        assert intent_nodes[0]["trust_zone"] == "A2_3_INTAKE"
        assert context_nodes[0]["trust_zone"] == "A2_3_INTAKE"
        assert intent_nodes[0]["admissibility_state"] == "PROPOSAL_ONLY"
        assert context_nodes[0]["admissibility_state"] == "RUNTIME_ONLY"
        context_for_edges = [e for e in edges if e.get("relation") == "CONTEXT_FOR"]
        assert len(context_for_edges) == 2

    print("PASS: test_runtime_graph_bridge_intent_smoke")


if __name__ == "__main__":
    test_runtime_graph_bridge_intent_smoke()
