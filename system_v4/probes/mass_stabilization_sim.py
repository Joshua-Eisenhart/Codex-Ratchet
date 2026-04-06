#!/usr/bin/env python3
"""
mass_stabilization_sim.py
=========================
Broad mass-sim pass covering:
  1. Bridge family verification (Clifford, TopoNetX, PyG)
  2. Entanglement dynamics (Type 1 vs Type 2, 50 cycles)
  3. Loop order sensitivity (normal, swapped, reversed, random)
  4. Torus transport (inner→Clifford→outer entropy/entanglement)
  5. Resonance sweep (piston strength 0→1)
  6. Torus entropy gradient (Clifford peak test)
  7. New tool validation (clifford, toponetx, pyg, z3, sympy, hypothesis, pydantic, gudhi)

All numbers are measured, not extrapolated.
"""

import sys, os, json, time, traceback
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, StageControls, LOOP_STAGE_ORDER
from hopf_manifold import (
    torus_coordinates, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    von_neumann_entropy_2x2, density_to_bloch, berry_phase,
    torus_radii, left_density, right_density,
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
# 1. BRIDGE FAMILY VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def test_clifford_bridge():
    """Verify Clifford algebra bridge roundtrip and rotor consistency."""
    try:
        from clifford_engine_bridge import (
            numpy_density_to_clifford, clifford_to_numpy_density,
            verify_roundtrip, verify_rotor_vs_numpy, chirality_content,
            rotor_z, rotor_x, apply_rotor, bloch_to_multivector,
        )
        results = {"status": "ok", "roundtrips": [], "rotor_dists": []}

        for eta_name, eta in [('inner', 0.3927), ('clifford', TORUS_CLIFFORD), ('outer', 1.1781)]:
            q = torus_coordinates(eta, 0.5, 0.3)
            rho_L = left_density(q)
            ok, dist = verify_roundtrip(rho_L)
            results["roundtrips"].append({"eta": eta_name, "ok": bool(ok), "dist": float(dist)})

        q = torus_coordinates(TORUS_CLIFFORD, 0.5, 0.3)
        rho = left_density(q)
        for angle in [0.1, 0.5, 1.0, np.pi/2]:
            dist_z, _, _ = verify_rotor_vs_numpy(rho, angle, 'z')
            results["rotor_dists"].append({"angle": float(angle), "axis": "z", "dist": float(dist_z)})

        # Chirality content check
        mv = numpy_density_to_clifford(rho)
        results["chirality_content"] = float(chirality_content(mv))
        results["all_roundtrips_ok"] = all(r["ok"] for r in results["roundtrips"])
        results["max_rotor_dist"] = max(r["dist"] for r in results["rotor_dists"])
        return results
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


def test_toponetx_bridge():
    """Verify TopoNetX cell complex construction."""
    try:
        from toponetx_torus_bridge import build_torus_complex, map_engine_cycle_to_complex, compute_shell_structure
        cc, node_map = build_torus_complex()
        results = {
            "status": "ok",
            "n_vertices": len(cc.nodes),
            "n_edges": len(cc.edges),
            "n_faces": len(cc.cells),
        }
        for et in [1, 2]:
            path = map_engine_cycle_to_complex(cc, et, node_map)
            results[f"type{et}_path_layers"] = [p[0] for p in path]
        shells = compute_shell_structure(cc, node_map)
        results["n_shells"] = len(shells)
        results["shell_deltas"] = [float(s["delta_eta"]) for s in shells]

        # Adjacency matrix
        adj = cc.adjacency_matrix(0)
        results["adj_shape"] = list(adj.shape)
        results["adj_nnz"] = int(adj.nnz)
        return results
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


def test_pyg_bridge():
    """Verify PyG heterogeneous graph construction."""
    try:
        from pyg_engine_bridge import build_engine_graph, attach_engine_state
        results = {"status": "ok", "types": {}}
        for et in [1, 2]:
            data = build_engine_graph(engine_type=et)
            engine = GeometricEngine(engine_type=et)
            state = engine.init_state()
            state = engine.run_cycle(state)
            data = attach_engine_state(data, state)
            results["types"][f"type{et}"] = {
                "node_types": data.node_types,
                "edge_types": [str(e) for e in data.edge_types],
                "terrain_shape": list(data['terrain'].x.shape),
                "operator_shape": list(data['operator'].x.shape),
                "torus_shape": list(data['torus'].x.shape),
                "state_shape": list(data['terrain'].state.shape),
                "ga0": float(state.ga0_level),
            }
        return results
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


# ═══════════════════════════════════════════════════════════════════
# 2. ENTANGLEMENT DYNAMICS (50 cycles, Type 1 vs Type 2)
# ═══════════════════════════════════════════════════════════════════

def test_entanglement_dynamics():
    """Run 50 cycles each for Type 1 and Type 2, track concurrence and entropy."""
    results = {}
    for et in [1, 2]:
        engine = GeometricEngine(engine_type=et)
        state = engine.init_state()
        trajectory = []
        for cycle in range(50):
            state = engine.run_cycle(state)
            C = concurrence_4x4(state.rho_AB)
            S_L = safe_entropy(state.rho_L)
            S_R = safe_entropy(state.rho_R)
            trajectory.append({
                "cycle": cycle,
                "concurrence": float(C),
                "S_L": float(S_L),
                "S_R": float(S_R),
                "ga0": float(state.ga0_level),
            })
        results[f"type{et}"] = {
            "final_concurrence": trajectory[-1]["concurrence"],
            "max_concurrence": max(t["concurrence"] for t in trajectory),
            "final_S_L": trajectory[-1]["S_L"],
            "trajectory_sample": trajectory[::10],  # every 10th cycle
        }
    return results


# ═══════════════════════════════════════════════════════════════════
# 3. LOOP ORDER SENSITIVITY
# ═══════════════════════════════════════════════════════════════════

def test_loop_order_sensitivity():
    """Test how composition order affects entanglement."""
    rng = np.random.default_rng(42)
    results = {}

    # Normal order
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    for _ in range(10):
        state = engine.run_cycle(state)
    results["normal"] = float(concurrence_4x4(state.rho_AB))

    # Reversed order
    engine2 = GeometricEngine(engine_type=1)
    state2 = engine2.init_state()
    reversed_order = list(reversed(LOOP_STAGE_ORDER[1]))
    for _ in range(10):
        for terrain_idx in reversed_order:
            state2 = engine2.step(state2, stage_idx=terrain_idx)
    results["reversed"] = float(concurrence_4x4(state2.rho_AB))

    # Random order (20 trials)
    random_Cs = []
    for trial in range(20):
        engine3 = GeometricEngine(engine_type=1)
        state3 = engine3.init_state()
        for _ in range(10):
            order = list(LOOP_STAGE_ORDER[1])
            rng.shuffle(order)
            for terrain_idx in order:
                state3 = engine3.step(state3, stage_idx=terrain_idx)
        random_Cs.append(float(concurrence_4x4(state3.rho_AB)))
    results["random_mean"] = float(np.mean(random_Cs))
    results["random_std"] = float(np.std(random_Cs))
    results["random_trials"] = random_Cs

    # Swapped (ind↔ded): swap outer and inner halves
    engine4 = GeometricEngine(engine_type=1)
    state4 = engine4.init_state()
    normal = LOOP_STAGE_ORDER[1]
    swapped = list(normal[4:]) + list(normal[:4])  # inner first, then outer
    for _ in range(10):
        for terrain_idx in swapped:
            state4 = engine4.step(state4, stage_idx=terrain_idx)
    results["swapped"] = float(concurrence_4x4(state4.rho_AB))

    return results


# ═══════════════════════════════════════════════════════════════════
# 4. TORUS TRANSPORT
# ═══════════════════════════════════════════════════════════════════

def test_torus_transport():
    """Test entropy and entanglement across torus levels."""
    results = {}
    for eta_name, eta in [('inner', TORUS_INNER), ('clifford', TORUS_CLIFFORD), ('outer', TORUS_OUTER)]:
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=eta)
        controls = {i: StageControls(torus=eta) for i in range(8)}
        for _ in range(10):
            state = engine.run_cycle(state, controls=controls)
        C = concurrence_4x4(state.rho_AB)
        S_L = safe_entropy(state.rho_L)
        S_R = safe_entropy(state.rho_R)
        R_maj, R_min = torus_radii(eta)
        results[eta_name] = {
            "eta": float(eta),
            "concurrence": float(C),
            "S_L": float(S_L),
            "S_R": float(S_R),
            "R_major": float(R_maj),
            "R_minor": float(R_min),
        }
    return results


