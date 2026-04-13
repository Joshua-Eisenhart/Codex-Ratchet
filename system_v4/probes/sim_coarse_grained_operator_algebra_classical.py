#!/usr/bin/env python3
"""Classical baseline: coarse_grained_operator_algebra.
Test whether block-averaging / projection preserves algebra structure (commutation, associativity)."""
import json, os, numpy as np
from _classical_baseline_common import TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH
classification = "classical_baseline"

NAME = "coarse_grained_operator_algebra"

def coarse_grain(A, block):
    # block-average n x n matrix into (n/block)x(n/block) via trace over blocks
    n = A.shape[0]; m = n // block
    return A.reshape(m, block, m, block).mean(axis=(1, 3))

def run_positive_tests():
    r = {}
    # Identity coarse-grains to identity
    I = np.eye(8)
    I_cg = coarse_grain(I, 2)
    r["identity_preserved"] = {"err": float(np.max(np.abs(I_cg - np.eye(4) * 0.5))), "pass": np.allclose(I_cg, np.eye(4) * 0.5)}
    # Linearity: CG(A+B) = CG(A)+CG(B)
    rng = np.random.default_rng(0)
    A = rng.standard_normal((8, 8)); B = rng.standard_normal((8, 8))
    r["linearity"] = {"err": float(np.max(np.abs(coarse_grain(A + B, 2) - (coarse_grain(A, 2) + coarse_grain(B, 2))))),
        "pass": np.allclose(coarse_grain(A + B, 2), coarse_grain(A, 2) + coarse_grain(B, 2))}
    # Hermiticity preserved
    H = (A + A.T) / 2
    H_cg = coarse_grain(H, 2)
    r["hermiticity_preserved"] = {"err": float(np.max(np.abs(H_cg - H_cg.T))), "pass": np.allclose(H_cg, H_cg.T)}
    # Trace scaling: CG via mean reduces trace by block
    # For diagonal matrices, mean-based CG with block b: Tr(CG(D)) = Tr(D)/b
    D = np.diag(np.arange(1.0, 9.0))
    D_cg = coarse_grain(D, 2)
    r["trace_scaling_diag"] = {"tr_full": float(np.trace(D)), "tr_cg": float(np.trace(D_cg)),
        "pass": bool(abs(np.trace(D) / 4 - np.trace(D_cg)) < 1e-8)}
    return r

def run_negative_tests():
    r = {}
    # Multiplication is NOT preserved: CG(AB) != CG(A) CG(B) in general
    rng = np.random.default_rng(1)
    A = rng.standard_normal((8, 8)); B = rng.standard_normal((8, 8))
    lhs = coarse_grain(A @ B, 2)
    rhs = coarse_grain(A, 2) @ coarse_grain(B, 2)
    r["multiplication_not_preserved"] = {"diff": float(np.max(np.abs(lhs - rhs))), "pass": float(np.max(np.abs(lhs - rhs))) > 0.1}
    # Commutator NOT preserved in general
    C_full = coarse_grain(A @ B - B @ A, 2)
    C_cg = coarse_grain(A, 2) @ coarse_grain(B, 2) - coarse_grain(B, 2) @ coarse_grain(A, 2)
    r["commutator_not_preserved"] = {"diff": float(np.max(np.abs(C_full - C_cg))), "pass": float(np.max(np.abs(C_full - C_cg))) > 0.1}
    return r

def run_boundary_tests():
    r = {}
    # block = 1: CG is identity
    A = np.arange(9).reshape(3, 3).astype(float)
    r["block_1_identity"] = {"err": float(np.max(np.abs(coarse_grain(A, 1) - A))), "pass": np.allclose(coarse_grain(A, 1), A)}
    # block = n: CG to 1x1 scalar = mean
    A = np.ones((4, 4)) * 7.0
    r["block_n_mean"] = {"val": float(coarse_grain(A, 4)[0, 0]), "pass": abs(coarse_grain(A, 4)[0, 0] - 7.0) < 1e-12}
    return r

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(v.get("pass", False) for v in list(pos.values()) + list(neg.values()) + list(bnd.values()))
    results = {"name": NAME, "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass,
        "note": "classical captures: linear, Hermiticity-preserving block-average coarse-graining. Innately fails (boundary data): multiplicativity and commutator structure are NOT preserved — the 'operator algebra' is genuinely broken by naive classical block-averaging."}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results"); os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_classical_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{NAME} all_pass={all_pass} -> {out_path}")
