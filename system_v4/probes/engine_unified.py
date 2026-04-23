#!/usr/bin/env python3
"""
engine_unified.py
=================
Unified engine: Cl(6) multivector as PRIMARY state, bipartite spinor algebra
as BRIDGE to density matrices, TopoNetX cell complex as topology GATE.

Architecture:
  Cl(6) multivector (64 elements)     <- PRIMARY STATE
      | extract Bloch + correlation
  bipartite_spinor_algebra             <- BRIDGE (no kron)
      | derive
  4x4 rho_AB                          <- VALIDATION ONLY
      | compute
  I_c, concurrence, entropy           <- OBSERVABLES

Plus:
  - TopoNetX cell complex gates every move
  - Torus position (eta, theta, phi) determines rotor angles
"""

import json
import math
import os
import sys
import numpy as np
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_pure_clifford import (
    PureCliffordEngine, PureCliffordState,
    get_bloch_L, get_bloch_R, get_correlation_matrix,
    derive_rho_AB, concurrence_from_rho,
    berry_increment_subsystem,
)
from bipartite_spinor_algebra import (
    build_joint_density, partial_trace_A, partial_trace_B,
    concurrence_4x4, correlation_tensor, ensure_valid_density,
)
from toponetx_torus_bridge import (
    build_torus_complex, compute_shell_structure, map_engine_cycle_to_complex,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER
from hopf_manifold import TORUS_CLIFFORD


# =====================================================================
# Von Neumann entropy for arbitrary-size density matrix
# =====================================================================

def von_neumann_entropy(rho):
    """Von Neumann entropy S(rho) = -Tr(rho log2 rho) for any-size matrix."""
    rho = np.asarray(rho, dtype=complex)
    rho = (rho + rho.conj().T) / 2
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-15]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log2(evals)))


# =====================================================================
# Bloch-correlation to rho bridge (using bipartite algebra, no kron)
# =====================================================================

def bloch_correlation_to_rho(bL, bR, C):
    """Build rho_AB from Bloch vectors + FULL correlation tensor.

    rho = (I@I + bL.sigma@I + I@bR.sigma + sum C_ij sigma_i@sigma_j) / 4

    The Cl(6) cross-bivector components store the FULL correlation tensor
    T_ij (product part + excess). bipartite_spinor_algebra.build_joint_density
    expects (bL, bR, C_excess) where T_ij = outer(bL,bR) + C_excess.
    So we compute: C_excess = T - outer(bL, bR).
    """
    bL = np.asarray(bL, dtype=float)
    bR = np.asarray(bR, dtype=float)
    C = np.asarray(C, dtype=float)
    # In engine_pure_clifford, get_correlation_matrix returns the FULL T_ij
    # build_joint_density adds outer(bL,bR) + C_excess internally as T
    # So C_excess = T_full - outer(bL, bR)
    C_excess = C - np.outer(bL, bR)
    return build_joint_density(bL, bR, C_excess)


# =====================================================================
# UNIFIED ENGINE
# =====================================================================

