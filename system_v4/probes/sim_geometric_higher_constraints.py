#!/usr/bin/env python3
"""
sim_geometric_higher_constraints.py
====================================
L7-L12 constraint layers driven by the REAL Cl(3) geometric engine.
No matrix algebra shortcuts. Actual rotors on the torus with Berry phase,
dissipation, and chirality forced through the hard constraints.

Output: a2_state/sim_results/geometric_higher_constraints_results.json
"""

import json
import os
import sys
import copy
import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_geometric import GeometricEngine, GeometricState
from hopf_manifold import (
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    torus_radii, berry_phase as hopf_berry_phase,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER


# ── numpy sanitiser ──────────────────────────────────────────────────
def _san(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: _san(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_san(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


# ── helpers ──────────────────────────────────────────────────────────
def _snapshot(eng, state, cycle_num):
    """Capture full geometric snapshot at end of a cycle."""
    sL, sR = eng.get_entropies(state)
    bL, bR = eng.get_bloch_vectors(state)
    return {
        "cycle": cycle_num,
        "berry_L": state.berry_phase_L,
        "berry_R": state.berry_phase_R,
        "entropy_L": sL,
        "entropy_R": sR,
        "purity_L": state.purity_L,
        "purity_R": state.purity_R,
        "bloch_L": bL.tolist(),
        "bloch_R": bR.tolist(),
        "eta": state.eta,
        "theta": state.theta,
        "phi": state.phi,
        "torus_level": state.torus_level,
        "LR_dot": float(np.dot(state.r_L, state.r_R)),
    }


def _run_n_cycles(eng, state, n):
    """Run n cycles, return list of snapshots."""
    snaps = [_snapshot(eng, state, 0)]
    for c in range(1, n + 1):
        state = eng.run_cycle(state)
        snaps.append(_snapshot(eng, state, c))
    return snaps, state


def _run_custom_order(eng, state, stage_order, n_cycles):
    """Run engine with a CUSTOM stage order instead of canonical."""
    snaps = [_snapshot(eng, state, 0)]
    for c in range(1, n_cycles + 1):
        for pos, ti in enumerate(stage_order):
            state = eng.run_stage(state, ti, pos)
        snaps.append(_snapshot(eng, state, c))
    return snaps, state


def _extract_trajectory(snaps, key):
    return [s[key] for s in snaps]


def _cross_corr(a, b):
    """Pearson correlation between two trajectories."""
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if len(a) < 2:
        return 0.0
    sa, sb = np.std(a), np.std(b)
    if sa < 1e-15 or sb < 1e-15:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _angle_between(v1, v2):
    """Angle in radians between two 3-vectors."""
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-14 or n2 < 1e-14:
        return 0.0
    cos_a = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.arccos(cos_a))


# =====================================================================
# L7: COMPOSITION ORDER WITH REAL GEOMETRY
# =====================================================================
def run_L7(n_cycles=10):
    print("=" * 60)
    print("L7: COMPOSITION ORDER -- Real Cl(3) Geometry")
    print("=" * 60)

    canonical_order = LOOP_STAGE_ORDER[1]
    reversed_order = list(reversed(canonical_order))
    rng = np.random.RandomState(42)
    random_orders = [list(rng.permutation(canonical_order)) for _ in range(5)]

    # canonical
    eng = GeometricEngine(engine_type=1)
    st = eng.init_state(eta=TORUS_CLIFFORD)
    canon_snaps, _ = _run_n_cycles(eng, st, n_cycles)

    # reversed
    eng2 = GeometricEngine(engine_type=1)
    st2 = eng2.init_state(eta=TORUS_CLIFFORD)
    rev_snaps, _ = _run_custom_order(eng2, st2, reversed_order, n_cycles)

    # random orderings
    rand_results = []
    for i, ro in enumerate(random_orders):
        eng_r = GeometricEngine(engine_type=1)
        st_r = eng_r.init_state(eta=TORUS_CLIFFORD)
        r_snaps, _ = _run_custom_order(eng_r, st_r, ro, n_cycles)
        rand_results.append({
            "order": ro,
            "trajectory": r_snaps,
        })

    # comparison
    canon_berry_L = _extract_trajectory(canon_snaps, "berry_L")
    rev_berry_L = _extract_trajectory(rev_snaps, "berry_L")
    canon_entropy_L = _extract_trajectory(canon_snaps, "entropy_L")
    rev_entropy_L = _extract_trajectory(rev_snaps, "entropy_L")

    berry_diff_rev = abs(canon_berry_L[-1] - rev_berry_L[-1])
    entropy_diff_rev = abs(canon_entropy_L[-1] - rev_entropy_L[-1])

    rand_berry_finals = [r["trajectory"][-1]["berry_L"] for r in rand_results]
    rand_entropy_finals = [r["trajectory"][-1]["entropy_L"] for r in rand_results]

    ordering_changes_berry = berry_diff_rev > 0.01
    ordering_changes_entropy = entropy_diff_rev > 0.001

    print(f"  Canonical final Berry_L:  {canon_berry_L[-1]:.6f}")
    print(f"  Reversed  final Berry_L:  {rev_berry_L[-1]:.6f}")
    print(f"  Berry diff (canon-rev):   {berry_diff_rev:.6f}")
    print(f"  Entropy diff (canon-rev): {entropy_diff_rev:.6f}")
    print(f"  Random Berry finals:      {[f'{x:.4f}' for x in rand_berry_finals]}")
    print(f"  ORDER CHANGES BERRY:      {'YES' if ordering_changes_berry else 'NO'}")
    print(f"  ORDER CHANGES ENTROPY:    {'YES' if ordering_changes_entropy else 'NO'}")

    return {
        "layer": "L7_composition_order",
        "n_cycles": n_cycles,
        "canonical_order": canonical_order,
        "reversed_order": reversed_order,
        "canonical_trajectory": canon_snaps,
        "reversed_trajectory": rev_snaps,
        "random_runs": rand_results,
        "comparison": {
            "canonical_final_berry_L": canon_berry_L[-1],
            "reversed_final_berry_L": rev_berry_L[-1],
            "berry_diff_canon_rev": berry_diff_rev,
            "entropy_diff_canon_rev": entropy_diff_rev,
            "random_final_berry_L": rand_berry_finals,
            "random_final_entropy_L": rand_entropy_finals,
            "ordering_changes_berry": ordering_changes_berry,
            "ordering_changes_entropy": ordering_changes_entropy,
        },
    }


# =====================================================================
# L8: POLARITY WITH REAL GEOMETRY
# =====================================================================
def run_L8(n_cycles=10):
    print("\n" + "=" * 60)
    print("L8: POLARITY -- Real Cl(3) Geometry")
    print("=" * 60)

    results = {}

    for label, polarity_override in [
        ("all_positive", True),
        ("all_negative", False),
        ("canonical_mixed", None),
    ]:
        eng = GeometricEngine(engine_type=1)

        # Override polarity in the LUT if requested
        if polarity_override is not None:
            orig_lut = dict(STAGE_OPERATOR_LUT)
            for key in STAGE_OPERATOR_LUT:
                op_name, _ = STAGE_OPERATOR_LUT[key]
                STAGE_OPERATOR_LUT[key] = (op_name, polarity_override)

        st = eng.init_state(eta=TORUS_CLIFFORD)
        snaps, _ = _run_n_cycles(eng, st, n_cycles)

        # Restore LUT
        if polarity_override is not None:
            STAGE_OPERATOR_LUT.update(orig_lut)

        bloch_L_traj = [s["bloch_L"] for s in snaps]
        bloch_R_traj = [s["bloch_R"] for s in snaps]

        results[label] = {
            "trajectory": snaps,
            "bloch_L_path": bloch_L_traj,
            "bloch_R_path": bloch_R_traj,
            "final_berry_L": snaps[-1]["berry_L"],
            "final_berry_R": snaps[-1]["berry_R"],
            "final_LR_dot": snaps[-1]["LR_dot"],
        }

        print(f"  {label:20s}  Berry_L={snaps[-1]['berry_L']:+.4f}  "
              f"Berry_R={snaps[-1]['berry_R']:+.4f}  LR_dot={snaps[-1]['LR_dot']:+.4f}")

    # compare bloch paths
    pos_path = np.array(results["all_positive"]["bloch_L_path"])
    neg_path = np.array(results["all_negative"]["bloch_L_path"])
    mix_path = np.array(results["canonical_mixed"]["bloch_L_path"])

    path_diff_pos_neg = float(np.mean(np.linalg.norm(pos_path - neg_path, axis=1)))
    path_diff_pos_mix = float(np.mean(np.linalg.norm(pos_path - mix_path, axis=1)))

    berry_diff = abs(results["all_positive"]["final_berry_L"] -
                     results["all_negative"]["final_berry_L"])

    print(f"  Bloch path diff (pos-neg): {path_diff_pos_neg:.6f}")
    print(f"  Bloch path diff (pos-mix): {path_diff_pos_mix:.6f}")
    print(f"  Berry diff (pos-neg):      {berry_diff:.6f}")
    print(f"  POLARITY CHANGES GEOMETRY: {'YES' if path_diff_pos_neg > 0.01 else 'NO'}")

    results["comparison"] = {
        "bloch_path_diff_pos_neg": path_diff_pos_neg,
        "bloch_path_diff_pos_mix": path_diff_pos_mix,
        "berry_diff_pos_neg": berry_diff,
        "polarity_changes_geometry": path_diff_pos_neg > 0.01,
    }
    return {"layer": "L8_polarity", "n_cycles": n_cycles, **results}


# =====================================================================
# L9: STRENGTH GOLDILOCKS WITH REAL GEOMETRY
# =====================================================================
def run_L9(n_cycles=10):
    print("\n" + "=" * 60)
    print("L9: STRENGTH GOLDILOCKS -- Real Cl(3) Geometry")
    print("=" * 60)

    strengths = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = {}

    for s_val in strengths:
        eng = GeometricEngine(engine_type=1)

        # Monkey-patch _operator_strength to return fixed value
        eng._operator_strength = lambda terrain, op_name, _sv=s_val: _sv

        st = eng.init_state(eta=TORUS_CLIFFORD)
        snaps, _ = _run_n_cycles(eng, st, n_cycles)

        entropy_traj = _extract_trajectory(snaps, "entropy_L")
        purity_L_traj = _extract_trajectory(snaps, "purity_L")
        purity_R_traj = _extract_trajectory(snaps, "purity_R")
        berry_traj = _extract_trajectory(snaps, "berry_L")

        results[f"strength_{s_val:.2f}"] = {
            "strength": s_val,
            "trajectory": snaps,
            "entropy_L_trajectory": entropy_traj,
            "purity_L_trajectory": purity_L_traj,
            "purity_R_trajectory": purity_R_traj,
            "berry_L_trajectory": berry_traj,
            "final_entropy_L": entropy_traj[-1],
            "final_purity_L": purity_L_traj[-1],
            "final_berry_L": berry_traj[-1],
        }

        print(f"  strength={s_val:.2f}  S_L={entropy_traj[-1]:.4f}  "
              f"|r_L|={purity_L_traj[-1]:.4f}  Berry_L={berry_traj[-1]:+.4f}")

    # Goldilocks: where is purity loss moderate (not 0, not max)?
    final_purities = {k: v["final_purity_L"] for k, v in results.items()}
    goldilocks_zone = {k: v for k, v in final_purities.items()
                       if 0.3 < v < 0.95}

    print(f"  Goldilocks zone (0.3 < purity < 0.95): {goldilocks_zone}")

    results["goldilocks_map"] = {
        "final_purities": final_purities,
        "goldilocks_zone": goldilocks_zone,
        "identity_at_zero": final_purities.get("strength_0.00", -1) > 0.99,
    }
    return {"layer": "L9_strength_goldilocks", "n_cycles": n_cycles, **results}


# =====================================================================
# L10: DUAL-STACK WITH REAL GEOMETRY
# =====================================================================
def run_L10(n_cycles=20):
    print("\n" + "=" * 60)
    print("L10: DUAL-STACK -- Real Cl(3) Geometry")
    print("=" * 60)

    # Type 1 only
    eng1 = GeometricEngine(engine_type=1)
    st1 = eng1.init_state(eta=TORUS_CLIFFORD)
    t1_snaps, _ = _run_n_cycles(eng1, st1, n_cycles)

    # Type 2 only
    eng2 = GeometricEngine(engine_type=2)
    st2 = eng2.init_state(eta=TORUS_CLIFFORD)
    t2_snaps, _ = _run_n_cycles(eng2, st2, n_cycles)

    # Alternating T1-T2
    eng1_alt = GeometricEngine(engine_type=1)
    eng2_alt = GeometricEngine(engine_type=2)
    # Align the cell complex states
    st_alt = eng1_alt.init_state(eta=TORUS_CLIFFORD)
    alt_snaps = [_snapshot(eng1_alt, st_alt, 0)]
    for c in range(1, n_cycles + 1):
        if c % 2 == 1:
            # T1 cycle
            for pos, ti in enumerate(LOOP_STAGE_ORDER[1]):
                st_alt = eng1_alt.run_stage(st_alt, ti, pos)
        else:
            # T2 cycle
            for pos, ti in enumerate(LOOP_STAGE_ORDER[2]):
                st_alt = eng2_alt.run_stage(st_alt, ti, pos)
        alt_snaps.append(_snapshot(eng1_alt, st_alt, c))

    t1_berry = _extract_trajectory(t1_snaps, "berry_L")
    t2_berry = _extract_trajectory(t2_snaps, "berry_L")
    alt_berry = _extract_trajectory(alt_snaps, "berry_L")

    t1_final = t1_berry[-1]
    t2_final = t2_berry[-1]
    alt_final = alt_berry[-1]

    # Is the alternating pattern different from either pure type?
    diff_from_t1 = abs(alt_final - t1_final)
    diff_from_t2 = abs(alt_final - t2_final)
    dual_differs = diff_from_t1 > 0.01 and diff_from_t2 > 0.01

    print(f"  T1-only  final Berry_L: {t1_final:+.6f}")
    print(f"  T2-only  final Berry_L: {t2_final:+.6f}")
    print(f"  Dual-alt final Berry_L: {alt_final:+.6f}")
    print(f"  Diff from T1: {diff_from_t1:.6f}  from T2: {diff_from_t2:.6f}")
    print(f"  DUAL WINDING DIFFERS:   {'YES' if dual_differs else 'NO'}")

    return {
        "layer": "L10_dual_stack",
        "n_cycles": n_cycles,
        "type1_trajectory": t1_snaps,
        "type2_trajectory": t2_snaps,
        "alternating_trajectory": alt_snaps,
        "comparison": {
            "t1_final_berry_L": t1_final,
            "t2_final_berry_L": t2_final,
            "alt_final_berry_L": alt_final,
            "diff_alt_t1": diff_from_t1,
            "diff_alt_t2": diff_from_t2,
            "dual_winding_differs": dual_differs,
        },
    }


# =====================================================================
# L11: FULL ETA SWEEP WITH REAL GEOMETRY
# =====================================================================
def run_L11(n_cycles=10):
    print("\n" + "=" * 60)
    print("L11: FULL ETA SWEEP -- Real Cl(3) Geometry")
    print("=" * 60)

    # Named etas + 4 intermediates
    named_etas = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    intermediates = np.linspace(TORUS_INNER, TORUS_OUTER, 6)[1:-1].tolist()
    all_etas = sorted(set(named_etas + intermediates))

    results = {}
    theoretical_berry = {}

    for eta_val in all_etas:
        eng = GeometricEngine(engine_type=1)
        st = eng.init_state(eta=eta_val)
        snaps, _ = _run_n_cycles(eng, st, n_cycles)

        berry_traj = _extract_trajectory(snaps, "berry_L")
        entropy_traj = _extract_trajectory(snaps, "entropy_L")
        purity_traj = _extract_trajectory(snaps, "purity_L")
        chirality_traj = _extract_trajectory(snaps, "LR_dot")

        # Theoretical Berry phase for great circle: -pi*(1 - cos(2*eta))
        theory = -np.pi * (1 - np.cos(2 * eta_val))

        R_maj, R_min = torus_radii(eta_val)
        label = f"eta_{eta_val:.4f}"

        results[label] = {
            "eta": eta_val,
            "R_major": R_maj,
            "R_minor": R_min,
            "trajectory": snaps,
            "berry_L_trajectory": berry_traj,
            "entropy_L_trajectory": entropy_traj,
            "purity_L_trajectory": purity_traj,
            "chirality_trajectory": chirality_traj,
            "final_berry_L": berry_traj[-1],
            "final_entropy_L": entropy_traj[-1],
            "final_purity_L": purity_traj[-1],
            "final_chirality": chirality_traj[-1],
            "theoretical_berry_great_circle": theory,
        }
        theoretical_berry[label] = theory

        eta_name = ""
        if abs(eta_val - TORUS_INNER) < 1e-6:
            eta_name = " (INNER)"
        elif abs(eta_val - TORUS_CLIFFORD) < 1e-6:
            eta_name = " (CLIFFORD)"
        elif abs(eta_val - TORUS_OUTER) < 1e-6:
            eta_name = " (OUTER)"

        print(f"  eta={eta_val:.4f}{eta_name:12s}  Berry_L={berry_traj[-1]:+.4f}  "
              f"S_L={entropy_traj[-1]:.4f}  |r_L|={purity_traj[-1]:.4f}  "
              f"L.R={chirality_traj[-1]:+.4f}  theory={theory:+.4f}")

    results["eta_sweep_map"] = {
        "etas": all_etas,
        "theoretical_berry": theoretical_berry,
    }
    return {"layer": "L11_eta_sweep", "n_cycles": n_cycles, **results}


# =====================================================================
# L12: ENTANGLEMENT WITH REAL GEOMETRY (UNCOUPLED)
# =====================================================================
def run_L12(n_cycles=10):
    print("\n" + "=" * 60)
    print("L12: ENTANGLEMENT (uncoupled) -- Real Cl(3) Geometry")
    print("=" * 60)

    eng = GeometricEngine(engine_type=1)
    st = eng.init_state(eta=TORUS_CLIFFORD)

    snaps = [_snapshot(eng, st, 0)]
    lr_angles = [_angle_between(st.r_L, st.r_R)]

    for c in range(1, n_cycles + 1):
        st = eng.run_cycle(st)
        snaps.append(_snapshot(eng, st, c))
        lr_angles.append(_angle_between(st.r_L, st.r_R))

    # Trajectories
    entropy_L = _extract_trajectory(snaps, "entropy_L")
    entropy_R = _extract_trajectory(snaps, "entropy_R")
    purity_L = _extract_trajectory(snaps, "purity_L")
    purity_R = _extract_trajectory(snaps, "purity_R")
    lr_dot = _extract_trajectory(snaps, "LR_dot")

    # Cross-correlations
    cc_entropy = _cross_corr(entropy_L, entropy_R)
    cc_purity = _cross_corr(purity_L, purity_R)

    # Does relative orientation change?
    angle_change = abs(lr_angles[-1] - lr_angles[0])
    angle_mean = float(np.mean(lr_angles))
    angle_std = float(np.std(lr_angles))

    # Purity evolution
    purity_L_change = purity_L[-1] - purity_L[0]
    purity_R_change = purity_R[-1] - purity_R[0]

    implicit_coupling = abs(cc_entropy) > 0.8 or abs(cc_purity) > 0.8

    print(f"  Cross-corr entropy L-R:   {cc_entropy:+.4f}")
    print(f"  Cross-corr purity  L-R:   {cc_purity:+.4f}")
    print(f"  L-R angle: start={lr_angles[0]:.4f}  end={lr_angles[-1]:.4f}  "
          f"change={angle_change:.4f}")
    print(f"  L-R angle mean={angle_mean:.4f}  std={angle_std:.4f}")
    print(f"  Purity change: L={purity_L_change:+.4f}  R={purity_R_change:+.4f}")
    print(f"  L.R dot trajectory:       {[f'{x:+.3f}' for x in lr_dot]}")
    print(f"  IMPLICIT GEOMETRIC COUPLING: {'YES' if implicit_coupling else 'NO'}")

    return {
        "layer": "L12_entanglement_uncoupled",
        "n_cycles": n_cycles,
        "trajectory": snaps,
        "lr_angle_trajectory": lr_angles,
        "entropy_L": entropy_L,
        "entropy_R": entropy_R,
        "purity_L": purity_L,
        "purity_R": purity_R,
        "lr_dot_trajectory": lr_dot,
        "cross_correlation": {
            "entropy_LR": cc_entropy,
            "purity_LR": cc_purity,
        },
        "lr_angle_stats": {
            "start": lr_angles[0],
            "end": lr_angles[-1],
            "change": angle_change,
            "mean": angle_mean,
            "std": angle_std,
        },
        "purity_change": {
            "L": purity_L_change,
            "R": purity_R_change,
        },
        "implicit_geometric_coupling": implicit_coupling,
    }


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("*" * 60)
    print("GEOMETRIC HIGHER CONSTRAINTS: L7-L12")
    print("Real Cl(3) rotors on nested Hopf tori")
    print("*" * 60)
    print()

    all_results = {}

    all_results["L7"] = run_L7()
    all_results["L8"] = run_L8()
    all_results["L9"] = run_L9()
    all_results["L10"] = run_L10()
    all_results["L11"] = run_L11()
    all_results["L12"] = run_L12()

    # ── summary ──
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    l7 = all_results["L7"]["comparison"]
    l8 = all_results["L8"]["comparison"]
    l9 = all_results["L9"]["goldilocks_map"]
    l10 = all_results["L10"]["comparison"]
    l12 = all_results["L12"]

    print(f"  L7  Order changes Berry:          {l7['ordering_changes_berry']}")
    print(f"  L7  Order changes entropy:        {l7['ordering_changes_entropy']}")
    print(f"  L8  Polarity changes geometry:    {l8['polarity_changes_geometry']}")
    print(f"  L9  Identity at strength=0:       {l9['identity_at_zero']}")
    print(f"  L9  Goldilocks zone:              {l9['goldilocks_zone']}")
    print(f"  L10 Dual winding differs:         {l10['dual_winding_differs']}")
    print(f"  L12 Implicit geometric coupling:  {l12['implicit_geometric_coupling']}")
    print(f"  L12 Cross-corr entropy:           {l12['cross_correlation']['entropy_LR']:+.4f}")
    print(f"  L12 Cross-corr purity:            {l12['cross_correlation']['purity_LR']:+.4f}")

    # ── write ──
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geometric_higher_constraints_results.json")

    with open(out_path, "w") as f:
        json.dump(_san(all_results), f, indent=2)

    print(f"\nResults written to: {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
