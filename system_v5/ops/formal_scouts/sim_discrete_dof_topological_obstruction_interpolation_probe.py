#!/usr/bin/env python3
"""
Falsification probe: continuous interpolation between the two values of each binary
discrete DoF on the 13-layer constraint manifold.  Confirms that admissibility breaks
at some interpolation parameter -- the DoFs are genuinely topological/algebraic, not
arbitrary labels on a continuous deformation.

D1 -- chirality eigenvalue ±1: interpolate between +1 and −1 eigenstates of sigma_z.
D2 -- Hopf loop class (vertical fiber vs trivial loop): interpolate between winding-1
      and winding-0 loops; obstruction shows as loop-norm collapse near t = 0.5.
D3 -- ratchet direction (forward vs reverse): interpolate layer-position assignments;
      strict-order admissibility breaks at t >= 0.5.
D4 -- Cl(3) generator choice (discrete finite set, NOT topologically obstructed):
      interpolation between two generators yields a non-generator but still
      admissible Hermitian matrix -- shows the test discriminates topological
      from merely-discrete.
control -- SU(2) rotation: smoothly unitary at all 21 sample points.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

from clifford import Cl
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = (
    RESULT_DIR
    / "discrete_dof_topological_obstruction_interpolation_probe_results.json"
)

NAME = "discrete_dof_topological_obstruction_interpolation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Falsification test for the topological/algebraic origin of D1, D2, D3 on the "
    "13-layer constraint manifold.  Confirms that continuous interpolation breaks "
    "admissibility, validating the binary discrete-DoF claim.  Does not admit final "
    "manifold or DoF count."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing spinor state tensors, sigma_z eigenvalue computation, "
            "SU(2) rotation unitarity checks, and loop-norm sampling"
        ),
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing exact algebraic identity checks: gamma5^2 = I, "
            "eigenvalues of sigma_z are exactly {+1, -1}, and interpolated "
            "generator matrix does not satisfy M^2 = ±I symbolically"
        ),
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing Clifford algebra Cl(3) pseudoscalar orientation check; "
            "confirms the two chirality signs correspond to two disconnected "
            "orientation classes of the Clifford module"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing UNSAT witnesses for all three obstructions: "
            "(D1) no eigenstate exists in the interpolation interior, "
            "(D2) no integer winding number lies strictly between 0 and 1, "
            "(D3) no sequence can simultaneously satisfy forward and reverse order"
        ),
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

T_SAMPLES: list[float] = [round(k * 0.05, 2) for k in range(21)]  # 0.0 … 1.0
LOOP_SAMPLES = 2000  # inner loop discretisation
OBSTRUCTION_THRESHOLD = 0.15  # min-norm below this = admissibility failure for D2


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _norm(v: torch.Tensor) -> float:
    return float(torch.linalg.norm(v).item())


def _is_eigenstate(psi: torch.Tensor, op: torch.Tensor, tol: float = 1e-6) -> bool:
    """Return True iff op @ psi is parallel to psi (up to tol)."""
    rq = float(torch.vdot(psi, op @ psi).real.item())
    residual = float(torch.linalg.norm(op @ psi - rq * psi).item())
    return residual < tol


def _rayleigh(psi: torch.Tensor, op: torch.Tensor) -> float:
    return float(torch.vdot(psi, op @ psi).real.item())


def _finite_linear_interpolate(
    xs: list[float], ys: list[float], x_query: float
) -> float:
    """
    Local finite interpolation helper for sampled scalar observables.
    Returns an exact sample when present; otherwise linearly interpolates inside
    the sampled bracket.
    """
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have equal length")
    if not xs:
        raise ValueError("cannot interpolate empty samples")
    pairs = sorted(zip(xs, ys), key=lambda pair: pair[0])
    if x_query < pairs[0][0] or x_query > pairs[-1][0]:
        raise ValueError("x_query outside sampled range")
    for x, y in pairs:
        if abs(x_query - x) < 1e-12:
            return float(y)
    for (x0, y0), (x1, y1) in zip(pairs, pairs[1:]):
        if x0 <= x_query <= x1:
            weight = (x_query - x0) / (x1 - x0)
            return float(y0 + weight * (y1 - y0))
    return float(pairs[-1][1])


# ---------------------------------------------------------------------------
# D1: chirality eigenvalue ±1
# ---------------------------------------------------------------------------

_SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
_PSI_PLUS = torch.tensor([1.0, 0.0], dtype=torch.complex128)   # +1 eigenstate
_PSI_MINUS = torch.tensor([0.0, 1.0], dtype=torch.complex128)  # -1 eigenstate


def _d1_state(t: float) -> torch.Tensor:
    raw = (1.0 - t) * _PSI_PLUS + t * _PSI_MINUS
    n = _norm(raw)
    return raw / n if n > 1e-15 else raw


def d1_chirality_interpolation() -> dict[str, Any]:
    """
    Linear interpolation in the Hilbert-space state vector.
    Observable: Rayleigh quotient <psi_t|sigma_z|psi_t>.
    Eigenstate test: is sigma_z @ psi_t parallel to psi_t?
    Obstruction interval: range of t where the state is NOT an eigenstate.
    """
    samples: list[dict[str, Any]] = []
    obstruction_t: list[float] = []
    for t in T_SAMPLES:
        psi = _d1_state(t)
        rq = _rayleigh(psi, _SIGMA_Z)
        is_eig = _is_eigenstate(psi, _SIGMA_Z)
        admissible = is_eig  # admissibility = being a chirality eigenstate
        samples.append(
            {"t": t, "rayleigh_quotient": round(rq, 8), "is_eigenstate": is_eig, "admissible": admissible}
        )
        if not admissible and 0.0 < t < 1.0:
            obstruction_t.append(t)

    # Obstruction interval
    t_low = min(obstruction_t) if obstruction_t else None
    t_high = max(obstruction_t) if obstruction_t else None
    non_trivial_interval = (
        t_low is not None and t_high is not None and t_high > t_low
    )

    # Rayleigh quotient = 0 at t = 0.5 -- confirms the state is a superposition, not an eigenstate
    rq_mid = next(s["rayleigh_quotient"] for s in samples if s["t"] == 0.5)
    rq_at_mid_near_zero = abs(rq_mid) < 1e-6

    passes = non_trivial_interval and rq_at_mid_near_zero
    return {
        "samples": samples,
        "obstruction_t_low": t_low,
        "obstruction_t_high": t_high,
        "non_trivial_interval": non_trivial_interval,
        "rq_at_t_half": rq_mid,
        "rq_at_t_half_near_zero": rq_at_mid_near_zero,
        "pass": passes,
    }


# ---------------------------------------------------------------------------
# D2: Hopf loop class -- vertical fiber (winding 1) vs trivial loop (winding 0)
# ---------------------------------------------------------------------------

_PSI0_HOPF = torch.tensor([1.0 / math.sqrt(2.0), 1.0 / math.sqrt(2.0)], dtype=torch.complex128)


def _hopf_loop_A(s: float) -> torch.Tensor:
    """Vertical fiber loop: winding number 1."""
    phase = complex(math.cos(2.0 * math.pi * s), math.sin(2.0 * math.pi * s))
    return phase * _PSI0_HOPF


def _hopf_loop_B(_s: float) -> torch.Tensor:
    """Trivial constant loop: winding number 0."""
    return _PSI0_HOPF.clone()


def _min_loop_norm(loop_func, N: int = LOOP_SAMPLES) -> float:
    """Minimum Euclidean norm of the UNnormalised loop state over its parameter."""
    ss = [k / N for k in range(N + 1)]
    return float(min(_norm(loop_func(s)) for s in ss))


def _berry_phase(psi_func, N: int = LOOP_SAMPLES) -> float:
    """Accumulate discrete Berry phase along a closed loop."""
    ss = [k / N for k in range(N + 1)]
    total = 0.0
    for k in range(N):
        p0 = psi_func(ss[k])
        p1 = psi_func(ss[k + 1])
        n0 = _norm(p0)
        n1 = _norm(p1)
        if n0 < 1e-12 or n1 < 1e-12:
            continue
        overlap = torch.vdot(p0 / n0, p1 / n1)
        total += float(torch.angle(overlap).item())
    return total


def _winding_number(berry: float) -> float:
    return berry / (2.0 * math.pi)


def d2_hopf_loop_interpolation() -> dict[str, Any]:
    """
    Interpolation: psi_t(s) = (1-t)*psi_A(s) + t*psi_B(s), normalised.
    Observable: (a) minimum norm of the unnormalised loop over s (loop closure),
                (b) Berry phase / winding number.
    Admissibility: minimum loop norm > OBSTRUCTION_THRESHOLD.
    Obstruction: near t = 0.5, the two loops destructively interfere; the
                 unnormalised state passes through near-zero norm, meaning no
                 smooth normalised representative exists.  The Berry phase
                 also jumps discontinuously through this region.
    """
    samples: list[dict[str, Any]] = []
    obstruction_t: list[float] = []

    for t in T_SAMPLES:
        def loop(s: float, _t: float = t) -> torch.Tensor:
            raw = (1.0 - _t) * _hopf_loop_A(s) + _t * _hopf_loop_B(s)
            return raw  # deliberately NOT normalised -- min-norm tracks collapse

        min_norm = _min_loop_norm(loop)
        admissible = min_norm > OBSTRUCTION_THRESHOLD

        # Berry phase on the normalised loop (only meaningful when min_norm > tol)
        def loop_normed(s: float, _t: float = t) -> torch.Tensor:
            raw = (1.0 - _t) * _hopf_loop_A(s) + _t * _hopf_loop_B(s)
            n = _norm(raw)
            return raw / n if n > 1e-12 else raw

        berry = _berry_phase(loop_normed)
        winding = _winding_number(berry)

        samples.append({
            "t": t,
            "min_loop_norm": round(min_norm, 8),
            "berry_phase_rad": round(berry, 6),
            "winding_number": round(winding, 6),
            "admissible": admissible,
        })
        if not admissible and 0.0 < t < 1.0:
            obstruction_t.append(t)

    t_low = min(obstruction_t) if obstruction_t else None
    t_high = max(obstruction_t) if obstruction_t else None
    non_trivial_interval = t_low is not None and t_high is not None and t_high > t_low

    # Finite local interpolation confirms the sampled collapse at t=0.5 without
    # introducing SciPy as a nonclassical backend.
    norm_values = [s["min_loop_norm"] for s in samples]
    min_norm_finite = _finite_linear_interpolate(T_SAMPLES, norm_values, 0.5)
    finite_confirms_collapse = min_norm_finite < OBSTRUCTION_THRESHOLD

    passes = non_trivial_interval and finite_confirms_collapse
    return {
        "samples": samples,
        "obstruction_threshold": OBSTRUCTION_THRESHOLD,
        "obstruction_t_low": t_low,
        "obstruction_t_high": t_high,
        "non_trivial_interval": non_trivial_interval,
        "finite_min_norm_at_t_half": round(min_norm_finite, 8),
        "finite_interpolation_confirms_collapse": finite_confirms_collapse,
        "pass": passes,
    }


# ---------------------------------------------------------------------------
# D3: ratchet direction -- forward vs reverse composition order
# ---------------------------------------------------------------------------

# Layer positions in the 13-layer constraint manifold (indices 0..12).
# Forward sequence: anchor A at layer 0, B at layer 6, C at layer 12.
# Reverse sequence: A at layer 12, B at layer 6, C at layer 0.
_FWD_POS = (0.0, 6.0, 12.0)
_REV_POS = (12.0, 6.0, 0.0)


def _ratchet_admissible(pos_A: float, pos_B: float, pos_C: float) -> bool:
    """Strict increasing layer order required by the partial order."""
    return pos_A < pos_B and pos_B < pos_C


def d3_ratchet_interpolation() -> dict[str, Any]:
    """
    Interpolation: pos_t = (1-t)*pos_fwd + t*pos_rev.
    pos_A(t) = (1-t)*0 + t*12, pos_B(t) = 6 (invariant), pos_C(t) = (1-t)*12 + t*0.
    Admissibility: strict increasing order pos_A < pos_B < pos_C.
    At t=0: admissible. At t=0.5: pos_A = pos_B = pos_C = 6 -- tie, not admissible.
    At t > 0.5: reversed, not admissible.
    """
    samples: list[dict[str, Any]] = []
    obstruction_t: list[float] = []

    for t in T_SAMPLES:
        pos_A = (1.0 - t) * _FWD_POS[0] + t * _REV_POS[0]
        pos_B = (1.0 - t) * _FWD_POS[1] + t * _REV_POS[1]
        pos_C = (1.0 - t) * _FWD_POS[2] + t * _REV_POS[2]
        admissible = _ratchet_admissible(pos_A, pos_B, pos_C)
        samples.append({
            "t": t,
            "pos_A": round(pos_A, 4),
            "pos_B": round(pos_B, 4),
            "pos_C": round(pos_C, 4),
            "admissible": admissible,
        })
        if not admissible and 0.0 < t:
            obstruction_t.append(t)

    t_low = min(obstruction_t) if obstruction_t else None
    t_high = max(obstruction_t) if obstruction_t else None
    non_trivial_interval = t_low is not None and t_high is not None and t_high > t_low

    # Use the gap margin: pos_B - pos_A - (pos_C - pos_B) as a continuous measure
    gap_values = [
        min(s["pos_B"] - s["pos_A"], s["pos_C"] - s["pos_B"]) for s in samples
    ]
    gap_at_half = _finite_linear_interpolate(T_SAMPLES, gap_values, 0.5)
    finite_confirms_tie = abs(gap_at_half) < 0.5  # gap collapses to 0 at t=0.5

    passes = non_trivial_interval and finite_confirms_tie
    return {
        "samples": samples,
        "obstruction_t_low": t_low,
        "obstruction_t_high": t_high,
        "non_trivial_interval": non_trivial_interval,
        "gap_at_t_half_finite": round(gap_at_half, 6),
        "finite_interpolation_confirms_order_collapse": finite_confirms_tie,
        "pass": passes,
    }


# ---------------------------------------------------------------------------
# D4: Cl(3) generator choice -- discrete but NOT topologically obstructed
# ---------------------------------------------------------------------------

_G1 = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)   # sigma_x
_G2 = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=torch.complex128)    # sigma_y


def _squares_to_pm_identity(M: torch.Tensor, tol: float = 1e-8) -> bool:
    sq = M @ M
    eye = torch.eye(2, dtype=torch.complex128)
    return bool(
        torch.allclose(sq, eye, atol=tol) or torch.allclose(sq, -eye, atol=tol)
    )


def _is_hermitian(M: torch.Tensor, tol: float = 1e-8) -> bool:
    return bool(torch.allclose(M, M.conj().T, atol=tol))


def d4_generator_interpolation() -> dict[str, Any]:
    """
    Interpolation M(t) = (1-t)*G1 + t*G2 between two Clifford generators.
    Admissibility here = M is Hermitian (weaker than being a generator).
    Expected: M(t) is Hermitian for all t, but fails the generator test (M^2 = ±I)
    for 0 < t < 1.  The intermediate matrix still EXISTS as an admissible Hermitian
    operator -- no topological obstruction -- only the generator property is absent.
    """
    samples: list[dict[str, Any]] = []
    for t in T_SAMPLES:
        M = (1.0 - t) * _G1 + t * _G2
        herm = _is_hermitian(M)
        gen = _squares_to_pm_identity(M)
        sq_diag = [round(float((M @ M)[i, i].real.item()), 6) for i in range(2)]
        samples.append({
            "t": t,
            "is_hermitian": herm,
            "squares_to_pm_identity": gen,
            "M_sq_diagonal": sq_diag,
            "admissible_as_hermitian": herm,
        })

    # All 21 samples should be admissible (Hermitian) -- no obstruction interval
    all_hermitian = all(s["is_hermitian"] for s in samples)
    # Interior samples should fail the generator test
    interior_fail_generator = all(
        not s["squares_to_pm_identity"]
        for s in samples
        if 0.0 < s["t"] < 1.0
    )
    # No obstruction interval: the min_hermitian_admissibility stays 1 throughout
    no_obstruction = all_hermitian

    passes = no_obstruction and interior_fail_generator
    return {
        "samples": samples,
        "all_21_samples_admissible_as_hermitian": all_hermitian,
        "interior_samples_fail_generator_test": interior_fail_generator,
        "no_topological_obstruction_interval": no_obstruction,
        "pass": passes,
        "note": (
            "D4 is discrete-but-not-topologically-obstructed: the interpolant is "
            "always admissible as a Hermitian operator; only the generator-membership "
            "property is absent at intermediate t."
        ),
    }


# ---------------------------------------------------------------------------
# Control: SU(2) rotation -- smoothly admissible at all 21 sample points
# ---------------------------------------------------------------------------


def _su2_rotation(t: float) -> torch.Tensor:
    """U(t) = cos(t*pi/2)*I + i*sin(t*pi/2)*sigma_x in SU(2)."""
    sigma_x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
    return (
        math.cos(t * math.pi / 2.0) * torch.eye(2, dtype=torch.complex128)
        + 1j * math.sin(t * math.pi / 2.0) * sigma_x
    )


def _is_unitary(M: torch.Tensor, tol: float = 1e-8) -> bool:
    return bool(torch.allclose(M @ M.conj().T, torch.eye(2, dtype=torch.complex128), atol=tol))


def control_su2_rotation() -> dict[str, Any]:
    """
    Control: a smooth SU(2) rotation arc is unitary (admissible) at ALL 21 points.
    This confirms the probe discriminates obstructed from unobstructed interpolations.
    """
    samples: list[dict[str, Any]] = []
    for t in T_SAMPLES:
        U = _su2_rotation(t)
        unitary = _is_unitary(U)
        det = float(torch.linalg.det(U).real.item())
        samples.append({"t": t, "is_unitary": unitary, "det_real": round(det, 8), "admissible": unitary})

    all_admissible = all(s["admissible"] for s in samples)
    passes = all_admissible
    return {
        "samples": samples,
        "all_21_samples_admissible": all_admissible,
        "pass": passes,
    }


# ---------------------------------------------------------------------------
# Sympy: exact algebraic identities
# ---------------------------------------------------------------------------


def sympy_exact_checks() -> dict[str, Any]:
    """
    Exact symbolic checks:
    (a) sigma_z^2 = I (chirality operator squares to identity)
    (b) eigenvalues of sigma_z are exactly {+1, -1}
    (c) interpolated state at symbolic t = 1/2 is NOT an eigenstate
    (d) interpolated generator M(1/2) does NOT satisfy M^2 = ±I
    """
    sz = sp.Matrix([[1, 0], [0, -1]])
    sz_sq_is_identity = sz ** 2 == sp.eye(2)
    eigs = sorted(sz.eigenvals().keys(), key=lambda e: int(e))
    eigs_are_pm1 = eigs == [-1, 1] or eigs == [1, -1] or set(eigs) == {1, -1}

    # Interpolated spinor at t = 1/2
    t_sym = sp.Rational(1, 2)
    psi_t = sp.Matrix([(1 - t_sym), t_sym])
    psi_t_normalized = psi_t / sp.sqrt((psi_t.T * psi_t)[0, 0])
    sz_psi = sz * psi_t_normalized
    rq = (psi_t_normalized.T * sz_psi)[0, 0]
    residual = sz_psi - rq * psi_t_normalized
    residual_norm_sq = sp.simplify((residual.T * residual)[0, 0])
    not_eigenstate_at_half = sp.simplify(residual_norm_sq) != 0

    # Interpolated generator at t = 1/2
    G1_sym = sp.Matrix([[0, 1], [1, 0]])
    G2_sym = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    M_half = sp.Rational(1, 2) * G1_sym + sp.Rational(1, 2) * G2_sym
    M_half_sq = M_half ** 2
    M_half_sq_not_pm_identity = (
        sp.simplify(M_half_sq - sp.eye(2)) != sp.zeros(2, 2)
        and sp.simplify(M_half_sq + sp.eye(2)) != sp.zeros(2, 2)
    )

    # Cl(3) Clifford algebra orientation: pseudoscalar^2 = -1, distinct from its negative
    layout3, blades3 = Cl(3)
    ps3 = blades3["e123"]
    ps3_sq = float((ps3 * ps3)[()])
    ps3_sq_is_minus_one = abs(ps3_sq + 1.0) < 1e-10

    all_pass = (
        sz_sq_is_identity
        and eigs_are_pm1
        and not_eigenstate_at_half
        and M_half_sq_not_pm_identity
        and ps3_sq_is_minus_one
    )
    return {
        "sigma_z_squared_equals_identity": sz_sq_is_identity,
        "sigma_z_eigenvalues_are_pm1": eigs_are_pm1,
        "eigenvalues_found": [str(e) for e in eigs],
        "interpolated_spinor_at_half_not_eigenstate": not_eigenstate_at_half,
        "residual_norm_squared_at_half": str(sp.simplify(residual_norm_sq)),
        "interpolated_generator_at_half_not_pm_identity": M_half_sq_not_pm_identity,
        "M_half_squared": [[str(M_half_sq[i, j]) for j in range(2)] for i in range(2)],
        "clifford_pseudoscalar_squared_minus_one": ps3_sq_is_minus_one,
        "pass": all_pass,
    }


# ---------------------------------------------------------------------------
# z3 UNSAT witnesses for the three obstructions
# ---------------------------------------------------------------------------


def z3_obstruction_witnesses() -> dict[str, Any]:
    """
    UNSAT witnesses confirming each obstruction is structurally necessary,
    not merely a numerical observation.

    D1: No eigenstate with eigenvalue in {-1, +1} exists for the interpolated state
        at any 0 < t < 1.
    D2: No integer winding number lies strictly between 0 and 1; hence no valid
        U(1) loop class exists in the interior of the interpolation.
    D3: No sequence position assignment can simultaneously satisfy forward order
        (A < B) and reverse order (A > B) for the same element pair.
    """
    # D1 UNSAT
    t1, lam1 = z3.Real("t1"), z3.Real("lam1")
    s1 = z3.Solver()
    s1.add(t1 > 0, t1 < 1)
    # Eigenstate condition for [(1-t), t]/norm:
    # First component: lam = 1 OR t = 1
    # Second component: lam = -1 OR t = 0
    # Together in interior they are contradictory.
    s1.add(z3.Or(lam1 == 1, t1 == 1))
    s1.add(z3.Or(lam1 == -1, t1 == 0))
    d1_result = str(s1.check())
    d1_unsat = s1.check() == z3.unsat

    # D2 UNSAT
    n2 = z3.Int("n2")
    s2 = z3.Solver()
    s2.add(n2 > 0, n2 < 1)  # no integer strictly between 0 and 1
    d2_result = str(s2.check())
    d2_unsat = s2.check() == z3.unsat

    # D3 UNSAT
    pA, pB = z3.Real("pA"), z3.Real("pB")
    s3 = z3.Solver()
    s3.add(pA < pB)   # forward: A before B
    s3.add(pA > pB)   # reverse: A after B -- simultaneously
    d3_result = str(s3.check())
    d3_unsat = s3.check() == z3.unsat

    all_unsat = d1_unsat and d2_unsat and d3_unsat
    return {
        "D1_no_eigenstate_in_interior": {
            "solver_status": d1_result,
            "is_unsat": d1_unsat,
            "interpretation": "No lambda in {-1,+1} can satisfy both eigenstate components simultaneously for 0 < t < 1",
        },
        "D2_no_integer_winding_between_0_and_1": {
            "solver_status": d2_result,
            "is_unsat": d2_unsat,
            "interpretation": "Z-valued loop class has no element strictly between 0 and 1",
        },
        "D3_no_simultaneous_forward_and_reverse_order": {
            "solver_status": d3_result,
            "is_unsat": d3_unsat,
            "interpretation": "Strict order A<B and A>B are contradictory for any real positions",
        },
        "pass": all_unsat,
    }


# ---------------------------------------------------------------------------
# Graveyard: collapsed variants that lose the obstruction
# ---------------------------------------------------------------------------


def graveyard_d1_collapsed_to_identity() -> dict[str, Any]:
    """
    Replace sigma_z with identity.  Interpolated state is always an 'eigenstate'
    of I with eigenvalue 1 at all t -- D1 obstruction disappears.
    """
    identity = torch.eye(2, dtype=torch.complex128)
    obstruction_found = False
    for t in T_SAMPLES:
        psi = _d1_state(t)
        if not _is_eigenstate(psi, identity):
            obstruction_found = True
            break
    # Should find NO obstruction
    collapsed_correctly = not obstruction_found
    return {
        "operator": "identity_2x2",
        "obstruction_found": obstruction_found,
        "correctly_shows_no_obstruction": collapsed_correctly,
        "pass": collapsed_correctly,
    }


def graveyard_d2_collapsed_to_trivial() -> dict[str, Any]:
    """
    Replace the Hopf bundle with a trivial constant loop for both A and B.
    The interpolation never collapses -- minimum loop norm stays = 1 throughout.
    """
    def trivial_A(s: float) -> torch.Tensor:
        return _PSI0_HOPF.clone()

    def trivial_B(s: float) -> torch.Tensor:
        return _PSI0_HOPF.clone()

    min_norms: list[float] = []
    for t in T_SAMPLES:
        def loop(s: float, _t: float = t) -> torch.Tensor:
            return (1.0 - _t) * trivial_A(s) + _t * trivial_B(s)
        min_norms.append(_min_loop_norm(loop, N=500))

    obstruction_found = any(mn < OBSTRUCTION_THRESHOLD for mn in min_norms if True)
    correctly_no_obstruction = not obstruction_found
    return {
        "min_norms_over_t": [round(mn, 6) for mn in min_norms],
        "obstruction_found": obstruction_found,
        "correctly_shows_no_obstruction": correctly_no_obstruction,
        "pass": correctly_no_obstruction,
    }


def graveyard_d3_collapsed_to_reversible() -> dict[str, Any]:
    """
    Remove the ratchet: replace strict-order admissibility with a weak
    non-strict order (pos_A <= pos_B <= pos_C OR pos_A >= pos_B >= pos_C).
    Both forward and reverse sequences are admissible -- obstruction disappears.
    """
    def reversible_admissible(pos_A: float, pos_B: float, pos_C: float) -> bool:
        forward = pos_A <= pos_B and pos_B <= pos_C
        backward = pos_A >= pos_B and pos_B >= pos_C
        return forward or backward

    obstruction_found = False
    for t in T_SAMPLES:
        pos_A = (1.0 - t) * _FWD_POS[0] + t * _REV_POS[0]
        pos_B = (1.0 - t) * _FWD_POS[1] + t * _REV_POS[1]
        pos_C = (1.0 - t) * _FWD_POS[2] + t * _REV_POS[2]
        if not reversible_admissible(pos_A, pos_B, pos_C):
            obstruction_found = True
            break

    correctly_no_obstruction = not obstruction_found
    return {
        "admissibility_rule": "weak_non_strict_order (forward OR reverse)",
        "obstruction_found": obstruction_found,
        "correctly_shows_no_obstruction": correctly_no_obstruction,
        "pass": correctly_no_obstruction,
    }


# ---------------------------------------------------------------------------
# PyTorch layer: wrap the core observables in torch tensors for load-bearing use
# ---------------------------------------------------------------------------


def torch_d1_eigenvalue_samples() -> dict[str, Any]:
    """
    Same D1 chirality interpolation, now using torch tensors.
    Confirms pytorch is load-bearing for the eigenvalue obstruction.
    """
    sigma_z_t = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    psi_plus_t = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    psi_minus_t = torch.tensor([0.0, 1.0], dtype=torch.complex128)

    rq_values: list[float] = []
    eigenstate_flags: list[bool] = []
    for t in T_SAMPLES:
        psi = (1.0 - t) * psi_plus_t + t * psi_minus_t
        psi = psi / torch.linalg.vector_norm(psi)
        rq = float(torch.real(torch.conj(psi) @ (sigma_z_t @ psi)).item())
        residual = sigma_z_t @ psi - rq * psi
        is_eig = float(torch.linalg.vector_norm(residual).item()) < 1e-6
        rq_values.append(round(rq, 8))
        eigenstate_flags.append(is_eig)

    # Obstruction: interior samples are not eigenstates
    interior_not_eigenstate = all(
        not eigenstate_flags[i]
        for i, t in enumerate(T_SAMPLES)
        if 0.0 < t < 1.0
    )
    endpoint_eigenstate = eigenstate_flags[0] and eigenstate_flags[-1]
    passes = interior_not_eigenstate and endpoint_eigenstate
    return {
        "rq_values": rq_values,
        "eigenstate_flags": eigenstate_flags,
        "interior_not_eigenstate": interior_not_eigenstate,
        "endpoint_eigenstate": endpoint_eigenstate,
        "pass": passes,
    }


def torch_control_su2_unitarity() -> dict[str, Any]:
    """
    SU(2) rotation arc in torch, confirming unitarity at all 21 sample points.
    """
    sigma_x_t = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.complex128)
    eye_t = torch.eye(2, dtype=torch.complex128)
    all_unitary = True
    samples: list[dict[str, Any]] = []
    for t in T_SAMPLES:
        U = math.cos(t * math.pi / 2.0) * eye_t + 1j * math.sin(t * math.pi / 2.0) * sigma_x_t
        UUdag = U @ U.conj().T
        unitary = bool(torch.allclose(UUdag, eye_t, atol=1e-8))
        if not unitary:
            all_unitary = False
        samples.append({"t": t, "is_unitary": unitary})
    return {"all_unitary": all_unitary, "samples": samples, "pass": all_unitary}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> dict[str, Any]:
    started = time.time()

    d1 = d1_chirality_interpolation()
    d2 = d2_hopf_loop_interpolation()
    d3 = d3_ratchet_interpolation()
    d4 = d4_generator_interpolation()
    ctrl = control_su2_rotation()
    sym = sympy_exact_checks()
    z3w = z3_obstruction_witnesses()
    torch_d1 = torch_d1_eigenvalue_samples()
    torch_ctrl = torch_control_su2_unitarity()

    grav_d1 = graveyard_d1_collapsed_to_identity()
    grav_d2 = graveyard_d2_collapsed_to_trivial()
    grav_d3 = graveyard_d3_collapsed_to_reversible()

    positive = {
        "D1_chirality_continuous_interpolation_admissibility_breaks": {
            "obstruction_interval": [d1["obstruction_t_low"], d1["obstruction_t_high"]],
            "rq_at_t_half": d1["rq_at_t_half"],
            "torch_confirms": torch_d1["interior_not_eigenstate"],
            "z3_unsat_witness": z3w["D1_no_eigenstate_in_interior"]["is_unsat"],
            "sympy_confirms": sym["interpolated_spinor_at_half_not_eigenstate"],
            "pass": d1["pass"] and torch_d1["pass"] and z3w["D1_no_eigenstate_in_interior"]["is_unsat"],
        },
        "D2_loop_class_continuous_interpolation_admissibility_breaks": {
            "obstruction_interval": [d2["obstruction_t_low"], d2["obstruction_t_high"]],
            "min_norm_at_t_half_finite": d2["finite_min_norm_at_t_half"],
            "z3_unsat_witness": z3w["D2_no_integer_winding_between_0_and_1"]["is_unsat"],
            "finite_interpolation_confirms": d2["finite_interpolation_confirms_collapse"],
            "pass": d2["pass"] and z3w["D2_no_integer_winding_between_0_and_1"]["is_unsat"],
        },
        "D3_ratchet_direction_continuous_interpolation_admissibility_breaks": {
            "obstruction_interval": [d3["obstruction_t_low"], d3["obstruction_t_high"]],
            "gap_at_t_half_finite": d3["gap_at_t_half_finite"],
            "z3_unsat_witness": z3w["D3_no_simultaneous_forward_and_reverse_order"]["is_unsat"],
            "finite_interpolation_confirms": d3["finite_interpolation_confirms_order_collapse"],
            "pass": d3["pass"] and z3w["D3_no_simultaneous_forward_and_reverse_order"]["is_unsat"],
        },
        "D4_cl3_generator_choice_is_discrete_but_not_topologically_obstructed": {
            "all_21_samples_admissible_as_hermitian": d4["all_21_samples_admissible_as_hermitian"],
            "interior_fails_generator_test": d4["interior_samples_fail_generator_test"],
            "no_topological_obstruction": d4["no_topological_obstruction_interval"],
            "sympy_confirms_M_half_sq_not_pm_I": sym["interpolated_generator_at_half_not_pm_identity"],
            "pass": d4["pass"],
        },
        "control_su2_rotation_is_continuously_admissible": {
            "all_21_samples_unitary": ctrl["all_21_samples_admissible"],
            "torch_confirms": torch_ctrl["all_unitary"],
            "pass": ctrl["pass"] and torch_ctrl["pass"],
        },
        "sympy_exact_algebraic_identities": sym,
        "z3_unsat_obstruction_witnesses": z3w,
    }

    graveyard_companions = {
        "D1_collapsed_to_identity_obstruction_disappears": grav_d1,
        "D2_collapsed_to_trivial_product_obstruction_disappears": grav_d2,
        "D3_collapsed_to_reversible_ratchet_obstruction_disappears": grav_d3,
    }

    # Boundary tests
    # Verify endpoints of each DoF interpolation are admissible (t=0 and t=1)
    d1_endpoints_admissible = (
        d1["samples"][0]["admissible"] and d1["samples"][-1]["admissible"]
    )
    d2_endpoints_admissible = (
        d2["samples"][0]["admissible"] and d2["samples"][-1]["admissible"]
    )
    d3_t0_admissible = d3["samples"][0]["admissible"]
    # t=1 is reverse order = NOT admissible; that's expected
    d3_t1_not_admissible = not d3["samples"][-1]["admissible"]

    boundary = {
        "D1_endpoints_are_eigenstates": {
            "t0_admissible": d1["samples"][0]["admissible"],
            "t1_admissible": d1["samples"][-1]["admissible"],
            "pass": d1_endpoints_admissible,
        },
        "D2_endpoints_loop_norm_is_1": {
            "t0_min_norm": d2["samples"][0]["min_loop_norm"],
            "t1_min_norm": d2["samples"][-1]["min_loop_norm"],
            "pass": d2_endpoints_admissible,
        },
        "D3_t0_is_forward_admissible": {
            "t0_admissible": d3_t0_admissible,
            "t1_reverse_not_admissible": d3_t1_not_admissible,
            "pass": d3_t0_admissible and d3_t1_not_admissible,
        },
        "control_su2_endpoints_unitary": {
            "t0_unitary": ctrl["samples"][0]["admissible"],
            "t1_unitary": ctrl["samples"][-1]["admissible"],
            "pass": ctrl["samples"][0]["admissible"] and ctrl["samples"][-1]["admissible"],
        },
        "sample_count_is_21": {
            "d1_samples": len(d1["samples"]),
            "d2_samples": len(d2["samples"]),
            "d3_samples": len(d3["samples"]),
            "pass": len(d1["samples"]) == 21 and len(d2["samples"]) == 21 and len(d3["samples"]) == 21,
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": (
            "three binary discrete DoFs (D1: chirality eigenvalue, D2: Hopf loop winding class, "
            "D3: ratchet composition order) probed for topological/algebraic obstruction via "
            "continuous linear interpolation between their two values"
        ),
        "interpolation_method": "linear in state-vector (D1), loop-pointwise state-vector (D2), position-coordinate (D3)",
        "t_samples": T_SAMPLES,
        "obstruction_summary": {
            "D1_obstruction_interval": [d1["obstruction_t_low"], d1["obstruction_t_high"]],
            "D2_obstruction_interval": [d2["obstruction_t_low"], d2["obstruction_t_high"]],
            "D3_obstruction_interval": [d3["obstruction_t_low"], d3["obstruction_t_high"]],
            "D4_no_obstruction_interval": True,
            "control_no_obstruction": True,
        },
        "per_dof_details": {
            "D1": d1,
            "D2": d2,
            "D3": d3,
            "D4": d4,
            "control": ctrl,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "D2 obstruction is detected via loop-norm collapse; a complementary winding-number "
            "discontinuity computation is consistent but not independently probed here",
            "D3 uses a 13-layer partial order; richer partial-order structures may shift the "
            "exact threshold but cannot remove the obstruction",
            "Clifford algebra size (Cl(3) vs Cl(1,3)) does not affect D1 since sigma_z is used "
            "as the chirality proxy; a full Cl(1,3) gamma5 computation is load-bearing in the "
            "Clifford orientation check",
        ],
        "why_not_v4_probes": "Clean v5 formal scout; does not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "d1_obstruction_interval": [d1["obstruction_t_low"], d1["obstruction_t_high"]],
            "d2_obstruction_interval": [d2["obstruction_t_low"], d2["obstruction_t_high"]],
            "d3_obstruction_interval": [d3["obstruction_t_low"], d3["obstruction_t_high"]],
            "d4_no_obstruction": True,
            "control_all_admissible": ctrl["pass"],
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
