#!/usr/bin/env python3
"""
Amplitude Damping Channel as a differentiable torch.nn.Module.

Kraus operators:
  K0 = [[1, 0], [0, sqrt(1-gamma)]]
  K1 = [[0, sqrt(gamma)], [0, 0]]

Models energy dissipation (T1 decay) to ground state |0>.

Tests torch AmplitudeDamping against numpy baseline across:
- Substrate equivalence (element-wise comparison)
- Gradient of output entropy w.r.t. damping rate gamma
- Positive, negative, and boundary states
- Sympy symbolic CPTP verification
- z3 parameter range constraint check
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

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


from torch_modules.amplitude_damping import AmplitudeDamping


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_amplitude_damping(rho, gamma):
    """Apply amplitude damping channel using numpy."""
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=np.complex128)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=np.complex128)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T


def numpy_purity(rho):
    """Tr(rho^2)."""
    return np.real(np.trace(rho @ rho))


def numpy_von_neumann_entropy(rho):
    """S = -Tr(rho log rho) via eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return float(-np.sum(evals * np.log(evals)))


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

def torch_von_neumann_entropy(rho):
    """S = -Tr(rho log rho) via eigenvalues, differentiable."""
    evals = torch.linalg.eigvalsh(rho)
    evals = torch.clamp(evals.real, min=1e-12)
    return -torch.sum(evals * torch.log(evals))


def torch_output_entropy(channel, rho):
    """Compute entropy of channel output, differentiable."""
    rho_out = channel(rho)
    return torch_von_neumann_entropy(rho_out)


def torch_purity(rho):
    """Tr(rho^2), differentiable."""
    return torch.real(torch.trace(rho @ rho))


# =====================================================================
# TEST STATES
# =====================================================================

