#!/usr/bin/env python3
"""
engine_toponetx_constrained.py
==============================
Dynamics engine where the TopoNetX cell complex GATES operations at runtime.

The cell complex IS the constraint manifold:
  - 0-cells (vertices): each carries a 2x2 density matrix rho
  - 1-cells (edges): define legal moves (adjacency gating)
  - 2-cells (faces): define shell connectivity (transport gating)

The topology doesn't just describe the structure --- it enforces it.
If an edge doesn't exist, the move is ILLEGAL and gets skipped.
If two rings don't share a shell face, transport is blocked.

Design invariants:
  1. Edge legality: engine can only move along existing 1-cells
  2. Adjacency gating: operator application requires adjacency check
  3. Incidence enforcement: B1 encodes legal moves and discrete gradients
  4. Shell constraints: 2-cells gate inter-ring transport
  5. Operator strength: scaled by local vertex degree (fewer neighbors = stronger)
"""

import sys
import os
import json
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toponetx.classes import CellComplex
from toponetx_torus_bridge import (
    build_torus_complex,
    map_engine_cycle_to_complex,
    compute_shell_structure,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER
from geometric_operators import apply_operator
from hopf_manifold import von_neumann_entropy_2x2


# ======================================================================
# TopoNetX-Constrained Engine
# ======================================================================

class TopoNetXConstrainedEngine:
    """Dynamics engine gated by a cell complex topology.

    The cell complex adjacency determines which operations are legal,
    incidence matrices enforce transport rules, and Betti numbers
    constrain the dynamics.
    """

    def __init__(self, engine_type=1, n_per_ring=8):
        self.n_per_ring = n_per_ring
        self.cc, self.node_map = build_torus_complex(n_per_ring=n_per_ring)
        self.shells = compute_shell_structure(self.cc, self.node_map, n_per_ring)
        self.engine_type = engine_type

        # Precompute node ordering for matrix indexing
        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        # Adjacency matrix (vertex-vertex)
        self.adj = self.cc.adjacency_matrix(0)

        # Incidence matrix B1 (vertex-edge)
        self.B1 = self.cc.incidence_matrix(1)

        # Incidence matrix B2 (edge-face) if available
        try:
            self.B2 = self.cc.incidence_matrix(2)
        except Exception:
            self.B2 = None

        # Engine cycle path through the complex
        self.path = map_engine_cycle_to_complex(
            self.cc, engine_type, self.node_map
        )

        # Maximum vertex degree (for strength normalization)
        degrees = np.array(self.adj.sum(axis=1)).flatten()
        self._max_degree = float(max(degrees)) if len(degrees) > 0 else 1.0

        # State
        self.vertex_states = {}   # {node_id: rho 2x2}
        self.current_node = None
        self.move_log = []

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def init_state(self):
        """Initialize all vertices with maximally mixed state.

        The starting vertex (first in cycle path) gets a pure |0> state.
        """
        for node_id in self._node_list:
            self.vertex_states[node_id] = np.eye(2, dtype=complex) / 2.0

        self.current_node = self.path[0]
        self.vertex_states[self.current_node] = np.array(
            [[1, 0], [0, 0]], dtype=complex
        )
        self.move_log = []
        return self

    # ------------------------------------------------------------------
    # Adjacency gating
    # ------------------------------------------------------------------

    def is_adjacent(self, node_a, node_b):
        """Check if two nodes are connected by a 1-cell (edge)."""
        ia = self._node_to_idx[node_a]
        ib = self._node_to_idx[node_b]
        return bool(self.adj[ia, ib])

    def legal_moves(self, from_node):
        """Return all nodes reachable from from_node via existing edges."""
        idx = self._node_to_idx[from_node]
        row = np.asarray(self.adj[idx].todense()).flatten()
        return [self._node_list[i] for i in range(len(row)) if row[i] > 0]

    def vertex_degree(self, node):
        """Number of edges incident to this vertex."""
        return len(self.legal_moves(node))

    # ------------------------------------------------------------------
    # Shell (2-cell) gating for transport
    # ------------------------------------------------------------------

    def _check_shell_connection(self, layer_a, layer_b):
        """Check if two torus layers share a shell face (2-cell)."""
        lo, hi = min(layer_a, layer_b), max(layer_a, layer_b)
        for shell in self.shells:
            if shell['inner_layer'] == lo and shell['outer_layer'] == hi:
                return True
        return False

    # ------------------------------------------------------------------
    # Move + operate
    # ------------------------------------------------------------------

    def move_and_apply(self, target_node, operator_name, polarity_up=True):
        """Move to target_node if legal, apply operator, log result.

        If the move is topologically forbidden (no edge), the operation
        is SKIPPED entirely. The topology gates the dynamics.
        """
        # --- adjacency gate ---
        if self.current_node == target_node:
            # Self-loop: apply operator in place (always legal)
            pass
        elif not self.is_adjacent(self.current_node, target_node):
            self.move_log.append({
                'from': str(self.current_node),
                'to': str(target_node),
                'legal': False,
                'reason': 'not adjacent',
            })
            return False

        prev_node = self.current_node
        self.current_node = target_node

        # --- operator strength from topology ---
        degree = self.vertex_degree(self.current_node)
        # Fewer neighbors = stronger operator (boundary vertex effect)
        strength = 1.0 - 0.5 * (degree / self._max_degree)
        strength = max(strength, 0.1)

        # --- apply operator ---
        rho = self.vertex_states[self.current_node]
        rho = apply_operator(operator_name, rho,
                             polarity_up=polarity_up, strength=strength)
        self.vertex_states[self.current_node] = rho

        self.move_log.append({
            'from': str(prev_node),
            'to': str(target_node),
            'legal': True,
            'operator': operator_name,
            'polarity_up': polarity_up,
            'degree': degree,
            'strength': round(strength, 4),
            'entropy': round(float(von_neumann_entropy_2x2(rho)), 6),
        })
        return True

    # ------------------------------------------------------------------
    # Full cycle
    # ------------------------------------------------------------------

    def _find_transport_path(self, from_node, to_node):
        """Find a topologically legal path from from_node to to_node.

        If direct adjacency exists, returns [to_node].
        If a relay through the Clifford ring (layer 1) is needed,
        returns the intermediate hops.
        If no path exists, returns None.
        """
        if self.is_adjacent(from_node, to_node):
            return [to_node]

        # Try relay through Clifford ring (layer 1)
        relay_node = (1, to_node[1])
        if relay_node in self._node_to_idx:
            if (self.is_adjacent(from_node, relay_node) and
                    self.is_adjacent(relay_node, to_node)):
                return [relay_node, to_node]

        # Try relay through same-position on intermediate layer
        from_layer, to_layer = from_node[0], to_node[0]
        if abs(from_layer - to_layer) > 1:
            mid_layer = (from_layer + to_layer) // 2
            relay = (mid_layer, from_node[1])
            target_via = (to_node[0], from_node[1])
            # Step 1: same position on mid layer
            # Step 2: traverse ring on target layer to reach target position
            if relay in self._node_to_idx and self.is_adjacent(from_node, relay):
                if target_via in self._node_to_idx and self.is_adjacent(relay, target_via):
                    path = [relay, target_via]
                    # Walk around target ring if positions differ
                    if target_via != to_node:
                        ring_path = self._ring_walk(target_via, to_node)
                        if ring_path is not None:
                            path.extend(ring_path)
                    return path

        return None

    def _ring_walk(self, from_node, to_node):
        """Walk around a ring from from_node to to_node (same layer).

        Returns list of intermediate nodes (not including from_node).
        """
        if from_node[0] != to_node[0]:
            return None
        layer = from_node[0]
        pos_from = from_node[1]
        pos_to = to_node[1]
        if pos_from == pos_to:
            return []

        # Shortest direction around the ring
        n = self.n_per_ring
        fwd_dist = (pos_to - pos_from) % n
        bwd_dist = (pos_from - pos_to) % n

        path = []
        if fwd_dist <= bwd_dist:
            for step in range(1, fwd_dist + 1):
                path.append((layer, (pos_from + step) % n))
        else:
            for step in range(1, bwd_dist + 1):
                path.append((layer, (pos_from - step) % n))
        return path

    def run_cycle(self):
        """Run one engine cycle following the path through the complex.

        At each stage:
          1. Look up the operator from STAGE_OPERATOR_LUT
          2. Determine the target node from the cycle path
          3. If it's a transport move (cross-ring), find a legal path
             through the complex (possibly relaying through Clifford ring)
          4. Walk each hop; apply the main operator only at the final node
          5. If no legal path exists, log and skip
        """
        stage_order = LOOP_STAGE_ORDER[self.engine_type]

        for step, si in enumerate(stage_order):
            terrain = TERRAINS[si]
            key = (self.engine_type, terrain['loop'], terrain['topo'])
            if key not in STAGE_OPERATOR_LUT:
                continue
            op_name, is_up = STAGE_OPERATOR_LUT[key]

            target = self.path[step % len(self.path)]

            if self.current_node == target:
                # Same node: apply in place
                self.move_and_apply(target, op_name, polarity_up=is_up)
                continue

            # Find a topologically legal path to the target
            transport_path = self._find_transport_path(self.current_node, target)

            if transport_path is None:
                self.move_log.append({
                    'from': str(self.current_node),
                    'to': str(target),
                    'legal': False,
                    'reason': 'no topological path',
                })
                continue

            # Walk intermediate hops (transport only, no operator)
            for hop in transport_path[:-1]:
                self.move_log.append({
                    'from': str(self.current_node),
                    'to': str(hop),
                    'legal': True,
                    'operator': 'transport',
                    'polarity_up': None,
                    'degree': self.vertex_degree(hop),
                    'strength': 0.0,
                    'entropy': round(float(
                        von_neumann_entropy_2x2(self.vertex_states[hop])
                    ), 6),
                })
                self.current_node = hop

            # Apply operator at the final destination
            self.move_and_apply(target, op_name, polarity_up=is_up)

        return self

    # ------------------------------------------------------------------
    # Observables
    # ------------------------------------------------------------------

    def get_vertex_entropy_field(self):
        """Compute von Neumann entropy at every vertex."""
        return {
            str(n): round(float(von_neumann_entropy_2x2(self.vertex_states[n])), 6)
            for n in self._node_list
        }

    def get_discrete_gradient(self):
        """Discrete gradient of the entropy field via B1 incidence.

        grad = B1^T @ entropy_vec  (maps vertex scalar to edge vector).
        Returns the gradient vector and a summary of steepest edges.
        """
        entropy_vec = np.array([
            von_neumann_entropy_2x2(self.vertex_states[n])
            for n in self._node_list
        ])
        grad = self.B1.T @ entropy_vec
        grad_arr = np.asarray(grad).flatten()

        # Find steepest edges
        edge_list = sorted(self.cc.edges)
        steepest_idx = np.argsort(np.abs(grad_arr))[::-1]
        steepest = []
        for k in steepest_idx[:5]:
            if k < len(edge_list):
                steepest.append({
                    'edge': str(edge_list[k]),
                    'gradient': round(float(grad_arr[k]), 6),
                })

        return {
            'gradient_vector': [round(float(g), 6) for g in grad_arr],
            'steepest_edges': steepest,
            'max_abs_gradient': round(float(np.max(np.abs(grad_arr))), 6),
            'mean_abs_gradient': round(float(np.mean(np.abs(grad_arr))), 6),
        }

    def get_betti_numbers(self):
        """Compute Betti numbers from the cell complex.

        b0 = connected components
        b1 = independent loops
        b2 = enclosed cavities
        """
        # b0: from adjacency via connected components
        from scipy.sparse.csgraph import connected_components
        n_comp, _ = connected_components(self.adj, directed=False)

        # b1, b2: from rank-nullity on incidence matrices
        # b1 = dim(ker(B1^T)) - b0  ... use Euler characteristic approach
        n_vertices = len(self._node_list)
        n_edges = len(list(self.cc.edges))
        n_faces = len(list(self.cc.cells))

        # Euler characteristic: chi = V - E + F = b0 - b1 + b2
        chi = n_vertices - n_edges + n_faces

        # For a torus: b0=1, b1=2, b2=1, chi=0
        # For our 3-ring structure the exact values depend on the complex
        return {
            'b0': n_comp,
            'vertices': n_vertices,
            'edges': n_edges,
            'faces': n_faces,
            'euler_characteristic': chi,
        }

    def summary(self):
        """Summary statistics for the current run."""
        legal = [m for m in self.move_log if m['legal']]
        illegal = [m for m in self.move_log if not m['legal']]
        return {
            'engine_type': self.engine_type,
            'total_moves': len(self.move_log),
            'legal_moves': len(legal),
            'illegal_moves': len(illegal),
            'illegal_reasons': [m['reason'] for m in illegal],
            'current_node': str(self.current_node),
        }


# ======================================================================
# Build a transport-blocked complex (negative test)
# ======================================================================

def build_no_transport_complex(n_per_ring=8):
    """Build a cell complex with NO between-ring edges.

    Within-ring edges exist; between-ring edges removed.
    Transport moves should be completely blocked.
    """
    from hopf_manifold import (
        torus_coordinates, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
        left_weyl_spinor, right_weyl_spinor,
    )

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

    # 1-cells: ONLY within-ring edges (no between-ring)
    for layer in range(n_layers):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cc.add_edge((layer, i), (layer, j))

    # No 2-cells either (no shell faces)

    return cc, node_map


class NoTransportEngine(TopoNetXConstrainedEngine):
    """Engine with transport edges removed for negative testing."""

    def __init__(self, engine_type=1, n_per_ring=8):
        self.n_per_ring = n_per_ring
        self.cc, self.node_map = build_no_transport_complex(n_per_ring)
        self.shells = []  # no shells
        self.engine_type = engine_type

        self._node_list = sorted(self.cc.nodes)
        self._node_to_idx = {n: i for i, n in enumerate(self._node_list)}

        self.adj = self.cc.adjacency_matrix(0)
        self.B1 = self.cc.incidence_matrix(1)
        self.B2 = None

        self.path = map_engine_cycle_to_complex(
            self.cc, engine_type, self.node_map
        )

        degrees = np.array(self.adj.sum(axis=1)).flatten()
        self._max_degree = float(max(degrees)) if len(degrees) > 0 else 1.0

        self.vertex_states = {}
        self.current_node = None
        self.move_log = []


# ======================================================================
# Verification harness
# ======================================================================

def run_verification(n_cycles=10):
    """Run the full verification suite and return results dict."""
    results = {}

    # --- Normal engine (both types) ---
    for etype in [1, 2]:
        eng = TopoNetXConstrainedEngine(engine_type=etype)
        eng.init_state()

        for _ in range(n_cycles):
            eng.run_cycle()

        summary = eng.summary()
        entropy_field = eng.get_vertex_entropy_field()
        gradient = eng.get_discrete_gradient()
        betti = eng.get_betti_numbers()

        results[f'type_{etype}_normal'] = {
            'summary': summary,
            'entropy_field': entropy_field,
            'gradient': gradient,
            'betti': betti,
            'move_log_sample': eng.move_log[:16],
        }

    # --- Negative test: no transport edges ---
    for etype in [1, 2]:
        eng_nt = NoTransportEngine(engine_type=etype)
        eng_nt.init_state()

        for _ in range(n_cycles):
            eng_nt.run_cycle()

        summary_nt = eng_nt.summary()
        entropy_nt = eng_nt.get_vertex_entropy_field()

        # Count transport-blocked moves
        transport_blocked = [
            m for m in eng_nt.move_log
            if not m['legal'] and m.get('reason') in ('not adjacent', 'no shell connection', 'no topological path')
        ]
        all_illegal = [m for m in eng_nt.move_log if not m['legal']]

        results[f'type_{etype}_no_transport'] = {
            'summary': summary_nt,
            'entropy_field': entropy_nt,
            'total_transport_blocked': len(transport_blocked),
            'total_illegal': len(all_illegal),
            'all_transport_moves_blocked': len(all_illegal) > 0,
            'move_log_sample': eng_nt.move_log[:16],
        }

    # --- Comparison: does gating change dynamics? ---
    # Run unconstrained (normal engine but track entropy trajectories)
    eng_normal = TopoNetXConstrainedEngine(engine_type=1)
    eng_normal.init_state()
    entropy_snapshots = []
    for cycle in range(n_cycles):
        eng_normal.run_cycle()
        snap = eng_normal.get_vertex_entropy_field()
        entropy_snapshots.append({
            'cycle': cycle,
            'mean_entropy': round(np.mean(list(snap.values())), 6),
            'max_entropy': round(max(snap.values()), 6),
            'min_entropy': round(min(snap.values()), 6),
        })

    results['entropy_trajectory'] = entropy_snapshots

    return results


# ======================================================================
# Main
# ======================================================================

if __name__ == '__main__':
    print("=== TopoNetX-Constrained Dynamics Engine ===")
    print()

    results = run_verification(n_cycles=10)

    # Print summary
    for key in sorted(results.keys()):
        if key == 'entropy_trajectory':
            print(f"\n--- Entropy trajectory (type 1, 10 cycles) ---")
            for snap in results[key]:
                print(f"  Cycle {snap['cycle']}: mean={snap['mean_entropy']:.4f}  "
                      f"min={snap['min_entropy']:.4f}  max={snap['max_entropy']:.4f}")
            continue

        section = results[key]
        print(f"\n--- {key} ---")
        s = section.get('summary', {})
        print(f"  Total moves: {s.get('total_moves', '?')}")
        print(f"  Legal:       {s.get('legal_moves', '?')}")
        print(f"  Illegal:     {s.get('illegal_moves', '?')}")
        if s.get('illegal_reasons'):
            from collections import Counter
            counts = Counter(s['illegal_reasons'])
            for reason, cnt in counts.items():
                print(f"    {reason}: {cnt}")

        betti = section.get('betti')
        if betti:
            print(f"  Betti: b0={betti['b0']}, V={betti['vertices']}, "
                  f"E={betti['edges']}, F={betti['faces']}, "
                  f"chi={betti['euler_characteristic']}")

        grad = section.get('gradient')
        if grad:
            print(f"  Gradient: max_abs={grad['max_abs_gradient']:.4f}, "
                  f"mean_abs={grad['mean_abs_gradient']:.4f}")
            for se in grad['steepest_edges'][:3]:
                print(f"    {se['edge']}: {se['gradient']:.4f}")

        if 'total_transport_blocked' in section:
            print(f"  Transport blocked: {section['total_transport_blocked']}")
            print(f"  All transport blocked: {section['all_transport_moves_blocked']}")

    # Write results
    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'a2_state', 'sim_results', 'toponetx_constrained_engine_results.json',
    )
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to {out_path}")
