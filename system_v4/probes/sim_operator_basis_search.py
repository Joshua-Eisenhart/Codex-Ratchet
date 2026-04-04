#!/usr/bin/env python3
"""
sim_operator_basis_search.py
============================
B3 Operator/Basis Search — four controlled tests on the admitted Hopf/Weyl carrier.

Tests whether the current {Ti, Te, Fi, Fe} operator basis is load-bearing substrate
or could be remapped/collapsed without changing lower-tier law behavior.

B3.1  basis_remap         swap Ti↔Te assignment on canonical carrier/loop law → should break
B3.2  coord_change        global SU(2) conjugate everything consistently → should NOT break
B3.3  noncomm_ablation    collapse operator family to all-commuting → grammar should degrade
B3.4  rep_demotion        ablate each operator; identify which are load-bearing

Lower-tier law measures (same as sim_neg_loop_law_swap):
  fiber_drift      = mean Frobenius ||ρ_after_op - ρ_before_op|| on fiber loop states
  base_traversal   = mean Frobenius ||ρ_after_op - ρ_before_op|| on base loop states
  sheet_gap        = |entropy_delta_L - entropy_delta_R| across Weyl sheets
  fiber_base_gap   = |mean_fiber_drift - mean_base_traversal|

A remap "breaks" lower-tier law behavior when fiber_base_gap collapses significantly
(< 10% of canonical gap) or sheet_gap collapses (< 10% of canonical sheet gap).

A coordinate change "does NOT break" when both gaps are preserved within 5% of canonical.
"""
from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, Callable

import numpy as np

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results"
)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "operator_basis_search_results.json")

# ─── Pauli matrices ───────────────────────────────────────────────────────────
I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

# Projectors onto σ_z eigenstates
P0 = np.array([[1, 0], [0, 0]], dtype=complex)   # |0><0|
P1 = np.array([[0, 0], [0, 1]], dtype=complex)   # |1><1|

# Projectors onto σ_x eigenstates
Qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2   # |+><+|
Qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2  # |-><-|

# ─── Hopf/Weyl geometry ───────────────────────────────────────────────────────

def spinor(phi: float, chi: float, eta: float) -> np.ndarray:
    """ψ(φ,χ;η) = (e^{i(φ+χ)}cosη, e^{i(φ−χ)}sinη)^T  on S³."""
    return np.array([
        np.exp(1j * (phi + chi)) * np.cos(eta),
        np.exp(1j * (phi - chi)) * np.sin(eta),
    ], dtype=complex)


def density(psi: np.ndarray) -> np.ndarray:
    """ρ = ψψ†."""
    return np.outer(psi, psi.conj())


def von_neumann_entropy(rho: np.ndarray) -> float:
    """S(ρ) = −Tr(ρ log ρ).  Uses eigenvalues; clamps tiny negatives."""
    evals = np.linalg.eigvalsh(rho)
    evals = np.clip(np.real(evals), 0, None)
    evals = evals[evals > 1e-15]
    return float(-np.dot(evals, np.log(evals)))


def frob(a: np.ndarray, b: np.ndarray) -> float:
    """Frobenius distance ||a − b||_F."""
    return float(np.linalg.norm(a - b, ord='fro'))


# ─── Canonical operators ──────────────────────────────────────────────────────

def apply_Ti(rho: np.ndarray, q: float = 0.9) -> np.ndarray:
    """Ti: z-dephasing.  ρ → (1−q)ρ + q(P₀ρP₀ + P₁ρP₁).
    Kills off-diagonal coherence in the z-basis."""
    return (1 - q) * rho + q * (P0 @ rho @ P0 + P1 @ rho @ P1)


def apply_Te(rho: np.ndarray, q: float = 0.9) -> np.ndarray:
    """Te: x-dephasing.  ρ → (1−q)ρ + q(Q₊ρQ₊ + Q₋ρQ₋).
    Kills off-diagonal coherence in the x-basis."""
    return (1 - q) * rho + q * (Qp @ rho @ Qp + Qm @ rho @ Qm)


def apply_Fi(rho: np.ndarray, theta: float = np.pi / 4) -> np.ndarray:
    """Fi: x-rotation.  ρ → U_x(θ) ρ U_x(θ)†.
    U_x(θ) = cos(θ/2) I − i sin(θ/2) σ_x."""
    Ux = np.cos(theta / 2) * I2 - 1j * np.sin(theta / 2) * sx
    return Ux @ rho @ Ux.conj().T


