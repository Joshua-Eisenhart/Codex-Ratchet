#!/usr/bin/env python3
"""
engine_graph_driven.py
======================
Graph-driven dynamics engine where PyG HeteroData IS the computation.

The graph adjacency determines which operations can follow which.
Message passing propagates state through the graph.  State lives on
nodes; operations happen along edges; the graph structure constrains
what is possible.

Node types  (from pyg_engine_bridge):
    terrain  – 8 nodes, each carries live quantum state
    operator – 4 nodes, each carries application metadata
    torus    – 3 nodes (inner / Clifford / outer)

Edge types that DRIVE dynamics:
    (terrain, sequence, terrain)      – traversal order
    (terrain, assigned_to, operator)  – which op acts on which terrain
    (terrain, sits_on, torus)         – torus level binding
    (torus, transport, torus)         – inter-torus transport paths
"""

import sys
import os
import copy
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyg_engine_bridge import (
    build_engine_graph, attach_engine_state,
    TERRAIN_NAMES, OPERATOR_NAMES, TORUS_LEVELS,
)
from engine_core import (
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER,
    GeometricEngine, EngineState,
)
from geometric_operators import (
    apply_operator, partial_trace_A, partial_trace_B,
    _ensure_valid_density, OPERATOR_MAP_4X4,
)
from hopf_manifold import (
    von_neumann_entropy_2x2, density_to_bloch, torus_radii,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from toponetx_torus_bridge import (
    build_torus_complex, map_engine_cycle_to_complex, compute_shell_structure,
    transport_allowed,
)


# ═══════════════════════════════════════════════════════════════════
# NODE STATE HELPERS
# ═══════════════════════════════════════════════════════════════════

def _compute_concurrence_4x4(rho_AB: np.ndarray) -> float:
    """Wootters concurrence for a 4x4 density matrix."""
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sigma_yy = np.kron(sy, sy)
    rho_tilde = sigma_yy @ rho_AB.conj() @ sigma_yy
    product = rho_AB @ rho_tilde
    evals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(product), 0))))[::-1]
    C = max(0.0, evals[0] - evals[1] - evals[2] - evals[3])
    return float(C)


def build_terrain_state(rho_AB: np.ndarray) -> torch.Tensor:
    """Build the 10-element terrain state vector from a 4x4 density matrix.

    Layout:
        [entropy_L, entropy_R,
         bloch_Lx, bloch_Ly, bloch_Lz,
         bloch_Rx, bloch_Ry, bloch_Rz,
         eta_placeholder,
         concurrence]
    """
    rho_L = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_R = _ensure_valid_density(partial_trace_A(rho_AB))
    s_L = von_neumann_entropy_2x2(rho_L)
    s_R = von_neumann_entropy_2x2(rho_R)
    b_L = density_to_bloch(rho_L)
    b_R = density_to_bloch(rho_R)
    conc = _compute_concurrence_4x4(rho_AB)
    return torch.tensor([
        s_L, s_R,
        b_L[0], b_L[1], b_L[2],
        b_R[0], b_R[1], b_R[2],
        0.0,  # eta — set per-terrain by caller
        conc,
    ], dtype=torch.float)


def build_operator_state(op_idx: int) -> torch.Tensor:
    """Build the 4-element operator state vector.

    Layout: [is_dissipative, is_z_axis, strength, total_applied]
    """
    name = OPERATOR_NAMES[op_idx]
    is_dissipative = 1.0 if name in ("Ti", "Te") else 0.0
    is_z_axis = 1.0 if name in ("Ti", "Fe") else 0.0
    return torch.tensor([is_dissipative, is_z_axis, 0.0, 0.0], dtype=torch.float)


# ═══════════════════════════════════════════════════════════════════
# GRAPH TRAVERSAL PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