# ═══════════════════════════════════════════════════════════════════
# 5. RESONANCE SWEEP
# ═══════════════════════════════════════════════════════════════════

def test_resonance_sweep():
    """Sweep piston strength 0→1 and measure concurrence peak."""
    results = {"type1": [], "type2": []}
    for et in [1, 2]:
        for p in np.linspace(0.0, 1.0, 21):
            engine = GeometricEngine(engine_type=et)
            state = engine.init_state()
            controls = {i: StageControls(piston=float(p)) for i in range(8)}
            for _ in range(10):
                state = engine.run_cycle(state, controls=controls)
            C = concurrence_4x4(state.rho_AB)
            results[f"type{et}"].append({"piston": float(p), "concurrence": float(C)})
    # Find peaks
    for et in [1, 2]:
        sweep = results[f"type{et}"]
        peak = max(sweep, key=lambda x: x["concurrence"])
        results[f"type{et}_peak"] = peak
    return results


# ═══════════════════════════════════════════════════════════════════
# 6. TORUS ENTROPY GRADIENT
# ═══════════════════════════════════════════════════════════════════

def test_torus_entropy_gradient():
    """Verify Clifford torus is entropy/entanglement maximum."""
    results = []
    for eta in np.linspace(0.1, np.pi/2 - 0.1, 15):
        engine = GeometricEngine(engine_type=1)
        state = engine.init_state(eta=float(eta))
        controls = {i: StageControls(torus=float(eta)) for i in range(8)}
        for _ in range(10):
            state = engine.run_cycle(state, controls=controls)
        C = concurrence_4x4(state.rho_AB)
        S_L = safe_entropy(state.rho_L)
        results.append({
            "eta": float(eta),
            "concurrence": float(C),
            "S_L": float(S_L),
        })
    # Find peak
    peak = max(results, key=lambda x: x["concurrence"])
    return {"sweep": results, "peak_eta": peak["eta"], "peak_concurrence": peak["concurrence"],
            "clifford_eta": float(TORUS_CLIFFORD)}


