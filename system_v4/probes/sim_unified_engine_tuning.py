#!/usr/bin/env python3
"""
sim_unified_engine_tuning.py
============================
Diagnostic + tuning probe for the unified engine.

Problem 1: 72.5% of moves topology-blocked (58/80)
  - fiber terrains map to layer 0, base terrains to layer 2
  - cell complex only has edges layer 0<->1, layer 1<->2
  - NO layer 0<->2 edge => fiber<->base transition always blocked
  - Fix: remap fiber terrains to layer 1 (Clifford ring)

Problem 2: I_c stays negative (dephasing dominates entangling)
  - Sweep dephasing strength and coupling strength
  - Find the boundary where I_c crosses zero
"""

import json
import math
import os
import sys
import copy
import numpy as np
from collections import Counter
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_pure_clifford import (
    PureCliffordEngine, PureCliffordState,
    get_bloch_L, get_bloch_R, get_correlation_matrix,
    derive_rho_AB, concurrence_from_rho,
    berry_increment_subsystem,
    _dephase_z_joint, _dephase_x_joint,
    _layout6, _scalar6, _L_basis, _R_basis,
    _IDX_CROSS,
)
from bipartite_spinor_algebra import (
    build_joint_density, partial_trace_A, partial_trace_B,
    concurrence_4x4, ensure_valid_density,
)
from toponetx.classes import CellComplex
from toponetx_torus_bridge import (
    build_torus_complex, compute_shell_structure, map_engine_cycle_to_complex,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER
from hopf_manifold import TORUS_CLIFFORD
from engine_unified import UnifiedEngine, von_neumann_entropy, bloch_correlation_to_rho


# =====================================================================
# PROBLEM 1: Diagnose why 72.5% of moves are blocked
# =====================================================================

def diagnose_path_blocking(engine_type=1):
    """Print the full path for a given engine type, showing which
    transitions are blocked and why."""
    print("=" * 72)
    print(f"PROBLEM 1: PATH BLOCKING DIAGNOSIS (Type {engine_type})")
    print("=" * 72)
    print()

    cc, node_map = build_torus_complex()
    path = map_engine_cycle_to_complex(cc, engine_type, node_map)
    stage_order = LOOP_STAGE_ORDER[engine_type]

    # Build adjacency lookup
    adj = cc.adjacency_matrix(0)
    node_list = sorted(cc.nodes)
    node_to_idx = {n: i for i, n in enumerate(node_list)}

    def is_adjacent(a, b):
        if a == b:
            return True
        if a not in node_to_idx or b not in node_to_idx:
            return False
        return bool(adj[node_to_idx[a], node_to_idx[b]])

    print(f"Stage order (terrain indices): {stage_order}")
    print(f"Path through cell complex:     {path}")
    print()

    # Print edges that exist between layers
    print("Cell complex inter-layer edges:")
    for layer in range(3):
        for next_layer in range(layer + 1, 3):
            count = 0
            for i in range(8):
                if is_adjacent((layer, i), (next_layer, i)):
                    count += 1
            if count > 0:
                print(f"  Layer {layer} <-> Layer {next_layer}: {count} edges")
            else:
                print(f"  Layer {layer} <-> Layer {next_layer}: NO EDGES")
    print()

    # Walk through one cycle showing each transition
    print(f"{'Step':>4} | {'Terrain':>6} | {'Loop':>5} | {'Target':>12} | {'From':>12} | {'Adjacent':>8} | Reason")
    print("-" * 85)

    blocked = 0
    total = 0
    current = path[0]

    for step, terrain_idx in enumerate(stage_order):
        terrain = TERRAINS[terrain_idx]
        target = path[step % len(path)]
        adj_ok = is_adjacent(current, target)
        total += 1

        reason = ""
        if not adj_ok:
            blocked += 1
            from_layer = current[0]
            to_layer = target[0]
            if from_layer != to_layer:
                layer_diff = abs(from_layer - to_layer)
                reason = f"layer jump {from_layer}->{to_layer} (diff={layer_diff}, no direct edge)"
            else:
                pos_diff = abs(current[1] - target[1])
                reason = f"same layer, position gap={pos_diff}"

        print(f"{step:>4} | {terrain['name']:>6} | {terrain['loop']:>5} | "
              f"{str(target):>12} | {str(current):>12} | "
              f"{'YES' if adj_ok else 'NO':>8} | {reason}")

        if adj_ok:
            current = target

    print()
    print(f"Single cycle: {blocked}/{total} blocked ({100*blocked/total:.1f}%)")
    print(f"Over 10 cycles: {blocked*10}/{total*10} blocked")
    print()
    return blocked, total


def diagnose_10_cycle_blocking(engine_type=1):
    """Run 10 actual cycles through UnifiedEngine and count blocks."""
    eng = UnifiedEngine(engine_type=engine_type)
    state = eng.init_state(eta=TORUS_CLIFFORD)

    for _ in range(10):
        state, _ = eng.run_cycle(state)

    total = len(eng.move_log)
    legal = sum(1 for m in eng.move_log if m['legal'])
    blocked = total - legal

    print(f"ACTUAL 10-cycle run (original mapping):")
    print(f"  Total moves: {total}")
    print(f"  Legal: {legal}")
    print(f"  Blocked: {blocked} ({100*blocked/total:.1f}%)")
    if blocked > 0:
        reasons = Counter(m.get('reason', '?') for m in eng.move_log if not m['legal'])
        for r, c in reasons.items():
            print(f"    {r}: {c}")
    print()
    return legal, total


# =====================================================================
# PROBLEM 1 FIX: Remap fiber -> layer 1 (Clifford ring)
# =====================================================================

def build_torus_complex_FIXED(n_per_ring=8, torus_levels=None):
    """Build cell complex with ADDED layer 0<->2 edges and
    diagonal edges (layer, i)<->(layer+1, (i+1)%8) for smooth traversal.

    Original complex only had:
      Within-ring: (layer, i) <-> (layer, (i+1)%8)
      Between-ring: (layer, i) <-> (layer+1, i)  [same position only]

    This blocked fiber<->base transitions because:
    1. fiber(layer 0) and base(layer 2) had no direct edges
    2. Even on adjacent layers, position changes during layer
       change had no edge

    Fix adds:
    - Layer 0<->2 edges at same position (skip connection)
    - Diagonal edges between adjacent layers: (l,i)<->(l+1,(i+1)%8)
      These represent the natural path of the engine traversing
      both the ring and the layer simultaneously.
    """
    from hopf_manifold import (
        torus_coordinates, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
        left_weyl_spinor, right_weyl_spinor,
    )

    if torus_levels is None:
        torus_levels = [
            ('inner', TORUS_INNER),
            ('clifford', TORUS_CLIFFORD),
            ('outer', TORUS_OUTER),
        ]

    cc = CellComplex()
    node_map = {}
    n_layers = len(torus_levels)

    # 0-cells
    for layer, (name, eta) in enumerate(torus_levels):
        for i in range(n_per_ring):
            theta = 2 * np.pi * i / n_per_ring
            node_id = (layer, i)
            cc.add_node(node_id)
            q = torus_coordinates(eta, theta, 0.0)
            node_map[node_id] = {
                'eta': eta, 'theta': theta, 'layer_name': name,
                'q': q,
                'psi_L': left_weyl_spinor(q),
                'psi_R': right_weyl_spinor(q),
            }

    # 1-cells: within-ring (original)
    for layer in range(n_layers):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cc.add_edge((layer, i), (layer, j))

    # 1-cells: between adjacent rings, same position (original)
    for layer in range(n_layers - 1):
        for i in range(n_per_ring):
            cc.add_edge((layer, i), (layer + 1, i))

    # 1-cells: NEW -- layer 0<->2 skip connections (same position)
    for i in range(n_per_ring):
        cc.add_edge((0, i), (2, i))

    # 1-cells: NEW -- diagonal edges between adjacent layers
    # (layer, i) <-> (layer+1, (i+1)%8) -- forward diagonal
    # (layer+1, i) <-> (layer, (i+1)%8) -- backward diagonal
    for layer in range(n_layers - 1):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cc.add_edge((layer, i), (layer + 1, j))
            cc.add_edge((layer + 1, i), (layer, j))

    # 1-cells: NEW -- diagonal edges layer 0<->2
    for i in range(n_per_ring):
        j = (i + 1) % n_per_ring
        cc.add_edge((0, i), (2, j))
        cc.add_edge((2, i), (0, j))

    # 2-cells: shell surfaces (original)
    for layer in range(n_layers - 1):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cell = [(layer, i), (layer, j), (layer + 1, j), (layer + 1, i)]
            cc.add_cell(cell, rank=2)

    return cc, node_map


def map_engine_cycle_to_complex_FIXED(cc, engine_type, node_map):
    """Fixed mapping: fiber -> layer 1 (Clifford), base -> layer 2 (outer).

    Combined with the enriched cell complex (diagonal edges), this
    ensures that transitions between layers at adjacent positions
    are legal moves.

    The path uses positions 0-7 sequentially. Base stages map to layer 2,
    fiber stages map to layer 1. The diagonal edges make the
    cross-layer transitions at adjacent positions legal.
    """
    stage_order = LOOP_STAGE_ORDER[engine_type]
    path = []
    for pos, terrain_idx in enumerate(stage_order):
        terrain = TERRAINS[terrain_idx]
        loop = terrain['loop']
        if loop == 'fiber':
            layer = 1   # Clifford ring
        else:
            layer = 2   # outer ring
        path.append((layer, pos % 8))
    return path


class UnifiedEngineFixed(UnifiedEngine):
    """UnifiedEngine with the fixed cell complex AND path mapping."""

    def __init__(self, engine_type=1):
        assert engine_type in (1, 2), "engine_type must be 1 or 2"
        self.engine_type = engine_type
        self.cl6 = PureCliffordEngine(engine_type)

        # Use the FIXED cell complex with enriched edges
        self.cc, self.node_map = build_torus_complex_FIXED()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.path = map_engine_cycle_to_complex_FIXED(
            self.cc, engine_type, self.node_map
        )

        self.adj = self.cc.adjacency_matrix(0)
        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        self.current_node = None
        self.move_log = []


def test_fixed_mapping(engine_type=1, n_cycles=10):
    """Run with the fixed fiber->layer1 mapping and report."""
    print("=" * 72)
    print(f"PROBLEM 1 FIX: fiber->layer 1, base->layer 2 (Type {engine_type})")
    print("=" * 72)
    print()

    eng = UnifiedEngineFixed(engine_type=engine_type)
    state = eng.init_state(eta=TORUS_CLIFFORD)

    # Show the new path
    print(f"Fixed path: {eng.path}")
    print()

    # Verify adjacency on the fixed path
    print("Transition check (single cycle):")
    current = eng.path[0]
    blocked = 0
    for step in range(len(eng.path)):
        target = eng.path[step]
        adj_ok = eng._is_adjacent(current, target)
        terrain_idx = LOOP_STAGE_ORDER[engine_type][step]
        terrain = TERRAINS[terrain_idx]
        status = "OK" if adj_ok else "BLOCKED"
        if not adj_ok:
            blocked += 1
        print(f"  Step {step}: {current} -> {target} [{terrain['name']}] {status}")
        if adj_ok:
            current = target
    print(f"  Single cycle: {blocked}/{len(eng.path)} blocked")
    print()

    # Run n_cycles
    state = eng.init_state(eta=TORUS_CLIFFORD)
    total_legal = 0
    cycle_obs = []

    for cyc in range(n_cycles):
        state, legal_count = eng.run_cycle(state)
        total_legal += legal_count
        obs = eng.get_observables(state)
        obs['cycle'] = cyc + 1
        obs['legal_count'] = legal_count
        cycle_obs.append(obs)

    total = len(eng.move_log)
    legal = sum(1 for m in eng.move_log if m['legal'])
    blocked = total - legal

    print(f"FIXED MAPPING -- {n_cycles} cycles:")
    print(f"  Total moves: {total}")
    print(f"  Legal: {legal} ({100*legal/total:.1f}%)")
    print(f"  Blocked: {blocked} ({100*blocked/total:.1f}%)")
    if blocked > 0:
        reasons = Counter(m.get('reason', '?') for m in eng.move_log if not m['legal'])
        for r, c in reasons.items():
            print(f"    {r}: {c}")
    print()

    # Show observables
    print(f"{'Cyc':>3} | {'Conc':>7} | {'I_c':>8} {'MI':>8} | "
          f"{'S_A':>6} {'S_B':>6} {'S_AB':>6} | {'Legal':>5}")
    print("-" * 70)
    for obs in cycle_obs:
        print(f"{obs['cycle']:>3} | {obs['concurrence']:>7.4f} | "
              f"{obs['I_c']:>8.4f} {obs['MI']:>8.4f} | "
              f"{obs['S_A']:>6.4f} {obs['S_B']:>6.4f} {obs['S_AB']:>6.4f} | "
              f"{obs['legal_count']:>5}")
    print()

    return {
        'total_moves': total,
        'legal_moves': legal,
        'blocked_moves': blocked,
        'block_rate': blocked / total if total > 0 else 0,
        'cycles': cycle_obs,
    }


# =====================================================================
# PROBLEM 2: Sweep dephasing and coupling strengths
# =====================================================================

class TunableCliffordEngine(PureCliffordEngine):
    """PureCliffordEngine with tunable dephasing and coupling multipliers."""

    def __init__(self, engine_type=1, dephasing_mult=1.0, coupling_mult=1.0):
        super().__init__(engine_type)
        self.dephasing_mult = dephasing_mult
        self.coupling_mult = coupling_mult

    def _apply_operator_cl6(self, mv, op_name, is_up, state, strength):
        """Override: scale dephasing by dephasing_mult."""
        from hopf_manifold import torus_radii
        R_maj, R_min = torus_radii(state.eta)
        sign = 1.0 if is_up else -1.0

        if op_name == "Ti":
            angle_L = sign * strength * R_min * 0.4
            angle_R = -sign * strength * R_min * 0.4
            deph = strength * R_min * 0.12 * self.dephasing_mult

            from engine_pure_clifford import (
                _rotor_L_z, _rotor_R_z, _apply_rotor,
            )
            R_L = _rotor_L_z(angle_L)
            mv = _apply_rotor(mv, R_L)
            R_R = _rotor_R_z(angle_R)
            mv = _apply_rotor(mv, R_R)
            mv = _dephase_z_joint(mv, deph, side='L')
            mv = _dephase_z_joint(mv, deph, side='R')

        elif op_name == "Fe":
            angle = sign * state.phi * strength * 0.5
            if abs(angle) < 1e-12:
                angle = sign * strength * 0.25
            from engine_pure_clifford import (
                _rotor_L_z, _rotor_R_z, _apply_rotor,
            )
            R_L = _rotor_L_z(angle)
            R_R = _rotor_R_z(-angle)
            mv = _apply_rotor(mv, R_L)
            mv = _apply_rotor(mv, R_R)

        elif op_name == "Te":
            angle_L = sign * strength * R_maj * 0.4
            angle_R = -sign * strength * R_maj * 0.4
            deph = strength * R_maj * 0.12 * self.dephasing_mult

            from engine_pure_clifford import (
                _rotor_L_x, _rotor_R_x, _apply_rotor,
            )
            R_L = _rotor_L_x(angle_L)
            mv = _apply_rotor(mv, R_L)
            R_R = _rotor_R_x(angle_R)
            mv = _apply_rotor(mv, R_R)
            mv = _dephase_x_joint(mv, deph, side='L')
            mv = _dephase_x_joint(mv, deph, side='R')

        elif op_name == "Fi":
            angle = sign * state.theta * strength * 0.5
            if abs(angle) < 1e-12:
                angle = sign * strength * 0.25
            from engine_pure_clifford import (
                _rotor_L_x, _rotor_R_x, _apply_rotor,
            )
            R_L = _rotor_L_x(angle)
            R_R = _rotor_R_x(-angle)
            mv = _apply_rotor(mv, R_L)
            mv = _apply_rotor(mv, R_R)

        else:
            raise ValueError(f"Unknown operator: {op_name}")

        return mv

    def _apply_entangling(self, mv, strength, state):
        """Override: scale coupling by coupling_mult."""
        scaled_strength = strength * self.coupling_mult
        return super()._apply_entangling(mv, scaled_strength, state)


class UnifiedEngineFixedTunable(UnifiedEngineFixed):
    """UnifiedEngine with fixed path AND tunable Cl(6) engine."""

    def __init__(self, engine_type=1, dephasing_mult=1.0, coupling_mult=1.0):
        # Need to build everything manually to inject TunableCliffordEngine
        self.engine_type = engine_type
        self.cl6 = TunableCliffordEngine(engine_type, dephasing_mult, coupling_mult)

        self.cc, self.node_map = build_torus_complex_FIXED()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.path = map_engine_cycle_to_complex_FIXED(
            self.cc, engine_type, self.node_map
        )

        self.adj = self.cc.adjacency_matrix(0)
        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        self.current_node = None
        self.move_log = []


def get_observables_from_state(eng, state):
    """Extract observables (lightweight version for sweeps)."""
    mv = state.mv_joint
    bL = get_bloch_L(mv)
    bR = get_bloch_R(mv)
    C = get_correlation_matrix(mv)

    rho_AB = bloch_correlation_to_rho(bL, bR, C)
    rho_A = partial_trace_B(rho_AB)
    rho_B = partial_trace_A(rho_AB)

    S_A = von_neumann_entropy(rho_A)
    S_B = von_neumann_entropy(rho_B)
    S_AB = von_neumann_entropy(rho_AB)

    I_c = S_B - S_AB
    conc = concurrence_4x4(rho_AB)

    return {
        'I_c': float(I_c),
        'S_A': float(S_A),
        'S_B': float(S_B),
        'S_AB': float(S_AB),
        'concurrence': float(conc),
        'corr_frobenius': float(np.linalg.norm(C, 'fro')),
    }


def sweep_dephasing(n_cycles=10):
    """Sweep dephasing strength, hold coupling fixed."""
    print("=" * 72)
    print("PROBLEM 2a: DEPHASING SWEEP (coupling_mult=1.0)")
    print("=" * 72)
    print()

    dephasing_values = [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
    results = []

    print(f"{'Deph':>6} | ", end="")
    for cyc in range(1, n_cycles + 1):
        print(f"{'C'+str(cyc)+' I_c':>10}", end="")
    print()
    print("-" * (8 + 10 * n_cycles))

    for deph in dephasing_values:
        eng = UnifiedEngineFixedTunable(
            engine_type=1, dephasing_mult=deph, coupling_mult=1.0
        )
        state = eng.init_state(eta=TORUS_CLIFFORD)

        cycle_Ic = []
        for cyc in range(n_cycles):
            state, legal = eng.run_cycle(state)
            obs = get_observables_from_state(eng, state)
            cycle_Ic.append(obs['I_c'])

        print(f"{deph:>6.2f} | ", end="")
        for ic in cycle_Ic:
            print(f"{ic:>10.4f}", end="")
        print()

        ever_positive = any(ic > 0 for ic in cycle_Ic)
        results.append({
            'dephasing_mult': deph,
            'coupling_mult': 1.0,
            'I_c_per_cycle': cycle_Ic,
            'I_c_final': cycle_Ic[-1],
            'I_c_ever_positive': ever_positive,
        })

    print()
    positive_at = [r['dephasing_mult'] for r in results if r['I_c_ever_positive']]
    if positive_at:
        print(f"I_c goes positive at dephasing_mult: {positive_at}")
    else:
        print("I_c NEVER goes positive in any dephasing sweep point")
    print()

    return results


def sweep_coupling(n_cycles=10):
    """Sweep coupling strength, hold dephasing fixed at baseline."""
    print("=" * 72)
    print("PROBLEM 2b: COUPLING SWEEP (dephasing_mult=1.0)")
    print("=" * 72)
    print()

    coupling_values = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
    results = []

    print(f"{'Coup':>6} | ", end="")
    for cyc in range(1, n_cycles + 1):
        print(f"{'C'+str(cyc)+' I_c':>10}", end="")
    print()
    print("-" * (8 + 10 * n_cycles))

    for coup in coupling_values:
        eng = UnifiedEngineFixedTunable(
            engine_type=1, dephasing_mult=1.0, coupling_mult=coup
        )
        state = eng.init_state(eta=TORUS_CLIFFORD)

        cycle_Ic = []
        for cyc in range(n_cycles):
            state, legal = eng.run_cycle(state)
            obs = get_observables_from_state(eng, state)
            cycle_Ic.append(obs['I_c'])

        print(f"{coup:>6.1f} | ", end="")
        for ic in cycle_Ic:
            print(f"{ic:>10.4f}", end="")
        print()

        ever_positive = any(ic > 0 for ic in cycle_Ic)
        results.append({
            'dephasing_mult': 1.0,
            'coupling_mult': coup,
            'I_c_per_cycle': cycle_Ic,
            'I_c_final': cycle_Ic[-1],
            'I_c_ever_positive': ever_positive,
        })

    print()
    positive_at = [r['coupling_mult'] for r in results if r['I_c_ever_positive']]
    if positive_at:
        print(f"I_c goes positive at coupling_mult: {positive_at}")
    else:
        print("I_c NEVER goes positive in any coupling sweep point")
    print()

    return results


def sweep_2d(n_cycles=10):
    """2D sweep: dephasing x coupling, 7x6 = 42 points.
    Record final I_c for each."""
    print("=" * 72)
    print("PROBLEM 2c: 2D SWEEP (dephasing x coupling)")
    print("=" * 72)
    print()

    dephasing_values = [0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
    coupling_values = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0]

    grid = []

    # Header
    print(f"{'':>6} |", end="")
    for c in coupling_values:
        print(f"  coup={c:<4.1f}", end="")
    print()
    print("-" * (8 + 11 * len(coupling_values)))

    for deph in dephasing_values:
        print(f"d={deph:<4.2f} |", end="")
        row = []
        for coup in coupling_values:
            eng = UnifiedEngineFixedTunable(
                engine_type=1, dephasing_mult=deph, coupling_mult=coup
            )
            state = eng.init_state(eta=TORUS_CLIFFORD)

            for cyc in range(n_cycles):
                state, _ = eng.run_cycle(state)

            obs = get_observables_from_state(eng, state)
            ic = obs['I_c']
            conc = obs['concurrence']

            marker = "+" if ic > 0 else "-"
            print(f"  {ic:>+7.4f}{marker}", end="")

            row.append({
                'dephasing_mult': deph,
                'coupling_mult': coup,
                'I_c_final': ic,
                'concurrence_final': conc,
                'I_c_positive': ic > 0,
            })
        grid.append(row)
        print()

    print()

    # Find the zero-crossing boundary
    print("ZERO-CROSSING BOUNDARY (I_c > 0):")
    found_any = False
    for row in grid:
        for pt in row:
            if pt['I_c_positive']:
                found_any = True
                print(f"  deph={pt['dephasing_mult']:.2f}, coup={pt['coupling_mult']:.1f} -> "
                      f"I_c={pt['I_c_final']:.4f}, conc={pt['concurrence_final']:.4f}")
    if not found_any:
        print("  NO points with I_c > 0 found in sweep.")
        print("  Investigating: what are the peak I_c values?")
        best = max((pt for row in grid for pt in row), key=lambda x: x['I_c_final'])
        print(f"  Best: deph={best['dephasing_mult']:.2f}, coup={best['coupling_mult']:.1f} "
              f"-> I_c={best['I_c_final']:.6f}")
    print()

    return grid


def sweep_extreme(n_cycles=10):
    """Extreme sweep: dephasing=0, coupling up to 20x.
    Tests whether the architecture CAN produce positive I_c at all."""
    print("=" * 72)
    print("PROBLEM 2d: EXTREME SWEEP (dephasing=0, high coupling)")
    print("=" * 72)
    print()

    coupling_values = [0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    results = []

    print(f"{'Coup':>6} | ", end="")
    for cyc in range(1, n_cycles + 1):
        print(f"{'C'+str(cyc)+' I_c':>10}", end="")
    print(f" | {'Peak':>8}")
    print("-" * (8 + 10 * n_cycles + 11))

    for coup in coupling_values:
        eng = UnifiedEngineFixedTunable(
            engine_type=1, dephasing_mult=0.0, coupling_mult=coup
        )
        state = eng.init_state(eta=TORUS_CLIFFORD)

        cycle_Ic = []
        for cyc in range(n_cycles):
            state, _ = eng.run_cycle(state)
            obs = get_observables_from_state(eng, state)
            cycle_Ic.append(obs['I_c'])

        peak = max(cycle_Ic)
        print(f"{coup:>6.1f} | ", end="")
        for ic in cycle_Ic:
            print(f"{ic:>10.4f}", end="")
        marker = " <-- POSITIVE!" if peak > 0 else ""
        print(f" | {peak:>8.4f}{marker}")

        results.append({
            'dephasing_mult': 0.0,
            'coupling_mult': coup,
            'I_c_per_cycle': cycle_Ic,
            'peak_I_c': peak,
            'ever_positive': peak > 0,
        })

    print()
    any_pos = any(r['ever_positive'] for r in results)
    if any_pos:
        best = max(results, key=lambda r: r['peak_I_c'])
        print(f"I_c CAN go positive! Best: coup={best['coupling_mult']:.1f}, "
              f"peak I_c={best['peak_I_c']:.6f}")
    else:
        print("I_c NEVER positive even with zero dephasing + 20x coupling.")
        print("ROOT CAUSE: the engine architecture itself creates net decoherence.")
        print("The opposite-chirality L/R rotations anti-correlate the subsystems.")
    print()
    return results


class EntangleAllEngine(TunableCliffordEngine):
    """Cl(6) engine that applies entangling on ALL stages, not just Fe/Fi."""

    def run_stage(self, state, stage_idx, stage_position):
        """Override: apply entangling after EVERY operator, not just Fe/Fi."""
        terrain = TERRAINS[stage_idx]
        key = (self.engine_type, terrain['loop'], terrain['topo'])
        op_name, is_up = STAGE_OPERATOR_LUT[key]
        strength = self._operator_strength(terrain, op_name)

        mv_old = state.mv_joint + 0 * _scalar6

        # Apply local operator
        state.mv_joint = self._apply_operator_cl6(
            state.mv_joint, op_name, is_up, state, strength
        )

        # Entangling coupling on ALL stages (not just Fe/Fi)
        coupling_strength = strength * 0.6
        state.mv_joint = self._apply_entangling(
            state.mv_joint, coupling_strength, state
        )

        # Advance torus angles
        d_angle = self.d_angle * strength
        if terrain['loop'] == 'fiber':
            state.theta = (state.theta + d_angle) % (2 * math.pi)
        else:
            state.phi = (state.phi + d_angle) % (2 * math.pi)

        # Berry phase
        state.berry_L += berry_increment_subsystem(mv_old, state.mv_joint, 'L')
        state.berry_R += berry_increment_subsystem(mv_old, state.mv_joint, 'R')

        # Transport
        state = self._check_transport(state, stage_position)

        return state


class UnifiedEngineEntangleAll(UnifiedEngineFixed):
    """Unified engine with fixed topology AND entangling on all stages."""

    def __init__(self, engine_type=1, dephasing_mult=1.0, coupling_mult=1.0):
        self.engine_type = engine_type
        self.cl6 = EntangleAllEngine(engine_type, dephasing_mult, coupling_mult)

        self.cc, self.node_map = build_torus_complex_FIXED()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.path = map_engine_cycle_to_complex_FIXED(
            self.cc, engine_type, self.node_map
        )

        self.adj = self.cc.adjacency_matrix(0)
        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        self.current_node = None
        self.move_log = []


def sweep_entangle_all_stages(n_cycles=10):
    """Test entangling on ALL stages (not just Fe/Fi) with dephasing=0."""
    print("=" * 72)
    print("PROBLEM 2e: ENTANGLE ALL STAGES (dephasing=0)")
    print("=" * 72)
    print()

    coupling_values = [0.5, 1.0, 2.0, 5.0, 10.0]
    results = []

    print(f"{'Coup':>6} | ", end="")
    for cyc in range(1, n_cycles + 1):
        print(f"{'C'+str(cyc)+' I_c':>10}", end="")
    print(f" | {'Peak':>8} {'Conc':>7}")
    print("-" * (8 + 10 * n_cycles + 20))

    for coup in coupling_values:
        eng = UnifiedEngineEntangleAll(
            engine_type=1, dephasing_mult=0.0, coupling_mult=coup
        )
        state = eng.init_state(eta=TORUS_CLIFFORD)

        cycle_Ic = []
        cycle_conc = []
        for cyc in range(n_cycles):
            state, _ = eng.run_cycle(state)
            obs = get_observables_from_state(eng, state)
            cycle_Ic.append(obs['I_c'])
            cycle_conc.append(obs['concurrence'])

        peak_ic = max(cycle_Ic)
        peak_conc = max(cycle_conc)
        print(f"{coup:>6.1f} | ", end="")
        for ic in cycle_Ic:
            print(f"{ic:>10.4f}", end="")
        marker = " <-- POS" if peak_ic > 0 else ""
        print(f" | {peak_ic:>8.4f} {peak_conc:>7.4f}{marker}")

        results.append({
            'dephasing_mult': 0.0,
            'coupling_mult': coup,
            'entangle_all': True,
            'I_c_per_cycle': cycle_Ic,
            'concurrence_per_cycle': cycle_conc,
            'peak_I_c': peak_ic,
            'peak_concurrence': peak_conc,
            'ever_positive': peak_ic > 0,
        })

    print()
    any_pos = any(r['ever_positive'] for r in results)
    if any_pos:
        best = max(results, key=lambda r: r['peak_I_c'])
        print(f"I_c positive with entangle-all! coup={best['coupling_mult']:.1f}, "
              f"peak I_c={best['peak_I_c']:.6f}, peak conc={best['peak_concurrence']:.6f}")
    else:
        print("I_c STILL negative even with entangle-all + zero dephasing.")
    print()
    return results


# =====================================================================
# MAIN
# =====================================================================

def main():
    results = {}

    # --- Problem 1: Diagnosis ---
    blocked_single, total_single = diagnose_path_blocking(engine_type=1)
    legal_actual, total_actual = diagnose_10_cycle_blocking(engine_type=1)

    results['problem1_diagnosis'] = {
        'single_cycle_blocked': blocked_single,
        'single_cycle_total': total_single,
        'ten_cycle_legal': legal_actual,
        'ten_cycle_total': total_actual,
        'ten_cycle_block_rate': (total_actual - legal_actual) / total_actual,
    }

    # --- Problem 1: Fix ---
    fix_results = test_fixed_mapping(engine_type=1, n_cycles=10)
    results['problem1_fix'] = fix_results

    # --- Problem 2: Dephasing sweep ---
    deph_results = sweep_dephasing(n_cycles=10)
    results['problem2_dephasing_sweep'] = deph_results

    # --- Problem 2: Coupling sweep ---
    coup_results = sweep_coupling(n_cycles=10)
    results['problem2_coupling_sweep'] = coup_results

    # --- Problem 2: 2D sweep ---
    grid_results = sweep_2d(n_cycles=10)
    results['problem2_2d_sweep'] = grid_results

    # --- Problem 2: Extreme sweep (dephasing=0, high coupling) ---
    extreme_results = sweep_extreme(n_cycles=10)
    results['problem2_extreme_sweep'] = extreme_results

    # --- Problem 2: Entangle-all-stages sweep ---
    entangle_all_results = sweep_entangle_all_stages(n_cycles=10)
    results['problem2_entangle_all'] = entangle_all_results

    # --- Write output ---
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'a2_state', 'sim_results',
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'unified_engine_tuning_results.json')

    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")

    return results


if __name__ == '__main__':
    main()
