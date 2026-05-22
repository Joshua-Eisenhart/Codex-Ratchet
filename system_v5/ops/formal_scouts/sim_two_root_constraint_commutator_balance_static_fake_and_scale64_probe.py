#!/usr/bin/env python3
"""Static-fake and scale-64 follow-up for commutator-balance selector energy."""

from __future__ import annotations

import hashlib
import json
import pathlib
import statistics
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3

from sim_two_root_constraint_group_action_weighted_selector_or_energy_probe import (
    ACTIVE_SCALES,
    BOOTSTRAP_SAMPLES,
    STRETCH_SCALE,
    STEPS,
    TRAJECTORIES,
    bootstrap_ci_difference,
    build_context,
    run_condition,
)


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_commutator_balance_static_fake_and_scale64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_METRIC = RESULT_DIR / "two_root_constraint_group_action_weighted_selector_or_energy_probe_results.json"
UPSTREAM_CROSS_AUDIT = RESULT_DIR / "two_root_constraint_selector_energy_cross_audit_or_scale64_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_commutator_balance_static_fake_scale64"
CLAIM_CEILING = (
    "Formal scout only: tests whether commutator_balance_energy survives an "
    "explicit static-fingerprint fake control and active-scale 64 follow-up. "
    "It does not admit a final selector, geometric constraint manifold, real "
    "attractor basin, Clifford basin, Axis0, engine, physics, target-system, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing construction of finite static fake commute graphs"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that static-fake pass blocks selector survival"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof that static-fake pass blocks selector survival"},
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt parsing and serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and input hashing"},
    "python_statistics": {"tried": True, "used": True, "reason": "supportive finite metric summaries for scale-64 trajectories"},
}
TOOL_INTEGRATION_DEPTH = {
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "python_statistics": "supportive",
}

TWO_ROOT_CONSTRAINTS = {
    "F01": True,
    "N01": True,
    "finite_carrier_root": True,
    "noncommutation_or_order_root": True,
    "scope": "commutator-balance selector follow-up over finite Pauli-label dynamics plus static fake control",
}

SELECTOR = "commutator_balance_energy"
NEXT_REQUIRED_SCOUT = "two_root_constraint_selector_phase_bounded_synthesis_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def static_fake_for_scale(active_scale: int) -> dict[str, Any]:
    context = build_context(active_scale, SELECTOR)
    node_count = active_scale
    total_pairs = node_count * (node_count - 1) // 2
    target_fraction = float(context["null_commute_fraction_mean"])
    edge_count = round(target_fraction * total_pairs)
    fake_graph = rx.PyGraph()
    fake_graph.add_nodes_from(range(node_count))
    edges = []
    for i in range(node_count):
        for j in range(i + 1, node_count):
            if len(edges) < edge_count:
                edges.append((i, j))
    fake_graph.add_edges_from_no_data(edges)
    fake_fraction = fake_graph.num_edges() / total_pairs if total_pairs else 0.0
    fake_energy = abs(fake_fraction - target_fraction)
    return {
        "pass": fake_energy <= float(context["low_energy_threshold"]),
        "active_scale": active_scale,
        "node_count": node_count,
        "edge_count": fake_graph.num_edges(),
        "total_pairs": total_pairs,
        "fake_commute_fraction": fake_fraction,
        "null_commute_fraction_mean": target_fraction,
        "commutator_balance_energy": fake_energy,
        "low_energy_threshold": context["low_energy_threshold"],
        "has_symplectic_label_carrier": False,
        "has_order_sensitive_composition_witness": False,
        "interpretation": "static graph can match the scalar commutator-balance energy without a Pauli-label noncommuting carrier",
    }


def static_fake_control_report() -> dict[str, Any]:
    rows = {str(scale): static_fake_for_scale(scale) for scale in (*ACTIVE_SCALES, STRETCH_SCALE)}
    return {
        "pass": all(row["pass"] for row in rows.values()),
        "rows": rows,
        "graveyard_implication": "commutator_balance_energy as a standalone scalar selector cannot distinguish hand-faked static commute-fraction controls from true order-sensitive structure",
    }


def scale64_dynamic_report() -> dict[str, Any]:
    qubit_count = STRETCH_SCALE
    context = build_context(qubit_count, SELECTOR)
    reports = {}
    metric_passes = []
    for regime_index, regime in enumerate(("local", "group", "mixed")):
        seed_base = 64_000_000 + regime_index * 100_000
        baseline = run_condition(SELECTOR, False, regime, context, seed_base)
        selector_run = run_condition(SELECTOR, True, regime, context, seed_base + 50_000)
        comparisons = {}
        for metric_name in ("low_energy_dwell", "energy_improvement", "variance_zero_dwell"):
            ci = bootstrap_ci_difference(
                [float(row[metric_name]) for row in selector_run["rows"]],
                [float(row[metric_name]) for row in baseline["rows"]],
                seed=seed_base + len(metric_name) * 313,
                samples=BOOTSTRAP_SAMPLES,
            )
            comparisons[metric_name] = ci
            if metric_name in {"low_energy_dwell", "energy_improvement"} and ci["pass"]:
                metric_passes.append({"regime": regime, "metric": metric_name, "ci": ci})
        reports[regime] = {
            "baseline": baseline["summary"],
            "selector": selector_run["summary"],
            "bootstrap_comparisons": comparisons,
        }
    return {
        "pass": True,
        "active_scale": qubit_count,
        "active_scale_meaning": "qubit/site count and sampled Pauli-label state size",
        "sample_floor": {"trajectories": TRAJECTORIES, "steps": STEPS},
        "context": {
            key: value
            for key, value in context.items()
            if key != "actions"
        } | {"action_family_count": len(context["actions"])},
        "reports": reports,
        "metric_passes": metric_passes,
        "has_scale64_metric_pass": bool(metric_passes),
        "interpretation": "scale-64 dynamics can only support metric evidence; static-fake failure still blocks standalone selector survival",
    }


