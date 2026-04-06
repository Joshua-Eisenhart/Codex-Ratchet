#!/usr/bin/env python3
"""
pyg_engine_bridge.py
====================
Bridge between the engine and PyG (torch_geometric) heterogeneous graphs.

The engine's structure — terrains, operators, torus levels, placements,
loop grammar — is a heterogeneous graph. PyG HeteroData represents it
natively with typed nodes and edges.

This bridge:
- Builds a HeteroData from the engine's STAGE_OPERATOR_LUT and LOOP_GRAMMAR
- Attaches live engine state as node features
- Enables graph-native analysis (message passing, neighborhood aggregation)
"""

import torch
import numpy as np
from torch_geometric.data import HeteroData

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import (
    TERRAINS, STAGE_OPERATOR_LUT, LOOP_GRAMMAR, LOOP_STAGE_ORDER,
    GeometricEngine, EngineState,
)
from hopf_manifold import (
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, torus_radii,
)


TERRAIN_NAMES = [t['name'] for t in TERRAINS]
OPERATOR_NAMES = ['Ti', 'Fe', 'Te', 'Fi']
TORUS_LEVELS = [
    ('inner', TORUS_INNER),
    ('clifford', TORUS_CLIFFORD),
    ('outer', TORUS_OUTER),
]


def build_engine_graph(engine_type=1):
    """Build a PyG HeteroData representing the engine's static structure.

    Node types:
        terrain: 8 nodes (Se_f, Si_f, Ne_f, Ni_f, Se_b, Si_b, Ne_b, Ni_b)
        operator: 4 nodes (Ti, Fe, Te, Fi)
        torus: 3 nodes (inner, Clifford, outer)

    Edge types:
        (terrain, assigned_to, operator): from STAGE_OPERATOR_LUT
        (terrain, sequence, terrain): from LOOP_STAGE_ORDER
        (torus, transport, torus): inner↔Clifford↔outer
        (terrain, sits_on, torus): fiber→inner, base→outer
    """
    data = HeteroData()

    # Terrain nodes
    terrain_features = []
    for t in TERRAINS:
        expansion = 1.0 if t['expansion'] else 0.0
        is_open = 1.0 if t['open'] else 0.0
        is_fiber = 1.0 if t['loop'] == 'fiber' else 0.0
        topo_idx = float(['Se', 'Si', 'Ne', 'Ni'].index(t['topo']))
        terrain_features.append([expansion, is_open, is_fiber, topo_idx])
    data['terrain'].x = torch.tensor(terrain_features, dtype=torch.float)

    # Operator nodes
    op_features = []
    for op in OPERATOR_NAMES:
        is_dissipative = 1.0 if op in ['Ti', 'Te'] else 0.0
        is_z_axis = 1.0 if op in ['Ti', 'Fe'] else 0.0
        op_features.append([is_dissipative, is_z_axis])
    data['operator'].x = torch.tensor(op_features, dtype=torch.float)

    # Torus nodes
    torus_features = []
    for name, eta in TORUS_LEVELS:
        R_maj, R_min = torus_radii(eta)
        torus_features.append([eta, R_maj, R_min])
    data['torus'].x = torch.tensor(torus_features, dtype=torch.float)

    # Edges: terrain → operator assignment
    src, dst = [], []
    polarity_attrs = []
    for (et, loop, topo), (op_name, is_up) in STAGE_OPERATOR_LUT.items():
        if et != engine_type:
            continue
        # Find terrain index
        for ti, t in enumerate(TERRAINS):
            if t['loop'] == loop and t['topo'] == topo:
                src.append(ti)
                dst.append(OPERATOR_NAMES.index(op_name))
                polarity_attrs.append([1.0 if is_up else 0.0])
                break

    data['terrain', 'assigned_to', 'operator'].edge_index = torch.tensor(
        [src, dst], dtype=torch.long
    )
    data['terrain', 'assigned_to', 'operator'].edge_attr = torch.tensor(
        polarity_attrs, dtype=torch.float
    )

    # Edges: terrain → terrain (stage sequence from loop order)
    stage_order = LOOP_STAGE_ORDER[engine_type]
    seq_src, seq_dst = [], []
    for i in range(len(stage_order) - 1):
        seq_src.append(stage_order[i])
        seq_dst.append(stage_order[i + 1])
    # Close the loop
    seq_src.append(stage_order[-1])
    seq_dst.append(stage_order[0])

    data['terrain', 'sequence', 'terrain'].edge_index = torch.tensor(
        [seq_src, seq_dst], dtype=torch.long
    )

    # Edges: torus → torus (transport)
    data['torus', 'transport', 'torus'].edge_index = torch.tensor(
        [[0, 1, 1, 2], [1, 0, 2, 1]], dtype=torch.long  # bidirectional
    )

    # Edges: terrain → torus (sits_on)
    sits_src, sits_dst = [], []
    for ti, t in enumerate(TERRAINS):
        if t['loop'] == 'fiber':
            sits_src.append(ti)
            sits_dst.append(0)  # inner torus
        else:
            sits_src.append(ti)
            sits_dst.append(2)  # outer torus

    data['terrain', 'sits_on', 'torus'].edge_index = torch.tensor(
        [sits_src, sits_dst], dtype=torch.long
    )

    return data


def attach_engine_state(data, state):
    """Attach live engine state as node features.

    Adds entropy, ga0, and Bloch vector info to terrain nodes.
    """
    from hopf_manifold import von_neumann_entropy_2x2, density_to_bloch
    from geometric_operators import partial_trace_A, partial_trace_B

    rho_L = partial_trace_B(state.rho_AB)
    rho_R = partial_trace_A(state.rho_AB)

    s_L = von_neumann_entropy_2x2(rho_L)
    s_R = von_neumann_entropy_2x2(rho_R)
    bloch_L = density_to_bloch(rho_L)
    bloch_R = density_to_bloch(rho_R)

    # Add state features to terrain nodes (broadcast same state to all)
    state_features = torch.tensor([
        [s_L, s_R, state.ga0_level, state.eta,
         bloch_L[0], bloch_L[1], bloch_L[2],
         bloch_R[0], bloch_R[1], bloch_R[2]]
    ] * 8, dtype=torch.float)

    data['terrain'].state = state_features
    return data


# ── Verification ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== PyG Engine Bridge Verification ===")
    print()

    for et in [1, 2]:
        data = build_engine_graph(engine_type=et)
        print(f"Type {et} engine graph:")
        print(f"  Node types: {data.node_types}")
        print(f"  Edge types: {data.edge_types}")
        print(f"  Terrain nodes: {data['terrain'].x.shape}")
        print(f"  Operator nodes: {data['operator'].x.shape}")
        print(f"  Torus nodes: {data['torus'].x.shape}")
        print(f"  Assignment edges: {data['terrain', 'assigned_to', 'operator'].edge_index.shape}")
        print(f"  Sequence edges: {data['terrain', 'sequence', 'terrain'].edge_index.shape}")
        print(f"  Transport edges: {data['torus', 'transport', 'torus'].edge_index.shape}")
        print(f"  Sits-on edges: {data['terrain', 'sits_on', 'torus'].edge_index.shape}")
        print()

        # Attach live state
        engine = GeometricEngine(engine_type=et)
        state = engine.init_state()
        state = engine.run_cycle(state)
        data = attach_engine_state(data, state)
        print(f"  State features attached: {data['terrain'].state.shape}")
        print(f"  ga0 = {state.ga0_level:.4f}")
        print()

    print("PyG engine bridge verified.")
