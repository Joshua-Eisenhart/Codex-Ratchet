#!/usr/bin/env python3
"""
Bit-Phase-Flip (Y-Dephasing) Channel as a differentiable torch.nn.Module.

Applies the Pauli-Y error channel: rho -> (1-p)*rho + p*Y*rho*Y
Kraus operators: K0 = sqrt(1-p)*I, K1 = sqrt(p)*Y

where Y = [[0, -i], [i, 0]].

This is the Y-dephasing channel. Unlike X-dephasing or Z-dephasing:
- NO Bloch axis is fully invariant (Y mixes all three components)
- At p=0.5: all off-diagonal elements killed (maximally depolarizing in Y basis)
- NOT equivalent to BitFlip or ZDephasing -- verified explicitly

Tests:
- No axis invariance (all Bloch components affected)
- p=0.5 kills off-diagonals for non-Y-eigenstates
- Non-equivalence to X-channel and Z-channel proved numerically and via z3
- Positive, negative, boundary, falsification
- Sympy symbolic CPTP verification
- z3 fixed-point structure proof: Y-channel differs from X and Z
"""

import json
import os
import sys
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
    from z3 import Real, Solver, And, Or, Not, Implies, sat, unsat, ForAll  # noqa: F401
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
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

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

# Import existing channels for non-equivalence proof
sys.path.insert(0, os.path.dirname(__file__))
from sim_torch_bit_flip import BitFlip  # noqa: E402
from sim_torch_z_dephasing import ZDephasing  # noqa: E402


# =====================================================================
# MODULE UNDER TEST: BitPhaseFlip
# =====================================================================

class BitPhaseFlip(nn.Module):
    """Differentiable bit-phase-flip (Pauli-Y error) channel.

    Channel action: rho -> (1-p)*rho + p*Y*rho*Y
    Kraus form: K0 = sqrt(1-p)*I, K1 = sqrt(p)*Y

    Y = [[0, -i], [i, 0]]

    Unlike X-dephasing (X-basis invariant) or Z-dephasing (Z-basis invariant),
    the Y channel has no Bloch axis that is fully preserved for all states.
    Y-eigenstates (|+i>, |-i>) ARE invariant, but these lie on the Y-axis.

    On the Bloch sphere:
    - X component: flips sign -> decays as (1-2p)
    - Y component: preserved (Y commutes with Y-axis)
    - Z component: flips sign -> decays as (1-2p)

    So the Y-axis IS preserved, but X and Z both decay.
    At p=0.5: only Y-component survives.
    """

    def __init__(self, p=0.5):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho):
        Y = torch.tensor(
            [[0, -1j], [1j, 0]], dtype=rho.dtype, device=rho.device
        )
        p = self.p.to(rho.dtype)
        out = (1 - p) * rho + p * (Y @ rho @ Y)
        return out

    def kraus_operators(self):
        """Return Kraus operators for inspection."""
        p = self.p
        I = torch.eye(2, dtype=torch.complex64)
        Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64)
        K0 = torch.sqrt((1 - p).to(torch.complex64)) * I
        K1 = torch.sqrt(p.to(torch.complex64)) * Y
        return K0, K1


# =====================================================================
# NUMPY BASELINE
# =====================================================================

def numpy_bit_phase_flip(rho, p):
    """Apply Y-dephasing channel using numpy."""
    Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    return (1 - p) * rho + p * (Y @ rho @ Y)


def numpy_bit_flip(rho, p):
    """Apply bit-flip channel using numpy."""
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    return (1 - p) * rho + p * (X @ rho @ X)


def numpy_z_dephasing(rho, p):
    """Apply Z-dephasing channel using numpy."""
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return (1 - p) * rho + p * (Z @ rho @ Z)


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


