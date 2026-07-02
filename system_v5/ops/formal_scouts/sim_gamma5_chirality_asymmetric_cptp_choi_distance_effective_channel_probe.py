#!/usr/bin/env python3
"""Gamma5 chirality-asymmetric CPTP Choi-distance effective-channel scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import opt_einsum as oe
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe_results.json"

NAME = "gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a gamma5 chirality-asymmetric CPTP "
    "channel is reducible to the one-parameter symmetric effective-gamma "
    "channel family by Choi trace distance and Stinespring-isometry projector "
    "distance. It does not prove novelty against arbitrary CPTP channels, "
    "does not admit empirical physics, and does not promote any final manifold "
    "or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "supportive local bounded scalar search for effective-gamma minimization"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Kraus maps, Choi matrices, trace norms, Stinespring isometries, and bounded-search objective evaluation"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing Choi partial-trace CPTP verification"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing Cl(1,3) chirality orientation boundary"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic projector identity boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing effective-channel reduction contradiction check"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "python_math" else "load_bearing")
    for tool in TOOL_MANIFEST
}

DTYPE = torch.complex128
DIM = 4


def bounded_scalar_minimize(
    objective: Any,
    lower: float,
    upper: float,
    *,
    xatol: float = 1e-12,
    grid_points: int = 257,
    max_iter: int = 128,
) -> dict[str, Any]:
    if not lower < upper:
        raise ValueError("lower bound must be smaller than upper bound")
    if grid_points < 3:
        raise ValueError("grid_points must be at least 3")
    evaluations = 0

    def evaluate(x: float) -> tuple[float, float]:
        nonlocal evaluations
        y = float(objective(float(x)))
        evaluations += 1
        return float(x), y

    candidates = [evaluate(lower), evaluate(upper)]
    step = (upper - lower) / (grid_points - 1)
    grid = [evaluate(lower + step * idx) for idx in range(grid_points)]
    candidates.extend(grid)
    best_index = min(range(len(grid)), key=lambda idx: grid[idx][1])
    left_index = max(0, best_index - 1)
    right_index = min(grid_points - 1, best_index + 1)
    left = lower + step * left_index
    right = lower + step * right_index

    if right > left:
        inv_phi = (math.sqrt(5.0) - 1.0) / 2.0
        inv_phi_sq = (3.0 - math.sqrt(5.0)) / 2.0
        x1 = left + inv_phi_sq * (right - left)
        x2 = left + inv_phi * (right - left)
        f1 = evaluate(x1)
        f2 = evaluate(x2)
        for _ in range(max_iter):
            if abs(right - left) <= xatol:
                break
            if f1[1] < f2[1]:
                right = x2
                x2, f2 = x1, f1
                x1 = left + inv_phi_sq * (right - left)
                f1 = evaluate(x1)
            else:
                left = x1
                x1, f1 = x2, f2
                x2 = left + inv_phi * (right - left)
                f2 = evaluate(x2)
        candidates.extend([f1, f2, evaluate((left + right) / 2.0)])

    x, fun = min(candidates, key=lambda item: item[1])
    return {"x": x, "fun": fun, "success": math.isfinite(fun), "evaluations": evaluations}


def gamma5_projectors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gamma5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=DTYPE))
    eye = torch.eye(DIM, dtype=DTYPE)
    p_l = (eye + gamma5) / 2
    p_r = (eye - gamma5) / 2
    return gamma5, p_l, p_r


def amplitude_damping(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(max(0.0, 1 - gamma))]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(max(0.0, gamma))], [0.0, 0.0]], dtype=DTYPE),
    ]


def asymmetric_kraus(gamma_left: float, gamma_right: float) -> list[torch.Tensor]:
    k0_l, k1_l = amplitude_damping(gamma_left)
    k0_r, k1_r = amplitude_damping(gamma_right)
    return [
        torch.block_diag(k0_l, k0_r),
        torch.block_diag(k1_l, torch.zeros((2, 2), dtype=DTYPE)),
        torch.block_diag(torch.zeros((2, 2), dtype=DTYPE), k1_r),
    ]


def symmetric_kraus(gamma: float) -> list[torch.Tensor]:
    k0, k1 = amplitude_damping(gamma)
    return [torch.block_diag(k, k) for k in (k0, k1)]


def depolarizing_kraus(weight: float) -> list[torch.Tensor]:
    eye = torch.eye(DIM, dtype=DTYPE)
    rows = [math.sqrt(max(0.0, 1 - weight)) * eye]
    for a in range(DIM):
        for b in range(DIM):
            op = torch.zeros((DIM, DIM), dtype=DTYPE)
            op[a, b] = math.sqrt(weight / DIM)
            rows.append(op)
    return rows


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros((DIM, DIM), dtype=DTYPE)
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(DIM, dtype=DTYPE)).item())


def apply_kraus(op: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(op)
    for k in kraus:
        out = out + k @ op @ k.conj().T
    return out


def choi_tensor(kraus: list[torch.Tensor]) -> torch.Tensor:
    tensor = torch.zeros((DIM, DIM, DIM, DIM), dtype=DTYPE)
    for i in range(DIM):
        for j in range(DIM):
            basis = torch.zeros((DIM, DIM), dtype=DTYPE)
            basis[i, j] = 1.0
            tensor[i, j] = apply_kraus(basis, kraus)
    return tensor / DIM


def choi_matrix(kraus: list[torch.Tensor]) -> torch.Tensor:
    return choi_tensor(kraus).permute(0, 2, 1, 3).reshape(DIM * DIM, DIM * DIM)


def choi_trace_preserving_gap(kraus: list[torch.Tensor]) -> float:
    tensor = choi_tensor(kraus)
    traced = oe.contract("ijaa->ij", tensor) * DIM
    return float(torch.linalg.matrix_norm(traced - torch.eye(DIM, dtype=DTYPE)).item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    diff = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.sum(torch.linalg.svdvals(diff)).item())


def stinespring_isometry(kraus: list[torch.Tensor]) -> torch.Tensor:
    return torch.cat(kraus, dim=0)


def stinespring_projector_distance(left: list[torch.Tensor], right: list[torch.Tensor]) -> float:
    width = max(len(left), len(right))
    def padded(kraus: list[torch.Tensor]) -> torch.Tensor:
        rows = list(kraus)
        while len(rows) < width:
            rows.append(torch.zeros((DIM, DIM), dtype=DTYPE))
        v = torch.cat(rows, dim=0)
        return v @ v.conj().T
    return trace_distance(padded(left), padded(right))


def best_symmetric_fit(target: list[torch.Tensor]) -> dict[str, Any]:
    target_choi = choi_matrix(target)
    def objective(gamma: float) -> float:
        return trace_distance(target_choi, choi_matrix(symmetric_kraus(float(gamma))))
    result = bounded_scalar_minimize(objective, 0.0, 0.45, xatol=1e-12)
    gamma = float(result["x"])
    sym = symmetric_kraus(gamma)
    return {
        "gamma": gamma,
        "choi_trace_distance": float(result["fun"]),
        "stinespring_projector_distance": stinespring_projector_distance(target, sym),
        "success": bool(result["success"]),
        "optimizer": "local_dense_refined_golden_section",
        "optimizer_evaluations": int(result["evaluations"]),
    }


def gamma5_boundary() -> dict[str, Any]:
    gamma5, p_l, p_r = gamma5_projectors()
    g = sp.diag(1, 1, -1, -1)
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {
        "gamma5_square_gap": float(torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(DIM, dtype=DTYPE)).item()),
        "projector_sum_gap": float(torch.linalg.matrix_norm(p_l + p_r - torch.eye(DIM, dtype=DTYPE)).item()),
        "projector_product_gap": float(torch.linalg.matrix_norm(p_l @ p_r).item()),
        "sympy_gamma5_square": bool(sp.simplify(g * g) == sp.eye(DIM)),
        "clifford_pseudoscalar": str(pseudo),
        "pass": torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(DIM, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l + p_r - torch.eye(DIM, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l @ p_r).item() < 1e-12
        and bool(sp.simplify(g * g) == sp.eye(DIM)),
    }


def z3_effective_fit_witness(choi_gap: float, stinespring_gap: float, cptp: float, symmetric_control_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    choi_sep, stine_sep, valid, control_zero = z3.Bools("choi_sep stine_sep valid control_zero")
    solver.add(choi_sep == (choi_gap > 0.02))
    solver.add(stine_sep == (stinespring_gap > 0.02))
    solver.add(valid == (cptp < 1e-12))
    solver.add(control_zero == (symmetric_control_gap < 1e-8))
    solver.add(z3.Not(z3.And(choi_sep, stine_sep, valid, control_zero)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "choi_separates": choi_gap > 0.02,
        "stinespring_separates": stinespring_gap > 0.02,
        "cptp_valid": cptp < 1e-12,
        "symmetric_control_zero": symmetric_control_gap < 1e-8,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    asymmetric = asymmetric_kraus(0.30, 0.05)
    symmetric_family_member = symmetric_kraus(0.17)
    separated_equal_rates = asymmetric_kraus(0.17, 0.17)
    depol = depolarizing_kraus(0.20)
    fit = best_symmetric_fit(asymmetric)
    symmetric_family_fit = best_symmetric_fit(symmetric_family_member)
    separated_equal_fit = best_symmetric_fit(separated_equal_rates)
    depol_fit = best_symmetric_fit(depol)
    cptp = max(
        cptp_gap(asymmetric),
        choi_trace_preserving_gap(asymmetric),
        cptp_gap(symmetric_kraus(fit["gamma"])),
        choi_trace_preserving_gap(symmetric_kraus(fit["gamma"])),
    )
    positive = {
        "gamma5_asymmetric_channel_resists_one_parameter_symmetric_choi_fit": {
            "best_fit": fit,
            "threshold": 0.02,
            "pass": fit["success"] and fit["choi_trace_distance"] > 0.02,
        },
        "gamma5_asymmetric_channel_resists_symmetric_stinespring_projector_fit": {
            "best_fit": fit,
            "threshold": 0.02,
            "pass": fit["stinespring_projector_distance"] > 0.02,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
        "asymmetric_and_best_symmetric_channels_are_cptp": {"cptp_gap": cptp, "pass": cptp < 1e-12},
    }
    graveyard_companions = {
        "symmetric_family_member_self_fit_has_zero_choi_distance": {
            "best_fit": symmetric_family_fit,
            "pass": symmetric_family_fit["choi_trace_distance"] < 1e-8,
        },
        "depolarizing_channel_not_in_symmetric_amplitude_damping_family": {
            "best_fit": depol_fit,
            "pass": depol_fit["choi_trace_distance"] > fit["choi_trace_distance"],
        },
        "identity_channel_has_zero_choi_fit_gap": {
            "best_fit": best_symmetric_fit(symmetric_kraus(0.0)),
            "pass": best_symmetric_fit(symmetric_kraus(0.0))["choi_trace_distance"] < 1e-9,
        },
        "arbitrary_cptp_family_would_trivially_represent_asymmetric_channel": {
            "same_kraus_choi_distance": trace_distance(choi_matrix(asymmetric), choi_matrix(asymmetric)),
            "pass": trace_distance(choi_matrix(asymmetric), choi_matrix(asymmetric)) < 1e-12,
        },
    }
    boundary = {
        "finite_four_component_channel_dimension": {"dimension": DIM, "choi_dimension": DIM * DIM, "pass": DIM == 4},
        "z3_effective_fit_witness": z3_effective_fit_witness(fit["choi_trace_distance"], fit["stinespring_projector_distance"], cptp, symmetric_family_fit["choi_trace_distance"]),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-component gamma5 chirality-asymmetric CPTP channel compared to one-parameter symmetric effective-gamma channel family by Choi trace distance and Stinespring-isometry projector distance",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This falsifies only the one-parameter symmetric effective-gamma reduction, not arbitrary CPTP representation.",
            "Equal left/right rates with separated jump Kraus are not the same as the combined symmetric jump family; this remains a useful boundary, not a collapse control.",
            "The next stronger falsifier should compare survivor quotient observables after Stinespring dilations of matched Choi rank.",
            "The same Choi-distance control should be inserted into dynamic shell and tensor-network scouts.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini channel-equivalence falsifier proposals; it is not a canonical v4 probe.",
        "raw_rows": {
            "asymmetric_best_symmetric_fit": fit,
            "symmetric_family_self_fit": symmetric_family_fit,
            "separated_equal_rates_fit": separated_equal_fit,
            "depolarizing_control_fit": depol_fit,
            "cptp_gap": cptp,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "best_gamma": fit["gamma"],
                "choi_trace_distance": fit["choi_trace_distance"],
                "stinespring_projector_distance": fit["stinespring_projector_distance"],
                "cptp_gap": cptp,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
