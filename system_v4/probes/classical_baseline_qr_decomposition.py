#!/usr/bin/env python3
"""classical_baseline_qr_decomposition.py -- non-canon, lane_B-eligible
Generated classical baseline. numpy supportive. pos/neg/boundary all required PASS.
"""
import json, os, numpy as np

from receipt_boundary import apply_default_receipt_boundary

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed for classical baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not a proof sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not a proof sim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra here"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold here"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "numpy sufficient"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
    "numpy": {"tried": True, "used": True, "reason": "supportive classical baseline numeric core for qr_decomposition"},
}
divergence_log = (
    "Classical QR decomposition baseline only; checks finite real-matrix "
    "orthonormal factorization and does not support bridge, QIT, GStack, axis, "
    "or nonclassical claims."
)
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}


def run_positive_tests():
    rng=np.random.default_rng(0); A=rng.standard_normal((6,4))
    Q,R=np.linalg.qr(A)
    return {"Q_orthonormal": bool(np.allclose(Q.T@Q, np.eye(4))),
            "reconstruct": bool(np.allclose(Q@R, A, atol=1e-10))}

def run_negative_tests():
    rng=np.random.default_rng(1); A=rng.standard_normal((4,4))
    Q,R=np.linalg.qr(A)
    return {"R_upper_tri": bool(np.allclose(np.tril(R,-1), 0))}

def run_boundary_tests():
    A=np.array([[3.0]]); Q,R=np.linalg.qr(A)
    return {"one_by_one": bool(abs(R[0,0])==3.0)}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = all(v for v in list(pos.values())+list(neg.values())+list(bnd.values()))
    results = {
        "name": "classical_baseline_qr_decomposition",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(all_pass),
        "lane": "lane_B",
    }
    results = apply_default_receipt_boundary(
        results,
        source_name="classical_baseline_qr_decomposition",
        target=(
            "Use as bounded classical QR baseline evidence before any "
            "operator-subspace, factorization, or spectral tool-lego comparison."
        ),
    )
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "classical_baseline_qr_decomposition_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} qr_decomposition -> {out_path}")
