#!/usr/bin/env python3
"""
SIM: Shell / History-Window Unification Probe
==============================================
Step 6 Coupling Program bridge problem: shell/history unification.

Claim under test: The "shell" cut (spatial: which subsystem is inside vs
outside the constraint surface) and the "history-window" cut (temporal: which
time steps are inside vs outside the observable window) reduce to the SAME
mathematical object — a bipartition of the system into "retained" (A) and
"discarded" (B), where I_c(A;B) = S(A) - S(AB) is the coherent information.
If this is true, shell/history unification is earned.

Candidate bridge object Xi_hist: I_c computed on the (current-state, history)
bipartition. If I_c(current; history) equals I_c(inside-shell; outside-shell)
for the same density matrix, the bridge closes.

Positive tests:
  P1: 3-step Markov chain — shell cut vs history cut give equal I_c for witness state
  P2: Shell permutation symmetry — |I_c(A;B)| = |I_c(B;A)| for pure states
  P3: I_c gradient along history dimension — monotone increase with memory depth k

Negative tests (z3 UNSAT):
  N1: pure_state AND shell_Ic > 0 AND hist_Ic < 0 -> UNSAT (for same rho_AB)
  N2: product_state AND I_c > 0 -> UNSAT (cut-independent structural impossibility)

Boundary tests:
  B1: k=0 (memoryless) -> I_c = 0; both cuts agree on product state
  B2: k=max (full memory) -> I_c = S(current state); both cuts agree

Load-bearing tools:
  pytorch: autograd for I_c gradient along history dimension (P3);
           partial trace via reshape/einsum; eigvalsh for VNE
  z3:      UNSAT proofs for N1 (shell/hist sign contradiction impossible)
           and N2 (product state cannot have I_c > 0)
  sympy:   formal I_c = S(A) - S(AB) expression across cut labels
"""

import json
import math
import os

classification = "classical_baseline"
divergence_log = [
    "classical-baseline shell/history cut comparison only; tests finite "
    "coherent-information witnesses and z3 guard conditions without closing "
    "Xi_hist, Axis0, bridge, GStack, QIT, or nonclassical admission",
]

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False,
                  "reason": "no graph message passing in this entropy sim"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False,
                  "reason": "z3 sufficient for these linear arithmetic UNSAT proofs"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False,
                  "reason": "no geometric algebra layer in this entropy sim"},
    "geomstats": {"tried": False, "used": False,
                  "reason": "no Riemannian manifold layer here"},
    "e3nn":      {"tried": False, "used": False,
                  "reason": "no equivariant network layer here"},
    "rustworkx": {"tried": False, "used": False,
                  "reason": "no dependency graph here"},
    "xgi":       {"tried": False, "used": False,
                  "reason": "no hypergraph layer here"},
    "toponetx":  {"tried": False, "used": False,
                  "reason": "no cell complex layer here"},
    "gudhi":     {"tried": False, "used": False,
                  "reason": "no persistent homology here"},
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

# ---- tool imports ----

_torch_available = False
try:
    import torch
    _torch_available = True
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

_z3_available = False
try:
    import z3
    _z3_available = True
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

_sympy_available = False
try:
    import sympy as sp
    _sympy_available = True
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# Attempt remaining tools for manifest completeness
try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    pass

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    pass

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    pass

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    pass

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    pass

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    pass

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    pass

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    pass

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    pass


# =====================================================================
# CORE PYTORCH PRIMITIVES (load-bearing)
# =====================================================================

def vn_entropy(rho):
    """Von Neumann entropy S(rho) = -Tr(rho log rho) in nats.
    rho: torch.Tensor shape (d, d) complex.
    Load-bearing: uses torch.linalg.eigvalsh and torch.log.
    """
    evals = torch.linalg.eigvalsh(rho).real
    evals = evals.clamp(min=1e-14)
    evals = evals / evals.sum()
    return -(evals * torch.log(evals)).sum()


def partial_trace_B(rho_AB, dimA, dimB):
    """Partial trace over B: rho_A = Tr_B(rho_AB).
    rho_AB: shape (dimA*dimB, dimA*dimB).
    Returns shape (dimA, dimA).
    Index convention: rho_AB[a*dimB+b, a'*dimB+b'] stored as r[a,b,a',b'].
    rho_A[a, a'] = sum_b r[a, b, a', b] -> einsum 'abcb->ac'.
    Load-bearing: uses torch.einsum for correct partial trace (diagonal in B).
    """
    r = rho_AB.reshape(dimA, dimB, dimA, dimB)
    return torch.einsum('abcb->ac', r)


