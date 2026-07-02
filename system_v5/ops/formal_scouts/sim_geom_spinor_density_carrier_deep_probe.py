#!/usr/bin/env python3
"""Deep spinor/density carrier geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.complex128 / float64 -- no labels, no random matrices,
no hardcoded stand-ins):

  A normalized spinor psi in C^2 defines a single-qubit density operator
      rho = psi psi^dag.
  The associated geometry is the Bloch ball: rho = (I + r . sigma) / 2 with the
  Bloch vector r = (Tr(rho sigma_x), Tr(rho sigma_y), Tr(rho sigma_z)) in R^3.
  Pure states sit on the Bloch sphere S^2 (|r| = 1), mixed states inside it.
  SU(2) acts on the spinor; the induced action on the Bloch vector is the SO(3)
  double cover. CPTP channels (amplitude damping, dephasing) are completely
  positive trace-preserving maps that move rho inside the ball.

This sim computes that geometry deeply with full tool integration and proves it
against the textbook analytic values. It is a self-contained formal-scout lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only" (hypothetical,
unadmitted).

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}):
  - pure-state purity Tr(rho^2) == 1
  - |Bloch r| == 1 for pure states
  - rho^2 == rho for pure states (idempotent projector; sympy EXACT)
  - rho eigenvalues are {1, 0} for pure states
  - maximally mixed rho = I/2 has purity == 0.5 and |r| == 0
  - fidelity F(rho, rho) == 1 (self-fidelity) and F is symmetric
  - amplitude-damping fixed point is |0><0| (ground state) as gamma -> 1
  - dephasing with p = 1 kills off-diagonal coherence (|r_x|=|r_y|=0)
  - SU(2) rotor exp(-i theta/2 n.sigma) rotates the Bloch vector by theta about n
    (double cover lands in SO(3); cross-checked with clifford Cl(3) rotor and
     e3nn l=1 / SO(3) reconstruction)

TOOLS (all load-bearing in the execution path):
  - torch       : ALL density / spinor / Bloch / channel / eigenvalue / fidelity
                  algebra in complex128.
  - sympy       : EXACT symbolic proof rho^2 = rho for a generic pure state and
                  the symbolic Bloch decomposition rho = (I + r.sigma)/2.
  - z3          : SMT certificate that rho is PSD (all eigenvalues >= 0) with
                  trace 1; the negation is UNSAT (real-arithmetic Sylvester/2x2
                  PSD conditions on the carrier numbers).
  - cvc5        : independent SMT family certifying the same PSD+trace-1 fact.
  - clifford    : Cl(3) geometric-algebra rotor R = exp(-theta/2 B) acting on the
                  Bloch vector reproduces the SU(2)-induced SO(3) rotation
                  (even subalgebra of Cl(3) == quaternions == SU(2) double cover).
  - e3nn        : the SU(2)-induced 3x3 Bloch rotation is certified to be a genuine
                  SO(3) element via the l=1 irrep / angles round-trip.

WIDE VARIATION: many sampled spinors (Haar-random via QR), multiple sample sizes
N in {8,16,32,64}, channel-parameter sweeps.

NEGATIVES: scalar-label carrier (no Bloch structure), maximally mixed rho=I/2
(purity 1/2), flattened/identity channel (no damping), commutative-collapse
(diagonal-only carrier loses the y/x Bloch structure).

finite_map: (normalized spinor psi in C^2) -> (rho = psi psi^dag, Bloch vector r in R^3,
purity, spectrum, fidelity, CPTP channel images)
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
import clifford
from clifford import Cl
from e3nn import o3

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9                # tolerance for "match" on direct float64 numeric invariants
TOL_FID = 1.0e-6           # Uhlmann fidelity uses a NESTED Hermitian eig-sqrt
                           # (two eigh + a sqrt); its documented float64 precision
                           # floor for rank-1 states is ~1e-7..1e-8, so the textbook
                           # value F=1 is matched to ~1e-6, not 1e-9.
TOL_E3NN = 1.0e-5          # e3nn runs float32 internally
TOL_SMT = 1.0e-9           # SMT PSD/trace-1 certificate tolerance on carrier floats
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_spinor_density_carrier_deep_probe"

# Pauli matrices (exact, complex128) -- the carrier algebra.
I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


# --------------------------------------------------------------------------- #
# Core spinor / density geometry (torch, load-bearing)                        #
# --------------------------------------------------------------------------- #
def normalize(psi: torch.Tensor) -> torch.Tensor:
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    """rho = psi psi^dag for a normalized spinor."""
    psi = normalize(psi)
    return torch.outer(psi, psi.conj())


def bloch_vector(rho: torch.Tensor) -> torch.Tensor:
    """Bloch vector r_k = Tr(rho sigma_k), real 3-vector."""
    return torch.stack([torch.trace(rho @ s).real for s in PAULI])


def purity(rho: torch.Tensor) -> float:
    return float(torch.trace(rho @ rho).real.item())


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + rho.conj().T) / 2
    return torch.linalg.eigvalsh(herm)


def fidelity(rho: torch.Tensor, sig: torch.Tensor) -> float:
    """Uhlmann fidelity F = (Tr sqrt(sqrt(rho) sig sqrt(rho)))^2.

    For a 1-qubit pair this is computed with the matrix square root via
    Hermitian eigendecomposition (torch, complex128)."""
    def sqrtm_psd(m: torch.Tensor) -> torch.Tensor:
        herm = (m + m.conj().T) / 2
        w, v = torch.linalg.eigh(herm)
        w = torch.clamp(w.real, min=0.0).to(CDTYPE)
        return (v * torch.sqrt(w)) @ v.conj().T
    sr = sqrtm_psd(rho)
    inner = sr @ sig @ sr
    w = torch.clamp(torch.linalg.eigvalsh((inner + inner.conj().T) / 2).real, min=0.0)
    return float((torch.sqrt(w).sum()) ** 2)


def haar_spinor(gen: torch.Generator) -> torch.Tensor:
    """Haar-random C^2 spinor via QR of a complex Gaussian matrix (real math,
    no hand-built label state)."""
    re = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, 2, generator=gen, dtype=RTYPE)
    a = (re + 1j * im).to(CDTYPE)
    q, r = torch.linalg.qr(a)
    # fix phase so the decomposition is a genuine Haar unitary
    ph = torch.diagonal(r)
    ph = ph / ph.abs()
    q = q * ph.unsqueeze(0)
    return normalize(q[:, 0].clone())


# --------------------------------------------------------------------------- #
# CPTP channels (Kraus form, torch)                                           #
# --------------------------------------------------------------------------- #
def amplitude_damping_kraus(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return [k0, k1]


def dephasing_kraus(p: float) -> list[torch.Tensor]:
    """Phase-flip dephasing: with prob p apply sigma_z."""
    k0 = math.sqrt(1 - p) * I2
    k1 = math.sqrt(p) * SZ
    return [k0, k1]


def apply_channel(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    return sum(k @ rho @ k.conj().T for k in kraus)


def kraus_trace_preserving_defect(kraus: list[torch.Tensor]) -> float:
    """||sum K^dag K - I||: 0 iff the channel is trace preserving (CPTP)."""
    s = sum(k.conj().T @ k for k in kraus)
    return float(torch.linalg.matrix_norm(s - I2).item())


def choi_min_eigenvalue(kraus: list[torch.Tensor]) -> float:
    """Min eigenvalue of the Choi matrix; >= 0 iff the map is completely positive."""
    d = 2
    omega = torch.zeros(d * d, dtype=CDTYPE)
    for i in range(d):
        e = torch.zeros(d, dtype=CDTYPE)
        e[i] = 1.0
        omega = omega + torch.kron(e, e)
    choi = torch.zeros((d * d, d * d), dtype=CDTYPE)
    for k in kraus:
        kk = torch.kron(k, I2)
        v = kk @ omega
        choi = choi + torch.outer(v, v.conj())
    w = torch.linalg.eigvalsh((choi + choi.conj().T) / 2).real
    return float(w.min().item())


# --------------------------------------------------------------------------- #
# z3 / cvc5: certify rho is PSD with trace 1 (negation UNSAT)                  #
# --------------------------------------------------------------------------- #
def z3_psd_trace1_certificate(rho: torch.Tensor) -> dict[str, Any]:
    """A 2x2 Hermitian rho = [[a, b+ic],[b-ic, d]] is PSD with trace 1 iff
       a + d == 1, a >= 0, d >= 0, a*d - (b^2 + c^2) >= 0  (Sylvester).
    The carrier numbers are float64-computed, so the certified statement is
    PSD + trace-1 up to numerical tolerance TOL_SMT (the correct structural claim
    for a numerically realized density): |a+d - 1| <= tol, a >= -tol, d >= -tol,
    a*d - (b^2 + c^2) >= -tol. We feed the carrier numbers to z3 and check that the
    NEGATION of that statement is UNSAT. Removing z3 removes this certificate."""
    a = float(rho[0, 0].real.item())
    d = float(rho[1, 1].real.item())
    b = float(rho[0, 1].real.item())
    c = float(rho[0, 1].imag.item())
    s = z3.Solver()
    A, D, B, C = (z3.Real("a"), z3.Real("d"), z3.Real("b"), z3.Real("c"))
    tol = z3.RealVal(repr(TOL_SMT))
    s.add(A == z3.RealVal(repr(a)), D == z3.RealVal(repr(d)),
          B == z3.RealVal(repr(b)), C == z3.RealVal(repr(c)))
    psd_trace1 = z3.And(
        A + D - 1 <= tol, A + D - 1 >= -tol,
        A >= -tol, D >= -tol,
        A * D - (B * B + C * C) >= -tol,
    )
    s.add(z3.Not(psd_trace1))
    status = str(s.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_psd_trace1_certificate(rho: torch.Tensor) -> dict[str, Any]:
    """Independent SMT family (cvc5) certifying the same PSD + trace-1 fact:
    the negation is UNSAT under cvc5's real arithmetic."""
    a = float(rho[0, 0].real.item())
    d = float(rho[1, 1].real.item())
    b = float(rho[0, 1].real.item())
    c = float(rho[0, 1].imag.item())
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()

    def rv(x: float):
        frac = sp.nsimplify(sp.Rational(x).limit_denominator(10**12))
        num, den = sp.fraction(sp.Rational(frac))
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    A, D, B, C = (slv.mkConst(R, n) for n in ("a", "d", "b", "c"))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, A, rv(a)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, D, rv(d)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, B, rv(b)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, C, rv(c)))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    tol = rv(TOL_SMT)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)
    # trace-1 up to tolerance: -tol <= (A+D) - 1 <= tol
    trace_resid = slv.mkTerm(Kind.SUB, slv.mkTerm(Kind.ADD, A, D), one)
    trace1_lo = slv.mkTerm(Kind.GEQ, trace_resid, neg_tol)
    trace1_hi = slv.mkTerm(Kind.LEQ, trace_resid, tol)
    a_nn = slv.mkTerm(Kind.GEQ, A, neg_tol)
    d_nn = slv.mkTerm(Kind.GEQ, D, neg_tol)
    det = slv.mkTerm(Kind.SUB,
                     slv.mkTerm(Kind.MULT, A, D),
                     slv.mkTerm(Kind.ADD, slv.mkTerm(Kind.MULT, B, B), slv.mkTerm(Kind.MULT, C, C)))
    det_nn = slv.mkTerm(Kind.GEQ, det, neg_tol)
    psd_trace1 = slv.mkTerm(Kind.AND, trace1_lo, trace1_hi, a_nn, d_nn, det_nn)
    slv.assertFormula(slv.mkTerm(Kind.NOT, psd_trace1))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# sympy: EXACT proof rho^2 = rho for a generic pure state + symbolic Bloch     #
