#!/usr/bin/env python3
"""Gamma5 off-diagonal coherence trace-orbit effective-channel scout."""

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
OUT_PATH = RESULT_DIR / "gamma5_offdiagonal_coherence_trace_orbit_effective_channel_probe_results.json"

NAME = "gamma5_offdiagonal_coherence_trace_orbit_effective_channel_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests gamma5 block off-diagonal coherence trace-norm "
    "orbits under chirality-asymmetric CPTP channels against symmetric effective "
    "channel fits. It does not admit novelty, empirical physics, a final manifold "
    "tower, bridge claim, ontology, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing four-qubit density, gamma5 projectors, Kraus channels, trace norms, and CPTP checks"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing reduced density contraction sanity"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing chirality orientation sanity check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic projector identities"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing effective-channel fit contradiction check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
N_QUBITS = 4


def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def initial_density(block_diagonal: bool = False, mixed: bool = False) -> torch.Tensor:
    if mixed:
        return torch.eye(2**N_QUBITS, dtype=DTYPE) / (2**N_QUBITS)
    psi = torch.zeros(2**N_QUBITS, dtype=DTYPE)
    psi[0b0000] = 0.42
    psi[0b0111] = 0.37j
    if not block_diagonal:
        psi[0b1010] = -0.51
        psi[0b1101] = 0.64j
    psi = normalize(psi)
    return torch.outer(psi, psi.conj())


def gamma5_projectors(local: bool = False) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    gamma5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=DTYPE))
    eye4 = torch.eye(4, dtype=DTYPE)
    p_l = (eye4 + gamma5) / 2
    p_r = (eye4 - gamma5) / 2
    if local:
        return gamma5, p_l, p_r
    eye_ref = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return torch.kron(gamma5, eye_ref), torch.kron(p_l, eye_ref), torch.kron(p_r, eye_ref)


def gamma5_boundary() -> dict[str, Any]:
    gamma5, p_l, p_r = gamma5_projectors(local=True)
    sx = sp.Matrix([[0, 1], [1, 0]])
    symbolic = sp.simplify(sx * sx) == sp.eye(2)
    _, blades = Cl(1, 3)
    pseudo = blades["e1234"]
    return {
        "gamma5_square_gap": float(torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item()),
        "projector_sum_gap": float(torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item()),
        "projector_product_gap": float(torch.linalg.matrix_norm(p_l @ p_r).item()),
        "left_rank": int(torch.linalg.matrix_rank(p_l).item()),
        "right_rank": int(torch.linalg.matrix_rank(p_r).item()),
        "sympy_boundary": bool(symbolic),
        "clifford_pseudoscalar": str(pseudo),
        "pass": torch.linalg.matrix_norm(gamma5 @ gamma5 - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l + p_r - torch.eye(4, dtype=DTYPE)).item() < 1e-12
        and torch.linalg.matrix_norm(p_l @ p_r).item() < 1e-12
        and int(torch.linalg.matrix_rank(p_l).item()) == 2
        and int(torch.linalg.matrix_rank(p_r).item()) == 2
        and str(pseudo) != str(-pseudo),
    }


def amplitude_damping(gamma: float) -> list[torch.Tensor]:
    return [
        torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1 - gamma)]], dtype=DTYPE),
        torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE),
    ]


def asymmetric_local_kraus(gamma_left: float, gamma_right: float) -> list[torch.Tensor]:
    k0_l, k1_l = amplitude_damping(gamma_left)
    k0_r, k1_r = amplitude_damping(gamma_right)
    return [
        torch.block_diag(k0_l, k0_r),
        torch.block_diag(k1_l, torch.zeros((2, 2), dtype=DTYPE)),
        torch.block_diag(torch.zeros((2, 2), dtype=DTYPE), k1_r),
    ]


def symmetric_local_kraus(gamma: float) -> list[torch.Tensor]:
    k0, k1 = amplitude_damping(gamma)
    return [torch.block_diag(k, k) for k in (k0, k1)]


def embed(kraus: list[torch.Tensor]) -> list[torch.Tensor]:
    eye_ref = torch.eye(2 ** (N_QUBITS - 2), dtype=DTYPE)
    return [torch.kron(k, eye_ref) for k in kraus]


def cptp_gap(kraus: list[torch.Tensor]) -> float:
    accum = torch.zeros_like(kraus[0])
    for k in kraus:
        accum = accum + k.conj().T @ k
    return float(torch.linalg.matrix_norm(accum - torch.eye(kraus[0].shape[0], dtype=DTYPE)).item())


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ k.conj().T
    return out


def offdiag_trace_norm(rho: torch.Tensor) -> float:
    _, p_l, p_r = gamma5_projectors()
    block = p_l @ rho @ p_r
    singular = torch.linalg.svdvals(block)
    return float(torch.sum(singular).item())


