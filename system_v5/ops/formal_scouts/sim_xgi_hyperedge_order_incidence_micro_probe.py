#!/usr/bin/env python3
"""Formal scout for xgi hyperedge order incidence."""

from __future__ import annotations

import hashlib
import json
import pathlib

import xgi


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_xgi_hyperedge_order_incidence_micro_probe_results.json"

NAME = "sim_xgi_hyperedge_order_incidence_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed xgi hyperedge incidence order on one finite "
    "carrier and one swapped-control negative. This is local tool evidence, "
    "not promoted bridge, axis, engine, topology theorem, or target-system evidence."
)

TOOL_MANIFEST = {
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph construction, edge membership, and incidence readout",
    },
    "python": {
        "tried": True,
        "used": True,
        "reason": "supportive finite fixture control flow and pass/fail checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path construction",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable observable digest",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "xgi": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_hypergraph(edge_order: list[tuple[str, list[str]]]) -> xgi.Hypergraph:
    hypergraph = xgi.Hypergraph()
    for edge_id, members in edge_order:
        hypergraph.add_edge(members, id=edge_id)
    return hypergraph


def incidence_observable(edge_order: list[tuple[str, list[str]]]) -> dict[str, object]:
    hypergraph = build_hypergraph(edge_order)
    node_order = ["root", "left", "right", "sink"]
    edge_ids = list(hypergraph.edges)
    incidence_rows = []
    for node in node_order:
        row = []
        for edge_id in edge_ids:
            members = set(hypergraph.edges.members(edge_id))
            row.append(1 if node in members else 0)
        incidence_rows.append(row)
    weighted_readout = [
        sum((edge_index + 1) * row[edge_index] for edge_index in range(len(edge_ids)))
        for row in incidence_rows
    ]
    return {
        "edge_ids": [str(edge_id) for edge_id in edge_ids],
        "node_order": node_order,
        "incidence_rows": incidence_rows,
        "weighted_readout": weighted_readout,
        "node_count": hypergraph.num_nodes,
        "edge_count": hypergraph.num_edges,
        "edge_members": {str(edge_id): sorted(str(member) for member in hypergraph.edges.members(edge_id)) for edge_id in edge_ids},
    }


def main() -> None:
    baseline_order = [
        ("constraint_pair", ["root", "left"]),
        ("closure_pair", ["left", "right", "sink"]),
        ("readout_pair", ["right", "sink"]),
    ]
    swapped_order = [
        ("closure_pair", ["left", "right", "sink"]),
        ("constraint_pair", ["root", "left"]),
        ("readout_pair", ["right", "sink"]),
    ]
    baseline = incidence_observable(baseline_order)
    swapped = incidence_observable(swapped_order)
    changed_observable = baseline["weighted_readout"] != swapped["weighted_readout"]
    same_unordered_members = sorted(baseline["edge_members"].values()) == sorted(swapped["edge_members"].values())
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_carrier_ran": baseline["node_count"] == 4 and baseline["edge_count"] == 3,
        "same_unordered_hyperedge_members": same_unordered_members,
        "swapped_control_changed_observable": changed_observable,
    }
    positive = {
        "xgi_incidence_readout_runs": {
            "pass": checks["finite_carrier_ran"],
            "node_count": baseline["node_count"],
            "edge_count": baseline["edge_count"],
        },
        "hyperedge_order_swap_changes_incidence_weighting": {
            "pass": checks["swapped_control_changed_observable"],
            "observable": "weighted_readout",
        },
    }
    graveyard_companions = {
        "unordered_hyperedge_members_control_preserved": {
            "pass": checks["same_unordered_hyperedge_members"],
            "reason": "the negative control changes hyperedge order while preserving member sets",
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "tool-function evidence stays scout-only",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_carrier_ran"],
            "claim": "bounded to one four-node three-hyperedge incidence carrier",
        },
        "not_hypergraph_theorem_or_engine_claim": {
            "pass": True,
            "claim": "does not promote a hypergraph theorem, bridge, axis, engine, or target-system result",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "fixture": "finite four-node three-hyperedge incidence carrier",
        "baseline": baseline,
        "swapped_control_negative": swapped,
        "changed_observable_required": True,
        "changed_observable": changed_observable,
        "observable_digest": stable_hash({"baseline": baseline, "swapped": swapped}),
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "XGI hyperedge-order incidence micro-probe, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "pass": all(checks.values()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT_PATH), "pass": result["pass"], "changed": changed_observable}, sort_keys=True))


if __name__ == "__main__":
    main()
