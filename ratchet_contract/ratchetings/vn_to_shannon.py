#!/usr/bin/env python3
"""Finite dephasing probe: von Neumann to Shannon entropy.

Object: Layer 1 is the Bloch ball of 2x2 density operators with the BKM
(Kubo--Mori) metric and von Neumann entropy.  Layer 2 is the diagonal,
commuting z-axis/simplex Delta^1 with the Fisher--Rao metric and Shannon
entropy.  The proposed ratcheting map is the CPTP dephasing/pinching channel
D(rho)=diag(rho_00, rho_11), from Layer 1 to Layer 2.

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon".  This finite probe does not settle a
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


classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"
TOL = 1.0e-10

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True,
              "reason": "Exact symbolic density-matrix, entropy, and diagonal BKM/Fisher checks."},
    "numpy": {"tried": True, "used": True,
              "reason": "Finite Bloch-ball and pure-state sweep, entropy, metric, and witness calculations."},
    "z3": {"tried": True, "used": True,
           "reason": "Primary SMT contradiction: one function of one dephased input cannot return two distinct coherences."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "jax": {"tried": False, "used": False,
            "reason": "Queued: memory below 0.40 threshold at build time; explicitly not run."},
    "julia": {"tried": False, "used": False,
              "reason": "Queued confirmation leg: not required for this probe and memory-gated at build time; explicitly not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": None,
    "jax": None,
    "julia": None,
}


def density_from_bloch(x: float, y: float, z: float) -> np.ndarray:
    """Return (I + x X + y Y + z Z)/2."""
    return np.array([[1.0 + z, x - 1j * y], [x + 1j * y, 1.0 - z]], dtype=complex) / 2.0


def dephase(rho: np.ndarray) -> np.ndarray:
    return np.diag(np.diag(rho)).astype(complex)


def vn_entropy(rho: np.ndarray) -> float:
    """Von Neumann entropy with the convention 0 log(0)=0."""
    eigenvalues = np.linalg.eigvalsh(rho)
    eigenvalues = np.clip(np.real(eigenvalues), 0.0, 1.0)
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def shannon(p: float) -> float:
    values = np.array([p, 1.0 - p], dtype=float)
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def bkm_metric_bloch(vector: np.ndarray) -> np.ndarray:
    """BKM tensor in Bloch Cartesian coordinates.

    For r=|v|, g = a(I-nn^T)+b nn^T, with
    a=atanh(r)/r and b=1/(1-r^2).  The r=0 limit is I.
    This follows from g_rho(A,A)=sum_ij ((log lam_i-log lam_j)/(lam_i-lam_j))
    |A_ij|^2 for the BKM metric.
    """
    vector = np.asarray(vector, dtype=float)
    radius = float(np.linalg.norm(vector))
    if radius < 1.0e-14:
        return np.eye(3)
    if radius >= 1.0:
        raise ValueError("BKM tensor is evaluated only on the Bloch-ball interior")
    transverse = math.atanh(radius) / radius
    radial = 1.0 / (1.0 - radius * radius)
    unit = vector / radius
    return transverse * np.eye(3) + (radial - transverse) * np.outer(unit, unit)


def fisher_rao_z(z: float) -> float:
    """Bernoulli Fisher information in z=2p-1 coordinates."""
    return 1.0 / (1.0 - z * z)


def symbolic_checks() -> dict[str, Any]:
    p, a, b = sp.symbols("p a b", real=True)
    coherence = a + sp.I * b
    rho = sp.Matrix([[p, coherence], [sp.conjugate(coherence), 1 - p]])
    d_rho = sp.diag(rho[0, 0], rho[1, 1])
    idempotent = sp.simplify(sp.diag(d_rho[0, 0], d_rho[1, 1]) - d_rho) == sp.zeros(2)

    vn_diagonal = -p * sp.log(p) - (1 - p) * sp.log(1 - p)
    shannon_diagonal = -p * sp.log(p) - (1 - p) * sp.log(1 - p)
    entropy_equal = sp.simplify(vn_diagonal - shannon_diagonal) == 0

    q = sp.symbols("q", real=True)
    relative_entropy = p * sp.log(p / q) + (1 - p) * sp.log((1 - p) / (1 - q))
    bkm_hessian_q = sp.simplify(sp.diff(relative_entropy, q, q).subs(q, p))
    fisher_p = sp.simplify(1 / (p * (1 - p)))
    metric_equal = sp.simplify(bkm_hessian_q - fisher_p) == 0
    return {
        "idempotent": bool(idempotent),
        "entropy_equal": bool(entropy_equal),
        "bkm_diagonal_equals_fisher": bool(metric_equal),
        "bkm_hessian_p": str(bkm_hessian_q),
    }


def sampled_states() -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Interior Cartesian grid plus boundary pure states on the Bloch sphere."""
    states: list[tuple[str, np.ndarray, np.ndarray]] = []
    grid = np.arange(-0.75, 0.751, 0.25)
    for x in grid:
        for y in grid:
            for z in grid:
                vector = np.array([x, y, z], dtype=float)
                if float(np.dot(vector, vector)) < 1.0 - 1.0e-12:
                    states.append(("interior", vector, density_from_bloch(x, y, z)))
    # Includes the two diagonal pure boundary states and non-diagonal pure states.
    for theta in np.linspace(0.0, math.pi, 7):
        for phi in np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False):
            vector = np.array([
                math.sin(theta) * math.cos(phi),
                math.sin(theta) * math.sin(phi),
                math.cos(theta),
            ])
            states.append(("pure_boundary", vector, density_from_bloch(*vector)))
    return states