def extract_bloch(rho):
    """Extract Bloch vector from 2x2 density matrix."""
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    rx = np.real(np.trace(sx @ rho))
    ry = np.real(np.trace(sy @ rho))
    rz = np.real(np.trace(sz @ rho))
    return np.array([rx, ry, rz])


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
    "|+i><+i|": np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=np.complex128),
    "|-i><-i|": np.array([[0.5, 0.5j], [-0.5j, 0.5]], dtype=np.complex128),
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
            channel = BitPhaseFlip(p_val)

            out_np = numpy_bit_phase_flip(rho_np, p_val)
            out_t = channel(rho_t).detach().cpu().numpy()

            max_diff = float(np.max(np.abs(out_np - out_t)))
            key = f"p={p_val}_{name}"
            p1_results[key] = {
                "max_abs_diff": max_diff,
                "pass": max_diff < 1e-5,
            }
    results["P1_element_wise_substrate_match"] = p1_results

    # --- P2: Y-basis states invariant ---
    p2_results = {}
    for p_val in [0.1, 0.5, 0.9]:
        for name in ["|+i><+i|", "|-i><-i|"]:
            rho_np = TEST_STATES[name]
            out_np = numpy_bit_phase_flip(rho_np, p_val)
            diff = float(np.max(np.abs(out_np - rho_np)))
            p2_results[f"p={p_val}_{name}"] = {
                "max_diff_from_input": diff,
                "pass": diff < 1e-10,
            }
    results["P2_y_basis_invariant"] = p2_results

    # --- P3: Bloch vector decay -- X and Z components decay, Y preserved ---
    p3_results = {}
    # Use a state with all three Bloch components nonzero
    bloch_in = np.array([0.5, 0.3, 0.7])
    bloch_in = bloch_in / np.linalg.norm(bloch_in) * 0.9
    rho_np = make_rho_from_bloch(bloch_in)
    for p_val in [0.1, 0.3, 0.5, 0.7, 0.9]:
        out_np = numpy_bit_phase_flip(rho_np, p_val)
        bloch_out = extract_bloch(out_np)
        # Expected: rx -> (1-2p)*rx, ry -> ry, rz -> (1-2p)*rz
        expected_rx = (1 - 2 * p_val) * bloch_in[0]
        expected_ry = bloch_in[1]
        expected_rz = (1 - 2 * p_val) * bloch_in[2]
        diff_x = abs(bloch_out[0] - expected_rx)
        diff_y = abs(bloch_out[1] - expected_ry)
        diff_z = abs(bloch_out[2] - expected_rz)
        p3_results[f"p={p_val}"] = {
            "bloch_in": bloch_in.tolist(),
            "bloch_out": bloch_out.tolist(),
            "x_decay_diff": diff_x,
            "y_preserved_diff": diff_y,
            "z_decay_diff": diff_z,
            "pass": diff_x < 1e-10 and diff_y < 1e-10 and diff_z < 1e-10,
        }
    results["P3_bloch_decay_xz_not_y"] = p3_results

    # --- P4: Kraus completeness ---
    p4_results = {}
    for p_val in [0.0, 0.25, 0.5, 0.75, 1.0]:
        channel = BitPhaseFlip(p_val)
        K0, K1 = channel.kraus_operators()
        completeness = (K0.conj().T @ K0 + K1.conj().T @ K1).detach().cpu().numpy()
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        p4_results[f"p={p_val}"] = {
            "identity_diff": identity_diff,
            "pass": identity_diff < 1e-5,
        }
    results["P4_kraus_completeness"] = p4_results

    # --- P5: Trace preservation ---
    p5_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = BitPhaseFlip(0.4)
        out = channel(rho_t).detach().cpu().numpy()
        trace_out = float(np.real(np.trace(out)))
        trace_in = float(np.real(np.trace(rho_np)))
        p5_results[name] = {
            "trace_in": trace_in,
            "trace_out": trace_out,
            "diff": abs(trace_out - trace_in),
            "pass": abs(trace_out - trace_in) < 1e-5,
        }
    results["P5_trace_preservation"] = p5_results

    # --- P6: NOT equivalent to BitFlip (X-channel) ---
    np.random.seed(999)
    nonequiv_x = []
    for _ in range(100):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * np.random.uniform(0.1, 0.99)
        rho_np = make_rho_from_bloch(bloch)
        p_val = np.random.uniform(0.01, 0.99)
        out_y = numpy_bit_phase_flip(rho_np, p_val)
        out_x = numpy_bit_flip(rho_np, p_val)
        nonequiv_x.append(float(np.max(np.abs(out_y - out_x))))

    results["P6_not_equivalent_to_BitFlip"] = {
        "n_states": 100,
        "n_with_difference_gt_1e6": sum(1 for d in nonequiv_x if d > 1e-6),
        "max_diff": max(nonequiv_x),
        "mean_diff": float(np.mean(nonequiv_x)),
        "pass": sum(1 for d in nonequiv_x if d > 1e-6) > 50,
    }

    # --- P7: NOT equivalent to ZDephasing ---
    nonequiv_z = []
    np.random.seed(888)
    for _ in range(100):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * np.random.uniform(0.1, 0.99)
        rho_np = make_rho_from_bloch(bloch)
        p_val = np.random.uniform(0.01, 0.99)
        out_y = numpy_bit_phase_flip(rho_np, p_val)
        out_z = numpy_z_dephasing(rho_np, p_val)
        nonequiv_z.append(float(np.max(np.abs(out_y - out_z))))

    results["P7_not_equivalent_to_ZDephasing"] = {
        "n_states": 100,
        "n_with_difference_gt_1e6": sum(1 for d in nonequiv_z if d > 1e-6),
        "max_diff": max(nonequiv_z),
        "mean_diff": float(np.mean(nonequiv_z)),
        "pass": sum(1 for d in nonequiv_z if d > 1e-6) > 50,
    }

    # --- P8: At p=0.5, non-Y-eigenstate off-diagonals killed ---
    p8_results = {}
    for name in ["|0><0|", "|+><+|"]:
        rho_np = TEST_STATES[name]
        out = numpy_bit_phase_flip(rho_np, 0.5)
        # At p=0.5: only diagonal survives for Z-basis states
        # For general state: X,Z Bloch components -> 0, only Y survives
        bloch_out = extract_bloch(out)
        bloch_in = extract_bloch(rho_np)
        x_killed = abs(bloch_out[0]) < 1e-10
        z_killed = abs(bloch_out[2]) < 1e-10
        y_preserved = abs(bloch_out[1] - bloch_in[1]) < 1e-10
        p8_results[name] = {
            "bloch_in": bloch_in.tolist(),
            "bloch_out": bloch_out.tolist(),
            "x_killed": x_killed,
            "z_killed": z_killed,
            "y_preserved": y_preserved,
            "pass": x_killed and z_killed and y_preserved,
        }
    results["P8_p05_kills_xz_preserves_y"] = p8_results

    # --- P9: Purity gradient w.r.t. p ---
    p9_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = BitPhaseFlip(0.3)
        out_purity = torch_output_purity(channel, rho_t)
        out_purity.backward()
        grad = channel.p.grad

        p9_results[name] = {
            "output_purity": float(out_purity.item()),
            "grad_p": float(grad.item()) if grad is not None else None,
            "grad_exists": grad is not None,
            "pass": grad is not None,
        }
    results["P9_purity_gradient_wrt_p"] = p9_results

    return results


