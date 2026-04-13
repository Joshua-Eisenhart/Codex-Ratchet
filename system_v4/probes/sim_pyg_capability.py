#!/usr/bin/env python3
"""
sim_pyg_capability -- Bounded tool-capability probe for torch_geometric (PyG).

Governing rule (owner+Hermes 2026-04-13): PyG is currently load_bearing in several
canonical sims with NO capability probe. This sim is the bounded isolation probe
that unblocks PyG for nonclassical use.

Contract: ~/wiki/concepts/tool-capability-sim-program.md
Template: system_v4/probes/SIM_TEMPLATE.py

Witness use-cases (actual load-bearing uses of PyG in this repo):
  - system_v4/probes/sim_pyg_dynamic_edge_werner.py
  - system_v4/probes/sim_geometric_constraint_manifold_pyg.py
  - system_v4/probes/sim_foundation_equivariant_graph_backprop.py

Tests (in isolation):
  1. Data / Batch construction with node/edge tensors         (positive)
  2. MessagePassing forward matches hand-computed             (positive, load-bearing)
  3. GCNConv / GATConv shape + gradient flow through autograd (positive)
  4. edge_index <-> dense adjacency round-trip                (positive)
  5. Baseline: raw torch scatter_add matches PyG message pass (comparison surface)
  6. Failure: mismatched edge_index / invalid graph raises     (boundary)
"""

