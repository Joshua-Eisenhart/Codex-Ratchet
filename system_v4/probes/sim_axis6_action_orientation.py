#!/usr/bin/env python3
"""
sim_axis6_action_orientation.py
===============================
Axis 6 -- Action Orientation in Cl(6)
--------------------------------------
Axis 6 distinguishes LEFT multiplication (pre-composition, Axis 6-UP)
from RIGHT multiplication (post-composition, Axis 6-DOWN).

In the Clifford algebra the geometric product is non-commutative, so:
  LEFT  (UP):   R * M * ~R
  RIGHT (DOWN): ~R * M * R
produce genuinely different results for generic M and R.

This SIM:
  P1  Left != Right for generic rotor+state
  P2  Difference depends on STATE (sweep Bloch sphere)
  P3  8-stage cycle: all-left vs mixed vs all-right
  P4  Axis 6 orthogonal to Axis 0 (coherent information)
  N1  Commuting algebra kills Axis 6
  N2  Identity operator trivialises Axis 6
  Token-order mapping for all 16 stages
  Magnitude comparison Axis 6 vs Axis 0
"""

import json
import math
import os
import sys
import copy
import numpy as np
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_pure_clifford import (
    PureCliffordEngine, PureCliffordState,
    _layout6, _blades6, _scalar6,
    e1, e2, e3, e4, e5, e6,
    e12, e23, e13, e45, e56, e46,
    e14, e25, e36,
    _L_basis, _R_basis,
    _rotor, _apply_rotor,
    _rotor_L_z, _rotor_L_x, _rotor_R_z, _rotor_R_x,
    _rotor_entangle_zz,
    get_bloch_L, get_bloch_R, get_correlation_matrix,
    derive_rho_AB, concurrence_from_rho,
    berry_increment, berry_increment_subsystem,
    _IDX_SCALAR, _IDX_L, _IDX_R, _IDX_CROSS,
    _dephase_z_joint,
)

from engine_core import (
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER,
    LOOP_GRAMMAR,
)

from hopf_manifold import (
    von_neumann_entropy_2x2, density_to_bloch,
    TORUS_CLIFFORD,
)

# =====================================================================
# AXIS 6 CORE:  left action vs right action
# =====================================================================

def apply_left(R, mv):
    """Axis 6-UP: left sandwich product  R * mv * ~R"""
    return R * mv * ~R


def apply_right(R, mv):
    """Axis 6-DOWN: right sandwich product  ~R * mv * R"""
    return ~R * mv * R


# =====================================================================
# TRACE DISTANCE between two Cl(6) multivector states
# =====================================================================

def trace_distance_mv(mv_a, mv_b):
    """Trace distance via the derived 4x4 density matrices."""
    rho_a = derive_rho_AB(mv_a)
    rho_b = derive_rho_AB(mv_b)
    diff = rho_a - rho_b
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def coherent_information(mv):
    """Axis 0 proxy: I_c = S(R) - S(AB).
    Positive => quantum capacity; sign distinguishes Axis 0 UP/DOWN."""
    rho_AB = derive_rho_AB(mv)
    # Partial trace to get rho_R
    rho_R = np.array([
        [rho_AB[0, 0] + rho_AB[1, 1], rho_AB[0, 2] + rho_AB[1, 3]],
        [rho_AB[2, 0] + rho_AB[3, 1], rho_AB[2, 2] + rho_AB[3, 3]],
    ], dtype=complex)
    rho_R = (rho_R + rho_R.conj().T) / 2.0
    tr = np.real(np.trace(rho_R))
    if abs(tr) > 1e-14:
        rho_R = rho_R / tr

    def _vn(rho):
        ev = np.linalg.eigvalsh(rho)
        ev = ev[ev > 1e-14]
        return float(-np.sum(ev * np.log2(ev)))

    S_R = _vn(rho_R)
    S_AB = _vn(rho_AB)
    return S_R - S_AB


# =====================================================================
# MAKE INITIAL STATE HELPER
# =====================================================================