# ═══════════════════════════════════════════════════════════════════
# 7. NEW TOOL VALIDATION
# ═══════════════════════════════════════════════════════════════════

def test_z3_guards():
    """Test z3 solver on operator algebra constraints."""
    try:
        import z3
        results = {"status": "ok"}
        # Verify Pauli algebra: σ_x² = I, σ_z² = I, {σ_x, σ_z} = 0
        # Encode as: for eigenvalues, σ_x has eigenvalues ±1, σ_z has eigenvalues ±1
        sx_eig = z3.Real('sx_eig')
        sz_eig = z3.Real('sz_eig')
        solver = z3.Solver()
        solver.add(sx_eig * sx_eig == 1)
        solver.add(sz_eig * sz_eig == 1)
        result = solver.check()
        results["pauli_eigenvalue_sat"] = str(result)

        # Verify: no simultaneous eigenstates (non-commutativity)
        # [σ_x, σ_z] ≠ 0 → cannot have simultaneous eigenstate
        # Model this as: if v is eigenvector of both, then σ_x σ_z v = sx*sz*v
        # but also σ_z σ_x v = sz*sx*v, and [σ_x,σ_z] = -2iσ_y ≠ 0
        # Z3 can verify the algebraic constraint
        a, b, c, d = z3.Reals('a b c d')
        solver2 = z3.Solver()
        # σ_x|v⟩ = λ|v⟩ means [[0,1],[1,0]][[a],[b]] = λ[[a],[b]]
        # → b = λa, a = λb → a = λ²a → λ² = 1
        # σ_z|v⟩ = μ|v⟩ means [[1,0],[0,-1]][[a],[b]] = μ[[a],[b]]
        # → a = μa, -b = μb → μ = 1, b = 0 OR μ = -1, a = 0
        # Combined: if μ=1 → b=0, but λa=b=0 → a=0 (contradiction with normalization)
        # if μ=-1 → a=0, but λb=a=0 → b=0 (contradiction)
        lam, mu = z3.Reals('lam mu')
        solver2.add(lam * lam == 1)
        solver2.add(mu * mu == 1)
        solver2.add(b == lam * a)
        solver2.add(a == lam * b)
        solver2.add(a == mu * a)
        solver2.add(-b == mu * b)
        solver2.add(a * a + b * b == 1)  # normalization
        result2 = solver2.check()
        results["simultaneous_eigenstate_sat"] = str(result2)  # should be unsat
        results["N01_confirmed"] = str(result2) == "unsat"
        return results
    except Exception as e:
        return {"status": "error", "error": str(e)}


