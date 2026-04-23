"""Smoke test for skill graph coverage reporting in the graph capability auditor."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.graph_capability_auditor import build_graph_capability_report


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _skill_record(skill_id: str) -> dict:
    return {
        "skill_id": skill_id,
        "name": skill_id,
        "description": f"{skill_id} description",
        "status": "active",
        "skill_type": "bridge",
        "source_type": "repo_skill",
        "source_path": f"system_v4/skills/{skill_id.replace('-', '_')}.py",
        "tags": [],
        "related_skills": [],
    }


def test_graph_capability_auditor_skill_graph_coverage_smoke() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_json(
            root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json",
            {
                "nodes": {
                    "SKILL::alpha-skill": {
                        "id": "SKILL::alpha-skill",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "alpha-skill",
                        "description": "alpha",
                    },
                    "SKILL::beta-skill": {
                        "id": "SKILL::beta-skill",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "beta-skill",
                        "description": "beta",
                    },
                    "SKILL::ghost-skill": {
                        "id": "SKILL::ghost-skill",
                        "node_type": "SKILL",
                        "layer": "SKILL_REGISTRY",
                        "name": "ghost-skill",
                        "description": "ghost",
                    },
                },
                "edges": [
                    {
                        "source_id": "SKILL::alpha-skill",
                        "target_id": "SKILL::beta-skill",
                        "relation": "RELATED_TO",
                        "attributes": {},
                    }
                ],
            },
        )
        _write_json(
            root / "system_v4" / "a1_state" / "skill_registry_v1.json",
            {
                "alpha-skill": _skill_record("alpha-skill"),
                "beta-skill": _skill_record("beta-skill"),
            },
        )

        report = build_graph_capability_report(str(root))
        coverage = report["skill_graph_coverage"]
        assert coverage["active_skill_count"] == 2
        assert coverage["graphed_skill_node_count"] == 3
        assert coverage["matching_active_skill_count"] == 2
        assert coverage["missing_active_skill_count"] == 0
        assert coverage["stale_skill_node_count"] == 1
        assert coverage["isolated_skill_node_count"] == 1
        assert coverage["single_edge_skill_node_count"] == 2
        assert coverage["fully_graphed"] is False
        assert coverage["sample_stale_skill_ids"] == ["ghost-skill"]
        assert coverage["sample_isolated_skill_ids"] == ["ghost-skill"]
        assert coverage["sample_single_edge_skill_ids"] == ["alpha-skill", "beta-skill"]

    print("PASS: test_graph_capability_auditor_skill_graph_coverage_smoke")


if __name__ == "__main__":
    test_graph_capability_auditor_skill_graph_coverage_smoke()