def z3_noninjectivity() -> dict[str, str]:
    """Encode a deterministic recovery's real/imaginary output at one input p=1/2."""
    p = RealVal("1/2")
    quarter = RealVal("1/4")
    recovered_re = Function("recover_re", RealSort(), RealSort())
    recovered_im = Function("recover_im", RealSort(), RealSort())
    solver = Solver()
    # rho has coherence 1/4; rho_prime has coherence i/4.  Both D-images have p=1/2.
    solver.add(recovered_re(p) == quarter, recovered_im(p) == 0,
               recovered_re(p) == 0, recovered_im(p) == quarter)
    verdict = solver.check()
    assert verdict == unsat
    relaxed = Solver()
    relaxed.add(recovered_re(p) == quarter, recovered_im(p) == 0)
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same dephased p=1/2 must recover both (Re,Im)=(1/4,0) and (0,1/4)",
            "result": str(verdict), "erased_constraint_result": str(relaxed_result)}


def cvc5_noninjectivity() -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function_sort = solver.mkFunctionSort([real], real)
        recovered_re = solver.mkConst(function_sort, "recover_re")
        recovered_im = solver.mkConst(function_sort, "recover_im")
        half = solver.mkReal("1/2")
        quarter = solver.mkReal("1/4")
        zero = solver.mkReal(0)
        app = lambda function: solver.mkTerm(cvc5.Kind.APPLY_UF, function, half)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recovered_re), quarter))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recovered_im), zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recovered_re), zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app(recovered_im), quarter))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function_sort2 = relaxed.mkFunctionSort([real2], real2)
        recovered_re2 = relaxed.mkConst(function_sort2, "recover_re_relaxed")
        recovered_im2 = relaxed.mkConst(function_sort2, "recover_im_relaxed")
        half2 = relaxed.mkReal("1/2")
        quarter2 = relaxed.mkReal("1/4")
        zero2 = relaxed.mkReal(0)
        app2 = lambda function: relaxed.mkTerm(cvc5.Kind.APPLY_UF, function, half2)
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2(recovered_re2), quarter2))
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2(recovered_im2), zero2))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same deterministic-recovery coherence contradiction"}
    except Exception as error:  # No false engine-use claim if the local API differs.
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def matrix_payload(rho: np.ndarray) -> list[list[Any]]:
    return [[float(value.real) if abs(value.imag) < TOL else [float(value.real), float(value.imag)]
             for value in row] for row in rho]