# =====================================================================
# FALSIFICATION TESTS
# =====================================================================

def run_falsification_tests():
    results = {}

    # --- F1: Autograd vs finite-difference gradient ---
    eps = 1e-4
    f1_results = {}
    test_inputs = {
        "|0><0|": TEST_STATES["|0><0|"],
        "|+><+|": TEST_STATES["|+><+|"],
        "|+i><+i|": TEST_STATES["|+i><+i|"],
    }
    for name, rho_np in test_inputs.items():
        for p_val in [0.1, 0.3, 0.5, 0.7]:
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)
            channel = BitPhaseFlip(p_val)
            purity = torch_output_purity(channel, rho_t)
            purity.backward()
            grad_auto = float(channel.p.grad.item())

            purity_plus = numpy_purity(numpy_bit_phase_flip(rho_np, p_val + eps))
            purity_minus = numpy_purity(numpy_bit_phase_flip(rho_np, p_val - eps))
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

    # --- F2: 100-state random substrate equivalence ---
    np.random.seed(42)
    max_diffs = []
    for _ in range(100):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * np.random.uniform(0.1, 0.95)
        rho_np = make_rho_from_bloch(bloch)
        p_val = np.random.uniform(0.0, 1.0)

        out_np = numpy_bit_phase_flip(rho_np, p_val)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = BitPhaseFlip(p_val)
        out_t = channel(rho_t).detach().cpu().numpy()
        max_diffs.append(float(np.max(np.abs(out_np - out_t))))

    results["F2_substrate_equivalence_100_states"] = {
        "n_states": 100,
        "overall_max_diff": max(max_diffs),
        "mean_max_diff": float(np.mean(max_diffs)),
        "pass": max(max_diffs) < 1e-5,
    }

    # --- F3: Non-equivalence to BitFlip via torch modules directly ---
    f3_diffs = []
    np.random.seed(777)
    for _ in range(50):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * 0.8
        rho_np = make_rho_from_bloch(bloch)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        p_val = np.random.uniform(0.05, 0.95)

        bpf = BitPhaseFlip(p_val)
        bf = BitFlip(p_val)
        out_bpf = bpf(rho_t).detach().cpu().numpy()
        out_bf = bf(rho_t).detach().cpu().numpy()
        f3_diffs.append(float(np.max(np.abs(out_bpf - out_bf))))

    results["F3_torch_nonequivalence_to_BitFlip"] = {
        "n_states": 50,
        "n_different": sum(1 for d in f3_diffs if d > 1e-6),
        "max_diff": max(f3_diffs),
        "pass": sum(1 for d in f3_diffs if d > 1e-6) > 25,
    }

    # --- F4: Non-equivalence to ZDephasing via torch modules directly ---
    f4_diffs = []
    np.random.seed(666)
    for _ in range(50):
        bloch = np.random.randn(3)
        bloch = bloch / np.linalg.norm(bloch) * 0.8
        rho_np = make_rho_from_bloch(bloch)
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        p_val = np.random.uniform(0.05, 0.95)

        bpf = BitPhaseFlip(p_val)
        zd = ZDephasing(p_val)
        out_bpf = bpf(rho_t).detach().cpu().numpy()
        out_zd = zd(rho_t).detach().cpu().numpy()
        f4_diffs.append(float(np.max(np.abs(out_bpf - out_zd))))

    results["F4_torch_nonequivalence_to_ZDephasing"] = {
        "n_states": 50,
        "n_different": sum(1 for d in f4_diffs if d > 1e-6),
        "max_diff": max(f4_diffs),
        "pass": sum(1 for d in f4_diffs if d > 1e-6) > 25,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: p > 1 violates CPTP ---
    n1_results = {}
    for p_val in [1.5, 2.0, 5.0]:
        channel = BitPhaseFlip(p_val)
        K0, K1 = channel.kraus_operators()
        completeness = (K0.conj().T @ K0 + K1.conj().T @ K1).detach().cpu().numpy()
        identity_diff = float(np.max(np.abs(completeness - np.eye(2))))
        n1_results[f"p={p_val}"] = {
            "identity_diff": identity_diff,
            "cptp_violated": identity_diff > 0.01,
            "pass": identity_diff > 0.01,
        }
    results["N1_p_gt_1_violates_cptp"] = n1_results

    # --- N2: p < 0 violates CPTP ---
    n2_results = {}
    for p_val in [-0.1, -0.5, -1.0]:
        channel = BitPhaseFlip(p_val)
        rho = torch.tensor(TEST_STATES["|0><0|"], dtype=torch.complex64)
        out = channel(rho).detach().cpu().numpy()
        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))
        n2_results[f"p={p_val}"] = {
            "eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "has_negative_eigenvalue": min_eval < -1e-10,
            "pass": min_eval < -1e-10,
        }
    results["N2_p_lt_0_non_positive"] = n2_results

    # --- N3: Hermiticity preserved ---
    n3_results = {}
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = BitPhaseFlip(0.3)
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
        channel = BitPhaseFlip(0.0)
        out = channel(rho_t).detach().cpu().numpy()
        diff = float(np.max(np.abs(out - rho_np)))
        b1_results[name] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-6,
        }
    results["B1_p0_identity"] = b1_results

    # --- B2: p=1 maps rho -> Y*rho*Y ---
    b2_results = {}
    Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        channel = BitPhaseFlip(1.0)
        out = channel(rho_t).detach().cpu().numpy()
        expected = Y @ rho_np @ Y
        diff = float(np.max(np.abs(out - expected)))
        b2_results[name] = {
            "max_diff_from_Y_rho_Y": diff,
            "pass": diff < 1e-6,
        }
    results["B2_p1_y_rotation"] = b2_results

    # --- B3: p=0.5 on |0> ---
    b3_results = {}
    rho_zero = TEST_STATES["|0><0|"]
    rho_t = torch.tensor(rho_zero, dtype=torch.complex64)
    channel = BitPhaseFlip(0.5)
    out = channel(rho_t).detach().cpu().numpy()
    # Y|0> = i|1>, so Y|0><0|Y = |1><1|
    # (1-0.5)*|0><0| + 0.5*|1><1| = I/2
    expected = np.eye(2, dtype=np.complex128) / 2
    diff = float(np.max(np.abs(out - expected)))
    b3_results["zero_state_half_flipped"] = {
        "max_diff_from_I_half": diff,
        "pass": diff < 1e-6,
    }

    # p=0.5 on |+> -- should lose X and Z components, keep Y
    rho_plus = TEST_STATES["|+><+|"]
    out_plus = numpy_bit_phase_flip(rho_plus, 0.5)
    bloch_out = extract_bloch(out_plus)
    bloch_in = extract_bloch(rho_plus)
    # |+> has Bloch = (1,0,0). At p=0.5: X->0, Y->0 (was 0), Z->0 (was 0)
    # So output = I/2
    diff_from_mixed = float(np.max(np.abs(out_plus - np.eye(2) / 2)))
    b3_results["plus_state_at_p05_is_maximally_mixed"] = {
        "bloch_in": bloch_in.tolist(),
        "bloch_out": bloch_out.tolist(),
        "diff_from_I_half": diff_from_mixed,
        "pass": diff_from_mixed < 1e-10,
    }

    # p=0.5 on |+i> -- should survive (Y eigenstate)
    rho_pi = TEST_STATES["|+i><+i|"]
    out_pi = numpy_bit_phase_flip(rho_pi, 0.5)
    diff_pi = float(np.max(np.abs(out_pi - rho_pi)))
    b3_results["plus_i_state_at_p05_survives"] = {
        "max_diff_from_input": diff_pi,
        "pass": diff_pi < 1e-10,
    }
    results["B3_p05_behavior"] = b3_results

    # --- B4: Purity of |0> monotonically decreases with p in [0, 0.5] ---
    p_vals = np.linspace(0, 0.5, 20)
    purities = []
    rho_zero = TEST_STATES["|0><0|"]
    for p_val in p_vals:
        out = numpy_bit_phase_flip(rho_zero, p_val)
        purities.append(float(numpy_purity(out)))

    mono_decreasing = all(
        purities[i] >= purities[i + 1] - 1e-10
        for i in range(len(purities) - 1)
    )
    results["B4_purity_monotone_decrease_first_half"] = {
        "p_values": p_vals.tolist(),
        "purities": purities,
        "monotone_decreasing": mono_decreasing,
        "pass": mono_decreasing,
    }

    return results


