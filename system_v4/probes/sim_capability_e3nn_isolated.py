#!/usr/bin/env python3
"""
sim_capability_e3nn_isolated.py -- Isolated tool-capability probe for e3nn.

Classical_baseline capability probe: demonstrates e3nn equivariant neural network
library: irreducible representations, spherical harmonics, tensor products of
irreps, Wigner D matrices, and SO(3) equivariance verification. Honest CAN/CANNOT
summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates e3nn equivariant neural network capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": True,  "used": True,  "reason": "required: e3nn is built on PyTorch; all tensor operations and autograd run through torch; e3nn cannot function without it."},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": True,  "used": True,  "reason": "load-bearing: e3nn irreps, spherical harmonics, and Wigner D matrices are the sole subject of this capability probe."},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "supportive", "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": "load_bearing",
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

E3NN_OK = False
TORCH_OK = False
try:
    import torch
    TORCH_OK = True
    import e3nn
    from e3nn import o3
    E3NN_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not E3NN_OK:
        r["e3nn_available"] = {"pass": False, "detail": "e3nn not importable"}
        return r

    import torch
    from e3nn import o3

    r["e3nn_available"] = {"pass": True, "version": e3nn.__version__}

    # --- Test 1: Irreps construction ---
    irreps = o3.Irreps("1x0e + 1x1o")  # scalar + vector
    r["irreps_construction"] = {
        "pass": len(irreps) == 2,
        "dim": irreps.dim,
        "detail": f"1x0e + 1x1o: dim={irreps.dim} (expected 4: 1 scalar + 3 vector)",
    }
    r["irreps_construction"]["pass"] = irreps.dim == 4

    # --- Test 2: spherical harmonics ---
    pos = torch.tensor([[0.0, 0.0, 1.0]])  # unit z vector
    sh = o3.spherical_harmonics([0, 1], pos, normalize=True)
    r["spherical_harmonics_shape"] = {
        "pass": sh.shape == (1, 4),  # l=0: 1, l=1: 3 => total 4
        "shape": list(sh.shape),
        "detail": "Y_l^m for l=0,1 on 1 point: shape (1, 4)",
    }

    # --- Test 3: Wigner D matrix is unitary ---
    angles = torch.tensor([0.1, 0.2, 0.3])  # alpha, beta, gamma ZYZ Euler
    D = o3.wigner_D(1, angles[0], angles[1], angles[2])
    # D * D^dagger should be identity (unitary)
    Ddagger = D.conj().T
    product = torch.mm(D, Ddagger)
    identity = torch.eye(3, dtype=product.dtype)
    is_unitary = torch.allclose(product, identity, atol=1e-6)
    r["wigner_D_unitary"] = {
        "pass": bool(is_unitary),
        "max_off_diag": float(torch.abs(product - identity).max()),
        "detail": "Wigner D(l=1) matrix must be unitary",
    }

    # --- Test 4: SO(3) equivariance of spherical harmonics ---
    # Y_l(R*x) = D_l(R) * Y_l(x)
    # Use a specific rotation
    from e3nn.o3 import rand_matrix
    torch.manual_seed(42)
    R = rand_matrix()  # random SO(3) matrix
    x = torch.tensor([[1.0, 0.0, 0.0]])  # unit x vector
    Rx = x @ R.T

    y_x = o3.spherical_harmonics([1], x, normalize=True)      # Y_1(x)
    y_Rx = o3.spherical_harmonics([1], Rx, normalize=True)    # Y_1(R*x)

    # D_1(R) * Y_1(x)
    alpha, beta, gamma = o3.matrix_to_angles(R)
    D1 = o3.wigner_D(1, alpha, beta, gamma)
    Dy_x = (D1 @ y_x.T).T  # D_1 * Y_1(x)

    equivariant = torch.allclose(y_Rx, Dy_x, atol=1e-5)
    r["spherical_harmonics_equivariance"] = {
        "pass": bool(equivariant),
        "max_diff": float(torch.abs(y_Rx - Dy_x).max()),
        "detail": "Y_1(R*x) = D_1(R) * Y_1(x): spherical harmonics are equivariant",
    }

    # --- Test 5: tensor product of irreps ---
    # Parity rule: p_out = p_in1 * p_in2 = (-1)*(-1) = +1 (even)
    # 1o x 1o -> 0e + 1e + 2e (all even parity from two odd irreps)
    tp = o3.TensorProduct(
        "1x1o", "1x1o", "1x0e + 1x1e + 1x2e",
        instructions=[(0, 0, 0, "uuu", True), (0, 0, 1, "uuu", True), (0, 0, 2, "uuu", True)],
    )
    v1 = torch.randn(3)
    v2 = torch.randn(3)
    out = tp(v1, v2)
    r["tensor_product"] = {
        "pass": out.shape[0] == 9,  # 1+3+5 = 9
        "output_dim": int(out.shape[0]),
        "detail": "1o x 1o -> 0e + 1e + 2e (parity: odd*odd=even): output dim = 1+3+5 = 9",
    }

    return r


def run_negative_tests():
    r = {}
    if not E3NN_OK:
        r["e3nn_unavailable"] = {"pass": True, "detail": "skip: e3nn not installed"}
        return r

    import torch
    from e3nn import o3

    # --- Neg 1: Wigner D is NOT identity for non-zero rotation ---
    angles = torch.tensor([0.5, 0.5, 0.5])
    D = o3.wigner_D(1, angles[0], angles[1], angles[2])
    identity = torch.eye(3, dtype=D.dtype)
    is_identity = torch.allclose(D, identity, atol=1e-4)
    r["wigner_D_not_identity_for_nonzero_rotation"] = {
        "pass": not is_identity,
        "detail": "D(l=1) for non-zero rotation must not equal identity",
    }

    # --- Neg 2: scalar irrep (l=0) is rotation-invariant ---
    from e3nn.o3 import rand_matrix
    torch.manual_seed(7)
    R = rand_matrix()
    x = torch.tensor([[0.0, 1.0, 0.0]])
    Rx = x @ R.T
    y0_x = o3.spherical_harmonics([0], x, normalize=True)
    y0_Rx = o3.spherical_harmonics([0], Rx, normalize=True)
    invariant = torch.allclose(y0_x, y0_Rx, atol=1e-6)
    r["scalar_irrep_is_invariant"] = {
        "pass": bool(invariant),
        "detail": "Y_0 (scalar) is rotation-invariant: Y_0(R*x) = Y_0(x)",
    }

    return r


def run_boundary_tests():
    r = {}
    if not E3NN_OK:
        r["e3nn_unavailable"] = {"pass": True, "detail": "skip: e3nn not installed"}
        return r

    import torch
    from e3nn import o3

    # --- Boundary 1: identity rotation Wigner D is identity ---
    D = o3.wigner_D(1, torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0))
    identity = torch.eye(3, dtype=D.dtype)
    r["identity_rotation_D"] = {
        "pass": bool(torch.allclose(D, identity, atol=1e-6)),
        "max_diff": float(torch.abs(D - identity).max()),
        "detail": "D(l=1, 0,0,0) = I_3 (zero rotation is identity)",
    }

    # --- Boundary 2: l=0 irreps dim is 1 ---
    irreps0 = o3.Irreps("1x0e")
    r["scalar_irreps_dim1"] = {
        "pass": irreps0.dim == 1,
        "dim": irreps0.dim,
        "detail": "1x0e has dimension 1",
    }

    # --- Boundary 3: l=2 Wigner D is 5x5 unitary ---
    D2 = o3.wigner_D(2, torch.tensor(0.3), torch.tensor(0.4), torch.tensor(0.5))
    Dd2 = D2.conj().T
    prod2 = torch.mm(D2, Dd2)
    r["l2_wigner_D_unitary"] = {
        "pass": bool(torch.allclose(prod2, torch.eye(5, dtype=prod2.dtype), atol=1e-5)),
        "shape": list(D2.shape),
        "detail": "D(l=2) is 5×5 unitary",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_e3nn_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "compute spherical harmonics Y_l^m and verify SO(3) equivariance",
                "construct Wigner D matrices and verify unitarity",
                "build equivariant tensor products of irreducible representations",
                "represent SO(3)/O(3) symmetry in neural network layers",
                "compute Clebsch-Gordan coefficients via tensor product instructions",
                "validate Y_l(R*x) = D_l(R)*Y_l(x) equivariance identity",
            ],
            "CANNOT": [
                "work without PyTorch (e3nn is a pure torch library)",
                "handle arbitrary Lie group symmetries beyond O(3)/SO(3)",
                "replace symbolic geometry tools (use clifford/geomstats for that)",
                "provide SMT proof of equivariance (use z3 for logical proof)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_e3nn_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