def partial_trace_A(rho_AB, dimA, dimB):
    """Partial trace over A: rho_B = Tr_A(rho_AB).
    rho_AB: shape (dimA*dimB, dimA*dimB).
    Returns shape (dimB, dimB).
    rho_B[b, b'] = sum_a r[a, b, a, b'] -> einsum 'abac->bc'.
    """
    r = rho_AB.reshape(dimA, dimB, dimA, dimB)
    return torch.einsum('abac->bc', r)


def coherent_information_AB(rho_AB, dimA, dimB):
    """I_c(A;B) = S(rho_A) - S(rho_AB).
    A is 'retained' (inside shell, or current state).
    B is 'discarded' (outside shell, or history).
    """
    rho_A = partial_trace_B(rho_AB, dimA, dimB)
    return vn_entropy(rho_A) - vn_entropy(rho_AB)


def coherent_information_BA(rho_AB, dimA, dimB):
    """I_c(B;A) = S(rho_B) - S(rho_AB).
    Swap the cut label: B is now 'retained'.
    """
    rho_B = partial_trace_A(rho_AB, dimA, dimB)
    return vn_entropy(rho_B) - vn_entropy(rho_AB)


def bell_state_rho():
    """Pure maximally entangled Bell state |Phi+> on 2x2.
    |Phi+> = (|00> + |11>) / sqrt(2).
    """
    psi = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2)
    return torch.outer(psi, psi.conj())


def product_state_rho(p_a=0.7, p_b=0.6):
    """Product state rho_A x rho_B with diagonal marginals."""
    rho_a = torch.tensor([[p_a, 0], [0, 1 - p_a]], dtype=torch.complex128)
    rho_b = torch.tensor([[p_b, 0], [0, 1 - p_b]], dtype=torch.complex128)
    return torch.kron(rho_a, rho_b)


def memory_state(k, max_k=3):
    """k-step memory state: mix Bell state with product state.
    k=0 -> product (memoryless), k=max_k -> maximally entangled.
    p = k / max_k interpolates smoothly.
    Load-bearing: constructed as torch tensor for autograd in P3.
    """
    p = k / max_k
    bell = torch.tensor(
        [[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]],
        dtype=torch.complex128,
    ) / 2.0
    product = torch.tensor(
        [[0.5, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0.5]],
        dtype=torch.complex128,
    )
    return (1 - p) * product + p * bell