def _make_state(engine, bloch_L=None, bloch_R=None):
    """Build a PureCliffordState from explicit Bloch vectors."""
    state = engine.init_state()
    if bloch_L is not None or bloch_R is not None:
        bL = bloch_L if bloch_L is not None else np.array([0.0, 0.0, 1.0])
        bR = bloch_R if bloch_R is not None else np.array([0.0, 0.0, 1.0])
        mv = _scalar6 * 1.0
        for i, v in enumerate(bL):
            mv = mv + float(v) * _L_basis[i]
        for j, v in enumerate(bR):
            mv = mv + float(v) * _R_basis[j]
        for i in range(3):
            for j in range(3):
                bv = _L_basis[i] ^ _R_basis[j]
                mv = mv + float(bL[i] * bR[j]) * bv
        state.mv_joint = mv
    return state


def _deep_copy_state(state):
    """Deep copy a PureCliffordState, handling the clifford MultiVector."""
    new_mv = _layout6.MultiVector(value=state.mv_joint.value.copy())
    return PureCliffordState(
        mv_joint=new_mv,
        eta=state.eta,
        theta=state.theta,
        phi=state.phi,
        berry_L=state.berry_L,
        berry_R=state.berry_R,
        torus_level=state.torus_level,
        history=list(state.history),
    )


# =====================================================================
# P1: Left != Right for generic rotor + state
# =====================================================================

def test_P1():
    """Apply same rotor with left vs right action. They must differ."""
    engine = PureCliffordEngine(engine_type=1)
    state = _make_state(engine, bloch_L=np.array([1.0, 0.0, 0.0]),
                        bloch_R=np.array([0.0, 1.0, 0.0]))
    mv = state.mv_joint

    # Use a non-trivial rotor: 45-degree rotation in e1-e2 plane
    R = _rotor(math.pi / 4, e12)

    mv_left = apply_left(R, mv)
    mv_right = apply_right(R, mv)

    td = trace_distance_mv(mv_left, mv_right)
    passed = td > 1e-6

    print(f"  P1  left!=right  td={td:.6f}  {'PASS' if passed else 'FAIL'}")
    return {"pass": passed, "trace_distance": round(td, 8)}


# =====================================================================
# P2: State dependence -- sweep Bloch sphere
# =====================================================================

def test_P2():
    """Sweep L Bloch vector on great circle; measure left-right td at each."""
    engine = PureCliffordEngine(engine_type=1)
    R = _rotor(math.pi / 4, e12)

    angles = [i * math.pi / 12 for i in range(25)]  # 0 to 2pi
    tds = []

    for a in angles:
        bL = np.array([math.sin(a), 0.0, math.cos(a)])
        bR = np.array([0.0, 0.0, 1.0])
        st = _make_state(engine, bloch_L=bL, bloch_R=bR)
        mv_l = apply_left(R, st.mv_joint)
        mv_r = apply_right(R, st.mv_joint)
        td = trace_distance_mv(mv_l, mv_r)
        tds.append(round(td, 8))

    # At a=0 (aligned with z, rotor in xy plane) the L Bloch is along z;
    # e12 rotation purely mixes x<->y so z component unchanged -- left=right
    # for the z-aligned part.  Max td should be away from poles.
    max_td = max(tds)
    min_td = min(tds)
    state_dependent = (max_td - min_td) > 1e-4

    print(f"  P2  state_dep  max_td={max_td:.6f} min_td={min_td:.6f}  "
          f"{'PASS' if state_dependent else 'FAIL'}")
    return {
        "bloch_sweep": [round(a, 4) for a in angles],
        "td_per_angle": tds,
        "max_td": max_td,
        "min_td": min_td,
        "state_dependent": state_dependent,
    }


# =====================================================================
# P3: 8-stage cycle comparison  (all-left, mixed, all-right)
# =====================================================================