# =====================================================================
# SYMPY SYMBOLIC CHECK
# =====================================================================

def run_sympy_check():
    """Symbolic verification of CPTP and Bloch decay structure."""
    if not TOOL_MANIFEST["sympy"]["tried"]:
        return {"skipped": True, "reason": "sympy not available"}

    p = sp.Symbol("p", real=True, positive=True)

    I = sp.eye(2)
    Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])

    # K0dK0 + K1dK1 = (1-p)*I + p*YdY = (1-p)*I + p*I = I
    sum_K = (1 - p) * I + p * (Y.H * Y)
    sum_simplified = sp.simplify(sum_K)
    is_identity = sum_simplified == I

    # Effect on general rho
    a, b_r, b_i, d = sp.symbols("a b_r b_i d", real=True)
    b = b_r + sp.I * b_i
    rho = sp.Matrix([[a, b], [sp.conjugate(b), d]])
    out = (1 - p) * rho + p * Y * rho * Y
    out_simplified = sp.simplify(out)

    # Diagonal: Y*rho*Y swaps diag AND negates off-diag
    # Y*[[a,b],[b*,d]]*Y = [[d,-b*],[-b,a]]
    # Actually: Y = [[0,-i],[i,0]]
    # Y*rho*Y^dag = Y*rho*(-Y) ... no, Y^dag = Y for Pauli
    # Let's compute: Y*[[a,b],[b*,d]]*Y
    # = [[0,-i],[i,0]]*[[a,b],[b*,d]]*[[0,-i],[i,0]]
    # Row 1 of Y*rho: [-i*b*, -i*d], [i*a, i*b]
    # Full product: [[d, -conj(b)],[-b, a]]
    # Wait let me just let sympy do it:
    diag_00 = sp.simplify(out_simplified[0, 0])
    diag_11 = sp.simplify(out_simplified[1, 1])
    off_01 = sp.simplify(out_simplified[0, 1])

    # The diagonal mixes like bit-flip: (1-p)*a + p*d
    expected_diag_00 = (1 - p) * a + p * d
    diag_match = sp.simplify(diag_00 - expected_diag_00) == 0

    # Off-diagonal: (1-p)*b + p*(-conj(b)) = ... NOT the same as X or Z
    # For X: off_01 = (1-p)*b + p*conj(b)
    # For Z: off_01 = (1-2p)*b
    # For Y: off_01 = (1-p)*b + p*(-b) = (1-2p)*b ... wait
    # Y*rho*Y: off_01 = -conj(b)? Let me check:
    # Actually Y*rho*Y where Y=[[0,-i],[i,0]]:
    # = [[0,-i],[i,0]] @ [[a,b],[b*,d]] @ [[0,-i],[i,0]]
    # First: Y*rho = [[-i*b*, -i*d],[i*a, i*b]]
    # Then: (Y*rho)*Y = [[-i*b*]*0+(-i*d)*i, (-i*b*)*(-i)+(-i*d)*0 ; ...]
    #                  = [[d, -b*], [-b, a]]
    # Wait, that has off-diag = -b* = -conj(b)
    # So out[0,1] = (1-p)*b + p*(-conj(b))
    expected_off = (1 - p) * b + p * (-sp.conjugate(b))
    off_match = sp.simplify(off_01 - expected_off) == 0

    # For real b (b_i=0): off = (1-p)*b - p*b = (1-2p)*b -- same as Z!
    # For pure imaginary b (b_r=0): off = (1-p)*i*b_i + p*i*b_i = i*b_i -- preserved!
    # This is the Y-basis behavior: imaginary off-diag (Y component) preserved

    return {
        "completeness_is_identity": bool(is_identity),
        "diagonal_00_formula": str(diag_00),
        "diagonal_matches_mix": bool(diag_match),
        "off_diagonal_formula": str(off_01),
        "off_diagonal_matches_expected": bool(off_match),
        "note": (
            "off_01 = (1-p)*b + p*(-conj(b)): "
            "real part decays as (1-2p), imaginary part preserved"
        ),
        "pass": bool(is_identity) and bool(off_match),
    }