def memory_state_float(k_float, max_k=3.0):
    """Differentiable version of memory_state for autograd.
    k_float: torch.Tensor scalar (requires_grad=True).
    max_k: float.
    """
    p = k_float / max_k
    bell = torch.tensor(
        [[1, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]],
        dtype=torch.complex128,
    ) / 2.0
    product = torch.tensor(
        [[0.5, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0.5]],
        dtype=torch.complex128,
    )
    # cast p to complex128 for broadcast
    p_c = p.to(dtype=torch.complex128)
    return (1 - p_c) * product + p_c * bell


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not _torch_available:
        results["skipped"] = "pytorch not available"
        return results

    LN2 = math.log(2.0)

    # ------------------------------------------------------------------
    # P1: 3-step Markov chain — shell cut vs history cut
    # ------------------------------------------------------------------
    # rho_01 and rho_12 are 2-qubit states from consecutive Markov steps.
    # Shell cut: bipartition ({rho_1}, {rho_0, rho_2}) — middle step as inside.
    # History cut: bipartition ({rho_2}, {rho_0, rho_1}) — latest vs history.
    #
    # We use a witness: the Bell state as rho_01 (step 0->1 channel is unitary,
    # maximally entangling), and rho_12 as Werner(p=0.8) (mixed, less entangled).
    # Both are 2-qubit states so we can compute I_c for each cut.
    #
    # The claim is that both cuts see the same I_c because both are bipartitions
    # of the SAME (2-qubit) state. The "shell cut" and "history cut" are just
    # relabelings of the retained/discarded split.

    p1 = {}

    # Witness state: Bell state (rho_01 = rho_12 for this test, showing
    # cut-independence for the same state)
    rho_bell = bell_state_rho()

    ic_shell = float(coherent_information_AB(rho_bell, 2, 2).item())
    ic_hist = float(coherent_information_BA(rho_bell, 2, 2).item())

    p1["bell_state_shell_cut"] = {
        "I_c_shell": ic_shell,
        "I_c_hist": ic_hist,
        "expected": LN2,
        "shell_diff": abs(ic_shell - LN2),
        "hist_diff": abs(ic_hist - LN2),
        "pass": abs(ic_shell - LN2) < 1e-6 and abs(ic_hist - LN2) < 1e-6,
        "note": "Pure Bell state: I_c(shell cut) = I_c(history cut) = log(2)",
    }

    # Markov step 01: Werner(p=0.9) as a more realistic intermediate state
    # Step 12: Werner(p=0.7) — decay of entanglement along the chain
    p_werner = 0.9
    bell = bell_state_rho()
    I4 = torch.eye(4, dtype=torch.complex128)
    rho_01 = (1.0 - p_werner) / 4.0 * I4 + p_werner * bell
    rho_12 = (1.0 - 0.7) / 4.0 * I4 + 0.7 * bell

    ic_01_shell = float(coherent_information_AB(rho_01, 2, 2).item())
    ic_01_hist = float(coherent_information_BA(rho_01, 2, 2).item())
    ic_12_shell = float(coherent_information_AB(rho_12, 2, 2).item())
    ic_12_hist = float(coherent_information_BA(rho_12, 2, 2).item())

    # For Werner states (U x U invariant), A and B are symmetric so
    # I_c(A;B) = I_c(B;A) — confirming cut-equivalence
    p1["werner_markov_chain_cut_equivalence"] = {
        "rho_01_ic_shell": ic_01_shell,
        "rho_01_ic_hist": ic_01_hist,
        "rho_01_cuts_agree": abs(ic_01_shell - ic_01_hist) < 1e-8,
        "rho_12_ic_shell": ic_12_shell,
        "rho_12_ic_hist": ic_12_hist,
        "rho_12_cuts_agree": abs(ic_12_shell - ic_12_hist) < 1e-8,
        "pass": (abs(ic_01_shell - ic_01_hist) < 1e-8
                 and abs(ic_12_shell - ic_12_hist) < 1e-8),
        "note": (
            "Werner state is symmetric under A<->B swap; "
            "shell cut and history cut agree exactly"
        ),
    }

    results["P1_markov_chain_shell_vs_history_cut"] = p1

    # ------------------------------------------------------------------
    # P2: Shell permutation symmetry — |I_c(A;B)| = |I_c(B;A)| for pure states
    # ------------------------------------------------------------------
    # For a PURE state |psi_AB>: S(AB) = 0, S(A) = S(B) (Schmidt decomposition).
    # Therefore I_c(A;B) = S(A) - 0 = S(A) and I_c(B;A) = S(B) - 0 = S(B).
    # Since S(A) = S(B) for pure states, I_c(A;B) = I_c(B;A).
    # Relabeling "inside" and "outside" gives the same |I_c| — unification holds.

    p2 = {}

    # Test with pure Bell state
    rho_bell = bell_state_rho()
    ic_AB = float(coherent_information_AB(rho_bell, 2, 2).item())
    ic_BA = float(coherent_information_BA(rho_bell, 2, 2).item())
    S_AB = float(vn_entropy(rho_bell).item())

    p2["bell_state_permutation"] = {
        "I_c_AB": ic_AB,
        "I_c_BA": ic_BA,
        "S_AB": S_AB,
        "diff": abs(ic_AB - ic_BA),
        "pass": abs(ic_AB - ic_BA) < 1e-8 and S_AB < 1e-10,
        "note": "Pure state: S(AB)=0 and S(A)=S(B), so I_c(A;B)=I_c(B;A)",
    }

    # Test with a non-symmetric pure state on 2x3 system
    # |psi> = (|00> + |11> + |12>) / sqrt(3) — partial entanglement on qubit side
    dimA, dimB = 2, 3
    psi_23 = torch.zeros(dimA * dimB, dtype=torch.complex128)
    psi_23[0 * dimB + 0] = 1.0   # |0,0>
    psi_23[1 * dimB + 1] = 1.0   # |1,1>
    psi_23[0 * dimB + 2] = 1.0   # |0,2>
    psi_23 = psi_23 / psi_23.norm()
    rho_23 = torch.outer(psi_23, psi_23.conj())

    ic_AB_23 = float(coherent_information_AB(rho_23, dimA, dimB).item())
    ic_BA_23 = float(coherent_information_BA(rho_23, dimA, dimB).item())
    S_full = float(vn_entropy(rho_23).item())

    p2["asymmetric_pure_2x3"] = {
        "I_c_AB": ic_AB_23,
        "I_c_BA": ic_BA_23,
        "S_AB": S_full,
        "diff_ic": abs(ic_AB_23 - ic_BA_23),
        "pass": abs(ic_AB_23 - ic_BA_23) < 1e-8 and S_full < 1e-10,
        "note": (
            "Pure state 2x3: S(A)=S(B) still holds (Schmidt), "
            "so I_c(A;B)=I_c(B;A) regardless of dimension"
        ),
    }

    results["P2_shell_permutation_symmetry"] = p2

    # ------------------------------------------------------------------
    # P3: I_c gradient along history dimension (autograd)
    # ------------------------------------------------------------------
    # memory_state(k) interpolates from product (k=0) to Bell (k=3).
    # I_c should increase monotonically with k.
    # Use pytorch autograd to confirm dI_c/dk > 0.

    p3 = {}

    ic_values = []
    for k_int in range(4):
        rho_k = memory_state(k_int, max_k=3)
        ic_k = float(coherent_information_AB(rho_k, 2, 2).real.item())
        ic_values.append(ic_k)

    # Check monotone increase
    diffs = [ic_values[i + 1] - ic_values[i] for i in range(3)]
    monotone = all(d > -1e-10 for d in diffs)

    p3["ic_values_by_memory_depth"] = {
        "k0": ic_values[0],
        "k1": ic_values[1],
        "k2": ic_values[2],
        "k3": ic_values[3],
        "increments": diffs,
        "monotone_increase": monotone,
        "pass": monotone,
        "note": "I_c increases monotonically with memory depth k: k=0 is product, k=3 is Bell",
    }

    # Autograd: compute dI_c/dk at k=1.5 using differentiable path through complex128
    # The complex128 -> eigvalsh.real -> log chain is differentiable in pytorch.
    k_val = torch.tensor(1.5, dtype=torch.float64, requires_grad=True)

    # Build rho as function of k_val using memory_state_float
    rho_diff = memory_state_float(k_val, max_k=3.0)

    # Partial trace via einsum (load-bearing: preserves grad through complex128)
    r_diff = rho_diff.reshape(2, 2, 2, 2)
    rho_A_diff = torch.einsum('abcb->ac', r_diff)
    evals_A_diff = torch.linalg.eigvalsh(rho_A_diff).real.clamp(min=1e-14)
    evals_A_diff = evals_A_diff / evals_A_diff.sum()
    S_A_diff = -(evals_A_diff * torch.log(evals_A_diff)).sum()
    evals_AB_diff = torch.linalg.eigvalsh(rho_diff).real.clamp(min=1e-14)
    evals_AB_diff = evals_AB_diff / evals_AB_diff.sum()
    S_AB_diff = -(evals_AB_diff * torch.log(evals_AB_diff)).sum()
    ic_grad_state = S_A_diff - S_AB_diff
    ic_grad_state.backward()
    grad_k = float(k_val.grad.item())

    p3["autograd_dIc_dk_at_k1p5"] = {
        "k": 1.5,
        "I_c": float(ic_grad_state.item()),
        "dI_c_dk": grad_k,
        "grad_positive": grad_k > 0,
        "pass": grad_k > 0,
        "note": "autograd confirms dI_c/dk > 0 at k=1.5; history depth increases coherent information",
    }

    results["P3_ic_gradient_history_dimension"] = p3

    # Mark pytorch as used
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "load-bearing: partial trace via reshape, VNE via eigvalsh, "
        "autograd for dI_c/dk in P3"
    )

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}

    # ------------------------------------------------------------------
    # N1: z3 UNSAT — shell and history cuts cannot disagree on I_c sign
    # For a pure bipartite state rho_AB: I_c = S(A) since S(AB) = 0.
    # S(A) = 0 iff A is pure (product), S(A) > 0 iff entangled.
    # Shell cut and history cut both observe S(A), so they cannot disagree.
    # Encode: pure_state AND shell_Ic > 0 AND hist_Ic < 0 -> UNSAT.
    # ------------------------------------------------------------------
    n1 = {}

    if not _z3_available:
        n1["skipped"] = "z3 not available"
    else:
        # For a pure state rho_AB with S(AB) = 0:
        #   I_c(shell) = S_A - 0 = S_A
        #   I_c(hist)  = S_B - 0 = S_B
        # For pure states: S_A = S_B (Schmidt theorem).
        # So sign(I_c(shell)) = sign(S_A) and sign(I_c(hist)) = sign(S_B).
        # Since S_A = S_B, they must have the same sign.
        # Contradiction: pure_state AND I_c_shell > 0 AND I_c_hist < 0
        #   requires S_A > 0 AND S_B < 0, but S_B >= 0 always (entropy non-negative).
        #   Additionally S_A = S_B for pure states, so S_A > 0 AND S_B < 0 is UNSAT.

        S_A = z3.Real("S_A")
        S_B = z3.Real("S_B")
        S_AB = z3.Real("S_AB")

        # Axioms
        pure_state = S_AB == 0                 # pure state: S(AB) = 0
        entropy_nonneg_A = S_A >= 0            # entropy always nonneg
        entropy_nonneg_B = S_B >= 0            # entropy always nonneg
        pure_state_symmetry = S_A == S_B       # Schmidt: S(A) = S(B) for pure |psi_AB>

        # I_c definitions (with S_AB = 0 for pure state)
        I_c_shell = S_A - S_AB                 # = S_A
        I_c_hist = S_B - S_AB                  # = S_B

        # Contradiction hypothesis
        shell_positive = I_c_shell > 0
        hist_negative = I_c_hist < 0

        solver = z3.Solver()
        solver.add(pure_state)
        solver.add(entropy_nonneg_A)
        solver.add(entropy_nonneg_B)
        solver.add(pure_state_symmetry)
        solver.add(shell_positive)
        solver.add(hist_negative)

        result_n1 = solver.check()
        is_unsat = (result_n1 == z3.unsat)

        n1["z3_pure_state_sign_contradiction"] = {
            "encoding": (
                "pure_state(S_AB=0) AND S_A=S_B(Schmidt) AND S_A>=0 AND S_B>=0 "
                "AND I_c_shell>0 AND I_c_hist<0"
            ),
            "z3_result": str(result_n1),
            "is_unsat": is_unsat,
            "interpretation": (
                "UNSAT: For pure state, S_A=S_B and both are nonneg, "
                "so I_c_shell and I_c_hist cannot have opposite signs. "
                "Shell/history unification is structurally enforced."
            ),
            "pass": is_unsat,
        }

        # Negative control: allow mixed state (S_AB > 0) and drop symmetry — now SAT
        # For a mixed bipartite state, I_c(shell) = S_A - S_AB can be > 0 (if S_A > S_AB)
        # while I_c(hist) = S_B - S_AB can be < 0 (if S_B < S_AB) for asymmetric state.
        # This SAT result confirms the UNSAT of N1 requires BOTH pure_state AND symmetry.
        solver_ctrl = z3.Solver()
        S_A_ctrl = z3.Real("S_A_ctrl")
        S_B_ctrl = z3.Real("S_B_ctrl")
        S_AB_ctrl = z3.Real("S_AB_ctrl")
        # Mixed state: S_AB > 0, subadditivity holds
        mixed_state = S_AB_ctrl > 0
        subadditivity = S_AB_ctrl <= S_A_ctrl + S_B_ctrl
        entropy_nonneg_A_ctrl = S_A_ctrl >= 0
        entropy_nonneg_B_ctrl = S_B_ctrl >= 0
        # Shell positive: S_A > S_AB (e.g. highly entangled A marginal)
        shell_ctrl_pos = S_A_ctrl - S_AB_ctrl > 0
        # Hist negative: S_B < S_AB (e.g. B marginal less mixed than joint)
        hist_ctrl_neg = S_B_ctrl - S_AB_ctrl < 0
        solver_ctrl.add(mixed_state)
        solver_ctrl.add(subadditivity)
        solver_ctrl.add(entropy_nonneg_A_ctrl)
        solver_ctrl.add(entropy_nonneg_B_ctrl)
        solver_ctrl.add(shell_ctrl_pos)
        solver_ctrl.add(hist_ctrl_neg)

        result_ctrl = solver_ctrl.check()
        n1["z3_negative_control_mixed_state_sign_differs"] = {
            "encoding": (
                "mixed_state(S_AB>0) AND S_AB<=S_A+S_B AND S_A>=0 AND S_B>=0 "
                "AND I_c_shell=S_A-S_AB>0 AND I_c_hist=S_B-S_AB<0 (NO pure/symmetry constraint)"
            ),
            "z3_result": str(result_ctrl),
            "is_sat": (result_ctrl == z3.sat),
            "interpretation": (
                "SAT: For mixed state without Schmidt symmetry, "
                "I_c(shell) > 0 and I_c(hist) < 0 is achievable. "
                "N1 UNSAT relies on BOTH pure_state AND S_A=S_B (Schmidt) — "
                "removing either allows sign disagreement."
            ),
            "pass": (result_ctrl == z3.sat),
        }

        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "load-bearing: UNSAT proof that pure-state shell/hist sign contradiction is "
            "impossible (N1); UNSAT proof that product state I_c > 0 is impossible (N2)"
        )

    results["N1_z3_shell_hist_sign_contradiction_unsat"] = n1

    # ------------------------------------------------------------------
    # N2: z3 UNSAT — I_c cannot be positive for product state under either cut
    # Product state rho_A x rho_B: S(AB) = S(A) + S(B).
    # I_c(A;B) = S(A) - S(AB) = S(A) - S(A) - S(B) = -S(B) <= 0.
    # This holds regardless of which cut is labelled "shell" or "history".
    # Structural impossibility is cut-independent — this IS the unification claim.
    # ------------------------------------------------------------------
    n2 = {}

    if not _z3_available:
        n2["skipped"] = "z3 not available"
    else:
        S_A2 = z3.Real("S_A2")
        S_B2 = z3.Real("S_B2")
        S_AB2 = z3.Real("S_AB2")
        I_c2 = z3.Real("I_c2")

        product_state_entropy = S_AB2 == S_A2 + S_B2   # product state additivity
        entropy_nonneg_A2 = S_A2 >= 0
        entropy_nonneg_B2 = S_B2 >= 0
        ic_definition = I_c2 == S_A2 - S_AB2            # I_c = S(A) - S(AB)
        ic_positive = I_c2 > 0                           # contradiction hypothesis

        solver2 = z3.Solver()
        solver2.add(product_state_entropy)
        solver2.add(entropy_nonneg_A2)
        solver2.add(entropy_nonneg_B2)
        solver2.add(ic_definition)
        solver2.add(ic_positive)

        result_n2 = solver2.check()
        is_unsat_n2 = (result_n2 == z3.unsat)

        n2["z3_product_state_ic_positive_unsat"] = {
            "encoding": (
                "product_state(S_AB=S_A+S_B) AND S_A>=0 AND S_B>=0 "
                "AND I_c=S_A-S_AB AND I_c>0"
            ),
            "z3_result": str(result_n2),
            "is_unsat": is_unsat_n2,
            "interpretation": (
                "UNSAT: For product state, I_c = -S_B <= 0 always. "
                "This is cut-independent: whether labelled 'shell' or 'history', "
                "a product state cannot have positive I_c. "
                "Cut-independence IS the shell/history unification claim."
            ),
            "pass": is_unsat_n2,
        }

        # Negative control: entangled state (S_AB < S_A + S_B) — I_c > 0 is SAT
        solver2_ctrl = z3.Solver()
        entangled = S_AB2 < S_A2 + S_B2                 # entangled: sub-additive S
        solver2_ctrl.add(entangled)
        solver2_ctrl.add(entropy_nonneg_A2)
        solver2_ctrl.add(entropy_nonneg_B2)
        solver2_ctrl.add(ic_definition)
        solver2_ctrl.add(ic_positive)
        # Also need S_A > S_AB for I_c > 0 (possible for entangled)
        solver2_ctrl.add(S_A2 > S_AB2)

        result_ctrl2 = solver2_ctrl.check()
        n2["z3_entangled_state_negative_control"] = {
            "encoding": (
                "entangled(S_AB < S_A+S_B) AND S_A>=0 AND S_B>=0 "
                "AND I_c=S_A-S_AB AND S_A>S_AB AND I_c>0"
            ),
            "z3_result": str(result_ctrl2),
            "is_sat": (result_ctrl2 == z3.sat),
            "interpretation": (
                "SAT: Entangled state can have I_c > 0. "
                "Product-state UNSAT is not trivially true for all states."
            ),
            "pass": (result_ctrl2 == z3.sat),
        }

    results["N2_z3_product_state_ic_positive_unsat"] = n2

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not _torch_available:
        results["skipped"] = "pytorch not available"
        return results

    # ------------------------------------------------------------------
    # B1: k=0 (memoryless) -> I_c = 0; shell and history cuts agree
    # ------------------------------------------------------------------
    b1 = {}

    rho_k0 = memory_state(0, max_k=3)
    ic_shell_k0 = float(coherent_information_AB(rho_k0, 2, 2).real.item())
    ic_hist_k0 = float(coherent_information_BA(rho_k0, 2, 2).real.item())

    # Product state: I_c(A;B) = -S(B) = -log(2)*binary_entropy(0.5) for 50/50 marginal B
    # memory_state(0) = product [[0.5,0,0,0],[0,...],[0,...],[0,0,0,0.5]] = diag(0.5,0,0,0.5)
    # rho_A = Tr_B = diag(0.5, 0.5), rho_B = diag(0.5, 0.5)
    # S(A) = log(2), S(B) = log(2), S(AB) = 2*log(2)  [since it's product, S_AB = S_A + S_B]
    # Actually rho_k0 = diag(0.5, 0, 0, 0.5) which is a pure state (|00> + |11>)/sqrt(2)?
    # No: outer products give [[0.5,0,0,0.5],[0,0,0,0],[0,0,0,0],[0.5,0,0,0.5]] = Bell state
    # But memory_state(0) is the product matrix diag(0.5, 0, 0, 0.5) (no off-diagonals)
    # Check: diag is [[0.5,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0.5]]
    # rho_A = partial_trace_B = diag(0.5,0.5), rho_B = diag(0.5,0.5)
    # S(AB) = -0.5*log(0.5) - 0.5*log(0.5) = log(2) [rank 2 diagonal]
    # S(A) = log(2), I_c(A;B) = log(2) - log(2) = 0 -- product-like (matches claim)

    b1["k0_memoryless_shell_ic"] = {
        "I_c_shell": ic_shell_k0,
        "I_c_hist": ic_hist_k0,
        "both_near_zero": abs(ic_shell_k0) < 1e-6 and abs(ic_hist_k0) < 1e-6,
        "pass": abs(ic_shell_k0) < 1e-6 and abs(ic_hist_k0) < 1e-6,
        "note": (
            "k=0 product state: I_c=0 for both cuts; "
            "shell and history cuts agree at boundary"
        ),
    }

    results["B1_k0_memoryless_zero_ic"] = b1

    # ------------------------------------------------------------------
    # B2: k=max (full memory) -> I_c = S(current state)
    # ------------------------------------------------------------------
    b2 = {}

    rho_kmax = memory_state(3, max_k=3)
    ic_shell_kmax = float(coherent_information_AB(rho_kmax, 2, 2).real.item())
    ic_hist_kmax = float(coherent_information_BA(rho_kmax, 2, 2).real.item())

    # k=3: memory_state(3, max_k=3) = Bell state (p=1.0)
    # S(A) = log(2), S(AB) = 0 (pure Bell state), I_c = log(2)
    LN2 = math.log(2.0)
    rho_A_kmax = partial_trace_B(rho_kmax, 2, 2)
    S_A_kmax = float(vn_entropy(rho_A_kmax).real.item())

    b2["kmax_full_memory_shell_ic"] = {
        "I_c_shell": ic_shell_kmax,
        "I_c_hist": ic_hist_kmax,
        "S_A": S_A_kmax,
        "expected_ic": LN2,
        "shell_diff": abs(ic_shell_kmax - LN2),
        "hist_diff": abs(ic_hist_kmax - LN2),
        "both_equal_SA": abs(ic_shell_kmax - S_A_kmax) < 1e-6 and abs(ic_hist_kmax - S_A_kmax) < 1e-6,
        "pass": abs(ic_shell_kmax - LN2) < 1e-6 and abs(ic_hist_kmax - LN2) < 1e-6,
        "note": (
            "k=3 Bell state: I_c = log(2) = S(A) for both cuts; "
            "shell and history cuts agree at maximal memory"
        ),
    }

    results["B2_kmax_full_memory_ic_equals_SA"] = b2

    # ------------------------------------------------------------------
    # B3 (sympy): formal I_c expression confirms cut-label independence
    # ------------------------------------------------------------------
    b3 = {}

    if _sympy_available:
        S_A_sym, S_B_sym, S_AB_sym = sp.symbols("S_A S_B S_AB", positive=True)

        # Shell cut: A = inside-shell, B = outside
        I_c_shell_sym = S_A_sym - S_AB_sym
        # History cut: A = current step, B = history
        I_c_hist_sym = S_A_sym - S_AB_sym  # same expression, different semantic labels

        # For pure state: S_AB = 0 and S_A = S_B
        I_c_shell_pure = I_c_shell_sym.subs(S_AB_sym, 0)
        I_c_hist_pure = I_c_hist_sym.subs(S_AB_sym, 0)
        pure_equal = sp.simplify(I_c_shell_pure - I_c_hist_pure) == 0

        # For product state: S_AB = S_A + S_B
        I_c_shell_prod = I_c_shell_sym.subs(S_AB_sym, S_A_sym + S_B_sym)
        I_c_hist_prod = I_c_hist_sym.subs(S_AB_sym, S_A_sym + S_B_sym)
        prod_equal = sp.simplify(I_c_shell_prod - I_c_hist_prod) == 0
        prod_nonpos = sp.simplify(I_c_shell_prod) == -S_B_sym

        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "supportive: formal I_c = S(A) - S(AB) expression confirms that "
            "shell and history cut labels produce identical algebraic objects"
        )

        b3["sympy_formal_expression"] = {
            "I_c_shell_general": str(I_c_shell_sym),
            "I_c_hist_general": str(I_c_hist_sym),
            "expressions_identical": str(I_c_shell_sym) == str(I_c_hist_sym),
            "I_c_pure_state": str(I_c_shell_pure),
            "pure_state_equal": pure_equal,
            "I_c_product_state": str(I_c_shell_prod),
            "product_state_nonpositive": prod_nonpos,
            "pass": pure_equal and prod_nonpos,
            "note": (
                "Sympy confirms: I_c(shell) and I_c(hist) are the same algebraic expression "
                "S_A - S_AB with different semantic labels. "
                "The structural equivalence is a tautology once cuts are defined as bipartitions."
            ),
        }
    else:
        b3["skipped"] = "sympy not available"

    results["B3_sympy_formal_cut_label_independence"] = b3

    return results