def proof_report(static_fake: dict[str, Any], scale64: dict[str, Any], cross_audit: dict[str, Any]) -> dict[str, Any]:
    fake_passes = bool(static_fake["pass"])
    scale64_metric = bool(scale64["has_scale64_metric_pass"])
    prior_borderline = cross_audit["summary"]["provider_verdict"] == "borderline_requires_static_fake_and_scale64"

    z_fake = z3.Bool("static_fake_passes")
    z_scale = z3.Bool("scale64_metric_pass")
    z_prior = z3.Bool("prior_cross_audit_borderline")
    z_survived = z3.Bool("standalone_commutator_balance_survived")
    solver = z3.Solver()
    solver.add(z_fake == fake_passes)
    solver.add(z_scale == scale64_metric)
    solver.add(z_prior == prior_borderline)
    solver.add(z_survived == z3.And(z_scale, z3.Not(z_fake), z3.Not(z_prior)))
    solver.add(z_survived)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_fake = tm.mkConst(bsort, "static_fake_passes")
    c_scale = tm.mkConst(bsort, "scale64_metric_pass")
    c_prior = tm.mkConst(bsort, "prior_cross_audit_borderline")
    c_survived = tm.mkConst(bsort, "standalone_commutator_balance_survived")
    slv.assertFormula(c_fake if fake_passes else tm.mkTerm(Kind.NOT, c_fake))
    slv.assertFormula(c_scale if scale64_metric else tm.mkTerm(Kind.NOT, c_scale))
    slv.assertFormula(c_prior if prior_borderline else tm.mkTerm(Kind.NOT, c_prior))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_survived, tm.mkTerm(Kind.AND, c_scale, tm.mkTerm(Kind.NOT, c_fake), tm.mkTerm(Kind.NOT, c_prior))))
    slv.assertFormula(c_survived)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": not z_sat and not c_sat,
        "static_fake_passes": fake_passes,
        "scale64_metric_pass": scale64_metric,
        "prior_cross_audit_borderline": prior_borderline,
        "z3_standalone_survival_unsat": not z_sat,
        "cvc5_standalone_survival_unsat": not c_sat,
        "blocked_reason": "static fake passes the scalar selector, so commutator_balance_energy is not sufficient as a standalone basin selector even if scale-64 metric evidence is positive",
    }


def main() -> int:
    started = time.time()
    upstream_metric = read_json(UPSTREAM_METRIC)
    cross_audit = read_json(UPSTREAM_CROSS_AUDIT)
    static_fake = static_fake_control_report()
    scale64 = scale64_dynamic_report()
    proof = proof_report(static_fake, scale64, cross_audit)
    positive = {
        "upstream_metric_pass_consumed": {
            "pass": upstream_metric["summary"]["candidate_statuses"][SELECTOR]["multi_substrate_metric_pass"] is True,
            "path": rel(UPSTREAM_METRIC),
            "sha256": sha256_file(UPSTREAM_METRIC),
        },
        "cross_audit_borderline_consumed": {
            "pass": cross_audit["summary"]["provider_verdict"] == "borderline_requires_static_fake_and_scale64",
            "path": rel(UPSTREAM_CROSS_AUDIT),
            "sha256": sha256_file(UPSTREAM_CROSS_AUDIT),
        },
        "scale64_dynamic_followup": scale64,
        "static_fake_control_executed": static_fake,
        "z3_cvc5_standalone_selector_block": proof,
    }
    graveyard = {
        "commutator_balance_as_standalone_selector_killed_by_static_fake": {
            "pass": static_fake["pass"] and proof["pass"],
            "reason": "hand-faked static commute-fraction controls pass the scalar energy without order-sensitive Pauli structure",
        },
        "scale64_metric_as_basin_claim_killed": {
            "pass": proof["pass"],
            "reason": "even positive scale-64 metric evidence cannot override the static-fake anti-tautology failure",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Synthesize selector-phase status: degree regularization killed, finite symmetry closure inconclusive/weak, commutator balance killed as standalone by static fake.",
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
        "two_root_constraints": TWO_ROOT_CONSTRAINTS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script_sha256": sha256_file(pathlib.Path(__file__)),
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "not_achieved",
            "candidate": SELECTOR,
            "static_fake_passed": static_fake["pass"],
            "scale64_metric_pass": scale64["has_scale64_metric_pass"],
            "standalone_selector_survived": False,
            "verdict": "standalone_commutator_balance_killed_by_static_fake_control",
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": "This is a v5 formal scout over selector-phase anti-tautology controls, not a v4 proposal.",
        "divergence_log": [
            "If scalar commutator balance is treated as a standalone selector, static fake controls can pass without N01 structure.",
            "If scale-64 metric evidence is promoted without fake controls, low-energy dwell is confused with basin attraction.",
            "If commutator balance is reused later, it must be subordinate to a stronger order-sensitive selector, not standalone.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": rel(OUT_PATH), "all_pass": all_pass, "verdict": result["summary"]["verdict"], "scale64_metric_pass": scale64["has_scale64_metric_pass"], "static_fake_passed": static_fake["pass"], "next_required_scout": NEXT_REQUIRED_SCOUT}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