def build_traversal_order(seq_edges: torch.Tensor) -> list:
    """Build linear traversal order from sequence edges.

    The sequence edges form a cycle.  We find a start node
    (the one that appears as a source but whose predecessor
    is the last node in the cycle), then follow edges.
    """
    src = seq_edges[0].tolist()
    dst = seq_edges[1].tolist()

    # Build adjacency: each source maps to its destination
    adj = {}
    in_nodes = set()
    for s, d in zip(src, dst):
        adj[s] = d
        in_nodes.add(d)

    # All nodes that participate
    all_nodes = set(src) | set(dst)

    # For a cycle, every node is both source and destination.
    # We need a canonical start.  Use the smallest index that appears.
    start = min(all_nodes)

    order = [start]
    current = start
    visited = {start}
    for _ in range(len(all_nodes) - 1):
        nxt = adj.get(current)
        if nxt is None or nxt in visited:
            break
        order.append(nxt)
        visited.add(nxt)
        current = nxt

    return order


def get_assigned_operator(assign_edges: torch.Tensor, terrain_idx: int):
    """Find which operator a terrain is assigned to, return (op_idx, edge_pos) or (None, None)."""
    src = assign_edges[0].tolist()
    dst = assign_edges[1].tolist()
    for i, s in enumerate(src):
        if s == terrain_idx:
            return dst[i], i
    return None, None


def get_polarity(polarity_attr: torch.Tensor, edge_pos: int) -> bool:
    """Read polarity from edge attribute at given position."""
    if edge_pos is None or polarity_attr is None:
        return True
    return bool(polarity_attr[edge_pos, 0].item() > 0.5)


def get_torus_level(data, terrain_idx: int):
    """Find which torus level a terrain sits on."""
    sits_edges = data['terrain', 'sits_on', 'torus'].edge_index
    src = sits_edges[0].tolist()
    dst = sits_edges[1].tolist()
    for s, d in zip(src, dst):
        if s == terrain_idx:
            return d
    return None


def has_transport_edge(data, torus_from: int, torus_to: int) -> bool:
    """Check if a transport edge exists between two torus levels."""
    transport = data['torus', 'transport', 'torus'].edge_index
    src = transport[0].tolist()
    dst = transport[1].tolist()
    for s, d in zip(src, dst):
        if s == torus_from and d == torus_to:
            return True
    return False


# ═══════════════════════════════════════════════════════════════════
# GRAPH-DRIVEN CYCLE
# ═══════════════════════════════════════════════════════════════════

def update_terrain_state(data, terrain_idx: int, rho_AB: np.ndarray, eta: float = 0.0):
    """Update the terrain node state tensor in-place."""
    state_vec = build_terrain_state(rho_AB)
    state_vec[8] = eta  # Set torus position
    if not hasattr(data['terrain'], 'live_state') or data['terrain'].live_state is None:
        data['terrain'].live_state = torch.zeros(8, 10, dtype=torch.float)
    data['terrain'].live_state[terrain_idx] = state_vec


def update_operator_state(data, op_idx: int, strength: float):
    """Increment application count and record strength on operator node."""
    if not hasattr(data['operator'], 'live_state') or data['operator'].live_state is None:
        data['operator'].live_state = torch.zeros(4, 4, dtype=torch.float)
        for i in range(4):
            data['operator'].live_state[i] = build_operator_state(i)
    data['operator'].live_state[op_idx, 2] = strength
    data['operator'].live_state[op_idx, 3] += 1.0


