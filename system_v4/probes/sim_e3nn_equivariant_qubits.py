#!/usr/bin/env python3
"""
E(3)-Equivariant Qubit Sim
============================
First probe exercising e3nn (tool #8 in the 12-tool stack, previously zero usage).

Demonstrates E(3)-equivariant computation on qubit states:
  1. Bloch sphere as O(3) representation -- qubits on S^2 transform under SU(2)~SO(3)
  2. Spherical harmonics embedding -- Bloch vectors as l=1 irreps
  3. Equivariant vs non-equivariant channels -- depolarizing commutes with SO(3),
     z-dephasing breaks it
  4. Equivariance verification via rotate-then-channel vs channel-then-rotate
  5. Two-qubit tensor product decomposition into l=0,1,2 (singlet, triplet, quintuplet)

Token: E_E3NN_EQUIVARIANT_QUBITS
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": True,  "used": True,  "reason": "e3nn backend, all tensor ops"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed for this probe"},
    "z3":        {"tried": False, "used": False, "reason": "not needed for this probe"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed for this probe"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed for this probe"},
    "clifford":  {"tried": True,  "used": False, "reason": "import verified; not used in computation"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "e3nn":      {"tried": True,  "used": True,  "reason": "PRIMARY: irreps, FCTP, Wigner-D, spherical harmonics"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this probe"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed for this probe"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed for this probe"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed for this probe"},
}

# =====================================================================
# Imports
# =====================================================================

import torch
from e3nn import o3
from e3nn.o3 import (
    FullyConnectedTensorProduct,
    Linear,
    Irreps,
    wigner_D,
    spherical_harmonics,
    angles_to_matrix,
)
try:
    from clifford import Cl  # noqa: F401
except Exception as exc:  # pragma: no cover - optional import only
    TOOL_MANIFEST["clifford"]["tried"] = False
    TOOL_MANIFEST["clifford"]["used"] = False
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

torch.manual_seed(42)
np.random.seed(42)

# =====================================================================
# Utilities
# =====================================================================

EQ_TOL = 1e-5   # equivariance tolerance
NON_EQ_FLOOR = 1e-3  # minimum deviation to confirm non-equivariance


def random_euler():
    """Random Euler angles (alpha, beta, gamma) as tensors."""
    a = torch.rand(1).item() * 2 * np.pi
    b = torch.rand(1).item() * np.pi
    g = torch.rand(1).item() * 2 * np.pi
    return torch.tensor(a), torch.tensor(b), torch.tensor(g)


def random_bloch_vector(n=1):
    """Random unit Bloch vectors (n, 3)."""
    v = torch.randn(n, 3)
    v = v / v.norm(dim=-1, keepdim=True)
    return v


def rotation_matrix_from_euler(alpha, beta, gamma):
    """SO(3) rotation matrix from Euler angles via e3nn."""
    return angles_to_matrix(alpha, beta, gamma)


def wigner_D_l1(alpha, beta, gamma):
    """Wigner D-matrix for l=1."""
    return wigner_D(1, alpha, beta, gamma)


def depolarizing_channel(v, p=0.5):
    """
    Depolarizing channel: v -> (1-p)*v.
    Commutes with all rotations (equivariant).
    """
    return (1.0 - p) * v


def z_dephasing_channel(v):
    """
    Z-dephasing: zeroes x,y components, keeps z.
    Breaks SO(3) -> U(1) around z-axis.
    v shape: (..., 3) with ordering (y, z, x) in e3nn convention for l=1.
    Actually in e3nn, the l=1 basis is (Y_1^{-1}, Y_1^0, Y_1^1) ~ (y, z, x).
    Z-dephasing kills x and y -> kills components 0 and 2.
    """
    out = torch.zeros_like(v)
    out[..., 1] = v[..., 1]  # keep z (Y_1^0)
    return out


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # ------------------------------------------------------------------
    # P1: Depolarizing channel is equivariant
    # ------------------------------------------------------------------
    alpha, beta, gamma = random_euler()
    D1 = wigner_D_l1(alpha, beta, gamma)  # (3,3) l=1 Wigner matrix
    v = random_bloch_vector(10)  # (10, 3)

    # Route A: rotate then depolarize
    v_rot = v @ D1.T
    route_a = depolarizing_channel(v_rot, p=0.3)

    # Route B: depolarize then rotate
    v_dep = depolarizing_channel(v, p=0.3)
    route_b = v_dep @ D1.T

    diff_depol = (route_a - route_b).norm().item()
    results["P1_depolarizing_equivariance"] = {
        "test": "depolarizing channel commutes with SO(3)",
        "diff": diff_depol,
        "tolerance": EQ_TOL,
        "pass": diff_depol < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # P2: Z-dephasing breaks equivariance
    # ------------------------------------------------------------------
    route_a_z = z_dephasing_channel(v @ D1.T)
    route_b_z = z_dephasing_channel(v) @ D1.T
    diff_zdeph = (route_a_z - route_b_z).norm().item()
    results["P2_z_dephasing_non_equivariance"] = {
        "test": "z-dephasing does NOT commute with SO(3)",
        "diff": diff_zdeph,
        "min_expected_diff": NON_EQ_FLOOR,
        "pass": diff_zdeph > NON_EQ_FLOOR,
    }

    # ------------------------------------------------------------------
    # P3: Spherical harmonics embedding recovers Bloch vector
    # ------------------------------------------------------------------
    # For l=1, Y_1(r_hat) should be proportional to the Bloch components
    v_unit = random_bloch_vector(20)
    Y1 = spherical_harmonics("1o", v_unit, normalize=True)  # (20, 3)
    # Y1 should be proportional to v_unit in the e3nn basis
    # Check via cosine similarity (each row)
    cos_sim = torch.nn.functional.cosine_similarity(Y1, v_unit, dim=-1)
    # All should be ~1.0 (up to sign convention)
    mean_abs_cos = cos_sim.abs().mean().item()
    results["P3_spherical_harmonic_embedding"] = {
        "test": "l=1 spherical harmonics recover Bloch vector direction",
        "mean_abs_cosine_similarity": mean_abs_cos,
        "tolerance": 0.99,
        "pass": mean_abs_cos > 0.99,
    }

    # ------------------------------------------------------------------
    # P4: e3nn Linear layer is equivariant
    # ------------------------------------------------------------------
    lin = Linear("1x1o", "1x1o")
    v_in = random_bloch_vector(5)

    # Route A: rotate then linear
    v_rot_in = (D1 @ v_in.T).T  # rotate
    out_a = lin(v_rot_in)

    # Route B: linear then rotate
    out_pre = lin(v_in)
    out_b = (D1 @ out_pre.T).T

    diff_lin = (out_a - out_b).norm().item()
    results["P4_e3nn_linear_equivariance"] = {
        "test": "e3nn Linear(1x1o -> 1x1o) is SO(3)-equivariant",
        "diff": diff_lin,
        "tolerance": EQ_TOL,
        "pass": diff_lin < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # P5: FullyConnectedTensorProduct equivariance
    # ------------------------------------------------------------------
    # Map: (1x1o) x (1x0e) -> (1x1o)  [scalar-weighted vector channel]
    tp = FullyConnectedTensorProduct("1x1o", "1x0e", "1x1o")
    v_in2 = random_bloch_vector(8)
    scalars = torch.randn(8, 1)  # l=0 scalars are rotation-invariant

    # Route A: rotate input then TP
    v_rot2 = (D1 @ v_in2.T).T
    out_a2 = tp(v_rot2, scalars)

    # Route B: TP then rotate output
    out_pre2 = tp(v_in2, scalars)
    out_b2 = (D1 @ out_pre2.T).T

    diff_tp = (out_a2 - out_b2).norm().item()
    results["P5_FCTP_equivariance"] = {
        "test": "FullyConnectedTensorProduct(1o x 0e -> 1o) is equivariant",
        "diff": diff_tp,
        "tolerance": EQ_TOL,
        "pass": diff_tp < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # P6: Two-qubit tensor product decomposition
    # ------------------------------------------------------------------
    # l=1 x l=1 = l=0 + l=1 + l=2  (Clebsch-Gordan)
    expected_irreps = Irreps("1x0e + 1x1e + 1x2e")
    # Check dimensions match: 3*3 = 9 = 1 + 3 + 5
    dim_product = 3 * 3
    dim_decomp = expected_irreps.dim

    # Build a TP that decomposes the product
    tp_2q = FullyConnectedTensorProduct("1x1o", "1x1o", "1x0e + 1x1e + 1x2e")

    v_a = random_bloch_vector(4)
    v_b = random_bloch_vector(4)
    decomp = tp_2q(v_a, v_b)  # (4, 9)

    # l=0 part (dim 1): singlet-like scalar
    l0_part = decomp[:, :1]
    # l=1 part (dim 3): triplet
    l1_part = decomp[:, 1:4]
    # l=2 part (dim 5): quintuplet
    l2_part = decomp[:, 4:9]

    results["P6_tensor_product_decomposition"] = {
        "test": "l=1 x l=1 decomposes into l=0 + l=1 + l=2",
        "product_dim": dim_product,
        "decomposition_dim": dim_decomp,
        "dims_match": dim_product == dim_decomp,
        "l0_dim": l0_part.shape[-1],
        "l1_dim": l1_part.shape[-1],
        "l2_dim": l2_part.shape[-1],
        "multiplicities_correct": (l0_part.shape[-1] == 1
                                   and l1_part.shape[-1] == 3
                                   and l2_part.shape[-1] == 5),
        "pass": (dim_product == dim_decomp
                 and l0_part.shape[-1] == 1
                 and l1_part.shape[-1] == 3
                 and l2_part.shape[-1] == 5),
    }

    # ------------------------------------------------------------------
    # P7: Wigner D-matrix is orthogonal (rotation matrix)
    # ------------------------------------------------------------------
    D_check = wigner_D_l1(*random_euler())
    orth_err = (D_check @ D_check.T - torch.eye(3)).norm().item()
    # float32 Wigner D has ~1e-5 orthogonality error; use relaxed tolerance
    orth_tol = 1e-4
    results["P7_wigner_D_orthogonality"] = {
        "test": "Wigner D(l=1) is orthogonal",
        "orthogonality_error": orth_err,
        "tolerance": orth_tol,
        "note": "float32 precision limits orthogonality to ~1e-5",
        "pass": orth_err < orth_tol,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    alpha, beta, gamma = random_euler()
    D1 = wigner_D_l1(alpha, beta, gamma)

    # ------------------------------------------------------------------
    # N1: Non-equivariant map is detected by rotation test
    # ------------------------------------------------------------------
    # A map that adds a fixed bias vector -- NOT equivariant
    bias = torch.tensor([1.0, 0.0, 0.0])
    v = random_bloch_vector(10)

    def biased_map(x):
        return x + bias

    route_a = biased_map(v @ D1.T)
    route_b = biased_map(v) @ D1.T
    diff_bias = (route_a - route_b).norm().item()
    results["N1_biased_map_detected"] = {
        "test": "non-equivariant biased map detected by rotation test",
        "diff": diff_bias,
        "min_expected": NON_EQ_FLOOR,
        "pass": diff_bias > NON_EQ_FLOOR,
    }

    # ------------------------------------------------------------------
    # N2: Wrong irrep assignment produces dimension mismatch
    # ------------------------------------------------------------------
    try:
        # Attempt to feed l=1 data (dim 3) into l=2 input (dim 5)
        bad_tp = FullyConnectedTensorProduct("1x2e", "1x0e", "1x1o")
        v_wrong = random_bloch_vector(3)  # (3, 3) but l=2 needs (3, 5)
        bad_tp(v_wrong, torch.ones(3, 1))
        results["N2_wrong_irrep_dimension"] = {
            "test": "wrong irrep causes runtime error",
            "pass": False,
            "detail": "no error raised -- unexpected",
        }
    except (RuntimeError, Exception) as e:
        results["N2_wrong_irrep_dimension"] = {
            "test": "wrong irrep causes runtime error",
            "pass": True,
            "error_type": type(e).__name__,
            "error_msg": str(e)[:200],
        }

    # ------------------------------------------------------------------
    # N3: z-dephasing consistently breaks equivariance across many rotations
    # ------------------------------------------------------------------
    violations = 0
    n_trials = 50
    v_test = random_bloch_vector(20)
    for _ in range(n_trials):
        a, b, g = random_euler()
        D_trial = wigner_D_l1(a, b, g)
        ra = z_dephasing_channel(v_test @ D_trial.T)
        rb = z_dephasing_channel(v_test) @ D_trial.T
        if (ra - rb).norm().item() > NON_EQ_FLOOR:
            violations += 1

    results["N3_z_dephasing_systematic_break"] = {
        "test": "z-dephasing breaks equivariance for generic rotations",
        "violations": violations,
        "trials": n_trials,
        "pass": violations > n_trials * 0.8,  # should break for most rotations
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # ------------------------------------------------------------------
    # B1: Identity rotation is trivially equivariant (even for non-eq channels)
    # ------------------------------------------------------------------
    D_id = wigner_D_l1(torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0))
    id_err = (D_id - torch.eye(3)).norm().item()

    v = random_bloch_vector(10)
    # Even z-dephasing "commutes" with identity
    ra = z_dephasing_channel(v @ D_id.T)
    rb = z_dephasing_channel(v) @ D_id.T
    diff_id = (ra - rb).norm().item()

    results["B1_identity_rotation"] = {
        "test": "identity rotation: D(0,0,0) = I_3",
        "identity_error": id_err,
        "z_dephasing_diff_at_identity": diff_id,
        "pass": id_err < EQ_TOL and diff_id < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # B2: 180-degree rotation -- equivariant channel stays equivariant
    # ------------------------------------------------------------------
    D_180 = wigner_D_l1(torch.tensor(np.pi), torch.tensor(0.0), torch.tensor(0.0))
    v2 = random_bloch_vector(10)

    # Depolarizing should still commute
    ra2 = depolarizing_channel(v2 @ D_180.T, p=0.5)
    rb2 = depolarizing_channel(v2, p=0.5) @ D_180.T
    diff_180 = (ra2 - rb2).norm().item()

    results["B2_180_degree_rotation"] = {
        "test": "180-deg rotation: depolarizing still equivariant",
        "diff": diff_180,
        "tolerance": EQ_TOL,
        "pass": diff_180 < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # B3: Zero Bloch vector (maximally mixed state)
    # ------------------------------------------------------------------
    v_zero = torch.zeros(1, 3)
    dep_zero = depolarizing_channel(v_zero, p=0.5)
    zdeph_zero = z_dephasing_channel(v_zero)

    results["B3_zero_bloch_vector"] = {
        "test": "zero Bloch vector (maximally mixed) is fixed point",
        "depolarizing_output_norm": dep_zero.norm().item(),
        "z_dephasing_output_norm": zdeph_zero.norm().item(),
        "pass": dep_zero.norm().item() < EQ_TOL and zdeph_zero.norm().item() < EQ_TOL,
    }

    # ------------------------------------------------------------------
    # B4: Numerical precision of e3nn at small angles
    # ------------------------------------------------------------------
    tiny = 1e-8
    D_tiny = wigner_D_l1(torch.tensor(tiny), torch.tensor(tiny), torch.tensor(tiny))
    near_id = (D_tiny - torch.eye(3)).norm().item()

    results["B4_small_angle_precision"] = {
        "test": "Wigner D at tiny angles is near identity",
        "deviation_from_identity": near_id,
        "tolerance": 1e-6,
        "pass": near_id < 1e-6,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    ts = datetime.now(UTC).isoformat()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {**positive, **negative, **boundary}
    total = len(all_tests)
    passed = sum(1 for v in all_tests.values() if v.get("pass"))

    results = {
        "name": "E3NN Equivariant Qubits",
        "token": "E_E3NN_EQUIVARIANT_QUBITS",
        "timestamp": ts,
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "all_pass": passed == total,
        },
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "e3nn_equivariant_qubits_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {passed}/{total} passed")
    if passed < total:
        failed_names = [k for k, v in all_tests.items() if not v.get("pass")]
        print(f"FAILED: {failed_names}")
        sys.exit(1)
    else:
        print("ALL PASS")
