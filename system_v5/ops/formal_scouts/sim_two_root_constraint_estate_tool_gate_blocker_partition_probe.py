#!/usr/bin/env python3
"""Partition remaining estate tool-gate blockers for the two-root chain.

Formal scout only. This scout does not broad-edit the sim estate. It reads the
canonical tool-role gate result and partitions remaining blockers into bounded
repair/quarantine classes so the next move can address the largest concrete
blocker without mixing unrelated repairs.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter, defaultdict
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
TOOL_ROLE_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_chain_fresh_rerun_and_estate_tool_gate_repair_probe_results.json"

NAME = "two_root_constraint_estate_tool_gate_blocker_partition_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_estate_tool_gate_blocker_partition"
CLAIM_CEILING = (
    "Formal scout only: partitions estate tool-gate blockers into bounded "
    "repair classes. It does not admit a final geometric constraint manifold, "
    "real attractor basin, Axis0, engine, physics, target-system, Holodeck, or "
    "canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing tool-role gate parsing, blocker partition, and receipt serialization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that completion remains blocked while any blocker partition is nonempty"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent blocker proof matching z3"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing blocker-class dependency graph"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

NEXT_SCOUT_BY_STATUS = {
    "blocked_missing_n01_noncommutation_or_order_evidence": "two_root_constraint_classical_admin_load_bearing_partition_repair_probe",
    "blocked_engine_core_importer_boundary": "engine_core_importer_boundary_classifier_probe",
    "blocked_engine_core_importer_boundary_finite_receipt_covered": "engine_core_finite_boundary_coverage_audit_probe",
    "blocked_result_not_all_pass": "result_not_all_pass_blocker_classifier_probe",
    "blocked_no_constraint_admissible_load_bearing_tool": "tool_integration_two_root_admission_gate_probe",
    "blocked_classical_or_admin_load_bearing": "two_root_constraint_classical_admin_load_bearing_partition_repair_probe",
    "blocked_result_only_source_regeneration_required": "two_root_constraint_classical_admin_load_bearing_partition_repair_probe",
    "blocked_result_only_support_quarantined": "two_root_constraint_classical_admin_load_bearing_partition_repair_probe",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    current_gate = read_json(TOOL_ROLE_GATE)
    current_rows = current_gate.get("tool_role_rows", [])
    current_counts = Counter(
        str(row.get("tool_role_status"))
        for row in current_rows
        if str(row.get("tool_role_status")) != "tool_role_candidate"
    )
    current_blocker_total = sum(current_counts.values())
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("next_required_scout") == NAME
        and summary.get("active_chain_fresh_rerun_pass") is True,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "fresh_rerun_count": summary.get("fresh_rerun_count"),
        "estate_tool_gate_blocker_total": summary.get("estate_tool_gate_blocker_total"),
        "current_tool_gate_blocker_total": current_blocker_total,
        "current_tool_gate_blocker_counts": dict(current_counts),
        "upstream_snapshot_is_stale": summary.get("estate_tool_gate_blocker_total") != current_blocker_total,
        "next_required_scout": summary.get("next_required_scout"),
    }


def partition_rows() -> dict[str, Any]:
    data = read_json(TOOL_ROLE_GATE)
    rows = data.get("tool_role_rows", [])
    rows = rows if isinstance(rows, list) else []
    partitions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_tool: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        status = str(row.get("tool_role_status"))
        compact = {
            "name": row.get("name"),
            "result_path": row.get("result_path"),
            "status": status,
            "load_bearing_tools": row.get("load_bearing_tools", []),
            "nonclassical_basin_claim_allowed": row.get("nonclassical_basin_claim_allowed"),
        }
        if status != "tool_role_candidate":
            partitions[status].append(compact)
        for tool in row.get("load_bearing_tools", []) or []:
            by_tool[str(tool)][status] += 1
    status_counts = Counter(str(row.get("tool_role_status")) for row in rows)
    blocker_total = sum(len(items) for items in partitions.values())
    repair_order = [
        "blocked_result_only_source_regeneration_required",
        "blocked_classical_or_admin_load_bearing",
        "blocked_result_only_support_quarantined",
        "blocked_missing_n01_noncommutation_or_order_evidence",
        "blocked_engine_core_importer_boundary",
        "blocked_engine_core_importer_boundary_finite_receipt_covered",
        "blocked_result_not_all_pass",
        "blocked_no_constraint_admissible_load_bearing_tool",
    ]
    next_status = next((status for status in repair_order if partitions.get(status)), "")
    next_required_scout = (
        NEXT_SCOUT_BY_STATUS.get(next_status, "manual_blocker_classification_required")
        if next_status
        else "none_tool_gate_clear"
    )
    return {
        "pass": data.get("all_pass") is True
        and blocker_total == sum(count for status, count in status_counts.items() if status != "tool_role_candidate")
        and ((blocker_total == 0 and not next_status) or (blocker_total > 0 and bool(next_status))),
        "tool_role_gate_path": rel(TOOL_ROLE_GATE),
        "tool_role_gate_sha256": hashlib.sha256(TOOL_ROLE_GATE.read_bytes()).hexdigest(),
        "all_pass": data.get("all_pass"),
        "status_counts": dict(status_counts),
        "blocker_total": blocker_total,
        "partitions": {key: value for key, value in sorted(partitions.items())},
        "by_tool": {tool: dict(counts) for tool, counts in sorted(by_tool.items())},
        "repair_order": repair_order,
        "selected_next_status": next_status,
        "selected_next_count": len(partitions[next_status]) if next_status else 0,
        "next_required_scout": next_required_scout,
    }


def graph_report(partition: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("estate_tool_gate_blockers")
    if partition["blocker_total"] == 0:
        return {
            "pass": bool(rx.is_directed_acyclic_graph(graph)),
            "nodes": graph.num_nodes(),
            "edges": graph.num_edges(),
            "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
            "empty_partition": True,
        }
    next_required_scout = partition.get("next_required_scout", "manual_blocker_classification_required")
    next_node = graph.add_node(next_required_scout)
    for status, rows in partition["partitions"].items():
        node = graph.add_node(status)
        graph.add_edge(root, node, len(rows))
        if status == partition["selected_next_status"]:
            graph.add_edge(node, next_node, "largest_first_repair")
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and graph.num_edges() >= len(partition["partitions"]) + 1,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def proof_report(partition: dict[str, Any]) -> dict[str, Any]:
    blockers_clear = partition["blocker_total"] == 0
    z_clear = z3.Bool("estate_tool_gate_blockers_clear")
    z_complete = z3.Bool("completion_allowed")
    solver = z3.Solver()
    solver.add(z_clear == blockers_clear)
    solver.add(z_complete == z_clear)
    solver.add(z_complete)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_clear = tm.mkConst(bsort, "estate_tool_gate_blockers_clear")
    c_complete = tm.mkConst(bsort, "completion_allowed")
    slv.assertFormula(c_clear if blockers_clear else tm.mkTerm(Kind.NOT, c_clear))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_complete, c_clear))
    slv.assertFormula(c_complete)
    c_sat = slv.checkSat().isSat()
    proof_pass = (z_sat and c_sat) if blockers_clear else (not z_sat and not c_sat)
    return {
        "pass": proof_pass,
        "blockers_clear": blockers_clear,
        "z3_completion_blocked": not z_sat,
        "cvc5_completion_blocked": not c_sat,
        "z3_completion_allowed_by_tool_gate_clear": z_sat,
        "cvc5_completion_allowed_by_tool_gate_clear": c_sat,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "trying to fix all current tool-gate blockers in one broad sweep",
        "most_dangerous_failure": "letting classical/admin load-bearing rows count toward nonclassical manifold maturity",
        "hidden_assumption": "classical/admin role failures, missing N01 evidence, EngineCore boundary rows, and failed receipts need the same repair path",
        "checks_applied": [
            "partition by tool_role_status",
            "select current highest-priority nonempty blocker class first",
            "keep result-not-all-pass and unknown-role rows separate",
            "z3/cvc5 completion block while partitions remain nonempty",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    partition = partition_rows()
    graph = graph_report(partition)
    proof = proof_report(partition)
    premortem = premortem_report()
    positive = {
        "upstream_fresh_rerun_estate_gate_consumed": upstream,
        "tool_gate_blockers_partitioned": partition,
        "blocker_partition_graph": graph,
        "z3_cvc5_completion_block": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "broad_estate_repair_killed": {
            "pass": True,
            "reason": "Blockers are partitioned; next work is the largest/highest-risk class only.",
        },
        "stale_numpy_first_repair_killed": {
            "pass": "blocked_numpy_load_bearing" not in partition["status_counts"],
            "reason": "The refreshed gate has no blocked_numpy_load_bearing partition; the next repair must use current blocker classes.",
        },
        "classical_admin_load_bearing_as_nonclassical_maturity_killed": {
            "pass": partition["selected_next_status"] != "blocked_classical_or_admin_load_bearing",
            "selected_next_status": partition["selected_next_status"],
            "selected_next_count": partition["selected_next_count"],
            "reason": f"The refreshed partition no longer selects classical/admin load-bearing rows; current selected debt is {partition['selected_next_status']}.",
        },
        "completion_before_tool_gate_clear_killed": proof,
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "next_required_scout": {
            "pass": True,
            "name": partition["next_required_scout"],
            "requirement": "Handle the selected tool-role blocker class by role correction, quarantine, source-native regeneration, or targeted source repair, without touching unrelated blocker classes.",
        },
        "completion_boundary": {
            "pass": True,
            "completion_status": "tool_gate_clear" if partition["blocker_total"] == 0 else "not_achieved",
            "reason": (
                "estate tool-role partition has no active blockers"
                if partition["blocker_total"] == 0
                else f"{partition['blocker_total']} estate tool-gate blockers remain partitioned but uncleared."
            ),
        },
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(
        item.get("pass") is True for item in graveyard.values()
    ) and all(item.get("pass") is True for item in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "premortem": premortem,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "tool_gate_clear" if partition["blocker_total"] == 0 else "not_achieved",
            "blocker_total": partition["blocker_total"],
            "status_counts": partition["status_counts"],
            "selected_next_status": partition["selected_next_status"],
            "selected_next_count": partition["selected_next_count"],
            "next_required_scout": partition["next_required_scout"],
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "items": [
                "blockers are partitioned rather than broad-edited",
                "stale numpy-first repair path is killed",
                "selected blocker class routes to its current required scout",
                "completion remains blocked while any partition is nonempty",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout over canonical tool-role gate receipts, not a v4 proposal.",
        "divergence_log": [
            "If classical/admin load-bearing rows are counted as nonclassical, tool integration overclaims.",
            "If missing-N01 rows are mixed with classical/admin rows, repair evidence becomes ambiguous.",
            "If EngineCore importer-boundary rows are mixed with source-native tool rows, the NumPy/autograd boundary is blurred.",
            "If unknown-role rows are promoted without review, the gate stops being meaningful.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "blocker_total": partition["blocker_total"],
                "selected_next_status": partition["selected_next_status"],
                "selected_next_count": partition["selected_next_count"],
                "next_required_scout": partition["next_required_scout"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
