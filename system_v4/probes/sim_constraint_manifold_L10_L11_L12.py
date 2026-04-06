#!/usr/bin/env python3
"""
sim_constraint_manifold_L10_L11_L12.py
======================================
Full-range exploration of the ALLOWED dynamics at Layers 10, 11, and 12.

Layer 10: All interleaving patterns of dual-stack (Type 1 / Type 2).
Layer 11: Full eta sweep across the torus family [0.137, 1.434].
Layer 12: Full entanglement parameter space -- operator subsets + angle sweeps.

Output: a2_state/sim_results/constraint_manifold_L10_L11_L12_results.json
"""

import sys
import os
import json
import itertools
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls, TERRAINS, LOOP_STAGE_ORDER
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    _ensure_valid_density, partial_trace_A, partial_trace_B,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2,
)
from hopf_manifold import (
    von_neumann_entropy_2x2, torus_radii, berry_phase,
    torus_coordinates, left_weyl_spinor, right_weyl_spinor,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)

try:
    from toponetx_torus_bridge import build_torus_complex, map_engine_cycle_to_complex, compute_shell_structure
    HAS_TOPONETX = True
except Exception:
    HAS_TOPONETX = False


# ── Helpers ──────────────────────────────────────────────────────────

def concurrence_4x4(rho):
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    R = rho @ sy_sy @ rho.conj() @ sy_sy
    evals = sorted(np.sqrt(np.maximum(np.real(np.linalg.eigvals(R)), 0)), reverse=True)
    return max(0, evals[0] - evals[1] - evals[2] - evals[3])


def vn_entropy_4x4(rho):
    """Von Neumann entropy for a 4x4 density matrix."""
    rho_h = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho_h))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