class UnifiedEngine:
    """Unified engine: Cl(6) state + bipartite bridge + TopoNetX gating.

    The Cl(6) multivector is the PRIMARY state carrier. The bipartite
    algebra provides the BRIDGE to density matrices for validation and
    observable computation. The TopoNetX cell complex gates every move.
    """

    def __init__(self, engine_type=1):
        assert engine_type in (1, 2), "engine_type must be 1 or 2"
        self.engine_type = engine_type

        # Cl(6) engine for state and dynamics
        self.cl6 = PureCliffordEngine(engine_type)

        # TopoNetX cell complex for topology gating
        self.cc, self.node_map = build_torus_complex()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.path = map_engine_cycle_to_complex(self.cc, engine_type, self.node_map)

        # Precompute adjacency for gating
        self.adj = self.cc.adjacency_matrix(0)
        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        # Position tracking
        self.current_node = None
        self.move_log = []

    # ------------------------------------------------------------------
    # Adjacency check
    # ------------------------------------------------------------------

    def _is_adjacent(self, node_a, node_b):
        """Check whether two nodes are connected by a 1-cell."""
        if node_a == node_b:
            return True
        if node_a not in self._node_to_idx or node_b not in self._node_to_idx:
            return False
        ia = self._node_to_idx[node_a]
        ib = self._node_to_idx[node_b]
        return bool(self.adj[ia, ib])

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def init_state(self, eta=TORUS_CLIFFORD):
        """Initialize Cl(6) product state and set starting node."""
        state = self.cl6.init_state(eta)
        self.current_node = self.path[0]
        self.move_log = []
        return state

    # ------------------------------------------------------------------
    # Single stage with topology gating
    # ------------------------------------------------------------------

    def run_stage(self, state, stage_idx, step_in_cycle):
        """Run one stage: topology gate -> Cl(6) operator -> update position.

        Returns (state, legal: bool).
        """
        target = self.path[step_in_cycle % len(self.path)]

        # Check topology gate
        if not self._is_adjacent(self.current_node, target):
            self.move_log.append({
                'from': str(self.current_node),
                'to': str(target),
                'legal': False,
                'reason': 'not adjacent',
                'stage_idx': stage_idx,
            })
            return state, False

        # Apply Cl(6) operator (delegates to PureCliffordEngine)
        state = self.cl6.run_stage(state, stage_idx, step_in_cycle)

        # Update position
        prev = self.current_node
        self.current_node = target
        self.move_log.append({
            'from': str(prev),
            'to': str(target),
            'legal': True,
            'stage_idx': stage_idx,
        })

        return state, True

    # ------------------------------------------------------------------
    # Full cycle
    # ------------------------------------------------------------------

    def run_cycle(self, state):
        """Run one full 8-stage cycle, returns (state, legal_count)."""
        stage_order = LOOP_STAGE_ORDER[self.engine_type]
        legal_count = 0
        for step, si in enumerate(stage_order):
            state, legal = self.run_stage(state, si, step)
            if legal:
                legal_count += 1
        return state, legal_count

    # ------------------------------------------------------------------
    # Observables via bipartite bridge
    # ------------------------------------------------------------------

    def get_observables(self, state):
        """Extract all observables from Cl(6) state via bipartite bridge.

        Flow: Cl(6) -> extract Bloch + correlation -> bridge to rho_AB
              -> compute I_c, concurrence, entropy.
        """
        mv = state.mv_joint

        # 1. Extract from Cl(6) multivector
        bL = get_bloch_L(mv)
        bR = get_bloch_R(mv)
        C = get_correlation_matrix(mv)

        # 2. Bridge to rho via bipartite algebra (no kron)
        rho_AB = bloch_correlation_to_rho(bL, bR, C)

        # 3. Partial traces
        rho_A = partial_trace_B(rho_AB)
        rho_B = partial_trace_A(rho_AB)

        # 4. Entropies
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho_AB)

        # 5. Coherent information and mutual information
        I_c = S_B - S_AB
        MI = S_A + S_B - S_AB

        # 6. Concurrence via bipartite algebra (no kron)
        conc = concurrence_4x4(rho_AB)

        # 7. Cross-validation: concurrence from derive_rho_AB (uses kron)
        #    derive_rho_AB does NOT PSD-project, so negative eigenvalues
        #    can leak through. Apply ensure_valid_density for fair comparison.
        rho_AB_v = ensure_valid_density(derive_rho_AB(mv))
        conc_v = concurrence_4x4(rho_AB_v)

        return {
            'bloch_L': bL.tolist(),
            'bloch_R': bR.tolist(),
            'correlation_frobenius': float(np.linalg.norm(C, 'fro')),
            'concurrence': float(conc),
            'concurrence_validation': float(conc_v),
            'I_c': float(I_c),
            'MI': float(MI),
            'S_A': float(S_A),
            'S_B': float(S_B),
            'S_AB': float(S_AB),
            'berry_L': float(state.berry_L),
            'berry_R': float(state.berry_R),
            'eta': float(state.eta),
            'theta': float(state.theta),
            'phi': float(state.phi),
            'torus_level': state.torus_level,
            'purity_L': float(np.linalg.norm(bL)),
            'purity_R': float(np.linalg.norm(bR)),
        }


