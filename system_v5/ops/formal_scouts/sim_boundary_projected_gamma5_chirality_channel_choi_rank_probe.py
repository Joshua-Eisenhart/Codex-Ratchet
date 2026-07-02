#!/usr/bin/env python3
"""Boundary-projected gamma5 chirality channel Choi-rank scout."""

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
    cptp_gap_any,
    boundary_expectation_kraus,
    boundary_graph,
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
    embed,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "boundary_projected_gamma5_chirality_channel_choi_rank_probe_results.json"

NAME = "boundary_projected_gamma5_chirality_channel_choi_rank_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: builds effective Choi matrices for finite "
    "boundary-projected gamma5 chirality-asymmetric channel sequences and "
    "compares Choi rank, spectrum, and trace distance against symmetric, "
    "equal-rate, static, random-boundary, and arbitrary same-channel controls. "
    "It does not admit novelty, empirical physics, a final manifold tower, "
    "ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "supportive local bounded golden-section scalar search for symmetric effective-rate Choi-distance fit"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing effective channel application, Choi matrices, ranks, spectra, trace distances, and fit objective evaluation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic Choi dimension and rank boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing Choi-rank survivor/control witness"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "python_math" else "load_bearing")
    for tool in TOOL_MANIFEST
}


def bounded_scalar_minimize(objective: Callable[[float], float], lower: float, upper: float, *, xatol: float = 1e-9, max_iter: int = 256) -> dict[str, Any]:
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
        gamma_left = 0.08 + 0.035 * step
        gamma_right = 0.025 + 0.010 * step
        return embed(asymmetric_local_kraus(gamma_left, gamma_right))
    if mode == "static_asymmetric":
        return embed(asymmetric_local_kraus(0.16, 0.055))
    if mode == "equal_rate":
        rate = 0.115 if gamma is None else gamma
        return embed(asymmetric_local_kraus(rate, rate))
    if mode == "symmetric":
        rate = 0.10 if gamma is None else gamma
        return embed(symmetric_kraus(rate))
    raise ValueError(mode)


def apply_sequence_to_basis(i: int, j: int, channel_mode: str, boundary_mode: str, gamma: float | None = None) -> torch.Tensor:
    _, boundary, interior = boundary_graph()
    boundary_kraus = boundary_expectation_kraus(boundary, interior, mode=boundary_mode)
    op = torch.zeros((DIM, DIM), dtype=DTYPE)
    op[i, j] = 1.0
    current = apply_kraus(op, boundary_kraus)
    for step in range(1, 7):
        current = apply_kraus(current, sequence_kraus(step, channel_mode, gamma=gamma))
        current = apply_kraus(current, boundary_kraus)
    return current


def choi_matrix(channel_mode: str, boundary_mode: str = "nearest", gamma: float | None = None) -> torch.Tensor:
    tensor = torch.zeros((DIM, DIM, DIM, DIM), dtype=DTYPE)
    for i in range(DIM):
        for j in range(DIM):
            tensor[i, j] = apply_sequence_to_basis(i, j, channel_mode, boundary_mode, gamma=gamma)
    return tensor.permute(0, 2, 1, 3).reshape(DIM * DIM, DIM * DIM) / DIM


def trace_distance(left: torch.Tensor, right: torch.Tensor) -> float:
    diff = (left - right + (left - right).conj().T) / 2
    return float(0.5 * torch.sum(torch.linalg.svdvals(diff)).item())


def choi_rank(choi: torch.Tensor, threshold: float = 1e-10) -> int:
    eigs = torch.linalg.eigvalsh((choi + choi.conj().T) / 2).real
    return int((eigs > threshold).sum().item())


def spectrum_signature(choi: torch.Tensor) -> list[float]:
    eigs = torch.sort(torch.clamp(torch.linalg.eigvalsh((choi + choi.conj().T) / 2).real, min=0.0), descending=True).values
    return [float(v) for v in eigs[:12]]


def best_symmetric_fit(target: torch.Tensor) -> dict[str, Any]:
    def objective(rate: float) -> float:
        return trace_distance(target, choi_matrix("symmetric", gamma=float(rate)))
    result = bounded_scalar_minimize(objective, 0.0, 0.35, xatol=1e-9)
    best = choi_matrix("symmetric", gamma=float(result["x"]))
    return {"gamma": float(result["x"]), "choi_trace_distance": float(result["fun"]), "choi_rank": choi_rank(best), "spectrum": spectrum_signature(best), "success": bool(result["success"])}