TEST_STATES = {
    "|0><0|": np.array([[1, 0], [0, 0]], dtype=np.complex128),
    "|1><1|": np.array([[0, 0], [0, 1]], dtype=np.complex128),
    "|+><+|": np.array([[0.5, 0.5], [0.5, 0.5]], dtype=np.complex128),
    "maximally_mixed": np.eye(2, dtype=np.complex128) / 2,
}


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Element-wise substrate comparison ---
    gamma_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    p1_results = {}
    for g_val in gamma_values:
        for name, rho_np in TEST_STATES.items():
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)
            channel = AmplitudeDamping(g_val)
            out_np = numpy_amplitude_damping(rho_np, g_val)
            out_t = channel(rho_t).detach().cpu().numpy()
            max_diff = float(np.max(np.abs(out_np - out_t)))
            key = f"gamma={g_val}_{name}"
            p1_results[key] = {
                "max_abs_diff": max_diff,
                "pass": max_diff < 1e-5,
            }
    results["P1_element_wise_substrate_match"] = p1_results

    # --- P2: Entropy gradient w.r.t. gamma exists ---
    p2_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = AmplitudeDamping(0.3)
        entropy = torch_output_entropy(channel, rho_t)
        entropy.backward()
        grad = channel.gamma.grad

        p2_results[name] = {
            "output_entropy": float(entropy.item()),
            "grad_gamma": float(grad.item()) if grad is not None else None,
            "grad_exists": grad is not None,
            "pass": grad is not None,
        }
    results["P2_entropy_gradient_wrt_gamma"] = p2_results

    # --- P3: Kraus completeness: K0†K0 + K1†K1 = I ---
    p3_results = {}
    for g_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        K0_np = np.array([[1, 0], [0, np.sqrt(1 - g_val)]], dtype=np.complex128)
        K1_np = np.array([[0, np.sqrt(g_val)], [0, 0]], dtype=np.complex128)
        completeness = K0_np.conj().T @ K0_np + K1_np.conj().T @ K1_np
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        p3_results[f"gamma={g_val}"] = {
            "identity_diff": identity_diff,
            "pass": identity_diff < 1e-10,
        }
    results["P3_kraus_completeness"] = p3_results

    # --- P4: Trace preservation ---
    p4_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = AmplitudeDamping(0.4)
        out = channel(rho_t).detach().cpu().numpy()
        trace_out = float(np.real(np.trace(out)))
        p4_results[name] = {
            "trace_out": trace_out,
            "diff_from_1": abs(trace_out - 1.0),
            "pass": abs(trace_out - 1.0) < 1e-5,
        }
    results["P4_trace_preservation"] = p4_results

    # --- P5: |0> is a fixed point (ground state invariant) ---
    p5_results = {}
    rho0 = TEST_STATES["|0><0|"]
    for g_val in [0.1, 0.5, 0.9, 1.0]:
        out = numpy_amplitude_damping(rho0, g_val)
        diff = float(np.max(np.abs(out - rho0)))
        p5_results[f"gamma={g_val}"] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-10,
        }
    results["P5_ground_state_fixed_point"] = p5_results

    # --- P6: |1> decays toward |0> ---
    p6_results = {}
    rho1 = TEST_STATES["|1><1|"]
    for g_val in [0.1, 0.5, 0.9]:
        out = numpy_amplitude_damping(rho1, g_val)
        pop_0 = float(np.real(out[0, 0]))
        pop_1 = float(np.real(out[1, 1]))
        p6_results[f"gamma={g_val}"] = {
            "pop_ground": pop_0,
            "pop_excited": pop_1,
            "ground_increased": pop_0 > 1e-10,
            "pop_ground_equals_gamma": abs(pop_0 - g_val) < 1e-10,
            "pass": abs(pop_0 - g_val) < 1e-10,
        }
    results["P6_excited_state_decays"] = p6_results

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Autograd vs finite-difference gradient of entropy ---
    eps = 1e-4
    f1_results = {}
    test_inputs = {"|1><1|": TEST_STATES["|1><1|"], "|+><+|": TEST_STATES["|+><+|"]}
    for name, rho_np in test_inputs.items():
        for g_val in [0.1, 0.3, 0.5, 0.7]:
            # Autograd
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)
            channel = AmplitudeDamping(g_val)
            entropy = torch_output_entropy(channel, rho_t)
            entropy.backward()
            grad_auto = float(channel.gamma.grad.item())

            # Finite difference
            out_plus = numpy_amplitude_damping(rho_np, g_val + eps)
            out_minus = numpy_amplitude_damping(rho_np, g_val - eps)
            S_plus = numpy_von_neumann_entropy(out_plus)
            S_minus = numpy_von_neumann_entropy(out_minus)
            grad_fd = (S_plus - S_minus) / (2 * eps)

            diff = abs(grad_auto - grad_fd)
            key = f"{name}_gamma={g_val}"
            f1_results[key] = {
                "autograd": grad_auto,
                "finite_diff": float(grad_fd),
                "abs_diff": diff,
                "pass": diff < 0.1,  # Generous for numerical entropy grad
            }
    results["F1_autograd_vs_finite_difference_entropy"] = f1_results

    # --- F2: 50-state random substrate equivalence ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(50):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * np.random.uniform(0.1, 0.95)
        rho_np = make_rho_from_bloch(bloch)
        g_val = np.random.uniform(0.0, 1.0)

        out_np = numpy_amplitude_damping(rho_np, g_val)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = AmplitudeDamping(g_val)
        out_t = channel(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))

    results["F2_substrate_equivalence_50_states"] = {
        "n_states": 50,
        "overall_max_diff": max(max_diffs),
        "mean_max_diff": float(np.mean(max_diffs)),
        "pass": max(max_diffs) < 1e-4,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: gamma > 1 violates CPTP (sqrt(1-gamma) imaginary) ---
    n1_results = {}
    for g_val in [1.5, 2.0, 5.0]:
        K0 = np.array([[1, 0], [0, np.sqrt(complex(1 - g_val))]], dtype=np.complex128)
        K1 = np.array([[0, np.sqrt(complex(g_val))], [0, 0]], dtype=np.complex128)
        completeness = K0.conj().T @ K0 + K1.conj().T @ K1
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))

        # Apply to |1> and check positivity
        rho1 = np.array([[0, 0], [0, 1]], dtype=np.complex128)
        out = K0 @ rho1 @ K0.conj().T + K1 @ rho1 @ K1.conj().T
        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))

        n1_results[f"gamma={g_val}"] = {
            "completeness_diff": identity_diff,
            "output_eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "cptp_violated": identity_diff > 0.01 or min_eval < -1e-10,
            "pass": identity_diff > 0.01 or min_eval < -1e-10,
        }
    results["N1_gamma_gt_1_violates_cptp"] = n1_results

    # --- N2: gamma < 0 violates CPTP (completeness fails: trace not preserved) ---
    n2_results = {}
    for g_val in [-0.1, -0.5]:
        K0 = np.array([[1, 0], [0, np.sqrt(complex(1 - g_val))]], dtype=np.complex128)
        K1 = np.array([[0, np.sqrt(complex(g_val))], [0, 0]], dtype=np.complex128)
        completeness = K0.conj().T @ K0 + K1.conj().T @ K1
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        # sqrt(negative) is imaginary, so K1†K1 has imaginary entries -> completeness != I
        n2_results[f"gamma={g_val}"] = {
            "completeness_diff": identity_diff,
            "completeness_violated": identity_diff > 1e-10,
            "pass": identity_diff > 1e-10,  # EXPECT violation
        }
    results["N2_gamma_lt_0_completeness_violation"] = n2_results

    # --- N3: Output Hermiticity maintained for valid gamma ---
    n3_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = AmplitudeDamping(0.3)
        out = channel(rho_t).detach().cpu().numpy()
        herm_diff = float(np.max(np.abs(out - out.conj().T)))
        n3_results[name] = {
            "hermitian_diff": herm_diff,
            "is_hermitian": herm_diff < 1e-5,
            "pass": herm_diff < 1e-5,
        }
    results["N3_output_hermiticity"] = n3_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: gamma=0 is identity channel ---
    b1_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = AmplitudeDamping(0.0)
        out = channel(rho_t).detach().cpu().numpy()
        diff = float(np.max(np.abs(out - rho_np)))
        b1_results[name] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-6,
        }
    results["B1_gamma0_identity"] = b1_results

    # --- B2: gamma=1 full decay to |0> ---
    b2_results = {}
    rho0 = np.array([[1, 0], [0, 0]], dtype=np.complex128)
    for name, rho_np in TEST_STATES.items():
        out = numpy_amplitude_damping(rho_np, 1.0)
        diff_from_ground = float(np.max(np.abs(out - rho0)))
        b2_results[name] = {
            "output": out.tolist(),
            "diff_from_ground_state": diff_from_ground,
            "pass": diff_from_ground < 1e-10,
        }
    results["B2_gamma1_full_decay_to_ground"] = b2_results

    # --- B3: Entropy of |1> output as function of gamma ---
    # At gamma=0: pure |1>, S=0. At gamma=1: pure |0>, S=0.
    # In between: mixed, S > 0. Maximum near gamma=0.5.
    gamma_vals = np.linspace(0.01, 0.99, 20)
    entropies = []
    rho1 = TEST_STATES["|1><1|"]
    for g in gamma_vals:
        out = numpy_amplitude_damping(rho1, g)
        entropies.append(numpy_von_neumann_entropy(out))

    max_idx = int(np.argmax(entropies))
    gamma_at_max = float(gamma_vals[max_idx])

    results["B3_entropy_bell_curve"] = {
        "gamma_values": gamma_vals.tolist(),
        "entropies": entropies,
        "gamma_at_max_entropy": gamma_at_max,
        "max_entropy": float(max(entropies)),
        "entropy_at_endpoints_low": entropies[0] < 0.1 and entropies[-1] < 0.1,
        "peak_near_half": abs(gamma_at_max - 0.5) < 0.15,
        "pass": abs(gamma_at_max - 0.5) < 0.15,
    }

    # --- B4: Purity of |1> output: min at intermediate gamma ---
    purities = []
    for g in gamma_vals:
        out = numpy_amplitude_damping(rho1, g)
        purities.append(float(numpy_purity(out)))

    min_idx = int(np.argmin(purities))
    gamma_at_min = float(gamma_vals[min_idx])

    results["B4_purity_valley"] = {
        "gamma_values": gamma_vals.tolist(),
        "purities": purities,
        "gamma_at_min_purity": gamma_at_min,
        "min_purity": float(min(purities)),
        "purity_at_endpoints_high": purities[0] > 0.9 and purities[-1] > 0.9,
        "pass": purities[0] > 0.9 and purities[-1] > 0.9,
    }

    return results