# =====================================================================
# COMPARISON: run engine_core for same 10 cycles
# =====================================================================

def run_engine_core_comparison(engine_type=1, n_cycles=10):
    """Run the engine_core GeometricEngine for comparison."""
    from engine_core import GeometricEngine

    eng = GeometricEngine(engine_type=engine_type)
    state = eng.init_state(eta=TORUS_CLIFFORD)

    results = []
    for cyc in range(n_cycles):
        state = eng.run_cycle(state)
        rho_AB = state.rho_AB
        rho_A = partial_trace_B(rho_AB)
        rho_B = partial_trace_A(rho_AB)
        S_A = von_neumann_entropy(rho_A)
        S_B = von_neumann_entropy(rho_B)
        S_AB = von_neumann_entropy(rho_AB)
        I_c = S_B - S_AB
        MI = S_A + S_B - S_AB
        conc = concurrence_4x4(rho_AB)

        results.append({
            'cycle': cyc + 1,
            'concurrence': float(conc),
            'I_c': float(I_c),
            'MI': float(MI),
            'S_A': float(S_A),
            'S_B': float(S_B),
            'S_AB': float(S_AB),
            'ga0_level': float(state.ga0_level),
        })

    return results


# =====================================================================
# VERIFICATION HARNESS
# =====================================================================