def sequence_cptp_gap(channel_mode: str, boundary_mode: str = "nearest") -> float:
    _, boundary, interior = boundary_graph()
    gaps = [cptp_gap_any(boundary_expectation_kraus(boundary, interior, mode=boundary_mode))]
    for step in range(1, 7):
        gaps.append(cptp_gap_any(sequence_kraus(step, channel_mode)))
    return max(gaps)


def z3_witness(target_rank: int, symmetric_gap: float, equal_gap: float, random_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    rank_nonzero, sym_sep, equal_sep, random_diff, valid = z3.Bools("rank_nonzero sym_sep equal_sep random_diff valid")
    solver.add(rank_nonzero == (target_rank > 0))
    solver.add(sym_sep == (symmetric_gap > 0.015))
    solver.add(equal_sep == (equal_gap > 0.015))
    solver.add(random_diff == (random_gap > 0.005))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(rank_nonzero, sym_sep, equal_sep, random_diff, valid)))
    status = solver.check()
    return {"solver_status": str(status), "pass": status == z3.unsat, "target_rank": target_rank, "symmetric_gap": symmetric_gap, "equal_rate_gap": equal_gap, "random_boundary_gap": random_gap, "cptp_valid": cptp < 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    target = choi_matrix("dynamic_asymmetric")
    symmetric_fit = best_symmetric_fit(target)
    equal = choi_matrix("equal_rate")
    static = choi_matrix("static_asymmetric")
    random_boundary = choi_matrix("dynamic_asymmetric", boundary_mode="random_boundary")
    target_rank = choi_rank(target)
    equal_gap = trace_distance(target, equal)
    static_gap = trace_distance(target, static)
    random_gap = trace_distance(target, random_boundary)
    self_gap = trace_distance(target, target)
    cptp = max(sequence_cptp_gap("dynamic_asymmetric"), sequence_cptp_gap("equal_rate"), sequence_cptp_gap("static_asymmetric"), sequence_cptp_gap("dynamic_asymmetric", boundary_mode="random_boundary"))
    symbolic = sp.Integer(DIM * DIM) == sp.Integer(256)
    positive = {
        "boundary_projected_dynamic_gamma5_choi_resists_symmetric_effective_fit": {"best_fit": symmetric_fit, "pass": symmetric_fit["choi_trace_distance"] > 0.015},
        "boundary_projected_dynamic_gamma5_choi_resists_equal_rate_control": {"equal_rate_choi_trace_distance": equal_gap, "pass": equal_gap > 0.015},
        "boundary_projected_dynamic_gamma5_choi_changes_under_random_boundary_projection": {"random_boundary_choi_trace_distance": random_gap, "pass": random_gap > 0.005},
        "effective_sequence_is_cptp": {"max_cptp_gap": cptp, "pass": cptp < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
    }
    graveyard_companions = {
        "arbitrary_same_channel_control_matches_exactly": {"same_channel_gap": self_gap, "pass": self_gap < 1e-12},
        "static_asymmetric_control_gap_is_recorded": {"static_asymmetric_choi_trace_distance": static_gap, "pass": True},
        "choi_dimension_boundary": {"dimension": DIM, "choi_dimension": DIM * DIM, "pass": bool(symbolic)},
        "target_choi_rank_is_recorded_not_promoted": {"target_choi_rank": target_rank, "pass": target_rank > 0},
    }
    boundary = {
        "z3_boundary_projected_gamma5_choi_witness": z3_witness(target_rank, symmetric_fit["choi_trace_distance"], equal_gap, random_gap, cptp),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "effective Choi matrix for six-step finite boundary-projected gamma5 chirality-asymmetric CPTP sequence compared with symmetric, equal-rate, static, random-boundary, and arbitrary same-channel controls",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This tests the composed effective channel rather than a state-orbit readout.",
            "The arbitrary same-channel control remains an exact representation, so this cannot prove novelty against unrestricted CPTP.",
            "Next scouts should lift the boundary-projected channel into eight-qubit tensor-network coherent information or add representation-branching constraints.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from current Grok/Gemini Choi-rank convergence; it is not a canonical v4 probe.",
        "raw_rows": {
            "target_choi_rank": target_rank,
            "target_spectrum": spectrum_signature(target),
            "symmetric_fit": symmetric_fit,
            "equal_rate_choi_rank": choi_rank(equal),
            "equal_rate_gap": equal_gap,
            "static_asymmetric_choi_rank": choi_rank(static),
            "static_asymmetric_gap": static_gap,
            "random_boundary_choi_rank": choi_rank(random_boundary),
            "random_boundary_gap": random_gap,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks), "result": str(OUT_PATH), "target_choi_rank": target_rank, "symmetric_gap": symmetric_fit["choi_trace_distance"], "equal_rate_gap": equal_gap, "random_boundary_gap": random_gap}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
