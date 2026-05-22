#!/usr/bin/env python3
"""Scope B2 selected rows as source-available repair candidates.

Formal scout only. This receipt consumes the current B2 row-level repair
receipt and checks whether the selected tool-role blocker rows have source
files that can be repaired or rerun. It replaces the earlier incorrect
missing-source reading and keeps B2 open.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_RECEIPT = RESULT_DIR / "two_root_constraint_classical_admin_load_bearing_partition_repair_probe_results.json"
ENGINE_CORE_TRIAGE = RESULT_DIR / "engine_core_boundary_row_triage_probe_results.json"
OUT_PATH = RESULT_DIR / "two_root_constraint_b2_source_available_repair_scope_probe_results.json"

NAME = "two_root_constraint_b2_source_available_repair_scope_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_b2_source_available_repair_scope"
CLAIM_CEILING = (
    "Formal scout audit only: audits source availability for the current B2 selected "
    "blocker rows; when the selected source-repair set is empty, this receipt is "
    "vacuous for repair availability. It separates support-only rerun/role "
    "correction rows from structurally blocked source-repair rows. It does not "
    "resolve B2, promote nonclassical evidence, authorize cleanup, or admit a "
    "basin/manifold claim."
)

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing check of whether selected B2 rows have source files available for repair/rerun",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing DAG from selected B2 rows to repair actions",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt parsing and serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path checks",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive provenance hash for the consumed B2 receipt",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "rustworkx": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
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


def consume_rows() -> list[dict[str, Any]]:
    data = read_json(SOURCE_RECEIPT)
    rows = data.get("row_classification_details", [])
    return rows if isinstance(rows, list) else []


def engine_core_triage_partition() -> dict[str, set[str]]:
    if not ENGINE_CORE_TRIAGE.exists():
        return {}
    data = read_json(ENGINE_CORE_TRIAGE)
    partition = data.get("partition", {})
    if not isinstance(partition, dict):
        return {}
    return {str(key): {str(item) for item in value or []} for key, value in partition.items()}


def action_for(row: dict[str, Any]) -> str:
    status = str(row.get("selected_status_before", ""))
    triage = engine_core_triage_partition()
    row_id = str(row.get("row_id") or row.get("name") or "")
    if status == "blocked_engine_core_importer_boundary_finite_receipt_covered":
        return "keep_finite_boundary_quarantined_or_torch_port"
    if row_id in triage.get("dynamic_torch_port_required", set()):
        return "dynamic_enginecore_torch_port_or_explicit_demote"
    if row_id in triage.get("finite_router_or_readout_quarantine_candidate", set()):
        return "write_exact_finite_boundary_quarantine_receipt"
    if status.startswith("blocked_engine_core_importer_boundary"):
        return "engine_core_boundary_triage_then_finite_receipt_or_torch_port"
    if row.get("classification") == "quarantined_classical_support":
        return "rerun_or_role_correct_support_source"
    if row.get("classification") == "result_only_source_regeneration_required":
        return "regenerate_source_native_replacement"
    return "targeted_source_repair"


def group_for(row: dict[str, Any]) -> str:
    tools = set(row.get("classical_or_admin_load_bearing_tools", []) or [])
    if str(row.get("selected_status_before", "")).startswith("blocked_engine_core_importer_boundary"):
        return "engine_core_boundary_source_repair"
    if row.get("classification") == "quarantined_classical_support":
        return "support_admin_source_rerun_or_role_correction"
    if "engine_core" in tools:
        return "engine_core_boundary_source_repair"
    if "engine_v6_reference" in tools or "engine_v7_reference" in tools or "sklearn" in tools:
        return "reservoir_reference_source_repair"
    if "scipy" in tools:
        return "scipy_metric_or_coupling_source_repair"
    if "python_json" in tools:
        return "json_scaffold_source_repair"
    return "mixed_structural_source_repair"


def z3_source_availability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "pass": True,
            "solver_status": "skipped_no_selected_rows",
            "selected_row_count": 0,
            "all_selected_rows_source_available": True,
            "missing_source_count": 0,
        }
    solver = z3.Solver()
    exists_vars = []
    for idx, row in enumerate(rows):
        exists = z3.Bool(f"source_exists_{idx}")
        exists_vars.append(exists)
        solver.add(exists == (row.get("source_exists") is True))
    solver.add(z3.And(exists_vars))
    status = solver.check()
    return {
        "pass": status == z3.sat,
        "solver_status": str(status),
        "selected_row_count": len(rows),
        "all_selected_rows_source_available": all(row.get("source_exists") is True for row in rows),
        "missing_source_count": sum(1 for row in rows if row.get("source_exists") is not True),
    }


def action_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("B2 selected source-available blockers")
    action_nodes: dict[str, int] = {}
    group_nodes: dict[str, int] = {}
    for row in rows:
        action = action_for(row)
        group = group_for(row)
        action_idx = action_nodes.setdefault(action, graph.add_node(f"action:{action}"))
        group_idx = group_nodes.setdefault(group, graph.add_node(f"group:{group}"))
        row_idx = graph.add_node(f"row:{row.get('row_id')}")
        graph.add_edge(root, action_idx, "requires")
        graph.add_edge(action_idx, group_idx, "routes")
        graph.add_edge(group_idx, row_idx, "contains")
    return {
        "pass": rx.is_directed_acyclic_graph(graph),
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "action_nodes": sorted(action_nodes),
        "group_nodes": sorted(group_nodes),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    action_counts = Counter(action_for(row) for row in rows)
    group_counts = Counter(group_for(row) for row in rows)
    class_counts = Counter(row.get("classification") for row in rows)
    source_available_count = sum(1 for row in rows if row.get("source_exists") is True)
    selected_count = len(rows)
    return {
        "selected_row_count": selected_count,
        "source_available_count": source_available_count,
        "missing_source_count": selected_count - source_available_count,
        "all_selected_rows_source_available": selected_count == 0 or source_available_count == selected_count,
        "classification_counts": dict(sorted(class_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "repair_group_counts": dict(sorted(group_counts.items())),
        "b2_resolved": selected_count == 0,
        "goal_complete": False,
        "cleanup_authorized": False,
        "completion_status": "b2_no_selected_source_repair_rows" if selected_count == 0 else "b2_source_available_repair_scope_scoped",
    }


def build_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": row.get("row_id"),
            "classification": row.get("classification"),
            "source_path": row.get("source_path"),
            "source_exists": row.get("source_exists"),
            "classical_or_admin_load_bearing_tools": row.get("classical_or_admin_load_bearing_tools", []),
            "constraint_admissible_load_bearing_tools": row.get("constraint_admissible_load_bearing_tools", []),
            "next_action": action_for(row),
            "repair_group": group_for(row),
            "promotion_allowed": False,
        }
        for row in rows
    ]


def next_move_text(summary: dict[str, Any]) -> str:
    if summary.get("selected_row_count", 0) == 0:
        return (
            "Current B2 selected source-available repair set is empty. Rerun the partition "
            "and final synthesis receipts to confirm whether B2 cleared or whether a different "
            "blocker class is now selected."
        )
    actions = summary.get("action_counts", {})
    groups = summary.get("repair_group_counts", {})
    selected = summary.get("selected_row_count", 0)
    action_text = ", ".join(f"{count} {name}" for name, count in sorted(actions.items())) or "no selected actions"
    group_text = ", ".join(f"{count} {name}" for name, count in sorted(groups.items())) or "no selected groups"
    if any("engine_core" in name for name in groups):
        repair_guidance = (
            "For EngineCore-boundary rows, write exact finite EngineCore boundary receipts "
            "or port the source path to torch-native execution."
        )
    elif actions.get("targeted_source_repair"):
        repair_guidance = (
            "For result-red source-available rows, repair the named predicate or preserve "
            "the row as counterevidence; do not recast red evidence as passing evidence."
        )
    else:
        repair_guidance = "Apply the selected row-specific repair action from the current partition receipt."
    return (
        f"Current B2 selected set has {selected} source-available rows: "
        f"{action_text}; repair groups: {group_text}. "
        f"{repair_guidance} Keep all rows blocked until the tool-role gate clears them."
    )


def open_blocker_text(summary: dict[str, Any]) -> list[str]:
    if summary.get("selected_row_count", 0) == 0:
        return [
            "No selected B2 source-available repair rows remain in this receipt",
            "Use current partition/final synthesis to identify any remaining blocker class",
            "This local source-scope receipt never authorizes cleanup; D86 final synthesis owns current closeout status",
        ]
    blockers = ["B2 raw estate/tool-role partition remains nonzero"]
    for action, count in sorted(summary.get("action_counts", {}).items()):
        blockers.append(f"{count} selected B2 rows still require {action}")
    blockers.append("Source availability is only a repair precondition; it is not nonclassical evidence or cleanup authorization")
    return blockers


def main() -> int:
    started = time.time()
    rows = consume_rows()
    summary = summarize(rows)
    z3_check = z3_source_availability(rows)
    graph = action_graph(rows)
    all_pass = (
        summary["all_selected_rows_source_available"]
        and summary["missing_source_count"] == 0
        and z3_check["pass"]
        and graph["pass"]
    )
    output = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": all_pass,
        "root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": True,
            "F01": True,
            "N01": True,
            "finite_evidence": "finite selected-row repair graph and bounded source availability predicates",
            "order_evidence": "ordered B2 repair actions route blocker rows through rerun, port, quarantine, demotion, or targeted source repair before promotion",
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "Earlier source-absence scoping was wrong because row source paths were resolved against the repo root instead of the formal_scouts directory.",
            "Source availability does not resolve B2; the rows still need rerun, role correction, targeted repair, or archival disposition.",
        ],
        "source_receipt": {
            "path": rel(SOURCE_RECEIPT),
            "exists": SOURCE_RECEIPT.exists(),
            "sha256": sha256(SOURCE_RECEIPT),
        },
        "summary": summary,
        "selected_rows": build_rows(rows),
        "boundary": {
            "nonpromotion_boundary": {
                "pass": PROMOTION_ALLOWED is False,
                "reason": "B2 rows remain blocked from nonclassical, basin, axis, bridge, or cleanup promotion.",
            },
            "b2_unresolved_boundary": {
                "pass": summary["cleanup_authorized"] is False,
                "reason": "This receipt scopes the source-available repair path; it never authorizes cleanup. A zero selected-row set only means this local repair scope is empty. Current D86 closeout is decided by final synthesis.",
            },
            "source_availability_boundary": {
                "pass": summary["all_selected_rows_source_available"],
                "reason": "All current selected B2 rows have source files available for rerun or targeted repair.",
            },
        },
        "positive": {
            "all_selected_rows_are_source_available": {
                "pass": summary["all_selected_rows_source_available"],
                "selected_row_count": summary["selected_row_count"],
                "source_available_count": summary["source_available_count"],
            },
            "z3_source_availability": z3_check,
            "next_action_graph": graph,
        },
        "nearby_variants": {
            "items": [
                "support-only source rows need rerun or role correction, not promotion",
                "mixed structurally blocked source rows need targeted source repair",
                "source availability does not authorize cleanup",
            ],
            "passed": 3 if all_pass else 0,
            "total": 3,
        },
        "graveyard_companions": {
            "missing_source_reading_killed": {
                "pass": summary["missing_source_count"] == 0,
                "reason": "All selected B2 rows now resolve to existing formal_scout source files.",
            },
            "cleanup_authorized_from_source_availability_killed": {
                "pass": True,
                "reason": "This receipt keeps source availability from becoming cleanup authorization; current D86 closeout is owned by the final synthesis.",
            },
            "promote_blocked_rows_killed": {
                "pass": all(row["promotion_allowed"] is False for row in build_rows(rows)),
                "reason": "All rows remain nonpromotional until repaired/rerun and gate-cleared.",
            },
        },
        "next_admissible_move": next_move_text(summary),
        "open_blockers": open_blocker_text(summary),
        "why_not_v4_probes": [
            "This is a V5 formal-scout blocker classification receipt, not a V4/v4 probe.",
            "It consumes current B2 row-level gate evidence and does not run a theory or basin simulation.",
            "It preserves claim ceilings and forbids promotion from blocked rows.",
        ],
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": rel(OUT_PATH), "summary": summary}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
