"""
Direct regression smoke for A1 stripped owner-surface preservation.

This guards against the stripped graph builder overwriting a richer existing
owner surface with a thinner or fail-closed rebuild when upstream doctrine is
missing or temporarily weaker than the surface already on disk.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a1_stripped_graph_builder import write_a1_stripped_graph


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_existing_stripped_graph(root: Path) -> dict:
    stripped_id = "A1_STRIPPED::pairwise_correlation_spread_functional"
    payload = {
        "schema": "A1_STRIPPED_GRAPH_v1",
        "generated_utc": "2026-03-20T00:00:00Z",
        "owner_layer": "A1_STRIPPED",
        "materialized": True,
        "build_status": "MATERIALIZED",
        "derived_from": {
            "a1_jargoned_graph": "seeded",
            "handoff_packet": "seeded",
            "family_slice": "seeded",
            "rosetta_batch": "seeded",
            "lift_pack": "seeded",
            "live_hints": "seeded",
        },
        "selection_contract": {
            "included_node_rule": "seeded preserve fixture",
            "edge_rule": "seeded preserve fixture",
            "selected_family_terms": ["correlation_diversity_functional"],
        },
        "blockers": [],
        "blocked_terms": [],
        "summary": {
            "node_count": 1,
            "edge_count": 0,
            "included_terms": ["correlation_diversity_functional"],
            "blocked_term_count": 0,
        },
        "nodes": {
            stripped_id: {
                "id": stripped_id,
                "node_type": "DEPENDENCY_TERM",
                "layer": "A1_STRIPPED",
                "trust_zone": "A1_STRIPPED",
                "name": "pairwise_correlation_spread_functional",
                "description": "Seeded materialized stripped owner node for preserve regression.",
                "status": "LIVE",
                "source_class": "OWNER_BOUND",
                "admissibility_state": "PASSENGER_ONLY",
                "lineage_refs": ["A1_JARGONED::correlation_diversity_functional"],
                "witness_refs": ["A2_TEST::density_matrix_channel"],
                "properties": {
                    "source_jargoned_id": "A1_JARGONED::correlation_diversity_functional",
                    "source_term": "correlation_diversity_functional",
                },
            }
        },
        "edges": [],
    }
    _write_json(root / "system_v4" / "a1_state" / "a1_stripped_graph_v1.json", payload)
    return payload


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="a1_stripped_preserve_smoke_"))
    try:
        expected_payload = _seed_existing_stripped_graph(temp_root)

        result = write_a1_stripped_graph(str(temp_root))
        json_path = Path(result["json_path"])
        audit_note_path = Path(result["audit_note_path"])

        _assert(json_path.exists(), "expected stripped graph JSON to exist after builder run")
        _assert(audit_note_path.exists(), "expected stripped audit note to exist after builder run")

        actual_payload = json.loads(json_path.read_text(encoding="utf-8"))
        audit_text = audit_note_path.read_text(encoding="utf-8")

        _assert(
            actual_payload == expected_payload,
            "expected builder to preserve the richer existing stripped owner surface exactly",
        )
        _assert(
            audit_text.startswith("# NON_REGRESSION_PRESERVE"),
            "expected stripped audit note to record non-regression preservation",
        )
        _assert(
            "attempted_build_status: FAIL_CLOSED" in audit_text,
            "expected audit note to record the attempted fail-closed rebuild",
        )
        _assert(
            "preserved_build_status: MATERIALIZED" in audit_text,
            "expected audit note to record the preserved materialized surface",
        )
        print("A1 stripped graph preserve smoke")
        print("PASS: richer existing stripped owner surface was preserved over fail-closed rebuild")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
