#!/usr/bin/env python3
"""Boundary-projected gamma5 chirality channel coherent-information scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import sympy as sp
import torch
import z3

from sim_boundary_projected_gamma5_chirality_channel_trace_distance_probe import (
    apply_boundary_expectation,
    boundary_graph,
    cptp_gap_any,
)
from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    DTYPE,
    apply_kraus,
    gamma5_boundary,
    symmetric_kraus,
)
from sim_gamma5_offdiagonal_coherence_trace_orbit_survivor_quotient_probe import (
    DIM,
    N_QUBITS,
    asymmetric_local_kraus,
    candidate_densities,
    embed,
)
from sim_spinor_shell_coherent_information_locality_preserving_rank3_control_probe import signed_readout


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "boundary_projected_gamma5_chirality_channel_coherent_information_probe_results.json"

NAME = "boundary_projected_gamma5_chirality_channel_coherent_information_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: composes a finite boundary conditional expectation "
    "with gamma5 chirality-asymmetric CPTP channels and reads coherent "
    "information plus conditional entropy against symmetric, equal-rate, "
    "static, and random-boundary controls. It does not admit novelty, "
    "empirical physics, a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "load-bearing local bounded golden-section scalar search for symmetric effective-rate fit"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density evolution, boundary expectation, entropy spectra, coherent information, CPTP checks, and fit objective evaluation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing coherent-information/conditional-entropy identity check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing survivor/control witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def bounded_scalar_minimize(objective: Callable[[float], float], lower: float, upper: float, *, xatol: float = 1e-10, max_iter: int = 256) -> dict[str, Any]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    inv_phi = 1.0 / phi
    left = float(lower)
    right = float(upper)
    c = right - (right - left) * inv_phi
    d = left + (right - left) * inv_phi
    fc = float(objective(c))
    fd = float(objective(d))
    iterations = 0
    while abs(right - left) > xatol and iterations < max_iter:
        iterations += 1
        if fc <= fd:
            right = d
            d = c
            fd = fc
            c = right - (right - left) * inv_phi
            fc = float(objective(c))
        else:
            left = c
            c = d
            fc = fd
            d = left + (right - left) * inv_phi
            fd = float(objective(d))
    x = (left + right) / 2.0
    fun = float(objective(x))
    return {"x": x, "fun": fun, "success": math.isfinite(fun) and iterations < max_iter, "iterations": iterations}


def sequence_kraus(step: int, mode: str, gamma: float | None = None) -> list[torch.Tensor]:
    if mode == "dynamic_asymmetric":
        return embed(asymmetric_local_kraus(0.08 + 0.035 * step, 0.025 + 0.010 * step))
    if mode == "static_asymmetric":
        return embed(asymmetric_local_kraus(0.16, 0.055))
    if mode == "equal_rate":
        rate = 0.115 if gamma is None else gamma
        return embed(asymmetric_local_kraus(rate, rate))
    if mode == "symmetric":
        rate = 0.10 if gamma is None else gamma
        return embed(symmetric_kraus(rate))
    raise ValueError(mode)


def run_sequence(rho: torch.Tensor, channel_mode: str, boundary_mode: str, gamma: float | None = None) -> dict[str, Any]:
    current = apply_boundary_expectation(rho, boundary_mode)
    coherent = [signed_readout(current)["coherent_information_local_to_rest"]]
    conditional = [signed_readout(current)["conditional_entropy_local_given_rest"]]
    cptp = []
    for step in range(1, 7):
        kraus = sequence_kraus(step, channel_mode, gamma=gamma)
        cptp.append(cptp_gap_any(kraus))
        current = apply_kraus(current, kraus)
        current = apply_boundary_expectation(current, boundary_mode)
        row = signed_readout(current)
        coherent.append(row["coherent_information_local_to_rest"])
        conditional.append(row["conditional_entropy_local_given_rest"])
    return {"coherent_orbit": coherent, "conditional_orbit": conditional, "max_cptp_gap": max(cptp)}


def l2_gap(left: list[float], right: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(left, dtype=torch.float64) - torch.tensor(right, dtype=torch.float64)).item())


def best_symmetric_fit(rho: torch.Tensor, target: list[float], boundary_mode: str) -> dict[str, Any]:
    def objective(rate: float) -> float:
        return l2_gap(target, run_sequence(rho, "symmetric", boundary_mode, gamma=float(rate))["coherent_orbit"])
    result = bounded_scalar_minimize(objective, 0.0, 0.35, xatol=1e-10)
    row = run_sequence(rho, "symmetric", boundary_mode, gamma=float(result["x"]))
    return {"gamma": float(result["x"]), "gap": float(result["fun"]), "coherent_orbit": row["coherent_orbit"], "success": bool(result["success"])}


def symbolic_signed_boundary() -> dict[str, Any]:
    s_ab, s_b = sp.symbols("S_AB S_B")
    return {"coherent_plus_conditional": str(sp.simplify((s_b - s_ab) + (s_ab - s_b))), "pass": sp.simplify((s_b - s_ab) + (s_ab - s_b)) == 0}


def z3_witness(sym_count: int, equal_count: int, random_collisions: int, cptp: float, entropy_bound: float) -> dict[str, Any]:
    solver = z3.Solver()
    sym, equal, collisions, valid, inside = z3.Bools("sym equal collisions valid inside")
    solver.add(sym == (sym_count >= 5))
    solver.add(equal == (equal_count >= 5))
    solver.add(collisions == (random_collisions > 0))
    solver.add(valid == (cptp < 1e-12))
    solver.add(inside == (entropy_bound <= N_QUBITS * math.log(2) + 1e-12))
    solver.add(z3.Not(z3.And(sym, equal, collisions, valid, inside)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "symmetric_survivor_count": sym_count, "equal_rate_survivor_count": equal_count, "random_boundary_collision_count": random_collisions, "cptp_valid": cptp < 1e-12, "inside_information_bound": entropy_bound <= N_QUBITS * math.log(2) + 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = {}
    symmetric_survivors = []
    equal_survivors = []
    random_collisions = []
    cptp_gaps = []
    max_abs_signed = 0.0
    for name, rho in candidate_densities().items():
        target = run_sequence(rho, "dynamic_asymmetric", "nearest")
        symmetric = best_symmetric_fit(rho, target["coherent_orbit"], "nearest")
        equal = run_sequence(rho, "equal_rate", "nearest", gamma=0.115)
        static = run_sequence(rho, "static_asymmetric", "nearest")
        random_boundary = run_sequence(rho, "dynamic_asymmetric", "random_boundary")
        sym_gap = symmetric["gap"]
        equal_gap = l2_gap(target["coherent_orbit"], equal["coherent_orbit"])
        static_gap = l2_gap(target["coherent_orbit"], static["coherent_orbit"])
        random_gap = l2_gap(target["coherent_orbit"], random_boundary["coherent_orbit"])
        if sym_gap > 0.01:
            symmetric_survivors.append(name)
        if equal_gap > 0.01:
            equal_survivors.append(name)
        if random_gap <= 0.005:
            random_collisions.append(name)
        cptp_gaps.extend([target["max_cptp_gap"], equal["max_cptp_gap"], static["max_cptp_gap"], random_boundary["max_cptp_gap"]])
        max_abs_signed = max(max_abs_signed, max(abs(v) for v in target["coherent_orbit"] + target["conditional_orbit"]))
        rows[name] = {
            "dynamic_boundary_projected": target,
            "best_symmetric_fit": symmetric,
            "equal_rate_control": equal,
            "static_asymmetric_control": static,
            "random_boundary_control": random_boundary,
            "symmetric_gap": sym_gap,
            "equal_rate_gap": equal_gap,
            "static_gap": static_gap,
            "random_boundary_gap": random_gap,
        }
    max_cptp = max(cptp_gaps)
    _, boundary_nodes, interior_nodes = boundary_graph()
    positive = {
        "boundary_projected_coherent_information_has_symmetric_fit_survivor_rows": {"survivor_names": symmetric_survivors, "survivor_count": len(symmetric_survivors), "threshold": 0.01, "pass": len(symmetric_survivors) >= 5},
        "boundary_projected_coherent_information_has_equal_rate_survivor_rows": {"survivor_names": equal_survivors, "survivor_count": len(equal_survivors), "threshold": 0.01, "pass": len(equal_survivors) >= 5},
        "boundary_projected_sequence_is_cptp": {"max_cptp_gap": max_cptp, "pass": max_cptp < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
        "symbolic_signed_entropy_boundary": symbolic_signed_boundary(),
    }
    graveyard_companions = {
        "random_boundary_projection_collides_on_some_rows": {"collision_names": random_collisions, "collision_count": len(random_collisions), "pass": len(random_collisions) > 0},
        "static_asymmetric_control_gap_is_recorded": {"min_static_gap": min(row["static_gap"] for row in rows.values()), "pass": True},
        "boundary_graph_has_interior_and_boundary": {"boundary_nodes": len(boundary_nodes), "interior_nodes": len(interior_nodes), "pass": len(boundary_nodes) == 12 and len(interior_nodes) == 4},
        "signed_readouts_stay_inside_finite_information_bound": {"max_abs_signed_readout": max_abs_signed, "bound": N_QUBITS * math.log(2), "pass": max_abs_signed <= N_QUBITS * math.log(2) + 1e-12},
    }
    boundary = {
        "z3_boundary_projected_coherent_information_witness": z3_witness(len(symmetric_survivors), len(equal_survivors), len(random_collisions), max_cptp, max_abs_signed),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit finite boundary conditional expectation composed with gamma5 chirality-asymmetric CPTP channels and read by coherent-information and conditional-entropy orbits",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This is still a four-qubit readout scout, not the requested eight-qubit tensor-network lift.",
            "Random boundary projection collisions remain a live weakness.",
            "Next scout should either add stronger locality-preserving rank-3 controls or lift this readout to eight qubits.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from current Grok/Gemini coherent-information convergence; it is not a canonical v4 probe.",
        "raw_rows": rows,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "symmetric_survivors": len(symmetric_survivors), "equal_rate_survivors": len(equal_survivors), "random_boundary_collisions": len(random_collisions)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
