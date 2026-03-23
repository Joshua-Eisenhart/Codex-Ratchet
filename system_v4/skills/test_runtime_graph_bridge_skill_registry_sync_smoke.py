"""Smoke test for active skill registry reconciliation in the runtime graph bridge."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.runtime_graph_bridge import bridge_runtime_to_graph


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _skill_record(skill_id: str, *, related_skills: list[str] | None = None) -> dict:
    return {
        "skill_id": skill_id,
        "name": skill_id,
        "description": f"{skill_id} description",
        "status": "active",
        "skill_type": "bridge",
        "source_type": "repo_skill",
        "source_path": f"system_v4/skills/{skill_id.replace('-', '_')}.py",
        "applicable_trust_zones": [],
        "applicable_graphs": [],
        "inputs": [],
        "outputs": [],
        "adapters": {"shell": f"system_v4/skills/{skill_id.replace('-', '_')}.py"},
        "related_skills": list(related_skills or []),
        "tags": ["graph-sync"],
    }


def test_runtime_graph_bridge_skill_registry_sync_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        graph_path = root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json"
        registry_path = root / "system_v4" / "a1_state" / "skill_registry_v1.json"

        _write_json(
            graph_path,
            {
                "nodes": {
                    "SKILL::codex-automation-controller": {
                        "id": "SKILL::codex-automation-controller",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "codex-automation-controller",
                        "description": "old alias",
                        "trust_zone": "SKILL_REGISTRY",
                        "tags": ["legacy"],
                        "authority": "SOURCE_CLAIM",
                        "properties": {},
                        "object_family": "SkillRecord",
                        "source_class": "DERIVED",
                        "status": "LIVE",
                        "admissibility_state": "REGISTERED",
                        "lineage_refs": ["legacy-lineage"],
                        "witness_refs": ["legacy-witness"],
                    },
                    "SKILL::playwright": {
                        "id": "SKILL::playwright",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "playwright",
                        "description": "old alias",
                        "trust_zone": "SKILL_REGISTRY",
                        "tags": ["legacy"],
                        "authority": "SOURCE_CLAIM",
                        "properties": {},
                        "object_family": "SkillRecord",
                        "source_class": "DERIVED",
                        "status": "LIVE",
                        "admissibility_state": "REGISTERED",
                        "lineage_refs": [],
                        "witness_refs": [],
                    },
                    "SKILL::ghost-skill": {
                        "id": "SKILL::ghost-skill",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "ghost-skill",
                        "description": "connected stale skill",
                        "trust_zone": "SKILL_REGISTRY",
                        "tags": ["legacy"],
                        "authority": "SOURCE_CLAIM",
                        "properties": {},
                        "object_family": "SkillRecord",
                        "source_class": "DERIVED",
                        "status": "LIVE",
                        "admissibility_state": "REGISTERED",
                        "lineage_refs": [],
                        "witness_refs": [],
                    },
                },
                "edges": [
                    {
                        "source_id": "SKILL::codex-automation-controller",
                        "target_id": "SKILL::run-real-ratchet",
                        "relation": "RELATED_TO",
                        "attributes": {"inferred": True, "role": "skill_hub"},
                    },
                    {
                        "source_id": "SKILL::playwright",
                        "target_id": "SKILL::runtime-graph-bridge",
                        "relation": "RELATED_TO",
                        "attributes": {"inferred": True, "role": "skill_hub"},
                    },
                    {
                        "source_id": "SKILL::ghost-skill",
                        "target_id": "SKILL::run-real-ratchet",
                        "relation": "RELATED_TO",
                        "attributes": {"inferred": True, "role": "skill_hub"},
                    },
                ],
            },
        )
        _write_json(
            registry_path,
            {
                "run-real-ratchet": _skill_record("run-real-ratchet"),
                "runtime-graph-bridge": _skill_record("runtime-graph-bridge"),
                "automation-controller": _skill_record("automation-controller"),
                "browser-automation": _skill_record("browser-automation"),
                "bounded-improve-operator": _skill_record("bounded-improve-operator"),
                "intent-control-surface-builder": _skill_record(
                    "intent-control-surface-builder",
                    related_skills=["runtime-graph-bridge", "automation-controller"],
                ),
            },
        )

        stats = bridge_runtime_to_graph(str(root), clean=False)
        assert stats["skill_alias_nodes_migrated"] == 2
        assert stats["skill_stale_nodes_removed"] == 1

        bridged = json.loads(graph_path.read_text(encoding="utf-8"))
        nodes = bridged["nodes"]
        edges = bridged["edges"]

        expected_skill_nodes = {
            "SKILL::run-real-ratchet",
            "SKILL::runtime-graph-bridge",
            "SKILL::automation-controller",
            "SKILL::browser-automation",
            "SKILL::bounded-improve-operator",
            "SKILL::intent-control-surface-builder",
        }
        for nid in expected_skill_nodes:
            assert nid in nodes
            assert nodes[nid]["node_type"] == "SKILL"

        assert "SKILL::codex-automation-controller" not in nodes
        assert "SKILL::playwright" not in nodes
        assert "SKILL::ghost-skill" not in nodes

        automation_node = nodes["SKILL::automation-controller"]
        assert automation_node["properties"]["source_type"] == "repo_skill"
        assert automation_node["lineage_refs"] == ["legacy-lineage"]
        assert automation_node["witness_refs"] == ["legacy-witness"]

        edge_pairs = {
            (edge["source_id"], edge["target_id"], edge["relation"], edge.get("attributes", {}).get("role", ""))
            for edge in edges
        }
        assert (
            "SKILL::automation-controller",
            "SKILL::run-real-ratchet",
            "RELATED_TO",
            "skill_hub",
        ) in edge_pairs
        assert (
            "SKILL::browser-automation",
            "SKILL::runtime-graph-bridge",
            "RELATED_TO",
            "skill_hub",
        ) in edge_pairs
        assert (
            "SKILL::intent-control-surface-builder",
            "SKILL::runtime-graph-bridge",
            "RELATED_TO",
            "registry_related_skill",
        ) in edge_pairs

        skill_nodes = [nid for nid, node in nodes.items() if node.get("node_type") == "SKILL"]
        connected = {
            edge["source_id"]
            for edge in edges
        } | {
            edge["target_id"]
            for edge in edges
        }
        assert set(skill_nodes) <= connected

    print("PASS: test_runtime_graph_bridge_skill_registry_sync_smoke")


if __name__ == "__main__":
    test_runtime_graph_bridge_skill_registry_sync_smoke()