def run_graph_cycle(data, rho_AB: np.ndarray, strength: float = 0.5, shells=None):
    """Run one engine cycle driven entirely by graph structure.

    1. Follow sequence edges to determine traversal order.
    2. At each terrain, look up assigned operator via assignment edges.
    3. Apply that operator (4x4 native) to the joint density matrix.
    4. Check torus transport along sits_on and transport edges.
    5. Update terrain and operator node states.

    Returns:
        (data, rho_AB, log) — mutated graph, final density matrix, step log.
    """
    seq_edges = data['terrain', 'sequence', 'terrain'].edge_index
    assign_edges = data['terrain', 'assigned_to', 'operator'].edge_index
    polarity_attr = data['terrain', 'assigned_to', 'operator'].edge_attr

    order = build_traversal_order(seq_edges)

    log = []
    prev_torus = None

    for terrain_idx in order:
        op_idx, edge_pos = get_assigned_operator(assign_edges, terrain_idx)

        if op_idx is None:
            # No operator assigned — identity pass-through
            log.append({
                "terrain": TERRAIN_NAMES[terrain_idx],
                "operator": "IDENTITY",
                "polarity": None,
                "strength": 0.0,
                "entropy_L_before": None,
                "entropy_L_after": None,
                "torus_transport": False,
            })
            update_terrain_state(data, terrain_idx, rho_AB)
            continue

        op_name = OPERATOR_NAMES[op_idx]
        is_up = get_polarity(polarity_attr, edge_pos)

        # Entropy before
        rho_L_before = _ensure_valid_density(partial_trace_B(rho_AB))
        s_before = von_neumann_entropy_2x2(rho_L_before)

        # Torus transport check
        current_torus = get_torus_level(data, terrain_idx)
        did_transport = False
        if prev_torus is not None and current_torus is not None and prev_torus != current_torus:
            topo_ok = transport_allowed(shells or [], prev_torus, current_torus)
            if topo_ok and has_transport_edge(data, prev_torus, current_torus):
                # Apply torus radii scaling
                _, eta_to = TORUS_LEVELS[current_torus]
                R_maj, R_min = torus_radii(eta_to)
                scale = R_maj * R_min  # Cross-section area as scaling factor
                # Gentle depolarization toward torus-natural mixed state
                I4 = np.eye(4, dtype=complex) / 4.0
                transport_mix = 0.05 * (1.0 - scale)
                rho_AB = _ensure_valid_density(
                    (1.0 - transport_mix) * rho_AB + transport_mix * I4
                )
                did_transport = True
            else:
                did_transport = False

        # Apply the 4x4 operator
        op_fn = OPERATOR_MAP_4X4[op_name]
        op_kwargs = {"polarity_up": is_up, "strength": strength}
        if op_name == "Te":
            op_kwargs["q"] = 0.3
        elif op_name == "Fe":
            op_kwargs["phi"] = 0.05
        rho_AB = op_fn(rho_AB, **op_kwargs)
        rho_AB = _ensure_valid_density(rho_AB)

        # Entropy after
        rho_L_after = _ensure_valid_density(partial_trace_B(rho_AB))
        s_after = von_neumann_entropy_2x2(rho_L_after)

        # Update graph node states
        eta_val = TORUS_LEVELS[current_torus][1] if current_torus is not None else 0.0
        update_terrain_state(data, terrain_idx, rho_AB, eta=eta_val)
        update_operator_state(data, op_idx, strength)

        log.append({
            "terrain": TERRAIN_NAMES[terrain_idx],
            "operator": op_name,
            "polarity": "UP" if is_up else "DOWN",
            "strength": strength,
            "entropy_L_before": s_before,
            "entropy_L_after": s_after,
            "torus_transport": did_transport,
        })

        prev_torus = current_torus

    return data, rho_AB, log


# ═══════════════════════════════════════════════════════════════════
# GRAPH-DRIVEN ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════

