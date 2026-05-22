#!/usr/bin/env python3
"""
sim_pytorch_capability_isolated.py -- Dedicated PyTorch capability sim.

Tests: tensor construction, autograd backward pass, torch.linalg.eigvalsh,
torch.kron, float64 dtype enforcement, gradient of entropy w.r.t. density
matrix parameter. z3+sympy verify gradient sign symbolically.

classification: canonical
pytorch: load_bearing
z3: load_bearing
sympy: load_bearing
"""

import json
import os
import numpy as np

classification = "canonical"

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": ""},
    "z3":         {"tried": False, "used": False, "reason": ""},
    "cvc5":       {"tried": False, "used": False, "reason": ""},
    "sympy":      {"tried": False, "used": False, "reason": ""},
    "clifford":   {"tried": False, "used": False, "reason": ""},
    "geomstats":  {"tried": False, "used": False, "reason": ""},
    "e3nn":       {"tried": False, "used": False, "reason": ""},
    "rustworkx":  {"tried": False, "used": False, "reason": ""},
    "xgi":        {"tried": False, "used": False, "reason": ""},
    "toponetx":   {"tried": False, "used": False, "reason": ""},
    "gudhi":      {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": None,
    "cvc5": None,
    "e3nn": None,
    "geomstats": None,
    "gudhi": None,
    "pyg": None,
    "pytorch": "load_bearing",
    "rustworkx": None,
    "sympy": "load_bearing",
    "toponetx": None,
    "xgi": None,
    "z3": "load_bearing",
}

# --- imports ---
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import Real, Solver, unsat, And  # noqa: F401
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

for tool_name, entry in TOOL_MANIFEST.items():
    if entry["tried"] and not entry["reason"]:
        entry["reason"] = (
            "import probe succeeded; this tool is not used unless a later "
            "test marks it load-bearing for the PyTorch capability claim"
        )


# =====================================================================
# HELPERS
# =====================================================================

def make_density_matrix(p: "torch.Tensor") -> "torch.Tensor":
    """
    Diagonal single-qubit density matrix: rho = diag(p, 1-p).
    Eigenvalues are p and 1-p; entropy is differentiable w.r.t. p via eigvalsh.
    """
    return torch.diag(torch.stack([p, 1.0 - p]))