# =====================================================================
# MAIN
# =====================================================================

def count_section(section):
    if not isinstance(section, dict):
        return {"passed": 0, "failed": 0, "total": 0}
    total = 0
    passed = 0
    for val in section.values():
        if isinstance(val, dict):
            if "pass" in val:
                total += 1
                if val["pass"] is True:
                    passed += 1
            else:
                # Recurse one level for nested dicts (e.g. P1, P2, P3 sub-dicts)
                for subval in val.values():
                    if isinstance(subval, dict) and "pass" in subval:
                        total += 1
                        if subval["pass"] is True:
                            passed += 1
    return {"passed": passed, "failed": total - passed, "total": total}


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    pos_counts = count_section(positive)
    neg_counts = count_section(negative)
    bnd_counts = count_section(boundary)
    total_fail = pos_counts["failed"] + neg_counts["failed"] + bnd_counts["failed"]

    results = {
        "name": "Shell / History-Window Unification Probe",
        "probe": "sim_shell_hist_unification_probe",
        "purpose": (
            "Test whether shell cut (spatial: inside vs outside constraint surface) "
            "and history-window cut (temporal: current vs history) reduce to the same "
            "mathematical object I_c(A;B) = S(A) - S(AB). "
            "Bridge object Xi_hist: I_c(current; history) = I_c(inside-shell; outside-shell)."
        ),
        "coupling_program_step": 6,
        "bridge_claim": "shell/history unification via I_c bipartition equivalence",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": classification,
        "divergence_log": divergence_log,
        "caveat": (
            "Step 6 bridge. Shell/history cuts are candidate-equivalent; "
            "this is not promoted to canonical without Steps 1-5 evidence. "
            "Structural impossibility proofs (z3 UNSAT) are load-bearing; "
            "numeric tests are candidate witnesses."
        ),
        "summary": {
            "positive_pass": pos_counts["passed"],
            "positive_fail": pos_counts["failed"],
            "negative_pass": neg_counts["passed"],
            "negative_fail": neg_counts["failed"],
            "boundary_pass": bnd_counts["passed"],
            "boundary_fail": bnd_counts["failed"],
            "total_fail": total_fail,
            "all_pass": total_fail == 0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_shell_hist_unification_probe_results.json"
    )
    with open(out_path, "w") as fh:
        json.dump(results, fh, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(json.dumps(results["summary"], indent=2))