def sanitize(obj):
    """Recursively sanitize numpy types for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    elif isinstance(obj, np.complexfloating):
        return {"re": float(np.real(obj)), "im": float(np.imag(obj))}
    return obj


# =====================================================================
# LAYER 10: ALL INTERLEAVING PATTERNS
# =====================================================================

def run_interleaving_pattern(pattern, n_cycles=20):
    """Run a sequence of engine types and record dynamics.

    pattern: list of 1s and 2s, length n_cycles.
    Returns dict of trajectory data.
    """
    eng1 = GeometricEngine(engine_type=1)
    eng2 = GeometricEngine(engine_type=2)

    # Start from Type 1 init
    state = eng1.init_state()

    entropy_traj = []
    concurrence_traj = []

    for i, et in enumerate(pattern):
        eng = eng1 if et == 1 else eng2
        # We must align the engine_type on the state for correct LUT lookups
        state.engine_type = et
        state = eng.run_cycle(state)

        ent = vn_entropy_4x4(state.rho_AB)
        conc = concurrence_4x4(state.rho_AB)
        entropy_traj.append(ent)
        concurrence_traj.append(conc)

    entropy_arr = np.array(entropy_traj)
    return {
        "pattern": [int(x) for x in pattern],
        "final_entropy": float(entropy_traj[-1]),
        "final_concurrence": float(concurrence_traj[-1]),
        "entropy_trajectory": [float(x) for x in entropy_traj],
        "concurrence_trajectory": [float(x) for x in concurrence_traj],
        "entropy_mean": float(np.mean(entropy_arr)),
        "entropy_variance": float(np.var(entropy_arr)),
        "entropy_max": float(np.max(entropy_arr)),
        "entropy_min": float(np.min(entropy_arr)),
        "concurrence_mean": float(np.mean(concurrence_traj)),
        "concurrence_max": float(np.max(concurrence_traj)),
    }


def layer_10():
    print("=== LAYER 10: Interleaving pattern space ===")
    N = 20
    rng = np.random.default_rng(42)

    patterns = {}

    # Named patterns
    named = {
        "pure_T1": [1] * N,
        "pure_T2": [2] * N,
        "alternating_12": [1, 2] * (N // 2),
        "alternating_21": [2, 1] * (N // 2),
        "pairs_1122": [1, 1, 2, 2] * (N // 4),
        "pairs_2211": [2, 2, 1, 1] * (N // 4),
        "blocks_4": [1]*4 + [2]*4 + [1]*4 + [2]*4 + [1]*4,  # trim to 20
        "burst_10_10": [1]*10 + [2]*10,
        "burst_10_10_rev": [2]*10 + [1]*10,
        "triple_133": ([1]*3 + [2]*3) * 3 + [1, 2],
    }
    # Fix blocks_4 to exactly 20
    named["blocks_4"] = named["blocks_4"][:N]
    named["triple_133"] = named["triple_133"][:N]

    for name, pat in named.items():
        print(f"  Running {name}...")
        patterns[name] = run_interleaving_pattern(pat, N)

    # Random patterns
    for i in range(10):
        pat = rng.choice([1, 2], size=N).tolist()
        name = f"random_{i}"
        print(f"  Running {name}...")
        patterns[name] = run_interleaving_pattern(pat, N)

    # Analysis
    all_names = list(patterns.keys())
    best_diversity = max(all_names, key=lambda n: patterns[n]["entropy_variance"])
    best_concurrence = max(all_names, key=lambda n: patterns[n]["concurrence_max"])
    best_final_conc = max(all_names, key=lambda n: patterns[n]["final_concurrence"])

    random_entropies = [patterns[f"random_{i}"]["final_entropy"] for i in range(10)]
    random_concurrences = [patterns[f"random_{i}"]["final_concurrence"] for i in range(10)]

    analysis = {
        "best_diversity_pattern": best_diversity,
        "best_diversity_variance": patterns[best_diversity]["entropy_variance"],
        "best_concurrence_pattern": best_concurrence,
        "best_concurrence_value": patterns[best_concurrence]["concurrence_max"],
        "best_final_concurrence_pattern": best_final_conc,
        "best_final_concurrence_value": patterns[best_final_conc]["final_concurrence"],
        "alternating_vs_pure_T1_entropy_delta": (
            patterns["alternating_12"]["final_entropy"] - patterns["pure_T1"]["final_entropy"]
        ),
        "alternating_vs_blocks_entropy_delta": (
            patterns["alternating_12"]["final_entropy"] - patterns["blocks_4"]["final_entropy"]
        ),
        "random_entropy_distribution": {
            "mean": float(np.mean(random_entropies)),
            "std": float(np.std(random_entropies)),
            "min": float(np.min(random_entropies)),
            "max": float(np.max(random_entropies)),
        },
        "random_concurrence_distribution": {
            "mean": float(np.mean(random_concurrences)),
            "std": float(np.std(random_concurrences)),
            "min": float(np.min(random_concurrences)),
            "max": float(np.max(random_concurrences)),
        },
    }

    print(f"  Best diversity: {best_diversity} (var={patterns[best_diversity]['entropy_variance']:.6f})")
    print(f"  Best concurrence: {best_concurrence} (max={patterns[best_concurrence]['concurrence_max']:.6f})")
    print(f"  Alternating final entropy: {patterns['alternating_12']['final_entropy']:.6f}")
    print(f"  Pure T1 final entropy: {patterns['pure_T1']['final_entropy']:.6f}")

    return {"patterns": patterns, "analysis": analysis}


# =====================================================================
# LAYER 11: FULL ETA SWEEP
# =====================================================================

def layer_11():
    print("\n=== LAYER 11: Full eta sweep [0.137, 1.434] ===")

    eta_values = np.linspace(0.137, 1.434, 30)
    n_cycles = 10

    sweep_results = []

    for idx, eta in enumerate(eta_values):
        if idx % 5 == 0:
            print(f"  eta = {eta:.4f} ({idx+1}/30)...")

        eng = GeometricEngine(engine_type=1)
        state = eng.init_state(eta=eta)

        entropy_traj = []
        concurrence_traj = []

        for cyc in range(n_cycles):
            state = eng.run_cycle(state)
            ent = vn_entropy_4x4(state.rho_AB)
            conc = concurrence_4x4(state.rho_AB)
            entropy_traj.append(ent)
            concurrence_traj.append(conc)

        R_major, R_minor = torus_radii(eta)

        # Berry phase at this eta
        us = np.linspace(0, 2 * np.pi, 64, endpoint=True)
        fiber_loop = np.array([torus_coordinates(eta, u, 0.0) for u in us])
        bp = berry_phase(fiber_loop)

        sweep_results.append({
            "eta": float(eta),
            "R_major": float(R_major),
            "R_minor": float(R_minor),
            "berry_phase": float(bp),
            "entropy_trajectory": [float(x) for x in entropy_traj],
            "concurrence_trajectory": [float(x) for x in concurrence_traj],
            "final_entropy": float(entropy_traj[-1]),
            "final_concurrence": float(concurrence_traj[-1]),
            "peak_concurrence": float(max(concurrence_traj)),
            "peak_entropy": float(max(entropy_traj)),
            "entropy_mean": float(np.mean(entropy_traj)),
            "concurrence_mean": float(np.mean(concurrence_traj)),
        })

    # Find peaks
    conc_peaks = [(r["eta"], r["peak_concurrence"]) for r in sweep_results]
    ent_peaks = [(r["eta"], r["peak_entropy"]) for r in sweep_results]
    best_conc = max(conc_peaks, key=lambda x: x[1])
    best_ent = max(ent_peaks, key=lambda x: x[1])

    # Qualitative change detection: where does concurrence drop to near zero?
    conc_finals = [r["final_concurrence"] for r in sweep_results]
    critical_transitions = []
    for i in range(1, len(conc_finals)):
        delta = abs(conc_finals[i] - conc_finals[i-1])
        if delta > 0.05:
            critical_transitions.append({
                "eta_from": float(eta_values[i-1]),
                "eta_to": float(eta_values[i]),
                "delta_concurrence": float(delta),
            })

    # Clifford value for comparison
    clifford_eta = np.pi / 4
    clifford_idx = int(np.argmin(np.abs(eta_values - clifford_eta)))

    # TopoNetX cell complex at 3 canonical positions
    toponetx_data = {}
    if HAS_TOPONETX:
        for name, eta_val in [("inner", TORUS_INNER), ("clifford", TORUS_CLIFFORD), ("outer", TORUS_OUTER)]:
            try:
                cc, node_map = build_torus_complex(n_per_ring=8, torus_levels=[(name, eta_val)])
                # Rebuild with all 3 for path mapping
                cc_full, nm_full = build_torus_complex()

                for et in [1, 2]:
                    path = map_engine_cycle_to_complex(cc_full, et, nm_full)
                    toponetx_data[f"{name}_type{et}_path"] = [list(p) for p in path]

                shells = compute_shell_structure(cc_full, nm_full)
                toponetx_data[f"shell_structure"] = [
                    {
                        "inner_layer": s["inner_layer"],
                        "outer_layer": s["outer_layer"],
                        "inner_eta": float(s["inner_eta"]),
                        "outer_eta": float(s["outer_eta"]),
                        "delta_eta": float(s["delta_eta"]),
                        "n_faces": s["n_faces"],
                    } for s in shells
                ]

                R_maj, R_min = torus_radii(eta_val)
                toponetx_data[f"{name}_radii"] = {"R_major": float(R_maj), "R_minor": float(R_min)}
            except Exception as e:
                toponetx_data[f"{name}_error"] = str(e)

    analysis = {
        "concurrence_peak_eta": float(best_conc[0]),
        "concurrence_peak_value": float(best_conc[1]),
        "entropy_peak_eta": float(best_ent[0]),
        "entropy_peak_value": float(best_ent[1]),
        "clifford_eta": float(clifford_eta),
        "clifford_nearest_idx": int(clifford_idx),
        "clifford_concurrence": float(sweep_results[clifford_idx]["final_concurrence"]),
        "clifford_entropy": float(sweep_results[clifford_idx]["final_entropy"]),
        "critical_transitions": critical_transitions,
        "is_clifford_optimal_concurrence": bool(abs(best_conc[0] - clifford_eta) < 0.1),
        "berry_phase_range": {
            "min": float(min(r["berry_phase"] for r in sweep_results)),
            "max": float(max(r["berry_phase"] for r in sweep_results)),
        },
    }

    print(f"  Concurrence peak at eta={best_conc[0]:.4f} (val={best_conc[1]:.6f})")
    print(f"  Entropy peak at eta={best_ent[0]:.4f} (val={best_ent[1]:.6f})")
    print(f"  Clifford (eta={clifford_eta:.4f}): conc={sweep_results[clifford_idx]['final_concurrence']:.6f}")
    print(f"  Critical transitions: {len(critical_transitions)}")

    return {
        "eta_sweep": sweep_results,
        "analysis": analysis,
        "toponetx": toponetx_data if toponetx_data else "toponetx_not_available",
    }


# =====================================================================
# LAYER 12: FULL ENTANGLEMENT PARAMETER SPACE
# =====================================================================

def layer_12():
    print("\n=== LAYER 12: Full entanglement parameter space ===")

    # --- 12a: Operator subset scan ---
    print("  12a: Operator subset scan (16 subsets)...")

    op_names = ["Ti", "Fe", "Te", "Fi"]
    op_fns = {
        "Ti": apply_Ti_4x4,
        "Fe": apply_Fe_4x4,
        "Te": apply_Te_4x4,
        "Fi": apply_Fi_4x4,
    }

    # Seed state: run 2 full engine cycles to get a slightly entangled state
    eng = GeometricEngine(engine_type=1)
    seed_state = eng.init_state()
    for _ in range(2):
        seed_state = eng.run_cycle(seed_state)
    seed_rho = seed_state.rho_AB.copy()
    seed_conc = concurrence_4x4(seed_rho)

    subset_results = []

    for r in range(len(op_names) + 1):
        for subset in itertools.combinations(op_names, r):
            subset_key = "+".join(subset) if subset else "NONE"

            rho = seed_rho.copy()
            conc_traj = []
            delta_conc_per_cycle = []

            for cyc in range(10):
                conc_before = concurrence_4x4(rho)

                # Apply each operator in the subset in order
                for op_name in subset:
                    fn = op_fns[op_name]
                    kwargs = {"polarity_up": True, "strength": 0.5}
                    if op_name == "Fe":
                        kwargs["phi"] = 0.4
                    elif op_name == "Fi":
                        kwargs["theta"] = 0.4
                    elif op_name == "Te":
                        kwargs["q"] = 0.7
                    rho = fn(rho, **kwargs)
                    rho = _ensure_valid_density(rho)

                conc_after = concurrence_4x4(rho)
                conc_traj.append(conc_after)
                delta_conc_per_cycle.append(conc_after - conc_before)

            avg_delta = float(np.mean(delta_conc_per_cycle))
            if avg_delta > 0.001:
                role = "BUILDS"
            elif avg_delta < -0.001:
                role = "DESTROYS"
            else:
                role = "PRESERVES"

            subset_results.append({
                "subset": list(subset),
                "subset_key": subset_key,
                "seed_concurrence": float(seed_conc),
                "final_concurrence": float(conc_traj[-1]),
                "concurrence_trajectory": [float(x) for x in conc_traj],
                "delta_concurrence_per_cycle": [float(x) for x in delta_conc_per_cycle],
                "avg_delta": float(avg_delta),
                "role": role,
            })

    builders = [s for s in subset_results if s["role"] == "BUILDS"]
    destroyers = [s for s in subset_results if s["role"] == "DESTROYS"]
    preservers = [s for s in subset_results if s["role"] == "PRESERVES"]

    print(f"    Builders: {[s['subset_key'] for s in builders]}")
    print(f"    Destroyers: {[s['subset_key'] for s in destroyers]}")
    print(f"    Preservers: {[s['subset_key'] for s in preservers]}")

    # --- 12b: Phase space sweep (theta, phi) ---
    print("  12b: Phase space sweep (30x30 = 900 points)...")

    theta_vals = np.linspace(0, 2 * np.pi, 30)
    phi_vals = np.linspace(0, 2 * np.pi, 30)

    landscape = np.zeros((30, 30))
    landscape_data = []

    for i, theta in enumerate(theta_vals):
        if i % 10 == 0:
            print(f"    theta row {i}/30...")
        for j, phi in enumerate(phi_vals):
            rho = seed_rho.copy()

            for cyc in range(5):
                # Apply all 4 operators with these angles
                rho = apply_Ti_4x4(rho, polarity_up=True, strength=0.5)
                rho = apply_Fe_4x4(rho, polarity_up=True, strength=0.5, phi=phi)
                rho = apply_Te_4x4(rho, polarity_up=True, strength=0.5, q=0.7)
                rho = apply_Fi_4x4(rho, polarity_up=True, strength=0.5, theta=theta)
                rho = _ensure_valid_density(rho)

            conc = concurrence_4x4(rho)
            landscape[i, j] = conc

    # Find optimal
    max_idx = np.unravel_index(np.argmax(landscape), landscape.shape)
    optimal_theta = float(theta_vals[max_idx[0]])
    optimal_phi = float(phi_vals[max_idx[1]])
    optimal_conc = float(landscape[max_idx[0], max_idx[1]])

    # Where is the engine's default (0.4, 0.4)?
    default_theta_idx = int(np.argmin(np.abs(theta_vals - 0.4)))
    default_phi_idx = int(np.argmin(np.abs(phi_vals - 0.4)))
    default_conc = float(landscape[default_theta_idx, default_phi_idx])

    # Landscape statistics
    flat = landscape.flatten()

    # Convert landscape to serializable list of dicts (sampled)
    landscape_rows = []
    for i in range(30):
        row = []
        for j in range(30):
            row.append(float(landscape[i, j]))
        landscape_rows.append(row)

    phase_space_analysis = {
        "optimal_theta": optimal_theta,
        "optimal_phi": optimal_phi,
        "optimal_concurrence": optimal_conc,
        "default_theta": 0.4,
        "default_phi": 0.4,
        "default_concurrence": default_conc,
        "default_is_at_peak": bool(abs(default_conc - optimal_conc) < 0.01),
        "default_rank_percentile": float(np.mean(flat <= default_conc) * 100),
        "landscape_mean": float(np.mean(flat)),
        "landscape_std": float(np.std(flat)),
        "landscape_min": float(np.min(flat)),
        "landscape_max": float(np.max(flat)),
        "landscape_median": float(np.median(flat)),
        "nonzero_fraction": float(np.mean(flat > 0.001)),
    }

    print(f"    Optimal: theta={optimal_theta:.4f}, phi={optimal_phi:.4f}, conc={optimal_conc:.6f}")
    print(f"    Default (0.4, 0.4): conc={default_conc:.6f}")
    print(f"    Default percentile: {phase_space_analysis['default_rank_percentile']:.1f}%")

    return {
        "operator_subset_scan": subset_results,
        "subset_analysis": {
            "builders": [s["subset_key"] for s in builders],
            "destroyers": [s["subset_key"] for s in destroyers],
            "preservers": [s["subset_key"] for s in preservers],
            "seed_concurrence": float(seed_conc),
        },
        "phase_space": {
            "theta_values": [float(x) for x in theta_vals],
            "phi_values": [float(x) for x in phi_vals],
            "landscape": landscape_rows,
            "analysis": phase_space_analysis,
        },
    }


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("Constraint Manifold Explorer: Layers 10, 11, 12")
    print("=" * 60)

    results = {}

    results["layer_10_interleaving"] = layer_10()
    results["layer_11_eta_sweep"] = layer_11()
    results["layer_12_entanglement"] = layer_12()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    l10 = results["layer_10_interleaving"]["analysis"]
    l11 = results["layer_11_eta_sweep"]["analysis"]
    l12 = results["layer_12_entanglement"]["phase_space"]["analysis"]

    print(f"\nL10: Best diversity pattern = {l10['best_diversity_pattern']}")
    print(f"     Best concurrence pattern = {l10['best_concurrence_pattern']}")
    print(f"     Alternating vs Pure T1 entropy delta = {l10['alternating_vs_pure_T1_entropy_delta']:.6f}")

    print(f"\nL11: Concurrence peak eta = {l11['concurrence_peak_eta']:.4f}")
    print(f"     Is Clifford optimal? {l11['is_clifford_optimal_concurrence']}")
    print(f"     Critical transitions = {len(l11['critical_transitions'])}")

    print(f"\nL12: Optimal (theta, phi) = ({l12['optimal_theta']:.4f}, {l12['optimal_phi']:.4f})")
    print(f"     Optimal concurrence = {l12['optimal_concurrence']:.6f}")
    print(f"     Default at percentile = {l12['default_rank_percentile']:.1f}%")

    # Write
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "constraint_manifold_L10_L11_L12_results.json"
    )

    with open(out_path, "w") as f:
        json.dump(sanitize(results), f, indent=2)

    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
