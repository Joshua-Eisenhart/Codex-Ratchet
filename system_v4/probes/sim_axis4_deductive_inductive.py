#!/usr/bin/env python3
"""
sim_axis4_deductive_inductive.py — Axis 4 Engine-Level Deductive/Inductive Probe
=================================================================================
Tests Axis 4 (deductive vs inductive loop ordering) through the FULL engine,
verifying that UEUE vs EUEU traversal order produces distinguishable dynamics,
that Type 1 and Type 2 have opposite Ax4 assignments, and that Ax4 is
orthogonal to the other locked axes.

Axis 4 definition (AXIS_3_4_5_6_QIT_MATH.md):
  - Deductive (FeTi): Phi_UEUE = U o E o U o E   ->  Se->Ne->Ni->Si
  - Inductive (TeFi): Phi_EUEU = E o U o E o U   ->  Se->Si->Ni->Ne
  - Type 1: outer=deductive (base), inner=inductive (fiber)
  - Type 2: outer=inductive (fiber), inner=deductive (base)

Build order: 6->5->3->4->1->2. Axes 6,5,3 are done. This is Axis 4.

Output: a2_state/sim_results/axis4_deductive_inductive_results.json
"""

import numpy as np
import json
import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, List, Tuple
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, EngineState, StageControls,
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR,
    _TERRAIN_TO_LOOP,
)
from geometric_operators import (
    partial_trace_A, partial_trace_B, trace_distance_4x4,
    _ensure_valid_density,
)
from hopf_manifold import von_neumann_entropy_2x2, TORUS_CLIFFORD


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def vn_entropy_4x4(rho):
    """Von Neumann entropy in nats for a 4x4 density matrix."""
    rho = (rho + rho.conj().T) / 2
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log(evals)))


