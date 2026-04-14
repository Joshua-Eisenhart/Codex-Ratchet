#!/usr/bin/env python3
"""
sim_e3nn_capability.py -- Tool-capability isolation sim for `e3nn`.

Governing rule (owner+Hermes 2026-04-13):
e3nn is load_bearing for SO(3)-equivariant claims across the geometry stack but
had no bounded capability probe. This is the isolation probe.

Decorative = `import e3nn` with no equivariance check actually run.
Load-bearing = equivariance residual IS the claim.

If e3nn is not importable, probe reports importable=False and all_pass=False
honestly (no fake pass).
"""

classification = "canonical"

import json
import math
import os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "used as e3nn backend (not under test)"},
    "pyg":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "z3":        {"tried": False, "used": False, "reason": "not SMT-relevant"},
    "cvc5":      {"tried": False, "used": False, "reason": "not SMT-relevant"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed"},
    "clifford":  {"tried": False, "used": False, "reason": "separate clifford probe"},
    "geomstats": {"tried": False, "used": False, "reason": "separate probe"},
    "e3nn":      {"tried": False, "used": False, "reason": "under test"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi":       {"tried": False, "used": False, "reason": "not graph-relevant"},
    "toponetx":  {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi":     {"tried": False, "used": False, "reason": "not topology-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None,
    "e3nn": "load_bearing",
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

E3NN_OK = False
E3NN_VERSION = None
TORCH_OK = False
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TORCH_OK = True
except Exception as exc:
    TOOL_MANIFEST["pytorch"]["reason"] = f"not installed: {exc}"

try:
    import e3nn
    from e3nn import o3
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["used"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = "capability under test -- SO(3) equivariance, irrep parsing, CG sanity"
    E3NN_OK = True
    E3NN_VERSION = getattr(e3nn, "__version__", "unknown")
except Exception as exc:
    E3NN_OK = False
    TOOL_MANIFEST["e3nn"]["reason"] = f"not installed: {exc}"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    if not (E3NN_OK and TORCH_OK):
        r["e3nn_available"] = {
            "pass": False,
            "importable": E3NN_OK,
            "torch_available": TORCH_OK,
            "detail": "e3nn or torch missing",
        }
        return r
    r["e3nn_available"] = {"pass": True, "version": E3NN_VERSION}

    torch.manual_seed(0)

    # 1. Irrep parsing: "1x0e + 1x1o" -> dim 1 + 3 = 4.
    irreps_in = o3.Irreps("1x0e + 1x1o")
    irreps_out = o3.Irreps("1x1o")
    r["irrep_parsing"] = {
        "pass": irreps_in.dim == 4 and irreps_out.dim == 3,
        "in_dim": irreps_in.dim,
        "out_dim": irreps_out.dim,
    }

    # 2. Clebsch-Gordan sanity: tensor product 1o x 1o contains 0e + 1e + 2e.
    ls_set = set()
    for mul_ir_1 in o3.Irreps("1x1o"):
        for mul_ir_2 in o3.Irreps("1x1o"):
            ir1 = mul_ir_1.ir
            ir2 = mul_ir_2.ir
            for ir_out in ir1 * ir2:
                ls_set.add((ir_out.l, ir_out.p))
    ls = sorted(ls_set)
    expected = sorted([(0, 1), (1, 1), (2, 1)])  # e parity = +1 since o*o=e
    r["cg_1ox1o_decomp"] = {
        "pass": ls == expected,
        "got": ls,
        "expected": expected,
    }

    # 3. SO(3) equivariance of a small tensor-product layer.
    # Build: TP of irreps_in -> irreps_out, then check f(D(R) x) == D'(R) f(x).
    tp = o3.FullyConnectedTensorProduct(
        irreps_in1="1x1o",
        irreps_in2="1x1o",
        irreps_out="1x1o",
    )
    with torch.no_grad():
        for p in tp.parameters():
            p.copy_(torch.randn_like(p))
    # Random rotation.
    R = o3.rand_matrix()
    D_in = o3.Irreps("1x1o").D_from_matrix(R)
    D_out = o3.Irreps("1x1e").D_from_matrix(R)

    x1 = torch.randn(1, 3)
    x2 = torch.randn(1, 3)
    y = tp(x1, x2)
    y_rot = tp(x1 @ D_in.T, x2 @ D_in.T)
    y_then_rot = y @ D_out.T
    err = float((y_rot - y_then_rot).abs().max())
    r["so3_equivariance"] = {
        "pass": err < 1e-4,
        "max_abs_err": err,
    }

    # 4. D-matrix preserves norm (orthogonality check on irrep rep).
    D_1o = o3.Irreps("1x1o").D_from_matrix(R)
    I_approx = D_1o @ D_1o.T
    err_id = float((I_approx - torch.eye(3)).abs().max())
    r["D_matrix_orthogonal"] = {
        "pass": err_id < 1e-5,
        "max_abs_err": err_id,
    }

    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    if not (E3NN_OK and TORCH_OK):
        r["e3nn_available"] = {"pass": False, "detail": "e3nn or torch missing"}
        return r

    # 1. Malformed irrep string raises.
    raised = False
    err = None
    try:
        _ = o3.Irreps("not_a_real_irrep_string!!")
    except Exception as exc:
        raised = True
        err = type(exc).__name__
    r["bad_irrep_raises"] = {"pass": raised, "error_type": err}

    # 2. Random (non-rotation) matrix breaks equivariance claim.
    torch.manual_seed(1)
    tp = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x1e")
    # Randomize weights away from zero init to make the map non-trivial.
    with torch.no_grad():
        for p in tp.parameters():
            p.copy_(torch.randn_like(p))
    M = torch.randn(3, 3)   # NOT a rotation
    x1 = torch.randn(1, 3)
    x2 = torch.randn(1, 3)
    y = tp(x1, x2)
    y_rot = tp(x1 @ M.T, x2 @ M.T)
    y_then_rot = y @ M.T
    err_val = float((y_rot - y_then_rot).abs().max())
    # Expected to be noticeably NONZERO for generic non-rotation.
    r["non_rotation_breaks_equivariance"] = {
        "pass": err_val > 1e-2,
        "max_abs_err": err_val,
    }

    # 3. Wrong input dimension to TP should raise.
    raised2 = False
    err2 = None
    try:
        tp(torch.randn(1, 5), torch.randn(1, 3))
    except Exception as exc:
        raised2 = True
        err2 = type(exc).__name__
    r["wrong_input_dim_raises"] = {"pass": raised2, "error_type": err2}

    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    if not (E3NN_OK and TORCH_OK):
        r["e3nn_available"] = {"pass": False, "detail": "e3nn or torch missing"}
        return r

    # 1. Identity rotation: equivariance is trivially exact.
    tp = o3.FullyConnectedTensorProduct("1x1o", "1x1o", "1x1e")
    with torch.no_grad():
        for p in tp.parameters():
            p.copy_(torch.randn_like(p))
    R = torch.eye(3)
    D_in = o3.Irreps("1x1o").D_from_matrix(R)
    D_out = o3.Irreps("1x1e").D_from_matrix(R)
    x1 = torch.randn(1, 3)
    x2 = torch.randn(1, 3)
    y = tp(x1, x2)
    y_rot = tp(x1 @ D_in.T, x2 @ D_in.T)
    err = float((y_rot - y @ D_out.T).abs().max())
    r["identity_rotation_exact"] = {"pass": err < 1e-6, "max_abs_err": err}

    # 2. Scalar (0e) irrep is rotation-invariant.
    D_0e = o3.Irreps("1x0e").D_from_matrix(o3.rand_matrix())
    err_scalar = float((D_0e - torch.eye(1)).abs().max())
    r["scalar_irrep_invariant"] = {"pass": err_scalar < 1e-6, "max_abs_err": err_scalar}

    # 3. Composition of rotations: D(R1 R2) = D(R1) D(R2) on 1o irrep.
    R1 = o3.rand_matrix()
    R2 = o3.rand_matrix()
    D_comp = o3.Irreps("1x1o").D_from_matrix(R1 @ R2)
    D_prod = o3.Irreps("1x1o").D_from_matrix(R1) @ o3.Irreps("1x1o").D_from_matrix(R2)
    err_comp = float((D_comp - D_prod).abs().max())
    r["D_homomorphism"] = {"pass": err_comp < 1e-5, "max_abs_err": err_comp}

    return r


# =====================================================================
# MAIN
# =====================================================================

def _all_pass(section):
    return all(bool(v.get("pass", False)) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    summary = {
        "positive_all_pass": _all_pass(pos),
        "negative_all_pass": _all_pass(neg),
        "boundary_all_pass": _all_pass(bnd),
        "importable": E3NN_OK,
    }
    summary["all_pass"] = bool(E3NN_OK and TORCH_OK
                               and summary["positive_all_pass"]
                               and summary["negative_all_pass"]
                               and summary["boundary_all_pass"])

    results = {
        "name": "sim_e3nn_capability",
        "purpose": "Tool-capability isolation probe for e3nn -- SO(3) equivariance, irrep parsing, CG sanity.",
        "e3nn_version": E3NN_VERSION,
        "importable": E3NN_OK,
        "torch_available": TORCH_OK,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "witness_file": "system_v4/probes/sim_e3nn_hopf_spinor_equivariance.py",
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "e3nn_capability_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"summary.all_pass = {summary['all_pass']}")