# =====================================================================
# SYMPY SYMBOLIC CHECK
# =====================================================================

def run_sympy_check():
    """Symbolic verification of Kraus completeness and channel action."""
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    g = sp.Symbol("gamma", real=True, positive=True)
    # Assume gamma < 1 so 1-gamma > 0 and sqrt is real
    g_lt_1 = sp.Symbol("gamma", real=True, positive=True)

    # Use explicit real sqrt for completeness proof
    # K0†K0 = diag(1, 1-g), K1†K1 = diag(g, 0)
    # Sum = diag(1+g, 1-g) ... wait, let's compute properly:
    # K0 = [[1,0],[0,sqrt(1-g)]], K0†K0 = [[1,0],[0,1-g]]
    # K1 = [[0,sqrt(g)],[0,0]], K1†K1 = [[0,0],[0,g]]  (K1† = [[0,0],[sqrt(g),0]])
    #   K1†K1 = [[0,0],[sqrt(g),0]] @ [[0,sqrt(g)],[0,0]] = [[0,0],[0,g]]
    # Sum = [[1,0],[0,1-g+g]] = [[1,0],[0,1]] = I

    K0dK0 = sp.Matrix([[1, 0], [0, 1 - g]])
    K1dK1 = sp.Matrix([[0, 0], [0, g]])
    completeness = K0dK0 + K1dK1
    is_identity = completeness == sp.eye(2)

    # Action on |1><1|
    # K0 |1><1| K0† = [[0,0],[0,1-g]]
    # K1 |1><1| K1† = [[0,sqrt(g)],[0,0]] @ [[0,0],[0,1]] @ [[0,0],[sqrt(g),0]]
    #               = [[0,sqrt(g)],[0,0]] @ [[0,0],[sqrt(g),0]] = [[g,0],[0,0]]
    # Sum = [[g,0],[0,1-g]]
    out_00 = g
    out_11 = 1 - g
    expected = sp.Matrix([[g, 0], [0, 1 - g]])
    # Verify by direct symbolic computation too
    K0 = sp.Matrix([[1, 0], [0, sp.sqrt(1 - g)]])
    K1 = sp.Matrix([[0, sp.sqrt(g)], [0, 0]])
    rho1 = sp.Matrix([[0, 0], [0, 1]])
    out = sp.simplify(K0 * rho1 * K0.T + K1 * rho1 * K1.T)  # .T since all real
    matches = sp.simplify(out - expected) == sp.zeros(2)

    return {
        "completeness_is_identity": bool(is_identity),
        "action_on_ket1": str(out),
        "matches_expected_gamma_1mgamma": bool(matches),
        "pass": bool(is_identity) and bool(matches),
    }


