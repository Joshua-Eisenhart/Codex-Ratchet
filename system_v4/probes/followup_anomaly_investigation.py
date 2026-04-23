#!/usr/bin/env python3
"""
Follow-up Anomaly Investigation — 3 targeted checks from mass-sim pass
======================================================================
1. Torus entropy-entanglement peak convergence: fine grid around eta=0.687 & 0.785, 200 cycles
2. Swapped-order (ind<->ded) sensitivity reconciliation: 0.000 vs 0.040 discrepancy
3. Extended Gudhi/Betti persistence: longer trajectory for persistent loops

All numbers measured, not extrapolated.
"""

import sys, os, json, time, traceback
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, LOOP_STAGE_ORDER
from hopf_manifold import (
    torus_coordinates, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    von_neumann_entropy_2x2, density_to_bloch, berry_phase, torus_radii,
    left_density, right_density,
)
from geometric_operators import (
    partial_trace_A, partial_trace_B, _ensure_valid_density,
    negentropy, trace_distance_4x4,
)

RESULTS = {}

def concurrence_4x4(rho_AB):
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho_AB.conj() @ sy_sy
    R = rho_AB @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
    return float(max(0, evals[0] - evals[1] - evals[2] - evals[3]))

def safe_entropy(rho):
    return von_neumann_entropy_2x2(_ensure_valid_density(rho))


# ═══════════════════════════════════════════════════════════════════
# 1. TORUS PEAK CONVERGENCE — fine grid, 200 cycles
# ═══════════════════════════════════════════════════════════════════

def test_torus_peak_convergence():
    """
    Fine eta sweep around the anomalous peak (0.687) and Clifford (0.785).
    Run each point for 200 cycles to check convergence.
    Also capture full trajectory at both eta values.
    """
    print("  [1a] Fine eta sweep (25 points, 200 cycles each)...", flush=True)

    # Fine sweep: 25 points from 0.5 to 1.0 (brackets both 0.687 and 0.785)
    sweep_results = []
    for eta in np.linspace(0.5, 1.0, 25):
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=float(eta))
        controls = {i: StageControls(torus=float(eta)) for i in range(8)}
        for _ in range(200):
            state = engine.run_cycle(state, controls=controls)
        C = concurrence_4x4(state.rho_AB)
        S_L = safe_entropy(state.rho_L)
        sweep_results.append({
            "eta": round(float(eta), 6),
            "concurrence_200c": float(C),
            "S_L_200c": float(S_L),
        })

    peak = max(sweep_results, key=lambda x: x["concurrence_200c"])

    # Full trajectory at eta=0.687 and eta=0.785 (200 cycles, sample every 10)
    print("  [1b] Trajectory at eta=0.687 and eta=0.785 (200 cycles)...", flush=True)
    trajectories = {}
    for eta_label, eta_val in [("peak_0687", 0.687), ("clifford_0785", TORUS_CLIFFORD)]:
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=float(eta_val))
        controls = {i: StageControls(torus=float(eta_val)) for i in range(8)}
        traj = []
        for cycle in range(200):
            state = engine.run_cycle(state, controls=controls)
            if cycle % 10 == 9:  # sample every 10th cycle
                traj.append({
                    "cycle": cycle + 1,
                    "concurrence": float(concurrence_4x4(state.rho_AB)),
                    "S_L": float(safe_entropy(state.rho_L)),
                    "ga0": float(state.ga0_level),
                })
        trajectories[eta_label] = traj

    # Also run at 10 cycles for comparison (to see if short-run caused the offset)
    short_run_results = []
    for eta in np.linspace(0.5, 1.0, 25):
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=float(eta))
        controls = {i: StageControls(torus=float(eta)) for i in range(8)}
        for _ in range(10):
            state = engine.run_cycle(state, controls=controls)
        C = concurrence_4x4(state.rho_AB)
        short_run_results.append({
            "eta": round(float(eta), 6),
            "concurrence_10c": float(C),
        })

    return {
        "sweep_200c": sweep_results,
        "sweep_10c": short_run_results,
        "peak_200c": peak,
        "trajectories": trajectories,
        "clifford_eta": float(TORUS_CLIFFORD),
    }


# ═══════════════════════════════════════════════════════════════════
# 2. SWAPPED-ORDER RECONCILIATION
# ═══════════════════════════════════════════════════════════════════

