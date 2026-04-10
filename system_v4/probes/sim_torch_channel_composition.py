#!/usr/bin/env python3
"""
Channel Composition as a differentiable torch.nn.Module.

Chains multiple quantum channels sequentially: rho -> C_n(...C_2(C_1(rho)))
Tests composition algebra, ordering sensitivity, semigroup laws,
gradient flow through composed chains, and Kraus operator equivalence.

Tests:
  P1: Depolarizing(0.1) then ZDephasing(0.2) more mixed than either alone
  P2: BitFlip(0.3) then PhaseFlip(0.3) order matters
  P3: AD(0.5) then AD(0.5) == AD(0.75) semigroup law
  P4: N applications of ZDephasing(p) == ZDephasing(1-(1-2p)^N / 2 + 1/2)
  P5: Identity composition (any channel with p=0 channels is unchanged)
  P6: Gradient of final purity w.r.t. ALL channel params via autograd
  P7: Composed Kraus operators vs direct application
  N1: Non-CPTP map in chain produces non-physical output
  B1: All channels at p=0 (identity composition)
  B2: All channels at p=1 (maximum decoherence)
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

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
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

# Import sibling channel modules
sys.path.insert(0, os.path.dirname(__file__))
from torch_modules.z_dephasing import ZDephasing  # noqa: E402
from torch_modules.amplitude_damping import AmplitudeDamping  # noqa: E402
from torch_modules.depolarizing import Depolarizing  # noqa: E402
from torch_modules.bit_flip import BitFlip  # noqa: E402
from sim_torch_phase_flip import PhaseFlip  # noqa: E402


# =====================================================================
# MODULE UNDER TEST: ChannelComposition
# =====================================================================

class ChannelComposition(nn.Module):
    """Differentiable sequential composition of quantum channels.

    Applies channels left-to-right: rho -> C_n(...C_2(C_1(rho)))
    All channel parameters remain differentiable through the full chain.
    """

    def __init__(self, channels):
        super().__init__()
        self.channels = nn.ModuleList(channels)

    def forward(self, rho):
        for ch in self.channels:
            rho = ch(rho)
        return rho


# =====================================================================
# NUMPY BASELINES
# =====================================================================

def numpy_z_dephasing(rho, p):
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return (1 - p) * rho + p * (Z @ rho @ Z)


def numpy_depolarizing(rho, p):
    d = rho.shape[0]
    I = np.eye(d, dtype=np.complex128)
    return (1 - p) * rho + p * I / d


def numpy_bit_flip(rho, p):
    X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    return (1 - p) * rho + p * (X @ rho @ X)


def numpy_phase_flip(rho, p):
    Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return (1 - p) * rho + p * (Z @ rho @ Z)


def numpy_amplitude_damping(rho, gamma):
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=np.complex128)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=np.complex128)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T


def numpy_purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def numpy_von_neumann_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > 1e-12]
    return float(-np.sum(evals * np.log(evals)))


# =====================================================================
# TORCH HELPERS
# =====================================================================

def torch_purity(rho):
    """Tr(rho^2), differentiable."""
    return torch.real(torch.trace(rho @ rho))


def make_rho_from_bloch(bloch):
    """Build 2x2 density matrix from Bloch vector (numpy)."""
    I = np.eye(2, dtype=np.complex128)
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return I / 2 + bloch[0] * sx / 2 + bloch[1] * sy / 2 + bloch[2] * sz / 2


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

    # --- P1: Depolarizing(0.1) then ZDephasing(0.2) more mixed than either alone ---
    p1_results = {}
    rho_plus_np = TEST_STATES["|+><+|"]
    rho_plus = torch.tensor(rho_plus_np, dtype=torch.complex64)

    # Single channels
    dep_only = Depolarizing(0.1)
    zdep_only = ZDephasing(0.2)

    out_dep = dep_only(rho_plus).detach().cpu().numpy()
    out_zdep = zdep_only(rho_plus).detach().cpu().numpy()

    purity_dep = numpy_purity(out_dep)
    purity_zdep = numpy_purity(out_zdep)

    # Composed
    composed = ChannelComposition([Depolarizing(0.1), ZDephasing(0.2)])
    out_composed = composed(rho_plus).detach().cpu().numpy()
    purity_composed = numpy_purity(out_composed)

    # Numpy cross-check
    np_step1 = numpy_depolarizing(rho_plus_np, 0.1)
    np_step2 = numpy_z_dephasing(np_step1, 0.2)
    purity_np = numpy_purity(np_step2)

    p1_results["purity_depolarizing_alone"] = purity_dep
    p1_results["purity_zdephasing_alone"] = purity_zdep
    p1_results["purity_composed"] = purity_composed
    p1_results["purity_numpy_cross"] = purity_np
    p1_results["composed_more_mixed_than_dep"] = purity_composed < purity_dep
    p1_results["composed_more_mixed_than_zdep"] = purity_composed < purity_zdep
    p1_results["torch_numpy_match"] = abs(purity_composed - purity_np) < 1e-5
    p1_results["pass"] = (
        purity_composed < purity_dep
        and purity_composed < purity_zdep
        and abs(purity_composed - purity_np) < 1e-5
    )
    results["P1_composition_more_mixed"] = p1_results

    # --- P2: AmplitudeDamping(0.3) then BitFlip(0.3) vs reversed order ---
    # Note: BitFlip and PhaseFlip commute as channels (both Pauli, ZX=XZ up to phase
    # that cancels in the sandwich). AmplitudeDamping is NOT a Pauli channel, so
    # AD composed with BitFlip genuinely does not commute.
    p2_results = {}
    rho_np = TEST_STATES["|1><1|"]
    rho_t = torch.tensor(rho_np, dtype=torch.complex64)

    # Order A: AmplitudeDamping -> BitFlip
    comp_a = ChannelComposition([AmplitudeDamping(0.3), BitFlip(0.3)])
    out_a = comp_a(rho_t).detach().cpu().numpy()

    # Order B: BitFlip -> AmplitudeDamping
    comp_b = ChannelComposition([BitFlip(0.3), AmplitudeDamping(0.3)])
    out_b = comp_b(rho_t).detach().cpu().numpy()

    # Numpy cross-checks
    np_a = numpy_bit_flip(numpy_amplitude_damping(rho_np, 0.3), 0.3)
    np_b = numpy_amplitude_damping(numpy_bit_flip(rho_np, 0.3), 0.3)

    diff_ab = float(np.max(np.abs(out_a - out_b)))
    np_diff = float(np.max(np.abs(np_a - np_b)))

    p2_results["order_a_output"] = out_a.tolist()
    p2_results["order_b_output"] = out_b.tolist()
    p2_results["max_diff_between_orders"] = diff_ab
    p2_results["numpy_max_diff_between_orders"] = np_diff
    p2_results["orders_differ"] = diff_ab > 1e-8
    p2_results["torch_a_matches_numpy_a"] = float(np.max(np.abs(out_a - np_a))) < 1e-5
    p2_results["torch_b_matches_numpy_b"] = float(np.max(np.abs(out_b - np_b))) < 1e-5
    p2_results["pass"] = diff_ab > 1e-8
    results["P2_order_matters"] = p2_results

    # --- P3: AD(0.5) then AD(0.5) == AD(0.75) semigroup law ---
    # Two applications of AD(gamma): effective gamma = 1 - (1-g)^2 = 1 - 0.25 = 0.75
    p3_results = {}
    test_states_p3 = {"|1><1|": TEST_STATES["|1><1|"], "|+><+|": TEST_STATES["|+><+|"]}
    for name, rho_np in test_states_p3.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)

        # Composed: AD(0.5) -> AD(0.5)
        comp_ad = ChannelComposition([AmplitudeDamping(0.5), AmplitudeDamping(0.5)])
        out_comp = comp_ad(rho_t).detach().cpu().numpy()

        # Single equivalent: AD(0.75)
        ad_equiv = AmplitudeDamping(0.75)
        out_equiv = ad_equiv(torch.tensor(rho_np, dtype=torch.complex64)).detach().cpu().numpy()

        # Numpy cross-check
        np_step1 = numpy_amplitude_damping(rho_np, 0.5)
        np_step2 = numpy_amplitude_damping(np_step1, 0.5)
        np_equiv = numpy_amplitude_damping(rho_np, 0.75)

        diff_comp_equiv = float(np.max(np.abs(out_comp - out_equiv)))
        diff_np = float(np.max(np.abs(np_step2 - np_equiv)))

        p3_results[name] = {
            "composed_output": out_comp.tolist(),
            "equivalent_output": out_equiv.tolist(),
            "diff_composed_vs_equivalent": diff_comp_equiv,
            "numpy_diff": diff_np,
            "pass": diff_comp_equiv < 1e-4 and diff_np < 1e-10,
        }
    results["P3_amplitude_damping_semigroup"] = p3_results

    # --- P4: N applications of ZDephasing(p) semigroup ---
    # ZDephasing: off-diag -> (1-2p)^N * off_diag_original
    # Effective single-shot p_eff = (1 - (1-2p)^N) / 2
    p4_results = {}
    p_val = 0.15
    for N in [1, 2, 5, 10]:
        rho_np = TEST_STATES["|+><+|"]
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)

        # Compose N copies
        channels = [ZDephasing(p_val) for _ in range(N)]
        comp = ChannelComposition(channels)
        out_comp = comp(rho_t).detach().cpu().numpy()

        # Effective p
        p_eff = (1 - (1 - 2 * p_val) ** N) / 2
        zdep_eff = ZDephasing(p_eff)
        out_eff = zdep_eff(torch.tensor(rho_np, dtype=torch.complex64)).detach().cpu().numpy()

        # Numpy cross-check
        rho_iter = rho_np.copy()
        for _ in range(N):
            rho_iter = numpy_z_dephasing(rho_iter, p_val)
        np_eff = numpy_z_dephasing(rho_np, p_eff)

        diff_torch = float(np.max(np.abs(out_comp - out_eff)))
        diff_np = float(np.max(np.abs(rho_iter - np_eff)))

        p4_results[f"N={N}"] = {
            "p_effective": p_eff,
            "diff_composed_vs_effective": diff_torch,
            "numpy_diff": diff_np,
            "pass": diff_torch < 1e-4 and diff_np < 1e-10,
        }
    results["P4_zdephasing_semigroup_N"] = p4_results

    # --- P5: Identity composition: channel with Identity channels ---
    p5_results = {}
    identity_channels = [
        ("ZDephasing(0)", ZDephasing(0.0)),
        ("Depolarizing(0)", Depolarizing(0.0)),
        ("BitFlip(0)", BitFlip(0.0)),
    ]
    target_channel = Depolarizing(0.3)

    for name, id_ch in identity_channels:
        for state_name, rho_np in [
            ("|+><+|", TEST_STATES["|+><+|"]),
            ("|0><0|", TEST_STATES["|0><0|"]),
        ]:
            rho_t = torch.tensor(rho_np, dtype=torch.complex64)

            # Target alone
            out_target = target_channel(rho_t).detach().cpu().numpy()

            # Target + identity before
            comp_before = ChannelComposition([id_ch, Depolarizing(0.3)])
            out_before = comp_before(rho_t).detach().cpu().numpy()

            # Target + identity after
            comp_after = ChannelComposition([Depolarizing(0.3), id_ch])
            out_after = comp_after(rho_t).detach().cpu().numpy()

            diff_before = float(np.max(np.abs(out_target - out_before)))
            diff_after = float(np.max(np.abs(out_target - out_after)))

            key = f"{name}_with_{state_name}"
            p5_results[key] = {
                "diff_identity_before": diff_before,
                "diff_identity_after": diff_after,
                "pass": diff_before < 1e-5 and diff_after < 1e-5,
            }
    results["P5_identity_composition"] = p5_results

    # --- P6: Gradient of final purity w.r.t. ALL channel parameters ---
    p6_results = {}
    rho_plus = torch.tensor(TEST_STATES["|+><+|"], dtype=torch.complex64)

    dep_ch = Depolarizing(0.1)
    zdep_ch = ZDephasing(0.2)
    bf_ch = BitFlip(0.15)
    comp = ChannelComposition([dep_ch, zdep_ch, bf_ch])

    out = comp(rho_plus)
    purity = torch_purity(out)
    purity.backward()

    grads = {}
    all_grads_exist = True
    for ch_name, ch in [("depolarizing", dep_ch), ("zdephasing", zdep_ch), ("bitflip", bf_ch)]:
        param = list(ch.parameters())[0]
        if param.grad is not None:
            grads[ch_name] = float(param.grad.item())
        else:
            grads[ch_name] = None
            all_grads_exist = False

    p6_results["purity"] = float(purity.item())
    p6_results["gradients"] = grads
    p6_results["all_grads_exist"] = all_grads_exist
    p6_results["all_grads_nonzero"] = all(
        v is not None and abs(v) > 1e-10 for v in grads.values()
    )
    p6_results["pass"] = all_grads_exist
    results["P6_gradient_all_params"] = p6_results

    # --- P7: Composed Kraus operators vs direct application ---
    # For ZDephasing(p1) then ZDephasing(p2):
    # Composed Kraus = {K_i^(2) K_j^(1)} for all i,j
    # Direct: apply channel 1 then channel 2
    p7_results = {}
    p1_val, p2_val = 0.3, 0.4
    ch1 = ZDephasing(p1_val)
    ch2 = ZDephasing(p2_val)

    K1_ops = ch1.kraus_operators()  # (K0_1, K1_1)
    K2_ops = ch2.kraus_operators()  # (K0_2, K1_2)

    # Build composed Kraus set: {K_i^(2) @ K_j^(1)}
    composed_kraus = []
    for K2 in K2_ops:
        for K1 in K1_ops:
            composed_kraus.append(K2 @ K1)

    for state_name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)

        # Direct sequential application
        comp_ch = ChannelComposition([ZDephasing(p1_val), ZDephasing(p2_val)])
        out_direct = comp_ch(rho_t).detach().cpu().numpy()

        # Via composed Kraus
        out_kraus = torch.zeros_like(rho_t)
        for K in composed_kraus:
            out_kraus = out_kraus + K @ rho_t @ K.conj().T
        out_kraus_np = out_kraus.detach().cpu().numpy()

        diff = float(np.max(np.abs(out_direct - out_kraus_np)))
        p7_results[state_name] = {
            "diff_direct_vs_kraus": diff,
            "pass": diff < 1e-4,
        }

    # Verify completeness of composed Kraus set
    completeness = sum(K.conj().T @ K for K in composed_kraus).detach().cpu().numpy()
    comp_diff = float(np.max(np.abs(completeness - np.eye(2))))
    p7_results["composed_kraus_completeness"] = {
        "identity_diff": comp_diff,
        "pass": comp_diff < 1e-4,
    }
    results["P7_composed_kraus_vs_direct"] = p7_results

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: Non-CPTP map in chain produces non-physical output ---
    # Use ZDephasing with p > 1 (non-CPTP)
    n1_results = {}
    rho_plus_np = TEST_STATES["|+><+|"]
    rho_plus = torch.tensor(rho_plus_np, dtype=torch.complex64)

    for bad_p in [1.5, 2.0]:
        bad_ch = ZDephasing(bad_p)
        comp = ChannelComposition([Depolarizing(0.1), bad_ch])
        out = comp(rho_plus).detach().cpu().numpy()

        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))
        trace_val = float(np.real(np.trace(out)))

        # Check hermiticity
        herm_diff = float(np.max(np.abs(out - out.conj().T)))

        # Non-physical: negative eigenvalue or trace != 1
        is_non_physical = min_eval < -1e-6 or abs(trace_val - 1.0) > 0.01

        n1_results[f"zdephasing_p={bad_p}"] = {
            "eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "trace": trace_val,
            "hermitian_diff": herm_diff,
            "non_physical_detected": is_non_physical,
            "pass": is_non_physical,
        }

    # Also test with amplitude damping gamma > 1
    for bad_g in [1.5, 3.0]:
        bad_ch = AmplitudeDamping(bad_g)
        comp = ChannelComposition([bad_ch, ZDephasing(0.1)])
        rho_1 = torch.tensor(TEST_STATES["|1><1|"], dtype=torch.complex64)
        out = comp(rho_1).detach().cpu().numpy()

        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))
        trace_val = float(np.real(np.trace(out)))
        is_non_physical = min_eval < -1e-6 or abs(trace_val - 1.0) > 0.01

        n1_results[f"amplitude_damping_gamma={bad_g}"] = {
            "eigenvalues": np.real(evals).tolist(),
            "min_eigenvalue": min_eval,
            "trace": trace_val,
            "non_physical_detected": is_non_physical,
            "pass": is_non_physical,
        }

    results["N1_non_cptp_in_chain"] = n1_results

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: All channels at p=0 (identity composition) ---
    b1_results = {}
    id_comp = ChannelComposition([
        Depolarizing(0.0),
        ZDephasing(0.0),
        BitFlip(0.0),
        PhaseFlip(0.0),
        AmplitudeDamping(0.0),
    ])
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out = id_comp(rho_t).detach().cpu().numpy()
        diff = float(np.max(np.abs(out - rho_np)))
        b1_results[name] = {
            "max_diff_from_input": diff,
            "pass": diff < 1e-5,
        }
    results["B1_all_p0_identity"] = b1_results

    # --- B2: All channels at p=1 (maximum decoherence) ---
    b2_results = {}
    max_comp = ChannelComposition([
        Depolarizing(1.0),
        ZDephasing(1.0),
        BitFlip(1.0),
        PhaseFlip(1.0),
        AmplitudeDamping(1.0),
    ])
    for name, rho_np in TEST_STATES.items():
        rho_t = torch.tensor(rho_np, dtype=torch.complex64)
        out = max_comp(rho_t).detach().cpu().numpy()

        # After Depolarizing(1.0): I/2
        # After ZDephasing(1.0): Z*(I/2)*Z = I/2 (unchanged)
        # After BitFlip(1.0): X*(I/2)*X = I/2 (unchanged)
        # After PhaseFlip(1.0): Z*(I/2)*Z = I/2 (unchanged)
        # After AmplitudeDamping(1.0): |0><0|
        ground = np.array([[1, 0], [0, 0]], dtype=np.complex128)
        diff_from_ground = float(np.max(np.abs(out - ground)))

        # Trace and positivity
        trace_val = float(np.real(np.trace(out)))
        evals = np.linalg.eigvalsh(out)
        min_eval = float(np.min(np.real(evals)))

        b2_results[name] = {
            "output": out.tolist(),
            "diff_from_ground_state": diff_from_ground,
            "trace": trace_val,
            "min_eigenvalue": min_eval,
            "is_physical": min_eval >= -1e-6 and abs(trace_val - 1.0) < 1e-5,
            "pass": diff_from_ground < 1e-5,
        }
    results["B2_all_p1_max_decoherence"] = b2_results

    # --- B3: Long chain convergence (many weak channels) ---
    b3_results = {}
    N = 20
    weak_p = 0.05
    rho_np = TEST_STATES["|+><+|"]
    rho_t = torch.tensor(rho_np, dtype=torch.complex64)

    long_chain = ChannelComposition([Depolarizing(weak_p) for _ in range(N)])
    out = long_chain(rho_t).detach().cpu().numpy()
    purity = numpy_purity(out)

    # Theoretical: (1-p)^N shrinkage of Bloch vector
    # Purity = 1/2 + |r|^2/2, for |+> state |r|=1
    # After N depolarizing: |r| -> (1-p)^N * |r|
    # Purity -> 1/2 + (1-p)^(2N) / 2
    expected_purity = 0.5 + (1 - weak_p) ** (2 * N) / 2

    b3_results["purity_after_20_weak_depolarizing"] = {
        "measured_purity": purity,
        "expected_purity": expected_purity,
        "diff": abs(purity - expected_purity),
        "pass": abs(purity - expected_purity) < 1e-4,
    }
    results["B3_long_chain_convergence"] = b3_results

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Mark tools as used
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core module: ChannelComposition as nn.Module chaining channel nn.Modules, "
        "autograd for purity gradients through composed chain"
    )
    for tool, meta in TOOL_MANIFEST.items():
        if meta["tried"] and not meta["used"] and not meta["reason"]:
            meta["reason"] = "import probe only; not used in the executed composition checks"

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
    }
    total_pass, total_tests = count_passes(all_results)

    results = {
        "name": "torch_channel_composition",
        "phase": "Phase 3 sim",
        "description": (
            "Channel composition as differentiable nn.Module chaining quantum channels. "
            "Tests semigroup laws, ordering sensitivity, gradient flow through composed chains, "
            "and Kraus operator product equivalence."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "total_tests": total_tests,
            "total_pass": total_pass,
            "all_pass": total_pass == total_tests,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "torch_channel_composition_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Tests: {total_pass}/{total_tests} passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- inspect results JSON")
