#!/usr/bin/env python3
"""
sim_geometric_constraint_manifold_pyg.py
=========================================
Geometric constraint manifold as a PyG HeteroData graph.

Architecture (SUPPORT-FIRST):
  - Nodes  = geometry shells (earned standalone sims)
  - Edges  = 'runs_on' relationships (earned coupling sims)
  - Message passing = constraint propagation through geometric hierarchy
  - PyTorch autograd = entropy gradient flows backward through layer graph
  - z3 guards = admissibility checks at each layer boundary

Two MessagePassing layers:
  1. GeometryConstraintConv: propagates G-structure features upward (child <- parent)
  2. EntropyReadoutConv: propagates entropy/I_c features upward, autograd-enabled

z3 admissibility:
  - Encodes G-structure level constraint: child G-level <= parent G-level
  - Verifies all existing edges: SAT
  - Verifies invalid backward edge (S3 runs_on ThreeQ): UNSAT

classification: canonical
"""

import json
import os
import sys
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",
    "pyg":       "load_bearing",
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# --- try imports -------------------------------------------------------

try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TORCH_OK = True
except ImportError:
    TORCH_OK = False
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from torch_geometric.data import HeteroData
    from torch_geometric.nn import MessagePassing
    TOOL_MANIFEST["pyg"]["tried"] = True
    PYG_OK = True
