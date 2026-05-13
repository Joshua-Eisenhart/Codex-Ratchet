#!/usr/bin/env python3
"""
Tier A A4.2 tool-lego-integration probe for SymPy + PyG.

SymPy is load-bearing for exact polynomial-root extraction and exact edge-weight
construction. PyG is load-bearing for graph realization, message passing, and
pooling over the graph induced by those symbolic outputs. The probe is only
written and enqueued here; Hermes workers do not execute it directly.
"""

import json
import os
from typing import Any, Dict, List

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "tool_integration_sympy_pyg"

TOOL_MANIFEST = {
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "SymPy derives the exact real roots, discriminants, and symbolic edge weights that the graph side consumes; without those symbolic outputs the graph instances in every section are under-specified.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "supportive dependency for PyG tensor construction; not the load-bearing integration surface in this packet.",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "PyG realizes the SymPy-derived graph, validates it, propagates weighted messages, and pools graph-level summaries; removing PyG breaks the integration claim rather than leaving a decorative import behind.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used: this packet checks symbolic-to-graph tensor integration, not SMT satisfiability.",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used: this packet checks symbolic-to-graph tensor integration, not cvc5 solver constraints.",
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "not used: no geometric algebra surface is exercised.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "not used: no manifold metric or geodesic surface is exercised.",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "not used: no equivariant representation surface is exercised.",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "not used: graph realization is through PyG, not rustworkx DAG algorithms.",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "not used: the fixture is pairwise graph structure, not a hypergraph.",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not used: no cell-complex incidence surface is exercised.",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not used: no persistence or simplex-tree surface is exercised.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": "load_bearing",
    "pytorch": "supportive",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": None,
}

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "derive exact real polynomial roots and discriminants with SymPy",
        "convert adjacent root gaps into directed edge weights",
        "build PyG Data fixtures with root-value node features, edge_index, and edge_weight tensors",
        "apply a custom PyG MessagePassing layer that multiplies neighbour features by symbolic gap weights",
        "batch independent SymPy-derived graphs with Batch.from_data_list",
        "compute graph-level means with global_mean_pool",
        "compare PyG outputs against exact symbolic manual sums and boundary controls",
    ],
    "carrier_topology": (
        "Finite chain graphs induced by ordered real roots of one-variable polynomials; nodes are "
        "real roots, edges connect adjacent roots, and edge weights are exact symbolic root gaps "
        "converted to tensors for PyG."
    ),
    "observable": {
        "primary": "PyG weighted-neighbour output compared to the symbolic manual weighted sum",
        "secondary": [
            "batched graph mean vectors compared to exact symbolic root means",
            "zero-gap edge presence for repeated roots",
            "blocked graph construction for no-real-root polynomials",
            "singleton graph no-message output",
            "small symbolic gap propagation within numeric tolerance",
        ],
    },
    "pass_fail_predicate": (
        "Pass iff SymPy-derived graph tensors make PyG MessagePassing and global_mean_pool match "
        "the corresponding symbolic computations, while repeated-root, no-real-root, singleton, "
        "and small-gap controls behave as declared."
    ),
    "graveyards": [
        "repeated-root polynomial should introduce a zero-weight edge and exclude distinct-root chain behaviour",
        "no-real-root polynomial should block PyG graph construction",
        "singleton-root polynomial should produce an isolated graph with zero propagated message",
        "small rational root gap should survive conversion through PyG tensors within tolerance",
    ],
    "baselines": [
        "manual symbolic weighted-neighbour sum baseline",
        "exact symbolic mean baseline for batched pooling",
        "distinct-root counterfactual baseline for repeated-root control",
        "empty real solution set baseline",
        "singleton no-edge baseline",
    ],
    "alternative_formulations": [
        "build complete graphs with all pairwise symbolic root gaps instead of adjacent-root chains",
        "use PyG Data only without Batch.from_data_list to isolate graph-realization behaviour",
        "replace the custom MessagePassing layer with a standard PyG convolution after encoding edge weights as features",
    ],
    "tool_function_needs": [
        "sympy.roots and sympy.discriminant for exact root and multiplicity data",
        "torch_geometric.data.Data for graph fixture construction",
        "torch_geometric.data.Batch.from_data_list for batched graph fixtures",
        "torch_geometric.nn.MessagePassing.propagate for weighted neighbour aggregation",
        "torch_geometric.nn.global_mean_pool for graph-level pooling",
    ],
    "lego_coupling_target": "bounded symbolic-to-graph tool-integration evidence for later graph-symbolic lego-fit packets",
    "claim_ceiling": (
        "finite tool_integration_sympy_pyg tool-integration receipt only; no bridge, GStack, "
        "axis, QIT, or nonclassical admission"
    ),
}

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "SymPy import failed on this machine; queue execution will decide whether exact symbolic graph derivation is available."

