#!/usr/bin/env python3
"""
sim_3qubit_bridge_prototype.py
==============================

Axis 0 Bridge Prototype: 3-qubit (d=8) Hilbert space I_c test.

The 2-qubit engine (d=4) cannot generate I_c > 0 from separable initial
states using its CPTP operator algebra.  This sim asks: does extending to
a 3-qubit register (d=8) break through?

Key insight — Fi acts across the 1,3 partition (X on qubit 1, Z on qubit 3),
which is an entangling gate across the A|B cut for bipartition
A={1}, B={2,3}.  The 2-qubit engine only has intra-partition operators.

Measures:
  I_c = S(rho_B) - S(rho_AB)     (coherent information)
  I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)   (mutual information)

Three bipartitions tested:
  Cut 1: A = qubit 1,     B = qubits 2,3   (2 x 4)
  Cut 2: A = qubits 1,2,  B = qubit 3      (4 x 2)
  Cut 3: A = qubits 1,3,  B = qubit 2      (requires reshuffling)
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ═══════════════════════════════════════════════════════════════════
# PAULI MATRICES
# ═══════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def von_neumann_entropy(rho: np.ndarray) -> float:
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho), in bits."""
    rho = (rho + rho.conj().T) / 2  # enforce Hermiticity
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    return float(-np.sum(evals * np.log2(evals)))


def partial_trace_keep(rho: np.ndarray, keep: list, dims: list) -> np.ndarray:
    """
    Partial trace: keep subsystems in 'keep', trace out the rest.
    dims = list of subsystem dimensions, e.g. [2,2,2] for 3 qubits.

    Uses the reshape-and-trace approach.
    """
    n = len(dims)
    # reshape rho into tensor with 2n indices: (d0,d1,...,d_{n-1}, d0,d1,...,d_{n-1})
    rho_r = rho.reshape(dims + dims)

    # trace out subsystems not in keep, from highest index to lowest
    trace_out = sorted([i for i in range(n) if i not in keep], reverse=True)
    current_n = n
    for i in trace_out:
        # axis1=i (bra index), axis2=i+current_n (ket index)
        rho_r = np.trace(rho_r, axis1=i, axis2=i + current_n)
        current_n -= 1

    d_keep = int(np.prod([dims[i] for i in keep]))
    return rho_r.reshape(d_keep, d_keep)