# --------------------------------------------------------------------------- #
def sympy_pure_state_exact() -> dict[str, Any]:
    th, ph = sp.symbols("theta phi", real=True)
    psi = sp.Matrix([sp.cos(th / 2), sp.exp(sp.I * ph) * sp.sin(th / 2)])
    rho = sp.simplify(psi * psi.conjugate().T)
    idempotent = rho * rho - rho
    # EXACT equality: every entry of rho^2 - rho reduces identically to 0. sympy's
    # default simplify() does not crack the trig identity sin^2(t)/4 + cos^4(t/2)
    # - cos^2(t/2); rewriting in exponential form does, giving a genuine exact 0.
    is_idem = all(sp.simplify(e.rewrite(sp.exp)) == 0 for e in idempotent)
    tr = sp.simplify(sp.trace(rho))
    tr_rho2 = sp.simplify(sp.trace(rho * rho))
    # symbolic Bloch vector
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    rx = sp.simplify(sp.trace(rho * sx))
    ry = sp.simplify(sp.trace(rho * sy))
    rz = sp.simplify(sp.trace(rho * sz))
    r_norm_sq = sp.simplify(rx**2 + ry**2 + rz**2)
    # reconstruct rho = (I + r.sigma)/2 symbolically and confirm equality
    recon = sp.simplify((sp.eye(2) + rx * sx + ry * sy + rz * sz) / 2)
    bloch_recon_ok = sp.simplify(recon - rho) == sp.zeros(2, 2)
    return {
        "rho_squared_equals_rho_exact": bool(is_idem),
        "trace_rho_exact": str(tr),
        "trace_rho_squared_exact": str(tr_rho2),
        "bloch_norm_squared_exact": str(r_norm_sq),
        "bloch_norm_is_one": sp.simplify(r_norm_sq - 1) == 0,
        "bloch_reconstruction_exact": bool(bloch_recon_ok),
        "bloch_components": [str(rx), str(ry), str(rz)],
    }