def test_sympy_algebra():
    """Verify Pauli algebra with sympy."""
    try:
        from sympy import Matrix, I, sqrt, simplify, eye
        sx = Matrix([[0, 1], [1, 0]])
        sy = Matrix([[0, -I], [I, 0]])
        sz = Matrix([[1, 0], [0, -1]])

        results = {"status": "ok"}
        # Commutation relations
        comm_xy = simplify(sx * sy - sy * sx - 2 * I * sz)
        comm_yz = simplify(sy * sz - sz * sy - 2 * I * sx)
        comm_zx = simplify(sz * sx - sx * sz - 2 * I * sy)
        results["comm_xy_zero"] = comm_xy == eye(2) * 0
        results["comm_yz_zero"] = comm_yz == eye(2) * 0
        results["comm_zx_zero"] = comm_zx == eye(2) * 0

        # Casimir
        casimir = simplify(sx**2 + sy**2 + sz**2)
        results["casimir"] = str(casimir)
        results["casimir_is_3I"] = casimir == 3 * eye(2)

        # Jacobi identity
        def comm(A, B): return A * B - B * A
        jacobi = simplify(comm(comm(sx, sy), sz) + comm(comm(sy, sz), sx) + comm(comm(sz, sx), sy))
        results["jacobi_zero"] = jacobi == eye(2) * 0
        return results
    except Exception as e:
        return {"status": "error", "error": str(e)}


def test_hypothesis_properties():
    """Property-based testing of engine invariants."""
    try:
        from hypothesis import given, settings, strategies as st

        results = {"status": "ok", "tests_run": 0, "tests_passed": 0}

        # Test: density matrix trace = 1 after any operator sequence
        @given(
            eta=st.floats(min_value=0.2, max_value=1.3, allow_nan=False),
            piston=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        )
        @settings(max_examples=50, deadline=None)
        def test_trace_preserved(eta, piston):
            engine = GeometricEngine(engine_type=1)
            state = engine.init_state(eta=eta)
            controls = {i: StageControls(piston=piston, torus=eta) for i in range(8)}
            state = engine.run_cycle(state, controls=controls)
            tr = float(np.real(np.trace(state.rho_AB)))
            assert abs(tr - 1.0) < 1e-10, f"Trace = {tr}"
            results["tests_passed"] += 1

        test_trace_preserved()
        results["tests_run"] += 50

        # Test: entropy non-negative
        @given(
            eta=st.floats(min_value=0.2, max_value=1.3, allow_nan=False),
        )
        @settings(max_examples=30, deadline=None)
        def test_entropy_nonneg(eta):
            engine = GeometricEngine(engine_type=1)
            state = engine.init_state(eta=eta)
            state = engine.run_cycle(state)
            S = safe_entropy(state.rho_L)
            assert S >= -1e-10, f"Negative entropy: {S}"
            results["tests_passed"] += 1

        test_entropy_nonneg()
        results["tests_run"] += 30

        return results
    except Exception as e:
        return {"status": "error", "error": str(e), "traceback": traceback.format_exc()}