def run_verification(n_cycles=10):
    """Run 10 cycles of unified engine, collect all observables, compare."""
    print("=" * 72)
    print("UNIFIED ENGINE -- Cl(6) + Bipartite Bridge + TopoNetX Gating")
    print("=" * 72)
    print()

    results = {
        'engine_type': 1,
        'n_cycles': n_cycles,
        'cycles': [],
        'topology': {
            'total_moves': 0,
            'legal_moves': 0,
            'blocked_moves': 0,
        },
        'summary': {},
    }

    # --- Unified engine ---
    eng = UnifiedEngine(engine_type=1)
    state = eng.init_state(eta=TORUS_CLIFFORD)

    # Initial observables
    obs0 = eng.get_observables(state)
    print("INITIAL STATE:")
    print(f"  Bloch L = {obs0['bloch_L']}")
    print(f"  Bloch R = {obs0['bloch_R']}")
    print(f"  Concurrence = {obs0['concurrence']:.6f}")
    print(f"  I_c = {obs0['I_c']:.6f}")
    print()

    # Header
    print(f"{'Cyc':>3} | {'Conc':>7} {'Conc_v':>7} | {'I_c':>8} {'MI':>8} | "
          f"{'S_A':>6} {'S_B':>6} {'S_AB':>6} | {'Berry_L':>8} {'Berry_R':>8} | "
          f"{'Legal':>5}")
    print("-" * 95)

    peak_conc = 0.0
    peak_Ic = -999.0
    Ic_positive_count = 0

    for cyc in range(n_cycles):
        state, legal_count = eng.run_cycle(state)
        obs = eng.get_observables(state)
        obs['cycle'] = cyc + 1
        obs['legal_count'] = legal_count
        results['cycles'].append(obs)

        if obs['concurrence'] > peak_conc:
            peak_conc = obs['concurrence']
        if obs['I_c'] > peak_Ic:
            peak_Ic = obs['I_c']
        if obs['I_c'] > 0:
            Ic_positive_count += 1

        print(f"{cyc+1:>3} | {obs['concurrence']:>7.4f} {obs['concurrence_validation']:>7.4f} | "
              f"{obs['I_c']:>8.4f} {obs['MI']:>8.4f} | "
              f"{obs['S_A']:>6.4f} {obs['S_B']:>6.4f} {obs['S_AB']:>6.4f} | "
              f"{obs['berry_L']:>8.4f} {obs['berry_R']:>8.4f} | "
              f"{legal_count:>5}")

    print()

    # Topology summary
    total = len(eng.move_log)
    legal = sum(1 for m in eng.move_log if m['legal'])
    blocked = total - legal
    results['topology']['total_moves'] = total
    results['topology']['legal_moves'] = legal
    results['topology']['blocked_moves'] = blocked

    print(f"TOPOLOGY GATING:")
    print(f"  Total moves: {total}")
    print(f"  Legal moves: {legal}")
    print(f"  Blocked moves: {blocked}")
    if blocked > 0:
        blocked_reasons = [m.get('reason', '?') for m in eng.move_log if not m['legal']]
        from collections import Counter
        for reason, cnt in Counter(blocked_reasons).items():
            print(f"    {reason}: {cnt}")
    print()

    # Concurrence agreement check
    conc_diffs = [abs(c['concurrence'] - c['concurrence_validation']) for c in results['cycles']]
    max_conc_diff = max(conc_diffs)
    print(f"CONCURRENCE AGREEMENT (bridge vs derive_rho):")
    print(f"  Max difference: {max_conc_diff:.8f}")
    print(f"  Match: {'YES' if max_conc_diff < 1e-6 else 'NO (divergence detected)'}")
    print()

    # Key question results
    print(f"KEY QUESTIONS:")
    print(f"  Peak concurrence: {peak_conc:.6f}")
    print(f"  Peak I_c: {peak_Ic:.6f}")
    print(f"  I_c > 0 in {Ic_positive_count}/{n_cycles} cycles")
    print(f"  Berry_L final: {results['cycles'][-1]['berry_L']:.6f}")
    print(f"  Berry_R final: {results['cycles'][-1]['berry_R']:.6f}")
    print()

    results['summary'] = {
        'peak_concurrence': peak_conc,
        'peak_Ic': peak_Ic,
        'Ic_positive_count': Ic_positive_count,
        'max_concurrence_diff': max_conc_diff,
        'concurrence_matches': max_conc_diff < 1e-6,
        'berry_L_final': results['cycles'][-1]['berry_L'],
        'berry_R_final': results['cycles'][-1]['berry_R'],
        'moves_blocked': blocked,
    }

    # --- Engine core comparison ---
    print("=" * 72)
    print("ENGINE CORE COMPARISON (same 10 cycles, engine_type=1)")
    print("=" * 72)

    try:
        core_results = run_engine_core_comparison(engine_type=1, n_cycles=n_cycles)
        results['engine_core_comparison'] = core_results

        print(f"{'Cyc':>3} | {'Conc':>7} | {'I_c':>8} {'MI':>8} | "
              f"{'S_A':>6} {'S_B':>6} {'S_AB':>6} | {'ga0':>6}")
        print("-" * 70)
        for cr in core_results:
            print(f"{cr['cycle']:>3} | {cr['concurrence']:>7.4f} | "
                  f"{cr['I_c']:>8.4f} {cr['MI']:>8.4f} | "
                  f"{cr['S_A']:>6.4f} {cr['S_B']:>6.4f} {cr['S_AB']:>6.4f} | "
                  f"{cr['ga0_level']:>6.4f}")

        print()
        print("DIVERGENCE ANALYSIS (Unified vs Core):")
        for i, (u, c) in enumerate(zip(results['cycles'], core_results)):
            d_conc = abs(u['concurrence'] - c['concurrence'])
            d_Ic = abs(u['I_c'] - c['I_c'])
            if d_conc > 0.01 or d_Ic > 0.01:
                print(f"  Cycle {i+1}: delta_conc={d_conc:.4f}, delta_Ic={d_Ic:.4f}")

        # Summary of agreement
        conc_agree = all(
            abs(u['concurrence'] - c['concurrence']) < 0.1
            for u, c in zip(results['cycles'], core_results)
        )
        results['summary']['core_concurrence_agrees'] = conc_agree
        print(f"  Concurrence within 0.1: {'YES' if conc_agree else 'NO (expected -- different dynamics)'}")

    except Exception as exc:
        print(f"  Engine core comparison failed: {exc}")
        results['engine_core_comparison'] = {'error': str(exc)}

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == '__main__':
    results = run_verification(n_cycles=10)

    # Write output
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'a2_state', 'sim_results',
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'unified_engine_results.json')

    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
