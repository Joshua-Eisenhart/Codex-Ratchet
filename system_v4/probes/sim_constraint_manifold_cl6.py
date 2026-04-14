#!/usr/bin/env python3
"""
sim_constraint_manifold_cl6.py
==============================
Constraint manifold exploration (layers 7-12) through the REAL Cl(6)
geometric engine (PureCliffordEngine) vs. the old matrix engine
(GeometricEngine).

Key question: does the allowed-space landscape change when geometry is real?

Tests:
  L7  -- ordering sensitivity: canonical vs reversed stage order
  L9  -- strength Goldilocks zone: does Berry phase show it too?
  L11 -- eta sweep: does real geometry shift the optimal eta?

Output: a2_state/sim_results/constraint_manifold_cl6_results.json
"""

import sys
import os
import json
import math
import copy
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_pure_clifford import (
    PureCliffordEngine, PureCliffordState,
    derive_rho_AB, concurrence_from_rho,
    get_bloch_L, get_bloch_R, get_correlation_matrix,
    berry_increment, berry_increment_subsystem,
    _scalar6, _L_basis, _R_basis, _layout6,
)
from engine_core import (
    GeometricEngine, EngineState, StageControls,
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER,
)
from hopf_manifold import (
    torus_coordinates, left_weyl_spinor, right_weyl_spinor,
    density_to_bloch, von_neumann_entropy_2x2,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from geometric_operators import partial_trace_A, partial_trace_B


# =====================================================================
# Helpers
# =====================================================================

def _von_neumann_4x4(rho):
    """Von Neumann entropy of a 4x4 density matrix in bits."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def _concurrence_4x4(rho):
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = rho @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))


def _purity_from_bloch(mv):
    """Purity proxy from Bloch vector norms (L and R)."""
    bL = get_bloch_L(mv)
    bR = get_bloch_R(mv)
    return float((np.linalg.norm(bL) + np.linalg.norm(bR)) / 2.0)


def _sanitize(obj):
    """Recursively convert numpy types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, complex):
        return float(obj.real)
    return obj


# =====================================================================
# L7: ORDERING SENSITIVITY
# =====================================================================

def run_cl6_with_order(engine_type, stage_order, n_cycles, eta=TORUS_CLIFFORD):
    """Run PureCliffordEngine with a specific stage order for n_cycles."""
    eng = PureCliffordEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    total_berry_L = 0.0
    total_berry_R = 0.0

    for cycle in range(n_cycles):
        for pos, ti in enumerate(stage_order):
            state = eng.run_stage(state, ti, pos)
        total_berry_L = state.berry_L
        total_berry_R = state.berry_R

    # Extract final metrics
    rho = derive_rho_AB(state.mv_joint)
    conc = concurrence_from_rho(rho)
    ent = _von_neumann_4x4(rho)

    return {
        "berry_L": float(total_berry_L),
        "berry_R": float(total_berry_R),
        "berry_total": float(total_berry_L + total_berry_R),
        "concurrence": float(conc),
        "entropy": float(ent),
        "purity": _purity_from_bloch(state.mv_joint),
    }


def run_old_with_order(engine_type, stage_order, n_cycles, eta=TORUS_CLIFFORD):
    """Run old GeometricEngine with a specific stage order for n_cycles."""
    eng = GeometricEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    for cycle in range(n_cycles):
        for pos, ti in enumerate(stage_order):
            state = eng.step(state, stage_idx=ti)

    conc = _concurrence_4x4(state.rho_AB)
    ent = _von_neumann_4x4(state.rho_AB)

    return {
        "concurrence": float(conc),
        "entropy": float(ent),
    }


def test_L7_ordering(n_cycles=5):
    """L7: does ordering change Berry phase in Cl(6)?"""
    print("\n=== L7: ORDERING SENSITIVITY ===")

    canonical = LOOP_STAGE_ORDER[1]
    reversed_order = list(reversed(canonical))

    cl6_can = run_cl6_with_order(1, canonical, n_cycles)
    cl6_rev = run_cl6_with_order(1, reversed_order, n_cycles)
    old_can = run_old_with_order(1, canonical, n_cycles)
    old_rev = run_old_with_order(1, reversed_order, n_cycles)

    berry_diff = abs(cl6_can["berry_total"] - cl6_rev["berry_total"])
    conc_diff_cl6 = abs(cl6_can["concurrence"] - cl6_rev["concurrence"])
    conc_diff_old = abs(old_can["concurrence"] - old_rev["concurrence"])

    # Berry reveals new structure if ordering changes Berry phase significantly
    berry_reveals = berry_diff > 0.01

    print(f"  Cl(6) canonical: Berry={cl6_can['berry_total']:.4f}, C={cl6_can['concurrence']:.4f}")
    print(f"  Cl(6) reversed:  Berry={cl6_rev['berry_total']:.4f}, C={cl6_rev['concurrence']:.4f}")
    print(f"  Old canonical:   C={old_can['concurrence']:.4f}, S={old_can['entropy']:.4f}")
    print(f"  Old reversed:    C={old_rev['concurrence']:.4f}, S={old_rev['entropy']:.4f}")
    print(f"  Berry diff: {berry_diff:.6f}  (reveals new structure: {berry_reveals})")
    print(f"  Concurrence diff Cl(6): {conc_diff_cl6:.6f}")
    print(f"  Concurrence diff Old:   {conc_diff_old:.6f}")

    return {
        "cl6_canonical": cl6_can,
        "cl6_reversed": cl6_rev,
        "old_canonical": old_can,
        "old_reversed": old_rev,
        "berry_diff": float(berry_diff),
        "concurrence_diff_cl6": float(conc_diff_cl6),
        "concurrence_diff_old": float(conc_diff_old),
        "berry_reveals_new_structure": bool(berry_reveals),
    }


