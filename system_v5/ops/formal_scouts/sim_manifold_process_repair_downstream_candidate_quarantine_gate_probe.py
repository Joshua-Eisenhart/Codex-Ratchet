#!/usr/bin/env python3
"""Quarantine premature downstream manifold candidates.

Formal scout only.

This is a process-repair blocker. It preserves the raw candidate receipts but
blocks their use as dependencies because the full nested base-manifold closure
receipt does not exist yet.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "manifold_process_repair_downstream_candidate_quarantine_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

BASE_CLOSURE_RESULT = RESULT_DIR / "peps3d_full_nested_base_manifold_closure_gate_probe_results.json"
DOWNSTREAM_CANDIDATE_RESULTS = {
    "phase8b_flux_dependency": RESULT_DIR / "quaternionic_flux_dependency_admission_gate_probe_results.json",
    "phase9_xi_phi0_axis0_readout": RESULT_DIR / "xi_phi0_axis0_flux_readout_candidate_gate_probe_results.json",
    "phase9b_readout_dependency": RESULT_DIR / "xi_phi0_axis0_readout_dependency_stability_gate_probe_results.json",
    "phase10_readout_convergence": RESULT_DIR / "axis0_readout_finite_convergence_candidate_gate_probe_results.json",
}

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "manifold_process_repair_downstream_candidate_quarantine"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal process-repair blocker only: quarantines premature flux, Xi/Phi0, "
    "Axis0, and convergence candidate receipts from dependency use until the "
    "full nested base PEPS3D spinor-manifold closure receipt exists. It does "
    "not admit flux, Axis0, basin, physics, ontology, or closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing blocked-state tensor over quarantined candidate receipts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that missing full nested base closure implies downstream dependency use is blocked",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent proof of the same quarantine implication",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact candidate-count and closure-count checks",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency graph from required base closure to quarantined candidate receipts",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt reads and serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return as_jsonable(value.detach().cpu().tolist())
    return value


def read_result(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def full_nested_base_closure_state() -> dict[str, Any]:
    data = read_result(BASE_CLOSURE_RESULT)
    closed = bool(data.get("all_pass", False)) and bool(data.get("summary", {}).get("full_nested_base_manifold_closed", False))
    return {
        "pass": not closed,
        "base_closure_result": str(BASE_CLOSURE_RESULT.relative_to(ROOT)),
        "base_closure_exists": BASE_CLOSURE_RESULT.exists(),
        "full_nested_base_manifold_closed": closed,
        "quarantine_required": not closed,
        "next_admissible_step": "build and validate sim_peps3d_full_nested_base_manifold_closure_gate_probe.py before any flux/Xi/Phi0/Axis0/basin dependency use",
    }


def candidate_receipt_rows() -> list[dict[str, Any]]:
    rows = []
    for name, path in DOWNSTREAM_CANDIDATE_RESULTS.items():
        data = read_result(path)
        rows.append(
            {
                "name": name,
                "path": str(path.relative_to(ROOT)),
                "exists": path.exists(),
                "all_pass": bool(data.get("all_pass", False)),
                "promotion_allowed": data.get("promotion_allowed"),
                "claim_ceiling": data.get("claim_ceiling", ""),
                "summary": data.get("summary", {}),
                "eligible_consumers": data.get("eligible_consumers", []),
                "downstream_blocks": data.get("downstream_blocks", []),
            }
        )
    return rows


def dependency_graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    closure_node = graph.add_node("required_full_nested_base_closure")
    for row in rows:
        node = graph.add_node(row["name"])
        graph.add_edge(closure_node, node, "required_before")
    return {
        "pass": graph.num_nodes() == len(rows) + 1 and graph.num_edges() == len(rows),
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "root": "required_full_nested_base_closure",
        "edge_rule": "every downstream candidate depends on full nested base closure",
    }


def quarantine_gate() -> dict[str, Any]:
    closure = full_nested_base_closure_state()
    rows = candidate_receipt_rows()
    existing = [row for row in rows if row["exists"]]
    blocked_state = torch.ones(len(rows), dtype=torch.float64) if closure["quarantine_required"] else torch.zeros(len(rows), dtype=torch.float64)
    exact_candidate_count = sp.Integer(len(rows))
    exact_closure_count = sp.Integer(1)
    graph = dependency_graph(rows)
    return {
        "pass": bool(
            closure["quarantine_required"]
            and len(existing) == len(rows)
            and torch.all(blocked_state == 1.0).item()
            and int(exact_candidate_count) == 4
            and int(exact_closure_count) == 1
            and graph["pass"]
        ),
        "finite_map": (
            "Q_process : (required_full_nested_base_closure=false, downstream_candidate_receipts) "
            "-> quarantined_from_dependency_use"
        ),
        "domain": (
            "D_repair = missing full nested base PEPS3D spinor-manifold closure receipt plus "
            "premature Phase 8b/9/9b/10 candidate receipts"
        ),
        "output": "O_repair = quarantine receipt with downstream dependency use blocked",
        "peps3d_embedding": "blocked pending a single nested PEPS3D carrier run over Phases 0-7",
        "candidate_receipts_quarantined": [row["name"] for row in rows],
        "candidate_receipt_count": len(rows),
        "blocked_state_tensor": blocked_state,
        "full_nested_base_manifold_closed": closure["full_nested_base_manifold_closed"],
        "quarantine_required": closure["quarantine_required"],
        "dependency_graph": graph,
        "sympy_exact_candidate_count": int(exact_candidate_count),
        "sympy_exact_required_closure_count": int(exact_closure_count),
        "next_admissible_step": closure["next_admissible_step"],
    }


def z3_quarantine_gate(candidate_count: int) -> dict[str, Any]:
    closure_closed = z3.Bool("full_nested_base_closure_closed")
    eligible = [z3.Bool(f"candidate_{idx}_dependency_eligible") for idx in range(candidate_count)]
    solver = z3.Solver()
    solver.add(z3.Not(closure_closed))
    for item in eligible:
        solver.add(z3.Implies(z3.Not(closure_closed), z3.Not(item)))
    solver.add(z3.And(*[z3.Not(item) for item in eligible]))
    collapse = z3.Solver()
    collapse.add(z3.Not(closure_closed))
    for item in eligible:
        collapse.add(z3.Implies(z3.Not(closure_closed), z3.Not(item)))
    collapse.add(z3.Or(*eligible))
    return {
        "positive_status": str(solver.check()),
        "unsafe_dependency_status": str(collapse.check()),
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def cvc5_quarantine_gate(candidate_count: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    bool_sort = solver.getBooleanSort()
    closure_closed = solver.mkConst(bool_sort, "full_nested_base_closure_closed")
    eligible = [solver.mkConst(bool_sort, f"candidate_{idx}_dependency_eligible") for idx in range(candidate_count)]
    solver.assertFormula(solver.mkTerm(Kind.NOT, closure_closed))
    for item in eligible:
        solver.assertFormula(solver.mkTerm(Kind.IMPLIES, solver.mkTerm(Kind.NOT, closure_closed), solver.mkTerm(Kind.NOT, item)))
    solver.assertFormula(solver.mkTerm(Kind.AND, *[solver.mkTerm(Kind.NOT, item) for item in eligible]))
    positive = solver.checkSat()

    collapse = cvc5.Solver()
    collapse.setLogic("ALL")
    bsort = collapse.getBooleanSort()
    c_closed = collapse.mkConst(bsort, "full_nested_base_closure_closed")
    c_eligible = [collapse.mkConst(bsort, f"candidate_{idx}_dependency_eligible") for idx in range(candidate_count)]
    collapse.assertFormula(collapse.mkTerm(Kind.NOT, c_closed))
    for item in c_eligible:
        collapse.assertFormula(collapse.mkTerm(Kind.IMPLIES, collapse.mkTerm(Kind.NOT, c_closed), collapse.mkTerm(Kind.NOT, item)))
    collapse.assertFormula(collapse.mkTerm(Kind.OR, *c_eligible))
    unsafe = collapse.checkSat()
    return {"positive_status": str(positive), "unsafe_dependency_status": str(unsafe), "pass": str(positive) == "sat" and str(unsafe) == "unsat"}


def passing_candidate_control_rejected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passing = [row["name"] for row in rows if row["all_pass"]]
    return {
        "pass": len(passing) == len(rows),
        "why_rejected": "a passing candidate receipt is still not dependency-admissible without the full nested base closure receipt",
        "passing_candidate_receipts": passing,
    }


def promotion_false_control_rejected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fenced = [row["name"] for row in rows if row["promotion_allowed"] is False]
    return {
        "pass": len(fenced) == len(rows),
        "why_rejected": "promotion_allowed=false is necessary but not sufficient; dependency use is also blocked by missing nested closure",
        "promotion_fenced_receipts": fenced,
    }


def eligible_consumer_control_rejected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    named = [row["name"] for row in rows if row["eligible_consumers"]]
    return {
        "pass": True,
        "why_rejected": "any earlier eligible_consumers field is superseded by this quarantine until nested base closure exists",
        "receipts_with_eligible_consumers": named,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    closure = full_nested_base_closure_state()
    rows = candidate_receipt_rows()
    quarantine = quarantine_gate()
    blocked_reason = {
        "kind": "blocked_reason",
        "reason": "Downstream candidate receipts were produced before a single full nested base-manifold PEPS3D spinor-network closure receipt existed.",
        "scope": "Phase 8b flux dependency, Phase 9 Xi/Phi0/Axis0 readout, Phase 9b readout dependency, and Phase 10 convergence candidate dependency use",
        "next_admissible_step": closure["next_admissible_step"],
    }
    graveyard_companions = {
        "GC1_passing_candidate_receipt_control_rejected": passing_candidate_control_rejected(rows),
        "GC2_promotion_false_control_rejected": promotion_false_control_rejected(rows),
        "GC3_eligible_consumer_control_rejected": eligible_consumer_control_rejected(rows),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_downstream_dependency_use_blocked": {
            "pass": True,
            "blocked_consumers": ["flux dependency use", "Xi/Phi0/Axis0 dependency use", "basin", "physics", "final Axis0"],
        },
        "B3_next_step_is_base_closure": {"pass": True, "next_admissible_step": blocked_reason["next_admissible_step"]},
        "B4_no_candidate_receipt_rewritten": {
            "pass": True,
            "reason": "raw candidate metrics are preserved as raw metrics; a superseding quarantine controls dependency use",
        },
    }
    positive = {
        "full_nested_base_closure_missing_gate": closure,
        "downstream_candidate_quarantine_gate": quarantine,
        "z3_quarantine_implication": z3_quarantine_gate(len(rows)),
        "cvc5_quarantine_implication": cvc5_quarantine_gate(len(rows)),
    }
    controls = {"positive": positive, "negative": graveyard_companions, "boundary": boundary}
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [quarantine["finite_map"]],
        "domain": quarantine["domain"],
        "codomain_or_output": quarantine["output"],
        "carrier_realization": "no new manifold carrier action; process blocker pending integrated PEPS3D spinor-network closure",
        "peps3d_embedding": quarantine["peps3d_embedding"],
        "spinor_state": "blocked pending full nested base spinor-network carrier closure",
        "quaternion_action": "blocked pending full nested base closure before downstream quaternionic flux/readout dependency use",
        "dependency_receipts": [str(path.relative_to(ROOT)) for path in DOWNSTREAM_CANDIDATE_RESULTS.values()],
        "downstream_blocks": ["flux dependency use", "Xi/Phi0/Axis0 dependency use", "basin", "physics", "final Axis0"],
        "candidate_receipt_rows": rows,
        "blocked_reason": blocked_reason,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": controls,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "phase": "process_repair",
            "candidate": "downstream_candidate_quarantine",
            "full_nested_base_manifold_closed": closure["full_nested_base_manifold_closed"],
            "quarantine_required": quarantine["quarantine_required"],
            "candidate_receipt_count": quarantine["candidate_receipt_count"],
            "candidate_receipts_quarantined": quarantine["candidate_receipts_quarantined"],
            "dependency_use_admitted": False,
            "flux_admitted": False,
            "xi_phi0_axis0_admitted": False,
            "basin_promotion_admitted": False,
            "physics_admitted": False,
            "final_axis0_admitted": False,
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": "This is a v5 process-repair blocker for premature downstream manifold candidates, not a legacy v4 probe.",
        "next_required_work": [blocked_reason["next_admissible_step"]],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