def _run_cycle_with_axis6(engine, state, n_cycles, action_mode):
    """Run n_cycles through the engine with explicit Axis 6 control.

    action_mode: 'left', 'right', or 'mixed'

    In 'mixed' mode, deductive loop stages -> left, inductive -> right.
    """
    loop_grammar = LOOP_GRAMMAR[engine.engine_type]
    # Build set of terrain indices per loop role
    deductive_terrains = set()
    inductive_terrains = set()
    for lspec in loop_grammar.values():
        if lspec.topology_order == "deduction":
            deductive_terrains.update(lspec.terrain_indices)
        else:
            inductive_terrains.update(lspec.terrain_indices)

    for _cycle in range(n_cycles):
        for pos, ti in enumerate(LOOP_STAGE_ORDER[engine.engine_type]):
            terrain = TERRAINS[ti]
            key = (engine.engine_type, terrain['loop'], terrain['topo'])
            op_name, is_up = STAGE_OPERATOR_LUT[key]
            strength = engine._operator_strength(terrain, op_name)

            # Determine action orientation
            if action_mode == 'left':
                use_left = True
            elif action_mode == 'right':
                use_left = False
            else:  # mixed
                use_left = (ti in deductive_terrains)

            # Build the operator rotor(s) matching _apply_operator_cl6
            sign = 1.0 if is_up else -1.0
            from hopf_manifold import torus_radii
            R_maj, R_min = torus_radii(state.eta)

            mv = state.mv_joint
            if op_name == "Ti":
                angle_L = sign * strength * R_min * 0.4
                angle_R = -sign * strength * R_min * 0.4
                deph = strength * R_min * 0.12
                RL = _rotor_L_z(angle_L)
                RR = _rotor_R_z(angle_R)
                if use_left:
                    mv = apply_left(RL, mv)
                    mv = apply_left(RR, mv)
                else:
                    mv = apply_right(RL, mv)
                    mv = apply_right(RR, mv)
                mv = _dephase_z_joint(mv, deph, side='L')
                mv = _dephase_z_joint(mv, deph, side='R')

            elif op_name == "Fe":
                angle = sign * state.phi * strength * 0.5
                if abs(angle) < 1e-12:
                    angle = sign * strength * 0.25
                RL = _rotor_L_z(angle)
                RR = _rotor_R_z(-angle)
                if use_left:
                    mv = apply_left(RL, mv)
                    mv = apply_left(RR, mv)
                else:
                    mv = apply_right(RL, mv)
                    mv = apply_right(RR, mv)

            elif op_name == "Te":
                angle_L = sign * strength * R_maj * 0.4
                angle_R = -sign * strength * R_maj * 0.4
                deph = strength * R_maj * 0.12
                RL = _rotor_L_x(angle_L)
                RR = _rotor_R_x(angle_R)
                if use_left:
                    mv = apply_left(RL, mv)
                    mv = apply_left(RR, mv)
                else:
                    mv = apply_right(RL, mv)
                    mv = apply_right(RR, mv)
                from engine_pure_clifford import _dephase_x_joint
                mv = _dephase_x_joint(mv, deph, side='L')
                mv = _dephase_x_joint(mv, deph, side='R')

            elif op_name == "Fi":
                angle = sign * state.theta * strength * 0.5
                if abs(angle) < 1e-12:
                    angle = sign * strength * 0.25
                RL = _rotor_L_x(angle)
                RR = _rotor_R_x(-angle)
                if use_left:
                    mv = apply_left(RL, mv)
                    mv = apply_left(RR, mv)
                else:
                    mv = apply_right(RL, mv)
                    mv = apply_right(RR, mv)

            state.mv_joint = mv

            # Entangling for F-kernels
            if op_name in ("Fe", "Fi"):
                coupling = strength * 0.6
                state.mv_joint = engine._apply_entangling(
                    state.mv_joint, coupling, state)

            # Advance angles
            d_angle = engine.d_angle * strength
            if terrain['loop'] == 'fiber':
                state.theta = (state.theta + d_angle) % (2 * math.pi)
            else:
                state.phi = (state.phi + d_angle) % (2 * math.pi)

    return state