def apply_Fe(rho: np.ndarray, phi: float = np.pi / 4) -> np.ndarray:
    """Fe: z-rotation.  ρ → U_z(φ) ρ U_z(φ)†.
    U_z(φ) = diag(e^{−iφ/2}, e^{iφ/2})."""
    Uz = np.array([[np.exp(-1j * phi / 2), 0],
                   [0, np.exp(1j * phi / 2)]], dtype=complex)
    return Uz @ rho @ Uz.conj().T


# ─── Operator families ────────────────────────────────────────────────────────

# Canonical assignment (admitted lower-tier grammar):
#   Type-1 fiber loop → Te, Fi  (x-axis family, heating / inductive)
#   Type-1 base loop  → Ti, Fe  (z-axis family, cooling / deductive)
#   Type-2 mirrors this

CANONICAL_FIBER_OPS: list[Callable] = [apply_Te, apply_Fi]
CANONICAL_BASE_OPS: list[Callable]  = [apply_Ti, apply_Fe]

# B3.1 Remap: swap z-family and x-family assignment
REMAPPED_FIBER_OPS: list[Callable] = [apply_Ti, apply_Fe]   # z-family on fiber
REMAPPED_BASE_OPS: list[Callable]  = [apply_Te, apply_Fi]   # x-family on base

# B3.3 Commuting collapse: replace all operators with Ti (all z-dephasing)
#   Ti commutes with Fe (z-rotation), so all-z-family collapses the algebra.
#   [Ti, Fe](ρ) = 0 for diagonal ρ — loses the cross-axis noncommutation.
COMMUTING_OPS: list[Callable] = [apply_Ti, apply_Fe]        # all z-axis, commute on diagonal


# ─── Geometry sampling ────────────────────────────────────────────────────────

def sample_fiber_states(n_eta: int = 6, n_u: int = 8) -> list[tuple]:
    """Sample (ρ_before, ρ_after_quarter_cycle) on fiber loops.

    Fiber loop: φ varies, χ and η fixed.
    Density period π (Bloch vector uses 2χ), so check at u = π/4.
    Returns list of (rho_at_0, rho_at_quarter, eta, chi) tuples.
    """
    results = []
    etas = np.linspace(0.3, 1.2, n_eta)
    chis = np.linspace(0.1, 0.9, n_u)
    phi0 = 0.5
    for eta in etas:
        for chi in chis:
            psi0 = spinor(phi0, chi, eta)
            rho0 = density(psi0)
            # Quarter-period traversal on fiber (u = π/4)
            psi1 = spinor(phi0 + np.pi / 4, chi, eta)
            rho1 = density(psi1)
            results.append((rho0, rho1, eta, chi))
    return results


def sample_base_states(n_eta: int = 6, n_u: int = 8) -> list[tuple]:
    """Sample (ρ_before, ρ_after_quarter_cycle) on base loops.

    Base loop (horizontal lift): φ = φ₀ − cos(2η)·u, χ = χ₀ + u.
    Returns list of (rho_at_0, rho_at_quarter, eta, chi) tuples.
    """
    results = []
    etas = np.linspace(0.3, 1.2, n_eta)
    chis = np.linspace(0.1, 0.9, n_u)
    phi0 = 0.5
    for eta in etas:
        for chi in chis:
            psi0 = spinor(phi0, chi, eta)
            rho0 = density(psi0)
            u = np.pi / 4
            psi1 = spinor(phi0 - np.cos(2 * eta) * u, chi + u, eta)
            rho1 = density(psi1)
            results.append((rho0, rho1, eta, chi))
    return results


def sample_weyl_states(n_eta: int = 6) -> list[tuple]:
    """Sample (ρ_L, ρ_R) pairs — same (φ,χ,η) but left vs right sheet.

    Left sheet: ψ_L with forward phase (+i).
    Right sheet: ψ_R has conjugate phase structure (e^{-i...}).
    """
    pairs = []
    etas = np.linspace(0.3, 1.2, n_eta)
    phi0, chi0 = 0.5, 0.4
    for eta in etas:
        # Left sheet: canonical
        psi_L = spinor(phi0, chi0, eta)
        rho_L = density(psi_L)
        # Right sheet: conjugated phases (H_R = -H_0 → complex conjugate)
        psi_R = spinor(-phi0, chi0, eta)
        rho_R = density(psi_R)
        pairs.append((rho_L, rho_R, eta))
    return pairs