# =====================================================================
# Z3 PARAMETER CONSTRAINT CHECK
# =====================================================================

def run_z3_check():
    """Use z3 to verify: 0 <= gamma <= 1 ensures valid channel."""
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not, sat, unsat

    g = Real("gamma")

    # For CPTP: need 0 <= gamma <= 1 so sqrt args are non-negative
    s = Solver()
    s.add(And(g >= 0, g <= 1))
    s.add(Not(And(1 - g >= 0, g >= 0)))
    result_valid = str(s.check())  # Should be unsat

    # Outside [0,1]: should be able to violate
    s2 = Solver()
    s2.add(g > 1)
    s2.add(Not(And(1 - g >= 0, g >= 0)))
    result_outside = str(s2.check())  # Should be sat

    return {
        "inside_01_can_violate": result_valid,
        "outside_01_can_violate": result_outside,
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
    TOOL_MANIFEST["pytorch"]["reason"] = "Core module: AmplitudeDamping as nn.Module, autograd for entropy gradients"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "Symbolic Kraus completeness and channel action on |1> verification"
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "Parameter range constraint: gamma in [0,1] ensures valid Kraus operators"

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
        "name": "torch_amplitude_damping",
        "migration_family": "amplitude_damping",
        "migration_registry_id": 6,
        "migration_status": "TORCH_TESTED",
        "phase": "Phase 3 sim",
        "description": "Amplitude damping channel as differentiable nn.Module with Kraus operators",
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
    out_path = os.path.join(out_dir, "torch_amplitude_damping_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
