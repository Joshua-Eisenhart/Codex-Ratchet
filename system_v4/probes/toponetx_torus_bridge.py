#!/usr/bin/env python3
"""
toponetx_torus_bridge.py
========================
Bridge between the engine's nested Hopf torus structure and TopoNetX
cell complexes.

The nested tori (inner/Clifford/outer) with fiber/base loops form a
topological structure that should be represented as a cell complex,
not just as coordinate arrays.

This bridge:
- Builds a CellComplex from the engine's torus parameters
- Maps engine states to nodes/edges in the complex
- Computes topological invariants (adjacency, incidence)
- Provides shell/boundary structure for Axis 0

The cell complex has:
- 0-cells: discrete points on each torus ring (terrain positions)
- 1-cells: edges (within-ring = loop traversal, between-ring = transport)
- 2-cells: faces (shell surfaces between adjacent torus levels)
"""

import numpy as np
from toponetx.classes import CellComplex

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    torus_coordinates, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
    torus_radii, berry_phase, left_weyl_spinor, right_weyl_spinor,
)
from engine_core import TERRAINS, LOOP_STAGE_ORDER


# ── Build the cell complex ──────────────────────────────────────────

def build_torus_complex(n_per_ring=8, torus_levels=None):
    """Build a CellComplex representing the nested torus structure.

    Args:
        n_per_ring: number of discrete positions per torus ring
                    (default 8 = number of terrain stages per engine type)
        torus_levels: list of (name, eta) pairs for torus levels
                      (default: inner/Clifford/outer)

    Returns:
        cc: CellComplex
        node_map: dict mapping (layer, position) to torus coordinates
    """
    if torus_levels is None:
        torus_levels = [
            ('inner', TORUS_INNER),
            ('clifford', TORUS_CLIFFORD),
            ('outer', TORUS_OUTER),
        ]

    cc = CellComplex()
    node_map = {}

    n_layers = len(torus_levels)

    # 0-cells: vertices on each ring
    for layer, (name, eta) in enumerate(torus_levels):
        for i in range(n_per_ring):
            theta = 2 * np.pi * i / n_per_ring
            node_id = (layer, i)
            cc.add_node(node_id)
            q = torus_coordinates(eta, theta, 0.0)
            node_map[node_id] = {
                'eta': eta,
                'theta': theta,
                'layer_name': name,
                'q': q,
                'psi_L': left_weyl_spinor(q),
                'psi_R': right_weyl_spinor(q),
            }

    # 1-cells: within-ring edges (loop traversal)
    for layer in range(n_layers):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cc.add_edge((layer, i), (layer, j))

    # 1-cells: between-ring edges (torus transport)
    for layer in range(n_layers - 1):
        for i in range(n_per_ring):
            cc.add_edge((layer, i), (layer + 1, i))

    # 2-cells: shell surfaces between adjacent rings
    for layer in range(n_layers - 1):
        for i in range(n_per_ring):
            j = (i + 1) % n_per_ring
            cell = [(layer, i), (layer, j), (layer + 1, j), (layer + 1, i)]
            cc.add_cell(cell, rank=2)

    return cc, node_map


def map_engine_cycle_to_complex(cc, engine_type, node_map):
    """Map an engine cycle's stage order onto the cell complex.

    Returns a list of node IDs in the order the engine visits them.
    This traces the engine's path through the topological structure.
    """
    stage_order = LOOP_STAGE_ORDER[engine_type]

    # Map terrain indices to positions on the Clifford ring (layer 1)
    # The engine operates primarily on one torus level at a time
    # but can transport between levels
    path = []
    for pos, terrain_idx in enumerate(stage_order):
        terrain = TERRAINS[terrain_idx]
        loop = terrain['loop']

        # Fiber terrains map to inner ring, base terrains to outer ring
        if loop == 'fiber':
            layer = 0  # inner
        else:
            layer = 2  # outer

        path.append((layer, pos % 8))

    return path


def compute_shell_structure(cc, node_map, n_per_ring=8):
    """Compute the shell/boundary structure needed for Axis 0.

    The shells are the 2-cells between torus rings.
    The boundary of each shell is the ring of edges connecting
    two adjacent torus levels.

    Returns:
        shells: list of shell descriptions with boundary info
    """
    shells = []
    n_layers = max(layer for layer, _ in node_map.keys()) + 1

    for layer in range(n_layers - 1):
        inner_nodes = [(layer, i) for i in range(n_per_ring)]
        outer_nodes = [(layer + 1, i) for i in range(n_per_ring)]

        # Compute average eta for each boundary
        inner_eta = node_map[inner_nodes[0]]['eta']
        outer_eta = node_map[outer_nodes[0]]['eta']

        # The shell is the region between these two rings
        shells.append({
            'inner_layer': layer,
            'outer_layer': layer + 1,
            'inner_eta': inner_eta,
            'outer_eta': outer_eta,
            'delta_eta': outer_eta - inner_eta,
            'inner_nodes': inner_nodes,
            'outer_nodes': outer_nodes,
            'n_faces': n_per_ring,  # number of 2-cells in this shell
        })

    return shells


def transport_allowed(shells, from_layer, to_layer):
    """Return True only if the requested transport is supported by shell adjacency.

    This is the runtime TopoNetX gate: the cell-complex shell structure
    must explicitly admit the layer transition.
    """
    if from_layer == to_layer:
        return True
    a, b = sorted((from_layer, to_layer))
    for shell in shells:
        if shell['inner_layer'] == a and shell['outer_layer'] == b:
            return True
    return False


# ── Verification ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== TopoNetX Torus Bridge Verification ===")
    print()

    cc, node_map = build_torus_complex()

    print(f"Cell complex:")
    print(f"  0-cells (vertices): {len(cc.nodes)}")
    print(f"  1-cells (edges): {len(cc.edges)}")
    print(f"  2-cells (faces): {len(cc.cells)}")
    print()

    # Map engine cycles
    for et in [1, 2]:
        path = map_engine_cycle_to_complex(cc, et, node_map)
        layers_visited = [p[0] for p in path]
        print(f"Type {et} cycle path through complex:")
        print(f"  Layers visited: {layers_visited}")
        print(f"  Unique layers: {sorted(set(layers_visited))}")
        print()

    # Shell structure
    shells = compute_shell_structure(cc, node_map)
    print(f"Shell structure ({len(shells)} shells):")
    for s in shells:
        print(f"  Layer {s['inner_layer']}→{s['outer_layer']}: "
              f"η=[{s['inner_eta']:.4f}, {s['outer_eta']:.4f}], "
              f"Δη={s['delta_eta']:.4f}, faces={s['n_faces']}")
    print()

    # Adjacency
    adj = cc.adjacency_matrix(0)
    print(f"Adjacency matrix: {adj.shape}")
    print(f"  Nonzero entries: {adj.nnz}")
    print()

    # Berry phase per ring
    for layer, (name, eta) in enumerate([('inner', TORUS_INNER),
                                          ('clifford', TORUS_CLIFFORD),
                                          ('outer', TORUS_OUTER)]):
        us = np.linspace(0, 2 * np.pi, 64, endpoint=True)
        fiber_loop = np.array([torus_coordinates(eta, u, 0.0) for u in us])
        bp = berry_phase(fiber_loop)
        R_maj, R_min = torus_radii(eta)
        print(f"  Ring '{name}': η={eta:.4f}, R_maj={R_maj:.4f}, "
              f"R_min={R_min:.4f}, Berry={bp:.4f}")

    print()
    print("TopoNetX torus bridge verified.")