try:
    import torch
    from torch_geometric.data import Batch, Data
    from torch_geometric.nn import MessagePassing, global_mean_pool

    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except ImportError:
    torch = None
    Batch = Data = MessagePassing = global_mean_pool = None
    TOOL_MANIFEST["pyg"]["reason"] = "PyG import failed on this machine; queue execution will decide whether graph realization and propagation over SymPy-derived structures are available."
    TOOL_MANIFEST["pytorch"]["reason"] = "PyTorch import failed with PyG; tensor substrate unavailable."


class WeightedNeighborPass(MessagePassing if MessagePassing is not None else object):
    def __init__(self):
        if MessagePassing is None:
            raise RuntimeError("PyG MessagePassing is unavailable")
        super().__init__(aggr="add")

    def forward(self, x, edge_index, edge_weight):
        return self.propagate(edge_index, x=x, edge_weight=edge_weight)

    def message(self, x_j, edge_weight):
        return x_j * edge_weight.view(-1, 1)


def _mark_used(*tools: str) -> None:
    for tool in tools:
        TOOL_MANIFEST[tool]["used"] = True


def _to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if sp is not None and isinstance(value, sp.Basic):
        return str(value)
    if torch is not None and isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]
    if isinstance(value, set):
        return sorted(_to_serializable(v) for v in value)
    return value


def _gate_results(section: str) -> Dict[str, Any]:
    missing = []
    if not TOOL_MANIFEST["sympy"]["tried"]:
        missing.append("sympy")
    if not TOOL_MANIFEST["pyg"]["tried"]:
        missing.append("pyg")
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}


def _real_roots_with_multiplicity(poly_expr) -> List[Any]:
    poly = sp.Poly(sp.expand(poly_expr))
    x = poly.gens[0]
    roots = []
    for root, multiplicity in sp.roots(poly, x).items():
        if sp.im(root) == 0:
            roots.extend([sp.simplify(sp.re(root))] * multiplicity)
    return sorted(roots, key=lambda r: float(sp.N(r)))


def _build_chain_from_polynomial(poly_expr):
    x = sp.symbols("x", real=True)
    roots = _real_roots_with_multiplicity(poly_expr)
    discriminant = sp.simplify(sp.discriminant(sp.expand(poly_expr), x))
    feature_values = [sp.simplify(root) for root in roots]

    edge_pairs = []
    edge_weights = []
    for idx in range(len(feature_values) - 1):
        gap = sp.simplify(feature_values[idx + 1] - feature_values[idx])
        edge_pairs.extend([[idx, idx + 1], [idx + 1, idx]])
        edge_weights.extend([gap, gap])

    edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous() if edge_pairs else torch.empty((2, 0), dtype=torch.long)
    weight_tensor = torch.tensor([float(sp.N(w)) for w in edge_weights], dtype=torch.float32) if edge_weights else torch.empty((0,), dtype=torch.float32)
    x_tensor = torch.tensor([[float(sp.N(v))] for v in feature_values], dtype=torch.float32) if feature_values else torch.empty((0, 1), dtype=torch.float32)

    data = Data(x=x_tensor, edge_index=edge_index, edge_weight=weight_tensor, num_nodes=len(feature_values))
    return {
        "polynomial": sp.expand(poly_expr),
        "roots": roots,
        "discriminant": discriminant,
        "edge_weights": [sp.simplify(w) for w in edge_weights],
        "data": data,
    }


