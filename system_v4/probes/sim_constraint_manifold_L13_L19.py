#!/usr/bin/env python3
"""
sim_constraint_manifold_L13_L19.py
==================================

Full constraint manifold exploration for Layers 13-19.

Layer 13-14: Bridge operator space — systematic scan of all 27 two-body
             Pauli interaction Hamiltonians on 3 qubits.
Layer 15-16: Dephasing x coupling phase diagram — 400-point grid.
Layer 17-19: Entropy and Axis 0 — eta x dephasing landscape (225 points).
Layer 19:    Initial state space — 12 states tested.

Outputs a single JSON with all landscapes, distributions, and optimal points.
"""

import json
import os
import sys
import time
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_3qubit_bridge_prototype import (
    partial_trace_keep, von_neumann_entropy, ensure_valid_density,
    build_3q_Ti, build_3q_Fe, build_3q_Te, build_3q_Fi,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2,
)
from hopf_manifold import TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, torus_radii


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

PAULIS = {"X": SIGMA_X, "Y": SIGMA_Y, "Z": SIGMA_Z}
PAULI_NAMES = ["X", "Y", "Z"]
DIMS = [2, 2, 2]

BIPARTITIONS = {
    "cut1_1vs23": {"A": [0], "B": [1, 2]},
    "cut2_12vs3": {"A": [0, 1], "B": [2]},
    "cut3_13vs2": {"A": [0, 2], "B": [1]},
}


def compute_Ic_all_cuts(rho):
    """Return dict of I_c for each bipartition cut."""
    S_AB = von_neumann_entropy(rho)
    results = {}
    for name, cut in BIPARTITIONS.items():
        rho_B = partial_trace_keep(rho, cut["B"], DIMS)
        S_B = von_neumann_entropy(rho_B)
        results[name] = S_B - S_AB
    return results


def make_rho_000():
    """Return |000><000| density matrix."""
    rho = np.zeros((8, 8), dtype=complex)
    rho[0, 0] = 1.0
    return rho


def state_ket(bits_str):
    """Convert '010' to |010> as 8-dim column vector."""
    idx = int(bits_str, 2)
    v = np.zeros(8, dtype=complex)
    v[idx] = 1.0
    return v


def ket_to_rho(v):
    """Pure state density matrix from ket."""
    v = v / np.linalg.norm(v)
    return np.outer(v, v.conj())


# ═══════════════════════════════════════════════════════════════════
# LAYER 13-14: BRIDGE OPERATOR SPACE
# Systematic scan of all 27 two-body Pauli Hamiltonians
# ═══════════════════════════════════════════════════════════════════

def build_2body_hamiltonian(pa_name, pb_name, pair):
    """Build P_a(i) x P_b(j) x I(remaining) as 8x8 matrix.

    pair: (i, j) where i < j, both in {0, 1, 2}.
    The remaining qubit gets identity.
    """
    P_a = PAULIS[pa_name]
    P_b = PAULIS[pb_name]
    i, j = pair

    # Build the 3-qubit operator by placing P_a at position i,
    # P_b at position j, and I2 at the remaining position.
    ops = [I2, I2, I2]
    ops[i] = P_a
    ops[j] = P_b
    return np.kron(np.kron(ops[0], ops[1]), ops[2])


def build_unitary_from_H(H, theta):
    """U = cos(theta/2)*I - i*sin(theta/2)*H"""
    d = H.shape[0]
    return np.cos(theta / 2) * np.eye(d, dtype=complex) - 1j * np.sin(theta / 2) * H