# =====================================================================
# L9: STRENGTH GOLDILOCKS
# =====================================================================

def run_cl6_with_strength(engine_type, strength_scale, n_cycles, eta=TORUS_CLIFFORD):
    """Run Cl(6) engine with operator strengths scaled by strength_scale."""
    eng = PureCliffordEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    # We need to modify the engine's strength computation.
    # Monkey-patch _operator_strength to scale by strength_scale.
    original_strength = eng._operator_strength

    def scaled_strength(terrain, op_name):
        base = original_strength(terrain, op_name)
        return float(np.clip(base * strength_scale / 0.5, 0.0, 1.0))

    eng._operator_strength = scaled_strength

    for cycle in range(n_cycles):
        state = eng.run_cycle(state)

    rho = derive_rho_AB(state.mv_joint)
    conc = concurrence_from_rho(rho)
    ent = _von_neumann_4x4(rho)

    return {
        "berry_L": float(state.berry_L),
        "berry_R": float(state.berry_R),
        "berry_total": float(state.berry_L + state.berry_R),
        "concurrence": float(conc),
        "entropy": float(ent),
        "purity": _purity_from_bloch(state.mv_joint),
    }


def run_old_with_strength(engine_type, strength_val, n_cycles, eta=TORUS_CLIFFORD):
    """Run old engine with a specific piston strength."""
    eng = GeometricEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    controls = {i: StageControls(piston=strength_val) for i in range(8)}
    for cycle in range(n_cycles):
        state = eng.run_cycle(state, controls=controls)

    conc = _concurrence_4x4(state.rho_AB)
    ent = _von_neumann_4x4(state.rho_AB)

    return {
        "concurrence": float(conc),
        "entropy": float(ent),
    }


def test_L9_strength(n_cycles=5):
    """L9: does the Goldilocks zone appear in Berry phase?"""
    print("\n=== L9: STRENGTH GOLDILOCKS ===")

    strengths = [0.0, 0.25, 0.5, 0.75, 1.0]

    cl6_berry = []
    cl6_conc = []
    cl6_purity = []
    old_conc = []
    old_ent = []

    for s in strengths:
        # For strength=0, Cl(6) engine won't move at all
        if s < 0.001:
            cl6_berry.append(0.0)
            cl6_conc.append(0.0)
            cl6_purity.append(1.0)
            old_conc.append(0.0)
            old_ent.append(0.0)
            continue

        cl6_res = run_cl6_with_strength(1, s, n_cycles)
        old_res = run_old_with_strength(1, s, n_cycles)

        cl6_berry.append(cl6_res["berry_total"])
        cl6_conc.append(cl6_res["concurrence"])
        cl6_purity.append(cl6_res["purity"])
        old_conc.append(old_res["concurrence"])
        old_ent.append(old_res["entropy"])

        print(f"  s={s:.2f}: Cl6 Berry={cl6_res['berry_total']:.4f} C={cl6_res['concurrence']:.4f} "
              f"P={cl6_res['purity']:.4f} | Old C={old_res['concurrence']:.4f} S={old_res['entropy']:.4f}")

    # Check if Berry phase shows a Goldilocks pattern (peak at intermediate strength)
    # Goldilocks = max is not at an endpoint
    if len(cl6_berry) >= 3:
        max_idx = int(np.argmax(cl6_berry))
        goldilocks_in_berry = 0 < max_idx < len(cl6_berry) - 1
    else:
        goldilocks_in_berry = False

    print(f"  Goldilocks in Berry: {goldilocks_in_berry} (peak at s={strengths[int(np.argmax(cl6_berry))]})")

    return {
        "cl6": {
            "strengths": strengths,
            "berry": cl6_berry,
            "concurrence": cl6_conc,
            "purity": cl6_purity,
        },
        "old": {
            "strengths": strengths,
            "concurrence": old_conc,
            "entropy": old_ent,
        },
        "goldilocks_in_berry": bool(goldilocks_in_berry),
    }


