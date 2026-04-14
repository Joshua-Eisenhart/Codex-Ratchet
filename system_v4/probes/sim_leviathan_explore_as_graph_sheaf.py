#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: sheaf over social graph.

Framing assumption:
  Each group holds a LOCAL section (vector of values). Restriction maps on
  edges define how neighbors must agree. Global sections = admissible
  civilizational states. Centralization = collapsing all stalks to rank-1.

Blind spot:
  - Linear restriction maps; real social coupling is nonlinear.
  - Stalk dimension fixed across groups.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"numpy": {"tried": True, "used": True, "reason": "linear sheaf sections"},
                 "toponetx": {"tried": False, "used": False, "reason": ""}}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "toponetx": None}
try:
    from toponetx.classes import CellComplex  # noqa
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["reason"] = "imported for future cell-complex lift"
    TOOL_INTEGRATION_DEPTH["toponetx"] = "decorative"
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"


def global_section_rank(edges, n_nodes, dim=3, restriction_rank=None):
    # Build block constraint matrix: for each edge (u,v): R_u * s_u - R_v * s_v = 0
    # Use identity restrictions (agreement on full stalk) unless rank<dim
    k = restriction_rank or dim
    R = np.eye(dim)[:k]
    M_rows = []
    for (u,v) in edges:
        row = np.zeros((k, n_nodes*dim))
        row[:, u*dim:(u+1)*dim] =  R
        row[:, v*dim:(v+1)*dim] = -R
        M_rows.append(row)
    M = np.vstack(M_rows) if M_rows else np.zeros((1,n_nodes*dim))
    # dim of kernel = global sections
    rank = np.linalg.matrix_rank(M)
    return n_nodes*dim - rank


def run_positive_tests():
    # connected 5-node graph, full restrictions => 1 global section per stalk dim
    edges = [(0,1),(1,2),(2,3),(3,4),(4,0)]
    gs = global_section_rank(edges, 5, dim=3)
    return {"global_section_dim": gs, "pass": gs == 3}

def run_negative_tests():
    # centralization: rank-1 restrictions everywhere => stalk collapse
    edges = [(0,1),(0,2),(0,3),(0,4)]
    gs = global_section_rank(edges, 5, dim=3, restriction_rank=1)
    # most of each stalk goes unconstrained relative to rank-1 agreement
    return {"rank1_gs": gs, "pass_gs_large": gs > 3}

def run_boundary_tests():
    gs = global_section_rank([(0,1)], 2, dim=2)
    return {"single_edge_gs": gs, "pass": gs == 2}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_graph_sheaf",
        "framing_assumption": "admissible civilizations = global sections of value-sheaf",
        "blind_spot": "linear restrictions; uniform stalk dim",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_graph_sheaf_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
