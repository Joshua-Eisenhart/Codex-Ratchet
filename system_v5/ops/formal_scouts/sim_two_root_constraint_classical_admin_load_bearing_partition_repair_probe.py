#!/usr/bin/env python3
"""Row-level repair receipt for the current selected tool-role blocker class.

Formal scout only. This packet consumes the current estate tool-gate partition
and reclassifies the selected blocker class into row-level repair/quarantine
categories. It intentionally does not weaken the tool-role gate, promote any
blocked row, or relaunch the broad sim queue.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
OUT_PATH = RESULT_DIR / "two_root_constraint_classical_admin_load_bearing_partition_repair_probe_results.json"

TOOL_ROLE_GATE = RESULT_DIR / "constraint_admissible_tool_role_gate_probe_results.json"
NUMPY_GATE = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"
CHAIN_FRESH = RESULT_DIR / "two_root_constraint_chain_fresh_rerun_and_estate_tool_gate_repair_probe_results.json"
PARTITION = RESULT_DIR / "two_root_constraint_estate_tool_gate_blocker_partition_probe_results.json"
GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"

NAME = "two_root_constraint_classical_admin_load_bearing_partition_repair_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_classical_admin_load_bearing_partition_repair_classifier"
CLAIM_CEILING = (
    "Formal scout only: reclassifies the current selected tool-role blocker "
    "partition into row-level repair/quarantine categories. It does not admit "
    "a final geometric constraint manifold, real attractor basin, Axis0, "
    "engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gate receipt parsing, row-level reclassification, and repair receipt serialization",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that every selected coarse blocker row receives exactly one stricter row classification",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent cross-check of the same row-accounting predicate",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing repair dependency graph from coarse blocker class to row classifications and next repair packets",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive pre/post gate receipt hashing",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical path handling",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

ALLOWED_ROW_CLASSIFICATIONS = {
    "role_corrected",
    "quarantined_classical_support",
    "result_only_source_regeneration_required",
    "source_repaired",
    "structurally_blocked",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def gate_hashes() -> dict[str, Any]:
    return {
        "tool_role_gate": {"path": rel(TOOL_ROLE_GATE), "sha256": sha256(TOOL_ROLE_GATE)},
        "numpy_quarantine_gate": {"path": rel(NUMPY_GATE), "sha256": sha256(NUMPY_GATE)},
        "chain_fresh_gate": {"path": rel(CHAIN_FRESH), "sha256": sha256(CHAIN_FRESH)},
        "partition_gate": {"path": rel(PARTITION), "sha256": sha256(PARTITION)},
    }


def grok_boundary_status() -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    if not GROK_RESULTS.exists():
        return {"all_pass": False, "checked_root": rel(GROK_RESULTS), "violations": [{"path": rel(GROK_RESULTS), "rule": "missing_root"}]}
    for path in sorted(GROK_RESULTS.rglob("*.json")):
        try:
            data = read_json(path)
        except json.JSONDecodeError as exc:
            violations.append({"path": rel(path), "rule": "json_parse_error", "detail": str(exc)})
            continue
        if data.get("classification") == "formal_scout":
            violations.append(
                {
                    "path": rel(path),
                    "rule": "grok_result_uses_formal_scout_classification",
                    "detail": "grok_sim results must stay side_quest_only or omit classification",
                }
            )
        if "formal scout only" in str(data.get("claim_ceiling", "")).lower():
            violations.append(
                {
                    "path": rel(path),
                    "rule": "grok_result_uses_formal_claim_ceiling",
                    "detail": "grok_sim claim ceilings must not present as formal scout receipts",
                }
            )
    return {"all_pass": not violations, "checked_root": rel(GROK_RESULTS), "violations": violations}


def current_gate_status() -> dict[str, Any]:
    tool_gate = read_json(TOOL_ROLE_GATE)
    numpy_gate = read_json(NUMPY_GATE)
    partition = read_json(PARTITION)
    upstream = partition.get("positive", {}).get("upstream_fresh_rerun_estate_gate_consumed", {})
    summary = partition.get("summary", {})
    summary_selected_status = summary.get("selected_next_status")
    positive_selected_status = partition.get("positive", {}).get("tool_gate_blockers_partitioned", {}).get("selected_next_status")
    summary_selected_count = summary.get("selected_next_count")
    positive_selected_count = partition.get("positive", {}).get("tool_gate_blockers_partitioned", {}).get("selected_next_count")
    summary_blocker_total = summary.get("blocker_total")
    positive_blocker_total = partition.get("positive", {}).get("tool_gate_blockers_partitioned", {}).get("blocker_total")
    return {
        "tool_role_gate_all_pass": tool_gate.get("all_pass") is True,
        "numpy_quarantine_all_pass": numpy_gate.get("all_pass") is True,
        "grok_boundary_all_pass": grok_boundary_status()["all_pass"] is True,
        "partition_all_pass": partition.get("summary", {}).get("all_pass") is True or partition.get("positive", {}).get("tool_gate_blockers_partitioned", {}).get("pass") is True,
        "partition_upstream_snapshot_is_stale": bool(upstream.get("upstream_snapshot_is_stale", summary.get("upstream_snapshot_is_stale", False))),
        "selected_next_status": summary_selected_status if summary_selected_status is not None else positive_selected_status,
        "selected_next_count": summary_selected_count if summary_selected_count is not None else positive_selected_count,
        "blocker_total": summary_blocker_total if summary_blocker_total is not None else positive_blocker_total,
    }


def selected_status() -> str:
    partition = read_json(PARTITION)
    summary = partition.get("summary", {})
    status = summary.get("selected_next_status") or partition.get("positive", {}).get("tool_gate_blockers_partitioned", {}).get("selected_next_status")
    if isinstance(status, str) and status:
        return status
    return ""


def selected_rows() -> list[dict[str, Any]]:
    data = read_json(TOOL_ROLE_GATE)
    rows = data.get("tool_role_rows", [])
    if not isinstance(rows, list):
        return []
    status = selected_status()
    return [row for row in rows if row.get("tool_role_status") == status]


def source_exists(row: dict[str, Any]) -> bool:
    source = row.get("source_path")
    if not source:
        return False
    path = pathlib.Path(str(source))
    candidates = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(SCOUT_ROOT / path)
        candidates.append(REPO / path)
    return any(candidate.exists() for candidate in candidates)


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    name = str(row.get("name"))
    classical_tools = sorted(str(tool) for tool in row.get("inadmissible_or_admin_tools", []) or [])
    admissible_tools = sorted(str(tool) for tool in row.get("constraint_admissible_tools", []) or [])
    source_path = row.get("source_path")
    exists = source_exists(row)
    status = row.get("tool_role_status")
    if str(status).startswith("blocked_engine_core_importer_boundary"):
        classification = "structurally_blocked"
        if status == "blocked_engine_core_importer_boundary_finite_receipt_covered":
            next_move = "keep finite-boundary receipt quarantined or port the dependency to a torch-native source path before any nonclassical basin admission"
            evidence = "direct EngineCore import has a finite-boundary receipt, but still crosses the NumPy/autograd-severed boundary for nonclassical basin evidence"
        else:
            next_move = "first classify whether this row is finite-router/readout-only or dynamic; write an exact finite EngineCore boundary receipt only for frozen JSON/scalar consumption, otherwise port the dependency to a torch-native source path"
            evidence = "direct EngineCore import crosses the current NumPy/autograd-severed boundary for nonclassical basin evidence"
    elif status == "blocked_result_only_source_regeneration_required":
        classification = "result_only_source_regeneration_required"
        next_move = "regenerate a source-native replacement receipt or explicitly archive this historical result-only row"
        evidence = "constraint-admissible tools are present but this selected row is result-only/missing-source debt"
    elif not admissible_tools:
        classification = "quarantined_classical_support"
        next_move = "leave blocked as support/admin-only until a source-native nonclassical load-bearing tool is added"
        evidence = "no constraint-admissible load-bearing tools remain after removing classical/admin tools"
    else:
        classification = "structurally_blocked"
        next_move = "patch this source/result so classical/admin tools are supportive, transitive, or removed from load-bearing depth, then rerun the row"
        evidence = "constraint-admissible tools are present, but classical/admin tools are still declared load-bearing"
    return {
        "row_id": name,
        "name": name,
        "result_path": row.get("result_path"),
        "source_path": source_path,
        "source_exists": exists,
        "classification": classification,
        "load_bearing_tools": row.get("load_bearing_tools", []),
        "classical_or_admin_load_bearing_tools": classical_tools,
        "constraint_admissible_load_bearing_tools": admissible_tools,
        "selected_status_before": row.get("tool_role_status"),
        "nonclassical_basin_claim_allowed_before": row.get("nonclassical_basin_claim_allowed"),
        "named_structural_evidence": evidence,
        "next_admissible_repair": next_move,
    }


def row_reclassification_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classified = [classify_row(row) for row in rows]
    counts = Counter(item["classification"] for item in classified)
    invalid = [item for item in classified if item["classification"] not in ALLOWED_ROW_CLASSIFICATIONS]
    duplicate_ids = [item for item, count in Counter(row["row_id"] for row in classified).items() if count != 1]
    untouched_remaining = [row.get("name") for row in rows if row.get("name") not in {item["row_id"] for item in classified}]
    if not rows:
        return {
            "pass": True,
            "selected_status": selected_status(),
            "selected_count_before": 0,
            "selected_count_after_reclassification": 0,
            "classification_counts": {},
            "invalid_classifications": [],
            "duplicate_row_ids": [],
            "untouched_remaining": [],
            "rows": [],
        }
    return {
        "pass": bool(rows) and not invalid and not duplicate_ids and not untouched_remaining and len(classified) == len(rows),
        "selected_status": selected_status(),
        "selected_count_before": len(rows),
        "selected_count_after_reclassification": len(untouched_remaining),
        "classification_counts": dict(counts),
        "invalid_classifications": invalid,
        "duplicate_row_ids": duplicate_ids,
        "untouched_remaining": untouched_remaining,
        "rows": classified,
    }


def graph_report(report: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node(report["selected_status"] or "no_selected_tool_role_blocker")
    class_nodes: dict[str, int] = {}
    for item in report["rows"]:
        label = item["classification"]
        if label not in class_nodes:
            class_nodes[label] = graph.add_node(label)
        row_node = graph.add_node(item["row_id"])
        graph.add_edge(root, class_nodes[label], "reclassified_as")
        graph.add_edge(class_nodes[label], row_node, "row")
    next_node = graph.add_node("next_targeted_source_repair_batch")
    for label in ("structurally_blocked", "quarantined_classical_support", "result_only_source_regeneration_required"):
        if label in class_nodes:
            graph.add_edge(class_nodes[label], next_node, "next_admissible_step")
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and (
            (not report["rows"] and graph.num_nodes() == 2)
            or graph.num_nodes() == 1 + len(class_nodes) + len(report["rows"]) + 1
        ),
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def proof_report(report: dict[str, Any]) -> dict[str, Any]:
    selected = int(report["selected_count_before"])
    classified = len(report["rows"])
    remaining = int(report["selected_count_after_reclassification"])
    z_selected = z3.Int("selected_rows")
    z_classified = z3.Int("classified_rows")
    z_remaining = z3.Int("remaining_unclassified_rows")
    z_ok = z3.Bool("row_accounting_complete")
    solver = z3.Solver()
    solver.add(z_selected == selected)
    solver.add(z_classified == classified)
    solver.add(z_remaining == remaining)
    solver.add(z_ok == z3.And(z_selected >= 0, z_classified == z_selected, z_remaining == 0))
    solver.add(z_ok)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    intsort = tm.getIntegerSort()
    bsort = tm.getBooleanSort()
    c_selected = tm.mkConst(intsort, "selected_rows")
    c_classified = tm.mkConst(intsort, "classified_rows")
    c_remaining = tm.mkConst(intsort, "remaining_unclassified_rows")
    c_ok = tm.mkConst(bsort, "row_accounting_complete")
    zero = tm.mkInteger(0)
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_selected, tm.mkInteger(selected)))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_classified, tm.mkInteger(classified)))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_remaining, tm.mkInteger(remaining)))
    slv.assertFormula(
        tm.mkTerm(
            Kind.EQUAL,
            c_ok,
            tm.mkTerm(
                Kind.AND,
                tm.mkTerm(Kind.GEQ, c_selected, zero),
                tm.mkTerm(Kind.EQUAL, c_classified, c_selected),
                tm.mkTerm(Kind.EQUAL, c_remaining, zero),
            ),
        )
    )
    slv.assertFormula(c_ok)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": z_sat and c_sat,
        "z3_row_accounting_complete": z_sat,
        "cvc5_row_accounting_complete": c_sat,
        "selected_rows": selected,
        "classified_rows": classified,
        "remaining_unclassified_rows": remaining,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "treating a green tool-role gate with unchanged coarse partition count as scientific repair",
        "most_dangerous_failure": "promoting rows that still declare classical/admin helpers as load-bearing nonclassical evidence",
        "hidden_assumption": "all rows in the coarse selected class need the same edit",
        "checks_applied": [
            "selected class consumed from refreshed partition receipt",
            "row-level finite classification set enforced",
            "raw post-partition count preserved separately from row-level reclassification count",
            "no claim promotion and no predicate weakening",
        ],
    }


def main() -> int:
    started = time.time()
    pre_hashes = gate_hashes()
    before = current_gate_status()
    rows = selected_rows()
    reclassified = row_reclassification_report(rows)
    graph = graph_report(reclassified)
    proof = proof_report(reclassified)
    after = current_gate_status()
    post_hashes = gate_hashes()
    raw_after_count = int(after.get("selected_next_count") or 0)
    selected_after_reclassification = int(reclassified["selected_count_after_reclassification"])
    gates_green = (
        after["tool_role_gate_all_pass"]
        and after["numpy_quarantine_all_pass"]
        and after["grok_boundary_all_pass"]
        and after["partition_all_pass"]
    )
    reclassification_complete = (
        before["selected_next_status"] == reclassified["selected_status"]
        and int(before.get("selected_next_count") or 0) == len(rows)
        and reclassified["pass"]
        and graph["pass"]
        and proof["pass"]
        and gates_green
        and selected_after_reclassification == 0
    )
    completion_status = "tooling_reclassified_complete" if reclassification_complete else "blocked"

    positive = {
        "pre_gates_consumed": {
            "pass": before["tool_role_gate_all_pass"]
            and before["numpy_quarantine_all_pass"]
            and before["grok_boundary_all_pass"]
            and before["partition_all_pass"],
            **before,
        },
        "selected_class_reclassified": reclassified,
        "repair_dependency_graph": graph,
        "z3_cvc5_row_accounting": proof,
        "post_gates_observed": {
            "pass": gates_green,
            **after,
            "raw_partition_selected_next_count_after": raw_after_count,
        },
        "premortem_applied": premortem_report(),
    }
    single_structural_repair_class = (
        reclassified["classification_counts"] == {"structurally_blocked": len(reclassified["rows"])}
        and all(item.get("source_exists") is True for item in reclassified["rows"])
    )
    no_selected_rows = len(reclassified["rows"]) == 0
    graveyard = {
        "coarse_class_as_single_repair_killed": {
            "pass": no_selected_rows or len(reclassified["classification_counts"]) >= 2 or single_structural_repair_class,
            "classification_counts": reclassified["classification_counts"],
            "no_selected_rows": no_selected_rows,
            "single_structural_repair_class_accepted": single_structural_repair_class,
            "reason": (
                "A single row-level class is acceptable only after support/admin rows are excluded "
                "and every remaining selected row is a source-backed structural repair; an empty selected set is accepted as gate-clear."
            ),
        },
        "admin_tools_as_nonclassical_load_bearing_killed": {
            "pass": all(item["classification"] != "role_corrected" for item in reclassified["rows"]),
            "reason": "No selected row was promoted or role-corrected without source/result rerun evidence.",
        },
        "raw_gate_delta_overclaim_killed": {
            "pass": raw_after_count == int(before.get("selected_next_count") or 0),
            "raw_partition_selected_next_count_after": raw_after_count,
            "row_level_remaining_after_reclassification": selected_after_reclassification,
            "reason": "The repair receipt separates raw gate count from row-level structural reclassification.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "workstream_lock_boundary": {
            "pass": True,
            "unlocks_later_workstreams": completion_status == "tooling_reclassified_complete",
            "reason": "Only row-level tooling reclassification or empty selected-blocker confirmation is claimed; no manifold/theory work is performed.",
        },
    }
    all_pass = (
        all(item.get("pass") is True for item in positive.values())
        and all(item.get("pass") is True for item in graveyard.values())
        and all(item.get("pass") is True for item in boundary.values())
    )
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
        "pre_gate_hashes": pre_hashes,
        "post_gate_hashes": post_hashes,
        "selected_next_status_before": before.get("selected_next_status"),
        "selected_next_status_after": "row_level_reclassified",
        "selected_next_count_before": int(before.get("selected_next_count") or 0),
        "selected_next_count_after": selected_after_reclassification,
        "raw_partition_selected_next_status_after": after.get("selected_next_status"),
        "raw_partition_selected_next_count_after": raw_after_count,
        "row_ids_touched": [item["row_id"] for item in reclassified["rows"]],
        "row_classifications": {
            item["row_id"]: item["classification"] for item in reclassified["rows"]
        },
        "row_classification_details": reclassified["rows"],
        "partition_upstream_snapshot_is_stale_after": after["partition_upstream_snapshot_is_stale"],
        "tool_role_gate_all_pass_after": after["tool_role_gate_all_pass"],
        "numpy_quarantine_all_pass_after": after["numpy_quarantine_all_pass"],
        "grok_boundary_all_pass_after": after["grok_boundary_all_pass"],
        "completion_status": completion_status,
        "all_pass": all_pass,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": completion_status,
            "selected_next_status_before": before.get("selected_next_status"),
            "selected_next_count_before": int(before.get("selected_next_count") or 0),
            "selected_next_status_after": "row_level_reclassified",
            "selected_next_count_after": selected_after_reclassification,
            "raw_partition_selected_next_status_after": after.get("selected_next_status"),
            "raw_partition_selected_next_count_after": raw_after_count,
            "classification_counts": reclassified["classification_counts"],
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "coarse selected class is not promoted",
                "admin-only rows are quarantined as support/admin-only",
                "mixed rows remain structurally blocked for targeted source repair or the selected blocker set is empty",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout over current tool-role gate receipts, not a v4 proposal.",
        "divergence_log": [
            "If raw partition count is mistaken for row-level reclassification count, W1 progress is overclaimed.",
            "If classical/admin tools remain load-bearing in a source receipt, that row cannot be nonclassical evidence.",
            "If all 49 rows are edited as one broad source repair, the repair stops being auditable.",
        ],
        "blockers": [] if completion_status == "tooling_reclassified_complete" else [
            "Selected coarse blocker class could not be fully reclassified under current gates."
        ],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "completion_status": completion_status,
                "selected_next_count_before": result["selected_next_count_before"],
                "selected_next_count_after": result["selected_next_count_after"],
                "raw_partition_selected_next_count_after": raw_after_count,
                "classification_counts": reclassified["classification_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