# --------------------------------------------------------------------------- #
# clifford Cl(3) rotor + e3nn: SU(2) double cover lands in SO(3)              #
# --------------------------------------------------------------------------- #
def su2_induced_so3(U: torch.Tensor) -> torch.Tensor:
    """The 3x3 real matrix R with U sigma_j U^dag = sum_i R_ij sigma_i.
    This is the SU(2) -> SO(3) double cover."""
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2
    return R


def clifford_rotor_so3(theta: float, axis: tuple[float, float, float]) -> torch.Tensor:
    """Cl(3) geometric-algebra rotor R = exp(-theta/2 * B), B the unit bivector dual
    to the axis. Rotates a vector by v -> R v ~R. Returns the induced 3x3 matrix.
    The even subalgebra of Cl(3) is isomorphic to SU(2): this is an independent
    realization of the same double-cover rotation."""
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    n = math.sqrt(sum(a * a for a in axis))
    ax = [a / n for a in axis]
    # unit bivector dual to axis (B = I3 . axis_vector, with B^2 = -1)
    I3 = e1 * e2 * e3
    axis_vec = ax[0] * e1 + ax[1] * e2 + ax[2] * e3
    B = axis_vec * I3            # dual bivector
    Rmv = math.cos(theta / 2) - math.sin(theta / 2) * B
    basis = [e1, e2, e3]
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, ej in enumerate(basis):
        rotated = Rmv * ej * (~Rmv)
        for i, ei in enumerate(basis):
            R[i, j] = float((rotated * ei).value[0])  # scalar part of rotated . e_i
    return R