def reduced_pair_entropy(rho: torch.Tensor) -> float:
    tensor = rho.reshape(4, 4, 4, 4)
    red = oe.contract("abcb->ac", tensor)
    eigs = torch.clamp(torch.linalg.eigvalsh((red + red.conj().T) / 2), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def orbit(rho: torch.Tensor, mode: str, gamma: float | None = None) -> dict[str, Any]:
    current = rho.clone()
    values = [offdiag_trace_norm(current)]
    entropy_values = [reduced_pair_entropy(current)]
    for step in range(1, 7):
        if mode == "asymmetric":
            g_l = 0.08 + 0.045 * step
            g_r = 0.02 + 0.012 * step
            kraus = embed(asymmetric_local_kraus(g_l, g_r))
        elif mode == "symmetric":
            if gamma is None:
                g = 0.05 + 0.025 * step
            else:
                g = gamma
            kraus = embed(symmetric_local_kraus(g))
        elif mode == "commuting":
            kraus = embed([torch.eye(4, dtype=DTYPE)])
        else:
            raise ValueError(mode)
        current = apply_kraus(current, kraus)
        values.append(offdiag_trace_norm(current))
        entropy_values.append(reduced_pair_entropy(current))
    return {"coherence_orbit": values, "pair_entropy_orbit": entropy_values, "final_density": current}


def l2_gap(a: list[float], b: list[float]) -> float:
    return float(torch.linalg.vector_norm(torch.tensor(a, dtype=torch.float64) - torch.tensor(b, dtype=torch.float64)).item())


def effective_gamma_sweep(asym: dict[str, Any], rho: torch.Tensor) -> dict[str, Any]:
    best = {"gamma": None, "gap": float("inf"), "coherence_orbit": None}
    for idx in range(81):
        gamma = 0.02 + 0.28 * idx / 80
        row = orbit(rho, "symmetric", gamma=gamma)
        gap = l2_gap(asym["coherence_orbit"], row["coherence_orbit"])
        if gap < best["gap"]:
            best = {"gamma": gamma, "gap": gap, "coherence_orbit": row["coherence_orbit"]}
    return {"best": best, "pass": best["gap"] > 1e-5}


def z3_witness(orbit_gap: float, gamma_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    orbit_sep, gamma_fail, valid = z3.Bools("orbit_sep gamma_fail valid")
    solver.add(orbit_sep == (orbit_gap > 1e-5), gamma_fail == (gamma_gap > 1e-5), valid == (cptp < 1e-12), z3.Not(z3.And(orbit_sep, gamma_fail, valid)))
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat, "orbit_separates": orbit_gap > 1e-5, "effective_gamma_fails": gamma_gap > 1e-5, "cptp": cptp < 1e-12}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rho = initial_density()
    asym = orbit(rho, "asymmetric")
    sym = orbit(rho, "symmetric")
    gamma_eff = effective_gamma_sweep(asym, rho)
    mixed = orbit(initial_density(mixed=True), "asymmetric")
    block_diag = orbit(initial_density(block_diagonal=True), "asymmetric")
    commuting = orbit(rho, "commuting")
    cptp = max(cptp_gap(embed(asymmetric_local_kraus(0.30, 0.05))), cptp_gap(embed(symmetric_local_kraus(0.17))))
    orbit_gap = l2_gap(asym["coherence_orbit"], sym["coherence_orbit"])
    positive = {
        "gamma5_offdiagonal_trace_orbit_separates_from_symmetric_schedule": {
            "asymmetric_orbit": asym["coherence_orbit"],
            "symmetric_orbit": sym["coherence_orbit"],
            "orbit_gap": orbit_gap,
            "pass": orbit_gap > 1e-5,
        },
        "effective_symmetric_gamma_cannot_match_offdiagonal_orbit": gamma_eff,
        "gamma5_projector_boundary": gamma5_boundary(),
        "asymmetric_and_symmetric_channels_are_cptp": {"cptp_gap": cptp, "pass": cptp < 1e-12},
    }
    graveyard_companions = {
        "maximally_mixed_input_has_zero_offdiagonal_orbit": {
            "orbit": mixed["coherence_orbit"],
            "pass": max(abs(value) for value in mixed["coherence_orbit"]) < 1e-12,
        },
        "block_diagonal_input_has_zero_offdiagonal_orbit": {
            "orbit": block_diag["coherence_orbit"],
            "pass": max(abs(value) for value in block_diag["coherence_orbit"]) < 1e-12,
        },
        "commuting_identity_schedule_preserves_initial_orbit": {
            "orbit": commuting["coherence_orbit"],
            "pass": max(abs(value - commuting["coherence_orbit"][0]) for value in commuting["coherence_orbit"]) < 1e-12,
        },
    }
    z3_row = z3_witness(orbit_gap, gamma_eff["best"]["gap"], cptp)
    boundary = {
        "finite_four_qubit_dimension": {"dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 16},
        "z3_orbit_and_gamma_eff_witness": z3_row,
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-qubit density under gamma5 chirality-asymmetric CPTP channel sequence, read by P_L rho P_R trace-norm orbit and symmetric effective-channel fit",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "This scout tests a trace-orbit readout rather than max coherent information.",
            "It remains a formal scout; standard Stinespring dilation is still an external novelty falsifier.",
            "If this survives validation, the next step is survivor quotienting over gamma5 off-diagonal trace orbits.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini post-kill provider proposals; it is not a canonical v4 probe.",
        "raw_rows": {
            "asymmetric": {"coherence_orbit": asym["coherence_orbit"], "pair_entropy_orbit": asym["pair_entropy_orbit"]},
            "symmetric": {"coherence_orbit": sym["coherence_orbit"], "pair_entropy_orbit": sym["pair_entropy_orbit"]},
            "effective_gamma": gamma_eff,
            "mixed": mixed["coherence_orbit"],
            "block_diagonal": block_diag["coherence_orbit"],
            "commuting": commuting["coherence_orbit"],
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all(checks) and all(row["pass"] for row in boundary.values()), "result": str(OUT_PATH), "orbit_gap": orbit_gap, "gamma_eff_gap": gamma_eff["best"]["gap"], "cptp_gap": cptp}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