def ensure_valid_density(rho: np.ndarray) -> np.ndarray:
    """Force Hermiticity, positivity, trace=1."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    rho /= np.trace(rho)
    return rho


# ═══════════════════════════════════════════════════════════════════
# 3-QUBIT OPERATORS (8x8)
# ═══════════════════════════════════════════════════════════════════

def build_3q_Ti(strength: float = 1.0) -> callable:
    """Ti: ZZ dephasing on qubits 1,2 (tensor I on qubit 3).
    Luders projection using ZZ eigenprojectors on q1q2, identity on q3."""
    ZZ = np.kron(SIGMA_Z, SIGMA_Z)  # 4x4
    ZZ_I = np.kron(ZZ, I2)          # 8x8
    P0 = (np.eye(8, dtype=complex) + ZZ_I) / 2
    P1 = (np.eye(8, dtype=complex) - ZZ_I) / 2

    def apply(rho, polarity_up=True):
        mix = strength if polarity_up else 0.3 * strength
        rho_proj = P0 @ rho @ P0 + P1 @ rho @ P1
        rho_out = mix * rho_proj + (1 - mix) * rho
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Fe(strength: float = 1.0, phi: float = 0.4) -> callable:
    """Fe: XX rotation on qubits 1,2 (tensor I on qubit 3)."""
    XX = np.kron(SIGMA_X, SIGMA_X)  # 4x4
    H_int = np.kron(XX, I2)         # 8x8

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * phi * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        rho_out = U @ rho @ U.conj().T
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Te(strength: float = 1.0, q: float = 0.7) -> callable:
    """Te: YY dephasing on qubits 1,2 (tensor I on qubit 3)."""
    YY = np.kron(SIGMA_Y, SIGMA_Y)  # 4x4
    YY_I = np.kron(YY, I2)          # 8x8
    P_plus = (np.eye(8, dtype=complex) + YY_I) / 2
    P_minus = (np.eye(8, dtype=complex) - YY_I) / 2

    def apply(rho, polarity_up=True):
        mix = min(strength * (q if polarity_up else 0.3 * q), 1.0)
        rho_proj = P_plus @ rho @ P_plus + P_minus @ rho @ P_minus
        rho_out = (1 - mix) * rho + mix * rho_proj
        return ensure_valid_density(rho_out)
    return apply


def build_3q_Fi(strength: float = 1.0, theta: float = 0.4) -> callable:
    """Fi: X on qubit 1, Z on qubit 3 — THIS crosses the 1|23 partition.
    H_int = sigma_X(1) tensor I(2) tensor sigma_Z(3)."""
    H_int = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)  # 8x8

    def apply(rho, polarity_up=True):
        sign = 1.0 if polarity_up else -1.0
        angle = sign * theta * strength
        U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_int
        rho_out = U @ rho @ U.conj().T
        return ensure_valid_density(rho_out)
    return apply


# ═══════════════════════════════════════════════════════════════════
# BIPARTITION ANALYSIS
# ═══════════════════════════════════════════════════════════════════

BIPARTITIONS = {
    "cut1_1vs23": {"A": [0], "B": [1, 2], "label": "A=q1 | B=q2q3"},
    "cut2_12vs3": {"A": [0, 1], "B": [2], "label": "A=q1q2 | B=q3"},
    "cut3_13vs2": {"A": [0, 2], "B": [1], "label": "A=q1q3 | B=q2"},
}


def compute_info_measures(rho: np.ndarray, dims=[2, 2, 2]) -> dict:
    """Compute I_c and I(A:B) for all three bipartitions."""
    results = {}
    S_AB = von_neumann_entropy(rho)

    for name, cut in BIPARTITIONS.items():
        rho_A = partial_trace_keep(rho, cut["A"], dims)
        rho_B = partial_trace_keep(rho, cut["B"], dims)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        I_c = S_B - S_AB        # coherent information
        I_AB = S_A + S_B - S_AB  # mutual information
        S_AgivenB = S_AB - S_B   # conditional entropy

        results[name] = {
            "label": cut["label"],
            "S_A": round(S_A, 8),
            "S_B": round(S_B, 8),
            "S_AB": round(S_AB, 8),
            "I_c": round(I_c, 8),
            "I_AB": round(I_AB, 8),
            "S_A_given_B": round(S_AgivenB, 8),
            "I_c_positive": bool(I_c > 1e-10),
        }
    return results


# ═══════════════════════════════════════════════════════════════════
# INITIAL STATES
# ═══════════════════════════════════════════════════════════════════

def state_ket(bits: str) -> np.ndarray:
    """Convert '010' to |010> as 8-dim column vector."""
    idx = int(bits, 2)
    v = np.zeros(8, dtype=complex)
    v[idx] = 1.0
    return v


def make_initial_states() -> dict:
    """Build the set of initial states to test."""
    states = {}

    # |000> — fully separable
    v000 = state_ket("000")
    states["sep_000"] = np.outer(v000, v000.conj())

    # GHZ-like: (|000> + |111>) / sqrt(2)
    v_ghz = (state_ket("000") + state_ket("111")) / np.sqrt(2)
    states["ghz_000_111"] = np.outer(v_ghz, v_ghz.conj())

    # W-like: (|010>|0> + |100>|1>) / sqrt(2) = (|010> + |101>) / sqrt(2)
    v_w = (state_ket("010") + state_ket("101")) / np.sqrt(2)
    states["w_like_010_101"] = np.outer(v_w, v_w.conj())

    # |+,+,0> — superposition on q1,q2, computational on q3
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    zero = np.array([1, 0], dtype=complex)
    v_pp0 = np.kron(np.kron(plus, plus), zero)
    states["sep_pp0"] = np.outer(v_pp0, v_pp0.conj())

    # |+,0,+> — superposition on q1,q3 (Fi's partition)
    v_p0p = np.kron(np.kron(plus, zero), plus)
    states["sep_p0p"] = np.outer(v_p0p, v_p0p.conj())

    return states


# ═══════════════════════════════════════════════════════════════════
# OPERATOR CYCLE ENGINE
# ═══════════════════════════════════════════════════════════════════

def run_operator_cycle(rho_init: np.ndarray, n_cycles: int = 20,
                       strength: float = 1.0) -> list:
    """Run Ti -> Fe -> Te -> Fi cycle, record info measures each cycle."""
    Ti = build_3q_Ti(strength)
    Fe = build_3q_Fe(strength)
    Te = build_3q_Te(strength)
    Fi = build_3q_Fi(strength)

    ops = [("Ti", Ti), ("Fe", Fe), ("Te", Te), ("Fi", Fi)]

    history = []
    rho = rho_init.copy()

    # Measure initial state
    info = compute_info_measures(rho)
    history.append({"cycle": 0, "stage": "init", "info": info})

    for cycle in range(1, n_cycles + 1):
        for stage_name, op_fn in ops:
            rho = op_fn(rho, polarity_up=True)

        info = compute_info_measures(rho)
        history.append({"cycle": cycle, "stage": "post_cycle", "info": info})

    return history


# ═══════════════════════════════════════════════════════════════════
# STRENGTH SWEEP — look for optimal coupling
# ═══════════════════════════════════════════════════════════════════

def run_strength_sweep(rho_init: np.ndarray, n_cycles: int = 20) -> list:
    """Sweep Fi strength from 0.1 to 2.0 to find I_c peak."""
    results = []
    for s in np.arange(0.1, 2.05, 0.1):
        s = round(float(s), 2)
        hist = run_operator_cycle(rho_init, n_cycles, strength=s)
        # Find max I_c across all cycles and cuts
        best_ic = -999
        best_cut = ""
        best_cycle = 0
        for entry in hist:
            for cut_name, data in entry["info"].items():
                if data["I_c"] > best_ic:
                    best_ic = data["I_c"]
                    best_cut = cut_name
                    best_cycle = entry["cycle"]
        results.append({
            "strength": s,
            "best_I_c": round(best_ic, 8),
            "best_cut": best_cut,
            "best_cycle": best_cycle,
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# REGIME SEARCH — dephasing vs cross-partition coupling
# ═══════════════════════════════════════════════════════════════════

def run_regime_search(n_cycles: int = 30) -> dict:
    """Vary dephasing strength vs Fi theta to find I_c > 0 regimes.
    This is the KEY diagnostic: does weakened dephasing + strong
    cross-partition Fi yield sustained I_c > 0 from separable input?"""
    results = {}
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0  # |000>

    deph_values = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    theta_values = [0.4, 0.8, 1.2, np.pi / 2, np.pi]

    for deph_str in deph_values:
        for fi_theta in theta_values:
            Ti = build_3q_Ti(strength=deph_str)
            Fe = build_3q_Fe(strength=1.0, phi=0.4)
            Te = build_3q_Te(strength=deph_str, q=0.7)
            Fi = build_3q_Fi(strength=1.0, theta=fi_theta)

            rho = rho_init.copy()
            max_ic = -999.0
            max_cyc = 0
            max_cut = ""
            trajectory = []
            positive_cycles = 0

            for c in range(1, n_cycles + 1):
                rho = Ti(rho)
                rho = Fe(rho)
                rho = Te(rho)
                rho = Fi(rho)
                info = compute_info_measures(rho)
                # Track best across all cuts
                for cut_name, data in info.items():
                    if data["I_c"] > max_ic:
                        max_ic = data["I_c"]
                        max_cyc = c
                        max_cut = cut_name
                best_this_cycle = max(
                    info[cn]["I_c"] for cn in BIPARTITIONS
                )
                if best_this_cycle > 1e-10:
                    positive_cycles += 1
                trajectory.append(round(best_this_cycle, 8))

            key = f"deph={deph_str:.2f}_theta={fi_theta:.4f}"
            results[key] = {
                "dephasing_strength": round(deph_str, 3),
                "fi_theta": round(float(fi_theta), 6),
                "max_I_c": round(max_ic, 8),
                "max_cycle": max_cyc,
                "max_cut": max_cut,
                "positive_cycles": positive_cycles,
                "total_cycles": n_cycles,
                "trajectory": trajectory,
            }

    return results


# ═══════════════════════════════════════════════════════════════════
# 2-QUBIT COMPARISON — identical operator algebra, no environment
# ═══════════════════════════════════════════════════════════════════

def run_2qubit_comparison(n_cycles: int = 30) -> dict:
    """Run the same operator cycle on 2-qubit (4x4) for comparison.
    This establishes whether 3-qubit genuinely outperforms 2-qubit."""
    rho_init = np.zeros((4, 4), dtype=complex)
    rho_init[0, 0] = 1.0  # |00>

    results = {}
    deph_values = [0.05, 0.1, 0.2, 0.3, 0.5]
    # For 2-qubit, Fi = XZ rotation on qubits 1,2 (same space, no cross-partition)

    for deph_str in deph_values:
        ZZ = np.kron(SIGMA_Z, SIGMA_Z)
        P0_2 = (np.eye(4, dtype=complex) + ZZ) / 2
        P1_2 = (np.eye(4, dtype=complex) - ZZ) / 2
        YY = np.kron(SIGMA_Y, SIGMA_Y)
        Pp_2 = (np.eye(4, dtype=complex) + YY) / 2
        Pm_2 = (np.eye(4, dtype=complex) - YY) / 2

        rho = rho_init.copy()
        max_ic = -999.0
        max_cyc = 0
        trajectory = []

        for c in range(1, n_cycles + 1):
            # Ti
            mix = deph_str
            rho_p = P0_2 @ rho @ P0_2 + P1_2 @ rho @ P1_2
            rho = mix * rho_p + (1 - mix) * rho
            rho = ensure_valid_density(rho)
            # Fe
            XX = np.kron(SIGMA_X, SIGMA_X)
            U = np.cos(0.2) * np.eye(4, dtype=complex) - 1j * np.sin(0.2) * XX
            rho = U @ rho @ U.conj().T
            rho = ensure_valid_density(rho)
            # Te
            mix_te = min(deph_str * 0.7, 1.0)
            rho_p = Pp_2 @ rho @ Pp_2 + Pm_2 @ rho @ Pm_2
            rho = (1 - mix_te) * rho + mix_te * rho_p
            rho = ensure_valid_density(rho)
            # Fi (within same 2-qubit space — no cross-partition)
            XZ = np.kron(SIGMA_X, SIGMA_Z)
            U = np.cos(0.2) * np.eye(4, dtype=complex) - 1j * np.sin(0.2) * XZ
            rho = U @ rho @ U.conj().T
            rho = ensure_valid_density(rho)

            s_ab = von_neumann_entropy(rho)
            rho_b = partial_trace_keep(rho, [1], [2, 2])
            s_b = von_neumann_entropy(rho_b)
            ic = s_b - s_ab
            if ic > max_ic:
                max_ic = ic
                max_cyc = c
            trajectory.append(round(ic, 8))

        key = f"2q_deph={deph_str:.2f}"
        results[key] = {
            "dephasing_strength": round(deph_str, 3),
            "max_I_c": round(max_ic, 8),
            "max_cycle": max_cyc,
            "trajectory": trajectory,
        }

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  3-QUBIT BRIDGE PROTOTYPE — Axis 0 I_c Test")
    print("=" * 72)

    initial_states = make_initial_states()
    all_results = {}
    global_best_ic = -999
    global_best_config = ""
    ic_positive_found = False

    for state_name, rho_init in initial_states.items():
        print(f"\n--- State: {state_name} ---")
        rho_init = ensure_valid_density(rho_init)

        # Run default cycle
        history = run_operator_cycle(rho_init, n_cycles=20)

        # Extract I_c trajectory for each cut
        trajectories = {}
        for cut_name in BIPARTITIONS:
            traj = [(e["cycle"], e["info"][cut_name]["I_c"]) for e in history]
            trajectories[cut_name] = traj
            max_ic = max(v for _, v in traj)
            print(f"  {BIPARTITIONS[cut_name]['label']:20s}  max I_c = {max_ic:+.6f}")
            if max_ic > global_best_ic:
                global_best_ic = max_ic
                global_best_config = f"{state_name} / {cut_name}"
            if max_ic > 1e-10:
                ic_positive_found = True

        # Store the final cycle info measures
        all_results[state_name] = {
            "initial_info": history[0]["info"],
            "final_info": history[-1]["info"],
            "max_I_c_per_cut": {
                cut: round(max(e["info"][cut]["I_c"] for e in history), 8)
                for cut in BIPARTITIONS
            },
            "trajectories": {
                cut: [(c, round(v, 8)) for c, v in trajectories[cut]]
                for cut in BIPARTITIONS
            },
        }

    # Strength sweep on the two most promising separable states
    print("\n" + "=" * 72)
    print("  STRENGTH SWEEP")
    print("=" * 72)
    sweep_results = {}
    for state_name in ["sep_000", "sep_p0p"]:
        print(f"\n--- Sweep: {state_name} ---")
        rho_init = ensure_valid_density(initial_states[state_name])
        sweep = run_strength_sweep(rho_init, n_cycles=20)
        sweep_results[state_name] = sweep
        best_entry = max(sweep, key=lambda x: x["best_I_c"])
        print(f"  Best I_c = {best_entry['best_I_c']:+.6f} at strength={best_entry['strength']}, "
              f"cut={best_entry['best_cut']}, cycle={best_entry['best_cycle']}")
        if best_entry["best_I_c"] > global_best_ic:
            global_best_ic = best_entry["best_I_c"]
            global_best_config = f"{state_name} / sweep strength={best_entry['strength']}"
        if best_entry["best_I_c"] > 1e-10:
            ic_positive_found = True

    # REGIME SEARCH — the key diagnostic
    print("\n" + "=" * 72)
    print("  REGIME SEARCH — dephasing vs cross-partition Fi strength")
    print("=" * 72)
    regime_results = run_regime_search(n_cycles=30)
    regime_best = max(regime_results.values(), key=lambda x: x["max_I_c"])
    print(f"\n  Best regime: deph={regime_best['dephasing_strength']}, "
          f"theta={regime_best['fi_theta']:.4f}")
    print(f"  Max I_c = {regime_best['max_I_c']:+.6f} at cycle {regime_best['max_cycle']}")
    print(f"  Positive cycles: {regime_best['positive_cycles']}/{regime_best['total_cycles']}")

    # Show top 5 regimes
    sorted_regimes = sorted(regime_results.items(),
                            key=lambda kv: kv[1]["max_I_c"], reverse=True)
    print("\n  Top 5 regimes (from separable |000>):")
    for key, val in sorted_regimes[:5]:
        print(f"    {key:30s}  max I_c={val['max_I_c']:+.6f}  "
              f"pos_cycles={val['positive_cycles']:2d}/{val['total_cycles']}")

    if regime_best["max_I_c"] > global_best_ic:
        global_best_ic = regime_best["max_I_c"]
        global_best_config = (f"sep_000 / regime deph={regime_best['dephasing_strength']} "
                              f"theta={regime_best['fi_theta']:.4f}")
    if regime_best["max_I_c"] > 1e-10:
        ic_positive_found = True

    # 2-QUBIT COMPARISON
    print("\n" + "=" * 72)
    print("  2-QUBIT COMPARISON (same operators, no environment qubit)")
    print("=" * 72)
    twoq_results = run_2qubit_comparison(n_cycles=30)
    for key, val in twoq_results.items():
        print(f"  {key:20s}  max I_c = {val['max_I_c']:+.6f} (cycle {val['max_cycle']})")

    # Compute earned-best (separable starts only, regime search)
    earned_best_ic = regime_best["max_I_c"]
    earned_best_config = (f"sep_000 / regime deph={regime_best['dephasing_strength']} "
                          f"theta={regime_best['fi_theta']:.4f}")

    # Also check default cycle separable results
    for state_name in ["sep_000", "sep_pp0", "sep_p0p"]:
        if state_name in all_results:
            for cut, val in all_results[state_name]["max_I_c_per_cut"].items():
                if val > earned_best_ic:
                    earned_best_ic = val
                    earned_best_config = f"{state_name} / default / {cut}"

    # 2-qubit earned best for comparison
    twoq_best = max(twoq_results.values(), key=lambda x: x["max_I_c"])

    # Summary
    print("\n" + "=" * 72)
    print("  VERDICT")
    print("=" * 72)
    print(f"  I_c > 0 achieved (any start):     {ic_positive_found}")
    print(f"  Best I_c (any start):              {global_best_ic:+.8f}")
    print(f"  Best config (any start):           {global_best_config}")
    print()
    print(f"  EARNED I_c (separable start only): {earned_best_ic:+.8f}")
    print(f"  Earned config:                     {earned_best_config}")
    print(f"  Sustained positive cycles:         {regime_best['positive_cycles']}/{regime_best['total_cycles']}")
    print()
    print(f"  2-qubit best (for comparison):     {twoq_best['max_I_c']:+.8f}")
    print(f"  3q/2q advantage ratio:             {earned_best_ic / max(twoq_best['max_I_c'], 1e-15):.2f}x")
    print("=" * 72)

    # Build output JSON
    output = {
        "name": "3qubit_bridge_prototype",
        "initial_states_tested": list(initial_states.keys()),
        "operator_structure": "Ti(ZZ x I) + Fe(XX x I) + Te(YY x I) + Fi(X x I x Z)",
        "bipartitions": {
            name: cut["label"] for name, cut in BIPARTITIONS.items()
        },
        "default_cycle_results": {
            state_name: {
                "max_I_c_per_cut": data["max_I_c_per_cut"],
                "final_info": data["final_info"],
            }
            for state_name, data in all_results.items()
        },
        "strength_sweep": sweep_results,
        "regime_search": regime_results,
        "regime_best": {
            "dephasing_strength": regime_best["dephasing_strength"],
            "fi_theta": regime_best["fi_theta"],
            "max_I_c": regime_best["max_I_c"],
            "positive_cycles": regime_best["positive_cycles"],
        },
        "two_qubit_comparison": twoq_results,
        "I_c_positive_achieved": ic_positive_found,
        "best_I_c": round(global_best_ic, 8),
        "best_config": global_best_config,
        "earned_best_I_c": round(earned_best_ic, 8),
        "earned_best_config": earned_best_config,
        "earned_sustained_positive_cycles": regime_best["positive_cycles"],
        "twoq_best_I_c": round(twoq_best["max_I_c"], 8),
        "advantage_ratio_3q_vs_2q": round(earned_best_ic / max(twoq_best["max_I_c"], 1e-15), 4),
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_3qubit_prototype_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    return output


if __name__ == "__main__":
    main()