def _extract_observables(mv):
    """Concurrence, Berry (total), VN entropy of partial trace."""
    rho_AB = derive_rho_AB(mv)
    conc = concurrence_from_rho(rho_AB)

    rho_L = np.array([
        [rho_AB[0, 0] + rho_AB[2, 2], rho_AB[0, 1] + rho_AB[2, 3]],
        [rho_AB[1, 0] + rho_AB[3, 2], rho_AB[1, 1] + rho_AB[3, 3]],
    ], dtype=complex)
    rho_L = (rho_L + rho_L.conj().T) / 2.0
    tr = np.real(np.trace(rho_L))
    if abs(tr) > 1e-14:
        rho_L = rho_L / tr

    entropy = von_neumann_entropy_2x2(rho_L)
    return conc, entropy


def test_P3():
    """Compare all-left, mixed, all-right over 5 cycles."""
    n_cycles = 5
    results = {}

    for mode in ('left', 'mixed', 'right'):
        label = f"all_{mode}" if mode != 'mixed' else 'mixed'
        engine = PureCliffordEngine(engine_type=1)
        state = engine.init_state()
        state = _run_cycle_with_axis6(engine, state, n_cycles, mode)
        conc, entropy = _extract_observables(state.mv_joint)

        # Berry phase: run again collecting increments
        engine2 = PureCliffordEngine(engine_type=1)
        st2 = engine2.init_state()
        mv_prev = _layout6.MultiVector(value=st2.mv_joint.value.copy())
        total_berry = 0.0
        # Quick approximation: run 1 cycle, sum berry increments
        for pos, ti in enumerate(LOOP_STAGE_ORDER[engine2.engine_type]):
            st2 = engine2.run_stage(st2, ti, pos)
        total_berry = st2.berry_L + st2.berry_R

        results[label] = {
            "concurrence": round(float(conc), 8),
            "berry_approx": round(float(total_berry), 8),
            "entropy": round(float(entropy), 8),
        }
        print(f"  P3  {label:10s}  conc={conc:.6f}  ent={entropy:.6f}")

    # They should differ
    vals = [results[k]['concurrence'] for k in results]
    differ = not (abs(vals[0] - vals[1]) < 1e-8 and abs(vals[1] - vals[2]) < 1e-8)
    print(f"  P3  differ={differ}")
    results["differ"] = differ
    return results


# =====================================================================
# P4: Axis 6 orthogonal to Axis 0
# =====================================================================

def test_P4():
    """Sweep rotor angle, compute Axis 0 (I_c) and Axis 6 (td).
    They should NOT correlate."""
    engine = PureCliffordEngine(engine_type=1)

    angles = [i * math.pi / 8 for i in range(17)]
    ic_vals = []
    td_vals = []

    for a in angles:
        st = _make_state(engine,
                         bloch_L=np.array([math.sin(a), 0.0, math.cos(a)]),
                         bloch_R=np.array([0.0, math.sin(a), math.cos(a)]))
        R = _rotor(math.pi / 3, e12)
        mv_l = apply_left(R, st.mv_joint)
        mv_r = apply_right(R, st.mv_joint)
        td = trace_distance_mv(mv_l, mv_r)
        ic = coherent_information(mv_l)
        td_vals.append(td)
        ic_vals.append(ic)

    # Pearson correlation
    td_arr = np.array(td_vals)
    ic_arr = np.array(ic_vals)
    if np.std(td_arr) < 1e-12 or np.std(ic_arr) < 1e-12:
        corr = 0.0
    else:
        corr = float(np.corrcoef(td_arr, ic_arr)[0, 1])

    orthogonal = abs(corr) < 0.5  # weak or no correlation
    print(f"  P4  corr(Ax6,Ax0)={corr:.4f}  orthogonal={orthogonal}")
    return {
        "correlation": round(corr, 6),
        "orthogonal": orthogonal,
        "td_samples": [round(v, 6) for v in td_vals],
        "ic_samples": [round(v, 6) for v in ic_vals],
    }