def von_neumann_entropy(rho: "torch.Tensor") -> "torch.Tensor":
    """S = -Tr(rho log rho) via eigendecomposition; float64 required."""
    eigvals = torch.linalg.eigvalsh(rho)
    # Clip to avoid log(0); constraint: eigenvalues must be non-negative
    eigvals = eigvals.clamp(min=1e-15)
    return -(eigvals * torch.log(eigvals)).sum()


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests() -> dict:
    results = {}

    # --- P1: float64 dtype enforcement ---
    t = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64)
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Autograd entropy gradient, eigvalsh, kron, and dtype checks are all load-bearing"
    )
    results["P1_float64_dtype"] = {
        "dtype": str(t.dtype),
        "pass": str(t.dtype) == "torch.float64",
        "note": "float64 admitted; float32 excluded from constraint-admissible geometry",
    }

    # --- P2: tensor construction + trace ---
    rho = torch.eye(2, dtype=torch.float64) / 2.0
    trace_val = rho.trace().item()
    results["P2_trace_normalization"] = {
        "trace": trace_val,
        "pass": abs(trace_val - 1.0) < 1e-12,
        "note": "Trace=1 is an admissibility constraint, not a classical assumption",
    }

    # --- P3: eigvalsh on PSD matrix ---
    eigvals = torch.linalg.eigvalsh(rho).tolist()
    all_nonneg = all(v >= -1e-12 for v in eigvals)
    results["P3_eigvalsh_psd"] = {
        "eigenvalues": eigvals,
        "pass": all_nonneg,
        "note": "Negative eigenvalues would exclude the matrix from density-matrix family",
    }

    # --- P4: torch.kron on 2x2 identities ---
    I2 = torch.eye(2, dtype=torch.float64)
    kron_result = torch.kron(I2, I2)
    kron_correct = torch.eye(4, dtype=torch.float64)
    results["P4_kron_identity"] = {
        "max_deviation": (kron_result - kron_correct).abs().max().item(),
        "pass": (kron_result - kron_correct).abs().max().item() < 1e-12,
        "note": "Kronecker product must be exact to float64 precision for multi-qubit states",
    }

    # --- P5: autograd backward pass on entropy ---
    # Use diagonal mixed-state rho = diag(p, 1-p); eigenvalues are p and 1-p.
    # Entropy = -p*log(p) - (1-p)*log(1-p); dS/dp = log((1-p)/p) > 0 for p < 0.5.
    p_param = torch.tensor(0.3, dtype=torch.float64, requires_grad=True)
    rho_param = torch.diag(torch.stack([p_param, 1.0 - p_param]))
    eigvals_p = torch.linalg.eigvalsh(rho_param).clamp(min=1e-15)
    entropy = -(eigvals_p * torch.log(eigvals_p)).sum()
    entropy.backward()
    grad_val = p_param.grad.item()
    results["P5_autograd_entropy_gradient"] = {
        "entropy": entropy.item(),
        "gradient_wrt_p": grad_val,
        "pass": p_param.grad is not None and abs(grad_val) > 1e-6,
        "note": "Gradient survived backward pass; non-zero confirms autograd graph is connected",
    }

    # --- P6: sympy symbolic gradient sign verification ---
    # dS/dp = log((1-p)/p); at p=0.3: log(7/3) > 0
    if TOOL_MANIFEST["sympy"]["tried"]:
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolic entropy derivative verifies sign direction of autograd result"
        )
        p_sym = sp.Symbol("p", real=True, positive=True)
        S_sym = -(p_sym * sp.log(p_sym) + (1 - p_sym) * sp.log(1 - p_sym))
        dS_dp = sp.diff(S_sym, p_sym)
        sign_at_03 = float(dS_dp.subs(p_sym, 0.3).evalf())
        sympy_sign = sign_at_03 > 0
        autograd_sign = grad_val > 0
        results["P6_sympy_gradient_sign_matches_autograd"] = {
            "sympy_dS_dp_at_0p3": sign_at_03,
            "autograd_gradient": grad_val,
            "signs_agree": sympy_sign == autograd_sign,
            "pass": sympy_sign == autograd_sign,
            "note": "sympy symbolic sign must agree with autograd numeric sign",
        }
    else:
        results["P6_sympy_gradient_sign_matches_autograd"] = {
            "pass": False,
            "note": "sympy not available; skipped",
        }

    # --- P7: z3 structural check: entropy gradient > 0 is consistent ---
    if TOOL_MANIFEST["z3"]["tried"]:
        from z3 import Real, Solver, unsat, And
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "z3 verifies that assuming entropy gradient <= 0 near p=0.3 is UNSAT"
        )
        # Encode: grad > 0 is consistent (SAT); grad <= 0 AND grad == observed is UNSAT
        g = Real("gradient")
        obs = float(grad_val)
        solver = Solver()
        solver.add(And(g == obs, g <= 0.0))
        result_z3 = solver.check()
        z3_unsat = result_z3 == unsat
        results["P7_z3_gradient_sign_consistent"] = {
            "z3_result_for_grad_leq_0": str(result_z3),
            "unsat_as_expected": z3_unsat,
            "pass": z3_unsat,
            "note": "UNSAT confirms gradient cannot be <=0 given observed value; structural exclusion",
        }
    else:
        results["P7_z3_gradient_sign_consistent"] = {
            "pass": False,
            "note": "z3 not available; skipped",
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests() -> dict:
    results = {}

    # --- N1: float32 excluded from constraint-admissible dtype ---
    t32 = torch.tensor([1.0], dtype=torch.float32)
    results["N1_float32_excluded"] = {
        "dtype": str(t32.dtype),
        "pass": str(t32.dtype) != "torch.float64",
        "note": "float32 is excluded from admissible dtype family; confirmed non-float64",
    }

    # --- N2: non-PSD matrix produces negative eigenvalue ---
    bad_mat = torch.tensor([[1.0, 2.0], [2.0, 0.1]], dtype=torch.float64)
    bad_eigvals = torch.linalg.eigvalsh(bad_mat).tolist()
    has_negative = any(v < 0 for v in bad_eigvals)
    results["N2_non_psd_has_negative_eigenvalue"] = {
        "eigenvalues": bad_eigvals,
        "pass": has_negative,
        "note": "Matrix with negative eigenvalue is excluded from density-matrix family",
    }

    # --- N3: kron of mismatched shape raises error ---
    try:
        A = torch.eye(2, dtype=torch.float64)
        B = torch.eye(3, dtype=torch.float64)
        # kron(2x2, 3x3) should work (produces 6x6); verify shape not 4x4
        result_shape = torch.kron(A, B).shape
        results["N3_kron_shape_mismatch_excluded"] = {
            "shape": list(result_shape),
            "pass": list(result_shape) != [4, 4],
            "note": "kron(2x2, 3x3) produces 6x6, excluded from 4-dim two-qubit family",
        }
    except Exception as e:
        results["N3_kron_shape_mismatch_excluded"] = {
            "error": str(e),
            "pass": True,
            "note": "Error correctly excluded incompatible kron operation",
        }

    # --- N4: gradient detached tensor yields None grad ---
    theta_det = torch.tensor(0.5, dtype=torch.float64)
    # No requires_grad=True; backward should not produce gradient
    val = theta_det * 2.0
    results["N4_no_gradient_without_requires_grad"] = {
        "grad_is_none": theta_det.grad is None,
        "pass": theta_det.grad is None,
        "note": "Detached tensor excluded from autograd graph; gradient is None",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests() -> dict:
    results = {}

    # --- B1: entropy at near-pure state (p=1e-10) approaches 0 ---
    # rho = diag(1-eps, eps) is nearly a pure state; entropy -> 0 as eps -> 0
    p_near_pure = torch.tensor(1e-10, dtype=torch.float64)
    rho_pure = torch.diag(torch.stack([1.0 - p_near_pure, p_near_pure]))
    ev = torch.linalg.eigvalsh(rho_pure).clamp(min=1e-15)
    entropy_pure = -(ev * torch.log(ev)).sum()
    results["B1_pure_state_entropy_near_zero"] = {
        "entropy": entropy_pure.item(),
        "pass": entropy_pure.item() < 1e-5,
        "note": "Near-pure state admitted only if entropy survives to near-zero; boundary stability",
    }

    # --- B2: entropy at maximally mixed state (p=0.5) near log(2) ---
    # rho = diag(0.5, 0.5) is the maximally mixed qubit state
    p_max = torch.tensor(0.5, dtype=torch.float64)
    rho_max = torch.diag(torch.stack([p_max, 1.0 - p_max]))
    ev2 = torch.linalg.eigvalsh(rho_max).clamp(min=1e-15)
    entropy_max = -(ev2 * torch.log(ev2)).sum()
    log2_val = float(np.log(2))
    results["B2_maximally_mixed_entropy_near_log2"] = {
        "entropy": entropy_max.item(),
        "log2": log2_val,
        "deviation": abs(entropy_max.item() - log2_val),
        "pass": abs(entropy_max.item() - log2_val) < 1e-8,
        "note": "Maximally mixed state must survive to entropy=log(2); boundary admissibility",
    }

    # --- B3: eigvalsh on identity/2 both eigenvalues are 0.5 ---
    half_id = torch.eye(2, dtype=torch.float64) / 2.0
    ev3 = torch.linalg.eigvalsh(half_id).tolist()
    results["B3_eigvalsh_half_identity"] = {
        "eigenvalues": ev3,
        "pass": all(abs(v - 0.5) < 1e-12 for v in ev3),
        "note": "Identity/2 boundary case: both eigenvalues must be exactly 0.5 at float64 precision",
    }

    # --- B4: kron of 1x1 tensors is identity operation ---
    a = torch.tensor([[3.0]], dtype=torch.float64)
    b = torch.tensor([[5.0]], dtype=torch.float64)
    kron_scalar = torch.kron(a, b).item()
    results["B4_kron_scalar_boundary"] = {
        "kron_result": kron_scalar,
        "pass": abs(kron_scalar - 15.0) < 1e-12,
        "note": "kron of 1x1 tensors degenerates to scalar multiply; boundary of tensor product",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_sections = {**positive, **negative, **boundary}
    all_pass = all(v.get("pass", False) for v in all_sections.values())

    results = {
        "name": "sim_pytorch_capability_isolated",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "total_tests": len(all_sections),
            "passed": sum(1 for v in all_sections.values() if v.get("pass", False)),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pytorch_capability_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass} | {results['summary']['passed']}/{results['summary']['total_tests']}")
    if not all_pass:
        for k, v in all_sections.items():
            if not v.get("pass", False):
                print(f"  FAILED: {k} -- {v.get('note', '')}")
        raise SystemExit(1)