def run_layer13_14():
    """Scan all 27 two-body Hamiltonians for I_c generation."""
    print("\n" + "=" * 72)
    print("  LAYER 13-14: BRIDGE OPERATOR SPACE (27 Hamiltonians)")
    print("=" * 72)

    pairs = [(0, 1), (0, 2), (1, 2)]
    pair_labels = {(0, 1): "q01", (0, 2): "q02", (1, 2): "q12"}
    theta_bridge = 0.4
    deph_strength = 0.05
    n_cycles = 10

    results = []
    universal_bridges = []  # operators that bridge ALL 3 cuts

    for pair in pairs:
        for pa in PAULI_NAMES:
            for pb in PAULI_NAMES:
                label = f"{pa}{pb}_{pair_labels[pair]}"
                H = build_2body_hamiltonian(pa, pb, pair)
                U = build_unitary_from_H(H, theta_bridge)

                # Build dephasing ops
                Ti = build_3q_Ti(strength=deph_strength)
                Te = build_3q_Te(strength=deph_strength)

                rho = make_rho_000()
                max_ic = {"cut1_1vs23": -999.0, "cut2_12vs3": -999.0, "cut3_13vs2": -999.0}
                trajectory = []

                for cyc in range(1, n_cycles + 1):
                    # Ti -> candidate_U -> Te -> identity
                    rho = Ti(rho)
                    rho = U @ rho @ U.conj().T
                    rho = ensure_valid_density(rho)
                    rho = Te(rho)
                    # identity step (no-op)

                    ic = compute_Ic_all_cuts(rho)
                    for cut in max_ic:
                        if ic[cut] > max_ic[cut]:
                            max_ic[cut] = ic[cut]
                    trajectory.append({c: round(float(ic[c]), 8) for c in ic})

                positive_cuts = [c for c in max_ic if max_ic[c] > 1e-10]
                all_positive = len(positive_cuts) == 3

                entry = {
                    "label": label,
                    "pauli_a": pa,
                    "pauli_b": pb,
                    "pair": list(pair),
                    "max_Ic": {c: round(float(max_ic[c]), 8) for c in max_ic},
                    "positive_cuts": positive_cuts,
                    "all_3_cuts_positive": all_positive,
                    "trajectory": trajectory,
                }
                results.append(entry)

                if all_positive:
                    universal_bridges.append(label)

                best_cut = max(max_ic, key=max_ic.get)
                best_val = max_ic[best_cut]
                marker = " ***" if best_val > 1e-10 else ""
                print(f"  {label:10s}  best={best_val:+.6f} ({best_cut}){marker}")

    # Summary
    print(f"\n  Operators with I_c > 0 on ANY cut:")
    for r in results:
        if r["positive_cuts"]:
            cuts_str = ", ".join(r["positive_cuts"])
            best = max(r["max_Ic"].values())
            print(f"    {r['label']:10s}  max={best:+.6f}  cuts: {cuts_str}")

    print(f"\n  Universal bridges (all 3 cuts): {universal_bridges if universal_bridges else 'NONE'}")

    return {
        "all_operators": results,
        "universal_bridges": universal_bridges,
        "n_operators_tested": len(results),
        "theta": theta_bridge,
        "dephasing": deph_strength,
        "n_cycles": n_cycles,
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 15-16: DEPHASING x COUPLING PHASE DIAGRAM
# ═══════════════════════════════════════════════════════════════════

def run_layer15_16():
    """Fine-grid 2D scan: dephasing x fi_theta."""
    print("\n" + "=" * 72)
    print("  LAYER 15-16: DEPHASING x COUPLING PHASE DIAGRAM (400 points)")
    print("=" * 72)

    deph_vals = np.linspace(0.01, 2.0, 20)
    theta_vals = np.linspace(0.1, 2 * np.pi, 20)
    n_cycles = 20

    grid = []
    ic_positive_region = []
    max_global_ic = -999.0
    max_global_config = ""

    total = len(deph_vals) * len(theta_vals)
    count = 0

    for deph in deph_vals:
        for theta in theta_vals:
            count += 1
            Ti = build_3q_Ti(strength=float(deph))
            Fe = build_3q_Fe(strength=1.0, phi=0.4)
            Te = build_3q_Te(strength=float(deph), q=0.7)
            Fi = build_3q_Fi(strength=1.0, theta=float(theta))

            rho = make_rho_000()
            max_ic = -999.0
            positive_count = 0
            ic_sum = 0.0

            for cyc in range(n_cycles):
                rho = Ti(rho)
                rho = Fe(rho)
                rho = Te(rho)
                rho = Fi(rho)
                ic = compute_Ic_all_cuts(rho)
                best_ic_this = max(ic.values())
                if best_ic_this > max_ic:
                    max_ic = best_ic_this
                if best_ic_this > 1e-10:
                    positive_count += 1
                ic_sum += best_ic_this

            mean_ic = ic_sum / n_cycles
            entry = {
                "dephasing": round(float(deph), 4),
                "fi_theta": round(float(theta), 4),
                "max_Ic": round(float(max_ic), 8),
                "positive_cycles": positive_count,
                "mean_Ic": round(float(mean_ic), 8),
            }
            grid.append(entry)

            if max_ic > 1e-10:
                ic_positive_region.append(entry)

            if max_ic > max_global_ic:
                max_global_ic = max_ic
                max_global_config = f"deph={deph:.4f}, theta={theta:.4f}"

    # Analyze shape of positive region
    if ic_positive_region:
        deph_range = [min(e["dephasing"] for e in ic_positive_region),
                      max(e["dephasing"] for e in ic_positive_region)]
        theta_range = [min(e["fi_theta"] for e in ic_positive_region),
                       max(e["fi_theta"] for e in ic_positive_region)]
        n_islands = 1  # simple heuristic — count connected components later if needed
    else:
        deph_range = [0, 0]
        theta_range = [0, 0]
        n_islands = 0

    print(f"  Total grid points: {total}")
    print(f"  Points with I_c > 0: {len(ic_positive_region)}")
    print(f"  Global max I_c: {max_global_ic:+.8f}")
    print(f"  At config: {max_global_config}")
    print(f"  Positive dephasing range: {deph_range}")
    print(f"  Positive theta range: {theta_range}")

    return {
        "grid": grid,
        "n_positive_points": len(ic_positive_region),
        "n_total_points": total,
        "fraction_positive": round(len(ic_positive_region) / total, 4),
        "max_Ic": round(float(max_global_ic), 8),
        "max_config": max_global_config,
        "positive_dephasing_range": [round(float(x), 4) for x in deph_range],
        "positive_theta_range": [round(float(x), 4) for x in theta_range],
        "deph_values": [round(float(x), 4) for x in deph_vals],
        "theta_values": [round(float(x), 4) for x in theta_vals],
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 17-19: ETA x DEPHASING LANDSCAPE
# ═══════════════════════════════════════════════════════════════════

def run_layer17_19():
    """2D sweep: eta x dephasing with torus-scaled operators."""
    print("\n" + "=" * 72)
    print("  LAYER 17-19: ETA x DEPHASING LANDSCAPE (225 points)")
    print("=" * 72)

    eta_vals = np.linspace(0.15, 1.4, 15)
    deph_vals = np.linspace(0.01, 0.5, 15)
    n_cycles = 15
    fi_theta = np.pi

    grid = []
    max_global_ic = -999.0
    max_global_eta = 0.0
    max_global_deph = 0.0

    for eta in eta_vals:
        for deph in deph_vals:
            R_major, R_minor = torus_radii(float(eta))

            # Scale operators by torus radii
            Ti = build_3q_Ti(strength=float(deph) * R_minor)
            Fe = build_3q_Fe(strength=R_minor, phi=0.4)
            Te = build_3q_Te(strength=float(deph) * R_major, q=0.7)
            Fi = build_3q_Fi(strength=R_major, theta=fi_theta)

            rho = make_rho_000()
            max_ic_cut1 = -999.0
            ic_sum = 0.0
            final_entropy = 0.0

            for cyc in range(n_cycles):
                rho = Ti(rho)
                rho = Fe(rho)
                rho = Te(rho)
                rho = Fi(rho)
                ic_cuts = compute_Ic_all_cuts(rho)
                ic_cut1 = ic_cuts["cut1_1vs23"]
                if ic_cut1 > max_ic_cut1:
                    max_ic_cut1 = ic_cut1
                ic_sum += ic_cut1

            mean_ic = ic_sum / n_cycles
            final_entropy = von_neumann_entropy(rho)

            entry = {
                "eta": round(float(eta), 4),
                "dephasing": round(float(deph), 4),
                "R_major": round(float(R_major), 6),
                "R_minor": round(float(R_minor), 6),
                "max_Ic_cut1": round(float(max_ic_cut1), 8),
                "mean_Ic_cut1": round(float(mean_ic), 8),
                "final_entropy": round(float(final_entropy), 8),
            }
            grid.append(entry)

            if max_ic_cut1 > max_global_ic:
                max_global_ic = max_ic_cut1
                max_global_eta = float(eta)
                max_global_deph = float(deph)

    # Find operating region (mean I_c > 0)
    operating_region = [e for e in grid if e["mean_Ic_cut1"] > 1e-10]

    # Check if peak is at Clifford
    clifford_eta = np.pi / 4
    eta_deviation = abs(max_global_eta - clifford_eta)

    print(f"  Total grid points: {len(grid)}")
    print(f"  Operating region (mean I_c > 0): {len(operating_region)} points")
    print(f"  Global max I_c (cut1): {max_global_ic:+.8f}")
    print(f"  Optimal eta: {max_global_eta:.4f}  (Clifford = {clifford_eta:.4f})")
    print(f"  Optimal dephasing: {max_global_deph:.4f}")
    print(f"  Eta deviation from Clifford: {eta_deviation:.4f}")

    return {
        "grid": grid,
        "n_operating_region": len(operating_region),
        "max_Ic_cut1": round(float(max_global_ic), 8),
        "optimal_eta": round(float(max_global_eta), 4),
        "optimal_dephasing": round(float(max_global_deph), 4),
        "clifford_eta": round(float(clifford_eta), 4),
        "eta_deviation_from_clifford": round(float(eta_deviation), 4),
        "eta_values": [round(float(x), 4) for x in eta_vals],
        "deph_values": [round(float(x), 4) for x in deph_vals],
        "fi_theta": round(float(fi_theta), 4),
    }


# ═══════════════════════════════════════════════════════════════════
# LAYER 19 SPECIFIC: INITIAL STATE SPACE
# ═══════════════════════════════════════════════════════════════════

def run_layer19_initial_states():
    """Sweep 12 initial states and record I_c trajectories."""
    print("\n" + "=" * 72)
    print("  LAYER 19: INITIAL STATE SPACE (12 states)")
    print("=" * 72)

    n_cycles = 15
    deph = 0.05
    fi_theta = np.pi

    # Build the 12 initial states
    initial_states = {}

    # 8 computational basis states
    for bits in ["000", "001", "010", "011", "100", "101", "110", "111"]:
        initial_states[f"|{bits}>"] = ket_to_rho(state_ket(bits))

    # |+++>
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    v_ppp = np.kron(np.kron(plus, plus), plus)
    initial_states["|+++>"] = ket_to_rho(v_ppp)

    # |+0+>
    zero = np.array([1, 0], dtype=complex)
    v_p0p = np.kron(np.kron(plus, zero), plus)
    initial_states["|+0+>"] = ket_to_rho(v_p0p)

    # |GHZ> = (|000> + |111>) / sqrt(2)
    v_ghz = (state_ket("000") + state_ket("111")) / np.sqrt(2)
    initial_states["|GHZ>"] = ket_to_rho(v_ghz)

    # |W> = (|001> + |010> + |100>) / sqrt(3)
    v_w = (state_ket("001") + state_ket("010") + state_ket("100")) / np.sqrt(3)
    initial_states["|W>"] = ket_to_rho(v_w)

    # Build operators
    Ti = build_3q_Ti(strength=deph)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=deph, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=fi_theta)

    results = {}
    best_state = ""
    best_max_ic = -999.0

    for name, rho_init in initial_states.items():
        rho = ensure_valid_density(rho_init.copy())
        trajectory = []
        max_ic = -999.0

        for cyc in range(n_cycles):
            rho = Ti(rho)
            rho = Fe(rho)
            rho = Te(rho)
            rho = Fi(rho)
            ic = compute_Ic_all_cuts(rho)
            best_this = max(ic.values())
            trajectory.append({c: round(float(v), 8) for c, v in ic.items()})
            if best_this > max_ic:
                max_ic = best_this

        reaches_positive = max_ic > 1e-10
        results[name] = {
            "max_Ic": round(float(max_ic), 8),
            "reaches_positive": reaches_positive,
            "trajectory": trajectory,
        }

        marker = " ***" if reaches_positive else ""
        print(f"  {name:8s}  max I_c = {max_ic:+.8f}{marker}")

        if max_ic > best_max_ic:
            best_max_ic = max_ic
            best_state = name

    positive_states = [n for n, r in results.items() if r["reaches_positive"]]
    negative_states = [n for n, r in results.items() if not r["reaches_positive"]]

    print(f"\n  States reaching I_c > 0: {positive_states}")
    print(f"  States NOT reaching I_c > 0: {negative_states}")
    print(f"  Best state: {best_state} ({best_max_ic:+.8f})")

    return {
        "states": results,
        "positive_states": positive_states,
        "negative_states": negative_states,
        "best_state": best_state,
        "best_max_Ic": round(float(best_max_ic), 8),
        "n_cycles": n_cycles,
        "dephasing": deph,
        "fi_theta": round(float(fi_theta), 4),
    }


# ═══════════════════════════════════════════════════════════════════
# NUMPY TYPE SANITIZER
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to Python native types for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(x) for x in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()

    print("=" * 72)
    print("  CONSTRAINT MANIFOLD EXPLORER — Layers 13-19")
    print("  Full range of allowed bridge and axis configurations")
    print("=" * 72)

    # Run all layers
    l13_14 = run_layer13_14()
    l15_16 = run_layer15_16()
    l17_19 = run_layer17_19()
    l19_states = run_layer19_initial_states()

    elapsed = time.time() - t0

    # Assemble output
    output = {
        "name": "constraint_manifold_L13_L19",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "elapsed_seconds": round(elapsed, 2),
        "layer_13_14_bridge_operator_space": l13_14,
        "layer_15_16_phase_diagram": l15_16,
        "layer_17_19_eta_dephasing_landscape": l17_19,
        "layer_19_initial_state_space": l19_states,
        "summary": {
            "n_hamiltonians_tested": l13_14["n_operators_tested"],
            "universal_bridges": l13_14["universal_bridges"],
            "phase_diagram_fraction_positive": l15_16["fraction_positive"],
            "phase_diagram_max_Ic": l15_16["max_Ic"],
            "optimal_eta": l17_19["optimal_eta"],
            "optimal_dephasing_L17": l17_19["optimal_dephasing"],
            "eta_deviation_from_clifford": l17_19["eta_deviation_from_clifford"],
            "operating_region_size": l17_19["n_operating_region"],
            "best_initial_state": l19_states["best_state"],
            "n_positive_initial_states": len(l19_states["positive_states"]),
        },
    }

    output = sanitize(output)

    # Write results
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "constraint_manifold_L13_L19_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*72}")
    print(f"  COMPLETE in {elapsed:.1f}s")
    print(f"  Results: {out_path}")
    print(f"{'='*72}")

    return output


if __name__ == "__main__":
    main()