# =====================================================================
# N1: Commuting algebra kills Axis 6
# =====================================================================

def test_N1():
    """With Z-only operators (all commuting), left = right."""
    engine = PureCliffordEngine(engine_type=1)
    state = _make_state(engine, bloch_L=np.array([0.3, 0.4, 0.5]),
                        bloch_R=np.array([0.1, 0.2, 0.9]))
    mv = state.mv_joint

    # Commuting rotor: Z-rotation only for BOTH L and R
    # e12 commutes with e3, e45 commutes with e6
    # But e12 does NOT commute with e1, e2 -- which is exactly the point.
    # For a truly commuting test: use a state aligned purely along z (e3, e6)
    # and a z-rotation (e12).  Then the rotor commutes with the state.
    bL_z = np.array([0.0, 0.0, 1.0])
    bR_z = np.array([0.0, 0.0, 1.0])
    st_z = _make_state(engine, bloch_L=bL_z, bloch_R=bR_z)
    mv_z = st_z.mv_joint

    R_z = _rotor_L_z(0.7)  # arbitrary angle
    mv_left = apply_left(R_z, mv_z)
    mv_right = apply_right(R_z, mv_z)
    td = trace_distance_mv(mv_left, mv_right)

    passed = td < 1e-6
    print(f"  N1  commuting  td={td:.10f}  {'PASS' if passed else 'FAIL'}")
    return {"left_eq_right": passed, "td": round(td, 10)}


# =====================================================================
# N2: Identity operator trivialises Axis 6
# =====================================================================

def test_N2():
    """Identity rotor: left = right trivially."""
    engine = PureCliffordEngine(engine_type=1)
    state = _make_state(engine, bloch_L=np.array([0.3, 0.7, 0.5]),
                        bloch_R=np.array([0.6, 0.2, 0.4]))
    mv = state.mv_joint

    R_id = _scalar6 * 1.0  # identity rotor
    mv_left = apply_left(R_id, mv)
    mv_right = apply_right(R_id, mv)
    td = trace_distance_mv(mv_left, mv_right)

    passed = td < 1e-10
    print(f"  N2  identity   td={td:.12f}  {'PASS' if passed else 'FAIL'}")
    return {"left_eq_right": passed, "td": round(td, 12)}


# =====================================================================
# TOKEN ORDER MAPPING  -- 16 stages
# =====================================================================

def build_token_mapping():
    """Map each of the 16 stage tokens to Axis 6 orientation.

    Operator-first token (e.g. TiSe) = Axis 6-UP  (left action)
    Topology-first token (e.g. SeFi) = Axis 6-DOWN (right action)
    """
    topologies = {"Ne", "Si", "Se", "Ni"}
    operators = {"Ti", "Te", "Fi", "Fe"}

    type_1_tokens = [
        "TiSe", "SeFi", "NeTi", "FiNe",
        "NiFe", "TeNi", "FeSi", "SiTe",
    ]
    type_2_tokens = [
        "FiSe", "SeTi", "TeSi", "SiFe",
        "NiTe", "FeNi", "NeFi", "TiNe",
    ]

    mapping = {"type_1": {}, "type_2": {}}
    up_count = 0
    down_count = 0

    for token in type_1_tokens:
        first = token[:2]
        if first in operators:
            mapping["type_1"][token] = "UP"
            up_count += 1
        else:
            mapping["type_1"][token] = "DOWN"
            down_count += 1

    for token in type_2_tokens:
        first = token[:2]
        if first in operators:
            mapping["type_2"][token] = "UP"
            up_count += 1
        else:
            mapping["type_2"][token] = "DOWN"
            down_count += 1

    balanced = (up_count == 8 and down_count == 8)
    print(f"  TOKEN  UP={up_count} DOWN={down_count}  balanced={balanced}")
    return {
        "type_1": mapping["type_1"],
        "type_2": mapping["type_2"],
        "total_up": up_count,
        "total_down": down_count,
        "balanced": balanced,
    }


