#!/usr/bin/env python3
"""sim_gtower_e3nn_so3_equivariance_check -- SO(3) equivariance via e3nn irreps.

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md: SO(3) fence preserves
irrep structure. Load-bearing: e3nn Irreps D-matrix verifies that a
random SO(3) element acts consistently on l=1 vectors (equivariance).
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    from e3nn import o3
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"


def run_positive_tests():
    r = {}
    if not TOOL_MANIFEST["e3nn"]["tried"]:
        return {"skipped": True}
    torch.manual_seed(0)
    irreps = o3.Irreps("1x1o")  # vector irrep
    R = o3.rand_matrix()
    D = irreps.D_from_matrix(R)
    v = torch.tensor([1.0, 0.0, 0.0])
    # equivariance: rotating then mapping == mapping then rotating
    lhs = D @ v
    rhs = R @ v  # l=1 irrep acts as the rotation matrix (with e3nn's basis convention)
    r["l1_equivariant"] = torch.allclose(lhs, rhs, atol=1e-5)
    # Composition: D(R1 R2) = D(R1) D(R2)
    R2 = o3.rand_matrix()
    D2 = irreps.D_from_matrix(R2)
    D12 = irreps.D_from_matrix(R @ R2)
    r["D_homomorphism"] = torch.allclose(D12, D @ D2, atol=1e-5)
    TOOL_MANIFEST["e3nn"]["used"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = "SO(3) irrep D-matrix homomorphism check"
    TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "tensor backend for e3nn"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"
    return r


def run_negative_tests():
    r = {}
    if not TOOL_MANIFEST["e3nn"]["tried"]:
        return {"skipped": True}
    irreps = o3.Irreps("1x1o")
    R = o3.rand_matrix()
    D = irreps.D_from_matrix(R)
    # A random non-SO(3) matrix must not yield an orthogonal D
    bad = torch.eye(3) * 2.0
    # e3nn refuses to build a D-matrix for a non-SO(3) input: that IS the
    # exclusion signal we want (negative test).
    try:
        irreps.D_from_matrix(bad)
        rejected = False
    except (AssertionError, RuntimeError, ValueError):
        rejected = True
    r["non_so3_rejected_by_e3nn"] = rejected
    return r


def run_boundary_tests():
    r = {}
    if not TOOL_MANIFEST["e3nn"]["tried"]:
        return {"skipped": True}
    irreps = o3.Irreps("1x1o")
    I = torch.eye(3)
    D = irreps.D_from_matrix(I)
    r["identity_maps_identity"] = torch.allclose(D, I, atol=1e-6)
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    keys_pos = ["l1_equivariant", "D_homomorphism"]
    keys_neg = ["non_so3_rejected_by_e3nn"]
    keys_bnd = ["identity_maps_identity"]
    all_pass = (all(_t(pos.get(k)) for k in keys_pos)
                and all(_t(neg.get(k)) for k in keys_neg)
                and all(_t(bnd.get(k)) for k in keys_bnd))
    results = {
        "name": "sim_gtower_e3nn_so3_equivariance_check",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: SO(3) fence equivariance via e3nn irreps",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_e3nn_so3_equivariance_check_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
