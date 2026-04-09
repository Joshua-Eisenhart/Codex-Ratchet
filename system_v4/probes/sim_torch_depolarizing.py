#!/usr/bin/env python3
"""
Depolarizing Channel as a differentiable torch.nn.Module.

Applies the depolarizing channel: rho -> (1-p)*rho + p*I/d  (d=2 for qubit)
Kraus operators: K0=sqrt(1-3p/4)*I, K1=sqrt(p/4)*X, K2=sqrt(p/4)*Y, K3=sqrt(p/4)*Z

Tests torch Depolarizing against numpy baseline across:
- Substrate equivalence (element-wise comparison)
- Gradient of output purity w.r.t. depolarizing strength p
- Positive, negative, and boundary states
- Sympy symbolic CPTP verification
- z3 parameter range constraint check
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "supportive",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try importing each tool
try:
    import torch
    import torch.nn as nn
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, And, Not, sat, unsat  # noqa: F401
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"optional import unavailable: {exc}"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


from torch_modules.depolarizing import Depolarizing


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_depolarizing(rho, p):
    """Apply depolarizing channel using numpy."""
    d = rho.shape[0]
    I = np.eye(d, dtype=np.complex128)
    return (1 - p) * rho + p * I / d


def numpy_purity(rho):
    """Tr(rho^2)."""
    return np.real(np.trace(rho @ rho))


def make_rho_from_bloch(bloch):
    """Build 2x2 density matrix from Bloch vector (numpy)."""
    I = np.eye(2, dtype=np.complex128)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return I / 2 + bloch[0] * sx / 2 + bloch[1] * sy / 2 + bloch[2] * sz / 2


# =====================================================================
# TORCH HELPERS
# =====================================================================

def torch_purity(rho):
    """Compute Tr(rho^2), differentiable."""
    return torch.real(torch.trace(rho @ rho))


def torch_output_purity(channel, rho):
    """Compute purity of channel output, differentiable."""
    rho_out = channel(rho)
    return torch_purity(rho_out)


# =====================================================================
# TEST STATES
# =====================================================================

TEST_STATES = {
    "|0><0|": np.array([[1, 0], [0, 0]], dtype=np.complex128),
    "|1><1|": np.array([[0, 0], [0, 1]], dtype=np.complex128),
    "|+><+|": np.array([[0.5, 0.5], [0.5, 0.5]], dtype=np.complex128),
    "|-><-|": np.array([[0.5, -0.5], [-0.5, 0.5]], dtype=np.complex128),
    "maximally_mixed": np.eye(2, dtype=np.complex128) / 2,
}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Element-wise substrate comparison ---
    p_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    p1_results = {}
    for p_val in p_values:
        for name, rho_np in TEST_STATES.items():
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)
            channel = Depolarizing(p_val)

            out_np = numpy_depolarizing(rho_np, p_val)
            out_t = channel(rho_t).detach().cpu().numpy()

            max_diff = float(np.max(np.abs(out_np - out_t)))
            key = f"p={p_val}_{name}"
            p1_results[key] = {
                "max_abs_diff": max_diff,
                "pass": max_diff < 1e-5,
            }
    results["P1_element_wise_substrate_match"] = p1_results

    # --- P2: Purity gradient w.r.t. p ---
    # Depolarizing always REDUCES purity for non-maximally-mixed states, so grad < 0
    # For maximally mixed, output is unchanged, grad = 0
    p2_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(0.3)
        out_purity = torch_output_purity(channel, rho_t)
        out_purity.backward()
        grad = channel.p.grad

        is_maximally_mixed = np.allclose(rho_np, np.eye(2) / 2)

        p2_results[name] = {
            "output_purity": float(out_purity.item()),
            "grad_p": float(grad.item()) if grad is not None else None,
            "grad_exists": grad is not None,
            "is_maximally_mixed": is_maximally_mixed,
            "pass": grad is not None,
        }
    results["P2_purity_gradient_wrt_p"] = p2_results

    # --- P3: Kraus completeness: sum K_i†K_i = I ---
    p3_results = {}
    for p_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        channel = Depolarizing(p_val)
        kraus = channel.kraus_operators()
        completeness = sum(K.conj().T @ K for K in kraus).detach().cpu().numpy()
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        p3_results[f"p={p_val}"] = {
            "identity_diff": identity_diff,
            "pass": identity_diff < 1e-5,
        }
    results["P3_kraus_completeness"] = p3_results

    # --- P4: Trace preservation ---
    p4_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(0.4)
        out = channel(rho_t).detach().cpu().numpy()
        trace_out = float(np.real(np.trace(out)))
        trace_in = float(np.real(np.trace(rho_np)))
        p4_results[name] = {
            "trace_in": trace_in,
            "trace_out": trace_out,
            "diff": abs(trace_out - trace_in),
            "pass": abs(trace_out - trace_in) < 1e-5,
        }
    results["P4_trace_preservation"] = p4_results

    # --- P5: At p=1 output is I/2 regardless of input ---
    p5_results = {}
    I_half = np.eye(2, dtype=np.complex128) / 2
    for name, rho_np in TEST_STATES.items():
        out_np = numpy_depolarizing(rho_np, 1.0)
        diff = float(np.max(np.abs(out_np - I_half)))
        p5_results[name] = {
            "max_diff_from_I_half": diff,
            "pass": diff < 1e-10,
        }
    results["P5_p1_fully_depolarized"] = p5_results

    # --- P6: Maximally mixed state is invariant for all p ---
    p6_results = {}
    rho_mm = TEST_STATES["maximally_mixed"]
    for p_val in [0.0, 0.3, 0.5, 0.7, 1.0]:
        out_np = numpy_depolarizing(rho_mm, p_val)
        diff = float(np.max(np.abs(out_np - rho_mm)))
        p6_results[f"p={p_val}"] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-10,
        }
    results["P6_maximally_mixed_invariant"] = p6_results

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Autograd vs finite-difference gradient of output purity ---
    eps = 1e-4
    f1_results = {}
    test_inputs = {"|+><+|": TEST_STATES["|+><+|"], "|0><0|": TEST_STATES["|0><0|"]}
    for name, rho_np in test_inputs.items():
        for p_val in [0.1, 0.3, 0.5, 0.7]:
            # Autograd
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)
            channel = Depolarizing(p_val)
            purity = torch_output_purity(channel, rho_t)
            purity.backward()
            grad_auto = float(channel.p.grad.item())

            # Finite difference
            purity_plus = numpy_purity(numpy_depolarizing(rho_np, p_val + eps))
            purity_minus = numpy_purity(numpy_depolarizing(rho_np, p_val - eps))
            grad_fd = (purity_plus - purity_minus) / (2 * eps)

            diff = abs(grad_auto - grad_fd)
            key = f"{name}_p={p_val}"
            f1_results[key] = {
                "autograd": grad_auto,
                "finite_diff": float(grad_fd),
                "abs_diff": diff,
                "pass": diff < 1e-2,
            }
    results["F1_autograd_vs_finite_difference"] = f1_results

    # --- F2: 50-state random substrate equivalence ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(50):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * np.random.uniform(0.1, 0.95)
        rho_np = make_rho_from_bloch(bloch)
        p_val = np.random.uniform(0.0, 1.0)

        out_np = numpy_depolarizing(rho_np, p_val)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(p_val)
        out_t = channel(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))

    results["F2_substrate_equivalence_50_states"] = {
        "n_states": 50,
        "overall_max_diff": max(max_diffs),
        "mean_max_diff": float(np.mean(max_diffs)),
        "pass": max(max_diffs) < 1e-5,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: p > 4/3 violates CPTP (K0 has imaginary sqrt since 1-3p/4 < 0) ---
    n1_results = {}
    for p_val in [1.5, 2.0, 4.0]:
        channel = Depolarizing(p_val)
        kraus = channel.kraus_operators()
        completeness = sum(K.conj().T @ K for K in kraus).detach().cpu().numpy()
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        n1_results[f"p={p_val}"] = {
            "identity_diff": identity_diff,
            "cptp_violated": identity_diff > 0.01,
            "pass": identity_diff > 0.01,  # We EXPECT violation
        }
    results["N1_p_gt_4_3_violates_cptp"] = n1_results

    # --- N2: p < 0 violates CPTP ---
    n2_results = {}
    for p_val in [-0.1, -0.5, -1.0]:
        channel = Depolarizing(p_val)
        rho = torch.tensor(TEST_STATES["|+><+|"], dtype=torch.complex64)
        out = channel(rho).detach().cpu().numpy()
        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))
        n2_results[f"p={p_val}"] = {
            "eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "has_negative_eigenvalue": min_eval < -1e-10,
            "pass": min_eval < -1e-10,  # EXPECT negative eigenvalue
        }
    results["N2_p_lt_0_non_positive"] = n2_results

    # --- N3: Hermiticity preserved ---
    n3_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(0.3)
        out = channel(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        n3_results[name] = {
            "hermitian_diff": herm_diff,
            "is_hermitian": herm_diff < 1e-6,
            "pass": herm_diff < 1e-6,
        }
    results["N3_output_hermiticity"] = n3_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: p=0 is identity channel ---
    b1_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(0.0)
        out = channel(rho_t).detach().cpu().numpy()
        diff = float(np.max(np.abs(out - rho_np)))
        b1_results[name] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-6,
        }
    results["B1_p0_identity"] = b1_results

    # --- B2: p=1 maps everything to I/2 ---
    b2_results = {}
    I_half = np.eye(2, dtype=np.complex128) / 2
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = Depolarizing(1.0)
        out = channel(rho_t).detach().cpu().numpy()
        diff = float(np.max(np.abs(out - I_half)))
        b2_results[name] = {
            "max_diff_from_I_half": diff,
            "pass": diff < 1e-6,
        }
    results["B2_p1_fully_depolarized"] = b2_results

    # --- B3: p=0.5 halfway ---
    b3_results = {}
    rho_zero = TEST_STATES["|0><0|"]
    rho_t = torch.tensor(rho_zero, dtype=torch.complex64)
    channel = Depolarizing(0.5)
    out = channel(rho_t).detach().cpu().numpy()
    # Expected: 0.5*|0><0| + 0.5*I/2 = [[0.75, 0], [0, 0.25]]
    expected = 0.5 * rho_zero + 0.5 * np.eye(2, dtype=np.complex128) / 2
    diff = float(np.max(np.abs(out - expected)))
    purity = numpy_purity(out)
    b3_results["zero_state_half_depolarized"] = {
        "max_diff_from_expected": diff,
        "purity": float(purity),
        "pass": diff < 1e-6,
    }
    results["B3_p05_half_depolarizing"] = b3_results

    # --- B4: Purity monotonically decreases with p for pure state ---
    p_vals = np.linspace(0, 1, 20)
    purities = []
    rho_zero = TEST_STATES["|0><0|"]
    for p_val in p_vals:
        out = numpy_depolarizing(rho_zero, p_val)
        purities.append(float(numpy_purity(out)))

    mono_decreasing = all(
        purities[i] >= purities[i + 1] - 1e-10
        for i in range(len(purities) - 1)
    )
    results["B4_purity_monotone_decrease"] = {
        "p_values": p_vals.tolist(),
        "purities": purities,
        "monotone_decreasing": mono_decreasing,
        "pass": mono_decreasing,
    }

    # --- B5: p=4/3 boundary (max CPTP range) ---
    # At p=4/3, K0=sqrt(1-3*(4/3)/4)*I = sqrt(0)*I = 0
    # Channel = (4/3)*I/2 - (1/3)*rho ... this maps everything to I/2 * (4/3) - rho/3
    # Actually: (1-4/3)*rho + (4/3)*I/2 = -rho/3 + 2I/3
    b5_results = {}
    for name, rho_np in TEST_STATES.items():
        out_np = numpy_depolarizing(rho_np, 4.0 / 3.0)
        evals = np.linalg.eigvalsh(out_np)
        min_eval = float(np.min(np.real(evals)))
        b5_results[name] = {
            "eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "is_positive_semidefinite": min_eval >= -1e-10,
            "pass": min_eval >= -1e-10,
        }
    results["B5_p_4_3_boundary"] = b5_results

    return results


# =====================================================================
# SYMPY SYMBOLIC CHECK
# =====================================================================

def run_sympy_check():
    """Symbolic verification of CPTP conditions."""
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    p = sp.Symbol("p", real=True, positive=True)

    I = sp.eye(2)
    X = sp.Matrix([[0, 1], [1, 0]])
    Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    Z = sp.Matrix([[1, 0], [0, -1]])

    # K0†K0 = (1-3p/4)*I, K1†K1 = p/4*X†X = p/4*I, etc.
    # Sum = (1-3p/4 + 3*p/4)*I = I
    sum_K = (1 - 3 * p / 4) * I + (p / 4) * (X.H * X) + (p / 4) * (Y.H * Y) + (p / 4) * (Z.H * Z)
    sum_simplified = sp.simplify(sum_K)
    is_identity = sum_simplified == I

    # Effect on general rho: should be (1-p)*rho + p*I/2
    a, b_r, b_i, d = sp.symbols("a b_r b_i d", real=True)
    b = b_r + sp.I * b_i
    rho = sp.Matrix([[a, b], [sp.conjugate(b), d]])
    out = (1 - p) * rho + p * I / 2
    # Diagonal: (1-p)*a + p/2
    diag_00 = sp.simplify(out[0, 0])
    expected_diag = (1 - p) * a + p / 2
    diag_match = sp.simplify(diag_00 - expected_diag) == 0
    # Off-diagonal: (1-p)*b
    off_diag = sp.simplify(out[0, 1])
    expected_off = (1 - p) * b
    off_diag_match = sp.simplify(off_diag - expected_off) == 0

    return {
        "completeness_is_identity": bool(is_identity),
        "diagonal_decay_formula": str(diag_00),
        "diagonal_matches": bool(diag_match),
        "off_diagonal_decay_formula": str(off_diag),
        "off_diagonal_matches_1_minus_p_times_b": bool(off_diag_match),
        "pass": bool(is_identity),
    }


# =====================================================================
# Z3 PARAMETER CONSTRAINT CHECK
# =====================================================================

def run_z3_check():
    """Use z3 to verify: 0 <= p <= 4/3 ensures valid channel."""
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not, sat, unsat, RealVal

    p = Real("p")

    # For CPTP: need 1-3p/4 >= 0 and p >= 0
    # i.e. p >= 0 and p <= 4/3
    s = Solver()
    s.add(And(p >= 0, p <= RealVal(4) / RealVal(3)))
    s.add(Not(And(1 - 3 * p / 4 >= 0, p >= 0)))
    result_valid = str(s.check())  # Should be unsat

    # Check: can p > 4/3 violate?
    s2 = Solver()
    s2.add(p > RealVal(4) / RealVal(3))
    s2.add(Not(And(1 - 3 * p / 4 >= 0, p >= 0)))
    result_outside = str(s2.check())  # Should be sat

    return {
        "inside_0_4_3_can_violate": result_valid,
        "outside_4_3_can_violate": result_outside,
        "pass": result_valid == "unsat" and result_outside == "sat",
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    falsification = run_falsification_tests()
    sympy_check = run_sympy_check()
    z3_check = run_z3_check()

    # Mark tools as used
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: Depolarizing as nn.Module, autograd for purity gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic CPTP completeness and decay formula verification"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Parameter range constraint: p in [0, 4/3] ensures valid Kraus operators"

    for info in TOOL_MANIFEST.values():
        if info.get("tried") is True and info.get("used") is not True and not info.get("reason"):
            info["reason"] = "Available in environment but not needed for this family proof surface"

    # Count passes
    def count_passes(d):
        passes, total = 0, 0
        if isinstance(d, dict):
            if "pass" in d:
                total += 1
                if d["pass"]:
                    passes += 1
            for v in d.values():
                p, t = count_passes(v)
                passes += p
                total += t
        return passes, total

    all_results = {
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "falsification": falsification,
        "sympy_check": sympy_check,
        "z3_check": z3_check,
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_depolarizing",
        "migration_family": "depolarizing",
        "migration_registry_id": 5,
        "migration_status": "TORCH_TESTED",
        "phase": "Phase 3 sim",
        "description": "Depolarizing channel as differentiable nn.Module with Kraus operators",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "falsification": falsification,
        "sympy_check": sympy_check,
        "z3_check": z3_check,
        "classification": "canonical",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_depolarizing_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
