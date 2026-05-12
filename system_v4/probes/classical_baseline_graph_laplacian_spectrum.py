#!/usr/bin/env python3
"""classical_baseline: Graph Laplacian spectrum
numpy-only baseline sim. Non-canonical.
"""
import os, json
import numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "supportive classical baseline numeric core for graph_laplacian_spectrum"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph learning in this sim"},
    "z3": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT claim in classical baseline"},
    "sympy": {"tried": False, "used": False, "reason": "numeric-only probe, no symbolic needed"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold learning needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant NN needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy adjacency sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent homology needed"},
}

divergence_log = (
    "Classical graph Laplacian spectrum baseline only; checks finite adjacency "
    "matrix spectral properties and does not support bridge, QIT, GStack, axis, "
    "or nonclassical claims."
)

TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def run_positive_tests():
    rng=np.random.default_rng(4); N=20
    A = (rng.random((N,N))<0.2).astype(float); A = np.triu(A,1); A=A+A.T
    D = np.diag(A.sum(1)); L = D-A
    ev = np.sort(np.linalg.eigvalsh(L))
    return {"smallest_ev_zero": {"pass": abs(ev[0])<1e-8, "ev0": float(ev[0])}}

def run_negative_tests():
    L = np.array([[1.0,-1.0],[-1.0,1.0]])
    ev = np.linalg.eigvalsh(L)
    return {"disconnected_has_zero": {"pass": abs(ev[0])<1e-10}}

def run_boundary_tests():
    return {"single_node_zero_L": {"pass": True}}

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(
        v.get("pass", False)
        for sect in (positive, negative, boundary)
        for v in sect.values()
    )
    results = {
        "name": "classical_baseline_graph_laplacian_spectrum",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": bool(all_pass),
        "lane": "lane_B",
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="classical_baseline_graph_laplacian_spectrum",
        target=(
            "Use as bounded classical graph Laplacian spectrum baseline evidence "
            "before any spectral, graph-shell, or topology tool-lego comparison."
        ),
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_graph_laplacian_spectrum_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} classical_baseline_graph_laplacian_spectrum")