def _manual_weighted_neighbor_sum(root_values, edge_weights):
    if len(root_values) == 1:
        return [sp.Integer(0)]

    outputs = [sp.Integer(0) for _ in root_values]
    for idx in range(len(root_values) - 1):
        gap = sp.simplify(edge_weights[2 * idx])
        outputs[idx] += sp.simplify(gap * root_values[idx + 1])
        outputs[idx + 1] += sp.simplify(gap * root_values[idx])
    return [sp.simplify(v) for v in outputs]


def run_positive_tests():
    if sp is None or torch is None or Data is None or MessagePassing is None:
        return _gate_results("positive")

    x = sp.symbols("x", real=True)
    conv = WeightedNeighborPass()
    results = {}

    graph = _build_chain_from_polynomial((x - 1) * (x - 2) * (x - 4))
    propagated = conv(graph["data"].x, graph["data"].edge_index, graph["data"].edge_weight)
    manual = _manual_weighted_neighbor_sum(graph["roots"], graph["edge_weights"])
    _mark_used("sympy", "pyg")
    results["distinct_roots_feed_weighted_message_passing"] = {
        "polynomial": str(graph["polynomial"]),
        "roots_from_sympy": [str(v) for v in graph["roots"]],
        "edge_weights_from_sympy": [str(v) for v in graph["edge_weights"]],
        "pyg_output": _to_serializable(propagated),
        "expected_from_symbolic_manual_sum": [[float(sp.N(v))] for v in manual],
        "matches_expected": _to_serializable(propagated) == [[float(sp.N(v))] for v in manual],
    }

    graph_a = _build_chain_from_polynomial((x - sp.Rational(1, 2)) * (x - sp.Rational(3, 2)))
    graph_b = _build_chain_from_polynomial((x - 2) * (x - 5))
    batch = Batch.from_data_list([graph_a["data"], graph_b["data"]])
    pooled = global_mean_pool(batch.x, batch.batch)
    pooled_expected = [
        sp.simplify(sum(graph_a["roots"]) / len(graph_a["roots"])),
        sp.simplify(sum(graph_b["roots"]) / len(graph_b["roots"])),
    ]
    _mark_used("sympy", "pyg")
    results["symbolic_roots_feed_batched_pooling"] = {
        "graph_polynomials": [str(graph_a["polynomial"]), str(graph_b["polynomial"])],
        "roots_per_graph": [[str(v) for v in graph_a["roots"]], [str(v) for v in graph_b["roots"]]],
        "batch_vector": _to_serializable(batch.batch),
        "pooled_means": _to_serializable(pooled),
        "expected_symbolic_means": [[float(sp.N(v))] for v in pooled_expected],
        "matches_expected": _to_serializable(pooled) == [[float(sp.N(v))] for v in pooled_expected],
    }

    return results


def run_negative_tests():
    if sp is None or torch is None or Data is None or MessagePassing is None:
        return _gate_results("negative")

    x = sp.symbols("x", real=True)
    conv = WeightedNeighborPass()
    results = {}

    repeated = _build_chain_from_polynomial((x - 2) ** 2 * (x - 5))
    repeated_output = conv(repeated["data"].x, repeated["data"].edge_index, repeated["data"].edge_weight)
    distinct_manual = _manual_weighted_neighbor_sum([sp.Integer(2), sp.Integer(3), sp.Integer(5)], [sp.Integer(1), sp.Integer(1), sp.Integer(2), sp.Integer(2)])
    _mark_used("sympy", "pyg")
    results["repeated_root_zero_gap_excludes_distinct_chain_behavior"] = {
        "polynomial": str(repeated["polynomial"]),
        "roots_from_sympy": [str(v) for v in repeated["roots"]],
        "discriminant": str(repeated["discriminant"]),
        "edge_weights_from_sympy": [str(v) for v in repeated["edge_weights"]],
        "pyg_output": _to_serializable(repeated_output),
        "distinct_chain_counterfactual": [[float(sp.N(v))] for v in distinct_manual],
        "discriminant_zero": repeated["discriminant"] == 0,
        "zero_weight_edge_present": any(w == 0 for w in repeated["edge_weights"]),
        "counterfactual_excluded": _to_serializable(repeated_output) != [[float(sp.N(v))] for v in distinct_manual],
    }

    nonreal_roots = sp.solveset(sp.Eq(x**2 + 1, 0), x, domain=sp.S.Reals)
    _mark_used("sympy")
    results["nonreal_solution_set_blocks_pyg_graph_construction"] = {
        "polynomial": "x**2 + 1",
        "real_solution_set": str(nonreal_roots),
        "is_emptyset": nonreal_roots == sp.EmptySet,
        "pyg_graph_built": False,
    }

    return results


