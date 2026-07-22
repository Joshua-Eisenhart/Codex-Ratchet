#!/usr/bin/env python3
"""Finite dimension-counting probe: real (rebit) vs complex (qubit) local tomography.

Object: Layer candidates are two finite state spaces built from the same rank-n
matrix skeleton -- REAL branch (rebit): n x n real symmetric density matrices;
COMPLEX branch (qubit): n x n complex Hermitian density matrices -- compared
against a single standard QIT reconstruction axiom, local tomography: the joint
state space of two systems is spanned by product (local) measurements, i.e.
d2 == d1 * d1 where d1, d2 are the real dimensions of the single- and two-system
state spaces respectively (Hardy 2001; Wootters 1990; Hardy & Wootters 2012,
"Limited Holism and Real-Vector-Space Quantum Theory"; Barnum & Wilce).

Dimension-counting convention: the STANDARD local-tomography count uses the real
vector space of general (possibly sub-normalized) Hermitian/symmetric operators,
NOT the trace-1-constrained affine slice (Bloch ball) -- an informationally
complete measurement must also estimate the trace/norm direction, so d1 = n^2
(complex Hermitian) or d1 = n(n+1)/2 (real symmetric), unconstrained. This is
the convention under which local tomography is a non-vacuous, correctly-defined
test. The trace-1 Bloch-ball numbers (d1=3 complex, d1=2 real) are reported
separately as "informal" numbers for comparison; under THAT convention the
naive d2==d1*d1 test does not hold for either branch (checked and reported
below), so it is not used as the axiom test.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". One reconstruction axiom (local
tomography) is not a full derivation of C; this probe does not settle a
canonical layer ordering or support bridge/axis/canonical promotion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp
from z3 import Function, RealSort, RealVal, Solver, sat, unsat

try:
    import cvc5
except ImportError:  # Recorded honestly below; z3 remains the primary proof leg.
    cvc5 = None


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-10

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact symbolic dimension counting (n^2, n(n+1)/2 formulas) over the rank-2 and rank-4 cases."},
    "numpy": {"tried": True, "used": True,
              "reason": "Finite sampled Hermitian/symmetric density matrices, PSD checks, and the forgetting-map witness pair."},
    "z3": {"tried": True, "used": True,
           "reason": "Primary SMT contradiction: one deterministic recovery of the real projection cannot return two distinct imaginary parts."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "jax": {"tried": False, "used": False,
            "reason": "Queued: not required for this finite dimension-counting probe; explicitly not run."},
    "julia": {"tried": False, "used": False,
              "reason": "Queued confirmation leg: not required for this probe; explicitly not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": None,
    "jax": None,
    "julia": None,
}


# --------------------------------------------------------------------------
# Dimension counting (symbolic, exact)
# --------------------------------------------------------------------------

def dimension_counts() -> dict[str, Any]:
    """Exact symbolic dimension counts for n=2 single systems and n1*n2=4 joint.

    complex Hermitian n x n: n^2 real parameters (unconstrained/subnormalized).
    real symmetric n x n: n(n+1)/2 real parameters (unconstrained/subnormalized).
    Bloch-ball (trace-1 constrained) figures are also computed for comparison.
    """
    n = sp.Integer(2)
    n_joint = n * n  # tensor product Hilbert-space dimension for two rank-2 systems

    complex_d1 = sp.simplify(n ** 2)
    complex_d2 = sp.simplify(n_joint ** 2)
    real_d1 = sp.simplify(n * (n + 1) / 2)
    real_d2 = sp.simplify(n_joint * (n_joint + 1) / 2)

    # Trace-1-constrained (Bloch-ball) numbers, reported for comparison only.
    complex_d1_trace1 = complex_d1 - 1
    complex_d2_trace1 = complex_d2 - 1
    real_d1_trace1 = real_d1 - 1
    real_d2_trace1 = real_d2 - 1

    return {
        "n": int(n), "n_joint": int(n_joint),
        "complex_d1": int(complex_d1), "complex_d2": int(complex_d2),
        "real_d1": int(real_d1), "real_d2": int(real_d2),
        "complex_d1_trace1": int(complex_d1_trace1), "complex_d2_trace1": int(complex_d2_trace1),
        "real_d1_trace1": int(real_d1_trace1), "real_d2_trace1": int(real_d2_trace1),
        "complex_local_tomography_trace1": bool(complex_d2_trace1 == complex_d1_trace1 ** 2),
        "real_local_tomography_trace1": bool(real_d2_trace1 == real_d1_trace1 ** 2),
    }


# --------------------------------------------------------------------------
# Forgetting map: complex Hermitian 2x2 -> real symmetric 2x2 (drop Im(off-diag))
# --------------------------------------------------------------------------

def complex_density(a: float, b: float, real_part: float, imag_part: float) -> np.ndarray:
    """(a, real_part+1j*imag_part; real_part-1j*imag_part, b), no trace/PSD enforcement here."""
    return np.array([[a, real_part + 1j * imag_part], [real_part - 1j * imag_part, b]], dtype=complex)


def is_psd_hermitian(rho: np.ndarray) -> bool:
    if not np.allclose(rho, rho.conj().T, atol=TOL):
        return False
    eigenvalues = np.linalg.eigvalsh(rho)
    return bool(np.all(eigenvalues >= -TOL)) and bool(abs(float(np.real(np.trace(rho))) - 1.0) < TOL)


def forget_imaginary(rho: np.ndarray) -> np.ndarray:
    """Project a complex Hermitian 2x2 matrix onto the real symmetric subspace."""
    return np.real(rho).astype(float)


def sampled_complex_states() -> list[np.ndarray]:
    """Finite grid of valid complex Hermitian trace-1 density matrices."""
    states: list[np.ndarray] = []
    for a in np.arange(0.1, 0.91, 0.2):
        b = 1.0 - a
        for re in np.arange(-0.4, 0.41, 0.2):
            for im in np.arange(-0.4, 0.41, 0.2):
                rho = complex_density(float(a), float(b), float(re), float(im))
                if is_psd_hermitian(rho):
                    states.append(rho)
    return states


def z3_noninjectivity() -> dict[str, str]:
    """Encode a deterministic recovery of Im(off-diag) from the real projection at a=b=1/2, re=1/4."""
    key = RealVal("1/4")  # stands in for (a, b, re) as a single collapsed real-valued input
    quarter = RealVal("1/4")
    tenth = RealVal("1/10")
    recover_im = Function("recover_im", RealSort(), RealSort())
    solver = Solver()
    # rho has im=0; rho_prime has im=1/10. Both have the identical real projection (key).
    solver.add(recover_im(key) == RealVal(0), recover_im(key) == tenth)
    verdict = solver.check()
    assert verdict == unsat
    relaxed = Solver()
    relaxed.add(recover_im(key) == RealVal(0))
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same real projection (a=b=1/2,re=1/4) must recover both Im=0 and Im=1/10",
            "result": str(verdict), "erased_constraint_result": str(relaxed_result)}


def cvc5_noninjectivity() -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function_sort = solver.mkFunctionSort([real], real)
        recover_im = solver.mkConst(function_sort, "recover_im")
        key = solver.mkReal("1/4")
        zero = solver.mkReal(0)
        tenth = solver.mkReal("1/10")
        app = lambda function: solver.mkTerm(cvc5.Kind.APPLY_UF, function, key)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recover_im), zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recover_im), tenth))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function_sort2 = relaxed.mkFunctionSort([real2], real2)
        recover_im2 = relaxed.mkConst(function_sort2, "recover_im_relaxed")
        key2 = relaxed.mkReal("1/4")
        zero2 = relaxed.mkReal(0)
        app2 = lambda function: relaxed.mkTerm(cvc5.Kind.APPLY_UF, function, key2)
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2(recover_im2), zero2))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same deterministic-recovery imaginary-part contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def matrix_payload(rho: np.ndarray) -> list[list[Any]]:
    return [[float(value.real) if abs(value.imag) < TOL else [float(value.real), float(value.imag)]
             for value in row] for row in rho]


def main() -> None:
    dims = dimension_counts()

    # --- one-way witness pair: same real projection, different original states ---
    rho = complex_density(0.5, 0.5, 0.25, 0.0)          # already real (im=0)
    rho_prime = complex_density(0.5, 0.5, 0.25, 0.1)    # im=0.1, PSD-checked below
    assert is_psd_hermitian(rho) and is_psd_hermitian(rho_prime)
    forgotten, forgotten_prime = forget_imaginary(rho), forget_imaginary(rho_prime)
    witness_valid = (not np.allclose(rho, rho_prime, atol=TOL)
                      and np.allclose(forgotten, forgotten_prime, atol=TOL))
    z3_result = z3_noninjectivity()
    cvc5_result = cvc5_noninjectivity()

    # --- control: phase-free complex states (im already 0) recover invertibly ---
    # Restrict to the sampled states with im=0 exactly (already real Hermitian).
    # On this subset, forget_imaginary is the identity map, so recovery is a
    # genuine recomputation (forgotten == original), not decorative.
    all_states = sampled_complex_states()
    phase_free_states = [s for s in all_states if abs(float(np.imag(s[0, 1]))) < TOL]
    assert len(phase_free_states) > 0, "control subset must be non-empty to be genuine"
    control_recovers = all(np.allclose(forget_imaginary(s), s, atol=TOL) for s in phase_free_states)
    control_invertible = bool(control_recovers)
    control_is_one_way = not control_invertible
    control_genuine = bool(len(phase_free_states) > 0 and control_invertible)

    # --- non-vacuity of the forgetting map over the full sampled grid ---
    proper_noninjective_witness = any(
        abs(float(np.imag(s[0, 1]))) > TOL for s in all_states
    ) and any(
        not np.allclose(a, b, atol=TOL) and np.allclose(forget_imaginary(a), forget_imaginary(b), atol=TOL)
        for a in all_states for b in all_states if a is not b
    )

    real_gap = dims["real_d2"] - dims["real_d1"] ** 2  # standard convention: 10-9=1

    complex_local_tomography = bool(dims["complex_d2"] == dims["complex_d1"] ** 2)
    real_local_tomography = bool(dims["real_d2"] == dims["real_d1"] ** 2)

    if complex_local_tomography and not real_local_tomography:
        selected_carrier = "complex"
    elif real_local_tomography and not complex_local_tomography:
        selected_carrier = "real"
    elif complex_local_tomography and real_local_tomography:
        selected_carrier = "both"
    else:
        selected_carrier = "neither"

    core_checks_ok = (
        complex_local_tomography and not real_local_tomography and real_gap == 1
        and witness_valid and proper_noninjective_witness
        and z3_result["result"] == "unsat" and z3_result["erased_constraint_result"] == "sat"
        and control_genuine and not control_is_one_way
    )
    verdict = "COMPLEX_EARNED_BY_TOMOGRAPHY" if core_checks_ok else "INCONCLUSIVE"
    if real_local_tomography and complex_local_tomography:
        verdict = "REAL_ALSO_PASSES"

    notes: list[str] = [
        "Finite dimension-counting probe over one reconstruction axiom (local tomography); not a full derivation of C.",
        "Standard convention: d1/d2 use the UNCONSTRAINED (subnormalized) Hermitian/symmetric operator-space dimension "
        "(n^2 complex, n(n+1)/2 real), not the trace-1 Bloch-ball slice -- this is the convention under which local "
        "tomography is a non-vacuous axiom (Hardy 2001; Hardy & Wootters 2012).",
        "Trace-1 (Bloch-ball) figures are reported separately for comparison (complex_d1_trace1, real_d1_trace1, etc); "
        "under that constrained convention the naive d2==d1*d1 test does NOT hold for either branch, so it is not used "
        "as the axiom test here.",
        "complex local tomography is an algebraic tautology at this n1=n2=2 case: (n1*n2)^2 = n1^2 * n2^2 identically.",
        "real local tomography fails by exactly one real dimension for two rebits (10 vs 9), the standard cited gap.",
    ]

    result = {
        "schema_version": "1.0",
        "real_d1": dims["real_d1"],
        "real_d2": dims["real_d2"],
        "real_local_tomography": real_local_tomography,
        "complex_d1": dims["complex_d1"],
        "complex_d2": dims["complex_d2"],
        "complex_local_tomography": complex_local_tomography,
        "dimension_arithmetic": {
            "n": dims["n"], "n_joint": dims["n_joint"],
            "complex_d1_formula": "n^2", "complex_d2_formula": "(n1*n2)^2 = n1^2*n2^2 (tautology)",
            "real_d1_formula": "n(n+1)/2", "real_d2_formula": "(n1*n2)(n1*n2+1)/2",
            "complex_d1_expected_from_formula": dims["complex_d1"],
            "complex_d2_from_d1_squared": dims["complex_d1"] ** 2,
            "real_d1_expected_from_formula": dims["real_d1"],
            "real_d2_from_d1_squared": dims["real_d1"] ** 2,
            "real_gap": real_gap,
            "trace1_bloch_ball_comparison": {
                "complex_d1_trace1": dims["complex_d1_trace1"], "complex_d2_trace1": dims["complex_d2_trace1"],
                "real_d1_trace1": dims["real_d1_trace1"], "real_d2_trace1": dims["real_d2_trace1"],
                "complex_local_tomography_trace1": dims["complex_local_tomography_trace1"],
                "real_local_tomography_trace1": dims["real_local_tomography_trace1"],
                "note": "Naive trace-1-constrained test does NOT confirm local tomography for either branch; "
                        "not used as the axiom test above.",
            },
        },
        "selected_carrier": selected_carrier,
        "one_way_forgetting_witness": {
            "map": "drop Im(off-diagonal) of a complex Hermitian 2x2 -> real symmetric 2x2",
            "rho": matrix_payload(rho), "rho_prime": matrix_payload(rho_prime),
            "forgotten": matrix_payload(forgotten.astype(complex)),
            "forgotten_prime": matrix_payload(forgotten_prime.astype(complex)),
            "witness_valid": witness_valid,
            "proper_noninjective_over_sampled_grid": proper_noninjective_witness,
        },
        "z3": z3_result,
        "z3_erased": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result,
        "control_channel": "Phase-free complex states (Im(off-diag)=0 already, a real Hermitian subset of the "
                            "complex branch): forget_imaginary restricted here is the identity map, recomputed "
                            "on every sampled phase-free state -- genuinely not one-way.",
        "control_genuine": control_genuine,
        "control_is_one_way": control_is_one_way,
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{
            "key": "ratcheting.complex_rung.tomography_gap",
            "value": real_gap,
            "direction": "higher_is_better",
            "description": "Real (rebit) local-tomography deficit: real_d2 - real_d1^2 for two rebits "
                            "(10-9=1 under the standard n(n+1)/2 convention); the discriminating number "
                            "by which local tomography excludes the real branch while the complex branch "
                            "passes it as an algebraic tautology.",
        }],
        "engines_ran": {"sympy": True, "numpy": True, "z3": True,
                         "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "real_vs_complex_tomography.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(output), "verdict": verdict,
        "real_d1": dims["real_d1"], "real_d2": dims["real_d2"], "real_local_tomography": real_local_tomography,
        "complex_d1": dims["complex_d1"], "complex_d2": dims["complex_d2"], "complex_local_tomography": complex_local_tomography,
        "real_gap": real_gap, "selected_carrier": selected_carrier,
        "z3": z3_result["result"], "z3_erased": z3_result["erased_constraint_result"],
        "cvc5": cvc5_result["result"],
    }, indent=2))


if __name__ == "__main__":
    main()