# =====================================================================
# MAGNITUDE: Axis 6 effect size and ratio to Axis 0
# =====================================================================

def test_magnitude():
    """Run 10 cycles each way, measure max trace distance per cycle."""
    n_cycles = 10
    engine = PureCliffordEngine(engine_type=1)

    # Run all-left trajectory
    st_left = engine.init_state()
    st_right = engine.init_state()
    st_mixed = engine.init_state()

    max_tds = []
    ic_range_samples = []

    for cyc in range(n_cycles):
        st_left = _run_cycle_with_axis6(engine, st_left, 1, 'left')
        st_right = _run_cycle_with_axis6(engine, st_right, 1, 'right')
        st_mixed = _run_cycle_with_axis6(engine, st_mixed, 1, 'mixed')

        td_lr = trace_distance_mv(st_left.mv_joint, st_right.mv_joint)
        max_tds.append(round(float(td_lr), 8))

        ic_l = coherent_information(st_left.mv_joint)
        ic_r = coherent_information(st_right.mv_joint)
        ic_range_samples.append(round(abs(ic_l - ic_r), 8))

    # Axis 0 magnitude: I_c range across a sweep
    engine_sweep = PureCliffordEngine(engine_type=1)
    ic_values = []
    for i in range(8):
        st = engine_sweep.init_state()
        for _ in range(i + 1):
            st = engine_sweep.run_cycle(st)
        ic_values.append(coherent_information(st.mv_joint))

    ax0_range = max(ic_values) - min(ic_values) if ic_values else 0.0
    ax6_max = max(max_tds) if max_tds else 0.0
    ratio = ax6_max / ax0_range if abs(ax0_range) > 1e-12 else float('inf')

    print(f"  MAG  ax6_max_td={ax6_max:.6f}  ax0_range={ax0_range:.6f}  ratio={ratio:.4f}")
    return {
        "max_td_per_cycle": max_tds,
        "ax0_ic_range": round(ax0_range, 8),
        "axis6_vs_axis0_ratio": round(ratio, 6) if not math.isinf(ratio) else "inf",
    }


# =====================================================================
# SANITIZE for JSON
# =====================================================================

def _sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return _sanitize(obj.tolist())
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


# =====================================================================
# MAIN
# =====================================================================

def main():
    print(f"\n{'='*60}")
    print("AXIS 6 -- ACTION ORIENTATION (LEFT vs RIGHT) in Cl(6)")
    print(f"{'='*60}\n")

    # Positive tests
    p1 = test_P1()
    p2 = test_P2()
    p3 = test_P3()
    p4 = test_P4()

    # Negative tests
    n1 = test_N1()
    n2 = test_N2()

    # Token mapping
    tokens = build_token_mapping()

    # Magnitude
    mag = test_magnitude()

    results = {
        "name": "axis6_action_orientation",
        "definition": "Left (Arho) vs Right (rhoA) multiplication under noncommutation",
        "positive": {
            "P1_left_ne_right": p1,
            "P2_state_dependence": p2,
            "P3_cycle_comparison": {
                "all_left": p3.get("all_left", {}),
                "mixed": p3.get("mixed", {}),
                "all_right": p3.get("all_right", {}),
                "differ": p3.get("differ", False),
            },
            "P4_orthogonal_to_axis0": p4,
        },
        "negative": {
            "N1_commuting_kills": n1,
            "N2_identity_trivial": n2,
        },
        "token_mapping": tokens,
        "magnitude": mag,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    results = _sanitize(results)

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "axis6_action_orientation_results.json",
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n  Results -> {out_file}")

    # Summary
    all_pass = (
        p1["pass"]
        and p2["state_dependent"]
        and p3["differ"]
        and p4["orthogonal"]
        and n1["left_eq_right"]
        and n2["left_eq_right"]
        and tokens["balanced"]
    )
    print(f"\n  ALL TESTS: {'PASS' if all_pass else 'FAIL'}")
    return results


if __name__ == "__main__":
    main()