# =====================================================================
# L11: ETA SWEEP
# =====================================================================

def run_cl6_at_eta(engine_type, eta, n_cycles):
    """Run Cl(6) engine initialized at a specific eta for n_cycles."""
    eng = PureCliffordEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    for cycle in range(n_cycles):
        state = eng.run_cycle(state)

    rho = derive_rho_AB(state.mv_joint)
    conc = concurrence_from_rho(rho)
    ent = _von_neumann_4x4(rho)

    return {
        "berry_L": float(state.berry_L),
        "berry_R": float(state.berry_R),
        "berry_total": float(state.berry_L + state.berry_R),
        "concurrence": float(conc),
        "entropy": float(ent),
    }


def run_old_at_eta(engine_type, eta, n_cycles):
    """Run old engine initialized at a specific eta for n_cycles."""
    eng = GeometricEngine(engine_type=engine_type)
    state = eng.init_state(eta=eta)

    for cycle in range(n_cycles):
        state = eng.run_cycle(state)

    conc = _concurrence_4x4(state.rho_AB)
    ent = _von_neumann_4x4(state.rho_AB)

    return {
        "concurrence": float(conc),
        "entropy": float(ent),
    }


def test_L11_eta(n_cycles=5):
    """L11: does real geometry shift the optimal eta?"""
    print("\n=== L11: ETA SWEEP ===")

    etas = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]

    cl6_berry = []
    cl6_conc = []
    cl6_ent = []
    old_conc = []
    old_ent = []

    for eta in etas:
        cl6_res = run_cl6_at_eta(1, eta, n_cycles)
        old_res = run_old_at_eta(1, eta, n_cycles)

        cl6_berry.append(cl6_res["berry_total"])
        cl6_conc.append(cl6_res["concurrence"])
        cl6_ent.append(cl6_res["entropy"])
        old_conc.append(old_res["concurrence"])
        old_ent.append(old_res["entropy"])

        print(f"  eta={eta:.2f}: Cl6 Berry={cl6_res['berry_total']:.4f} C={cl6_res['concurrence']:.4f} "
              f"S={cl6_res['entropy']:.4f} | Old C={old_res['concurrence']:.4f} S={old_res['entropy']:.4f}")

    # Find optimal eta for concurrence in both engines
    cl6_peak_idx = int(np.argmax(cl6_conc))
    old_peak_idx = int(np.argmax(old_conc))
    cl6_peak_eta = etas[cl6_peak_idx]
    old_peak_eta = etas[old_peak_idx]

    shift = cl6_peak_eta - old_peak_eta
    optimal_eta_shift = float(shift) if abs(shift) > 0.01 else "none"

    print(f"\n  Cl(6) concurrence peak at eta={cl6_peak_eta:.2f}")
    print(f"  Old   concurrence peak at eta={old_peak_eta:.2f}")
    print(f"  Shift: {optimal_eta_shift}")

    # Also check Berry phase peak
    berry_peak_idx = int(np.argmax(cl6_berry))
    berry_peak_eta = etas[berry_peak_idx]
    print(f"  Cl(6) Berry phase peak at eta={berry_peak_eta:.2f}")

    return {
        "cl6": {
            "etas": etas,
            "berry": cl6_berry,
            "concurrence": cl6_conc,
            "entropy": cl6_ent,
        },
        "old": {
            "etas": etas,
            "concurrence": old_conc,
            "entropy": old_ent,
        },
        "cl6_peak_eta": float(cl6_peak_eta),
        "old_peak_eta": float(old_peak_eta),
        "berry_peak_eta": float(berry_peak_eta),
        "optimal_eta_shift": optimal_eta_shift,
    }


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 72)
    print("CONSTRAINT MANIFOLD CL(6) EXPLORATION")
    print("  Does the allowed-space landscape change when geometry is real?")
    print("=" * 72)

    results = {"name": "constraint_manifold_cl6"}

    results["L7_ordering"] = test_L7_ordering(n_cycles=5)
    results["L9_strength"] = test_L9_strength(n_cycles=5)
    results["L11_eta"] = test_L11_eta(n_cycles=5)

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  L7 Berry reveals new structure: {results['L7_ordering']['berry_reveals_new_structure']}")
    print(f"  L9 Goldilocks in Berry phase:   {results['L9_strength']['goldilocks_in_berry']}")
    print(f"  L11 Optimal eta shift:          {results['L11_eta']['optimal_eta_shift']}")

    # Write results
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "constraint_manifold_cl6_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(_sanitize(results), f, indent=2, default=str)
    print(f"\n  Results written to: {out_path}")


if __name__ == "__main__":
    main()
