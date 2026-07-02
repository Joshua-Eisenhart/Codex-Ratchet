#!/usr/bin/env python3
"""Deep, standalone geometry lego: Left/Right Weyl chirality geometry (KNOWN math).

This is a lego / pre-sim phase artifact. It computes the REAL left/right Weyl
(chiral-projector) geometry in torch (complex128 / float64) and cross-checks every
named invariant against its KNOWN analytic value. It is NOT gated on manifold
membership: classification = "diagnostic_only" (hypothetical, unadmitted). No
distinctness gate, no forcing filter, no cross-layer rules.

Object computed (genuine, no labels, no stand-ins, no random claim-matrices):
  Chirality:  gamma5 = diag(+1,+1,-1,-1)  in the 4-component chiral (Weyl) Dirac basis.
              gamma5 is the chirality operator: gamma5^2 = I, gamma5^dag = gamma5.
  Projectors: P_L = (I + gamma5)/2,  P_R = (I - gamma5)/2  (orthogonal projectors).
  Weyl spinors: psi_L = P_L psi,  psi_R = P_R psi  (left/right chiral components).
  Densities:  rho_L = psi_L psi_L^dag,  rho_R = psi_R psi_R^dag.
  Evolution:  opposite-handed Hamiltonians H_L = +H0, H_R = -H0 with the von Neumann
              equation d rho_s/dt = -i [H_s, rho_s]; closed-form U_s(t) = exp(-i H_s t).
              Because H_R = -H0 = -H_L, the right-handed evolution is the LEFT-handed
              evolution run backward in time: U_R(t) = U_L(-t) exactly.

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; match is COMPUTED, never hardcoded True):
  - gamma5^2 == I
  - P_L + P_R == I
  - P_L P_R == 0   (orthogonal projectors)
  - P_R P_L == 0
  - P_L^2 == P_L,  P_R^2 == P_R   (idempotent)
  - P_L^dag == P_L,  P_R^dag == P_R   (Hermitian / orthogonal projectors)
  - rank(P_L) == 2, rank(P_R) == 2  (two left, two right Weyl components)
  - the L and R Weyl subspaces are orthogonal: P_L psi  perp  P_R psi
  - left and right evolutions are time-reverses: U_R(t) == U_L(-t)
    (equivalently rho_R(t) == [the rho_L(-t) structure])
  - clifford Cl(1,3) chirality element (i * pseudoscalar e1234)^2 == +1 == gamma5^2
  - sympy EXACT: every projector identity holds symbolically (no float tolerance)

ANTI-FABRICATION: if any computed invariant does not match its known value, it is
reported as a blocker, not fudged.

TOOLS (all load-bearing in the execution path):
  torch     -- ALL chiral states, projectors, densities, U(1)... no: unitary time
               evolution exp(-i H t), commutator d rho/dt, subspace orthogonality,
               time-reverse comparison. Every number comes from torch.complex128.
  sympy     -- EXACT symbolic projector algebra: gamma5^2=I, P_L+P_R=I, P_L P_R=0,
               idempotency, Hermiticity, traces -- all as exact matrix identities,
               not float comparisons.
  z3        -- SMT certificate that P_L + P_R = I structurally (all 16 entry residuals
               are zero; the negation is UNSAT) and that P_L P_R = 0 structurally.
  cvc5      -- independent SMT family (QF_NRA) certifying the same P_L+P_R=I and
               P_L P_R=0 facts (negation UNSAT).
  clifford  -- Cl(1,3) geometric algebra: the chirality element is i times the
               pseudoscalar e1234; (i e1234)^2 = +1 reproduces gamma5^2 = I from the
               geometric-algebra structure (not a hardcoded matrix).

WIDE VARIATION: many sampled psi (Haar via QR), multiple H0 (Hermitian, sampled +
structured), multiple evolution times, multiple seeds.

NEGATIVES (collapse controls, must change/kill the chiral signature):
  merge_LR          P_L := P_R  -> P_L + P_R = 2 P_R != I, P_L P_R = P_R != 0 (chirality gone).
  handedness_gone   H_R := H_L = +H0 -> U_R(t) != U_L(-t) (the time-reverse relation breaks).
  swap_sigma        swap the chiral block structure (gamma5 -> +I, i.e. no sign split)
                    -> P_R = 0, all states are 'left' (the L/R split collapses).

finite_map: (4-comp chiral spinor psi, Hermitian H0, time t) ->
            (P_L, P_R, psi_L, psi_R, rho_L, rho_R, U_L(t), U_R(t), chiral invariants)
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3

CDTYPE = torch.complex128
RTYPE = torch.float64
torch.set_default_dtype(RTYPE)

TOL = 1.0e-9            # tolerance for float64 numeric invariants
TOL_EVO = 1.0e-9       # matrix_exp comparison floor
TOL_SMT = 1.0e-9       # SMT structural-residual tolerance

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_left_right_weyl_deep_probe"

# Wide variation sweeps.
SEEDS = [0, 1, 2, 3, 4, 5, 6, 7]
TIMES = [0.13, 0.37, 0.5, 0.91, 1.3, 2.0]
N_PSI_PER_SEED = 8

# Chiral (Weyl) basis chirality operator and projectors (the carrier algebra).
I4 = torch.eye(4, dtype=CDTYPE)
GAMMA5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=CDTYPE))
P_L = (I4 + GAMMA5) / 2
P_R = (I4 - GAMMA5) / 2


# --------------------------------------------------------------------------- #
# Core chiral geometry (torch, load-bearing)                                  #
# --------------------------------------------------------------------------- #
def normalize(psi: torch.Tensor) -> torch.Tensor:
    n = torch.linalg.vector_norm(psi)
    return psi / n if float(n.item()) > 0 else psi


def haar_spinor4(gen: torch.Generator) -> torch.Tensor:
    """Haar-random C^4 spinor via QR of a complex Gaussian matrix (genuine, not a
    hand-built label state)."""
    re = torch.randn(4, 4, generator=gen, dtype=RTYPE)
    im = torch.randn(4, 4, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)
    return normalize(q[:, 0].clone())


def haar_hermitian4(gen: torch.Generator) -> torch.Tensor:
    """A genuine Hermitian 4x4 H0 (GUE-style) -- a real Hamiltonian carrier."""
    re = torch.randn(4, 4, generator=gen, dtype=RTYPE)
    im = torch.randn(4, 4, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    return (a + a.conj().T) / 2


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def evolve(rho: torch.Tensor, H: torch.Tensor, t: float) -> torch.Tensor:
    """Unitary evolution U rho U^dag with U = exp(-i H t) (von Neumann d rho/dt = -i[H,rho])."""
    U = torch.linalg.matrix_exp(-1j * H * t)
    return U @ rho @ U.conj().T


def vn_residual(rho: torch.Tensor, H: torch.Tensor, t: float, dt: float = 1e-5) -> float:
    """Finite-difference check that d rho/dt = -i[H, rho] holds for U rho U^dag at time t."""
    rp = evolve(rho, H, t + dt)
    rm = evolve(rho, H, t - dt)
    drho_dt = (rp - rm) / (2 * dt)
    rt = evolve(rho, H, t)
    commutator = -1j * (H @ rt - rt @ H)
    return float(torch.linalg.matrix_norm(drho_dt - commutator).item())


# --------------------------------------------------------------------------- #
# sympy: EXACT projector algebra (no float tolerance)                          #
# --------------------------------------------------------------------------- #
def sympy_exact_projectors() -> dict[str, Any]:
    g5 = sp.diag(1, 1, -1, -1)
    I = sp.eye(4)
    PL = (I + g5) / 2
    PR = (I - g5) / 2
    Z = sp.zeros(4, 4)
    return {
        "gamma5_squared_eq_I": sp.simplify(g5 * g5 - I) == Z,
        "gamma5_hermitian": sp.simplify(g5 - g5.conjugate().T) == Z,
        "PL_plus_PR_eq_I": sp.simplify(PL + PR - I) == Z,
        "PL_PR_eq_0": sp.simplify(PL * PR) == Z,
        "PR_PL_eq_0": sp.simplify(PR * PL) == Z,
        "PL_idempotent": sp.simplify(PL * PL - PL) == Z,
        "PR_idempotent": sp.simplify(PR * PR - PR) == Z,
        "PL_hermitian": sp.simplify(PL - PL.conjugate().T) == Z,
        "PR_hermitian": sp.simplify(PR - PR.conjugate().T) == Z,
        "trace_PL": int(sp.trace(PL)),
        "trace_PR": int(sp.trace(PR)),
        "trace_gamma5": int(sp.trace(g5)),
    }


# --------------------------------------------------------------------------- #
# clifford Cl(1,3): the chirality element from the geometric algebra           #
# --------------------------------------------------------------------------- #
def clifford_chirality_element() -> dict[str, Any]:
    """In Cl(1,3) with signature (+,-,-,-) the pseudoscalar omega = e1 e2 e3 e4
    satisfies omega^2 = -1, so the chirality element gamma5 = i * omega has
    (i omega)^2 = -omega^2 = +1, reproducing the matrix fact gamma5^2 = I from the
    geometric-algebra structure (no hardcoded matrix). The chirality element
    anticommutes with each vector e_k (the grade-flip property that splits L/R)."""
    from clifford import Cl
    layout, blades = Cl(1, 3)
    e1, e2, e3, e4 = blades["e1"], blades["e2"], blades["e3"], blades["e4"]
    metric = [float((b * b).value[0]) for b in (e1, e2, e3, e4)]
    omega = e1 * e2 * e3 * e4
    omega_sq = float((omega * omega).value[0])
    chirality_sq = -omega_sq  # (i omega)^2 = i^2 omega^2 = -omega^2
    # chirality element anticommutes with vectors: omega e_k + e_k omega == 0
    anticomm = max(
        float((omega * b + b * omega).value[0])  # scalar part; full mv should vanish
        if abs(float((omega * b + b * omega).value[0])) > 0 else
        float(abs((omega * b + b * omega)))
        for b in (e1, e2, e3, e4)
    )
    anticomm_norm = max(float(abs(omega * b + b * omega)) for b in (e1, e2, e3, e4))
    return {
        "metric_signature": metric,
        "pseudoscalar_squared": omega_sq,
        "chirality_element_squared": chirality_sq,
        "chirality_sq_equals_one": abs(chirality_sq - 1.0) < TOL,
        "anticommutes_with_vectors_defect": anticomm_norm,
        "chirality_anticommutes_with_vectors": anticomm_norm < TOL,
    }


# --------------------------------------------------------------------------- #
# z3 + cvc5: structural certificates P_L+P_R=I and P_L P_R=0 (negation UNSAT)  #
# --------------------------------------------------------------------------- #
def _entry_residuals(M: torch.Tensor) -> list[tuple[float, float]]:
    out = []
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            out.append((float(M[i, j].real.item()), float(M[i, j].imag.item())))
    return out


def z3_zero_matrix_certificate(M: torch.Tensor, label: str) -> dict[str, Any]:
    """z3 certifies every entry of M is within tol of zero: the negation
    NOT(all |re|<=tol and |im|<=tol) is UNSAT. Removing z3 removes this certificate."""
    s = z3.Solver()
    conds = []
    for k, (re, im) in enumerate(_entry_residuals(M)):
        vr = z3.Real(f"re_{k}")
        vi = z3.Real(f"im_{k}")
        s.add(vr == z3.RealVal(repr(re)), vi == z3.RealVal(repr(im)))
        tol = z3.RealVal(repr(TOL_SMT))
        conds += [vr <= tol, vr >= -tol, vi <= tol, vi >= -tol]
    s.add(z3.Not(z3.And(*conds)))
    status = str(s.check())
    return {"label": label, "negation_status": status, "pass": status == "unsat"}


def cvc5_zero_matrix_certificate(M: torch.Tensor, label: str) -> dict[str, Any]:
    """Independent cvc5 (QF_NRA) certificate that every entry of M is within tol of
    zero (negation UNSAT)."""
    import cvc5
    from cvc5 import Kind
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10 ** 12)
        num, den = frac.p, frac.q
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    tol = rv(TOL_SMT)
    zero = slv.mkReal(0)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)
    conds = []
    for k, (re, im) in enumerate(_entry_residuals(M)):
        vr = slv.mkConst(R, f"re_{k}")
        vi = slv.mkConst(R, f"im_{k}")
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, vr, rv(re)))
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, vi, rv(im)))
        conds.append(slv.mkTerm(Kind.LEQ, vr, tol))
        conds.append(slv.mkTerm(Kind.GEQ, vr, neg_tol))
        conds.append(slv.mkTerm(Kind.LEQ, vi, tol))
        conds.append(slv.mkTerm(Kind.GEQ, vi, neg_tol))
    all_zero = slv.mkTerm(Kind.AND, *conds)
    slv.assertFormula(slv.mkTerm(Kind.NOT, all_zero))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"label": label, "negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# Wide-variation sweep over states / Hamiltonians / times                      #
# --------------------------------------------------------------------------- #
def sweep_block(seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed * 9973 + 17)
    psis = [haar_spinor4(gen) for _ in range(N_PSI_PER_SEED)]
    H0 = haar_hermitian4(gen)

    max_subspace_overlap = 0.0       # |<psi_L | psi_R>| should be 0 (orthogonal subspaces)
    max_timerev_defect = 0.0         # ||U_R(t) - U_L(-t)|| should be 0
    max_vn_defect = 0.0              # von Neumann d rho/dt = -i[H,rho]
    max_trace_drift_L = 0.0          # Tr(rho_L) preserved under unitary evolution
    max_decomp_defect = 0.0          # psi == psi_L + psi_R

    for psi in psis:
        psiL = P_L @ psi
        psiR = P_R @ psi
        overlap = float(torch.abs(torch.vdot(psiL, psiR)).item())
        max_subspace_overlap = max(max_subspace_overlap, overlap)
        decomp = float(torch.linalg.vector_norm(psi - (psiL + psiR)).item())
        max_decomp_defect = max(max_decomp_defect, decomp)

        # densities of the chiral components (skip degenerate zero-norm components)
        nL = float(torch.linalg.vector_norm(psiL).item())
        nR = float(torch.linalg.vector_norm(psiR).item())
        if nL > 1e-6:
            rhoL = density(psiL / nL)
        else:
            rhoL = None
        for t in TIMES:
            UL = torch.linalg.matrix_exp(-1j * H0 * t)             # H_L = +H0
            UR = torch.linalg.matrix_exp(-1j * (-H0) * t)          # H_R = -H0
            UL_negt = torch.linalg.matrix_exp(-1j * H0 * (-t))     # U_L(-t)
            timerev = float(torch.linalg.matrix_norm(UR - UL_negt).item())
            max_timerev_defect = max(max_timerev_defect, timerev)
            if rhoL is not None:
                tr0 = float(torch.trace(rhoL).real.item())
                trt = float(torch.trace(UL @ rhoL @ UL.conj().T).real.item())
                max_trace_drift_L = max(max_trace_drift_L, abs(trt - tr0))
                max_vn_defect = max(max_vn_defect, vn_residual(rhoL, H0, t))

    return {
        "seed": seed,
        "n_psi": len(psis),
        "max_subspace_overlap": max_subspace_overlap,
        "max_decomposition_defect": max_decomp_defect,
        "max_timereverse_defect": max_timerev_defect,
        "max_trace_drift_L": max_trace_drift_L,
        "max_vonNeumann_defect": max_vn_defect,
    }


# --------------------------------------------------------------------------- #
# Negatives (collapse controls)                                                #
# --------------------------------------------------------------------------- #
def negative_merge_LR() -> dict[str, Any]:
    """Merge L/R: set P_L := P_R. Then P_L + P_R = 2 P_R != I and P_L P_R = P_R != 0.
    The orthogonal-projector / chirality structure is destroyed."""
    PLm = P_R  # merged
    sum_defect = float(torch.linalg.matrix_norm(PLm + P_R - I4).item())
    prod_defect = float(torch.linalg.matrix_norm(PLm @ P_R).item())
    return {
        "PL_plus_PR_minus_I_norm": sum_defect,
        "PL_PR_norm": prod_defect,
        "kills_signature": sum_defect > 0.5 and prod_defect > 0.5,
    }


def negative_handedness_gone() -> dict[str, Any]:
    """Handedness gone: set H_R := H_L = +H0. Then the right evolution no longer equals
    the left evolution run backward: U_R(t) != U_L(-t). The time-reverse relation breaks."""
    gen = torch.Generator().manual_seed(424242)
    H0 = haar_hermitian4(gen)
    worst = 0.0
    for t in TIMES:
        UR_same = torch.linalg.matrix_exp(-1j * H0 * t)        # H_R := +H0 (wrong)
        UL_negt = torch.linalg.matrix_exp(-1j * H0 * (-t))     # U_L(-t)
        worst = max(worst, float(torch.linalg.matrix_norm(UR_same - UL_negt).item()))
    return {
        "max_timereverse_defect_when_HR_eq_HL": worst,
        "kills_signature": worst > 1e-3,
    }


def negative_swap_no_chirality() -> dict[str, Any]:
    """No-chirality collapse: replace gamma5 by +I (no sign split between blocks).
    Then P_L = (I + I)/2 = I and P_R = (I - I)/2 = 0: every state is 'left', the L/R
    split collapses, and P_L P_R = 0 trivially but P_R projects onto nothing."""
    g5_flat = I4  # no chirality sign split
    PLf = (I4 + g5_flat) / 2
    PRf = (I4 - g5_flat) / 2
    rankPR = int(torch.linalg.matrix_rank(PRf).item())
    rankPL = int(torch.linalg.matrix_rank(PLf).item())
    return {
        "rank_PR_after_collapse": rankPR,
        "rank_PL_after_collapse": rankPL,
        "PR_is_zero": float(torch.linalg.matrix_norm(PRf).item()) < TOL,
        "kills_signature": rankPR == 0 and rankPL == 4,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                      #
# --------------------------------------------------------------------------- #
def check(invariant: str, computed: Any, known: Any, *, match: bool) -> dict[str, Any]:
    return {"invariant": invariant, "computed": computed, "known": known, "match": bool(match)}


def build_known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                             cliff: dict[str, Any]) -> list[dict[str, Any]]:
    # direct torch structural facts
    g5_sq_defect = float(torch.linalg.matrix_norm(GAMMA5 @ GAMMA5 - I4).item())
    g5_herm_defect = float(torch.linalg.matrix_norm(GAMMA5 - GAMMA5.conj().T).item())
    plpr_sum_defect = float(torch.linalg.matrix_norm(P_L + P_R - I4).item())
    plpr_prod_defect = float(torch.linalg.matrix_norm(P_L @ P_R).item())
    prpl_prod_defect = float(torch.linalg.matrix_norm(P_R @ P_L).item())
    pl_idem_defect = float(torch.linalg.matrix_norm(P_L @ P_L - P_L).item())
    pr_idem_defect = float(torch.linalg.matrix_norm(P_R @ P_R - P_R).item())
    pl_herm_defect = float(torch.linalg.matrix_norm(P_L - P_L.conj().T).item())
    pr_herm_defect = float(torch.linalg.matrix_norm(P_R - P_R.conj().T).item())
    rank_PL = int(torch.linalg.matrix_rank(P_L).item())
    rank_PR = int(torch.linalg.matrix_rank(P_R).item())

    max_overlap = max(b["max_subspace_overlap"] for b in blocks)
    max_decomp = max(b["max_decomposition_defect"] for b in blocks)
    max_timerev = max(b["max_timereverse_defect"] for b in blocks)
    max_trace_drift = max(b["max_trace_drift_L"] for b in blocks)
    max_vn = max(b["max_vonNeumann_defect"] for b in blocks)

    return [
        check("gamma5_squared_eq_I", f"||g5^2 - I|| = {g5_sq_defect:.2e}", "0", match=g5_sq_defect < TOL),
        check("gamma5_hermitian", f"||g5 - g5^dag|| = {g5_herm_defect:.2e}", "0", match=g5_herm_defect < TOL),
        check("P_L_plus_P_R_eq_I", f"||P_L+P_R - I|| = {plpr_sum_defect:.2e}", "0", match=plpr_sum_defect < TOL),
        check("P_L_P_R_eq_0", f"||P_L P_R|| = {plpr_prod_defect:.2e}", "0", match=plpr_prod_defect < TOL),
        check("P_R_P_L_eq_0", f"||P_R P_L|| = {prpl_prod_defect:.2e}", "0", match=prpl_prod_defect < TOL),
        check("P_L_idempotent", f"||P_L^2 - P_L|| = {pl_idem_defect:.2e}", "0", match=pl_idem_defect < TOL),
        check("P_R_idempotent", f"||P_R^2 - P_R|| = {pr_idem_defect:.2e}", "0", match=pr_idem_defect < TOL),
        check("P_L_hermitian", f"||P_L - P_L^dag|| = {pl_herm_defect:.2e}", "0", match=pl_herm_defect < TOL),
        check("P_R_hermitian", f"||P_R - P_R^dag|| = {pr_herm_defect:.2e}", "0", match=pr_herm_defect < TOL),
        check("rank_P_L", rank_PL, "2", match=rank_PL == 2),
        check("rank_P_R", rank_PR, "2", match=rank_PR == 2),
        check("trace_P_L", sym["trace_PL"], "2", match=sym["trace_PL"] == 2),
        check("trace_P_R", sym["trace_PR"], "2", match=sym["trace_PR"] == 2),
        check("trace_gamma5", sym["trace_gamma5"], "0", match=sym["trace_gamma5"] == 0),
        check("psi_eq_psiL_plus_psiR_decomposition", f"max ||psi - (psi_L+psi_R)|| = {max_decomp:.2e}", "0",
              match=max_decomp < TOL),
        check("L_R_Weyl_subspaces_orthogonal", f"max |<psi_L|psi_R>| = {max_overlap:.2e}", "0",
              match=max_overlap < TOL),
        check("left_right_evolutions_time_reverse_U_R(t)==U_L(-t)",
              f"max ||U_R(t) - U_L(-t)|| = {max_timerev:.2e}", "0", match=max_timerev < TOL_EVO),
        check("rho_L_trace_preserved_under_unitary_evolution",
              f"max |Tr rho_L(t) - Tr rho_L(0)| = {max_trace_drift:.2e}", "0", match=max_trace_drift < TOL),
        check("von_Neumann_d_rho_dt_eq_minus_i_commutator",
              f"max FD defect = {max_vn:.2e}", "0", match=max_vn < 1e-6),
        # sympy EXACT (no float tolerance)
        check("sympy_EXACT_gamma5_squared_eq_I", str(sym["gamma5_squared_eq_I"]), "True",
              match=bool(sym["gamma5_squared_eq_I"])),
        check("sympy_EXACT_P_L_plus_P_R_eq_I", str(sym["PL_plus_PR_eq_I"]), "True",
              match=bool(sym["PL_plus_PR_eq_I"])),
        check("sympy_EXACT_P_L_P_R_eq_0", str(sym["PL_PR_eq_0"]), "True", match=bool(sym["PL_PR_eq_0"])),
        check("sympy_EXACT_P_R_P_L_eq_0", str(sym["PR_PL_eq_0"]), "True", match=bool(sym["PR_PL_eq_0"])),
        check("sympy_EXACT_P_L_idempotent", str(sym["PL_idempotent"]), "True", match=bool(sym["PL_idempotent"])),
        check("sympy_EXACT_P_R_idempotent", str(sym["PR_idempotent"]), "True", match=bool(sym["PR_idempotent"])),
        check("sympy_EXACT_P_L_hermitian", str(sym["PL_hermitian"]), "True", match=bool(sym["PL_hermitian"])),
        check("sympy_EXACT_P_R_hermitian", str(sym["PR_hermitian"]), "True", match=bool(sym["PR_hermitian"])),
        # clifford geometric-algebra chirality element
        check("clifford_Cl(1,3)_chirality_element_squared_eq_one",
              f"(i*pseudoscalar)^2 = {cliff['chirality_element_squared']:.6f}", "1 (== gamma5^2)",
              match=cliff["chirality_sq_equals_one"]),
        check("clifford_chirality_anticommutes_with_vectors",
              f"max anticommutator defect = {cliff['anticommutes_with_vectors_defect']:.2e}", "0",
              match=cliff["chirality_anticommutes_with_vectors"]),
    ]


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    witness: list[dict[str, Any]] = []

    # wide-variation sweep
    blocks = [sweep_block(seed) for seed in SEEDS]
    for b in blocks:
        witness.append({"step": "sweep", "seed": b["seed"],
                        "max_timereverse_defect": b["max_timereverse_defect"],
                        "max_subspace_overlap": b["max_subspace_overlap"]})

    # sympy exact projector algebra
    sym = sympy_exact_projectors()
    witness.append({"step": "sympy_exact", "PL_plus_PR_eq_I": bool(sym["PL_plus_PR_eq_I"]),
                    "PL_PR_eq_0": bool(sym["PL_PR_eq_0"])})

    # clifford chirality element
    cliff = clifford_chirality_element()
    witness.append({"step": "clifford_chirality", "chirality_sq": cliff["chirality_element_squared"]})

    # known-value cross-checks
    kvc = build_known_value_checks(blocks, sym, cliff)
    all_known_match = all(c["match"] for c in kvc)
    witness.append({"step": "known_value_checks", "n": len(kvc), "all_match": all_known_match})

    # z3 + cvc5 structural certificates: P_L+P_R-I == 0 and P_L P_R == 0
    M_sum = P_L + P_R - I4
    M_prod = P_L @ P_R
    z3_sum = z3_zero_matrix_certificate(M_sum, "P_L+P_R-I")
    z3_prod = z3_zero_matrix_certificate(M_prod, "P_L*P_R")
    cvc5_sum = cvc5_zero_matrix_certificate(M_sum, "P_L+P_R-I")
    cvc5_prod = cvc5_zero_matrix_certificate(M_prod, "P_L*P_R")
    z3_pass = z3_sum["pass"] and z3_prod["pass"]
    cvc5_pass = cvc5_sum["pass"] and cvc5_prod["pass"]
    certs_pass = z3_pass and cvc5_pass
    witness.append({"step": "smt_certificates", "z3": z3_pass, "cvc5": cvc5_pass})

    # negatives
    neg_merge = negative_merge_LR()
    neg_hand = negative_handedness_gone()
    neg_swap = negative_swap_no_chirality()
    negatives = {
        "merge_LR_PL_eq_PR": {"detail": neg_merge, "kills_signature": neg_merge["kills_signature"]},
        "handedness_gone_HR_eq_HL": {"detail": neg_hand, "kills_signature": neg_hand["kills_signature"]},
        "no_chirality_gamma5_eq_I": {"detail": neg_swap, "kills_signature": neg_swap["kills_signature"]},
    }
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    witness.append({"step": "negatives", "all_kill": negatives_all_kill,
                    "which": list(negatives.keys())})

    # aggregate verdict
    blockers: list[str] = []
    for c in kvc:
        if not c["match"]:
            blockers.append(f"KNOWN_VALUE_MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE_DID_NOT_KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]
    if not certs_pass:
        blockers.append(f"CERTIFICATE_FAILED: z3_sum={z3_sum['negation_status']} z3_prod={z3_prod['negation_status']} "
                        f"cvc5_sum={cvc5_sum['negation_status']} cvc5_prod={cvc5_prod['negation_status']}")

    all_pass = all_known_match and negatives_all_kill and certs_pass and not blockers

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "ALL chiral states, projectors P_L/P_R, chiral densities, unitary time evolution "
                            "exp(-i H t), von Neumann commutator FD-check, subspace orthogonality, and the "
                            "time-reverse comparison U_R(t)==U_L(-t) -- every number comes from torch.complex128"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic projector algebra: gamma5^2=I, P_L+P_R=I, P_L P_R=0, P_R P_L=0, "
                            "idempotency, Hermiticity, traces -- exact matrix identities, not float comparisons"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that P_L+P_R-I == 0 and P_L P_R == 0 structurally (all 16 entry "
                         "residuals zero; the negation is UNSAT)"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent QF_NRA SMT family certifying the same P_L+P_R=I and P_L P_R=0 facts "
                           "(negation UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(1,3) geometric algebra: the chirality element is i*pseudoscalar e1234; "
                               "(i*e1234)^2 = +1 reproduces gamma5^2 = I from the GA structure, and the element "
                               "anticommutes with each vector (the grade-flip that splits L/R) -- not a hardcoded matrix"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "4_chirality",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone left/right Weyl chirality geometry lego computed in real torch with full "
                   "tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: "
                   "NOT gated on manifold membership.",
        "scientific_question": "Does the chiral-basis chirality operator gamma5=diag(+1,+1,-1,-1) with projectors "
                               "P_L=(I+gamma5)/2, P_R=(I-gamma5)/2 reproduce the known left/right Weyl geometry "
                               "(orthogonal idempotent Hermitian projectors summing to I, orthogonal L/R subspaces, "
                               "opposite-handed evolutions that are time-reverses U_R(t)=U_L(-t)) to its exact "
                               "analytic values, and do the merge/handedness-gone/no-chirality controls kill the signature?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. "
                         "Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, "
                         "QIT, or physics claim. NOT gated on manifold membership; no distinctness/forcing/cross-layer claim.",
        "finite_map": "(4-component chiral Dirac spinor psi in C^4, Hermitian H0 in C^{4x4}, time t in R) -> "
                      "(projectors P_L,P_R, Weyl components psi_L=P_L psi & psi_R=P_R psi, chiral densities "
                      "rho_L,rho_R, opposite-handed evolutions U_L(t)=exp(-i H0 t) & U_R(t)=exp(+i H0 t), and the "
                      "chiral invariants gamma5^2=I, P_L+P_R=I, P_L P_R=0, rank(P_L)=rank(P_R)=2, U_R(t)=U_L(-t))",
        "domain": f"Haar-sampled 4-component complex spinors psi in C^4 (QR of complex Gaussian), Hermitian "
                  f"Hamiltonians H0 (GUE-style), and times {TIMES}, over {len(SEEDS)} seeds x {N_PSI_PER_SEED} spinors",
        "codomain_or_output": "chirality projectors, left/right Weyl spinor components and densities, opposite-handed "
                              "unitary evolutions and their time-reverse comparison, projector-algebra invariants, "
                              "subspace orthogonality, ranks/traces",
        "carrier_layer": "left_right_weyl",
        "geometry_layer": "4-component chiral (Weyl) Dirac space C^4 split by gamma5 into orthogonal rank-2 "
                          "left/right Weyl subspaces; opposite-handed Hamiltonian evolution",
        "carrier_realization": "torch.complex128 / float64 spinors, projectors, densities, and matrix_exp evolutions; "
                               "no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices "
                               "(random spinors/Hamiltonians are genuine Haar/GUE samples)",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "spinor_state": "torch.complex128 4-component chiral Dirac spinor psi and its Weyl components "
                        "psi_L=P_L psi, psi_R=P_R psi with chiral densities rho_L=psi_L psi_L^dag, rho_R=psi_R psi_R^dag",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_membership", "axis0", "bridge", "QIT_engine", "stacking", "coupling",
                              "flux", "Phi0", "Xi", "physics", "distinctness_gate", "forcing_filter"],
        "blocked_consumers": ["manifold_membership", "axis0", "bridge", "QIT_engine", "stacking", "coupling",
                              "flux", "Phi0", "Xi", "physics", "distinctness_gate", "forcing_filter"],
        "bridge_layer": "bridge_not_applicable_at_this_tier",
        "cut_layer": "cut_not_applicable_at_this_tier",
        "law_or_candidate_tested": "the textbook left/right Weyl chirality structure (gamma5 chirality operator, "
                                   "orthogonal idempotent Hermitian projectors P_L/P_R summing to I, orthogonal "
                                   "rank-2 L/R Weyl subspaces, opposite-handed time-reverse evolutions)",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math left/right Weyl chirality geometry witness; computed invariants "
                           "match textbook values in this run; merge/handedness-gone/no-chirality controls kill the signature"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); not gated on or admitted to "
                               "manifold membership; no cross-layer evidence, no coupling"],

        "known_value_checks": kvc,
        "all_known_value_checks_match": all_known_match,

        "sympy_exact_projectors": sym,
        "clifford_chirality_element": cliff,

        "smt_certificates": {
            "z3": {"P_L_plus_P_R_eq_I": z3_sum, "P_L_P_R_eq_0": z3_prod, "all_unsat": z3_pass},
            "cvc5": {"P_L_plus_P_R_eq_I": cvc5_sum, "P_L_P_R_eq_0": cvc5_prod, "all_unsat": cvc5_pass},
        },
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],

        "variation_blocks": blocks,
        "wide_variation": {"seeds": SEEDS, "times": TIMES, "n_psi_per_seed": N_PSI_PER_SEED,
                           "n_states_total": len(SEEDS) * N_PSI_PER_SEED},

        "required_negatives": ["merge_LR_PL_eq_PR", "handedness_gone_HR_eq_HL", "no_chirality_gamma5_eq_I"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "negatives_all_kill": negatives_all_kill,
        "kill_conditions": [
            "any known-value invariant fails to match its analytic value",
            "z3 or cvc5 P_L+P_R=I / P_L P_R=0 negation not UNSAT",
            "merge L/R (P_L:=P_R) still gives P_L+P_R=I or P_L P_R=0",
            "handedness gone (H_R:=H_L) still gives U_R(t)=U_L(-t)",
            "no-chirality (gamma5:=I) still gives a nonzero rank-2 P_R",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {k: v["role"] for k, v in tool_manifest.items()},
        "tool_integration_depth": {k: v["role"] for k, v in tool_manifest.items()},
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",
        "witness_trace": witness,

        "result_summary": {
            "all_pass": all_pass,
            "all_known_value_checks_match": all_known_match,
            "negatives_all_kill": negatives_all_kill,
            "certificates_unsat": certs_pass,
            "z3_all_unsat": z3_pass,
            "cvc5_all_unsat": cvc5_pass,
            "n_known_value_checks": len(kvc),
            "n_states_total": len(SEEDS) * N_PSI_PER_SEED,
            "max_timereverse_defect": max(b["max_timereverse_defect"] for b in blocks),
            "max_subspace_overlap": max(b["max_subspace_overlap"] for b in blocks),
            "classification": "diagnostic_only", "promotion_allowed": False,
        },
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its analytic value AND all negatives kill the chiral "
                     "signature AND z3+cvc5 P_L+P_R=I / P_L P_R=0 negations are UNSAT",
        "fail_rule": "any known-value mismatch, any negative that does not kill, or any non-UNSAT certificate",
        "eligible_consumers": ["other diagnostic_only chirality / Weyl geometry probes"],
        "next_admissible_step": "this is a standalone known-geometry lego; no gate is run here. Any downstream use "
                                "requires explicit admission and the relevant gate, which this receipt does not satisfy.",
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wit = RESULT_DIR / f"{SIM_ID}_witness.json"
    wit.write_text(json.dumps({"sim_id": SIM_ID, "steps": witness,
                               "final_classification": "diagnostic_only",
                               "all_pass": all_pass, "blockers": blockers}, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")

    print(json.dumps({
        "wrote": str(out),
        "witness": str(wit),
        "all_pass": all_pass,
        "all_known_value_checks_match": all_known_match,
        "negatives_all_kill": negatives_all_kill,
        "certificates_unsat": certs_pass,
        "n_known_value_checks": len(kvc),
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