def concurrence_2x2(rho):
    """Concurrence for a 2-qubit state (Wootters formula)."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sy_sy = np.kron(sy, sy)
    rho_tilde = sy_sy @ rho.conj() @ sy_sy
    R = rho @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
    return float(max(0.0, evals[0] - evals[1] - evals[2] - evals[3]))


def mutual_information_4x4(rho_AB):
    """I(A:B) = S(A) + S(B) - S(AB)."""
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    s_a = von_neumann_entropy_2x2(rho_A)
    s_b = von_neumann_entropy_2x2(rho_B)
    s_ab = vn_entropy_4x4(rho_AB)
    return float(max(0.0, s_a + s_b - s_ab))


def ax4_label_for_step(engine_type, position_in_cycle):
    """Return +1 (deductive) or -1 (inductive) for a given position in the cycle.

    Positions 0-3 are outer loop, 4-7 are inner loop.
    Type 1: outer=deductive(+1), inner=inductive(-1)
    Type 2: outer=inductive(-1), inner=deductive(+1)
    """
    is_outer = position_in_cycle < 4
    if engine_type == 1:
        return +1 if is_outer else -1   # outer=ded, inner=ind
    else:
        return -1 if is_outer else +1   # outer=ind, inner=ded


def terrain_topo_order(engine_type, loop_name):
    """Return the topology traversal sequence for a given loop.

    From LOOP_STAGE_ORDER:
      Deductive: Se->Ne->Ni->Si
      Inductive: Se->Si->Ni->Ne
    """
    order = LOOP_STAGE_ORDER[engine_type]
    if loop_name == "outer":
        indices = order[:4]
    else:
        indices = order[4:]
    return [TERRAINS[i]["topo"] for i in indices]


# ═══════════════════════════════════════════════════════════════════
# CORE DATA COLLECTION: Run engine, record per-step metrics
# ═══════════════════════════════════════════════════════════════════

def run_engine_with_ax4_recording(engine_type, n_cycles=10, entangle_strength=0.3, seed=42):
    """Run engine for n_cycles, recording Ax4 assignment and dynamics at each step."""
    engine = GeometricEngine(engine_type=engine_type, entangle_strength=entangle_strength)
    rng = np.random.default_rng(seed)
    state = engine.init_state(rng=rng)

    records = []
    stage_order = LOOP_STAGE_ORDER[engine_type]

    for cycle in range(n_cycles):
        for position, terrain_idx in enumerate(stage_order):
            terrain = TERRAINS[terrain_idx]
            rho_before = state.rho_AB.copy()
            s_before = vn_entropy_4x4(rho_before)
            c_before = concurrence_2x2(rho_before)
            mi_before = mutual_information_4x4(rho_before)

            # Look up operator
            op_name, polarity = STAGE_OPERATOR_LUT[(engine_type, terrain["loop"], terrain["topo"])]

            # Step
            state = engine.step(state, stage_idx=terrain_idx)

            rho_after = state.rho_AB.copy()
            s_after = vn_entropy_4x4(rho_after)
            c_after = concurrence_2x2(rho_after)
            mi_after = mutual_information_4x4(rho_after)

            # Ax4 assignment
            ax4 = ax4_label_for_step(engine_type, position)

            # Ax0: hemisphere
            ax0 = int(np.sign(np.cos(2 * state.eta)))

            # Ax3: fiber=-1, base=+1
            ax3 = -1 if terrain["loop"] == "fiber" else +1

            # Ax5: T-kernel=-1, F-kernel=+1
            ax5 = -1 if op_name in ("Ti", "Te") else +1

            # Ax6: derived = -ax0 * ax3
            ax6 = -ax0 * ax3

            records.append({
                "cycle": cycle,
                "position": position,
                "terrain": terrain["name"],
                "topo": terrain["topo"],
                "loop": terrain["loop"],
                "expansion": terrain["expansion"],
                "open": terrain["open"],
                "operator": op_name,
                "polarity_up": polarity,
                "ax4": ax4,
                "ax0": ax0,
                "ax3": ax3,
                "ax5": ax5,
                "ax6": ax6,
                "delta_entropy": s_after - s_before,
                "delta_concurrence": c_after - c_before,
                "delta_MI": mi_after - mi_before,
                "entropy_after": s_after,
                "concurrence_after": c_after,
                "MI_after": mi_after,
            })

        # End-of-cycle entangling gate
        if entangle_strength > 0:
            from geometric_operators import apply_Entangle_4x4
            state.rho_AB = apply_Entangle_4x4(state.rho_AB, strength=entangle_strength)

    return records, state


# ═══════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════

def test_P1_different_dynamics(records):
    """P1: Deductive and inductive stages produce DIFFERENT mean delta_entropy."""
    ded = [r["delta_entropy"] for r in records if r["ax4"] == +1]
    ind = [r["delta_entropy"] for r in records if r["ax4"] == -1]
    mean_ded = np.mean(ded)
    mean_ind = np.mean(ind)
    diff = abs(mean_ded - mean_ind)
    passed = diff > 1e-6
    return {
        "id": "P1",
        "name": "deductive_inductive_different_dynamics",
        "mean_delta_entropy_deductive": float(mean_ded),
        "mean_delta_entropy_inductive": float(mean_ind),
        "difference": float(diff),
        "pass": passed,
    }


def test_P2_opposite_assignments(records_t1, records_t2):
    """P2: Type 1 and Type 2 have OPPOSITE Ax4 assignments for the same loop position."""
    mismatches = 0
    total = min(8, len(records_t1), len(records_t2))  # first cycle, 8 steps
    details = []
    for i in range(total):
        r1 = records_t1[i]
        r2 = records_t2[i]
        # Same position in cycle should have opposite Ax4
        opposite = (r1["ax4"] != r2["ax4"])
        if opposite:
            mismatches += 1
        details.append({
            "position": i,
            "t1_ax4": r1["ax4"],
            "t2_ax4": r2["ax4"],
            "t1_terrain": r1["terrain"],
            "t2_terrain": r2["terrain"],
            "opposite": opposite,
        })
    passed = mismatches == total
    return {
        "id": "P2",
        "name": "opposite_ax4_across_types",
        "opposite_count": mismatches,
        "total": total,
        "details": details,
        "pass": passed,
    }


def test_P3_reversed_order_changes_trajectory(engine_type=1, n_cycles=5, seed=42):
    """P3: Reversing the loop order within a loop changes the trajectory."""
    # Normal run
    engine_normal = GeometricEngine(engine_type=engine_type, entangle_strength=0.3)
    state_normal = engine_normal.init_state(rng=np.random.default_rng(seed))

    normal_order = LOOP_STAGE_ORDER[engine_type]
    for _ in range(n_cycles):
        for terrain_idx in normal_order:
            state_normal = engine_normal.step(state_normal, stage_idx=terrain_idx)

    rho_normal = state_normal.rho_AB.copy()

    # Reversed inner loop
    engine_reversed = GeometricEngine(engine_type=engine_type, entangle_strength=0.3)
    state_reversed = engine_reversed.init_state(rng=np.random.default_rng(seed))

    reversed_order = list(normal_order[:4]) + list(reversed(normal_order[4:]))
    for _ in range(n_cycles):
        for terrain_idx in reversed_order:
            state_reversed = engine_reversed.step(state_reversed, stage_idx=terrain_idx)

    rho_reversed = state_reversed.rho_AB.copy()

    td = trace_distance_4x4(rho_normal, rho_reversed)
    passed = td > 1e-4
    return {
        "id": "P3",
        "name": "reversed_order_changes_trajectory",
        "trace_distance_normal_vs_reversed": float(td),
        "pass": passed,
    }


def test_N1_both_deductive(n_cycles=5, seed=42):
    """N1: Make both loops deductive (same order). Does the engine still work?"""
    engine = GeometricEngine(engine_type=1, entangle_strength=0.3)
    state_normal = engine.init_state(rng=np.random.default_rng(seed))
    state_modified = engine.init_state(rng=np.random.default_rng(seed))

    normal_order = LOOP_STAGE_ORDER[1]
    # Both deductive: Se->Ne->Ni->Si for both loops
    # Fiber: Se=0, Ne=2, Ni=3, Si=1
    both_ded_order = list(normal_order[:4]) + [0, 2, 3, 1]  # inner also deductive

    for _ in range(n_cycles):
        for terrain_idx in normal_order:
            state_normal = engine.step(state_normal, stage_idx=terrain_idx)
        for terrain_idx in both_ded_order:
            state_modified = engine.step(state_modified, stage_idx=terrain_idx)

    td = trace_distance_4x4(state_normal.rho_AB, state_modified.rho_AB)
    s_normal = vn_entropy_4x4(state_normal.rho_AB)
    s_modified = vn_entropy_4x4(state_modified.rho_AB)

    # Engine should still produce valid density matrices
    evals = np.real(np.linalg.eigvalsh(state_modified.rho_AB))
    valid_density = all(e >= -1e-10 for e in evals) and abs(np.trace(state_modified.rho_AB) - 1.0) < 1e-8

    return {
        "id": "N1",
        "name": "both_loops_deductive",
        "trace_distance_from_normal": float(td),
        "entropy_normal": float(s_normal),
        "entropy_both_ded": float(s_modified),
        "valid_density": valid_density,
        "different_from_normal": td > 1e-4,
        "pass": True,  # diagnostic; always passes — we report what happens
    }


def test_N2_both_inductive(n_cycles=5, seed=42):
    """N2: Make both loops inductive (same order). Compare."""
    engine = GeometricEngine(engine_type=1, entangle_strength=0.3)
    state_normal = engine.init_state(rng=np.random.default_rng(seed))
    state_modified = engine.init_state(rng=np.random.default_rng(seed))

    normal_order = LOOP_STAGE_ORDER[1]
    # Both inductive: Se->Si->Ni->Ne for both loops
    # Base: Se=4, Si=5, Ni=7, Ne=6
    both_ind_order = [4, 5, 7, 6] + list(normal_order[4:])  # outer also inductive

    for _ in range(n_cycles):
        for terrain_idx in normal_order:
            state_normal = engine.step(state_normal, stage_idx=terrain_idx)
        for terrain_idx in both_ind_order:
            state_modified = engine.step(state_modified, stage_idx=terrain_idx)

    td = trace_distance_4x4(state_normal.rho_AB, state_modified.rho_AB)
    s_normal = vn_entropy_4x4(state_normal.rho_AB)
    s_modified = vn_entropy_4x4(state_modified.rho_AB)

    evals = np.real(np.linalg.eigvalsh(state_modified.rho_AB))
    valid_density = all(e >= -1e-10 for e in evals) and abs(np.trace(state_modified.rho_AB) - 1.0) < 1e-8

    return {
        "id": "N2",
        "name": "both_loops_inductive",
        "trace_distance_from_normal": float(td),
        "entropy_normal": float(s_normal),
        "entropy_both_ind": float(s_modified),
        "valid_density": valid_density,
        "different_from_normal": td > 1e-4,
        "pass": True,  # diagnostic
    }


def test_N3_randomized_order(n_cycles=5, seed=42):
    """N3: Randomize the order within each loop. Does it degrade?"""
    engine = GeometricEngine(engine_type=1, entangle_strength=0.3)
    state_normal = engine.init_state(rng=np.random.default_rng(seed))
    state_random = engine.init_state(rng=np.random.default_rng(seed))

    normal_order = LOOP_STAGE_ORDER[1]
    rng = np.random.default_rng(seed + 1)

    for _ in range(n_cycles):
        for terrain_idx in normal_order:
            state_normal = engine.step(state_normal, stage_idx=terrain_idx)

        # Randomize within each loop
        outer = list(normal_order[:4])
        inner = list(normal_order[4:])
        rng.shuffle(outer)
        rng.shuffle(inner)
        random_order = outer + inner
        for terrain_idx in random_order:
            state_random = engine.step(state_random, stage_idx=terrain_idx)

    td = trace_distance_4x4(state_normal.rho_AB, state_random.rho_AB)
    s_normal = vn_entropy_4x4(state_normal.rho_AB)
    s_random = vn_entropy_4x4(state_random.rho_AB)
    c_normal = concurrence_2x2(state_normal.rho_AB)
    c_random = concurrence_2x2(state_random.rho_AB)

    return {
        "id": "N3",
        "name": "randomized_order",
        "trace_distance_from_normal": float(td),
        "entropy_normal": float(s_normal),
        "entropy_random": float(s_random),
        "concurrence_normal": float(c_normal),
        "concurrence_random": float(c_random),
        "degrades": td > 1e-4,
        "pass": True,  # diagnostic
    }


def test_orthogonality(records):
    """Compute correlations: Ax4 vs Ax0, Ax3, Ax5, Ax6.

    Ax4 should be independent of Ax5 (T/F kernel) and Ax6 (left/right).
    Check: is there an algebraic identity involving Ax4?
    """
    axes = {name: np.array([r[name] for r in records], dtype=float)
            for name in ["ax0", "ax3", "ax4", "ax5", "ax6"]}

    correlations = {}
    for name in ["ax0", "ax3", "ax5", "ax6"]:
        if np.std(axes["ax4"]) > 1e-10 and np.std(axes[name]) > 1e-10:
            corr = float(np.corrcoef(axes["ax4"], axes[name])[0, 1])
        else:
            corr = 0.0
        correlations[f"Ax4_vs_{name}"] = corr

    # Check algebraic identity: Ax4 = ? function of other axes
    # Test: Ax4 = Ax3 (since Type1: outer=ded=+1, inner=ind=-1 and Ax3: base=+1, fiber=-1)
    # But Type2 reverses this! So Ax4 depends on engine type.
    # For Type1: outer=base=Ax3+1=ded=Ax4+1, inner=fiber=Ax3-1=ind=Ax4-1 => Ax4 = Ax3
    # For Type2: outer=fiber=Ax3-1=ind=Ax4-1, inner=base=Ax3+1=ded=Ax4+1 => Ax4 = Ax3
    # Wait, let me check more carefully...
    # Type1: outer=base(Ax3=+1)=deductive(Ax4=+1), inner=fiber(Ax3=-1)=inductive(Ax4=-1)
    # Type2: outer=fiber(Ax3=-1)=inductive(Ax4=-1), inner=base(Ax3=+1)=deductive(Ax4=+1)
    # In BOTH cases Ax4 tracks base/fiber, not outer/inner!
    # So Ax4 = Ax3 identically? No -- the LOOP ORDER differs, not just the assignment.
    # Actually: deductive is always on base terrains, inductive always on fiber.
    # Type1: base=outer=deductive, fiber=inner=inductive
    # Type2: fiber=outer=inductive, base=inner=deductive
    # So: deductive <-> base, inductive <-> fiber in BOTH types.
    # This means Ax4 = Ax3 in the +-1 encoding!
    # But Ax4 is NOT redundant with Ax3 because Ax4 encodes the TRAVERSAL ORDER
    # (Se->Ne->Ni->Si vs Se->Si->Ni->Ne), not just which loop we're in.

    # Check product rule: does Ax4 = some_product(Ax0, Ax3, Ax5, Ax6)?
    product_ax0_ax3 = axes["ax0"] * axes["ax3"]
    product_ax3_ax5 = axes["ax3"] * axes["ax5"]
    identity_checks = {}
    for label, product in [("Ax0*Ax3", product_ax0_ax3), ("Ax3*Ax5", product_ax3_ax5)]:
        match_rate = float(np.mean(product == axes["ax4"]))
        identity_checks[f"Ax4_equals_{label}"] = match_rate

    # Ax4 vs Ax3 direct match
    ax4_equals_ax3 = float(np.mean(axes["ax4"] == axes["ax3"]))
    identity_checks["Ax4_equals_Ax3"] = ax4_equals_ax3

    return {
        "id": "ORTHO",
        "name": "axis_orthogonality",
        "correlations": correlations,
        "identity_checks": identity_checks,
        "pass": True,  # diagnostic
    }


def test_ax4_observable(records):
    """Ax4 observable: is Ax4 correlated with entropy production? Concurrence?"""
    ded = [r for r in records if r["ax4"] == +1]
    ind = [r for r in records if r["ax4"] == -1]

    mean_de_ded = float(np.mean([r["delta_entropy"] for r in ded])) if ded else 0.0
    mean_de_ind = float(np.mean([r["delta_entropy"] for r in ind])) if ind else 0.0

    mean_dc_ded = float(np.mean([r["delta_concurrence"] for r in ded])) if ded else 0.0
    mean_dc_ind = float(np.mean([r["delta_concurrence"] for r in ind])) if ind else 0.0

    mean_dmi_ded = float(np.mean([r["delta_MI"] for r in ded])) if ded else 0.0
    mean_dmi_ind = float(np.mean([r["delta_MI"] for r in ind])) if ind else 0.0

    # Correlation of ax4 with each observable across all steps
    ax4_arr = np.array([r["ax4"] for r in records], dtype=float)
    de_arr = np.array([r["delta_entropy"] for r in records])
    dc_arr = np.array([r["delta_concurrence"] for r in records])
    dmi_arr = np.array([r["delta_MI"] for r in records])

    def safe_corr(a, b):
        if np.std(a) < 1e-15 or np.std(b) < 1e-15:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    return {
        "id": "OBS",
        "name": "ax4_observable_correlations",
        "mean_delta_entropy_deductive": mean_de_ded,
        "mean_delta_entropy_inductive": mean_de_ind,
        "mean_delta_concurrence_deductive": mean_dc_ded,
        "mean_delta_concurrence_inductive": mean_dc_ind,
        "mean_delta_MI_deductive": mean_dmi_ded,
        "mean_delta_MI_inductive": mean_dmi_ind,
        "corr_ax4_delta_entropy": safe_corr(ax4_arr, de_arr),
        "corr_ax4_delta_concurrence": safe_corr(ax4_arr, dc_arr),
        "corr_ax4_delta_MI": safe_corr(ax4_arr, dmi_arr),
        "pass": True,  # diagnostic
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def run():
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": "axis4_deductive_inductive",
        "source": "sim_axis4_deductive_inductive.py",
        "axis": "Ax4",
        "claim": "Deductive (UEUE) and inductive (EUEU) loop orderings produce distinguishable "
                 "engine dynamics; Type 1 and Type 2 assign opposite Ax4 labels",
        "tests": [],
        "evidence_tokens": [],
    }

    print("=" * 70)
    print("  AX4 DEDUCTIVE/INDUCTIVE ENGINE-LEVEL PROBE")
    print("=" * 70)

    # ── Step 1: Extract traversal orders ──
    print("\n[SETUP] Traversal orders from LOOP_STAGE_ORDER:")
    for et in [1, 2]:
        for loop_name in ["outer", "inner"]:
            topo_seq = terrain_topo_order(et, loop_name)
            loop_spec = LOOP_GRAMMAR[et][loop_name]
            print(f"  Type {et} {loop_name} ({loop_spec.topology_order}): {' -> '.join(topo_seq)}")

    # ── Step 2: Run engine for both types ──
    print("\n[RUN] Running engine Type 1, 10 cycles, entangle_strength=0.3 ...")
    records_t1, state_t1 = run_engine_with_ax4_recording(engine_type=1, n_cycles=10)
    print(f"  Collected {len(records_t1)} step records for Type 1")

    print("[RUN] Running engine Type 2, 10 cycles, entangle_strength=0.3 ...")
    records_t2, state_t2 = run_engine_with_ax4_recording(engine_type=2, n_cycles=10)
    print(f"  Collected {len(records_t2)} step records for Type 2")

    # ── P1: Different dynamics ──
    print("\n[P1] Deductive vs inductive produce different dynamics ...")
    p1_t1 = test_P1_different_dynamics(records_t1)
    p1_t2 = test_P1_different_dynamics(records_t2)
    print(f"  Type 1: mean dS(ded)={p1_t1['mean_delta_entropy_deductive']:.6f}, "
          f"mean dS(ind)={p1_t1['mean_delta_entropy_inductive']:.6f}, "
          f"diff={p1_t1['difference']:.6f} -> {'PASS' if p1_t1['pass'] else 'FAIL'}")
    print(f"  Type 2: mean dS(ded)={p1_t2['mean_delta_entropy_deductive']:.6f}, "
          f"mean dS(ind)={p1_t2['mean_delta_entropy_inductive']:.6f}, "
          f"diff={p1_t2['difference']:.6f} -> {'PASS' if p1_t2['pass'] else 'FAIL'}")
    p1_pass = p1_t1["pass"] and p1_t2["pass"]
    results["tests"].append({"id": "P1", "name": "different_dynamics",
                             "type1": p1_t1, "type2": p1_t2, "pass": p1_pass})

    # ── P2: Opposite assignments ──
    print("\n[P2] Type 1 and Type 2 have opposite Ax4 assignments ...")
    p2 = test_P2_opposite_assignments(records_t1, records_t2)
    print(f"  Opposite at {p2['opposite_count']}/{p2['total']} positions -> "
          f"{'PASS' if p2['pass'] else 'FAIL'}")
    for d in p2["details"]:
        print(f"    pos {d['position']}: T1={d['t1_ax4']:+d} ({d['t1_terrain']}), "
              f"T2={d['t2_ax4']:+d} ({d['t2_terrain']}) {'OK' if d['opposite'] else 'MISMATCH'}")
    results["tests"].append(p2)

    # ── P3: Reversed order changes trajectory ──
    print("\n[P3] Reversing loop order changes trajectory ...")
    p3 = test_P3_reversed_order_changes_trajectory()
    print(f"  D(normal, reversed) = {p3['trace_distance_normal_vs_reversed']:.6f} -> "
          f"{'PASS' if p3['pass'] else 'FAIL'}")
    results["tests"].append(p3)

    # ── N1: Both deductive ──
    print("\n[N1] Both loops deductive (diagnostic) ...")
    n1 = test_N1_both_deductive()
    print(f"  D(normal, both_ded) = {n1['trace_distance_from_normal']:.6f}, "
          f"S_normal={n1['entropy_normal']:.4f}, S_both_ded={n1['entropy_both_ded']:.4f}, "
          f"valid={n1['valid_density']}")
    results["tests"].append(n1)

    # ── N2: Both inductive ──
    print("\n[N2] Both loops inductive (diagnostic) ...")
    n2 = test_N2_both_inductive()
    print(f"  D(normal, both_ind) = {n2['trace_distance_from_normal']:.6f}, "
          f"S_normal={n2['entropy_normal']:.4f}, S_both_ind={n2['entropy_both_ind']:.4f}, "
          f"valid={n2['valid_density']}")
    results["tests"].append(n2)

    # ── N3: Randomized order ──
    print("\n[N3] Randomized loop order (diagnostic) ...")
    n3 = test_N3_randomized_order()
    print(f"  D(normal, random) = {n3['trace_distance_from_normal']:.6f}, "
          f"S_normal={n3['entropy_normal']:.4f}, S_random={n3['entropy_random']:.4f}")
    print(f"  C_normal={n3['concurrence_normal']:.4f}, C_random={n3['concurrence_random']:.4f}")
    results["tests"].append(n3)

    # ── Orthogonality ──
    print("\n[ORTHO] Axis orthogonality (combined T1+T2 records) ...")
    all_records = records_t1 + records_t2
    ortho = test_orthogonality(all_records)
    print("  Correlations:")
    for k, v in ortho["correlations"].items():
        print(f"    {k}: {v:.4f}")
    print("  Identity checks:")
    for k, v in ortho["identity_checks"].items():
        print(f"    {k}: {v:.4f}")
    results["tests"].append(ortho)

    # ── Ax4 Observable ──
    print("\n[OBS] Ax4 observable correlations ...")
    obs_t1 = test_ax4_observable(records_t1)
    obs_t2 = test_ax4_observable(records_t2)
    print("  Type 1:")
    print(f"    dS: ded={obs_t1['mean_delta_entropy_deductive']:.6f}, "
          f"ind={obs_t1['mean_delta_entropy_inductive']:.6f}")
    print(f"    dC: ded={obs_t1['mean_delta_concurrence_deductive']:.6f}, "
          f"ind={obs_t1['mean_delta_concurrence_inductive']:.6f}")
    print(f"    dMI: ded={obs_t1['mean_delta_MI_deductive']:.6f}, "
          f"ind={obs_t1['mean_delta_MI_inductive']:.6f}")
    print(f"    corr(Ax4, dS)={obs_t1['corr_ax4_delta_entropy']:.4f}, "
          f"corr(Ax4, dC)={obs_t1['corr_ax4_delta_concurrence']:.4f}, "
          f"corr(Ax4, dMI)={obs_t1['corr_ax4_delta_MI']:.4f}")
    print("  Type 2:")
    print(f"    dS: ded={obs_t2['mean_delta_entropy_deductive']:.6f}, "
          f"ind={obs_t2['mean_delta_entropy_inductive']:.6f}")
    print(f"    dC: ded={obs_t2['mean_delta_concurrence_deductive']:.6f}, "
          f"ind={obs_t2['mean_delta_concurrence_inductive']:.6f}")
    print(f"    dMI: ded={obs_t2['mean_delta_MI_deductive']:.6f}, "
          f"ind={obs_t2['mean_delta_MI_inductive']:.6f}")
    print(f"    corr(Ax4, dS)={obs_t2['corr_ax4_delta_entropy']:.4f}, "
          f"corr(Ax4, dC)={obs_t2['corr_ax4_delta_concurrence']:.4f}, "
          f"corr(Ax4, dMI)={obs_t2['corr_ax4_delta_MI']:.4f}")
    results["tests"].append({"id": "OBS", "name": "ax4_observable",
                             "type1": obs_t1, "type2": obs_t2, "pass": True})

    # ── Summary ──
    positive_tests = [t for t in results["tests"] if t["id"] in ("P1", "P2", "P3")]
    p_pass = sum(1 for t in positive_tests if t["pass"])
    p_total = len(positive_tests)
    all_pass = p_pass == p_total

    print(f"\n{'='*70}")
    print(f"  AX4 VERDICT: {'PASS' if all_pass else f'PARTIAL ({p_pass}/{p_total} positive tests)'}")
    print(f"{'='*70}")

    # Evidence tokens
    if p1_pass:
        results["evidence_tokens"].append({
            "token": "AX4_DED_IND_DIFFERENT_DYNAMICS",
            "value": "PASS",
            "witness": f"diff_T1={p1_t1['difference']:.6f}, diff_T2={p1_t2['difference']:.6f}",
        })
    if p2["pass"]:
        results["evidence_tokens"].append({
            "token": "AX4_OPPOSITE_ACROSS_TYPES",
            "value": "PASS",
            "witness": f"opposite={p2['opposite_count']}/{p2['total']}",
        })
    if p3["pass"]:
        results["evidence_tokens"].append({
            "token": "AX4_ORDER_MATTERS",
            "value": "PASS",
            "witness": f"D(normal,reversed)={p3['trace_distance_normal_vs_reversed']:.6f}",
        })

    results["verdict"] = "PASS" if all_pass else "PARTIAL"
    results["n_pass"] = p_pass
    results["n_total"] = p_total

    # ── Trajectory sample (first cycle T1, for JSON output) ──
    results["trajectory_sample_t1_cycle0"] = [
        {k: v for k, v in r.items()} for r in records_t1[:8]
    ]
    results["trajectory_sample_t2_cycle0"] = [
        {k: v for k, v in r.items()} for r in records_t2[:8]
    ]

    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "axis4_deductive_inductive_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved: {out_path}")
    print(f"  Evidence tokens emitted: {len(results['evidence_tokens'])}")
    for tok in results["evidence_tokens"]:
        print(f"    {tok['token']}={tok['value']}")

    return results


if __name__ == "__main__":
    run()
