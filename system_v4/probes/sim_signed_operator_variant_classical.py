#!/usr/bin/env python3
"""Classical baseline: signed_operator_variant.
Signed variants A_+ = A, A_- = -A. Checks: spectrum negation, eigenvector
preservation, composition A_+ A_- = -A^2, and sign-flip idempotence."""
import json, os, numpy as np
from receipt_boundary import apply_default_receipt_boundary
classification = "classical_baseline"
NAME = "sim_signed_operator_variant_classical"
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "symmetric spectra, eigenspace, and sign-flip checks",
    },
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}
divergence_details = [
    "Classical captures spectrum negation, eigenspace preservation, and sign-flip involution.",
    "Nonclassical signed-operator admissibility under coupling or charge-like constraints is not represented.",
]
divergence_log = (
    "Classical signed-operator variant baseline only; no coupled admissibility, "
    "charge-like constraint, bridge, GStack, axis, QIT, or nonclassical "
    "admission claim."
)

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    for n in (2, 4, 6):
        A = rng.standard_normal((n, n)); H = (A + A.T) / 2
        wp = np.sort(np.linalg.eigvalsh(H)); wm = np.sort(np.linalg.eigvalsh(-H))
        r[f"spectrum_negates_n{n}"] = bool(np.allclose(wp, -wm[::-1], atol=1e-10))
        # same eigenvectors
        _, Vp = np.linalg.eigh(H); _, Vm = np.linalg.eigh(-H)
        # columns may be permuted; check subspace equality via |Vp^T Vm| has near-permutation rows
        overlap = np.abs(Vp.T @ Vm)
        r[f"eigvecs_same_span_n{n}"] = bool(np.allclose(np.sort(overlap.max(axis=1)), np.ones(n), atol=1e-6))
        # composition
        r[f"compose_neg_square_n{n}"] = bool(np.allclose(H @ (-H), -H @ H, atol=1e-12))
        # double flip is identity
        r[f"double_flip_n{n}"] = bool(np.allclose(-(-H), H))
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(1)
    A = rng.standard_normal((3, 3)); H = (A + A.T) / 2
    # sign flip changes spectrum sign (not identical)
    w = np.linalg.eigvalsh(H)
    r["spectrum_not_equal_under_flip"] = bool(not np.allclose(np.sort(w), np.sort(-w), atol=1e-6))
    # signed variant differs from original unless H=0
    r["not_equal_to_self"] = bool(not np.allclose(H, -H))
    return r

def run_boundary_tests():
    r = {}
    # zero operator invariant under sign flip
    Z = np.zeros((3, 3))
    r["zero_invariant"] = bool(np.allclose(Z, -Z))
    # symmetric spectrum case (traceless 2x2)
    H = np.array([[1.0, 0], [0, -1.0]])
    r["symmetric_spectrum_setwise_eq"] = bool(np.allclose(np.sort(np.linalg.eigvalsh(H)), np.sort(np.linalg.eigvalsh(-H))))
    return r

if __name__ == "__main__":
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "divergence_log": divergence_log, "divergence_details": divergence_details}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    results["summary"] = {"all_pass": results["all_pass"]}
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target="Use as bounded classical signed-operator baseline before coupled operator-admissibility packets.",
    )
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w", encoding="utf-8") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