def test_swapped_order_reconciliation():
    """
    Rerun swapped (ind<->ded) with full diagnostics.
    The mass-sim measured 0.000, but an earlier doc claimed 0.040.

    Investigate:
    - Exact swapped order vs normal
    - Multiple cycle counts (5, 10, 20, 50, 100)
    - Per-cycle trajectory for both
    - Both engine types
    """
    print("  [2a] Swapped vs normal at multiple cycle counts...", flush=True)

    normal_order = LOOP_STAGE_ORDER[1]  # [4,6,7,5, 0,1,3,2]
    # "Swapped" = ind<->ded = swap the two halves
    swapped_order = list(normal_order[4:]) + list(normal_order[:4])  # [0,1,3,2, 4,6,7,5]

    cycle_counts = [5, 10, 20, 50, 100, 200]
    comparison = {}
    for n_cycles in cycle_counts:
        # Normal
        engine_n = GeometricEngine(engine_type=1)
        state_n = engine_n.init_state()
        for _ in range(n_cycles):
            for terrain_idx in normal_order:
                state_n = engine_n.step(state_n, stage_idx=terrain_idx)
        C_normal = concurrence_4x4(state_n.rho_AB)

        # Swapped
        engine_s = GeometricEngine(engine_type=1)
        state_s = engine_s.init_state()
        for _ in range(n_cycles):
            for terrain_idx in swapped_order:
                state_s = engine_s.step(state_s, stage_idx=terrain_idx)
        C_swapped = concurrence_4x4(state_s.rho_AB)

        comparison[n_cycles] = {
            "normal": float(C_normal),
            "swapped": float(C_swapped),
            "ratio": float(C_swapped / C_normal) if C_normal > 1e-12 else None,
        }

    # Per-cycle trajectory for 50 cycles (normal vs swapped)
    print("  [2b] Per-cycle trajectory (50 cycles)...", flush=True)
    traj_normal, traj_swapped = [], []
    engine_n = GeometricEngine(engine_type=1)
    state_n = engine_n.init_state()
    engine_s = GeometricEngine(engine_type=1)
    state_s = engine_s.init_state()
    for cycle in range(50):
        for terrain_idx in normal_order:
            state_n = engine_n.step(state_n, stage_idx=terrain_idx)
        for terrain_idx in swapped_order:
            state_s = engine_s.step(state_s, stage_idx=terrain_idx)
        traj_normal.append({"cycle": cycle + 1, "C": float(concurrence_4x4(state_n.rho_AB))})
        traj_swapped.append({"cycle": cycle + 1, "C": float(concurrence_4x4(state_s.rho_AB))})

    # Also test: what does Type 2 with swapped order look like?
    print("  [2c] Type 2 swapped...", flush=True)
    normal_order_t2 = LOOP_STAGE_ORDER[2]
    swapped_order_t2 = list(normal_order_t2[4:]) + list(normal_order_t2[:4])
    engine_t2n = GeometricEngine(engine_type=2)
    state_t2n = engine_t2n.init_state()
    engine_t2s = GeometricEngine(engine_type=2)
    state_t2s = engine_t2s.init_state()
    for _ in range(50):
        for ti in normal_order_t2:
            state_t2n = engine_t2n.step(state_t2n, stage_idx=ti)
        for ti in swapped_order_t2:
            state_t2s = engine_t2s.step(state_t2s, stage_idx=ti)

    return {
        "orders": {
            "normal_t1": list(normal_order),
            "swapped_t1": swapped_order,
            "normal_t2": list(normal_order_t2),
            "swapped_t2": swapped_order_t2,
        },
        "cycle_count_comparison": comparison,
        "trajectory_normal_50c": traj_normal[::5],   # every 5th
        "trajectory_swapped_50c": traj_swapped[::5],
        "type2_50c": {
            "normal": float(concurrence_4x4(state_t2n.rho_AB)),
            "swapped": float(concurrence_4x4(state_t2s.rho_AB)),
        },
        "diagnosis": "Swapped order == Type 2 normal order. Swapping ind<->ded converts T1 into T2's loop grammar, which dissipates entanglement." if swapped_order == list(normal_order_t2) else "Swapped order is NOT identical to T2 normal order — further investigation needed.",
    }


