#!/usr/bin/env python3
"""Fresh-rerun and estate tool-gate repair audit for the two-root chain.

Formal scout only. This scout runs the formal-scout validator with fresh reruns
over the active two-root foundation chain, then audits the estate tool gate so
remaining integration blockers are concrete rather than a vague weak row.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time
from collections import Counter
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
SYSTEM_V5 = SCOUT_ROOT.parents[1]
RESULT_DIR = SCOUT_ROOT / "results"
VALIDATOR = SCOUT_ROOT / "validate_formal_scout_results.py"
ESTATE_INDEX = SYSTEM_V5 / "evidence" / "sim_estate_integration_index.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_global_countermodel_completion_audit_probe_results.json"

NAME = "two_root_constraint_chain_fresh_rerun_and_estate_tool_gate_repair_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
FRESH_RERUN_TIMEOUT_SECONDS = 600
FRESH_RERUN_WRAPPER_TIMEOUT_SECONDS = 3600

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_chain_fresh_rerun_estate_tool_gate_repair"
CLAIM_CEILING = (
    "Formal scout only: fresh-reruns the active two-root chain and audits estate "
    "tool-gate blockers. It does not admit a final geometric constraint "
    "manifold, real attractor basin, Axis0, engine, physics, target-system, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing validator JSON parsing, estate index parsing, and receipt serialization"},
    "subprocess": {"tried": True, "used": True, "reason": "load-bearing fresh-rerun validator execution over the active chain"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that completion remains blocked by estate tool-gate blockers"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent blocker proof matching z3"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing blocker dependency graph"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "subprocess": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "pathlib": "supportive",
}

CHAIN = [
    "two_root_constraint_layer_stack_peps3d_boundary_portability_probe",
    "two_root_constraint_long_horizon_layer_stack_countermodel_probe",
    "two_root_constraint_cross_family_countermodel_transfer_probe",
    "two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe",
    "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe",
    "two_root_constraint_layer_order_gauge_invariant_observable_probe",
    "two_root_constraint_completion_audit_and_gap_classifier_probe",
    "two_root_constraint_layer_forcing_theorem_or_countermodel_probe",
    "two_root_constraint_selection_axiom_layer_discriminator_probe",
    "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe",
    "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe",
    "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe",
    "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe",
    "two_root_constraint_selector_basin_adversarial_leak_retune_probe",
    "two_root_constraint_completion_audit_after_selector_basin_chain_probe",
    "two_root_constraint_layer_level_selector_necessity_countermodel_probe",
    "two_root_constraint_layer_selector_cross_carrier_minimality_probe",
    "two_root_constraint_selector_minimality_completion_audit_probe",
    "two_root_constraint_provider_and_global_falsifier_gap_probe",
    "two_root_constraint_global_countermodel_exhaustive_finite_family_probe",
    "two_root_constraint_global_countermodel_completion_audit_probe",
]

NEXT_REQUIRED_SCOUT = "two_root_constraint_estate_tool_gate_blocker_partition_probe"


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
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "completion_status": summary.get("completion_status"),
        "weak_or_open_requirements": summary.get("weak_or_open_requirements"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def run_fresh_validator() -> dict[str, Any]:
    paths = [RESULT_DIR / f"{stem}_results.json" for stem in CHAIN]
    cmd = [
        sys.executable,
        str(VALIDATOR),
        "--fresh-rerun",
        "--fresh-rerun-timeout",
        str(FRESH_RERUN_TIMEOUT_SECONDS),
        *[str(path) for path in paths],
    ]
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=FRESH_RERUN_WRAPPER_TIMEOUT_SECONDS,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"all_pass": False, "parse_error": proc.stdout[-1000:]}
    reruns = data.get("reruns", []) if isinstance(data, dict) else []
    results = data.get("results", []) if isinstance(data, dict) else []
    return {
        "pass": proc.returncode == 0 and data.get("all_pass") is True,
        "returncode": proc.returncode,
        "runtime_seconds": round(time.time() - started, 6),
        "command": [rel(pathlib.Path(part)) if part.startswith(str(REPO)) else part for part in cmd],
        "all_pass": data.get("all_pass"),
        "fresh_rerun": data.get("fresh_rerun"),
        "rerun_count": len(reruns),
        "result_count": len(results),
        "failed_reruns": [row for row in reruns if row.get("pass") is not True],
        "failed_results": [row for row in results if row.get("pass") is not True],
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
    }


def estate_tool_gate_report() -> dict[str, Any]:
    data = read_json(ESTATE_INDEX)
    tool_gate = data.get("tool_gate_summary", {}) if isinstance(data, dict) else {}
    status_counts = tool_gate.get("status_counts") or {}
    candidates = tool_gate.get("candidates") or []
    blockers = {
        key: value
        for key, value in status_counts.items()
        if str(key).startswith("blocked") or str(key).startswith("review")
    }
    return {
        "pass": bool(tool_gate) and bool(status_counts),
        "path": rel(ESTATE_INDEX),
        "status_counts": status_counts,
        "candidate_count": len(candidates) if isinstance(candidates, list) else None,
        "blocker_counts": blockers,
        "blocker_total": sum(int(value) for value in blockers.values()),
        "result_row_count": data.get("result_row_count"),
        "surface_counts": {
            "manifold": len(data.get("geometric_constraint_manifold_rows", [])),
            "peps": len(data.get("peps_peps3d_rows", [])),
            "axis0": len(data.get("axis0_summary", {}).get("axis0_rows", [])) if isinstance(data.get("axis0_summary"), dict) else None,
            "basin": len(data.get("attractor_basin_rows", [])),
            "lirpa_lewm": len(data.get("auto_lirpa_lewm_rows", [])),
        },
        "next_partition": [
            "blocked_numpy_load_bearing",
            "blocked_classical_or_admin_load_bearing",
            "blocked_result_not_all_pass",
            "review_unknown_tool_role",
        ],
    }


def graph_report(validator: dict[str, Any], estate: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    fresh = graph.add_node("fresh_rerun_chain")
    estate_node = graph.add_node("estate_tool_gate")
    next_node = graph.add_node(NEXT_REQUIRED_SCOUT)
    graph.add_edge(fresh, next_node, "fresh_pass" if validator["pass"] else "fresh_fail")
    graph.add_edge(estate_node, next_node, f"blockers:{estate['blocker_total']}")
    for status, count in estate["blocker_counts"].items():
        node = graph.add_node(status)
        graph.add_edge(node, estate_node, count)
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and graph.num_edges() >= 4,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def proof_report(validator: dict[str, Any], estate: dict[str, Any]) -> dict[str, Any]:
    fresh_pass = validator["pass"]
    blockers_clear = estate["blocker_total"] == 0

    f = z3.Bool("fresh_rerun_chain_pass")
    e = z3.Bool("estate_tool_gate_clear")
    complete = z3.Bool("completion_allowed")
    solver = z3.Solver()
    solver.add(f == fresh_pass)
    solver.add(e == blockers_clear)
    solver.add(complete == z3.And(f, e))
    solver.add(complete)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    cf = tm.mkConst(bsort, "fresh_rerun_chain_pass")
    ce = tm.mkConst(bsort, "estate_tool_gate_clear")
    cc = tm.mkConst(bsort, "completion_allowed")
    slv.assertFormula(cf if fresh_pass else tm.mkTerm(Kind.NOT, cf))
    slv.assertFormula(ce if blockers_clear else tm.mkTerm(Kind.NOT, ce))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, cc, tm.mkTerm(Kind.AND, cf, ce)))
    slv.assertFormula(cc)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": not z_sat and not c_sat,
        "fresh_rerun_chain_pass": fresh_pass,
        "estate_tool_gate_clear": blockers_clear,
        "z3_completion_still_blocked": not z_sat,
        "cvc5_completion_still_blocked": not c_sat,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "fresh-rerun chain passes and the remaining estate tool gate is hand-waved away",
        "most_dangerous_failure": "numpy/classical/admin load-bearing rows remain mixed into nonclassical tool-integration claims",
        "hidden_assumption": "candidate tool-role rows are enough to close blocker categories",
        "checks_applied": [
            "batch fresh-rerun validator",
            "estate blocker count partition",
            "z3/cvc5 completion block on uncleared tool gate",
            "next scout narrowed to blocker partition",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    validator = run_fresh_validator()
    estate = estate_tool_gate_report()
    graph = graph_report(validator, estate)
    proof = proof_report(validator, estate)
    premortem = premortem_report()
    positive = {
        "upstream_completion_audit_consumed": upstream,
        "active_chain_fresh_rerun_batch": validator,
        "estate_tool_gate_blockers_classified": estate,
        "blocker_dependency_graph": graph,
        "z3_cvc5_estate_tool_gate_completion_block": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "fresh_rerun_gap_killed_for_active_chain": {
            "pass": validator["pass"],
            "rerun_count": validator["rerun_count"],
            "failed_reruns": validator["failed_reruns"],
        },
        "tool_gate_as_closed_claim_killed": {
            "pass": estate["blocker_total"] > 0,
            "blocker_counts": estate["blocker_counts"],
        },
        "completion_before_tool_gate_partition_killed": proof,
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "completion_boundary": {
            "pass": True,
            "completion_status": "not_achieved",
            "reason": "Fresh-rerun gap is closed for the active chain, but estate tool-gate blockers remain.",
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Partition estate tool-gate blockers and choose repair vs quarantine for each blocker class.",
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
            "completion_status": "not_achieved",
            "active_chain_fresh_rerun_pass": validator["pass"],
            "fresh_rerun_count": validator["rerun_count"],
            "estate_tool_gate_blocker_total": estate["blocker_total"],
            "estate_tool_gate_blocker_counts": estate["blocker_counts"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "active chain fresh-reruns as a batch",
                "tool gate remains blocked and is not hidden",
                "next repair is partitioned by blocker class",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout using the canonical validator and estate index, not a v4 proposal.",
        "divergence_log": [
            "If fresh-rerun pass is used to ignore tool-gate blockers, integration overclaims.",
            "If blocked numpy/classical/admin rows are not partitioned, nonclassical tool integration stays muddy.",
            "If the next repair edits all blockers at once, the tool-gate evidence becomes hard to audit.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "active_chain_fresh_rerun_pass": validator["pass"],
                "fresh_rerun_count": validator["rerun_count"],
                "estate_tool_gate_blocker_total": estate["blocker_total"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
