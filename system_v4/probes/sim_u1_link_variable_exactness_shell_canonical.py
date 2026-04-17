#!/usr/bin/env python3
"""
Canonical shell-local U(1) link-variable exactness probe.

QED-style shell-local claim: on one cycle, link variables induced by vertex phases form an
exact assignment with unit Wilson loop, while a non-exact edge phase assignment does not.
"""

import cmath
import json
import math
import os

classification = "canonical"
NAME = "sim_u1_link_variable_exactness_shell_canonical"
RESULTS_BASENAME = f"{NAME}_results.json"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "tensor numerics are not needed for cycle-level exact link variables"},
    "pyg": {"tried": False, "used": False, "reason": "message passing is not needed for one fixed cycle"},
    "z3": {"tried": False, "used": False, "reason": "direct cycle evaluation suffices for exact-vs-non-exact link phases"},
    "cvc5": {"tried": False, "used": False, "reason": "graph cycle evaluation already witnesses shell-local exactness"},
    "sympy": {"tried": False, "used": False, "reason": "sympy symbolically checks telescoping cancellation of exact link phases around a cycle"},
    "clifford": {"tried": False, "used": False, "reason": "geometric algebra is not required for scalar U(1) link variables"},
    "geomstats": {"tried": False, "used": False, "reason": "manifold geodesics are not needed for one-cycle Wilson closure"},
    "e3nn": {"tried": False, "used": False, "reason": "equivariant networks are outside this local gauge-link lane"},
    "rustworkx": {"tried": False, "used": False, "reason": "rustworkx provides the load-bearing single-cycle witness and ordered edge data for the exactness check"},
    "xgi": {"tried": False, "used": False, "reason": "hypergraphs are not needed for one-cycle link variables"},
    "toponetx": {"tried": False, "used": False, "reason": "cell complexes are not needed for the graph-cycle exactness witness"},
    "gudhi": {"tried": False, "used": False, "reason": "persistent homology is not needed for exact link-variable closure"},
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


EDGE_ORDER = [(0, 1), (1, 2), (2, 3), (3, 0)]


def cycle_graph(edge_phases):
    graph = rx.PyGraph()
    nodes = [graph.add_node(i) for i in range(4)]
    for (u, v), phase in zip(EDGE_ORDER, edge_phases):
        graph.add_edge(nodes[u], nodes[v], float(phase))
    return graph


def exact_edge_phases(vertex_phases):
    return [
        vertex_phases[1] - vertex_phases[0],
        vertex_phases[2] - vertex_phases[1],
        vertex_phases[3] - vertex_phases[2],
        vertex_phases[0] - vertex_phases[3],
    ]


def wilson_value(edge_phases):
    return cmath.exp(1j * sum(edge_phases))


def run_positive_tests():
    phases = exact_edge_phases([0.0, 0.4, 1.0, 1.3])
    graph = cycle_graph(phases)
    results = {
        "single_cycle_detected": {"cycle_basis_size": len(rx.cycle_basis(graph)), "pass": bool(len(rx.cycle_basis(graph)) == 1)},
        "exact_link_assignment_has_unit_wilson_loop": {"pass": bool(abs(wilson_value(phases) - 1.0) < 1e-10)},
    }
    TOOL_MANIFEST["rustworkx"]["used"] = True
    if sp is not None:
        a0, a1, a2, a3 = sp.symbols("a0 a1 a2 a3", real=True)
        telescoping = (a1 - a0) + (a2 - a1) + (a3 - a2) + (a0 - a3)
        results["sympy_telescoping_exactness"] = {"pass": bool(sp.simplify(telescoping) == 0)}
        TOOL_MANIFEST["sympy"]["used"] = True
    else:
        results["sympy_telescoping_exactness"] = {"pass": False, "reason": "sympy unavailable"}
    return results


def run_negative_tests():
    exact = exact_edge_phases([0.0, 0.4, 1.0, 1.3])
    non_exact = exact.copy()
    non_exact[2] += math.pi / 5.0

    tree = rx.PyGraph()
    nodes = [tree.add_node(i) for i in range(4)]
    for u, v in [(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3])]:
        tree.add_edge(u, v, 0.0)

    return {
        "non_exact_link_assignment_has_nontrivial_wilson_loop": {"pass": bool(abs(wilson_value(non_exact) - 1.0) > 1e-6)},
        "tree_has_no_cycle_witness": {"pass": bool(len(rx.cycle_basis(tree)) == 0)},
    }


def run_boundary_tests():
    zero = exact_edge_phases([0.0, 0.0, 0.0, 0.0])
    periodic = exact_edge_phases([0.0, 2.0 * math.pi, 2.0 * math.pi, 2.0 * math.pi])
    return {
        "constant_vertex_phase_gives_identity_loop": {"pass": bool(abs(wilson_value(zero) - 1.0) < 1e-10)},
        "two_pi_shifted_vertex_phases_still_exact": {"pass": bool(abs(wilson_value(periodic) - 1.0) < 1e-10)},
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(item.get("pass", False) for group in (positive, negative, boundary) for item in group.values())
    results = {
        "name": NAME,
        "classification": classification,
        "scope_note": "shell-local QED-style exact link variables on one U(1) cycle",
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