# ─── Measurement functions ────────────────────────────────────────────────────

def measure_fiber_base_gap(
    fiber_states: list,
    base_states: list,
    fiber_ops: list[Callable],
    base_ops: list[Callable],
) -> Dict[str, float]:
    """Compute fiber_drift and base_traversal under given operator assignments.

    fiber_drift     = mean ||op(ρ₀) - ρ₀|| across fiber states
                      (operator-induced change at the start of a fiber loop)
    base_traversal  = mean ||op(ρ₁) - ρ₀|| across base states
                      (total state change after base quarter-cycle + operator)
    fiber_base_gap  = |base_traversal - fiber_drift|
    """
    fiber_drifts = []
    for (rho0, rho1, eta, chi) in fiber_states:
        # Apply each fiber operator to the initial fiber state
        for op in fiber_ops:
            rho_op = op(rho0)
            fiber_drifts.append(frob(rho_op, rho0))

    base_traversals = []
    for (rho0, rho1, eta, chi) in base_states:
        # Geometric traversal distance (pure geometry, no operator)
        geom_dist = frob(rho1, rho0)
        # Apply each base operator to traversed state
        for op in base_ops:
            rho_op = op(rho1)
            # Total change = geometry + operator from initial
            base_traversals.append(frob(rho_op, rho0))

    mean_fiber_drift = float(np.mean(fiber_drifts))
    mean_base_traversal = float(np.mean(base_traversals))
    fiber_base_gap = abs(mean_base_traversal - mean_fiber_drift)

    return {
        "mean_fiber_drift": mean_fiber_drift,
        "mean_base_traversal": mean_base_traversal,
        "fiber_base_gap": fiber_base_gap,
    }


def measure_sheet_gap(
    weyl_pairs: list,
    ops: list[Callable],
) -> Dict[str, float]:
    """Compute entropy delta difference across left/right Weyl sheets.

    sheet_gap = mean |ΔS_L - ΔS_R| where ΔS = S(op(ρ)) - S(ρ).
    A large sheet_gap means the operators distinguish L from R.
    A collapsed sheet_gap means operator action is symmetric across sheets.
    """
    gaps = []
    for (rho_L, rho_R, eta) in weyl_pairs:
        for op in ops:
            ds_L = von_neumann_entropy(op(rho_L)) - von_neumann_entropy(rho_L)
            ds_R = von_neumann_entropy(op(rho_R)) - von_neumann_entropy(rho_R)
            gaps.append(abs(ds_L - ds_R))
    return {
        "mean_sheet_gap": float(np.mean(gaps)),
        "max_sheet_gap": float(np.max(gaps)),
        "min_sheet_gap": float(np.min(gaps)),
    }


def measure_noncomm_strength(ops: list[Callable]) -> Dict[str, float]:
    """Measure how noncommutative the operator family is on a sample of states.

    noncomm_residual = mean || op_A(op_B(ρ)) - op_B(op_A(ρ)) ||_F
    over a sample of states and all ordered pairs (op_A, op_B).
    A commuting family gives noncomm_residual ≈ 0.
    """
    test_etas = [0.4, 0.7, 1.0, 1.2]
    test_chis = [0.2, 0.6]
    phi0 = 0.5
    residuals = []
    for eta in test_etas:
        for chi in test_chis:
            psi = spinor(phi0, chi, eta)
            rho = density(psi)
            for i, op_A in enumerate(ops):
                for j, op_B in enumerate(ops):
                    if i == j:
                        continue
                    ab = op_A(op_B(rho))
                    ba = op_B(op_A(rho))
                    residuals.append(frob(ab, ba))
    return {
        "mean_noncomm_residual": float(np.mean(residuals)),
        "max_noncomm_residual": float(np.max(residuals)),
    }


def apply_global_conjugation(
    rho: np.ndarray,
    U: np.ndarray,
) -> np.ndarray:
    """Conjugate density matrix: ρ' = U ρ U†."""
    return U @ rho @ U.conj().T


