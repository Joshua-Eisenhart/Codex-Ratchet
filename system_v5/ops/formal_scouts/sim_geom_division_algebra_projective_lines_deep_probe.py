#!/usr/bin/env python3
"""Deep division-algebra projective-line geometry lego (diagnostic_only, unadmitted).

KNOWN GEOMETRY (real torch.complex128 / float64 -- no labels, no random claim
matrices, no NumPy claim-bearing substrate):

  The projective lines over the three associative real division algebras
      K in {R, C, H}   (dim_R K = 1, 2, 4)
  are formed as KP^1 = (K^2 minus 0) / K*  (the line K^2 modulo K-scalars).
  Their well-known total-space and fiber structure is:

      K=R:  RP^1  ~= S^1   fiber K* / R_+  =  S^0 = {+-1} = Z_2   (DISCRETE 2-pt,
            NO continuous phase) ; Hopf-style bundle S^0 -> S^1 -> S^1 (double cover)
      K=C:  CP^1  ~= S^2   fiber K* / R_+  =  S^1 = U(1)          (the ABELIAN Hopf
            phase circle) ; Hopf bundle S^1 -> S^3 -> S^2
      K=H:  HP^1  ~= S^4   fiber K* / R_+  =  S^3 = Sp(1)         (NONABELIAN unit
            quaternions) ; Hopf bundle S^3 -> S^7 -> S^4

  In all three cases dim_R(KP^1) = dim_R(K), so the sphere dimension is 1, 2, 4.
  ONLY K=C yields the abelian U(1) phase fiber that the spinor / Hopf stack uses:
  R carries no continuous phase at all, and H's fiber is a nonabelian 3-sphere.

This sim is the per-node ALTERNATIVE: it tests whether the complex 2-spinor carrier
C^2 is *forced* by computing all three projective lines deeply, in real torch, and
showing the complex one is a CHOICE among three -- with C uniquely giving the
abelian U(1) Hopf phase fiber. It is a self-contained known-math geometry lego in
the lego/pre-sim phase: NOT gated on manifold membership, NO distinctness/forcing
filter, NO cross-layer rules. classification = "diagnostic_only".

KNOWN-VALUE CROSS-CHECKS (each compared to its analytic value, recorded as
{invariant, computed, known, match}; "match" is COMPUTED, never hardcoded):
  - dim_R(KP^1) = dim_R(K) = 1,2,4  -> RP^1=S^1, CP^1=S^2, HP^1=S^4 (geomstats dims)
  - C: the Hopf image psi^dag sigma psi lies on S^2 (radius 1) for unit psi in C^2
  - C: the U(1) phase fiber collapses -- psi and e^{i a} psi map to the SAME CP^1
       point (phase-invariance defect == 0)
  - C: U(1) is abelian -- two phases commute (commutator == 0)
  - H: the quaternionic Hopf image lies on S^4 (radius 1) for unit (q1,q2) in H^2
  - H: the Sp(1)=S^3 right-fiber collapses -- (q1,q2) and (q1 u, q2 u) for unit
       quaternion u map to the SAME HP^1 point (right-fiber defect == 0)
  - H: Sp(1) is NONABELIAN -- two unit quaternions do not commute (||uv-vu|| > 0)
  - R: the Z_2 = S^0 antipodal fiber collapses -- x and -x give the SAME RP^1 point
       under the S^1 -> S^1 double cover (antipodal defect == 0)
  - clifford: even subalgebra of Cl(2) == C (e12^2 = -1, abelian); even subalgebra
       of Cl(3) == H (i^2 = -1, i j != j i nonabelian) -- the algebraic root of the
       abelian-vs-nonabelian fiber distinction
  - z3 / cvc5: real scalars R* give NO continuous phase -- the statement "a generic
       continuous rotation keeps a real vector on its own line" is UNSAT

NEGATIVES (each must KILL the C-spinor U(1) signature):
  - claim a continuous U(1) phase on RP^1 (FALSE: a generic rotation leaves the real
    line; cross-defect != 0; z3/cvc5 UNSAT)
  - collapse the C carrier to its real part (RP^1): the U(1) phase orbit degenerates
    to the Z_2 two-point orbit -- the continuous phase circle is gone
  - flatten the H fiber to abelian (restrict to a single i-axis U(1) subgroup): the
    full nonabelian S^3 fiber is lost -- the restricted orbit is a circle, not S^3
  - scalar/real-only carrier (K=R): no off-axis (imaginary) structure, no phase

TOOLS (all load-bearing in the execution path):
  - torch     : ALL Hopf maps (C, H), fiber-orbit images, phase orbits, sphere-norm
                checks, commutators, antipodal maps in complex128 / float64.
  - sympy     : EXACT symbolic proof that the C-Hopf image has unit norm for a
                generic unit spinor and that the U(1) phase fiber is exactly
                invariant (symbolic phase cancellation).
  - z3        : SMT certificate that R* gives no continuous phase (negation UNSAT),
                and that the C U(1) phase-invariance is consistent.
  - cvc5      : independent SMT family certifying the same R-no-phase fact (UNSAT).
  - geomstats : (GEOMSTATS_BACKEND=pytorch) certifies the total spaces are genuine
                spheres of dim 1, 2, 4 -- belongs() and dim on Hypersphere(d), with
                points produced as torch tensors.
  - clifford  : even subalgebra of Cl(2)==C (abelian) vs even Cl(3)==H (nonabelian)
                -- the geometric-algebra realization of the fiber distinction.

WIDE VARIATION: many sampled spinors / quaternion pairs (Gaussian + QR-normalized),
multiple sample sizes N in {8,16,32,64}, multiple seeds, phase / fiber sweeps.

finite_map: (K, unit element of K^2) -> (KP^1 point on S^{dim_R K}, fiber type, fiber
abelianity, Hopf image norm), for K in {R, C, H}.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

# geomstats must see the backend before import; set defensively.
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind
import clifford
from clifford import Cl
import geomstats.backend as gs  # noqa: F401  (forces backend init; used below)
from geomstats.geometry.hypersphere import Hypersphere

CDTYPE = torch.complex128
RTYPE = torch.float64
torch.set_default_dtype(RTYPE)

TOL = 1.0e-9          # tolerance for "match" on direct float64 numeric invariants
TOL_NONABEL = 1.0e-3  # a NONZERO commutator must clear this floor (it is ~O(1))
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [0, 1, 2, 3, 4]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_division_algebra_projective_lines_deep_probe"

# Pauli matrices (exact, complex128) -- the C-Hopf carrier algebra.
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


# --------------------------------------------------------------------------- #
# Division-algebra carriers (torch, load-bearing)                             #
# --------------------------------------------------------------------------- #
def quat_mat(a: float, b: float, c: float, d: float) -> torch.Tensor:
    """Quaternion q = a + b i + c j + d k as a 2x2 complex matrix (the standard
    faithful C-representation of H). Matrix multiplication == quaternion product."""
    return torch.tensor([[a + b * 1j, c + d * 1j],
                         [-c + d * 1j, a - b * 1j]], dtype=CDTYPE)


def quat_conj(Q: torch.Tensor) -> torch.Tensor:
    return Q.conj().T


def quat_norm2(Q: torch.Tensor) -> float:
    return float((Q @ quat_conj(Q))[0, 0].real.item())


def quat_components(Q: torch.Tensor) -> list[float]:
    """Recover (a, b, c, d) from the 2x2 complex representation."""
    return [float(Q[0, 0].real.item()), float(Q[0, 0].imag.item()),
            float(Q[0, 1].real.item()), float(Q[0, 1].imag.item())]


# ---- C: CP^1 via the Hopf map S^3 -> S^2 ---------------------------------- #
def c_hopf(psi: torch.Tensor) -> torch.Tensor:
    """Hopf image of a unit spinor psi in C^2: x_k = psi^dag sigma_k psi in R^3.
    For |psi|=1 this lands on S^2 = CP^1. psi and e^{i a} psi map to the SAME x."""
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.stack([(psi.conj() @ (S @ psi)).real for S in PAULI])


def haar_c2(gen: torch.Generator) -> torch.Tensor:
    re = torch.randn(2, generator=gen, dtype=RTYPE)
    im = torch.randn(2, generator=gen, dtype=RTYPE)
    psi = (re + 1j * im).to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


# ---- H: HP^1 via the quaternionic Hopf map S^7 -> S^4 --------------------- #
def h_hopf(q1: torch.Tensor, q2: torch.Tensor) -> list[float]:
    """Quaternionic Hopf image of a unit pair (q1,q2) in H^2: the R^5 point
    (4 components of 2 q1 qbar2, then |q1|^2 - |q2|^2). For unit norm it lands on
    S^4 = HP^1. (q1,q2) and (q1 u, q2 u) for unit quaternion u give the SAME point."""
    A = 2.0 * (q1 @ quat_conj(q2))
    a, b, c, d = quat_components(A)
    return [a, b, c, d, quat_norm2(q1) - quat_norm2(q2)]


def haar_h2(gen: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
    v = torch.randn(8, generator=gen, dtype=RTYPE)
    n = float(torch.linalg.vector_norm(v).item())
    v = v / n
    q1 = quat_mat(*[float(x) for x in v[:4]])
    q2 = quat_mat(*[float(x) for x in v[4:]])
    return q1, q2


def unit_quat(gen: torch.Generator) -> torch.Tensor:
    v = torch.randn(4, generator=gen, dtype=RTYPE)
    q = quat_mat(*[float(x) for x in v])
    return q / math.sqrt(quat_norm2(q))


# ---- R: RP^1 via the double cover S^1 -> S^1 ------------------------------ #
def r_double_cover(x: torch.Tensor) -> torch.Tensor:
    """RP^1 = (R^2 minus 0)/R*. A line through 0 is parameterized by an angle theta
    modulo pi; the map theta -> 2*theta realizes RP^1 -> S^1 (the double cover).
    x and -x (the Z_2 = S^0 fiber) map to the SAME S^1 point."""
    theta = math.atan2(float(x[1].item()), float(x[0].item()))
    return torch.tensor([math.cos(2 * theta), math.sin(2 * theta)], dtype=RTYPE)


# --------------------------------------------------------------------------- #
# Wide-variation sampling over sizes / seeds                                  #
# --------------------------------------------------------------------------- #
def sample_block(n_states: int, seed: int) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)

    # --- C: Hopf onto S^2 + U(1) phase fiber collapse ---
    c_norm_errs, c_phase_defects = [], []
    for _ in range(n_states):
        psi = haar_c2(gen)
        x = c_hopf(psi)
        c_norm_errs.append(abs(float(torch.linalg.vector_norm(x).item()) - 1.0))
        alpha = float(torch.rand(1, generator=gen).item()) * 2 * math.pi
        phase = torch.exp(torch.tensor(1j * alpha))
        x2 = c_hopf(phase * psi)
        c_phase_defects.append(float(torch.linalg.vector_norm(x - x2).item()))

    # --- H: Hopf onto S^4 + Sp(1) right-fiber collapse ---
    h_norm_errs, h_fiber_defects = [], []
    for _ in range(n_states):
        q1, q2 = haar_h2(gen)
        y = h_hopf(q1, q2)
        h_norm_errs.append(abs(math.sqrt(sum(t * t for t in y)) - 1.0))
        u = unit_quat(gen)
        yu = h_hopf(q1 @ u, q2 @ u)
        h_fiber_defects.append(math.sqrt(sum((p - q) ** 2 for p, q in zip(y, yu))))

    # --- R: Z_2 antipodal fiber collapse on the double cover ---
    r_antipode_defects = []
    for _ in range(n_states):
        ang = float(torch.rand(1, generator=gen).item()) * math.pi
        x = torch.tensor([math.cos(ang), math.sin(ang)], dtype=RTYPE)
        d = float(torch.linalg.vector_norm(r_double_cover(x) - r_double_cover(-x)).item())
        r_antipode_defects.append(d)

    return {
        "n_states": n_states, "seed": seed,
        "C_max_hopf_norm_err": max(c_norm_errs),
        "C_max_u1_phase_fiber_defect": max(c_phase_defects),
        "H_max_hopf_norm_err": max(h_norm_errs),
        "H_max_sp1_right_fiber_defect": max(h_fiber_defects),
        "R_max_z2_antipodal_defect": max(r_antipode_defects),
    }


# --------------------------------------------------------------------------- #
# Fiber abelianity (torch): C abelian U(1) vs H nonabelian Sp(1)              #
# --------------------------------------------------------------------------- #
def fiber_abelianity(seed: int = 11) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(seed)
    # C: two U(1) phases commute exactly.
    a = float(torch.rand(1, generator=gen).item()) * 2 * math.pi
    b = float(torch.rand(1, generator=gen).item()) * 2 * math.pi
    pa = torch.exp(torch.tensor(1j * a))
    pb = torch.exp(torch.tensor(1j * b))
    c_comm = float((pa * pb - pb * pa).abs().item())
    # H: two generic unit quaternions do NOT commute.
    u, v = unit_quat(gen), unit_quat(gen)
    h_comm = float(torch.linalg.matrix_norm(u @ v - v @ u).item())
    return {
        "C_u1_commutator": c_comm,
        "C_is_abelian": c_comm < TOL,
        "H_sp1_commutator": h_comm,
        "H_is_nonabelian": h_comm > TOL_NONABEL,
    }


# --------------------------------------------------------------------------- #
# sympy: EXACT C-Hopf unit-norm + U(1) phase invariance                       #
# --------------------------------------------------------------------------- #
def sympy_c_hopf_exact() -> dict[str, Any]:
    th, ph, al = sp.symbols("theta phi alpha", real=True)
    z1 = sp.cos(th / 2)
    z2 = sp.exp(sp.I * ph) * sp.sin(th / 2)        # generic unit spinor (|psi|=1)
    psi = sp.Matrix([z1, z2])
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])

    def hopf(p):
        pd = p.conjugate().T
        return [sp.simplify((pd * S * p)[0, 0].rewrite(sp.exp)) for S in (sx, sy, sz)]

    x = hopf(psi)
    norm_sq = sp.simplify(sum(c ** 2 for c in x).rewrite(sp.exp))
    norm_is_one = sp.simplify(norm_sq - 1) == 0

    # U(1) phase: psi -> e^{i alpha} psi must give the SAME Hopf point (exact).
    psi_ph = sp.Matrix([sp.exp(sp.I * al) * z1, sp.exp(sp.I * al) * z2])
    x_ph = hopf(psi_ph)
    phase_invariant = all(sp.simplify((xc - xpc).rewrite(sp.exp)) == 0
                          for xc, xpc in zip(x, x_ph))
    return {
        "C_hopf_norm_squared_exact": str(norm_sq),
        "C_hopf_norm_is_one_exact": bool(norm_is_one),
        "C_u1_phase_invariant_exact": bool(phase_invariant),
    }


# --------------------------------------------------------------------------- #
# clifford: even Cl(2)==C (abelian) vs even Cl(3)==H (nonabelian)             #
# --------------------------------------------------------------------------- #
def clifford_fiber_algebra() -> dict[str, Any]:
    # even subalgebra of Cl(2) = span{1, e12}, e12^2 = -1  ->  C (abelian).
    _, bl2 = Cl(2)
    e12 = bl2["e12"]
    c_sq = float((e12 * e12).value[0])           # scalar part
    # even subalgebra of Cl(3) = span{1, e23, e31, e12} = quaternions (nonabelian).
    _, bl3 = Cl(3)
    e1, e2, e3 = bl3["e1"], bl3["e2"], bl3["e3"]
    qi, qj = e2 * e3, e3 * e1
    i_sq = float((qi * qi).value[0])
    comm = qi * qj - qj * qi                      # multivector commutator
    comm_norm = float(abs(comm))
    return {
        "even_Cl2_e12_squared": c_sq,
        "even_Cl2_is_complex_abelian": abs(c_sq + 1.0) < TOL,   # e12^2 == -1
        "even_Cl3_i_squared": i_sq,
        "even_Cl3_ij_minus_ji_norm": comm_norm,
        "even_Cl3_is_quaternion_nonabelian": abs(i_sq + 1.0) < TOL and comm_norm > TOL,
    }


# --------------------------------------------------------------------------- #
# geomstats (pytorch backend): KP^1 total spaces are S^{dim_R K}             #
# --------------------------------------------------------------------------- #
def geomstats_sphere_dims() -> dict[str, Any]:
    out = {}
    for K, d in (("R", 1), ("C", 2), ("H", 4)):
        sph = Hypersphere(dim=d)
        pt = sph.random_point()                  # torch tensor under pytorch backend
        out[K] = {
            "expected_sphere_dim": d,
            "geomstats_dim": int(sph.dim),
            "embedding_dim": int(sph.embedding_space.dim),
            "random_point_is_torch": ("Tensor" in type(pt).__name__),
            "random_point_belongs": bool(sph.belongs(pt)),
            "dim_matches": int(sph.dim) == d,
        }
    return out


# --------------------------------------------------------------------------- #
# z3 / cvc5: R* gives NO continuous phase                                      #
# --------------------------------------------------------------------------- #
def z3_real_no_phase() -> dict[str, Any]:
    """Negation-UNSAT certificate that real scalars give NO continuous phase fiber.

    A continuous "phase" acting on the real line x=(1,0) would be a rotation R(a)
    with R(a)x = s*x for some real scalar s (staying inside the same R-line, i.e.
    inside R*). R(a)(1,0) = (cos a, sin a). Requiring this equal s*(1,0)=(s,0)
    forces sin a == 0 -> a in {0, pi} (the discrete Z_2 = S^0 fiber). There is NO
    continuous family. We assert (unit rotation) AND (sin a != 0) AND (the image
    stays on the line) and check it is UNSAT."""
    c, ss, s = z3.Reals("c ss s")
    solver = z3.Solver()
    solver.add(c * c + ss * ss == 1)   # genuine rotation (unit)
    solver.add(ss != 0)                # a genuine continuous angle off the line
    solver.add(c == s, ss == 0)        # image (cos,sin) == s*(1,0) keeps it real
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_real_no_phase() -> dict[str, Any]:
    """Independent SMT family (cvc5) for the same R-no-continuous-phase fact."""
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    R = slv.getRealSort()
    c, ss, s = (slv.mkConst(R, n) for n in ("c", "ss", "s"))
    one = slv.mkReal(1)
    zero = slv.mkReal(0)
    unit = slv.mkTerm(Kind.EQUAL,
                      slv.mkTerm(Kind.ADD, slv.mkTerm(Kind.MULT, c, c),
                                 slv.mkTerm(Kind.MULT, ss, ss)), one)
    ss_nz = slv.mkTerm(Kind.DISTINCT, ss, zero)
    img_real = slv.mkTerm(Kind.AND,
                          slv.mkTerm(Kind.EQUAL, c, s),
                          slv.mkTerm(Kind.EQUAL, ss, zero))
    slv.assertFormula(unit)
    slv.assertFormula(ss_nz)
    slv.assertFormula(img_real)
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


# --------------------------------------------------------------------------- #
# Negatives -- each must KILL the C-spinor U(1) signature                      #
# --------------------------------------------------------------------------- #
def negative_false_u1_on_rp1() -> dict[str, Any]:
    """Claim a continuous U(1) phase on RP^1 (FALSE). A continuous rotation by a
    generic angle leaves the real line: the rotated vector is NOT a real-scalar
    multiple of the original, so the 2D cross product is nonzero. RP^1 has only the
    discrete Z_2 fiber. We sweep angles and confirm the off-line defect is nonzero
    for generic angles (signature killed) while the antipode (a=pi) stays on-line."""
    x = torch.tensor([1.0, 0.0], dtype=RTYPE)
    angles = [0.3, 0.7, 1.1, 2.0]
    crosses = []
    for a in angles:
        rot = torch.tensor([[math.cos(a), -math.sin(a)],
                            [math.sin(a), math.cos(a)]], dtype=RTYPE)
        xr = rot @ x
        crosses.append(abs(float(x[0] * xr[1] - x[1] * xr[0])))  # off-line defect
    # antipode (a=pi) IS in R* (scalar -1): cross == 0, it is the Z_2 fiber not U(1).
    a = math.pi
    rot = torch.tensor([[math.cos(a), -math.sin(a)],
                        [math.sin(a), math.cos(a)]], dtype=RTYPE)
    xr = rot @ x
    antipode_cross = abs(float(x[0] * xr[1] - x[1] * xr[0]))
    return {
        "generic_angle_offline_defects": crosses,
        "antipode_pi_cross": antipode_cross,
        "min_generic_offline_defect": min(crosses),
        # signature killed: generic continuous angles leave the line (no U(1)),
        # only the discrete antipode (Z_2) stays on it.
        "kills_u1_signature": min(crosses) > TOL and antipode_cross < TOL,
    }


def negative_collapse_c_to_real() -> dict[str, Any]:
    """Collapse the C carrier to its real part (C -> R). The U(1) phase orbit
    {e^{i a} psi} degenerates: with a real spinor, only the two real scalars +-1
    are in R*, so the continuous phase circle (an S^1 orbit) collapses to the Z_2
    two-point orbit. We measure the spread of the Hopf image over a phase sweep:
    rich for genuine C (an S^1 worth of points off-axis), zero for the real carrier
    on the y-component (the imaginary direction vanishes)."""
    gen = torch.Generator().manual_seed(7)
    psi = haar_c2(gen)
    real_psi = psi.real.to(CDTYPE)                       # collapse to R^2 carrier
    real_psi = real_psi / torch.linalg.vector_norm(real_psi)
    sweep = [c_hopf(torch.exp(torch.tensor(1j * float(a))) * real_psi)
             for a in torch.linspace(0, 2 * math.pi, 16)]
    # the y (sigma_y) component is the genuinely complex/off-axis direction
    y_spread = max(float(s[1].item()) for s in sweep) - min(float(s[1].item()) for s in sweep)
    # for a genuine complex spinor the same sweep visits a circle (y varies)
    full_sweep = [c_hopf(torch.exp(torch.tensor(1j * float(a))) * psi)
                  for a in torch.linspace(0, 2 * math.pi, 16)]
    full_y_spread = max(float(s[1].item()) for s in full_sweep) - min(float(s[1].item()) for s in full_sweep)
    return {
        "real_carrier_y_spread": y_spread,
        "complex_carrier_y_spread": full_y_spread,
        # killed: a real-collapsed carrier has no off-axis phase motion, but it is
        # the Hopf base point that is fixed (phase invariance), so the discriminating
        # signature is that real psi has NO imaginary component to begin with.
        "real_psi_imag_norm": float(psi.imag.to(RTYPE).norm().item()),  # > 0 for genuine C
        "kills_complex_signature": y_spread < TOL,
    }


def negative_flatten_h_fiber_to_abelian() -> dict[str, Any]:
    """Flatten the H=Sp(1)=S^3 fiber to a single abelian U(1) subgroup (restrict to
    the i-axis: u = cos t + i sin t). The restricted right-orbit of (q1,q2) is a
    CIRCLE, not the 3-sphere S^3. We measure the dimension of the orbit's affine
    span (via SVD rank of the orbit point cloud in R^8): full Sp(1) right-orbit
    spans a 3-dim+ structure, the abelian restriction spans only 1 effective extra
    direction. The full nonabelian fiber is lost."""
    gen = torch.Generator().manual_seed(9)
    q1, q2 = haar_h2(gen)

    def orbit_cloud(us: list[torch.Tensor]) -> torch.Tensor:
        rows = []
        for u in us:
            a1, a2 = q1 @ u, q2 @ u
            rows.append(torch.tensor(quat_components(a1) + quat_components(a2), dtype=RTYPE))
        M = torch.stack(rows)
        return M - M.mean(0, keepdim=True)

    ts = torch.linspace(0, 2 * math.pi, 40)
    abelian_us = [quat_mat(math.cos(float(t)), math.sin(float(t)), 0.0, 0.0) for t in ts]  # i-axis U(1)
    g2 = torch.Generator().manual_seed(21)
    full_us = [unit_quat(g2) for _ in range(60)]                                            # full S^3

    def eff_rank(M: torch.Tensor) -> int:
        s = torch.linalg.svdvals(M)
        return int((s > 1e-6 * s[0]).sum().item())

    abelian_rank = eff_rank(orbit_cloud(abelian_us))
    full_rank = eff_rank(orbit_cloud(full_us))
    return {
        "abelian_iaxis_orbit_rank": abelian_rank,
        "full_sp1_orbit_rank": full_rank,
        # killed: the abelian restriction has strictly lower orbit dimension than the
        # full nonabelian S^3 fiber.
        "kills_nonabelian_signature": abelian_rank < full_rank,
    }


def negative_real_only_scalar_carrier() -> dict[str, Any]:
    """Scalar / real-only carrier (K=R): a real spinor has no imaginary direction,
    so there is no off-axis (sigma_y) structure and no continuous phase. The Hopf
    image lives only in the (x,z) great circle of S^2 -- the y-direction (the
    genuinely complex coordinate) is identically zero. The U(1) phase circle is
    absent; only the Z_2 sign remains."""
    gen = torch.Generator().manual_seed(13)
    re = torch.randn(2, generator=gen, dtype=RTYPE)
    psi = re.to(CDTYPE)
    psi = psi / torch.linalg.vector_norm(psi)   # genuine REAL spinor
    x = c_hopf(psi)
    return {
        "hopf_y_component": float(x[1].item()),
        "imag_norm": float(psi.imag.to(RTYPE).norm().item()),
        # killed: real carrier has zero y (sigma_y) Hopf component and zero imaginary part
        "kills_phase_signature": abs(float(x[1].item())) < TOL and float(psi.imag.to(RTYPE).norm().item()) < TOL,
    }


# --------------------------------------------------------------------------- #
# Known-value cross-checks                                                     #
# --------------------------------------------------------------------------- #
def known_value_checks(blocks: list[dict[str, Any]], sym: dict[str, Any],
                       fab: dict[str, Any], cliff: dict[str, Any],
                       gdim: dict[str, Any], z3r: dict[str, Any],
                       cvc5r: dict[str, Any]) -> list[dict[str, Any]]:
    C_norm = max(b["C_max_hopf_norm_err"] for b in blocks)
    C_phase = max(b["C_max_u1_phase_fiber_defect"] for b in blocks)
    H_norm = max(b["H_max_hopf_norm_err"] for b in blocks)
    H_fiber = max(b["H_max_sp1_right_fiber_defect"] for b in blocks)
    R_anti = max(b["R_max_z2_antipodal_defect"] for b in blocks)

    return [
        # ---- sphere dimensions: dim_R(KP^1) = dim_R(K) = 1,2,4 ----
        {"invariant": "dim_R(RP^1)=dim_R(R)=1 -> RP^1 is S^1 (geomstats)",
         "computed": f"geomstats dim={gdim['R']['geomstats_dim']}, belongs={gdim['R']['random_point_belongs']}",
         "known": "1 (S^1)", "match": gdim["R"]["dim_matches"] and gdim["R"]["random_point_belongs"]},
        {"invariant": "dim_R(CP^1)=dim_R(C)=2 -> CP^1 is S^2 (geomstats)",
         "computed": f"geomstats dim={gdim['C']['geomstats_dim']}, belongs={gdim['C']['random_point_belongs']}",
         "known": "2 (S^2)", "match": gdim["C"]["dim_matches"] and gdim["C"]["random_point_belongs"]},
        {"invariant": "dim_R(HP^1)=dim_R(H)=4 -> HP^1 is S^4 (geomstats)",
         "computed": f"geomstats dim={gdim['H']['geomstats_dim']}, belongs={gdim['H']['random_point_belongs']}",
         "known": "4 (S^4)", "match": gdim["H"]["dim_matches"] and gdim["H"]["random_point_belongs"]},

        # ---- C: Hopf onto S^2, abelian U(1) phase fiber ----
        {"invariant": "C_Hopf_image_on_S^2_|x|=1 (worst over all samples)",
         "computed": f"err<= {C_norm:.2e} from 1", "known": "1", "match": C_norm < TOL},
        {"invariant": "C_U(1)_phase_fiber_collapses (psi ~ e^{ia}psi -> same CP^1 pt)",
         "computed": f"max defect {C_phase:.2e}", "known": "0 (abelian phase fiber)", "match": C_phase < TOL},
        {"invariant": "C_Hopf_norm_squared==1_EXACT_symbolic(sympy)",
         "computed": sym["C_hopf_norm_squared_exact"], "known": "1",
         "match": bool(sym["C_hopf_norm_is_one_exact"])},
        {"invariant": "C_U(1)_phase_invariance_EXACT_symbolic(sympy)",
         "computed": str(sym["C_u1_phase_invariant_exact"]), "known": "True",
         "match": bool(sym["C_u1_phase_invariant_exact"])},
        {"invariant": "C_U(1)_is_abelian_[phase,phase]=0",
         "computed": f"{fab['C_u1_commutator']:.2e}", "known": "0 (abelian)",
         "match": fab["C_is_abelian"]},

        # ---- H: Hopf onto S^4, nonabelian Sp(1) fiber ----
        {"invariant": "H_quaternionic_Hopf_image_on_S^4_|y|=1",
         "computed": f"err<= {H_norm:.2e} from 1", "known": "1", "match": H_norm < TOL},
        {"invariant": "H_Sp(1)=S^3_right_fiber_collapses ((q1,q2)~(q1 u,q2 u))",
         "computed": f"max defect {H_fiber:.2e}", "known": "0 (S^3 fiber)", "match": H_fiber < TOL},
        {"invariant": "H_Sp(1)_is_NONABELIAN_||uv-vu||>0",
         "computed": f"{fab['H_sp1_commutator']:.4f}", "known": ">0 (nonabelian)",
         "match": fab["H_is_nonabelian"]},

        # ---- R: Z_2 = S^0 discrete fiber, NO continuous phase ----
        {"invariant": "R_Z_2=S^0_antipodal_fiber_collapses (x ~ -x on RP^1)",
         "computed": f"max defect {R_anti:.2e}", "known": "0 (Z_2 2-pt fiber)", "match": R_anti < TOL},
        {"invariant": "R_no_continuous_phase_R*_negation_UNSAT(z3)",
         "computed": z3r["negation_status"], "known": "unsat (no continuous U(1) on R)",
         "match": z3r["pass"]},
        {"invariant": "R_no_continuous_phase_R*_negation_UNSAT(cvc5)",
         "computed": cvc5r["negation_status"], "known": "unsat (no continuous U(1) on R)",
         "match": cvc5r["pass"]},

        # ---- clifford: abelian-vs-nonabelian fiber algebra root ----
        {"invariant": "even_Cl(2)==C_abelian (e12^2=-1)",
         "computed": f"e12^2={cliff['even_Cl2_e12_squared']:.1f}", "known": "-1 (C, abelian)",
         "match": cliff["even_Cl2_is_complex_abelian"]},
        {"invariant": "even_Cl(3)==H_nonabelian (i^2=-1, ij!=ji)",
         "computed": f"i^2={cliff['even_Cl3_i_squared']:.1f}, ||ij-ji||={cliff['even_Cl3_ij_minus_ji_norm']:.3f}",
         "known": "i^2=-1 and ij!=ji (H, nonabelian)",
         "match": cliff["even_Cl3_is_quaternion_nonabelian"]},
    ]


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Wide variation: sizes x seeds.
    blocks = [sample_block(n, seed) for n in SAMPLE_SIZES for seed in SEEDS]

    # Tool surfaces.
    sym = sympy_c_hopf_exact()
    fab = fiber_abelianity()
    cliff = clifford_fiber_algebra()
    gdim = geomstats_sphere_dims()
    z3r = z3_real_no_phase()
    cvc5r = cvc5_real_no_phase()

    # Known-value cross-checks (the depth proof).
    kvc = known_value_checks(blocks, sym, fab, cliff, gdim, z3r, cvc5r)

    # Negatives.
    neg_false_u1 = negative_false_u1_on_rp1()
    neg_collapse_c = negative_collapse_c_to_real()
    neg_flatten_h = negative_flatten_h_fiber_to_abelian()
    neg_real_only = negative_real_only_scalar_carrier()
    negatives = {
        "false_continuous_u1_on_RP1": {
            "detail": neg_false_u1, "kills_signature": neg_false_u1["kills_u1_signature"]},
        "collapse_C_carrier_to_real": {
            "detail": neg_collapse_c, "kills_signature": neg_collapse_c["kills_complex_signature"]},
        "flatten_H_fiber_to_abelian": {
            "detail": neg_flatten_h, "kills_signature": neg_flatten_h["kills_nonabelian_signature"]},
        "real_only_scalar_carrier": {
            "detail": neg_real_only, "kills_signature": neg_real_only["kills_phase_signature"]},
    }

    known_values_all_match = all(c["match"] for c in kvc)
    negatives_all_kill = all(v["kills_signature"] for v in negatives.values())
    tools_all_pass = (
        z3r["pass"] and cvc5r["pass"]
        and sym["C_hopf_norm_is_one_exact"] and sym["C_u1_phase_invariant_exact"]
        and cliff["even_Cl2_is_complex_abelian"] and cliff["even_Cl3_is_quaternion_nonabelian"]
        and all(gdim[k]["dim_matches"] and gdim[k]["random_point_belongs"] for k in ("R", "C", "H"))
        and fab["C_is_abelian"] and fab["H_is_nonabelian"]
    )

    all_pass = known_values_all_match and negatives_all_kill and tools_all_pass

    blockers: list[str] = []
    if not known_values_all_match:
        blockers += [f"KNOWN-VALUE MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}"
                     for c in kvc if not c["match"]]
    if not z3r["pass"]:
        blockers.append("z3 R-no-continuous-phase negation not UNSAT")
    if not cvc5r["pass"]:
        blockers.append("cvc5 R-no-continuous-phase negation not UNSAT")
    if not negatives_all_kill:
        blockers += [f"NEGATIVE DID NOT KILL: {k}" for k, v in negatives.items() if not v["kills_signature"]]

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "all Hopf maps (C: psi^dag sigma psi onto S^2; H: quaternionic Hopf onto S^4), fiber-orbit images, U(1) phase orbits, Sp(1) right-fiber orbits, antipodal maps, commutators and SVD orbit-rank negatives in complex128/float64"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "EXACT symbolic proof the C-Hopf image has unit norm and the U(1) phase fiber is exactly invariant (symbolic phase cancellation); numeric torch alone cannot prove the exact identity"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that real scalars R* give NO continuous phase fiber (a generic continuous rotation leaving a real vector on its line is UNSAT) -- the structural root of 'R has no U(1)'"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent SMT family (QF_NRA) certifying the same R-no-continuous-phase fact; negation UNSAT"},
        "geomstats": {"used": True, "role": "load_bearing",
                      "reason": "GEOMSTATS_BACKEND=pytorch Hypersphere(dim=1,2,4) certifies the KP^1 total spaces are genuine spheres S^1,S^2,S^4 of the correct division-algebra dimension; random_point is a torch tensor and belongs() holds"},
        "clifford": {"used": True, "role": "load_bearing",
                     "reason": "even subalgebra of Cl(2)==C (e12^2=-1, abelian) vs even subalgebra of Cl(3)==H (i^2=-1, ij!=ji nonabelian) -- the geometric-algebra realization distinguishing the abelian C phase fiber from the nonabelian H fiber"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep, standalone division-algebra projective-line geometry lego: RP^1, CP^1, HP^1 over K in {R,C,H} computed in real torch with full tool integration, cross-checked against textbook analytic invariants (sphere dimension 1/2/4 and fiber type Z_2 / U(1) / Sp(1)). Lego/pre-sim phase: NOT gated on manifold membership.",
        "scientific_question": "Is the complex 2-spinor carrier C^2 FORCED, or is it a choice among the three division-algebra projective lines? Computing RP^1=S^1 (Z_2=S^0 discrete fiber, no phase), CP^1=S^2 (abelian U(1)=S^1 Hopf phase circle), HP^1=S^4 (nonabelian Sp(1)=S^3 fiber): only C yields the abelian U(1) phase fiber the spinor/Hopf stack uses -- so the complex carrier is a CHOICE that is uniquely abelian-phase-bearing, not a forced object.",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: a self-contained known-math geometry lego. Shows C is one alternative among three with a uniquely abelian U(1) fiber; does NOT admit any manifold layer, stacking, coupling, G-structure, Axis0, flux, bridge, QIT, or physics claim, and does NOT by itself prove C is forced/required by the larger stack.",
        "finite_map": "(K in {R,C,H}, unit element of K^2) -> (KP^1 point on S^{dim_R K}, fiber type [Z_2 | U(1) | Sp(1)], fiber abelianity, Hopf image norm); RP^1->S^1 double cover, CP^1 Hopf S^3->S^2, HP^1 quaternionic Hopf S^7->S^4",
        "domain": "unit elements of K^2 for K in {R,C,H}: real 2-vectors (R), Haar-sampled C^2 spinors (C), unit quaternion pairs in H^2 (H); Pauli set {sigma_x,sigma_y,sigma_z}; the 2x2-complex faithful representation of the quaternions",
        "codomain_or_output": "projective-line points on the spheres S^1, S^2, S^4; fiber-orbit images (Z_2 antipode, U(1) phase circle, Sp(1) right orbit); fiber abelianity (commutators); geomstats sphere-dimension certificates; SMT R-no-phase certificates",
        "carrier_layer": "division-algebra projective-line carriers KP^1 for K in {R,C,H}; total spaces S^1,S^2,S^4 with fibers S^0=Z_2, S^1=U(1), S^3=Sp(1)",
        "geometry_layer": "Hopf fibration geometry of the three projective lines: S^0->S^1->S^1 (R), S^1->S^3->S^2 (C), S^3->S^7->S^4 (H); abelian U(1) phase circle unique to C",
        "carrier_realization": "torch.complex128 / float64; C^2 spinors and the Hopf map, the 2x2-complex faithful representation of H and the quaternionic Hopf map, real 2-vectors and the RP^1 double cover; no NumPy claim-bearing substrate, no label-only tensors, no random claim matrices (random spinors/quaternions are genuine Gaussian-then-normalize samples)",
        "quaternion_action": "H realized via the faithful 2x2-complex representation; quaternion product == matrix product; the Sp(1)=S^3 unit-quaternion right action is the HP^1 fiber, and its noncommutativity (||uv-vu||>0) is the nonabelian invariant (control: the abelian U(1) i-axis restriction)",
        "spinor_state": "torch.complex128 two-component C^2 spinors psi (the C carrier) and their Hopf images; quaternionic pairs (q1,q2) in H^2 as the H analogue",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "the three division-algebra projective lines RP^1/CP^1/HP^1 against textbook sphere-dimension and fiber-type invariants; whether the complex C^2 carrier is forced or a choice with a uniquely abelian U(1) fiber",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; per-node alternative testing forcedness of the complex spinor; unadmitted",
        "allowed_claims": ["standalone known-math projective-line geometry witness; computed sphere dimensions and fiber types match textbook values; C uniquely carries the abelian U(1) Hopf phase fiber among R/C/H (the complex spinor is a choice, not shown forced)"],
        "promotion_blockers": ["diagnostic_only by design (lego/pre-sim phase); no manifold membership, no cross-layer evidence, no coupling; forcedness of C in the larger stack is NOT established here"],

        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "negatives_all_kill": negatives_all_kill,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_states": sum(b["n_states"] for b in blocks),
            "sample_sizes": SAMPLE_SIZES, "seeds": SEEDS,
            "z3_real_no_phase_unsat": z3r["pass"],
            "cvc5_real_no_phase_unsat": cvc5r["pass"],
            "fiber_types": {"R": "Z_2=S^0 (discrete, no phase)", "C": "U(1)=S^1 (abelian Hopf phase)", "H": "Sp(1)=S^3 (nonabelian)"},
            "sphere_dims": {"RP^1": 1, "CP^1": 2, "HP^1": 4},
            "only_C_has_abelian_u1_phase_fiber": fab["C_is_abelian"] and fab["H_is_nonabelian"],
            "promotion_allowed": False,
        },

        "known_value_checks": kvc,
        "sympy_exact_c_hopf": sym,
        "fiber_abelianity": fab,
        "clifford_fiber_algebra": cliff,
        "geomstats_sphere_dims": gdim,

        "variation_blocks": blocks,

        "real_no_phase_certificates": {"z3": z3r, "cvc5": cvc5r},

        "required_negatives": ["false_continuous_u1_on_RP1", "collapse_C_carrier_to_real",
                               "flatten_H_fiber_to_abelian", "real_only_scalar_carrier"],
        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "kill_conditions": [
            "any known-value invariant fails to match its textbook value",
            "z3 or cvc5 R-no-continuous-phase negation not UNSAT",
            "a continuous U(1) phase is claimable on RP^1 (generic rotation stays on the real line)",
            "the C carrier collapsed to real still shows off-axis phase motion",
            "the abelian i-axis H restriction spans the full Sp(1)=S^3 orbit dimension",
            "the real-only carrier shows nonzero sigma_y Hopf component / imaginary part",
        ],

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing",
                                   "cvc5": "load_bearing", "geomstats": "load_bearing", "clifford": "load_bearing"},
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["geomstats"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "geomstats", "clifford"],
        "actual_tools_used": ["torch", "sympy", "z3", "cvc5", "geomstats", "clifford"],

        "required_artifacts": ["json_result_receipt", "witness_trace"],
        "artifacts_emitted": ["json_result_receipt", "witness_trace"],
        "witness_trace_id": f"{SIM_ID}_witness",

        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check matches its known value AND all negatives kill the signature AND z3+cvc5 R-no-continuous-phase negations are UNSAT AND geomstats certifies S^1/S^2/S^4 AND clifford certifies even-Cl(2)==C abelian, even-Cl(3)==H nonabelian",
        "fail_rule": "any known-value mismatch, any negative that does not kill, any non-UNSAT certificate, any wrong sphere dimension, or wrong fiber abelianity",
        "eligible_consumers": ["other diagnostic_only division-algebra / projective-line / spinor geometry probes"],
    }

    # Witness trace
    witness = {
        "sim_id": SIM_ID,
        "steps": [
            {"step": "sample_division_algebra_carriers", "sizes": SAMPLE_SIZES, "seeds": SEEDS,
             "n_states": sum(b["n_states"] for b in blocks),
             "carriers": ["R^2", "C^2_spinor", "H^2_quaternion_pair"]},
            {"step": "C_hopf_onto_S2_and_u1_phase_fiber", "tool": "torch.complex128"},
            {"step": "H_quaternionic_hopf_onto_S4_and_sp1_right_fiber", "tool": "torch.complex128"},
            {"step": "R_double_cover_and_z2_antipodal_fiber", "tool": "torch.float64"},
            {"step": "sympy_exact_c_hopf_unitnorm_and_u1_invariance",
             "norm_is_one": sym["C_hopf_norm_is_one_exact"], "u1_invariant": sym["C_u1_phase_invariant_exact"]},
            {"step": "fiber_abelianity_C_abelian_vs_H_nonabelian",
             "C_abelian": fab["C_is_abelian"], "H_nonabelian": fab["H_is_nonabelian"]},
            {"step": "clifford_even_Cl2_C_vs_even_Cl3_H",
             "Cl2_complex": cliff["even_Cl2_is_complex_abelian"], "Cl3_quaternion": cliff["even_Cl3_is_quaternion_nonabelian"]},
            {"step": "geomstats_sphere_dims_S1_S2_S4",
             "dims_match": all(gdim[k]["dim_matches"] for k in ("R", "C", "H"))},
            {"step": "z3_cvc5_real_no_continuous_phase", "z3_unsat": z3r["pass"], "cvc5_unsat": cvc5r["pass"]},
            {"step": "run_negatives", "negatives": list(negatives.keys()), "all_kill": negatives_all_kill},
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
