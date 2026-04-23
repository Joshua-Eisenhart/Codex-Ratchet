#!/usr/bin/env python3
"""
Canonical shell-local U(1) distinguishability probe via Wilson loops on a single cycle.

Distinguishability probe: different local flux angles on the same cycle produce different
Wilson loop values, while shifts by 2*pi remain gauge-indistinguishable.
"""

import cmath
import json
import math
import os

classification = "canonical"
NAME = "sim_u1_wilson_loop_distinguishability_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for the cycle-level Wilson loop probe"},
    "pyg": {"tried": False, "used": False, "reason": "message passing is not needed for a fixed single cycle"},
    "z3": {"tried": False, "used": False, "reason": "SMT is not needed for direct Wilson loop comparisons"},
    "cvc5": {"tried": False, "used": False, "reason": "direct cycle evaluation suffices for the local distinguishability probe"},
    "sympy": {"tried": False, "used": False, "reason": "sympy checks exp(i(alpha+2*pi))=exp(i alpha) for gauge-indistinguishable shifts"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar Wilson loop phases"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for a single graph cycle"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this shell-local cycle probe"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx provides the load-bearing cycle object and cycle-basis witness"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for a one-cycle Wilson loop"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for the graph-only Wilson loop probe"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for this single cycle graph"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["rustworkx"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

for _name, _importer in [
    ("pytorch", lambda: __import__("torch")),
    ("pyg", lambda: __import__("torch_geometric")),
    ("z3", lambda: __import__("z3")),
    ("cvc5", lambda: __import__("cvc5")),
    ("clifford", lambda: __import__("clifford")),
    ("geomstats", lambda: __import__("geomstats")),
    ("e3nn", lambda: __import__("e3nn")),
    ("xgi", lambda: __import__("xgi")),
    ("toponetx", lambda: __import__("toponetx")),
    ("gudhi", lambda: __import__("gudhi")),
]:
    try:
        _importer()
        TOOL_MANIFEST[_name]["tried"] = True
    except Exception as exc:
        TOOL_MANIFEST[_name]["reason"] = f"not installed: {exc}"

import rustworkx as rx
TOOL_MANIFEST["rustworkx"]["tried"] = True

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def cycle_graph_with_total_angle(total_angle: float):
    graph = rx.PyGraph()
    nodes = [graph.add_node(i) for i in range(4)]
    edge_angle = total_angle / 4.0
    for u, v in [(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3]), (nodes[3], nodes[0])]:
        graph.add_edge(u, v, edge_angle)
    return graph



def wilson_value(graph) -> complex:
    return cmath.exp(1j * sum(graph.edges()))



def run_positive_tests():
    g1 = cycle_graph_with_total_angle(math.pi / 3.0)
    g2 = cycle_graph_with_total_angle(2.0 * math.pi / 3.0)
    basis = rx.cycle_basis(g1)
    w1 = wilson_value(g1)
    w2 = wilson_value(g2)
    results = {
        "single_cycle_detected": {"cycle_basis_size": len(basis), "pass": bool(len(basis) == 1)},
        "distinct_flux_angles_distinguished": {"pass": bool(abs(w1 - w2) > 1e-6)},
    }
    TOOL_MANIFEST["rustworkx"]["used"] = True
    if sp is not None:
        alpha = sp.symbols("alpha", real=True)
        invariant = sp.simplify(sp.exp(sp.I * (alpha + 2 * sp.pi)) - sp.exp(sp.I * alpha)) == 0
        results["sympy_two_pi_gauge_indistinguishable"] = {"pass": bool(invariant)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_two_pi_gauge_indistinguishable"] = {"pass": False, "reason": "sympy unavailable"}
    return results



def run_negative_tests():
    tree = rx.PyGraph()
    nodes = [tree.add_node(i) for i in range(4)]
    for u, v in [(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3])]:
        tree.add_edge(u, v, math.pi / 8.0)
    g1 = cycle_graph_with_total_angle(math.pi / 3.0)
    g2 = cycle_graph_with_total_angle(math.pi / 3.0 + 2.0 * math.pi)
    return {
        "tree_has_no_cycle_witness": {"pass": bool(len(rx.cycle_basis(tree)) == 0)},
        "two_pi_shift_not_distinguished": {"pass": bool(abs(wilson_value(g1) - wilson_value(g2)) < 1e-6)},
    }



def run_boundary_tests():
    zero = cycle_graph_with_total_angle(0.0)
    pi_loop = cycle_graph_with_total_angle(math.pi)
    reverse_pi = cycle_graph_with_total_angle(-math.pi)
    return {
        "zero_flux_identity_loop": {"pass": bool(abs(wilson_value(zero) - 1.0) < 1e-10)},
        "orientation_reversal_conjugates_phase": {"pass": bool(abs(wilson_value(pi_loop) - wilson_value(reverse_pi).conjugate()) < 1e-10)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local U(1) distinguishability via Wilson loop values on one cycle",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "passes_local_rerun": bool(all_pass),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, RESULTS_BASENAME)
    with open(out_path, "w") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{NAME}: {'PASS' if all_pass else 'FAIL'} -> {out_path}")