class GraphDrivenEngine:
    """Engine where the PyG HeteroData graph IS the computation substrate.

    State lives on nodes.  Operations happen along edges.
    The graph structure constrains what is possible.
    """

    def __init__(self, engine_type: int = 1):
        self.engine_type = engine_type
        self.data = build_engine_graph(engine_type)
        self.cc, self.node_map = build_torus_complex()
        self.shells = compute_shell_structure(self.cc, self.node_map)
        self.rho_AB = None
        self.cycle_count = 0
        self.entropy_trajectory = []
        self.concurrence_trajectory = []

    def init(self):
        """Initialize from GeometricEngine's init_state to ensure identical starting conditions."""
        engine = GeometricEngine(engine_type=self.engine_type)
        state = engine.init_state()
        self.rho_AB = state.rho_AB.copy()
        self.data = attach_engine_state(self.data, state)

        # Initialize live_state tensors on all nodes
        for i in range(8):
            update_terrain_state(self.data, i, self.rho_AB)
        for i in range(4):
            update_operator_state(self.data, i, 0.0)
            # Reset the count that update_operator_state incremented
            self.data['operator'].live_state[i, 3] = 0.0

        self.entropy_trajectory = [self.get_entropy()]
        self.concurrence_trajectory = [self.get_concurrence()]
        return self

    def run_cycle(self, strength: float = 0.5):
        """Run one full cycle driven by graph structure."""
        self.data, self.rho_AB, log = run_graph_cycle(
            self.data, self.rho_AB, strength=strength, shells=self.shells
        )
        self.cycle_count += 1
        self.entropy_trajectory.append(self.get_entropy())
        self.concurrence_trajectory.append(self.get_concurrence())
        return log

    def get_entropy(self) -> float:
        """Von Neumann entropy of the L subsystem."""
        rho_L = _ensure_valid_density(partial_trace_B(self.rho_AB))
        return von_neumann_entropy_2x2(rho_L)

    def get_concurrence(self) -> float:
        """Wootters concurrence of the 4x4 joint state."""
        return _compute_concurrence_4x4(self.rho_AB)

    def get_terrain_state(self, terrain_idx: int) -> torch.Tensor:
        """Read the live state vector of a terrain node."""
        return self.data['terrain'].live_state[terrain_idx]

    def get_operator_state(self, op_idx: int) -> torch.Tensor:
        """Read the live state vector of an operator node."""
        return self.data['operator'].live_state[op_idx]

    # ── Graph mutation methods ────────────────────────────────────

    def remove_sequence_edge(self, position: int):
        """Remove a sequence edge by position index.  Mutates the graph."""
        ei = self.data['terrain', 'sequence', 'terrain'].edge_index
        mask = torch.ones(ei.shape[1], dtype=torch.bool)
        mask[position] = False
        self.data['terrain', 'sequence', 'terrain'].edge_index = ei[:, mask]

    def remove_assignment_edge(self, terrain_idx: int):
        """Remove the assignment edge for a specific terrain.  That terrain becomes identity."""
        ei = self.data['terrain', 'assigned_to', 'operator'].edge_index
        attr = self.data['terrain', 'assigned_to', 'operator'].edge_attr
        mask = ei[0] != terrain_idx
        self.data['terrain', 'assigned_to', 'operator'].edge_index = ei[:, mask]
        self.data['terrain', 'assigned_to', 'operator'].edge_attr = attr[mask]

    def remove_transport_edge(self, src_torus: int, dst_torus: int):
        """Remove a transport edge between two torus levels."""
        ei = self.data['torus', 'transport', 'torus'].edge_index
        mask = ~((ei[0] == src_torus) & (ei[1] == dst_torus))
        self.data['torus', 'transport', 'torus'].edge_index = ei[:, mask]


# ═══════════════════════════════════════════════════════════════════
# REFERENCE ENGINE RUNNER (for comparison)
# ═══════════════════════════════════════════════════════════════════