# ═══════════════════════════════════════════════════════════════════
# 3. EXTENDED GUDHI / BETTI PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def test_extended_gudhi_persistence():
    """
    Extended Gudhi persistence with longer trajectories.
    Original: 20 points, betti_1=0.
    Now: 200 cycles, both engine types, Type 1 at various torus levels.
    Also test dim-2 persistence.
    """
    try:
        import gudhi
    except ImportError:
        return {"status": "unavailable", "reason": "gudhi not installed"}

    results = {}

    # 200-cycle trajectory at Clifford (Type 1)
    print("  [3a] 200-cycle Bloch trajectory (Type 1, Clifford)...", flush=True)
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    points_L, points_R = [], []
    for _ in range(200):
        state = engine.run_cycle(state)
        b_L = density_to_bloch(state.rho_L)
        b_R = density_to_bloch(state.rho_R)
        points_L.append(list(b_L))
        points_R.append(list(b_R))

    for label, pts in [("type1_L_200c", points_L), ("type1_R_200c", points_R)]:
        rips = gudhi.RipsComplex(points=pts, max_edge_length=2.0)
        st = rips.create_simplex_tree(max_dimension=3)
        st.compute_persistence()

        intervals_0 = st.persistence_intervals_in_dimension(0)
        intervals_1 = st.persistence_intervals_in_dimension(1)
        intervals_2 = st.persistence_intervals_in_dimension(2)

        betti_0 = sum(1 for b, d in intervals_0 if d == float('inf'))
        betti_1 = sum(1 for b, d in intervals_1 if d == float('inf'))
        betti_2 = sum(1 for b, d in intervals_2 if d == float('inf'))

        # Most persistent finite intervals in dim 1
        finite_1 = [(float(b), float(d), float(d - b)) for b, d in intervals_1 if d != float('inf')]
        finite_1.sort(key=lambda x: -x[2])  # sort by persistence descending

        results[label] = {
            "n_points": len(pts),
            "betti_0": int(betti_0),
            "betti_1": int(betti_1),
            "betti_2": int(betti_2),
            "n_intervals_dim0": len(intervals_0),
            "n_intervals_dim1": len(intervals_1),
            "n_intervals_dim2": len(intervals_2),
            "top5_persistent_dim1": finite_1[:5] if finite_1 else [],
        }

    # Type 2 for comparison
    print("  [3b] 200-cycle Bloch trajectory (Type 2)...", flush=True)
    engine2 = GeometricEngine(engine_type=2)
    state2 = engine2.init_state()
    pts2 = []
    for _ in range(200):
        state2 = engine2.run_cycle(state2)
        pts2.append(list(density_to_bloch(state2.rho_L)))

    rips2 = gudhi.RipsComplex(points=pts2, max_edge_length=2.0)
    st2 = rips2.create_simplex_tree(max_dimension=3)
    st2.compute_persistence()
    i1_t2 = st2.persistence_intervals_in_dimension(1)
    finite_1_t2 = [(float(b), float(d), float(d - b)) for b, d in i1_t2 if d != float('inf')]
    finite_1_t2.sort(key=lambda x: -x[2])

    results["type2_L_200c"] = {
        "n_points": len(pts2),
        "betti_1": sum(1 for b, d in i1_t2 if d == float('inf')),
        "n_intervals_dim1": len(i1_t2),
        "top5_persistent_dim1": finite_1_t2[:5] if finite_1_t2 else [],
    }

    # Dual-stack trajectory (Type 1 + Type 2 cross-coupled)
    print("  [3c] 200-cycle dual-stack trajectory...", flush=True)
    e1 = GeometricEngine(engine_type=1)
    e2 = GeometricEngine(engine_type=2)
    s1 = e1.init_state()
    s2 = e2.init_state()
    pts_dual = []
    for _ in range(200):
        s1 = e1.run_cycle(s1)
        s2 = e2.run_cycle(s2)
        rho_mix = 0.95 * s1.rho_AB + 0.05 * s2.rho_AB
        s1.rho_AB = _ensure_valid_density(rho_mix)
        # Track combined Bloch point (L spinor of the mixed state)
        pts_dual.append(list(density_to_bloch(s1.rho_L)))

    rips_d = gudhi.RipsComplex(points=pts_dual, max_edge_length=2.0)
    st_d = rips_d.create_simplex_tree(max_dimension=3)
    st_d.compute_persistence()
    i1_d = st_d.persistence_intervals_in_dimension(1)
    finite_1_d = [(float(b), float(d), float(d - b)) for b, d in i1_d if d != float('inf')]
    finite_1_d.sort(key=lambda x: -x[2])

    results["dual_stack_200c"] = {
        "n_points": len(pts_dual),
        "betti_1": sum(1 for b, d in i1_d if d == float('inf')),
        "n_intervals_dim1": len(i1_d),
        "top5_persistent_dim1": finite_1_d[:5] if finite_1_d else [],
    }

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("FOLLOW-UP ANOMALY INVESTIGATION")
    print("=" * 70)

    tests = [
        ("torus_peak_convergence", test_torus_peak_convergence),
        ("swapped_order_reconciliation", test_swapped_order_reconciliation),
        ("extended_gudhi_persistence", test_extended_gudhi_persistence),
    ]

    t0 = time.time()
    for name, fn in tests:
        print(f"\n[{name}] running...", flush=True)
        try:
            result = fn()
            RESULTS[name] = result
            print(f"[{name}] done")
        except Exception as e:
            RESULTS[name] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
            print(f"[{name}] ERROR: {e}")

    elapsed = time.time() - t0
    RESULTS["_meta"] = {
        "elapsed_seconds": round(elapsed, 2),
        "n_tests": len(tests),
    }

    def numpy_encoder(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    out_path = os.path.join(os.path.dirname(__file__), "followup_anomaly_results.json")
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=numpy_encoder)

    print(f"\n{'=' * 70}")
    print(f"DONE in {elapsed:.1f}s")
    print(f"Results: {out_path}")
    print(f"{'=' * 70}")