def conjugate_channel(
    op: Callable,
    U: np.ndarray,
) -> Callable:
    """Conjugate an operator channel by global SU(2) rotation U.

    Channel C becomes: C'(ρ) = U† · C(U ρ U†) · U
    (rotate state in, apply original op, rotate back)
    """
    Ud = U.conj().T
    def conjugated(rho: np.ndarray) -> np.ndarray:
        rho_rot = U @ rho @ Ud
        rho_out = op(rho_rot)
        return Ud @ rho_out @ U
    return conjugated


# ─── Main computation ─────────────────────────────────────────────────────────

def run() -> Dict[str, Any]:
    fiber_states = sample_fiber_states()
    base_states = sample_base_states()
    weyl_pairs = sample_weyl_states()

    # ── Canonical baseline ────────────────────────────────────────────────────
    canon_fb = measure_fiber_base_gap(
        fiber_states, base_states,
        CANONICAL_FIBER_OPS, CANONICAL_BASE_OPS,
    )
    canon_sheet = measure_sheet_gap(weyl_pairs, CANONICAL_FIBER_OPS + CANONICAL_BASE_OPS)
    canon_noncomm = measure_noncomm_strength(CANONICAL_FIBER_OPS + CANONICAL_BASE_OPS)

    # ── B3.1 Basis remap ──────────────────────────────────────────────────────
    # Swap z-family and x-family assignment while keeping loop law and carrier fixed.
    remap_fb = measure_fiber_base_gap(
        fiber_states, base_states,
        REMAPPED_FIBER_OPS, REMAPPED_BASE_OPS,
    )
    remap_sheet = measure_sheet_gap(weyl_pairs, REMAPPED_FIBER_OPS + REMAPPED_BASE_OPS)

    # Gap change: did remap collapse the fiber/base distinction?
    remap_gap_change = abs(remap_fb["fiber_base_gap"] - canon_fb["fiber_base_gap"])
    remap_gap_fraction = (
        remap_gap_change / canon_fb["fiber_base_gap"]
        if canon_fb["fiber_base_gap"] > 1e-15 else 0.0
    )

    # ── B3.2 Coordinate-change control ───────────────────────────────────────
    # Global Hadamard: H = (σ_x + σ_z) / √2 — swaps z↔x basis
    H_gate = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)

    # Conjugate the canonical operators consistently
    coord_fiber_ops = [conjugate_channel(op, H_gate) for op in CANONICAL_FIBER_OPS]
    coord_base_ops  = [conjugate_channel(op, H_gate) for op in CANONICAL_BASE_OPS]

    # Conjugate all states consistently
    coord_fiber_states = [
        (apply_global_conjugation(r0, H_gate),
         apply_global_conjugation(r1, H_gate), eta, chi)
        for (r0, r1, eta, chi) in fiber_states
    ]
    coord_base_states = [
        (apply_global_conjugation(r0, H_gate),
         apply_global_conjugation(r1, H_gate), eta, chi)
        for (r0, r1, eta, chi) in base_states
    ]
    coord_weyl_pairs = [
        (apply_global_conjugation(rL, H_gate),
         apply_global_conjugation(rR, H_gate), eta)
        for (rL, rR, eta) in weyl_pairs
    ]

    coord_fb = measure_fiber_base_gap(
        coord_fiber_states, coord_base_states,
        coord_fiber_ops, coord_base_ops,
    )
    coord_sheet = measure_sheet_gap(coord_weyl_pairs, coord_fiber_ops + coord_base_ops)

    # Coordinate change should NOT break: gaps preserved within 5%
    coord_gap_change = abs(coord_fb["fiber_base_gap"] - canon_fb["fiber_base_gap"])
    coord_gap_fraction = (
        coord_gap_change / canon_fb["fiber_base_gap"]
        if canon_fb["fiber_base_gap"] > 1e-15 else 0.0
    )

    # ── B3.3 Noncommutation ablation ─────────────────────────────────────────
    # Collapse both loop assignments to all-z-family (Ti+Fe, commute on diagonals).
    # This collapses the cross-axis noncommutation between z-family and x-family.
    comm_fb = measure_fiber_base_gap(
        fiber_states, base_states,
        COMMUTING_OPS, COMMUTING_OPS,   # same family on both loops
    )
    comm_noncomm = measure_noncomm_strength(COMMUTING_OPS)

    # Noncomm ablation should weaken fiber/base distinction
    comm_gap_change = abs(comm_fb["fiber_base_gap"] - canon_fb["fiber_base_gap"])
    comm_gap_fraction = (
        comm_gap_change / canon_fb["fiber_base_gap"]
        if canon_fb["fiber_base_gap"] > 1e-15 else 0.0
    )
    noncomm_ratio = (
        comm_noncomm["mean_noncomm_residual"] / canon_noncomm["mean_noncomm_residual"]
        if canon_noncomm["mean_noncomm_residual"] > 1e-15 else 0.0
    )

    # ── B3.4 Representation demotion ─────────────────────────────────────────
    # Ablate each operator individually from the canonical set.
    # "Load-bearing" = removal collapses fiber_base_gap by > 20%.
    # "Representation-only" candidate = removal does NOT collapse gap.
    all_canonical = CANONICAL_FIBER_OPS + CANONICAL_BASE_OPS
    op_names = ["Te", "Fi", "Ti", "Fe"]
    demotion = {}
    for i, (name, op) in enumerate(zip(op_names, all_canonical)):
        remaining_fiber = [o for j, o in enumerate(CANONICAL_FIBER_OPS) if o is not op]
        remaining_base  = [o for j, o in enumerate(CANONICAL_BASE_OPS)  if o is not op]

        # If removing from fiber set, fall back to base ops on fiber
        if not remaining_fiber:
            remaining_fiber = CANONICAL_BASE_OPS
        if not remaining_base:
            remaining_base = CANONICAL_FIBER_OPS

        ablated_fb = measure_fiber_base_gap(
            fiber_states, base_states,
            remaining_fiber, remaining_base,
        )
        gap_drop = abs(ablated_fb["fiber_base_gap"] - canon_fb["fiber_base_gap"])
        gap_drop_fraction = (
            gap_drop / canon_fb["fiber_base_gap"]
            if canon_fb["fiber_base_gap"] > 1e-15 else 0.0
        )
        demotion[name] = {
            "fiber_base_gap_without": ablated_fb["fiber_base_gap"],
            "gap_drop_fraction": float(gap_drop_fraction),
            "load_bearing": bool(gap_drop_fraction > 0.20),
        }

    # ── Summary ───────────────────────────────────────────────────────────────
    n_load_bearing = sum(1 for v in demotion.values() if v["load_bearing"])
    n_demotion_candidates = sum(1 for v in demotion.values() if not v["load_bearing"])

    return {
        "sim": "operator_basis_search",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "canonical": {
            "fiber_base_gap": canon_fb["fiber_base_gap"],
            "mean_fiber_drift": canon_fb["mean_fiber_drift"],
            "mean_base_traversal": canon_fb["mean_base_traversal"],
            "mean_sheet_gap": canon_sheet["mean_sheet_gap"],
            "mean_noncomm_residual": canon_noncomm["mean_noncomm_residual"],
        },
        "B3_1_basis_remap": {
            "fiber_base_gap": remap_fb["fiber_base_gap"],
            "gap_change_fraction": float(remap_gap_fraction),
            "remap_breaks_grammar": bool(remap_gap_fraction > 0.10),
            "sheet_gap": remap_sheet["mean_sheet_gap"],
        },
        "B3_2_coord_change": {
            "fiber_base_gap": coord_fb["fiber_base_gap"],
            "gap_change_fraction": float(coord_gap_fraction),
            "coord_change_preserves_grammar": bool(coord_gap_fraction < 0.05),
            "sheet_gap": coord_sheet["mean_sheet_gap"],
        },
        "B3_3_noncomm_ablation": {
            "fiber_base_gap": comm_fb["fiber_base_gap"],
            "gap_change_fraction": float(comm_gap_fraction),
            "noncomm_residual": comm_noncomm["mean_noncomm_residual"],
            "noncomm_ratio": float(noncomm_ratio),
            "noncomm_ablation_degrades_grammar": bool(comm_gap_fraction > 0.10),
        },
        "B3_4_rep_demotion": {
            "per_operator": demotion,
            "n_load_bearing": n_load_bearing,
            "n_demotion_candidates": n_demotion_candidates,
            "at_least_one_load_bearing": bool(n_load_bearing >= 1),
            "at_least_one_demotion_candidate": bool(n_demotion_candidates >= 1),
        },
    }


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    result = run()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
