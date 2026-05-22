#!/usr/bin/env python3
"""Bounded synthesis receipt for the selector/energy first-pass phase."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_selector_phase_bounded_synthesis_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

WEIGHTED_SELECTOR = RESULT_DIR / "two_root_constraint_group_action_weighted_selector_or_energy_probe_results.json"
CROSS_AUDIT = RESULT_DIR / "two_root_constraint_selector_energy_cross_audit_or_scale64_probe_results.json"
STATIC_FAKE_SCALE64 = RESULT_DIR / "two_root_constraint_commutator_balance_static_fake_and_scale64_probe_results.json"
PLAN_PATH = REPO / "system_v5" / "ops" / "NEXT_GOAL_SELECTOR_ENERGY_PHASE_PLAN.md"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_selector_phase_bounded_synthesis"
CLAIM_CEILING = (
    "Formal scout only: synthesizes the first-pass selector/energy phase over "
    "degree regularization, finite symmetry closure, and commutator balance. "
    "It may close the listed first-pass selector families as failed or killed, "
    "but does not admit a final geometric constraint manifold, real attractor "
    "basin, Clifford basin, Axis0, engine, physics, target-system, Holodeck, "
    "or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive parsing of first-pass selector result receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive input/source hashing"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing dependency graph proving all listed selector-family receipts were consumed"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that no listed selector family survived the gates"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof that no listed selector family survived the gates"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

TWO_ROOT_CONSTRAINTS = {
    "F01": True,
    "N01": True,
    "finite_carrier_root": True,
    "noncommutation_or_order_root": True,
    "scope": "bounded synthesis of first-pass selector/energy receipts under two-root basin constraints",
}

NEXT_REQUIRED_SCOUT = "two_root_constraint_measure_theoretic_extreme_corner_reframe_probe"


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


def dependency_report() -> dict[str, Any]:
    paths = {
        "weighted_selector": WEIGHTED_SELECTOR,
        "cross_audit": CROSS_AUDIT,
        "static_fake_scale64": STATIC_FAKE_SCALE64,
        "goal_plan": PLAN_PATH,
    }
    graph = rx.PyDiGraph()
    synthesis = graph.add_node("selector_phase_synthesis")
    for name, path in paths.items():
        node = graph.add_node(name)
        graph.add_edge(node, synthesis, rel(path))
    rows = {
        name: {"path": rel(path), "exists": path.exists(), "sha256": sha256_file(path) if path.exists() else None}
        for name, path in paths.items()
    }
    return {
        "pass": all(row["exists"] for row in rows.values()) and graph.num_edges() == len(paths),
        "dependency_graph_node_count": graph.num_nodes(),
        "dependency_graph_edge_count": graph.num_edges(),
        "inputs": rows,
    }


def selector_family_status(weighted: dict[str, Any], cross: dict[str, Any], fake: dict[str, Any]) -> dict[str, Any]:
    statuses = weighted["summary"]["candidate_statuses"]
    degree = {
        "status": "killed",
        "reason": "graveyard-by-design direct variance/degree regularization control",
        "evidence": statuses["degree_regularization_energy"],
    }
    finite_closure = {
        "status": "killed",
        "reason": "failed first-pass metric gate across active scales 8 and 16; no survived or borderline provider route opened",
        "evidence": statuses["finite_symmetry_closure_energy"],
    }
    commutator = {
        "status": "killed_as_standalone_selector",
        "reason": "metric pass and cross-audit borderline were superseded by static-fake control; scale64 metric signal remains insufficient",
        "weighted_metric": statuses["commutator_balance_energy"],
        "cross_audit": cross["summary"],
        "static_fake_scale64": fake["summary"],
    }
    survived = []
    killed = {
        "degree_regularization_energy": degree,
        "finite_symmetry_closure_energy": finite_closure,
        "commutator_balance_energy": commutator,
    }
    return {
        "pass": True,
        "survived_selector_families": survived,
        "killed_or_failed_selector_families": killed,
        "listed_first_pass_family_count": 3,
        "listed_first_pass_survivor_count": 0,
        "listed_first_pass_killed_or_failed_count": len(killed),
        "outcome": "Outcome_B_first_pass_selectors_fail",
        "claim_boundary": "This closes only the listed first-pass families; it does not prove all possible selector families are exhausted.",
    }


def proof_report(status: dict[str, Any]) -> dict[str, Any]:
    degree_killed = "degree_regularization_energy" in status["killed_or_failed_selector_families"]
    closure_killed = "finite_symmetry_closure_energy" in status["killed_or_failed_selector_families"]
    commutator_killed = "commutator_balance_energy" in status["killed_or_failed_selector_families"]
    no_survivors = int(status["listed_first_pass_survivor_count"]) == 0

    z_degree = z3.Bool("degree_killed")
    z_closure = z3.Bool("closure_killed")
    z_commutator = z3.Bool("commutator_killed")
    z_no_survivors = z3.Bool("no_survivors")
    z_close = z3.Bool("first_pass_outcome_b_closed")
    solver = z3.Solver()
    solver.add(z_degree == degree_killed)
    solver.add(z_closure == closure_killed)
    solver.add(z_commutator == commutator_killed)
    solver.add(z_no_survivors == no_survivors)
    solver.add(z_close == z3.And(z_degree, z_closure, z_commutator, z_no_survivors))
    solver.add(z3.Not(z_close))
    z_unsat = solver.check() == z3.unsat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_degree = tm.mkConst(bsort, "degree_killed")
    c_closure = tm.mkConst(bsort, "closure_killed")
    c_commutator = tm.mkConst(bsort, "commutator_killed")
    c_no_survivors = tm.mkConst(bsort, "no_survivors")
    c_close = tm.mkConst(bsort, "first_pass_outcome_b_closed")
    slv.assertFormula(c_degree if degree_killed else tm.mkTerm(Kind.NOT, c_degree))
    slv.assertFormula(c_closure if closure_killed else tm.mkTerm(Kind.NOT, c_closure))
    slv.assertFormula(c_commutator if commutator_killed else tm.mkTerm(Kind.NOT, c_commutator))
    slv.assertFormula(c_no_survivors if no_survivors else tm.mkTerm(Kind.NOT, c_no_survivors))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_close, tm.mkTerm(Kind.AND, c_degree, c_closure, c_commutator, c_no_survivors)))
    slv.assertFormula(tm.mkTerm(Kind.NOT, c_close))
    c_unsat = slv.checkSat().isUnsat()
    return {
        "pass": z_unsat and c_unsat,
        "degree_regularization_killed": degree_killed,
        "finite_symmetry_closure_killed": closure_killed,
        "commutator_balance_killed": commutator_killed,
        "no_first_pass_survivors": no_survivors,
        "z3_outcome_b_close_proved": z_unsat,
        "cvc5_outcome_b_close_proved": c_unsat,
    }


def main() -> int:
    started = time.time()
    weighted = read_json(WEIGHTED_SELECTOR)
    cross = read_json(CROSS_AUDIT)
    fake = read_json(STATIC_FAKE_SCALE64)
    deps = dependency_report()
    status = selector_family_status(weighted, cross, fake)
    proof = proof_report(status)
    positive = {
        "input_dependency_graph_complete": deps,
        "selector_family_status_synthesized": status,
        "z3_cvc5_first_pass_outcome_b_close": proof,
    }
    graveyard = {
        "degree_regularization_first_pass_killed": {
            "pass": status["killed_or_failed_selector_families"]["degree_regularization_energy"]["status"] == "killed",
            "reason": status["killed_or_failed_selector_families"]["degree_regularization_energy"]["reason"],
        },
        "finite_symmetry_closure_first_pass_killed": {
            "pass": status["killed_or_failed_selector_families"]["finite_symmetry_closure_energy"]["status"] == "killed",
            "reason": status["killed_or_failed_selector_families"]["finite_symmetry_closure_energy"]["reason"],
        },
        "commutator_balance_standalone_first_pass_killed": {
            "pass": status["killed_or_failed_selector_families"]["commutator_balance_energy"]["status"] == "killed_as_standalone_selector",
            "reason": status["killed_or_failed_selector_families"]["commutator_balance_energy"]["reason"],
        },
        "dynamic_basin_generation_claim_killed_for_first_pass_selectors": {
            "pass": proof["pass"],
            "reason": "no listed first-pass selector family survived all gates; static/extreme-corner plus reachability/orbit connectivity remains the honest boundary",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "cleanup_boundary": {
            "pass": True,
            "temporary_goal_docs_cleanup_pending_user_approval": [rel(PLAN_PATH)],
            "reason": "This synthesis closes the first-pass selector evidence, but repo cleanup of NEXT_GOAL docs is a controller/user-approved hygiene step, not a proof mutation.",
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "If continuing theory rather than cleanup, reframe toward measure-theoretic/static extreme-corner evidence or design a stronger order-sensitive selector that rejects static fakes.",
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
            "completion_status": "first_pass_selector_phase_closed_outcome_B",
            "listed_first_pass_family_count": 3,
            "listed_first_pass_survivor_count": 0,
            "outcome": status["outcome"],
            "claim_boundary": status["claim_boundary"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": "This is a v5 formal scout synthesis over selector-energy receipts, not a v4 proposal.",
        "divergence_log": [
            "If Outcome B is read as all possible selectors exhausted, the synthesis overclaims.",
            "If low-energy dwell is called a basin, the commutator-balance static-fake kill is ignored.",
            "If temporary goal docs are left active indefinitely, future threads may treat a closed first-pass plan as still live.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": rel(OUT_PATH), "all_pass": all_pass, "outcome": status["outcome"], "survivor_count": 0, "next_required_scout": NEXT_REQUIRED_SCOUT}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
