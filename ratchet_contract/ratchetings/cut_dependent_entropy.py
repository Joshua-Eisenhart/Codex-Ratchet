#!/usr/bin/env python3
"""Cut-dependent correlation entropy: the SIGNED correlation structure is born at the cut.

Provenance: the joint carrier functions ket, entangled, vn_entropy, ptrace,
negativity are LIFTED VERBATIM from system_v8/nested_manifold/rungC_joint_cuts.py;
cut_readouts is ADAPTED from rungC's -- byte-identical formulas for the shared
readouts (S_L/S_R/S_LR/I/S(L|R)/negativity), dropping rungC's unused
Ic_RL/CUT_FAMILY/Phi0/DeltaS fields. Not re-derived. This file is
the sibling arrow-packaging of ratchet_contract/ratchetings/pure_to_vn.py,
matching its channel_is_one_way predicate, control_discriminates gate,
BY_CONSTRUCTION reachability, qutip cross-check, and TOOL_MANIFEST /
TOOL_INTEGRATION_DEPTH / smt_role / classification / promotion_allowed /
ordering_status schema exactly.

Object: Layer J is the joint two-qubit density operator rho_AB on
C^2 (x) C^2. Layer M is the PAIR of marginals (rho_A, rho_B), one on each
factor. The proposed ratcheting map is marginalization
M(rho_AB) = (rho_A, rho_B) = (Tr_B rho_AB, Tr_A rho_AB).

CLAIM: marginalization is ONE-WAY -- it forgets the correlation entropies.
The conditional entropy S(A|B) = S(AB) - S(B) and the mutual information
I(A:B) = S(A) + S(B) - S(AB) are BORN AT THE CUT (computable only from the
joint rho_AB, never recoverable from the marginal pair alone).

GENUINELY-NEW CONTENT over pure_to_vn (novel_over_pure_to_vn, also recorded
in the receipt): pure_to_vn shows the MAGNITUDE (von Neumann entropy) is
born at the partial-trace cut -- a single nonnegative number appears where
none existed on the pure ray. THIS arrow shows the SIGNED correlation
structure is born at the joint cut -- specifically NEGATIVE conditional
entropy S(A|B) < 0 (the entanglement resource / "fuel"; -S(A|B) = I(A>B),
the coherent information). Classical Shannon conditional entropy
H(A|B) = H(A,B) - H(B) is ALWAYS >= 0 for any classical joint distribution
(a fact this file computes explicitly on a classical joint pmf, not merely
asserted in prose), so S(A|B) < 0 has NO classical shadow: this is the rung
where the SIGN of the entropy structure itself, not just its magnitude,
distinguishes quantum from classical. On the Bell state (t=pi/4),
S(A|B) = S_AB - S_B = 0 - 1 = -1 bit (s_cond_bell_bits, recorded below).

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". This finite probe does not settle a
canonical layer ordering or support bridge/axis/canonical promotion.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp
from z3 import Function, RealSort, RealVal, Solver, sat, unsat

try:
    import cvc5
except ImportError:  # Recorded honestly below; z3 remains the primary proof leg.
    cvc5 = None

try:
    import psutil
    _MEM_AVAILABLE_FRACTION = psutil.virtual_memory().available / psutil.virtual_memory().total
except ImportError:
    psutil = None
    _MEM_AVAILABLE_FRACTION = None

QUTIP_MEMORY_FLOOR = 0.15  # qutip is light (~200MB); not the >0.40 heavy-engine gate.
_QUTIP_IMPORT_ERROR: str | None = None
try:
    if _MEM_AVAILABLE_FRACTION is not None and _MEM_AVAILABLE_FRACTION < QUTIP_MEMORY_FLOOR:
        raise RuntimeError(
            f"psutil available fraction {_MEM_AVAILABLE_FRACTION:.3f} <= floor "
            f"{QUTIP_MEMORY_FLOOR}; qutip import skipped")
    import qutip as qt
except Exception as _qutip_exc:  # Recorded honestly below; qutip is a second-engine cross-check, not primary.
    qt = None
    _QUTIP_IMPORT_ERROR = repr(_qutip_exc)


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-9
NUM_TOL = 1.0e-10

OUT = Path(__file__).resolve().parent / "results" / "cut_dependent_entropy.json"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True,
              "reason": "Lifted rungC carrier (ket/entangled/vn_entropy/ptrace/negativity verbatim; cut_readouts adapted), "
                        "the marginalize/reconstruct witness-and-control pair, the Umegaki relative-entropy "
                        "cross-identity, and the classical Shannon H(A|B)>=0 contrast computation."},
    "sympy": {"tried": True, "used": True,
              "reason": "Exact family-wide algebraic identity S(L|R)(t) = -S_A(t) over the ENTIRE entangled "
                        "family (global rank-1 purity + Schmidt marginal symmetry, both proved symbolically), "
                        "not a sampled numeric approximation."},
    "z3": {"tried": True, "used": True,
           "reason": "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- the "
                     "load-bearing evidence is the numpy same-marginals/different-mutual-information witness "
                     "pair plus the sympy exact family identity."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "qutip": {"tried": True, "used": False,
              "reason": ("Second independent quantum-library engine (Qobj/entropy_conditional/entropy_mutual/"
                         "negativity); updated at runtime with its actual cross-check result.")
                        if qt is not None else f"Import skipped/failed: {_QUTIP_IMPORT_ERROR}"},
    "jax": {"tried": False, "used": False,
            "reason": "Not required for this finite two-qubit probe; queued as a confirmation leg, not run."},
    "julia": {"tried": False, "used": False,
              "reason": "DEFERRED_BLOCKED_ON_MEMORY (QuantumOptics precompile needs the >0.40 window; not run for this probe)."},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing", "sympy": "load_bearing", "z3": "supportive",
    "cvc5": None, "qutip": None, "jax": None, "julia": None,
}


# ---------------------------------------------------------------------------
# ket/entangled/vn_entropy/ptrace/negativity are LIFTED VERBATIM from
# system_v8/nested_manifold/rungC_joint_cuts.py; cut_readouts (below) is ADAPTED
# from rungC's -- byte-identical formulas for the shared readouts, drops rungC's
# unused Ic_RL/Phi0/DeltaS. Do not re-derive the shared quantities differently.
# ---------------------------------------------------------------------------
def ket(i, j):
    v = np.zeros(4, dtype=complex)
    v[2 * i + j] = 1.0
    return v


def entangled(t):
    psi = np.cos(t) * ket(0, 1) + np.sin(t) * ket(1, 0)
    return np.outer(psi, psi.conj())


def vn_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = w[w > 1e-14]
    return float(-(w * np.log2(w)).sum())


def ptrace(rho, keep):
    r = rho.reshape(2, 2, 2, 2)  # indices (l, r, l', r')
    if keep == "L":
        return np.trace(r, axis1=1, axis2=3)
    return np.trace(r, axis1=0, axis2=2)


def negativity(rho):
    pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    w = np.linalg.eigvalsh(pt)
    return float(-w[w < 0].sum())


def cut_readouts(rho):
    S_L = vn_entropy(ptrace(rho, "L"))
    S_R = vn_entropy(ptrace(rho, "R"))
    S_LR = vn_entropy(rho)
    I = S_L + S_R - S_LR
    S_cond = S_LR - S_R          # S(L|R)
    Ic_LR = -S_cond              # coherent information, cut (L|R)
    return {"S_L": S_L, "S_R": S_R, "S_LR": S_LR, "I": I,
            "S_L_given_R": S_cond, "I_c": Ic_LR, "negativity": negativity(rho)}
# ---------------------------------------------------------------------------
# End lifted block.
# ---------------------------------------------------------------------------


def marginalize_to_pair(rho: np.ndarray) -> np.ndarray:
    """M(rho_AB) = (rho_A, rho_B), stacked into one array so the generic
    channel_is_one_way(channel, a, b) predicate (identical to pure_to_vn.py /
    vn_to_shannon.py) applies unchanged."""
    return np.concatenate([ptrace(rho, "L").reshape(-1), ptrace(rho, "R").reshape(-1)])


def channel_is_one_way(channel, a, b) -> bool:
    """One-way iff distinct inputs a != b are collapsed to a common image.
    Verbatim generic predicate, lifted from pure_to_vn.py / vn_to_shannon.py."""
    return bool((not np.allclose(a, b, atol=NUM_TOL))
                and np.allclose(channel(a), channel(b), atol=NUM_TOL))


def reconstruct(rho: np.ndarray) -> np.ndarray:
    """Marginalize-then-remarry: R(rho) = kron(Tr_B rho, Tr_A rho)."""
    return np.kron(ptrace(rho, "L"), ptrace(rho, "R"))


def reconstruction_is_lossy(rho: np.ndarray, tol: float = NUM_TOL) -> bool:
    """CONTROL predicate (feed-both-and-differ): True iff rho is NOT a fixed
    point of reconstruct -- i.e. the marginal pair alone cannot rebuild rho.
    On the product submanifold reconstruct is the identity (False); on
    entangled states it is not (True). This is fed both an entangled probe
    and a product probe below and must return DIFFERENT answers for
    control_discriminates to hold."""
    return bool(not np.allclose(reconstruct(rho), rho, atol=tol))


def log2_hermitian(rho: np.ndarray, floor: float = 1e-14) -> np.ndarray:
    """Matrix log2 of a Hermitian PSD matrix via eigendecomposition. Zero
    eigenvalues are floored; they only ever get multiplied (in the caller's
    trace) against a partner matrix whose weight is itself zero in that same
    direction for every state probed here (checked, not assumed)."""
    w, v = np.linalg.eigh(rho)
    w_clipped = np.clip(np.real(w), floor, None)
    return (v * np.log2(w_clipped)) @ v.conj().T


def relative_entropy_bits(rho: np.ndarray, sigma: np.ndarray) -> float:
    """Umegaki relative entropy S(rho || sigma) = Tr[rho (log2 rho - log2 sigma)], in bits."""
    log2_rho = log2_hermitian(rho)
    log2_sigma = log2_hermitian(sigma)
    return float(np.real(np.trace(rho @ (log2_rho - log2_sigma))))


def classical_conditional_entropy_bits(joint_probs: dict[tuple[int, int], float]) -> float:
    """Shannon H(A|B) = H(A,B) - H(B) for a classical joint pmf over {0,1}x{0,1}.
    Operationalizes the "no classical shadow" claim: this is always >= 0."""
    def h(probs):
        vals = np.array([p for p in probs if p > 0.0])
        return float(-np.sum(vals * np.log2(vals)))
    h_ab = h(joint_probs.values())
    b_marg: dict[int, float] = {}
    for (_, b), p in joint_probs.items():
        b_marg[b] = b_marg.get(b, 0.0) + p
    h_b = h(b_marg.values())
    return h_ab - h_b


def symbolic_family_checks() -> dict[str, Any]:
    """Exact algebraic (not sampled) derivation that S(L|R)(t) = -S_A(t) over
    the ENTIRE entangled family entangled(t), t in (0, pi/2), by proving
    (a) the global state is exactly rank 1 (S_LR = 0 identically) and
    (b) the marginals are exactly Schmidt-symmetric (S_R = S_A identically)."""
    t = sp.symbols("t", real=True)
    c, s = sp.cos(t), sp.sin(t)
    psi = sp.Matrix([0, c, s, 0])  # matches ket(i,j) index=2*i+j: |01>-comp=1, |10>-comp=2
    rho = psi * psi.T

    support_block = sp.Matrix([[rho[1, 1], rho[1, 2]], [rho[2, 1], rho[2, 2]]])
    det_zero = sp.simplify(support_block.det()) == 0
    trace_one = sp.simplify(support_block.trace() - 1) == 0
    rank1_exact = bool(det_zero and trace_one)

    rho_a = sp.Matrix([[rho[0, 0] + rho[1, 1], rho[0, 2] + rho[1, 3]],
                       [rho[2, 0] + rho[3, 1], rho[2, 2] + rho[3, 3]]])
    rho_b = sp.Matrix([[rho[0, 0] + rho[2, 2], rho[0, 1] + rho[2, 3]],
                       [rho[1, 0] + rho[3, 2], rho[1, 1] + rho[3, 3]]])
    schmidt_symmetric = bool(sp.simplify(rho_a[0, 0] - rho_b[1, 1]) == 0
                             and sp.simplify(rho_a[1, 1] - rho_b[0, 0]) == 0)

    s_a = -c**2 * sp.log(c**2, 2) - s**2 * sp.log(s**2, 2)
    conditional_identity_exact = bool(rank1_exact and schmidt_symmetric)

    s_cond_pi4 = sp.simplify((-s_a).subs(t, sp.pi / 4))
    s_cond_pi4_is_minus_one = bool(sp.simplify(s_cond_pi4 - (-1)) == 0)
    endpoints_zero = all(sp.simplify(sp.limit(s_a, t, value, dir="+")) == 0
                         for value in (0, sp.pi / 2))

    return {
        "s_a_formula": str(s_a),
        "rank1_exact": rank1_exact,
        "schmidt_symmetric": schmidt_symmetric,
        "conditional_identity_exact": conditional_identity_exact,
        "s_cond_formula": "S(L|R)(t) = -S_A(t), exact over the whole entangled family (not sampled)",
        "s_cond_pi4_bits": float(sp.N(s_cond_pi4)),
        "s_cond_pi4_is_minus_one": s_cond_pi4_is_minus_one,
        "endpoints_zero": bool(endpoints_zero),
    }


def z3_noninjectivity() -> dict[str, str]:
    """Generic single-valued-function non-vacuity witness (NOT a mechanism
    encoding -- matches the fixed sibling convention exactly): the same
    marginal-pair key cannot deterministically recover two different
    mutual-information values."""
    key = RealVal("1")  # stands for the shared (rho_A, rho_B) marginal-pair key
    i_bell, i_prod = RealVal("2"), RealVal("0")
    recover_I = Function("recover_mutual_information", RealSort(), RealSort())
    solver = Solver()
    solver.add(recover_I(key) == i_bell, recover_I(key) == i_prod)
    result = solver.check()
    assert result == unsat
    relaxed = Solver()
    relaxed.add(recover_I(key) == i_bell)
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same marginal-pair key must recover both I=2 (bell) and I=0 (product)",
            "result": str(result), "erased_constraint_result": str(relaxed_result)}


def cvc5_noninjectivity() -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        recover_I = solver.mkConst(solver.mkFunctionSort([real], real), "recover_mutual_information")
        key, i_bell, i_prod = solver.mkReal(1), solver.mkReal(2), solver.mkReal(0)
        app = solver.mkTerm(cvc5.Kind.APPLY_UF, recover_I, key)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, i_bell))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, i_prod))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        recover_I2 = relaxed.mkConst(relaxed.mkFunctionSort([real2], real2), "recover_mutual_information_relaxed")
        app2 = relaxed.mkTerm(cvc5.Kind.APPLY_UF, recover_I2, relaxed.mkReal(1))
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2, relaxed.mkReal(2)))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same deterministic-recovery mutual-information contradiction"}
    except Exception as error:
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def qutip_cross_check(bell: np.ndarray) -> dict[str, Any]:
    """Independent second-engine recomputation of the Bell witness's S(L|R),
    I(L:B) and negativity using qutip's own Qobj/entropy_conditional/
    entropy_mutual/negativity primitives -- not numpy dressed as qutip."""
    if qt is None:
        return {"ran": False, "reason": _QUTIP_IMPORT_ERROR or "qutip import unavailable",
                "S_cond": None, "I": None, "negativity": None,
                "S_cond_divergence": None, "I_divergence": None, "negativity_divergence": None}
    try:
        bell_q = qt.Qobj(bell, dims=[[2, 2], [2, 2]])
        s_cond_q = float(qt.entropy_conditional(bell_q, 1, base=2))
        i_q = float(qt.entropy_mutual(bell_q, 0, 1, base=2))
        neg_q = float(qt.negativity(bell_q, 1))
        witness = cut_readouts(bell)
        s_cond_div = abs(s_cond_q - witness["S_L_given_R"])
        i_div = abs(i_q - witness["I"])
        neg_div = abs(neg_q - witness["negativity"])
        TOOL_MANIFEST["qutip"]["used"] = True
        TOOL_MANIFEST["qutip"]["reason"] = (
            f"qutip.entropy_conditional/entropy_mutual/negativity independently reproduced the Bell "
            f"witness (S(L|R)={s_cond_q:.6f}, I={i_q:.6f}, N={neg_q:.6f}), agreeing with the numpy "
            f"witness to {max(s_cond_div, i_div, neg_div):.3e}.")
        TOOL_INTEGRATION_DEPTH["qutip"] = "supportive"
        return {"ran": True, "reason": None, "S_cond": s_cond_q, "I": i_q, "negativity": neg_q,
                "S_cond_divergence": s_cond_div, "I_divergence": i_div, "negativity_divergence": neg_div}
    except Exception as error:
        TOOL_MANIFEST["qutip"]["used"] = False
        TOOL_MANIFEST["qutip"]["reason"] = f"qutip available but cross-check did not run successfully: {error}"
        return {"ran": False, "reason": str(error), "S_cond": None, "I": None, "negativity": None,
                "S_cond_divergence": None, "I_divergence": None, "negativity_divergence": None}


def payload(matrix: np.ndarray) -> list[Any]:
    values: list[Any] = []
    for value in matrix.reshape(-1):
        values.append(float(value.real) if abs(value.imag) < TOL else [float(value.real), float(value.imag)])
    return values


def matrix_payload(matrix: np.ndarray) -> list[list[Any]]:
    return [payload(row) for row in matrix]


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")

    symbolic = symbolic_family_checks()

    # --- WITNESS: identical marginals, different joint (C4-style construction, lifted) ---
    bell = entangled(math.pi / 4)
    bell_readouts = cut_readouts(bell)
    bell_product = reconstruct(bell)
    product_readouts = cut_readouts(bell_product)
    marg_gap = max(
        float(np.abs(ptrace(bell, "L") - ptrace(bell_product, "L")).max()),
        float(np.abs(ptrace(bell, "R") - ptrace(bell_product, "R")).max()))
    marginalize_is_one_way = channel_is_one_way(marginalize_to_pair, bell, bell_product)
    s_cond_bell_bits = bell_readouts["S_L_given_R"]

    # --- RELATIVE-ENTROPY LEG: I(A:B) a second way, as distance-from-product ---
    I_bell_rel = relative_entropy_bits(bell, bell_product)
    ccorr = 0.5 * (np.outer(ket(0, 1), ket(0, 1).conj()) + np.outer(ket(1, 0), ket(1, 0).conj()))
    ccorr_sigma = reconstruct(ccorr)
    ccorr_readouts = cut_readouts(ccorr)
    I_ccorr_rel = relative_entropy_bits(ccorr, ccorr_sigma)
    prod_pure = np.outer(ket(0, 1), ket(0, 1).conj())
    prod_sigma = reconstruct(prod_pure)
    prod_pure_readouts = cut_readouts(prod_pure)
    I_prod_pure_rel = relative_entropy_bits(prod_pure, prod_sigma)

    # --- CONTROL that flips (feed-both-and-differ, genuine) ---
    entangled_probe = entangled(math.pi / 3)
    control_entangled_lossy = reconstruction_is_lossy(entangled_probe)
    control_product_lossy = reconstruction_is_lossy(prod_pure)
    control_discriminates = bool(control_entangled_lossy and not control_product_lossy)

    # --- family-wide numeric sweep, redundant confirmation of the symbolic identity ---
    ts = np.linspace(0.0, math.pi / 2, 13)
    sweep = [(float(t), cut_readouts(entangled(t))) for t in ts]
    sweep_S_cond = [r["S_L_given_R"] for _, r in sweep]
    interior_S_cond = sweep_S_cond[1:-1]
    family_nonpositive = all(v <= 1e-9 for v in sweep_S_cond)
    family_interior_strictly_negative = all(v < -1e-6 for v in interior_S_cond)

    # --- classical Shannon contrast: H(A|B) >= 0 even at perfect classical correlation ---
    classical_perfect_anticorr = {(0, 1): 0.5, (1, 0): 0.5, (0, 0): 0.0, (1, 1): 0.0}
    classical_h_cond = classical_conditional_entropy_bits(classical_perfect_anticorr)

    # --- SMT (supportive only) + qutip cross-check ---
    z3_result = z3_noninjectivity()
    cvc5_result = cvc5_noninjectivity()
    qutip_result = qutip_cross_check(bell)

    checks: dict[str, bool] = {}
    checks["positive_same_marginals"] = marg_gap < 1e-12
    checks["positive_mutual_information_differs"] = abs(bell_readouts["I"] - product_readouts["I"]) > 0.5
    checks["positive_marginalize_is_one_way"] = marginalize_is_one_way
    checks["positive_s_cond_bell_negative"] = s_cond_bell_bits < -1e-6
    checks["positive_s_cond_bell_matches_minus_one_bit"] = abs(s_cond_bell_bits - (-1.0)) < TOL
    checks["positive_relative_entropy_matches_identity_bell"] = abs(bell_readouts["I"] - I_bell_rel) < TOL
    checks["positive_relative_entropy_matches_identity_ccorr"] = abs(ccorr_readouts["I"] - I_ccorr_rel) < TOL
    checks["positive_relative_entropy_matches_identity_product_boundary"] = abs(prod_pure_readouts["I"] - I_prod_pure_rel) < TOL
    checks["positive_symbolic_rank1_global_pure"] = symbolic["rank1_exact"]
    checks["positive_symbolic_schmidt_symmetric"] = symbolic["schmidt_symmetric"]
    checks["positive_symbolic_S_cond_equals_minus_S_A_exact"] = symbolic["conditional_identity_exact"]
    checks["positive_symbolic_S_cond_at_pi4_is_minus_one"] = symbolic["s_cond_pi4_is_minus_one"]
    checks["positive_family_sweep_nonpositive"] = family_nonpositive
    checks["positive_family_sweep_interior_strictly_negative"] = family_interior_strictly_negative
    checks["positive_classical_shadow_absent"] = classical_h_cond >= -1e-9  # H(A|B) never negative classically

    checks["negative_control_product_reconstruction_exact"] = not control_product_lossy
    checks["negative_control_entangled_probe_reconstruction_lossy"] = control_entangled_lossy

    checks["boundary_endpoint_t0_I_zero"] = abs(sweep[0][1]["I"]) < 1e-9
    checks["boundary_endpoint_tpi2_I_zero"] = abs(sweep[-1][1]["I"]) < 1e-9
    checks["boundary_endpoint_t0_S_cond_nonnegative"] = sweep[0][1]["S_L_given_R"] >= -1e-9
    checks["boundary_endpoint_tpi2_S_cond_nonnegative"] = sweep[-1][1]["S_L_given_R"] >= -1e-9
    checks["boundary_classical_corr_I_positive"] = ccorr_readouts["I"] > 0.5
    checks["boundary_classical_corr_negativity_zero"] = ccorr_readouts["negativity"] < 1e-9
    checks["boundary_classical_corr_S_cond_nonnegative"] = ccorr_readouts["S_L_given_R"] >= -1e-9

    qutip_max_div = None
    if qutip_result["ran"]:
        qutip_max_div = max(qutip_result["S_cond_divergence"], qutip_result["I_divergence"],
                            qutip_result["negativity_divergence"])
        if qutip_max_div > 1e-9:
            # Loud, not smoothed: a genuine cross-engine disagreement on the shared witness quantity.
            raise AssertionError(f"qutip cross-check diverges from the numpy witness by "
                                 f"{qutip_max_div} > 1e-9 -- report, do not smooth.")
        checks["positive_qutip_matches_numpy"] = qutip_max_div < 1e-9

    # Mechanism gate (the arrow's own facts), independent of control_discriminates so
    # BY_CONSTRUCTION is a genuinely reachable branch, not dead code -- mirrors
    # pure_to_vn.py / vn_to_shannon.py exactly: mechanism_ok excludes the two
    # control-channel booleans (control_entangled_lossy, control_product_lossy)
    # used to compute control_discriminates below.
    mechanism_ok = (
        checks["positive_same_marginals"] and checks["positive_mutual_information_differs"]
        and checks["positive_marginalize_is_one_way"] and checks["positive_s_cond_bell_negative"]
        and checks["positive_s_cond_bell_matches_minus_one_bit"]
        and checks["positive_relative_entropy_matches_identity_bell"]
        and checks["positive_relative_entropy_matches_identity_ccorr"]
        and checks["positive_relative_entropy_matches_identity_product_boundary"]
        and checks["positive_symbolic_rank1_global_pure"] and checks["positive_symbolic_schmidt_symmetric"]
        and checks["positive_symbolic_S_cond_equals_minus_S_A_exact"]
        and checks["positive_symbolic_S_cond_at_pi4_is_minus_one"]
        and checks["positive_family_sweep_nonpositive"] and checks["positive_family_sweep_interior_strictly_negative"]
        and checks["positive_classical_shadow_absent"]
        and checks["boundary_endpoint_t0_I_zero"] and checks["boundary_endpoint_tpi2_I_zero"]
        and checks["boundary_endpoint_t0_S_cond_nonnegative"] and checks["boundary_endpoint_tpi2_S_cond_nonnegative"]
        and checks["boundary_classical_corr_I_positive"] and checks["boundary_classical_corr_negativity_zero"]
        and checks["boundary_classical_corr_S_cond_nonnegative"]
        and (not qutip_result["ran"] or checks.get("positive_qutip_matches_numpy", True))
    )

    notes: list[str] = [
        "Finite two-qubit sampled probe only; proposed layer ordering is not canon.",
        "OPEN BOUNDARY (untested, named): the born-at-the-cut result is established only for the "
        "PURE two-qubit entangled(t) family. Mixed rho_AB and dimension > 2 (d_A d_B > 4) are NOT "
        "tested here -- the next tooth for this rung, before Holevo-at-records. No claim is made beyond "
        "the pure two-qubit family.",
        "S(L|R) < 0 has no classical shadow: the classical H(A|B) computed on the perfectly "
        f"anti-correlated joint pmf is {classical_h_cond:.6f} bits (>= 0), while the quantum "
        f"S(L|R) at the SAME correlation strength (Bell state) is {s_cond_bell_bits:.6f} bits (< 0).",
        symbolic["s_cond_formula"],
        "SMT encodes deterministic recovery of two different mutual-information values from the "
        "same marginal-pair key, not a full parametrization of all joints sharing that marginal pair.",
        "Control is a DISCRIMINATING predicate: the same reconstruction_is_lossy(rho) test returns "
        f"entangled_probe={control_entangled_lossy} vs product_probe={control_product_lossy}; it is not a constant.",
    ]
    if not mechanism_ok:
        verdict = "FAILED"
        notes.append("At least one required finite-probe check failed; inspect check details.")
    elif not control_discriminates:
        verdict = "BY_CONSTRUCTION"
        notes.append("The discriminating predicate did not separate the product probe from the entangled "
                     "probe; directionality is not entanglement-specific.")
    else:
        verdict = "CORRELATION_ENTROPY_BORN_AT_CUT"
    core_ok = mechanism_ok

    result = {
        "schema_version": "1.0",
        "layer_joint": "Layer J: joint two-qubit density operator rho_AB on C^2 (x) C^2.",
        "layer_marginal_pair": "Layer M: the pair of marginals (rho_A, rho_B) = (Tr_B rho_AB, Tr_A rho_AB).",
        "novel_over_pure_to_vn": (
            "pure_to_vn shows the MAGNITUDE (von Neumann entropy) is born at the partial-trace cut. "
            "This arrow shows the SIGNED correlation structure is born at the joint cut -- specifically "
            "NEGATIVE conditional entropy S(A|B) < 0 (the entanglement resource / fuel; "
            "-S(A|B) = I(A>B), the coherent information). Classical H(A|B) >= 0 ALWAYS "
            f"(computed here as {classical_h_cond:.6f} bits on a perfectly-correlated classical pmf), "
            "so S(A|B) < 0 has no classical shadow: this is the rung where the SIGN of the entropy "
            "structure, not just its magnitude, distinguishes quantum from classical."
        ),
        "s_cond_bell_bits": s_cond_bell_bits,
        "one_way_witness_pair": {
            "description": "bell = entangled(pi/4); bell_product = kron(Tr_B bell, Tr_A bell). "
                           "Identical marginals, different joint, different I(A:B) and S(A|B).",
            "bell_readouts": bell_readouts, "bell_product_readouts": product_readouts,
            "marginal_gap": marg_gap,
            "marginal_gap_evidence": {
                "raw_ptrace_L_bell": matrix_payload(ptrace(bell, "L")),
                "raw_ptrace_L_bell_product": matrix_payload(ptrace(bell_product, "L")),
                "raw_ptrace_R_bell": matrix_payload(ptrace(bell, "R")),
                "raw_ptrace_R_bell_product": matrix_payload(ptrace(bell_product, "R")),
            },
        },
        "relative_entropy_leg": {
            "description": "I(A:B) = S(rho_AB || rho_A (x) rho_B), Umegaki relative entropy in bits, "
                           "cross-checked against the S_A+S_B-S_AB identity.",
            "bell": {"I_via_identity": bell_readouts["I"], "I_via_relative_entropy": I_bell_rel,
                    "matches": checks["positive_relative_entropy_matches_identity_bell"]},
            "classically_correlated_mixture": {"I_via_identity": ccorr_readouts["I"], "I_via_relative_entropy": I_ccorr_rel,
                                               "matches": checks["positive_relative_entropy_matches_identity_ccorr"]},
            "product_boundary": {"I_via_identity": prod_pure_readouts["I"], "I_via_relative_entropy": I_prod_pure_rel,
                                 "matches": checks["positive_relative_entropy_matches_identity_product_boundary"]},
        },
        "control_channel": "reconstruction_is_lossy(rho): rho is NOT a fixed point of R(rho)=kron(Tr_B rho, Tr_A rho). "
                           "Fed both an entangled probe (t=pi/3) and a pure product probe; must return different answers.",
        "control_discrimination": {
            "predicate": "reconstruction_is_lossy(rho): rho != kron(Tr_B rho, Tr_A rho)",
            "entangled_probe_lossy": bool(control_entangled_lossy),
            "product_probe_lossy": bool(control_product_lossy),
            "discriminates": bool(control_discriminates),
            "note": "Feed-both-and-differ: same predicate returns True on the entangled probe and False on "
                    "the product probe; the control can flip and does not.",
        },
        "symbolic_family_identity": symbolic,
        "family_sweep": {
            "description": "entangled(t) for 13 t in [0, pi/2]; S(L|R)(t) sampled numerically as a "
                           "redundant confirmation of the symbolic identity above.",
            "t_values": [t for t, _ in sweep],
            "S_cond_values": sweep_S_cond,
            "nonpositive_everywhere": family_nonpositive,
            "strictly_negative_interior": family_interior_strictly_negative,
        },
        "classical_shadow_check": {
            "description": "Shannon H(A|B) on a classical joint pmf with PERFECT correlation "
                           "(p(0,1)=p(1,0)=0.5) -- the classical analogue of maximal correlation strength.",
            "joint_pmf": {f"{a}{b}": p for (a, b), p in classical_perfect_anticorr.items()},
            "H_A_given_B_bits": classical_h_cond,
            "always_nonnegative": checks["positive_classical_shadow_absent"],
        },
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "smt_role": "supportive_nonvacuity_only",
        "load_bearing_evidence": (
            "numpy same-marginals/different-correlation witness pair (Bell vs product-of-marginals) + "
            "Umegaki relative-entropy cross-identity (3 states) + exact sympy family-wide "
            "S(L|R)=-S_A identity + qutip independent recompute."
        ),
        "provenance": {
            "carrier": "system_v8/nested_manifold/rungC_joint_cuts.py "
                      "(ket/entangled/vn_entropy/ptrace/negativity lifted verbatim; "
                      "cut_readouts adapted -- shared readouts byte-identical, drops unused Ic_RL/Phi0/DeltaS)",
            "packaging_sibling": "ratchet_contract/ratchetings/pure_to_vn.py "
                                 "(channel_is_one_way / control_discriminates / BY_CONSTRUCTION-reachability / "
                                 "TOOL_MANIFEST / smt_role schema matched exactly)",
        },
        "checks": {k: bool(v) for k, v in checks.items()},
        "preregistered": sorted(checks.keys()),
        "core_ok": bool(core_ok),
        "floor_claims": [{"key": "ratcheting.cut_dependent_entropy.s_cond_margin",
                          "value": abs(s_cond_bell_bits), "direction": "higher_is_better"}],
        "engine_values": {"sympy_numpy_S_cond_bell": s_cond_bell_bits,
                          "qutip_S_cond_bell": qutip_result["S_cond"]},
        "qutip_vs_witness_divergence": qutip_max_div,
        "qutip_cross_check": qutip_result,
        "julia_leg": "DEFERRED_BLOCKED_ON_MEMORY (QuantumOptics precompile needs the >0.40 window; not run for this probe)",
        "engines_ran": {"sympy": True, "numpy": True, "z3": True, "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]),
                        "jax": False, "julia": False, "qutip": bool(qutip_result["ran"])},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
        "matrix_witnesses": {
            "bell": matrix_payload(bell), "bell_product": matrix_payload(bell_product),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(OUT), "verdict": verdict, "core_ok": core_ok,
        "control_discriminates": control_discriminates, "s_cond_bell_bits": s_cond_bell_bits,
        "z3": z3_result["result"], "z3_erased_constraint": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result["result"], "qutip_ran": qutip_result["ran"],
        "qutip_vs_witness_divergence": qutip_max_div,
    }, indent=2))


if __name__ == "__main__":
    main()