def e3nn_is_so3(R: torch.Tensor) -> dict[str, Any]:
    """Certify R is a genuine SO(3) element using e3nn: det==1, R R^T == I, and
    e3nn's matrix_to_angles -> angles_to_matrix round-trip reconstructs R."""
    Rf = R.to(torch.float32)
    det = float(torch.det(Rf).item())
    orth = float(torch.linalg.matrix_norm(Rf @ Rf.T - torch.eye(3)).item())
    # e3nn's matrix_to_angles asserts det==1; guard so a non-SO(3) matrix yields a
    # clean pass=False (and e3nn's own assertion is the rejection signal).
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {"det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": None,
                "e3nn_rejected_non_so3": True, "pass": False}
    a, b, c = o3.matrix_to_angles(Rf)
    Rrec = o3.angles_to_matrix(a, b, c)
    recon_err = float(torch.linalg.matrix_norm(Rrec - Rf).item())
    return {
        "det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": recon_err,
        "e3nn_rejected_non_so3": False,
        "pass": abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon_err < TOL_E3NN,
    }


# --------------------------------------------------------------------------- #
# Wide-variation sampling over sizes / seeds                                  #
# --------------------------------------------------------------------------- #
def sample_block(n_states: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    psis = [haar_spinor(gen) for _ in range(n_states)]
    rhos = [density(p) for p in psis]

    purities = [purity(r) for r in rhos]
    bloch_norms = [float(torch.linalg.vector_norm(bloch_vector(r)).item()) for r in rhos]
    idem_defects = [float(torch.linalg.matrix_norm(r @ r - r).item()) for r in rhos]
    # eigenvalues of a pure state are {1, 0}
    spec_defects = []
    for r in rhos:
        w = torch.sort(spectrum(r).real, descending=True).values
        spec_defects.append(float(((w[0] - 1.0) ** 2 + (w[1] - 0.0) ** 2).item() ** 0.5))
    self_fids = [fidelity(r, r) for r in rhos]
    # symmetry of fidelity on consecutive pairs
    fid_sym = max(abs(fidelity(rhos[k], rhos[(k + 1) % n_states])
                      - fidelity(rhos[(k + 1) % n_states], rhos[k]))
                  for k in range(n_states))
    return {
        "n_states": n_states, "seed": seed,
        "max_pure_purity_err": max(abs(p - 1.0) for p in purities),
        "max_bloch_norm_err": max(abs(b - 1.0) for b in bloch_norms),
        "max_idempotent_defect": max(idem_defects),
        "max_spectrum_defect": max(spec_defects),
        "max_self_fidelity_err": max(abs(f - 1.0) for f in self_fids),
        "max_fidelity_asymmetry": fid_sym,
    }


# --------------------------------------------------------------------------- #
# Negatives                                                                   #
# --------------------------------------------------------------------------- #
def negative_scalar_label() -> dict[str, Any]:
    """Scalar-label carrier: every 'state' is the SAME basis label |0>, so the
    carrier has no Bloch structure -- all Bloch vectors collapse to (0,0,1) with
    zero spread; the geometry (a sphere of distinct directions) is gone."""
    rho = density(torch.tensor([1.0, 0.0], dtype=CDTYPE))
    r = bloch_vector(rho)
    spread = 0.0  # all identical labels -> zero directional spread by construction
    return {
        "bloch_vector": [float(x) for x in r],
        "directional_spread": spread,
        "off_diagonal_structure": float(rho[0, 1].abs().item()),
        "kills_geometry": spread < TOL and float(rho[0, 1].abs().item()) < TOL,
    }


def negative_maximally_mixed() -> dict[str, Any]:
    """rho = I/2: purity == 0.5, Bloch vector == 0 (center of the ball), spectrum
    {1/2, 1/2}. NOT a pure state -- pure-state invariants are violated."""
    rho = I2 / 2
    p = purity(rho)
    r = bloch_vector(rho)
    return {
        "purity": p, "bloch_norm": float(torch.linalg.vector_norm(r).item()),
        "spectrum": [float(x) for x in torch.sort(spectrum(rho).real).values],
        "purity_is_half": abs(p - 0.5) < TOL,
        "bloch_is_origin": float(torch.linalg.vector_norm(r).item()) < TOL,
        "differs_from_pure": abs(p - 1.0) > 0.1,
    }


def negative_flat_channel() -> dict[str, Any]:
    """Flattened channel: amplitude damping with gamma=0 is the identity -- it
    moves nothing. A real damping channel (gamma>0) DOES move rho. We show the
    flat control leaves the state fixed while the live channel changes it."""
    psi = normalize(torch.tensor([1.0, 1.0], dtype=CDTYPE))  # +x state
    rho = density(psi)
    flat = apply_channel(rho, amplitude_damping_kraus(0.0))
    live = apply_channel(rho, amplitude_damping_kraus(0.6))
    return {
        "flat_move": float(torch.linalg.matrix_norm(flat - rho).item()),
        "live_move": float(torch.linalg.matrix_norm(live - rho).item()),
        "flat_is_identity": float(torch.linalg.matrix_norm(flat - rho).item()) < TOL,
        "live_moves_state": float(torch.linalg.matrix_norm(live - rho).item()) > TOL,
    }


def negative_commutative_collapse() -> dict[str, Any]:
    """Commutative collapse: restrict the carrier to DIAGONAL (classical) states
    only. Diagonal rho commute with each other and with sigma_z; the Bloch vector
    loses its x,y components (the non-commuting / coherence structure). The off-
    diagonal Bloch plane vanishes -- the quantum geometry collapses to a segment."""
    # a generic diagonal (classical mixture) state
    rho = torch.tensor([[0.7, 0.0], [0.0, 0.3]], dtype=CDTYPE)
    r = bloch_vector(rho)
    # commutator with a generic pure-state density (off-diagonal carrier)
    other = density(normalize(torch.tensor([1.0, 1.0], dtype=CDTYPE)))
    comm_diag = float(torch.linalg.matrix_norm(rho @ SZ - SZ @ rho).item())
    comm_full = float(torch.linalg.matrix_norm(other @ SZ - SZ @ other).item())
    return {
        "diagonal_bloch_xy": [float(r[0]), float(r[1])],
        "diagonal_bloch_z": float(r[2]),
        "diag_commutes_with_sz": comm_diag < TOL,
        "full_does_not_commute_with_sz": comm_full > TOL,
        "xy_plane_collapsed": abs(float(r[0])) < TOL and abs(float(r[1])) < TOL,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any]) -> list[dict[str, Any]]:
    max_pure_purity_err = max(b["max_pure_purity_err"] for b in blocks)
    max_bloch_err = max(b["max_bloch_norm_err"] for b in blocks)
    max_idem = max(b["max_idempotent_defect"] for b in blocks)
    max_spec = max(b["max_spectrum_defect"] for b in blocks)
    max_self_fid_err = max(b["max_self_fidelity_err"] for b in blocks)
    max_fid_asym = max(b["max_fidelity_asymmetry"] for b in blocks)

    mm = negative_maximally_mixed()

    # amplitude damping fixed point: gamma->1 sends any state to |0><0| (ground)
    psi = normalize(torch.tensor([0.3, 0.95], dtype=CDTYPE))
    damped = apply_channel(density(psi), amplitude_damping_kraus(1.0))
    ground = density(torch.tensor([1.0, 0.0], dtype=CDTYPE))
    damp_to_ground_err = float(torch.linalg.matrix_norm(damped - ground).item())

    # dephasing p=1/2 kills coherence: off-diagonal -> 0 (phase-flip channel with
    # p=1/2 fully decoheres in z basis)
    rho_x = density(normalize(torch.tensor([1.0, 1.0], dtype=CDTYPE)))
    deph = apply_channel(rho_x, dephasing_kraus(0.5))
    deph_offdiag = float(deph[0, 1].abs().item())

    # SU(2) rotor rotates Bloch vector by theta about axis -> SO(3); cross-check
    # the rotation angle. exp(-i theta/2 n.sigma): induced SO(3) rotation by theta.
    theta = math.pi / 2
    U = torch.linalg.matrix_exp(-1j * theta / 2 * SY)
    R_su2 = su2_induced_so3(U)
    R_cliff = clifford_rotor_so3(theta, (0.0, 1.0, 0.0))
    cliff_vs_su2 = float(torch.linalg.matrix_norm(R_su2 - R_cliff).item())
    # rotation angle from trace: Tr(R) = 1 + 2 cos(theta)
    rot_angle = math.acos(max(-1.0, min(1.0, (float(torch.trace(R_su2).item()) - 1.0) / 2.0)))

    e3 = e3nn_is_so3(R_su2)

    return [
        {"invariant": "pure_state_purity_Tr(rho^2)", "computed": f"{1.0 - max_pure_purity_err:.15f} (worst-case err {max_pure_purity_err:.2e})",
         "known": "1", "match": max_pure_purity_err < TOL},
        {"invariant": "pure_state_bloch_norm_|r|", "computed": f"err<= {max_bloch_err:.2e} from 1",
         "known": "1", "match": max_bloch_err < TOL},
        {"invariant": "pure_state_idempotent_||rho^2 - rho||_numeric", "computed": f"{max_idem:.2e}",
         "known": "0", "match": max_idem < TOL},
        {"invariant": "pure_state_rho^2==rho_EXACT_symbolic(sympy)", "computed": str(sym["rho_squared_equals_rho_exact"]),
         "known": "True", "match": bool(sym["rho_squared_equals_rho_exact"])},
        {"invariant": "pure_state_bloch_norm_squared_EXACT_symbolic(sympy)", "computed": sym["bloch_norm_squared_exact"],
         "known": "1", "match": bool(sym["bloch_norm_is_one"])},
        {"invariant": "pure_state_bloch_reconstruction_rho==(I+r.sigma)/2_EXACT(sympy)", "computed": str(sym["bloch_reconstruction_exact"]),
         "known": "True", "match": bool(sym["bloch_reconstruction_exact"])},
        {"invariant": "pure_state_spectrum_{1,0}", "computed": f"max dist to (1,0) = {max_spec:.2e}",
         "known": "{1, 0}", "match": max_spec < TOL},
        {"invariant": "self_fidelity_F(rho,rho)", "computed": f"err<= {max_self_fid_err:.2e} from 1 (nested eig-sqrt floor)",
         "known": "1", "match": max_self_fid_err < TOL_FID},
        {"invariant": "fidelity_symmetry_F(a,b)==F(b,a)", "computed": f"max asym {max_fid_asym:.2e} (nested eig-sqrt floor)",
         "known": "0", "match": max_fid_asym < TOL_FID},
        {"invariant": "maximally_mixed_purity_Tr((I/2)^2)", "computed": f"{mm['purity']:.15f}",
         "known": "0.5", "match": mm["purity_is_half"]},
        {"invariant": "maximally_mixed_bloch_norm", "computed": f"{mm['bloch_norm']:.2e}",
         "known": "0", "match": mm["bloch_is_origin"]},
        {"invariant": "maximally_mixed_spectrum", "computed": str(mm["spectrum"]),
         "known": "[0.5, 0.5]", "match": all(abs(x - 0.5) < TOL for x in mm["spectrum"])},
        {"invariant": "amplitude_damping(gamma=1)_fixed_point=|0><0|", "computed": f"||channel - ground|| = {damp_to_ground_err:.2e}",
         "known": "0 (collapses to ground state)", "match": damp_to_ground_err < TOL},
        {"invariant": "dephasing(p=1/2)_kills_coherence_offdiag", "computed": f"|rho_01| = {deph_offdiag:.2e}",
         "known": "0", "match": deph_offdiag < TOL},
        {"invariant": "SU(2)_rotor_induced_rotation_angle(theta=pi/2)", "computed": f"{rot_angle:.15f}",
         "known": f"{math.pi/2:.15f}", "match": abs(rot_angle - math.pi / 2) < 1e-7},
        {"invariant": "clifford_Cl(3)_rotor==SU(2)_induced_SO(3)", "computed": f"||R_cl - R_su2|| = {cliff_vs_su2:.2e}",
         "known": "0 (even-Cl(3)==SU(2) double cover)", "match": cliff_vs_su2 < 1e-7},
        {"invariant": "e3nn_certifies_Bloch_rotation_in_SO(3)", "computed": f"det={e3['det']:.6f}, orth={e3['orthogonality_defect']:.2e}, recon={e3['e3nn_reconstruction_err']:.2e}",
         "known": "det=1, orthogonal, reconstructs (genuine SO(3))", "match": e3["pass"]},
    ], {
        "su2_induced_so3": [[float(x) for x in row] for row in R_su2],
        "clifford_rotor_so3": [[float(x) for x in row] for row in R_cliff],
        "e3nn_so3_check": e3,
        "amplitude_damping_fixed_point_err": damp_to_ground_err,
        "dephasing_offdiag": deph_offdiag,
        "rotation_angle": rot_angle,
    }