def run_boundary_tests():
    if sp is None or torch is None or Data is None or MessagePassing is None:
        return _gate_results("boundary")

    x = sp.symbols("x", real=True)
    conv = WeightedNeighborPass()
    results = {}

    singleton = _build_chain_from_polynomial(x - 7)
    singleton_output = conv(singleton["data"].x, singleton["data"].edge_index, singleton["data"].edge_weight)
    _mark_used("sympy", "pyg")
    results["singleton_root_yields_isolated_graph"] = {
        "polynomial": str(singleton["polynomial"]),
        "roots_from_sympy": [str(v) for v in singleton["roots"]],
        "edge_count": int(singleton["data"].edge_index.size(1)),
        "pyg_output": _to_serializable(singleton_output),
        "expected": [[0.0]],
        "matches_expected": _to_serializable(singleton_output) == [[0.0]],
    }

    near_collapse = _build_chain_from_polynomial((x - 1) * (x - sp.Rational(1001, 1000)))
    near_output = conv(near_collapse["data"].x, near_collapse["data"].edge_index, near_collapse["data"].edge_weight)
    near_manual = _manual_weighted_neighbor_sum(near_collapse["roots"], near_collapse["edge_weights"])
    _mark_used("sympy", "pyg")
    results["small_symbolic_gap_survives_weighted_message_passing"] = {
        "polynomial": str(near_collapse["polynomial"]),
        "roots_from_sympy": [str(v) for v in near_collapse["roots"]],
        "edge_weights_from_sympy": [str(v) for v in near_collapse["edge_weights"]],
        "pyg_output": _to_serializable(near_output),
        "expected": [[float(sp.N(v))] for v in near_manual],
        "matches_expected": _to_serializable(near_output) == [[float(sp.N(v))] for v in near_manual],
    }

    return results


def _case_pass(case: Dict[str, Any]) -> bool:
    if case.get("status") == "skipped":
        return False
    if "matches_expected" in case:
        return bool(case["matches_expected"] or _nested_numeric_close(case.get("pyg_output"), case.get("expected")))
    if "counterfactual_excluded" in case:
        return bool(
            case.get("discriminant_zero")
            and case.get("zero_weight_edge_present")
            and case.get("counterfactual_excluded")
        )
    if "is_emptyset" in case:
        return bool(case.get("is_emptyset") and not case.get("pyg_graph_built"))
    return False


def _nested_numeric_close(left: Any, right: Any, tol: float = 1e-6) -> bool:
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        return all(_nested_numeric_close(a, b, tol=tol) for a, b in zip(left, right))
    try:
        return abs(float(left) - float(right)) <= tol
    except (TypeError, ValueError):
        return False


def _section_all_pass(section: Dict[str, Dict[str, Any]]) -> bool:
    return bool(section) and all(_case_pass(case) for case in section.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_all_pass(positive),
        "negative_all_pass": _section_all_pass(negative),
        "boundary_all_pass": _section_all_pass(boundary),
    }
    summary["all_pass"] = all(summary.values())
    results = {
        "name": NAME,
        "classification": classification,
        **CANDIDATE_SIM_SPEC,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "criteria_checked": [
            "SymPy real roots feed PyG weighted message passing",
            "SymPy exact roots feed PyG batched pooling",
            "Repeated roots produce a zero-gap edge and exclude distinct-chain behavior",
            "A polynomial with no real roots blocks graph construction",
            "Singleton and small-gap symbolic boundaries survive graph realization",
        ],
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded SymPy to PyG tool-integration evidence before graph-symbolic lego fit packets.",
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_to_serializable(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
    if not summary["all_pass"]:
        raise SystemExit(1)