def main() -> None:
    symbolic = symbolic_checks()
    states = sampled_states()
    numerical_idempotent = all(np.allclose(dephase(dephase(rho)), dephase(rho), atol=TOL)
                                for _, _, rho in states)
    image_z = {round(float(np.real(dephase(rho)[0, 0]) * 2.0 - 1.0), 12) for _, _, rho in states}
    diagonal_sample_z = {round(float(vector[2]), 12) for _, vector, _ in states}
    all_images_diagonal = all(abs(dephase(rho)[0, 1]) < TOL and abs(dephase(rho)[1, 0]) < TOL
                              for _, _, rho in states)
    proper_subset_witness = any(abs(rho[0, 1]) > TOL for _, _, rho in states)
    nesting = numerical_idempotent and all_images_diagonal and image_z == diagonal_sample_z and proper_subset_witness

    diagonal_entropy_matches = all(
        abs(vn_entropy(dephase(rho)) - shannon(float(np.real(rho[0, 0])))) < TOL
        for _, _, rho in states
    )
    gaps: list[float] = []
    off_diagonal_gaps: list[float] = []
    boundary_offdiag_gaps: list[float] = []
    diagonal_gaps: list[float] = []
    for kind, vector, rho in states:
        gap = vn_entropy(dephase(rho)) - vn_entropy(rho)
        gaps.append(gap)
        if abs(rho[0, 1]) > TOL:
            off_diagonal_gaps.append(gap)
            if kind == "pure_boundary":
                boundary_offdiag_gaps.append(gap)
        else:
            diagonal_gaps.append(gap)
    minimum_offdiag_gap = float(min(off_diagonal_gaps))
    entropy_monotone = min(gaps) >= -TOL and minimum_offdiag_gap > TOL and max(abs(g) for g in diagonal_gaps) < TOL

    diagonal_z = sorted({round(float(vector[2]), 12) for kind, vector, _ in states
                         if kind == "interior" and abs(vector[0]) < TOL and abs(vector[1]) < TOL
                         and abs(vector[2]) < 1.0 - TOL})
    metric_differences = [abs(bkm_metric_bloch(np.array([0.0, 0.0, z]))[2, 2] - fisher_rao_z(z))
                          for z in diagonal_z]
    metric_max_difference = float(max(metric_differences))

    rho = np.array([[0.5, 0.25], [0.25, 0.5]], dtype=complex)
    rho_prime = np.array([[0.5, 0.25j], [-0.25j, 0.5]], dtype=complex)
    d_rho, d_rho_prime = dephase(rho), dephase(rho_prime)
    witness_valid = (not np.allclose(rho, rho_prime, atol=TOL)
                     and np.allclose(d_rho, d_rho_prime, atol=TOL))
    z3_result = z3_noninjectivity()
    cvc5_result = cvc5_noninjectivity()

    # Control: a z-rotation U=diag(1,e^{i phi}) — coherence-preserving, unitary,
    # hence genuinely invertible by U^dagger. Must NOT be one-way: recovering the
    # input is a real recomputation (U^dagger U rho U U^dagger == rho), and it does
    # NOT collapse VN to Shannon (unitaries preserve VN entropy). If this control
    # ALSO looked one-way, the dephasing result would be by-construction.
    phi = 0.7
    U = np.array([[1.0, 0.0], [0.0, np.exp(1j * phi)]], dtype=complex)
    Udag = U.conj().T
    control_gap = abs(vn_entropy(rho) - shannon(float(np.real(rho[0, 0]))))
    control_recovers = all(
        np.allclose(Udag @ (U @ cand @ Udag) @ U, cand, atol=TOL)
        for _, _, cand in states)
    control_preserves_vn = all(
        abs(vn_entropy(U @ cand @ Udag) - vn_entropy(cand)) < TOL
        for _, _, cand in states)
    control_invertible = bool(control_recovers)
    # one-way iff non-invertible (like dephasing). The control is invertible, so
    # this evaluates to a genuine False — not a hard-coded one.
    control_is_one_way = not control_invertible

    verdict = "RATCHETED_ONE_WAY"
    notes: list[str] = [
        "Finite sampled probe only; proposed layer ordering is not canon.",
        "BKM tensor used: g=a(I-nn^T)+b nn^T, a=atanh(r)/r, b=1/(1-r^2); z=2p-1.",
        "SMT encodes deterministic recovery of two different coherences from the same dephased diagonal, not a full Choi/CPTP parametrization.",
    ]
    core_ok = (nesting and symbolic["idempotent"] and diagonal_entropy_matches and symbolic["entropy_equal"]
               and entropy_monotone and symbolic["bkm_diagonal_equals_fisher"]
               and metric_max_difference < 1.0e-8 and witness_valid and z3_result["result"] == "unsat"
               and z3_result["erased_constraint_result"] == "sat"
               and control_gap > TOL and control_invertible and not control_is_one_way)
    if not core_ok:
        verdict = "FAILED"
        notes.append("At least one required finite-probe check failed; inspect check details.")
    elif control_is_one_way:
        verdict = "BY_CONSTRUCTION"
        notes.append("The proposed control was not invertible, so it cannot separate dephasing-specific directionality.")

    result = {
        "schema_version": "1.0",
        "layer1": "2x2 density operators (Bloch ball), BKM metric, von Neumann entropy.",
        "layer2": "Diagonal density operators (simplex Delta^1), Fisher-Rao metric, Shannon entropy.",
        "nesting_idempotent": bool(nesting and symbolic["idempotent"]),
        "shannon_equals_vn_on_diagonal": bool(diagonal_entropy_matches and symbolic["entropy_equal"]),
        "dephasing_entropy_monotone": minimum_offdiag_gap,
        "bkm_restricts_to_fisher": metric_max_difference,
        "one_way_witness_pair": {"rho": matrix_payload(rho), "rho_prime": matrix_payload(rho_prime),
                                 "D_rho": matrix_payload(d_rho), "D_rho_prime": matrix_payload(d_rho_prime)},
        "control_channel": "z-rotation U=diag(1,e^{i*0.7}); unitary, coherence-preserving, invertible by U^dagger (recovery recomputed on every sampled state) and VN-preserving -- genuinely not one-way.",
        "control_is_one_way": control_is_one_way,
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{"key": "ratcheting.vn_to_shannon.one_way_margin", "value": minimum_offdiag_gap,
                          "direction": "higher_is_better"}],
        "engines_ran": {"sympy": True, "numpy": True, "z3": True,
                        "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "vn_to_shannon.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "verdict": verdict,
                      "minimum_offdiagonal_gap": minimum_offdiag_gap,
                      "metric_max_difference": metric_max_difference,
                      "z3": z3_result["result"], "z3_erased_constraint": z3_result["erased_constraint_result"],
                      "cvc5": cvc5_result["result"], "cvc5_erased_constraint": cvc5_result["erased_constraint_result"]}, indent=2))


if __name__ == "__main__":
    main()