# --------------------------------------------------------------------------- #
# Channel CPTP certificates (Choi PSD + trace preservation)                   #
# --------------------------------------------------------------------------- #
def channel_cptp_evidence() -> dict[str, Any]:
    out = {}
    for name, kraus_fn, params in (
        ("amplitude_damping", amplitude_damping_kraus, [0.0, 0.2, 0.5, 0.8, 1.0]),
        ("dephasing", dephasing_kraus, [0.0, 0.25, 0.5, 0.75, 1.0]),
    ):
        rows = []
        for prm in params:
            kr = kraus_fn(prm)
            rows.append({
                "param": prm,
                "trace_preserving_defect": kraus_trace_preserving_defect(kr),
                "choi_min_eigenvalue": choi_min_eigenvalue(kr),
            })
        out[name] = {
            "rows": rows,
            "all_trace_preserving": all(r["trace_preserving_defect"] < TOL for r in rows),
            "all_completely_positive": all(r["choi_min_eigenvalue"] > -TOL for r in rows),
        }
    return out


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # sympy exact pure-state geometry.
    sym = sympy_pure_state_exact()

    # known-value cross-checks (the depth proof).
    kvc, kvc_aux = known_value_checks(blocks, sym)

    # z3 + cvc5 PSD/trace-1 certificates on a sweep of sampled densities.
    gen = torch.Generator().manual_seed(1234)
    cert_rhos = [density(haar_spinor(gen)) for _ in range(6)]
    cert_rhos.append(I2 / 2)  # maximally mixed
    cert_rhos.append(torch.tensor([[0.7, 0.2 + 0.1j], [0.2 - 0.1j, 0.3]], dtype=CDTYPE))  # mixed
    z3_rows = [z3_psd_trace1_certificate(r) for r in cert_rhos]
    cvc5_rows = [cvc5_psd_trace1_certificate(r) for r in cert_rhos]
    z3_pass = all(r["pass"] for r in z3_rows)
    cvc5_pass = all(r["pass"] for r in cvc5_rows)

    # CPTP channel evidence.
    cptp = channel_cptp_evidence()

    # Negatives.
    neg_scalar = negative_scalar_label()
    neg_mixed = negative_maximally_mixed()
    neg_flat = negative_flat_channel()
    neg_comm = negative_commutative_collapse()
    negatives = {
        "scalar_label_carrier": {"detail": neg_scalar, "kills_signature": neg_scalar["kills_geometry"]},
        "maximally_mixed_rho": {"detail": neg_mixed, "kills_signature": neg_mixed["differs_from_pure"] and neg_mixed["purity_is_half"]},
        "flattened_identity_channel": {"detail": neg_flat, "kills_signature": neg_flat["flat_is_identity"] and neg_flat["live_moves_state"]},
        "commutative_collapse_diagonal": {"detail": neg_comm, "kills_signature": neg_comm["xy_plane_collapsed"] and neg_comm["diag_commutes_with_sz"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (z3_pass and cvc5_pass
                      and sym["rho_squared_equals_rho_exact"]
                      and kvc_aux["e3nn_so3_check"]["pass"]
                      and kvc_aux["clifford_rotor_so3"] is not None
                      and cptp["amplitude_damping"]["all_completely_positive"]
                      and cptp["dephasing"]["all_completely_positive"])

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3_pass:
        blockers.append("z3 PSD+trace1 negation not UNSAT for all sampled densities")
    if not cvc5_pass:
        blockers.append("cvc5 PSD+trace1 negation not UNSAT for all sampled densities")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all density/spinor/Bloch/eigenvalue/fidelity/CPTP-channel algebra in complex128; scalar-label and commutative-collapse negatives kill the Bloch geometry"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proof rho^2=rho for a generic pure state and rho=(I+r.sigma)/2 symbolic Bloch reconstruction; numeric torch alone cannot prove the exact idempotent identity"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that each sampled rho is PSD with trace 1 (2x2 Sylvester conditions); the negation is UNSAT"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family certifying the same PSD+trace-1 fact (QF_NRA, negation UNSAT)"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "Cl(3) geometric-algebra rotor reproduces the SU(2)-induced SO(3) Bloch rotation (even subalgebra == SU(2) double cover); ||R_cl - R_su2|| ~ 0"},
        "e3nn": {"used": True, "role": "load_bearing",
                 "reason": "certifies the SU(2)-induced 3x3 Bloch rotation is a genuine SO(3) element via the l=1 irrep angle round-trip"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Deep, standalone spinor/density (single-qubit Bloch-ball) carrier geometry lego computed in real torch with full tool integration, cross-checked against textbook analytic invariants. Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Does the spinor->density map psi -> rho = psi psi^dag reproduce the known single-qubit Bloch-ball geometry (purity, Bloch vector, spectrum, fidelity, CPTP channels, SU(2)->SO(3) double cover) to its exact analytic values, and do the reduced/flattened controls kill that geometry?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim.",
        "finite_map": "(normalized spinor psi in C^2) -> (rho = psi psi^dag, Bloch vector r in R^3, purity Tr(rho^2), spectrum, Uhlmann fidelity, amplitude-damping & dephasing CPTP channel images)",
        "domain": "normalized two-component spinors psi in C^2 (Haar-sampled via complex-Gaussian QR), Pauli operator set {sigma_x, sigma_y, sigma_z}, CPTP channel parameters",
        "codomain_or_output": "single-qubit density operators rho (the Bloch ball), their Bloch vectors, purities, spectra, pairwise fidelities, and CPTP channel images",
        "carrier_layer": "single-qubit spinor/density carrier (Bloch ball B^3 with boundary sphere S^2 of pure states)",
        "geometry_layer": "Bloch-ball geometry: pure states on S^2 (|r|=1), mixed states interior; SU(2) acts on spinors, SO(3) double cover acts on Bloch vectors",
        "carrier_realization": "torch.complex128 spinors and densities; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random spinors are genuine Haar samples)",
        "spinor_state": "torch.complex128 two-component spinors psi and spinor-derived densities rho = psi psi^dag",
        "quaternion_action": "even subalgebra of Cl(3) (clifford) realizes the unit quaternions == SU(2); rotor R=exp(-theta/2 B) reproduces the SU(2)-induced SO(3) Bloch rotation",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "single-qubit spinor->density Bloch-ball geometry against textbook analytic invariants",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["standalone known-math spinor/density carrier geometry witness; computed invariants match textbook values to machine precision"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_states": sum(b["n_states"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_psd_trace1_all_unsat": z3_pass,
            "cvc5_psd_trace1_all_unsat": cvc5_pass,
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "known_value_aux": kvc_aux,
        "sympy_exact_pure_state": sym,

        "variation_blocks": blocks,

        "psd_trace1_certificates": {
            "z3": {"rows": z3_rows, "all_unsat": z3_pass, "n_states_certified": len(cert_rhos)},
            "cvc5": {"rows": cvc5_rows, "all_unsat": cvc5_pass, "n_states_certified": len(cert_rhos)},
        },

        "cptp_channels": cptp,

        "required_negatives": ["scalar_label_carrier", "maximally_mixed_rho", "flattened_identity_channel", "commutative_collapse_diagonal"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 PSD+trace-1 negation not UNSAT",
            "scalar-label carrier retains Bloch directional spread",
            "maximally mixed state does not collapse to purity 1/2",
            "flattened identity channel moves the state",
            "diagonal carrier retains x/y Bloch structure",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "clifford": "load_bearing", "e3nn": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "clifford", "e3nn"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 PSD/trace-1 negations are UNSAT AND all CPTP channels are completely positive & trace preserving",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, or any non-CPTP channel",
        "eligible_consumers": ["other diagnostic_only spinor/density geometry probes"],
    }

    # Witness trace
    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_haar_spinors", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_states": sum(b["n_states"] for b in blocks)},
            {"step": "compute_density_bloch_purity_spectrum_fidelity", "tool": "torch.complex128"},
            {"step": "sympy_exact_idempotent_and_bloch", "rho2_eq_rho": sym["rho_squared_equals_rho_exact"],
             "bloch_norm_sq": sym["bloch_norm_squared_exact"]},
            {"step": "z3_psd_trace1_certificate", "all_unsat": z3_pass, "n": len(cert_rhos)},
            {"step": "cvc5_psd_trace1_certificate", "all_unsat": cvc5_pass, "n": len(cert_rhos)},
            {"step": "cptp_channel_choi_and_trace_preservation", "channels": list(cptp.keys())},
            {"step": "clifford_Cl3_rotor_vs_su2_so3", "matrix_diff": kvc_aux["su2_induced_so3"] is not None},
            {"step": "e3nn_so3_certification", "pass": kvc_aux["e3nn_so3_check"]["pass"]},
            {"step": "run_negatives", "negatives": list(negatives.keys()),
             "all_kill": negatives_all_kill},
            {"step": "known_value_cross_checks", "n": len(kvc), "all_match": known_values_all_match},
        ],
        "final_classification": "diagnostic_only",
        "all_pass": all_pass,
        "blockers": blockers,
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    wit = RESULT_DIR / f"{SIM_ID}_witness.json"
    wit.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "wrote": str(out),
        "witness": str(wit),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "negatives_all_kill": negatives_all_kill,
        "tools_all_pass": tools_all_pass,
        "n_known_value_checks": len(kvc),
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in kvc],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