def run_reference_engine(engine_type: int = 1, n_cycles: int = 10):
    """Run the original GeometricEngine for n_cycles and return trajectories."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state()

    rho_L = _ensure_valid_density(partial_trace_B(state.rho_AB))
    entropy_traj = [von_neumann_entropy_2x2(rho_L)]
    conc_traj = [_compute_concurrence_4x4(state.rho_AB)]

    for _ in range(n_cycles):
        state = engine.run_cycle(state)
        rho_L = _ensure_valid_density(partial_trace_B(state.rho_AB))
        entropy_traj.append(von_neumann_entropy_2x2(rho_L))
        conc_traj.append(_compute_concurrence_4x4(state.rho_AB))

    return entropy_traj, conc_traj


# ═══════════════════════════════════════════════════════════════════
# VERIFICATION
# ═══════════════════════════════════════════════════════════════════

def main():
    N_CYCLES = 10
    print("=" * 72)
    print("  GRAPH-DRIVEN ENGINE vs ORIGINAL ENGINE COMPARISON")
    print("=" * 72)

    # ── 1. Run both engines ──────────────────────────────────────
    print("\n[1] Running graph-driven engine for %d cycles..." % N_CYCLES)
    gde = GraphDrivenEngine(engine_type=1).init()
    graph_logs = []
    for c in range(N_CYCLES):
        log = gde.run_cycle(strength=0.5)
        graph_logs.append(log)

    print("[1] Running reference engine for %d cycles..." % N_CYCLES)
    ref_entropy, ref_conc = run_reference_engine(engine_type=1, n_cycles=N_CYCLES)

    # ── 2. Compare trajectories ──────────────────────────────────
    print("\n[2] ENTROPY TRAJECTORY COMPARISON")
    print("    Cycle | Graph-Driven | Reference  | Delta")
    print("    " + "-" * 50)
    for i in range(N_CYCLES + 1):
        ge = gde.entropy_trajectory[i]
        re = ref_entropy[i]
        delta = abs(ge - re)
        marker = " <-- DIVERGED" if delta > 0.01 else ""
        print("    %5d | %12.6f | %10.6f | %.6f%s" % (i, ge, re, delta, marker))

    print("\n[3] CONCURRENCE TRAJECTORY COMPARISON")
    print("    Cycle | Graph-Driven | Reference  | Delta")
    print("    " + "-" * 50)
    for i in range(N_CYCLES + 1):
        gc = gde.concurrence_trajectory[i]
        rc = ref_conc[i]
        delta = abs(gc - rc)
        marker = " <-- DIVERGED" if delta > 0.01 else ""
        print("    %5d | %12.6f | %10.6f | %.6f%s" % (i, gc, rc, delta, marker))

    # ── 3. Graph state verification ──────────────────────────────
    print("\n[4] GRAPH NODE STATE VERIFICATION")
    print("    Terrain node states updated: ", end="")
    live = gde.data['terrain'].live_state
    nonzero_terrains = (live.abs().sum(dim=1) > 1e-6).sum().item()
    print("%d / 8" % nonzero_terrains)

    print("    Operator application counts:")
    for i in range(4):
        os = gde.get_operator_state(i)
        print("      %s: applied %d times, last strength=%.3f" % (
            OPERATOR_NAMES[i], int(os[3].item()), os[2].item()))

    # ── 4. Last cycle step log ───────────────────────────────────
    print("\n[5] LAST CYCLE STEP LOG (graph-driven traversal order)")
    for step in graph_logs[-1]:
        t_str = "  %-6s -> %-8s (%s) str=%.2f  S_L: %.4f -> %.4f" % (
            step["terrain"], step["operator"],
            step["polarity"] or "N/A",
            step["strength"],
            step["entropy_L_before"] or 0.0,
            step["entropy_L_after"] or 0.0,
        )
        if step["torus_transport"]:
            t_str += "  [TORUS TRANSPORT]"
        print("   ", t_str)

    # ── 5. NEGATIVE TESTS: Break the graph ───────────────────────
    print("\n" + "=" * 72)
    print("  NEGATIVE TESTS: GRAPH MUTATIONS")
    print("=" * 72)

    # 5a. Remove a sequence edge
    print("\n[6a] REMOVE SEQUENCE EDGE (position 2)")
    gde_broken_seq = GraphDrivenEngine(engine_type=1).init()
    gde_broken_seq.remove_sequence_edge(2)
    broken_seq_log = gde_broken_seq.run_cycle(strength=0.5)
    intact_terrains = [s["terrain"] for s in graph_logs[0]]
    broken_terrains = [s["terrain"] for s in broken_seq_log]
    print("     Intact traversal: %s" % " -> ".join(intact_terrains))
    print("     Broken traversal: %s" % " -> ".join(broken_terrains))
    seq_entropy_delta = abs(gde_broken_seq.get_entropy() - gde.entropy_trajectory[1])
    print("     Entropy delta after 1 cycle: %.6f" % seq_entropy_delta)
    print("     Traversal changed: %s" % (intact_terrains != broken_terrains))

    # 5b. Remove an assignment edge
    print("\n[6b] REMOVE ASSIGNMENT EDGE (terrain 0 = Se_f)")
    gde_broken_assign = GraphDrivenEngine(engine_type=1).init()
    gde_broken_assign.remove_assignment_edge(0)
    broken_assign_log = gde_broken_assign.run_cycle(strength=0.5)
    identity_steps = [s for s in broken_assign_log if s["operator"] == "IDENTITY"]
    print("     Identity pass-throughs: %d" % len(identity_steps))
    if identity_steps:
        print("     Identity terrain(s): %s" % ", ".join(s["terrain"] for s in identity_steps))
    assign_entropy_delta = abs(gde_broken_assign.get_entropy() - gde.entropy_trajectory[1])
    print("     Entropy delta vs intact: %.6f" % assign_entropy_delta)

    # 5c. Transport edge test
    # In Type-1, fiber terrains sit on inner torus (0), base on outer (2).
    # Transport edges are 0<->1 and 1<->2 (bidirectional).
    # The fiber->base jump is torus 0->2, which has NO direct edge.
    # Adding a direct 0->2 edge enables transport on that boundary.
    print("\n[6c] TRANSPORT EDGE TEST (add direct inner->outer edge)")
    gde_with_transport = GraphDrivenEngine(engine_type=1).init()
    # Add a direct inner->outer transport edge to enable the crossing
    te = gde_with_transport.data['torus', 'transport', 'torus'].edge_index
    new_edge = torch.tensor([[0], [2]], dtype=torch.long)
    gde_with_transport.data['torus', 'transport', 'torus'].edge_index = torch.cat([te, new_edge], dim=1)
    transport_log = gde_with_transport.run_cycle(strength=0.5)
    transport_steps_intact = sum(1 for s in graph_logs[0] if s["torus_transport"])
    transport_steps_added = sum(1 for s in transport_log if s["torus_transport"])
    transport_entropy = gde_with_transport.get_entropy()
    intact_entropy = gde.entropy_trajectory[1]
    print("     Transport events (no direct edge):   %d" % transport_steps_intact)
    print("     Transport events (with direct edge):  %d" % transport_steps_added)
    print("     Entropy delta from transport:          %.6f" % abs(transport_entropy - intact_entropy))

    # ── 6. Summary ───────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)

    # Check initial conditions match
    init_match = abs(gde.entropy_trajectory[0] - ref_entropy[0]) < 1e-10
    print("  Initial conditions match:        %s" % init_match)

    # Check graph states are populated
    print("  Graph terrain states populated:   %d/8" % nonzero_terrains)

    # Check negative tests produced divergence
    print("  Sequence break caused change:     %s" % (intact_terrains != broken_terrains or seq_entropy_delta > 1e-6))
    print("  Assignment break caused identity: %s" % (len(identity_steps) > 0))

    # Note about trajectory divergence
    # The graph-driven engine applies operators differently from the reference
    # (no axis0 coarse-graining, no angular advancement, no terrain modulation)
    # so trajectories WILL diverge.  This is expected and correct.
    final_entropy_delta = abs(gde.entropy_trajectory[-1] - ref_entropy[-1])
    print("  Final entropy delta (expected divergence): %.6f" % final_entropy_delta)
    print()
    print("  NOTE: Trajectory divergence is EXPECTED. The graph-driven engine")
    print("  applies operators via graph structure without the reference engine's")
    print("  axis0 coarse-graining, angular advancement, or terrain modulation.")
    print("  The point is that the GRAPH STRUCTURE drives the computation.")
    print()


if __name__ == "__main__":
    main()