import json
import os
import traceback

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "tensor/autograd backend -- overwritten on import"},
    "pyg":       {"tried": False, "used": False, "reason": "tool under capability test -- overwritten on import"},
    "z3":        {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "no proof obligation in a capability probe"},
    "sympy":     {"tried": False, "used": False, "reason": "no symbolic derivation required"},
    "clifford":  {"tried": False, "used": False, "reason": "no geometric algebra needed for graph MP probe"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold structure in this probe"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariant NN required"},
    "rustworkx": {"tried": False, "used": False, "reason": "PyG internal aggregation is what's under test, not external graph lib"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph / multi-way interaction"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell/simplicial complex needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistent homology in this probe"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None

try:
    import torch_geometric  # noqa: F401
    from torch_geometric.data import Data, Batch
    from torch_geometric.nn import MessagePassing, GCNConv, GATConv
    from torch_geometric.utils import to_dense_adj, dense_to_sparse
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"


# =====================================================================
# Helpers
# =====================================================================

class SumAggMP(MessagePassing):
    """Hand-verifiable message-passing: sum of neighbor features, no self-loop."""
    def __init__(self):
        super().__init__(aggr="add", flow="source_to_target")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def _small_graph():
    # 4 nodes, directed edges (src -> dst):
    # 0->1, 0->2, 1->2, 2->3, 3->1
    edge_index = torch.tensor(
        [[0, 0, 1, 2, 3],
         [1, 2, 2, 3, 1]], dtype=torch.long)
    x = torch.tensor([[1.0, 0.0],
                      [0.0, 1.0],
                      [1.0, 1.0],
                      [2.0, -1.0]], dtype=torch.float)
    return x, edge_index


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # 1. Data / Batch construction
    try:
        x, edge_index = _small_graph()
        d1 = Data(x=x, edge_index=edge_index)
        d2 = Data(x=x + 10.0, edge_index=edge_index)
        batch = Batch.from_data_list([d1, d2])
        ok = (
            d1.num_nodes == 4 and d1.num_edges == 5
            and batch.num_nodes == 8 and batch.num_edges == 10
            and batch.batch.tolist() == [0, 0, 0, 0, 1, 1, 1, 1]
        )
        results["data_batch_construction"] = {"pass": bool(ok)}
    except Exception as e:
        results["data_batch_construction"] = {"pass": False, "error": repr(e)}

    # 2. MessagePassing matches hand-computed (load-bearing)
    try:
        x, edge_index = _small_graph()
        mp = SumAggMP()
        out = mp(x, edge_index).detach()
        # dst=1 receives from src 0, 3 -> x[0]+x[3] = [3, -1]
        # dst=2 receives from src 0, 1 -> x[0]+x[1] = [1, 1]
        # dst=3 receives from src 2   -> x[2]        = [1, 1]
        # dst=0 receives nothing      -> [0, 0]
        expected = torch.tensor([[0.0, 0.0],
                                 [3.0, -1.0],
                                 [1.0, 1.0],
                                 [1.0, 1.0]])
        match = torch.allclose(out, expected, atol=1e-6)
        results["message_passing_hand_match"] = {
            "pass": bool(match),
            "out": out.tolist(),
            "expected": expected.tolist(),
        }
    except Exception as e:
        results["message_passing_hand_match"] = {"pass": False, "error": repr(e)}

    # 3. GCNConv / GATConv shape + gradient flow
    try:
        x, edge_index = _small_graph()
        x = x.clone().requires_grad_(True)
        gcn = GCNConv(2, 3)
        gat = GATConv(2, 3, heads=2, concat=False)
        yg = gcn(x, edge_index)
        ya = gat(x, edge_index)
        loss = yg.sum() + ya.sum()
        loss.backward()
        grad_ok = x.grad is not None and torch.isfinite(x.grad).all().item()
        shape_ok = yg.shape == (4, 3) and ya.shape == (4, 3)
        results["gcn_gat_autograd"] = {
            "pass": bool(grad_ok and shape_ok),
            "yg_shape": list(yg.shape),
            "ya_shape": list(ya.shape),
            "grad_finite": bool(grad_ok),
        }
    except Exception as e:
        results["gcn_gat_autograd"] = {"pass": False, "error": repr(e)}

    # 4. edge_index <-> dense adjacency round-trip
    try:
        _, edge_index = _small_graph()
        A = to_dense_adj(edge_index, max_num_nodes=4)[0]  # [4,4]
        ei2, _ = dense_to_sparse(A)
        # Compare edge sets (order may differ)
        s1 = set(map(tuple, edge_index.t().tolist()))
        s2 = set(map(tuple, ei2.t().tolist()))
        results["edge_index_adjacency_roundtrip"] = {
            "pass": s1 == s2,
            "A_shape": list(A.shape),
            "edges": sorted(list(s1)),
        }
    except Exception as e:
        results["edge_index_adjacency_roundtrip"] = {"pass": False, "error": repr(e)}

    # 5. Baseline: raw torch scatter_add matches PyG sum MP
    try:
        x, edge_index = _small_graph()
        src, dst = edge_index[0], edge_index[1]
        baseline = torch.zeros_like(x)
        baseline.index_add_(0, dst, x[src])
        mp = SumAggMP()
        pyg_out = mp(x, edge_index).detach()
        match = torch.allclose(baseline, pyg_out, atol=1e-6)
        results["baseline_scatter_vs_pyg"] = {
            "pass": bool(match),
            "baseline": baseline.tolist(),
            "pyg": pyg_out.tolist(),
        }
    except Exception as e:
        results["baseline_scatter_vs_pyg"] = {"pass": False, "error": repr(e)}

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # N1: mismatched message-passing output must NOT equal a wrong expected
    try:
        x, edge_index = _small_graph()
        mp = SumAggMP()
        out = mp(x, edge_index).detach()
        wrong = torch.zeros_like(out)
        results["mp_not_equal_zero"] = {
            "pass": not torch.allclose(out, wrong),
        }
    except Exception as e:
        results["mp_not_equal_zero"] = {"pass": False, "error": repr(e)}

    # N2: permuting edge_index src/dst must change output (directed flow)
    try:
        x, edge_index = _small_graph()
        mp = SumAggMP()
        out = mp(x, edge_index).detach()
        flipped = edge_index.flip(0)
        out_flip = mp(x, flipped).detach()
        results["direction_matters"] = {
            "pass": not torch.allclose(out, out_flip),
        }
    except Exception as e:
        results["direction_matters"] = {"pass": False, "error": repr(e)}

    return results


# =====================================================================
# BOUNDARY / FAILURE-MODE TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # B1: edge_index with out-of-range node id should raise (or produce invalid index)
    try:
        x, _ = _small_graph()  # 4 nodes
        bad_ei = torch.tensor([[0, 5], [1, 2]], dtype=torch.long)  # 5 is out of range
        mp = SumAggMP()
        raised = False
        err = ""
        try:
            _ = mp(x, bad_ei)
        except Exception as e:
            raised = True
            err = type(e).__name__
        results["out_of_range_node"] = {
            "pass": bool(raised),
            "error_type": err,
            "note": "PyG/torch should reject indexing beyond x.size(0)",
        }
    except Exception as e:
        results["out_of_range_node"] = {"pass": False, "error": repr(e)}

    # B2: wrong-shape edge_index (not [2, E]) should raise
    try:
        x, _ = _small_graph()
        mal_ei = torch.tensor([[0, 1, 2]], dtype=torch.long)  # shape [1,3]
        mp = SumAggMP()
        raised = False
        err = ""
        try:
            _ = mp(x, mal_ei)
        except Exception as e:
            raised = True
            err = type(e).__name__
        results["malformed_edge_index_shape"] = {
            "pass": bool(raised),
            "error_type": err,
        }
    except Exception as e:
        results["malformed_edge_index_shape"] = {"pass": False, "error": repr(e)}

    # B3: empty edge_index yields zero-message output (no crash)
    try:
        x, _ = _small_graph()
        empty_ei = torch.zeros((2, 0), dtype=torch.long)
        mp = SumAggMP()
        out = mp(x, empty_ei).detach()
        results["empty_edge_index"] = {
            "pass": bool(torch.allclose(out, torch.zeros_like(x))),
            "out": out.tolist(),
        }
    except Exception as e:
        results["empty_edge_index"] = {"pass": False, "error": repr(e)}

    # B4: disconnected components still aggregate per-component correctly
    try:
        x = torch.tensor([[1.0], [2.0], [10.0], [20.0]])
        ei = torch.tensor([[0, 2], [1, 3]], dtype=torch.long)  # two disconnected edges
        mp = SumAggMP()
        out = mp(x, ei).detach()
        expected = torch.tensor([[0.0], [1.0], [0.0], [10.0]])
        results["disconnected_components"] = {
            "pass": bool(torch.allclose(out, expected)),
            "out": out.tolist(),
        }
    except Exception as e:
        results["disconnected_components"] = {"pass": False, "error": repr(e)}

    return results


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    sections = {}
    try:
        sections["positive"] = run_positive_tests()
        sections["negative"] = run_negative_tests()
        sections["boundary"] = run_boundary_tests()
    except Exception:
        sections.setdefault("positive", {})["fatal"] = {
            "pass": False, "traceback": traceback.format_exc()
        }

    # Mark tool use
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "tensor ops, autograd through GCN/GAT, scatter_add baseline comparison"
    )
    TOOL_MANIFEST["pyg"]["used"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "Data/Batch, MessagePassing propagate, GCNConv/GATConv, "
        "to_dense_adj/dense_to_sparse round-trip -- the object under test"
    )
    TOOL_INTEGRATION_DEPTH["pyg"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

    all_pass = all(_all_pass(s) for s in sections.values())

    results = {
        "name": "sim_pyg_capability",
        "purpose": (
            "Bounded isolation probe of torch_geometric capabilities. "
            "Unblocks load-bearing PyG use in canonical sims."
        ),
        "witness_use_cases": [
            "system_v4/probes/sim_pyg_dynamic_edge_werner.py",
            "system_v4/probes/sim_geometric_constraint_manifold_pyg.py",
            "system_v4/probes/sim_foundation_equivariant_graph_backprop.py",
        ],
        "contract": "~/wiki/concepts/tool-capability-sim-program.md",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "classification": "canonical",
        "all_pass": bool(all_pass),
        "positive": sections.get("positive", {}),
        "negative": sections.get("negative", {}),
        "boundary": sections.get("boundary", {}),
        "summary": {
            "positive_all_pass": _all_pass(sections.get("positive", {})),
            "negative_all_pass": _all_pass(sections.get("negative", {})),
            "boundary_all_pass": _all_pass(sections.get("boundary", {})),
            "all_pass": bool(all_pass),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pyg_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass = {results['summary']['all_pass']}")
    print(f"summary  = {json.dumps(results['summary'], indent=2)}")
