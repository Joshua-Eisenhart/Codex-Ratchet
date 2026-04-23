"""Smoke test for graph-discriminative executable intent focus filtering."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from system_v4.skills.intent_control_surface_builder import (
    GRAPH_REL_PATH,
    SURFACE_REL_PATH,
    WITNESS_REL_PATH,
    build_intent_control_surface,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_intent_control_surface_builder_executable_focus_filter_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        graph_path = root / GRAPH_REL_PATH
        witness_path = root / WITNESS_REL_PATH

        nodes = {
            "INTENT::REFINED::TEST": {
                "id": "INTENT::REFINED::TEST",
                "node_type": "INTENT_REFINEMENT",
                "name": "intent_runtime_contract",
                "description": (
                    "Intent system context graphs skills memory graph skill "
                    "should remain available as refined intent."
                ),
                "tags": ["intent", "intent-refinement", "graph", "skill"],
                "properties": {"source_intent_ids": ["INTENT::SIGNAL::TEST"]},
                "lineage_refs": ["INTENT::SIGNAL::TEST"],
                "witness_refs": ["WITNESS_CORPUS::0"],
            },
            "C001": {
                "id": "C001",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "system_topology_alpha",
                "description": "System topology alpha concept.",
                "tags": ["SYSTEM"],
            },
            "C002": {
                "id": "C002",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "system_topology_beta",
                "description": "System topology beta concept.",
                "tags": ["SYSTEM"],
            },
            "C003": {
                "id": "C003",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "system_topology_gamma",
                "description": "System topology gamma concept.",
                "tags": ["SYSTEM"],
            },
            "C004": {
                "id": "C004",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "system_topology_delta",
                "description": "System topology delta concept.",
                "tags": ["SYSTEM"],
            },
            "C005": {
                "id": "C005",
                "node_type": "REFINED_CONCEPT",
                "name": "system_context_bridge",
                "description": "System context bridge concept.",
                "tags": ["SYSTEM", "CONTEXT"],
            },
            "C006": {
                "id": "C006",
                "node_type": "REFINED_CONCEPT",
                "name": "intent_memory_loop",
                "description": "Intent memory context preservation loop.",
                "tags": ["INTENT", "MEMORY", "CONTEXT"],
            },
            "C007": {
                "id": "C007",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "graph_graphs_surface",
                "description": "Graph graphs semantic surface.",
                "tags": ["GRAPH", "GRAPHS"],
            },
            "C008": {
                "id": "C008",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "skill_skills_surface",
                "description": "Skill skills coordination surface.",
                "tags": ["SKILL", "SKILLS"],
            },
        }
        _write_json(graph_path, {"nodes": nodes, "edges": []})
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
                                "notes": [
                                    "Intent system context graphs skills memory graph skill should steer the runtime carefully."
                                ],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "phase": "DESIGN_PRINCIPLE",
                        "priority": "P0",
                        "topic": "intent_preservation",
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
                                "notes": ["Context remains available for the batch."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "system",
                        "phase": "STARTUP",
                    },
                },
            ],
        )

        build_intent_control_surface(td)
        payload = json.loads((root / SURFACE_REL_PATH).read_text(encoding="utf-8"))

        steering_focus_terms = payload["control"]["steering_focus_terms"]
        executable_focus_terms = payload["control"]["executable_focus_terms"]
        metrics = payload["control"]["runtime_policy"]["executable_focus_graph_metrics"]

        assert "system" in steering_focus_terms
        assert "system" not in executable_focus_terms
        assert "graphs" in steering_focus_terms
        assert "graphs" not in executable_focus_terms
        assert "skills" in steering_focus_terms
        assert "skills" not in executable_focus_terms
        assert "intent" in executable_focus_terms
        assert "context" in executable_focus_terms
        assert "memory" in executable_focus_terms
        assert "graph" in executable_focus_terms
        assert "skill" in executable_focus_terms
        assert payload["control"]["runtime_policy"]["concept_selection"]["gating_focus_terms"] == executable_focus_terms
        assert any(item["term"] == "system" for item in metrics["pruned_terms"])
        assert any(
            item["term"] == "graphs" and item["redundant_alias_of"] == "graph"
            for item in metrics["pruned_terms"]
        )
        assert any(
            item["term"] == "skills" and item["redundant_alias_of"] == "skill"
            for item in metrics["pruned_terms"]
        )
        assert payload["self_audit"]["executable_focus_term_count"] == len(executable_focus_terms)


def test_intent_control_surface_builder_executable_focus_anchor_filter_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        graph_path = root / GRAPH_REL_PATH
        witness_path = root / WITNESS_REL_PATH

        nodes = {
            "INTENT::REFINED::TEST": {
                "id": "INTENT::REFINED::TEST",
                "node_type": "INTENT_REFINEMENT",
                "name": "skill_integration_intent_contract",
                "description": "Skill integration should remain visible as refined intent.",
                "tags": ["intent", "intent-refinement", "skill", "integration"],
                "properties": {"source_intent_ids": ["INTENT::SIGNAL::TEST"]},
                "lineage_refs": ["INTENT::SIGNAL::TEST"],
                "witness_refs": ["WITNESS_CORPUS::0"],
            },
            "ANCHOR::A1": {
                "id": "ANCHOR::A1",
                "layer": "A1_STRIPPED",
                "node_type": "REFINED_CONCEPT",
                "name": "skill_anchor_upper_surface",
                "description": "Upper-surface skill anchor.",
                "tags": ["SKILL"],
            },
            "ANCHOR::A2": {
                "id": "ANCHOR::A2",
                "layer": "A2_2_CANDIDATE",
                "node_type": "EXTRACTED_CONCEPT",
                "name": "skill_anchor_candidate_surface",
                "description": "Candidate-layer skill anchor.",
                "tags": ["SKILL"],
            },
            "KEEP::INTENT": {
                "id": "KEEP::INTENT",
                "layer": "A1_STRIPPED",
                "node_type": "REFINED_CONCEPT",
                "name": "intent_memory_anchor",
                "description": "Intent memory anchor concept.",
                "tags": ["INTENT", "MEMORY"],
            },
        }
        for idx in range(18):
            nodes[f"HI::{idx:02d}"] = {
                "id": f"HI::{idx:02d}",
                "layer": "A2_HIGH_INTAKE",
                "node_type": "EXTRACTED_CONCEPT",
                "name": f"skill_intake_{idx:02d}",
                "description": f"Skill intake concept {idx:02d}.",
                "tags": ["SKILL"],
            }

        _write_json(graph_path, {"nodes": nodes, "edges": []})
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
                                "notes": ["Skill integration should mature, but weak intake-heavy skill hits should not steer execution."],
                            }
                        ],
                    },
                    "tags": {
                        "source": "maker",
                        "phase": "DESIGN_PRINCIPLE",
                        "priority": "P0",
                        "topic": "skill_graph_integration",
                    },
                }
            ],
        )

        build_intent_control_surface(td)
        payload = json.loads((root / SURFACE_REL_PATH).read_text(encoding="utf-8"))

        executable_focus_terms = payload["control"]["executable_focus_terms"]
        metrics = payload["control"]["runtime_policy"]["executable_focus_graph_metrics"]

        assert "skill" not in executable_focus_terms
        assert "intent" in executable_focus_terms
        skill_prune = next(item for item in metrics["pruned_terms"] if item["term"] == "skill")
        assert skill_prune["high_intake_share"] == 0.9
        assert skill_prune["anchored_support_count"] == 2
        assert "high_intake_dominance" in skill_prune["prune_reason"]

    print("PASS: test_intent_control_surface_builder_executable_focus_filter_smoke")


if __name__ == "__main__":
    test_intent_control_surface_builder_executable_focus_filter_smoke()
    test_intent_control_surface_builder_executable_focus_anchor_filter_smoke()