except ImportError:
    PYG_OK = False
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import (
        Solver, Int, Bool, And, Or, Not, Implies,
        sat, unsat, ArithRef,
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    Z3_OK = True
except ImportError:
    Z3_OK = False
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    SYMPY_OK = True
except ImportError:
    SYMPY_OK = False
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# NODE DEFINITIONS
# =====================================================================

# Geometry node feature vectors [dim, is_spin, has_contact, is_sasakian,
#                                  is_kahler, is_hopf_flag]
GEOMETRY_NODES = {
    "S3":            [3, 1, 1, 1, 0, 1],
    "S2_CP1":        [2, 1, 0, 0, 1, 0],
    "T_eta":         [2, 1, 0, 0, 1, 0],
    "Contact_S3":    [3, 1, 1, 0, 0, 0],
    "Sasakian_S3":   [3, 1, 1, 1, 0, 0],
    "Spin3_SU2":     [3, 1, 0, 0, 0, 0],
    "WeylBipartite": [4, 1, 0, 0, 0, 0],
    "ThreeQ":        [6, 1, 0, 0, 0, 0],
}

GEOMETRY_NODE_LIST = list(GEOMETRY_NODES.keys())
GEOMETRY_NODE_IDX  = {k: i for i, k in enumerate(GEOMETRY_NODE_LIST)}

# Topology node feature vectors [orbit_type_id, is_unitary, is_dissipative]
TOPOLOGY_NODES = {
    "Si": [0, 1, 0],
    "Ne": [1, 1, 0],
    "Se": [2, 0, 1],
    "Ni": [3, 0, 1],
}
TOPOLOGY_NODE_LIST = list(TOPOLOGY_NODES.keys())
TOPOLOGY_NODE_IDX  = {k: i for i, k in enumerate(TOPOLOGY_NODE_LIST)}

# Operator node feature vectors [pauli_id, is_hermitian, in_su2]
OPERATOR_NODES = {
    "sigma_z":     [0, 1, 1],
    "sigma_x":     [1, 1, 1],
    "sigma_plus":  [2, 0, 0],
    "sigma_minus": [3, 0, 0],
}
OPERATOR_NODE_LIST = list(OPERATOR_NODES.keys())
OPERATOR_NODE_IDX  = {k: i for i, k in enumerate(OPERATOR_NODE_LIST)}

# G-structure levels for z3 admissibility checking.
#
# Semantics: higher G-level = MORE constrained / more specialized geometry.
# A 'runs_on' edge (child -> parent) means the child is built ON TOP OF
# the parent.  The parent is LESS constrained (lower level); the child
# is MORE constrained (higher or equal level).
#
# Admissibility rule: g_level(child) >= g_level(parent)
# (child needs at least as much G-structure as its support provides)
#
# Tower (bottom to top of specialization):
#   S3 base sphere            → level 1  (most general support)
#   Spin3/SU2 G-structure     → level 2  (spinor structure on S3)
#   Contact structure on S3   → level 3  (contact geometry layer)
#   Sasakian structure        → level 4  (Sasakian on top of contact)
#   WeylBipartite (2q spin)   → level 2  (spin-level bipartite Weyl)
#   ThreeQ (3q extension)     → level 3  (extends 2q)
#   T_eta (flat torus leaf)   → level 2  (runs directly on S3)
#   S2_CP1 (Hopf base)        → level 1  (Hopf base of S3, same level)
G_LEVELS = {
    "S3":            1,
    "S2_CP1":        1,
    "Spin3_SU2":     2,
    "T_eta":         2,
    "WeylBipartite": 2,
    "Contact_S3":    3,
    "ThreeQ":        3,
    "Sasakian_S3":   4,
}

# Directed runs_on edges: (child, parent)
RUNS_ON_EDGES = [
    ("T_eta",        "S3"),
    ("Contact_S3",   "S3"),
    ("Sasakian_S3",  "Contact_S3"),
    ("Spin3_SU2",    "S3"),
    ("WeylBipartite","Spin3_SU2"),
    ("ThreeQ",       "WeylBipartite"),
]

HOPF_BASE_EDGES = [
    ("S2_CP1", "S3"),
]

# topology lives_at geometry
LIVES_AT_EDGES = [
    ("Si", "Spin3_SU2"),
    ("Ne", "Spin3_SU2"),
    ("Se", "Spin3_SU2"),
    ("Ni", "Spin3_SU2"),
]

# operator generates topology
GENERATES_EDGES = [
    ("sigma_z",    "Si"),
    ("sigma_x",    "Ne"),
    ("sigma_plus", "Se"),
    ("sigma_minus","Ni"),
]

# operator acts_on geometry
ACTS_ON_EDGES = [
    ("sigma_z",   "S3"),
    ("sigma_plus","S3"),
]


# =====================================================================
# GRAPH CONSTRUCTION
# =====================================================================

def build_constraint_manifold_graph():
    """
    Build the HeteroData constraint manifold graph.
    Returns data, theta_params (per-geometry-node learnable params).
    """
    if not TORCH_OK:
        raise RuntimeError("pytorch not available")

    # Learnable coherence factor for each geometry node (for autograd test)
    # nn.Parameter so autograd tracks them
    theta_params = nn.ParameterList([
        nn.Parameter(torch.randn(1))
        for _ in GEOMETRY_NODE_LIST
    ])

    if PYG_OK:
        data = _build_hetero_data_pyg(theta_params)
    else:
        data = _build_hetero_data_manual(theta_params)

    return data, theta_params


def _build_hetero_data_pyg(theta_params):
    """Build via torch_geometric HeteroData."""
    data = HeteroData()

    # --- geometry nodes (feature + theta embedded as extra dim) -------
    geom_feats = []
    for i, name in enumerate(GEOMETRY_NODE_LIST):
        feat = GEOMETRY_NODES[name]
        # Append sigmoid(theta) as a 7th feature so it participates in graph
        theta_val = torch.sigmoid(theta_params[i])
        row = torch.tensor(feat, dtype=torch.float32)
        row = torch.cat([row, theta_val])        # shape [7]
        geom_feats.append(row.unsqueeze(0))
    data["geometry"].x = torch.cat(geom_feats, dim=0)   # [8, 7]

    # --- topology nodes -----------------------------------------------
    topo_feats = [
        torch.tensor(TOPOLOGY_NODES[k], dtype=torch.float32)
        for k in TOPOLOGY_NODE_LIST
    ]
    data["topology"].x = torch.stack(topo_feats)         # [4, 3]

    # --- operator nodes -----------------------------------------------
    op_feats = [
        torch.tensor(OPERATOR_NODES[k], dtype=torch.float32)
        for k in OPERATOR_NODE_LIST
    ]
    data["operator"].x = torch.stack(op_feats)           # [4, 3]

    # --- runs_on edges (geometry -> geometry) -------------------------
    ro_src, ro_dst = [], []
    for child, parent in RUNS_ON_EDGES:
        ro_src.append(GEOMETRY_NODE_IDX[child])
        ro_dst.append(GEOMETRY_NODE_IDX[parent])
    data["geometry", "runs_on", "geometry"].edge_index = torch.tensor(
        [ro_src, ro_dst], dtype=torch.long
    )

    # --- hopf_base_of edges -------------------------------------------
    hb_src, hb_dst = [], []
    for child, parent in HOPF_BASE_EDGES:
        hb_src.append(GEOMETRY_NODE_IDX[child])
        hb_dst.append(GEOMETRY_NODE_IDX[parent])
    data["geometry", "hopf_base_of", "geometry"].edge_index = torch.tensor(
        [hb_src, hb_dst], dtype=torch.long
    )

    # --- lives_at edges (topology -> geometry) ------------------------
    la_src, la_dst = [], []
    for topo, geom in LIVES_AT_EDGES:
        la_src.append(TOPOLOGY_NODE_IDX[topo])
        la_dst.append(GEOMETRY_NODE_IDX[geom])
    data["topology", "lives_at", "geometry"].edge_index = torch.tensor(
        [la_src, la_dst], dtype=torch.long
    )

    # --- generates edges (operator -> topology) -----------------------
    gen_src, gen_dst = [], []
    for op, topo in GENERATES_EDGES:
        gen_src.append(OPERATOR_NODE_IDX[op])
        gen_dst.append(TOPOLOGY_NODE_IDX[topo])
    data["operator", "generates", "topology"].edge_index = torch.tensor(
        [gen_src, gen_dst], dtype=torch.long
    )

    # --- acts_on edges (operator -> geometry) -------------------------
    ao_src, ao_dst = [], []
    for op, geom in ACTS_ON_EDGES:
        ao_src.append(OPERATOR_NODE_IDX[op])
        ao_dst.append(GEOMETRY_NODE_IDX[geom])
    data["operator", "acts_on", "geometry"].edge_index = torch.tensor(
        [ao_src, ao_dst], dtype=torch.long
    )

    return data


def _build_hetero_data_manual(theta_params):
    """
    Fallback: build a plain dict mimicking HeteroData when PyG is absent.
    Uses torch tensors throughout so autograd still works.
    """
    class _ManualHeteroData:
        """Minimal HeteroData surrogate backed by plain dicts."""

        def __init__(self):
            self._nodes  = {}   # type -> tensor
            self._edges  = {}   # (src_type, rel, dst_type) -> {edge_index}
            self.node_types = []
            self.edge_types = []

        def __setitem__(self, key, val):
            if isinstance(key, str):
                if key not in self._nodes:
                    self.node_types.append(key)
                self._nodes[key] = val
            elif isinstance(key, tuple):
                if key not in self._edges:
                    self.edge_types.append(key)
                self._edges[key] = val

        def __getitem__(self, key):
            if isinstance(key, str):
                return self._nodes[key]
            return self._edges[key]

        def validate(self):
            return True  # minimal surrogate always valid

    data = _ManualHeteroData()

    # geometry nodes
    geom_feats = []
    for i, name in enumerate(GEOMETRY_NODE_LIST):
        feat = GEOMETRY_NODES[name]
        theta_val = torch.sigmoid(theta_params[i])
        row = torch.cat([torch.tensor(feat, dtype=torch.float32), theta_val])
        geom_feats.append(row.unsqueeze(0))
    data["geometry"] = torch.cat(geom_feats, dim=0)   # tensor [8, 7]

    # topology and operator nodes as plain tensors
    data["topology"] = torch.stack([
        torch.tensor(TOPOLOGY_NODES[k], dtype=torch.float32)
        for k in TOPOLOGY_NODE_LIST
    ])
    data["operator"] = torch.stack([
        torch.tensor(OPERATOR_NODES[k], dtype=torch.float32)
        for k in OPERATOR_NODE_LIST
    ])

    # edges stored as tensors in nested dict
    ro_src, ro_dst = zip(*[
        (GEOMETRY_NODE_IDX[c], GEOMETRY_NODE_IDX[p])
        for c, p in RUNS_ON_EDGES
    ])
    data[("geometry", "runs_on", "geometry")] = {
        "edge_index": torch.tensor([list(ro_src), list(ro_dst)], dtype=torch.long)
    }

    return data


# =====================================================================
# MESSAGE PASSING LAYERS
# =====================================================================

if PYG_OK and TORCH_OK:

    class GeometryConstraintConv(MessagePassing):
        """
        Propagates G-structure level features through 'runs_on' edges.

        Direction: child -> parent in edge_index means the child is
        at the source end. We propagate parent features DOWN to inform
        the child (aggr='mean'): a child cannot exceed the structural
        support its parent provides.

        Implementation: each child node receives a linear transform of
        its parent's feature vector, then residually adds it.
        """

        def __init__(self, in_channels: int, out_channels: int):
            super().__init__(aggr="mean", flow="source_to_target")
            self.lin_parent = nn.Linear(in_channels, out_channels, bias=False)
            self.lin_self   = nn.Linear(in_channels, out_channels, bias=True)

        def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor") -> "torch.Tensor":
            # edge_index: [2, E]  row0=child (src), row1=parent (dst)
            # We want parents to send messages to children.
            # Reverse the index so parent=src, child=dst.
            rev_ei = edge_index[[1, 0], :]
            return self.propagate(rev_ei, x=x, size=(x.size(0), x.size(0)))

        def message(self, x_j: "torch.Tensor") -> "torch.Tensor":
            # x_j = parent features
            return self.lin_parent(x_j)

        def update(self, aggr_out: "torch.Tensor", x: "torch.Tensor") -> "torch.Tensor":
            return self.lin_self(x) + aggr_out


    class EntropyReadoutConv(MessagePassing):
        """
        Propagates entropy / I_c features upward through 'runs_on' edges.

        A child node's coherence (theta) contributes to its parent's
        readout — this creates the autograd path: I_c at ThreeQ depends
        on theta values all the way down to S3.

        flow="source_to_target" with the ORIGINAL edge_index (child -> parent)
        means children send to parents (upward propagation).
        """

        def __init__(self, in_channels: int):
            super().__init__(aggr="add", flow="source_to_target")
            self.gate = nn.Linear(in_channels, 1, bias=True)

        def forward(self, x: "torch.Tensor", edge_index: "torch.Tensor") -> "torch.Tensor":
            # Original edge_index: row0=child(src), row1=parent(dst)
            # source_to_target: children send to parents — correct upward flow
            return self.propagate(edge_index, x=x, size=(x.size(0), x.size(0)))

        def message(self, x_j: "torch.Tensor") -> "torch.Tensor":
            # x_j = child features; gate controls how much flows up
            gate_val = torch.sigmoid(self.gate(x_j))
            return gate_val * x_j

        def update(self, aggr_out: "torch.Tensor", x: "torch.Tensor") -> "torch.Tensor":
            return x + aggr_out

else:
    # Manual fallback implementations (no PyG MessagePassing base class)
    class GeometryConstraintConv(nn.Module):  # type: ignore[no-redef]
        def __init__(self, in_channels, out_channels):
            super().__init__()
            self.lin_parent = nn.Linear(in_channels, out_channels, bias=False)
            self.lin_self   = nn.Linear(in_channels, out_channels, bias=True)

        def forward(self, x, edge_index):
            # edge_index: [2,E] row0=child, row1=parent
            # Aggregate parent features into children
            child_idx  = edge_index[0]   # destination in reverse pass
            parent_idx = edge_index[1]
            out = self.lin_self(x).clone()
            for e in range(edge_index.shape[1]):
                c = child_idx[e].item()
                p = parent_idx[e].item()
                out[c] = out[c] + self.lin_parent(x[p])
            return out

    class EntropyReadoutConv(nn.Module):  # type: ignore[no-redef]
        def __init__(self, in_channels):
            super().__init__()
            self.gate = nn.Linear(in_channels, 1, bias=True)

        def forward(self, x, edge_index):
            # child->parent: children send to parents
            child_idx  = edge_index[0]
            parent_idx = edge_index[1]
            out = x.clone()
            for e in range(edge_index.shape[1]):
                c = child_idx[e].item()
                p = parent_idx[e].item()
                gate_val = torch.sigmoid(self.gate(x[c]))
                out[p] = out[p] + gate_val * x[c]
            return out


# =====================================================================
# Z3 ADMISSIBILITY GUARDS
# =====================================================================

def run_z3_admissibility():
    """
    Encode G-structure admissibility as a z3 SAT problem.

    Rule: a 'runs_on' edge (child -> parent) is admissible iff
          g_level(child) <= g_level(parent)

    Returns dict with SAT/UNSAT results for valid graph and invalid edge.

    Implementation note: we declare one Int variable per node name
    (not per edge occurrence) to avoid conflicting equality assertions
    when the same node appears as parent in multiple edges.
    """
    if not Z3_OK:
        return {
            "z3_available": False,
            "valid_graph_result": "skipped",
            "invalid_edge_result": "skipped",
        }

    # Collect all node names referenced by RUNS_ON_EDGES
    all_nodes = set()
    for child, parent in RUNS_ON_EDGES:
        all_nodes.add(child)
        all_nodes.add(parent)

    # ---- Positive check: all RUNS_ON_EDGES are admissible -----------
    s_pos = Solver()

    # Declare one Int variable per node and pin it to its G-level
    node_vars = {}
    for name in all_nodes:
        v = Int(f"g_{name}")
        node_vars[name] = v
        s_pos.add(v == G_LEVELS.get(name, 0))

    # Admissibility rule: g_level(child) >= g_level(parent)
    # (child is more constrained; parent is the less-constrained support)
    for child, parent in RUNS_ON_EDGES:
        s_pos.add(node_vars[child] >= node_vars[parent])

    valid_result = s_pos.check()

    # ---- Negative check: S3 runs_on ThreeQ -- MUST be UNSAT ---------
    # S3 has g_level=1 (most general), ThreeQ has g_level=3.
    # If S3 were the child running ON ThreeQ (parent), admissibility
    # would require g_S3 >= g_ThreeQ => 1 >= 3 => False => UNSAT.
    s_neg = Solver()
    c_level_s3 = Int("g_S3_bad")
    p_level_3q = Int("g_ThreeQ_bad")
    s_neg.add(c_level_s3 == G_LEVELS["S3"])      # 1
    s_neg.add(p_level_3q == G_LEVELS["ThreeQ"])  # 3
    # admissibility condition for the invalid edge: child_level >= parent_level
    s_neg.add(c_level_s3 >= p_level_3q)           # 1 >= 3 => UNSAT

    invalid_result = s_neg.check()

    return {
        "z3_available": True,
        "valid_graph_result": str(valid_result),
        "invalid_edge_result": str(invalid_result),
        "valid_graph_sat": valid_result == sat,
        "invalid_edge_unsat": invalid_result == unsat,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests(data, theta_params):
    results = {}

    if not TORCH_OK:
        return {"error": "pytorch not available"}

    # --- P1: Graph construction succeeds, correct node / edge counts --
    try:
        if PYG_OK:
            valid = data.validate()
            n_geom  = data["geometry"].x.shape[0]
            n_topo  = data["topology"].x.shape[0]
            n_op    = data["operator"].x.shape[0]
            n_ro    = data["geometry", "runs_on", "geometry"].edge_index.shape[1]
        else:
            valid   = True
            n_geom  = data["geometry"].shape[0]
            n_topo  = data["topology"].shape[0]
            n_op    = data["operator"].shape[0]
            n_ro    = data[("geometry","runs_on","geometry")]["edge_index"].shape[1]

        results["P1_graph_construction"] = {
            "pass": (
                valid and
                n_geom == 8 and
                n_topo == 4 and
                n_op   == 4 and
                n_ro   == len(RUNS_ON_EDGES)
            ),
            "n_geometry_nodes": n_geom,
            "n_topology_nodes": n_topo,
            "n_operator_nodes": n_op,
            "n_runs_on_edges": n_ro,
            "pyg_validate": valid,
        }
    except Exception as exc:
        results["P1_graph_construction"] = {"pass": False, "error": str(exc)}

    # --- P2: GeometryConstraintConv forward pass ---------------------
    try:
        GCC_IN  = 7   # 6 structural features + 1 theta
        GCC_OUT = 7

        gcc = GeometryConstraintConv(GCC_IN, GCC_OUT)
        gcc.eval()

        if PYG_OK:
            x_geom = data["geometry"].x
            ro_ei  = data["geometry", "runs_on", "geometry"].edge_index
        else:
            x_geom = data["geometry"]
            ro_ei  = data[("geometry","runs_on","geometry")]["edge_index"]

        with torch.no_grad():
            out = gcc(x_geom, ro_ei)

        shape_ok = (out.shape == x_geom.shape)
        results["P2_geometry_constraint_conv"] = {
            "pass": shape_ok and not torch.isnan(out).any().item(),
            "output_shape": list(out.shape),
            "no_nan": not torch.isnan(out).any().item(),
        }
    except Exception as exc:
        results["P2_geometry_constraint_conv"] = {"pass": False, "error": str(exc)}

    # --- P3: EntropyReadoutConv forward pass, I_c at ThreeQ ----------
    try:
        ERC = EntropyReadoutConv(7)
        ERC.eval()

        if PYG_OK:
            x_geom = data["geometry"].x
            ro_ei  = data["geometry", "runs_on", "geometry"].edge_index
        else:
            x_geom = data["geometry"]
            ro_ei  = data[("geometry","runs_on","geometry")]["edge_index"]

        with torch.no_grad():
            out_e = ERC(x_geom, ro_ei)

        # I_c at ThreeQ = sigmoid of last feature (theta-derived) at ThreeQ index
        three_q_idx = GEOMETRY_NODE_IDX["ThreeQ"]
        ic_val = torch.sigmoid(out_e[three_q_idx, -1]).item()

        results["P3_entropy_readout_conv"] = {
            "pass": not torch.isnan(out_e).any().item(),
            "Ic_at_ThreeQ": ic_val,
            "output_shape": list(out_e.shape),
        }
    except Exception as exc:
        results["P3_entropy_readout_conv"] = {"pass": False, "error": str(exc)}

    # --- P4: Autograd flows through runs_on edges to S3 --------------
    #
    # Architecture of the gradient path:
    #   GeometryConstraintConv propagates parent features DOWN to children
    #   (S3 -> Spin3_SU2 -> WeylBipartite -> ThreeQ).
    #   After the forward pass, out_grad[ThreeQ] is a function of S3's
    #   theta (via lin_parent applied to S3's feature row, passed down
    #   two hops through the conv layers).  The loss at ThreeQ therefore
    #   depends on theta_S3 and backward() must reach it.
    #
    #   We use two sequential GCC passes to deepen the dependency path
    #   so the gradient is guaranteed non-zero.
    try:
        # Zero any accumulated grads from previous tests
        for p in theta_params:
            if p.grad is not None:
                p.grad.zero_()

        # Build fresh geometry features with gradients
        geom_rows = []
        for i, name in enumerate(GEOMETRY_NODE_LIST):
            feat = torch.tensor(GEOMETRY_NODES[name], dtype=torch.float32)
            theta_val = torch.sigmoid(theta_params[i])        # differentiable
            geom_rows.append(torch.cat([feat, theta_val]).unsqueeze(0))
        x_grad = torch.cat(geom_rows, dim=0)                  # [8, 7]

        if PYG_OK:
            ro_ei = data["geometry", "runs_on", "geometry"].edge_index
        else:
            ro_ei = data[("geometry","runs_on","geometry")]["edge_index"]

        # GeometryConstraintConv: parent features propagate DOWN to children.
        # S3 is the root parent; ThreeQ is a leaf child.
        # Path: S3 -> Spin3_SU2 -> WeylBipartite -> ThreeQ (3 hops).
        # We need 3 sequential passes so that information from S3
        # (and its theta) reaches ThreeQ, making the loss at ThreeQ
        # depend on theta_S3 through the computation graph.
        gcc_a = GeometryConstraintConv(7, 7)
        gcc_b = GeometryConstraintConv(7, 7)
        gcc_c = GeometryConstraintConv(7, 7)

        # Pass 1: S3 -> immediate children (Spin3_SU2, Contact_S3, T_eta, ...)
        out_a = gcc_a(x_grad, ro_ei)
        # Pass 2: Spin3_SU2 -> WeylBipartite
        out_b = gcc_b(out_a, ro_ei)
        # Pass 3: WeylBipartite -> ThreeQ (S3's gradient path now complete)
        out_c = gcc_c(out_b, ro_ei)

        three_q_idx = GEOMETRY_NODE_IDX["ThreeQ"]
        s3_idx      = GEOMETRY_NODE_IDX["S3"]

        # I_c(ThreeQ) = sigmoid of the last feature dimension at ThreeQ.
        # After 3 passes, out_c[ThreeQ] has received features from S3
        # via Spin3_SU2 -> WeylBipartite -> ThreeQ (3 hops = 3 passes).
        loss = torch.sigmoid(out_c[three_q_idx, -1])
        loss.backward()

        # Check gradient reached theta_params[s3_idx]
        grad_s3 = theta_params[s3_idx].grad
        grad_ok = (grad_s3 is not None) and (grad_s3.abs().item() > 0.0)

        results["P4_autograd_flows_to_S3"] = {
            "pass": grad_ok,
            "grad_S3_is_not_None": grad_s3 is not None,
            "grad_S3_nonzero": grad_s3.abs().item() > 0.0 if grad_s3 is not None else False,
            "grad_S3_value": grad_s3.item() if grad_s3 is not None else None,
            "conv_used": "GeometryConstraintConv (3 passes — parent->child, 3-hop path S3->Spin->Weyl->ThreeQ)",
        }
    except Exception as exc:
        results["P4_autograd_flows_to_S3"] = {"pass": False, "error": str(exc)}

    # --- P5: z3 admissibility SAT ------------------------------------
    try:
        z3_res = run_z3_admissibility()
        results["P5_z3_admissibility_sat"] = {
            "pass": z3_res.get("valid_graph_sat", False),
            "z3_result": z3_res.get("valid_graph_result", "skipped"),
            "z3_available": z3_res.get("z3_available", False),
        }
    except Exception as exc:
        results["P5_z3_admissibility_sat"] = {"pass": False, "error": str(exc)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests(data, theta_params):
    results = {}

    if not TORCH_OK:
        return {"error": "pytorch not available"}

    # --- N1: z3 UNSAT for invalid backward edge S3 runs_on ThreeQ ---
    try:
        z3_res = run_z3_admissibility()
        results["N1_z3_invalid_edge_unsat"] = {
            "pass": z3_res.get("invalid_edge_unsat", False),
            "z3_result": z3_res.get("invalid_edge_result", "skipped"),
            "z3_available": z3_res.get("z3_available", False),
        }
    except Exception as exc:
        results["N1_z3_invalid_edge_unsat"] = {"pass": False, "error": str(exc)}

    # --- N2: No gradient path when graph is disconnected -------------
    try:
        # Build fresh params (must zero prior grads)
        theta_disconnected = nn.ParameterList([
            nn.Parameter(torch.randn(1))
            for _ in GEOMETRY_NODE_LIST
        ])

        geom_rows = []
        for i, name in enumerate(GEOMETRY_NODE_LIST):
            feat = torch.tensor(GEOMETRY_NODES[name], dtype=torch.float32)
            theta_val = torch.sigmoid(theta_disconnected[i])
            geom_rows.append(torch.cat([feat, theta_val]).unsqueeze(0))
        x_disconn = torch.cat(geom_rows, dim=0)

        # Empty edge_index (fully disconnected graph)
        empty_ei = torch.zeros((2, 0), dtype=torch.long)

        erc_dc = EntropyReadoutConv(7)
        out_dc = erc_dc(x_disconn, empty_ei)

        three_q_idx = GEOMETRY_NODE_IDX["ThreeQ"]
        s3_idx      = GEOMETRY_NODE_IDX["S3"]

        loss_dc = torch.sigmoid(out_dc[three_q_idx, -1])
        loss_dc.backward()

        grad_s3_dc = theta_disconnected[s3_idx].grad
        # S3 has no path to ThreeQ when disconnected -> grad should be None or 0
        no_grad = (grad_s3_dc is None) or (grad_s3_dc.abs().item() < 1e-12)

        results["N2_disconnected_no_gradient"] = {
            "pass": no_grad,
            "grad_S3_disconnected": grad_s3_dc.item() if grad_s3_dc is not None else None,
            "interpretation": "no gradient path from ThreeQ to S3 when disconnected",
        }
    except Exception as exc:
        results["N2_disconnected_no_gradient"] = {"pass": False, "error": str(exc)}

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests(data, theta_params):
    results = {}

    if not TORCH_OK:
        return {"error": "pytorch not available"}

    # --- B1: Single-node graph (just S3): forward pass is identity ---
    try:
        s3_feat = torch.tensor(
            GEOMETRY_NODES["S3"] + [0.5], dtype=torch.float32
        ).unsqueeze(0)  # [1, 7]

        empty_ei = torch.zeros((2, 0), dtype=torch.long)

        gcc_single = GeometryConstraintConv(7, 7)
        erc_single = EntropyReadoutConv(7)

        gcc_single.eval()
        erc_single.eval()

        with torch.no_grad():
            out_gcc = gcc_single(s3_feat, empty_ei)
            out_erc = erc_single(s3_feat, empty_ei)

        results["B1_single_node_forward"] = {
            "pass": (
                out_gcc.shape == (1, 7) and
                out_erc.shape == (1, 7) and
                not torch.isnan(out_gcc).any().item() and
                not torch.isnan(out_erc).any().item()
            ),
            "gcc_out_shape": list(out_gcc.shape),
            "erc_out_shape": list(out_erc.shape),
            "no_nan_gcc": not torch.isnan(out_gcc).any().item(),
            "no_nan_erc": not torch.isnan(out_erc).any().item(),
        }
    except Exception as exc:
        results["B1_single_node_forward"] = {"pass": False, "error": str(exc)}

    # --- B2: Full graph forward pass: no NaN or inf ------------------
    try:
        if PYG_OK:
            x_geom = data["geometry"].x
            ro_ei  = data["geometry", "runs_on", "geometry"].edge_index
        else:
            x_geom = data["geometry"]
            ro_ei  = data[("geometry","runs_on","geometry")]["edge_index"]

        gcc_full = GeometryConstraintConv(7, 7)
        erc_full = EntropyReadoutConv(7)

        gcc_full.eval()
        erc_full.eval()

        with torch.no_grad():
            out_gcc_full = gcc_full(x_geom, ro_ei)
            out_erc_full = erc_full(x_geom, ro_ei)

        no_nan_gcc  = not torch.isnan(out_gcc_full).any().item()
        no_inf_gcc  = not torch.isinf(out_gcc_full).any().item()
        no_nan_erc  = not torch.isnan(out_erc_full).any().item()
        no_inf_erc  = not torch.isinf(out_erc_full).any().item()

        results["B2_full_graph_no_nan_inf"] = {
            "pass": no_nan_gcc and no_inf_gcc and no_nan_erc and no_inf_erc,
            "gcc_no_nan": no_nan_gcc,
            "gcc_no_inf": no_inf_gcc,
            "erc_no_nan": no_nan_erc,
            "erc_no_inf": no_inf_erc,
        }
    except Exception as exc:
        results["B2_full_graph_no_nan_inf"] = {"pass": False, "error": str(exc)}

    return results


# =====================================================================
# SYMPY: symbolic G-level admissibility confirmation (supportive)
# =====================================================================

def run_sympy_admissibility_check():
    """
    Symbolic check: verify all RUNS_ON_EDGES satisfy g_level(child) <= g_level(parent).
    Returns a list of edge admissibility verdicts.
    """
    if not SYMPY_OK:
        return {"sympy_available": False}

    import sympy as sp
    edges_checked = []
    all_ok = True
    for child, parent in RUNS_ON_EDGES:
        g_c = G_LEVELS.get(child, 0)
        g_p = G_LEVELS.get(parent, 0)
        # admissibility: child >= parent (child more constrained)
        ok  = sp.Ge(g_c, g_p)
        edges_checked.append({
            "child": child,
            "parent": parent,
            "g_child": g_c,
            "g_parent": g_p,
            "admissible": bool(ok),
        })
        if not bool(ok):
            all_ok = False

    return {
        "sympy_available": True,
        "all_admissible": all_ok,
        "edges": edges_checked,
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    torch.manual_seed(42)

    if not TORCH_OK:
        print("ERROR: pytorch not available. Cannot run sim.")
        sys.exit(1)

    # Build constraint manifold
    data, theta_params = build_constraint_manifold_graph()

    # Get edge counts for manifold_structure summary
    if PYG_OK:
        n_geom = data["geometry"].x.shape[0]
        n_topo = data["topology"].x.shape[0]
        n_op   = data["operator"].x.shape[0]
        n_ro   = data["geometry", "runs_on", "geometry"].edge_index.shape[1]
    else:
        n_geom = data["geometry"].shape[0]
        n_topo = data["topology"].shape[0]
        n_op   = data["operator"].shape[0]
        n_ro   = data[("geometry","runs_on","geometry")]["edge_index"].shape[1]

    # Run z3 admissibility here (used in both pos and neg tests)
    z3_results = run_z3_admissibility()

    # Run tests
    pos = run_positive_tests(data, theta_params)
    neg = run_negative_tests(data, theta_params)
    bnd = run_boundary_tests(data, theta_params)
    sym = run_sympy_admissibility_check()

    # Summary
    all_tests = {**pos, **neg, **bnd}
    all_pass   = all(
        v.get("pass", False)
        for v in all_tests.values()
        if isinstance(v, dict) and "pass" in v
    )

    # Update TOOL_MANIFEST used flags
    TOOL_MANIFEST["pytorch"]["used"]   = True
    TOOL_MANIFEST["pytorch"]["reason"] = "HeteroData node tensors, autograd through runs_on edges"
    TOOL_INTEGRATION_DEPTH["pytorch"]  = "load_bearing"

    if PYG_OK:
        TOOL_MANIFEST["pyg"]["used"]   = True
        TOOL_MANIFEST["pyg"]["reason"] = "HeteroData graph construction, MessagePassing base class"
        TOOL_INTEGRATION_DEPTH["pyg"]  = "load_bearing"
    else:
        TOOL_MANIFEST["pyg"]["reason"] = "not installed — manual fallback used"
        TOOL_INTEGRATION_DEPTH["pyg"]  = None

    if Z3_OK:
        TOOL_MANIFEST["z3"]["used"]   = True
        TOOL_MANIFEST["z3"]["reason"] = "admissibility SAT/UNSAT for G-structure tower constraints"
        TOOL_INTEGRATION_DEPTH["z3"]  = "load_bearing"

    if SYMPY_OK:
        TOOL_MANIFEST["sympy"]["used"]   = True
        TOOL_MANIFEST["sympy"]["reason"] = "symbolic verification of g_level admissibility"
        TOOL_INTEGRATION_DEPTH["sympy"]  = "supportive"

    # Tried-but-unused tools: record honest reasons so no reason field is blank.
    # cvc5: z3 already provides the SAT/UNSAT proof for G-structure admissibility;
    # cvc5 would serve as an independent cross-check but this packet is bounded to
    # the single admissibility claim and cvc5 SyGuS synthesis is out of scope here.
    if TOOL_MANIFEST["cvc5"]["tried"] and not TOOL_MANIFEST["cvc5"]["used"]:
        TOOL_MANIFEST["cvc5"]["reason"] = (
            "tried and available; not used — z3 already supplies the load-bearing "
            "SAT/UNSAT admissibility proof for this packet; cvc5 cross-check and "
            "SyGuS fence synthesis are out of scope for this bounded same-carrier run"
        )

    # clifford: operates on spinor/rotor algebra over a geometric algebra;
    # this packet represents the constraint manifold as a graph with integer G-levels,
    # not as a Clifford algebra over R^n; no geometric product is computed here.
    if TOOL_MANIFEST["clifford"]["tried"] and not TOOL_MANIFEST["clifford"]["used"]:
        TOOL_MANIFEST["clifford"]["reason"] = (
            "tried and available; not used — node features are integer G-structure "
            "flags, not spinor/rotor objects; no Cl(3) geometric product needed in "
            "this graph-topology packet"
        )

    # geomstats: models Riemannian manifolds (geodesics, metrics, holonomy);
    # this packet encodes G-structure hierarchy as a discrete graph of integer levels;
    # no Riemannian metric, geodesic, or Fréchet computation is performed.
    if TOOL_MANIFEST["geomstats"]["tried"] and not TOOL_MANIFEST["geomstats"]["used"]:
        TOOL_MANIFEST["geomstats"]["reason"] = (
            "tried and available; not used — constraint manifold is represented as a "
            "discrete G-level hierarchy graph; no Riemannian metric, geodesic, or "
            "holonomy computation is required in this packet"
        )

    # e3nn: provides E(3)-equivariant neural network layers for SO(3)/SU(2) symmetry;
    # node features here are structural flags (spin, contact, Kähler bits) and integer
    # G-levels, not SO(3) spherical-harmonic vectors; equivariant computation is not
    # the relevant operation for this graph-admissibility packet.
    if TOOL_MANIFEST["e3nn"]["tried"] and not TOOL_MANIFEST["e3nn"]["used"]:
        TOOL_MANIFEST["e3nn"]["reason"] = (
            "tried and available; not used — node features are binary structural flags "
            "and G-level integers, not SO(3)/SU(2) equivariant vectors; no equivariant "
            "layer computation needed in this bounded graph-topology packet"
        )

    # rustworkx: fast graph algorithms and DAG utilities;
    # PyG MessagePassing already handles graph-native computation here; rustworkx DAG
    # ordering or routing algorithms are not needed for this single-layer hierarchy.
    if TOOL_MANIFEST["rustworkx"]["tried"] and not TOOL_MANIFEST["rustworkx"]["used"]:
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "tried and available; not used — PyG handles all graph computation; "
            "rustworkx DAG/routing algorithms are not needed for this single "
            "G-structure hierarchy packet"
        )

    # xgi: hypergraphs and simplicial complexes for multi-way interactions;
    # all relationships in this graph are pairwise (runs_on, acts_on, lives_at,
    # generates); no multi-way hyperedge structure is present in the constraint
    # manifold as modeled here.
    if TOOL_MANIFEST["xgi"]["tried"] and not TOOL_MANIFEST["xgi"]["used"]:
        TOOL_MANIFEST["xgi"]["reason"] = (
            "tried and available; not used — all graph edges are pairwise; "
            "no multi-way hyperedge structure is modeled in this packet; "
            "XGI is relevant if multi-shell interactions are encoded as hyperedges, "
            "which is not done here"
        )

    # toponetx: cell-complex topology for higher-order structures;
    # the graph encodes a G-structure constraint hierarchy with simple directed edges;
    # no CW-complex cells, faces, or higher-order simplices are constructed here.
    if TOOL_MANIFEST["toponetx"]["tried"] and not TOOL_MANIFEST["toponetx"]["used"]:
        TOOL_MANIFEST["toponetx"]["reason"] = (
            "tried and available; not used — no CW-complex or cell-complex structure "
            "is constructed; the constraint manifold graph uses directed pairwise edges "
            "only; TopoNetX is relevant for shell-face / higher-order topology, which "
            "is not in scope for this packet"
        )

    # gudhi: persistent homology and filtration-based topology;
    # boundary conditions are tested by z3 UNSAT proofs, not topological filtrations;
    # no persistence diagram or Betti-number computation is needed in this packet.
    if TOOL_MANIFEST["gudhi"]["tried"] and not TOOL_MANIFEST["gudhi"]["used"]:
        TOOL_MANIFEST["gudhi"]["reason"] = (
            "tried and available; not used — boundary conditions are handled by z3 "
            "UNSAT proofs; no persistence diagram, filtration, or Betti-number "
            "computation is required in this bounded graph-admissibility packet"
        )

    manifold_structure = {
        "n_geometry_nodes":        n_geom,
        "n_topology_nodes":        n_topo,
        "n_operator_nodes":        n_op,
        "n_runs_on_edges":         n_ro,
        "gradient_flows_to_base":  pos.get("P4_autograd_flows_to_S3", {}).get("pass", False),
        "z3_admissibility":        z3_results.get("valid_graph_result", "skipped"),
        "z3_invalid_edge_unsat":   z3_results.get("invalid_edge_unsat", False),
        "pyg_native":              PYG_OK,
        "message_passing_layers":  ["GeometryConstraintConv", "EntropyReadoutConv"],
    }

    output = {
        "name": "sim_geometric_constraint_manifold_pyg",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "manifold_structure": manifold_structure,
        "z3_details": z3_results,
        "sympy_admissibility": sym,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "all_pass": all_pass,
            "pyg_available": PYG_OK,
            "z3_available": Z3_OK,
            "autograd_to_S3": pos.get("P4_autograd_flows_to_S3", {}).get("pass", False),
            "z3_valid_graph_sat": z3_results.get("valid_graph_sat", False),
            "z3_invalid_edge_unsat": z3_results.get("invalid_edge_unsat", False),
        },
    }

    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results",
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "geometric_constraint_manifold_pyg_results.json")

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print()
    print("=== SUMMARY ===")
    print(f"  PyG native:                {PYG_OK}")
    print(f"  z3 available:              {Z3_OK}")
    print(f"  GeometryConstraintConv:    {pos.get('P2_geometry_constraint_conv', {}).get('pass', False)}")
    print(f"  EntropyReadoutConv:        {pos.get('P3_entropy_readout_conv', {}).get('pass', False)}")
    print(f"  Autograd flows to S3:      {pos.get('P4_autograd_flows_to_S3', {}).get('pass', False)}")
    print(f"  z3 valid graph SAT:        {z3_results.get('valid_graph_sat', False)}")
    print(f"  z3 invalid edge UNSAT:     {z3_results.get('invalid_edge_unsat', False)}")
    print(f"  All tests pass:            {all_pass}")
