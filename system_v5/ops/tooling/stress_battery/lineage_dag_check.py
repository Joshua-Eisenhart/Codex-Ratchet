#!/usr/bin/env python3
"""Check the packet-166b living-purgatory variation lineage with rustworkx.

The persisted ledger has two separate namespaces:

* candidate nodes are the object keys of ``$.entries``;
* directed lineage edges are ``$.variation_log[*].parent_id -> child_id``.

The content hashes and variation ids bind those records but are not node ids.
This tool is a bounded integrity probe; it does not repair or rewrite the
external packet.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rustworkx as rx


HERE = Path(__file__).resolve().parent
DEFAULT_LEDGER = Path(
    "/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/"
    "ae78ff9c-0704-43c0-81b3-af566c1b5861/scratchpad/packet166b/"
    "sims_and_scripts/living_purgatory_ledger_r2_results.json"
)
RESULT_PATH = HERE / "lineage_dag_check_results.json"

EXPECTED_LEDGER_SCHEMA = "ratchet.purgatory-ledger.v3"
EXPECTED_EDGE_SCHEMA = "ratchet.variation-edge.v1"
CLASSIFICATION = "tool_lego_fit_probe"
PROMOTION_ALLOWED = False

TOOL_MANIFEST = {
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": (
            "PyDiGraph, is_directed_acyclic_graph, and digraph_find_cycle "
            "directly gate the lineage-DAG finding and name a cycle when present."
        ),
    }
}
TOOL_INTEGRATION_DEPTH = {"rustworkx": "load_bearing"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def named_cycle(graph: rx.PyDiGraph) -> dict[str, Any] | None:
    edges = list(rx.digraph_find_cycle(graph))
    if not edges:
        return None
    nodes = [graph[edges[0][0]], *[graph[target] for _, target in edges]]
    return {
        "node_ids": nodes,
        "directed_edges": [
            {"parent_id": graph[source], "child_id": graph[target]}
            for source, target in edges
        ],
    }


def fixture_controls() -> dict[str, Any]:
    positive = rx.PyDiGraph(multigraph=True)
    positive.add_nodes_from(["root", "left", "right", "leaf"])
    positive.add_edges_from_no_data([(0, 1), (0, 2), (1, 3), (2, 3)])
    positive_dag = bool(rx.is_directed_acyclic_graph(positive))

    negative = rx.PyDiGraph(multigraph=True)
    negative.add_nodes_from(["a", "b", "c"])
    negative.add_edges_from_no_data([(0, 1), (1, 2), (2, 0)])
    negative_dag = bool(rx.is_directed_acyclic_graph(negative))
    negative_cycle = named_cycle(negative)

    boundary = rx.PyDiGraph(multigraph=True)
    boundary.add_nodes_from(["isolated"])
    boundary_dag = bool(rx.is_directed_acyclic_graph(boundary))

    passed = positive_dag and not negative_dag and negative_cycle is not None and boundary_dag
    return {
        "status": "PASS" if passed else "FAIL",
        "positive_dag": positive_dag,
        "negative_cycle_detected": not negative_dag,
        "negative_named_cycle": negative_cycle,
        "boundary_isolated_node_dag": boundary_dag,
    }


def main() -> int:
    ledger_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_LEDGER
    raw = json.loads(ledger_path.read_text(encoding="utf-8"))

    entries = raw.get("entries")
    variation_log = raw.get("variation_log")
    if not isinstance(entries, dict):
        raise TypeError("$.entries must be an object keyed by candidate id")
    if not isinstance(variation_log, list):
        raise TypeError("$.variation_log must be an array of variation-edge records")

    candidate_ids = sorted(entries)
    candidate_id_set = set(candidate_ids)
    edge_schema_mismatches: list[str] = []
    missing_parents: list[str] = []
    missing_children: list[str] = []
    self_edges: list[str] = []
    duplicate_variation_ids: list[str] = []
    seen_variation_ids: set[str] = set()

    for index, edge in enumerate(variation_log):
        if not isinstance(edge, dict):
            raise TypeError(f"$.variation_log[{index}] must be an object")
        for field in ("variation_id", "schema", "parent_id", "child_id"):
            if field not in edge:
                raise KeyError(f"$.variation_log[{index}] missing {field!r}")
        variation_id = str(edge["variation_id"])
        parent_id = str(edge["parent_id"])
        child_id = str(edge["child_id"])
        if edge["schema"] != EXPECTED_EDGE_SCHEMA:
            edge_schema_mismatches.append(variation_id)
        if parent_id not in candidate_id_set:
            missing_parents.append(parent_id)
        if child_id not in candidate_id_set:
            missing_children.append(child_id)
        if parent_id == child_id:
            self_edges.append(variation_id)
        if variation_id in seen_variation_ids:
            duplicate_variation_ids.append(variation_id)
        seen_variation_ids.add(variation_id)

    schema_parse_pass = (
        raw.get("schema") == EXPECTED_LEDGER_SCHEMA
        and not edge_schema_mismatches
        and not missing_parents
        and not missing_children
        and not self_edges
        and not duplicate_variation_ids
    )

    controls = fixture_controls()
    graph: rx.PyDiGraph | None = None
    is_dag: bool | None = None
    cycle: dict[str, Any] | None = None
    cycle_edge_records: list[dict[str, Any]] = []
    verdict = "schema-integrity-blocker"

    if schema_parse_pass:
        graph = rx.PyDiGraph(multigraph=True)
        node_indices = graph.add_nodes_from(candidate_ids)
        index_by_candidate = dict(zip(candidate_ids, node_indices, strict=True))
        graph.add_edges_from_no_data(
            [
                (index_by_candidate[str(edge["parent_id"])], index_by_candidate[str(edge["child_id"])])
                for edge in variation_log
            ]
        )
        is_dag = bool(rx.is_directed_acyclic_graph(graph))
        cycle = None if is_dag else named_cycle(graph)
        verdict = "my-parsing-error" if is_dag else "genuine-integrity-finding"

        if cycle is not None:
            pairs = {
                (edge["parent_id"], edge["child_id"])
                for edge in cycle["directed_edges"]
            }
            cycle_edge_records = [
                {
                    "variation_id": edge["variation_id"],
                    "parent_id": edge["parent_id"],
                    "child_id": edge["child_id"],
                    "operator": edge.get("operator"),
                    "proposed_at_rung": edge.get("proposed_at_rung"),
                }
                for edge in variation_log
                if (edge["parent_id"], edge["child_id"]) in pairs
            ]

    actual_node_count = graph.num_nodes() if graph is not None else 0
    actual_edge_count = graph.num_edges() if graph is not None else 0
    graph_count_pass = (
        graph is not None
        and actual_node_count == len(entries)
        and actual_edge_count == len(variation_log)
    )
    tool_probe_pass = schema_parse_pass and graph_count_pass and controls["status"] == "PASS"
    lineage_integrity_pass = tool_probe_pass and is_dag is True

    result = {
        "schema": "codex-ratchet.lineage-dag-check.v1",
        "sim_id": "packet166b_living_purgatory_lineage_dag_check",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": (
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 "
            "system_v5/ops/tooling/stress_battery/lineage_dag_check.py"
        ),
        "runner_identity": {
            "engine": "python",
            "executable": sys.executable,
            "rustworkx_version": rx.__version__,
        },
        "source": {
            "checker_path": str(Path(__file__).resolve()),
            "checker_sha256": sha256_file(Path(__file__).resolve()),
            "ledger_path": str(ledger_path),
            "ledger_sha256": sha256_file(ledger_path),
            "ledger_schema": raw.get("schema"),
            "packet_read_only": True,
        },
        "parsing_contract": {
            "candidate_namespace": "$.entries object keys",
            "edge_namespace": "$.variation_log[*]",
            "edge_direction": "parent_id -> child_id",
            "parent_field": "parent_id",
            "child_field": "child_id",
            "edge_identity_field": "variation_id",
            "integrity_binding_fields": ["parent_content_sha", "child_content_sha"],
            "non_endpoint_fields": [
                "variation_id",
                "parent_content_sha",
                "child_content_sha",
                "candidate_encoded",
                "receipt_id",
            ],
        },
        "schema_checks": {
            "status": "PASS" if schema_parse_pass else "FAIL",
            "edge_schema_mismatches": edge_schema_mismatches,
            "missing_parents": sorted(set(missing_parents)),
            "missing_children": sorted(set(missing_children)),
            "self_edges": self_edges,
            "duplicate_variation_ids": duplicate_variation_ids,
        },
        "graph": {
            "node_count": actual_node_count,
            "edge_count": actual_edge_count,
            "expected_node_count": len(entries),
            "expected_edge_count": len(variation_log),
            "counts_match_native_namespaces": graph_count_pass,
            "multigraph": True,
            "is_dag": is_dag,
            "one_cycle": cycle,
            "one_cycle_edge_records": cycle_edge_records,
        },
        "controls": controls,
        "verdict": verdict,
        "checks": {
            "tool_probe": "PASS" if tool_probe_pass else "FAIL",
            "lineage_is_dag": "PASS" if lineage_integrity_pass else "FAIL",
        },
        "all_pass": lineage_integrity_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "rustworkx",
                "qualified_api/function": (
                    "rustworkx.PyDiGraph + rustworkx.is_directed_acyclic_graph + "
                    "rustworkx.digraph_find_cycle"
                ),
                "input_object": "261 candidate ids and 312 parent_id-to-child_id variation records",
                "output_object": "DAG verdict and one named cycle",
                "positive_case": "an acyclic diamond fixture returns is_dag true",
                "negative/erased_control": "an injected three-node cycle returns false and is named",
                "boundary_case": "one isolated candidate with no edges remains a DAG",
                "demotion_condition": "schema mismatch, unresolved endpoint, count mismatch, or failed controls",
                "gates": ["verdict", "all_pass"],
            }
        ],
        "claim_ceiling": (
            "packet-local lineage parsing and DAG integrity only; no packet repair, "
            "scientific admission, basin admission, bridge, axis, or manifold claim"
        ),
        "expected_process_exit_code": 0 if lineage_integrity_pass else 1,
        "blocked_consumers": [
            "whole-packet canonical integrity",
            "lego promotion",
            "scientific basin or manifold admission",
            "bridge or axis claims",
        ],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"PASS lineage_schema_parse nodes={actual_node_count} edges={actual_edge_count}" if schema_parse_pass else "FAIL lineage_schema_parse")
    print(f"PASS rustworkx_controls" if controls["status"] == "PASS" else "FAIL rustworkx_controls")
    print(f"PASS lineage_is_dag is_dag={is_dag}" if lineage_integrity_pass else f"FAIL lineage_is_dag is_dag={is_dag}")
    if cycle is not None:
        print("CYCLE " + " -> ".join(cycle["node_ids"]))
    print(f"VERDICT {verdict}")
    print(f"RECEIPT {RESULT_PATH}")
    return 0 if lineage_integrity_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