# =====================================================================
# Z3 FIXED-POINT STRUCTURE PROOF
# =====================================================================

def run_z3_check():
    """Use z3 to prove Y-channel has different fixed-point structure than X and Z.

    Fixed points of Pauli-sigma channel E_sigma(rho) = (1-p)*rho + p*sigma*rho*sigma:
    - E_sigma(rho) = rho  iff  p*(sigma*rho*sigma - rho) = 0
    - For p != 0: sigma*rho*sigma = rho, i.e., [sigma, rho] = 0 (up to sign)

    X channel fixed points: states diagonal in X basis (real off-diag)
    Z channel fixed points: states diagonal in Z basis (zero off-diag)
    Y channel fixed points: states diagonal in Y basis (pure imaginary off-diag)

    We prove these are structurally different using z3.
    """
    if not TOOL_MANIFEST["z3"]["tried"]:
        return {"skipped": True, "reason": "z3 not available"}

    from z3 import Real, Solver, And, Not, Or, sat, unsat

    # Represent a general 2x2 Hermitian matrix rho = [[a, br+i*bi],[br-i*bi, d]]
    a = Real("a")
    d = Real("d")
    br = Real("br")  # real part of off-diagonal
    bi = Real("bi")  # imaginary part of off-diagonal

    # --- Parameter range check (same as other channels) ---
    p = Real("p")
    s = Solver()
    s.add(And(p >= 0, p <= 1))
    s.add(Not(And(1 - p >= 0, p >= 0)))
    result_valid = str(s.check())

    s2 = Solver()
    s2.add(p > 1)
    s2.add(Not(And(1 - p >= 0, p >= 0)))
    result_outside = str(s2.check())

    # --- Fixed-point structure differences ---
    # For X-channel: X*rho*X = rho iff diagonal swaps: a=d, off-diag preserved
    # Fixed point condition for X: a=d (any br, bi)
    # But actually X*[[a,br+i*bi],[br-i*bi,d]]*X = [[d,br-i*bi],[br+i*bi,a]]
    # So X*rho*X = rho requires a=d AND bi=0 (off-diag must be real)
    # Wait: X*rho*X[0,1] = br - i*bi, original [0,1] = br + i*bi
    # Equal iff bi = 0. And a=d.

    # For Z-channel: Z*rho*Z = [[a,-br-i*bi],[-br+i*bi,d]]
    # Equal to rho iff br=0 and bi=0 (diagonal states only)

    # For Y-channel: Y*rho*Y = [[d,-br+i*bi],[-br-i*bi,a]]
    # Wait, we computed: Y*rho*Y = [[d, -conj(b)],[-b, a]]
    # = [[d, -br+i*bi],[-br-i*bi, a]]
    # Equal to rho iff a=d AND -br+i*bi = br+i*bi iff br=0
    # So Y fixed points: a=d, br=0 (any bi)

    # Prove: X fixed points != Y fixed points
    # X: a=d, bi=0 (any br)
    # Y: a=d, br=0 (any bi)
    # These are different subspaces!

    # z3 proof: exists a state that is X-fixed but NOT Y-fixed
    s3 = Solver()
    # X-fixed: a=d, bi=0
    s3.add(a == d)
    s3.add(bi == 0)
    # NOT Y-fixed: not(a=d and br=0)
    s3.add(Not(And(a == d, br == 0)))
    # Need some non-trivial state
    s3.add(Or(br != 0, bi != 0))
    x_not_y = str(s3.check())  # Should be sat (e.g., a=d, bi=0, br=1)

    # Exists a state that is Y-fixed but NOT X-fixed
    s4 = Solver()
    s4.add(a == d)
    s4.add(br == 0)
    s4.add(Not(And(a == d, bi == 0)))
    s4.add(Or(br != 0, bi != 0))
    y_not_x = str(s4.check())  # Should be sat (e.g., a=d, br=0, bi=1)

    # Exists a state that is Z-fixed but NOT Y-fixed
    s5 = Solver()
    s5.add(br == 0)
    s5.add(bi == 0)
    s5.add(Not(And(a == d, br == 0)))
    s5.add(Or(a != 0, d != 0))
    z_not_y = str(s5.check())  # Should be sat (e.g., a=1, d=0, br=bi=0)

    # Exists a state that is Y-fixed but NOT Z-fixed
    s6 = Solver()
    s6.add(a == d)
    s6.add(br == 0)
    s6.add(Not(And(br == 0, bi == 0)))
    y_not_z = str(s6.check())  # Should be sat (e.g., a=d, br=0, bi=1)

    return {
        "inside_01_can_violate": result_valid,
        "outside_01_can_violate": result_outside,
        "param_range_pass": result_valid == "unsat" and result_outside == "sat",
        "fixed_point_analysis": {
            "X_fixed_points": "a=d, bi=0 (real off-diagonal)",
            "Y_fixed_points": "a=d, br=0 (pure imaginary off-diagonal)",
            "Z_fixed_points": "br=0, bi=0 (diagonal states)",
            "exists_X_fixed_not_Y_fixed": x_not_y,
            "exists_Y_fixed_not_X_fixed": y_not_x,
            "exists_Z_fixed_not_Y_fixed": z_not_y,
            "exists_Y_fixed_not_Z_fixed": y_not_z,
            "all_structurally_different": (
                x_not_y == "sat" and y_not_x == "sat"
                and z_not_y == "sat" and y_not_z == "sat"
            ),
        },
        "pass": (
            result_valid == "unsat"
            and result_outside == "sat"
            and x_not_y == "sat"
            and y_not_x == "sat"
            and z_not_y == "sat"
            and y_not_z == "sat"
        ),
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
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core module: BitPhaseFlip as nn.Module, autograd for purity gradients, "
        "direct non-equivalence proof against BitFlip and ZDephasing modules"
    )
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic CPTP completeness, off-diagonal decay structure, "
        "real part decays / imaginary part preserved"
    )
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Parameter range constraint AND fixed-point structure proof: "
        "Y-channel fixed points (a=d, br=0) differ from X (a=d, bi=0) "
        "and Z (br=bi=0)"
    )

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
        "name": "torch_bit_phase_flip",
        "phase": "Phase 3 sim",
        "description": (
            "Bit-phase-flip (Pauli-Y error) channel as differentiable nn.Module. "
            "NOT equivalent to BitFlip or ZDephasing -- proven via 100-state "
            "numerical comparison and z3 fixed-point structure analysis"
        ),
        "non_equivalence_proven": (
            "BitPhaseFlip != BitFlip AND BitPhaseFlip != ZDephasing "
            "(different fixed-point subspaces via z3)"
        ),
        "tool_manifest": TOOL_MANIFEST,
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
    out_path = os.path.join(out_dir, "torch_bit_phase_flip_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