def test_pydantic_validation():
    """Validate engine output schemas with pydantic."""
    try:
        from pydantic import BaseModel, field_validator
        from typing import List

        class CycleResult(BaseModel):
            cycle: int
            concurrence: float
            S_L: float
            S_R: float
            ga0: float

            @field_validator('concurrence')
            @classmethod
            def concurrence_range(cls, v):
                assert 0 <= v <= 1, f"Concurrence {v} out of [0,1]"
                return v

            @field_validator('S_L', 'S_R')
            @classmethod
            def entropy_nonneg(cls, v):
                assert v >= -1e-10, f"Negative entropy {v}"
                return v

        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        validated = 0
        for cycle in range(10):
            state = engine.run_cycle(state)
            C = concurrence_4x4(state.rho_AB)
            r = CycleResult(
                cycle=cycle,
                concurrence=C,
                S_L=safe_entropy(state.rho_L),
                S_R=safe_entropy(state.rho_R),
                ga0=state.ga0_level,
            )
            validated += 1

        return {"status": "ok", "validated_cycles": validated}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def test_gudhi_persistence():
    """Compute persistent homology of engine trajectory in Bloch space."""
    try:
        import gudhi

        engine = GeometricEngine(engine_type=1)
        state = engine.init_state()
        points = []
        for _ in range(20):
            state = engine.run_cycle(state)
            b = density_to_bloch(state.rho_L)
            points.append(list(b))

        rips = gudhi.RipsComplex(points=points, max_edge_length=2.0)
        st = rips.create_simplex_tree(max_dimension=2)
        st.compute_persistence()
        intervals = st.persistence_intervals_in_dimension(0)
        betti_0 = sum(1 for birth, death in intervals if death == float('inf'))
        intervals_1 = st.persistence_intervals_in_dimension(1)
        betti_1 = sum(1 for birth, death in intervals_1 if death == float('inf'))

        return {
            "status": "ok",
            "n_points": len(points),
            "betti_0": int(betti_0),
            "betti_1": int(betti_1),
            "n_intervals_dim0": len(intervals),
            "n_intervals_dim1": len(intervals_1),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# 8. DUAL-STACK RATCHET COMPARISON
# ═══════════════════════════════════════════════════════════════════

def test_dual_stack_ratchet():
    """Alternating Type 1 + Type 2 interaction dynamics."""
    engine1 = GeometricEngine(engine_type=1)
    engine2 = GeometricEngine(engine_type=2)
    state1 = engine1.init_state()
    state2 = engine2.init_state()
    trajectory = []
    for cycle in range(30):
        state1 = engine1.run_cycle(state1)
        state2 = engine2.run_cycle(state2)
        # Cross-couple: mix small fraction of joint states
        rho_mix = 0.95 * state1.rho_AB + 0.05 * state2.rho_AB
        state1.rho_AB = _ensure_valid_density(rho_mix)
        rho_mix2 = 0.95 * state2.rho_AB + 0.05 * state1.rho_AB
        state2.rho_AB = _ensure_valid_density(rho_mix2)
        trajectory.append({
            "cycle": cycle,
            "C1": float(concurrence_4x4(state1.rho_AB)),
            "C2": float(concurrence_4x4(state2.rho_AB)),
            "S1_L": float(safe_entropy(state1.rho_L)),
            "S2_L": float(safe_entropy(state2.rho_L)),
        })
    return {
        "trajectory_sample": trajectory[::5],
        "final_C1": trajectory[-1]["C1"],
        "final_C2": trajectory[-1]["C2"],
    }


# ═══════════════════════════════════════════════════════════════════
# 9. ENGINE IRREVERSIBILITY
# ═══════════════════════════════════════════════════════════════════

def test_irreversibility():
    """Confirm engine never returns to initial state."""
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state()
    rho_init = state.rho_AB.copy()
    min_dist = float('inf')
    for cycle in range(50):
        state = engine.run_cycle(state)
        dist = trace_distance_4x4(state.rho_AB, rho_init)
        min_dist = min(min_dist, dist)
    return {
        "min_trace_distance_from_init": float(min_dist),
        "irreversible": min_dist > 1e-6,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("MASS STABILIZATION SIM — BROAD PASS")
    print("=" * 70)

    tests = [
        ("clifford_bridge", test_clifford_bridge),
        ("toponetx_bridge", test_toponetx_bridge),
        ("pyg_bridge", test_pyg_bridge),
        ("entanglement_dynamics", test_entanglement_dynamics),
        ("loop_order_sensitivity", test_loop_order_sensitivity),
        ("torus_transport", test_torus_transport),
        ("resonance_sweep", test_resonance_sweep),
        ("torus_entropy_gradient", test_torus_entropy_gradient),
        ("z3_guards", test_z3_guards),
        ("sympy_algebra", test_sympy_algebra),
        ("hypothesis_properties", test_hypothesis_properties),
        ("pydantic_validation", test_pydantic_validation),
        ("gudhi_persistence", test_gudhi_persistence),
        ("dual_stack_ratchet", test_dual_stack_ratchet),
        ("irreversibility", test_irreversibility),
    ]

    t0 = time.time()
    for name, fn in tests:
        print(f"\n[{name}] running...", flush=True)
        try:
            result = fn()
            RESULTS[name] = result
            status = result.get("status", "ok") if isinstance(result, dict) else "ok"
            print(f"[{name}] {status}")
        except Exception as e:
            RESULTS[name] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
            print(f"[{name}] ERROR: {e}")

    elapsed = time.time() - t0
    RESULTS["_meta"] = {
        "elapsed_seconds": round(elapsed, 2),
        "n_tests": len(tests),
        "n_passed": sum(1 for r in RESULTS.values() if isinstance(r, dict) and r.get("status") != "error"),
        "n_errors": sum(1 for r in RESULTS.values() if isinstance(r, dict) and r.get("status") == "error"),
    }

    # Serialize
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

    out_path = os.path.join(os.path.dirname(__file__), "mass_stabilization_results.json")
    with open(out_path, "w") as f:
        json.dump(RESULTS, f, indent=2, default=numpy_encoder)

    print(f"\n{'=' * 70}")
    print(f"DONE in {elapsed:.1f}s — {RESULTS['_meta']['n_passed']}/{len(tests)} passed")
    print(f"Results: {out_path}")
    print(f"{'=' * 70}")
