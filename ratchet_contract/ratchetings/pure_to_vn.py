#!/usr/bin/env python3
"""Finite partial-trace probe: pure states to von Neumann entropy.

Object: Layer 0 is the rank-1 rays |psi><psi| on C^2, namely CP^1 with the
Fubini--Study metric ds^2=<dpsi|dpsi>-|<psi|dpsi>|^2 and identically zero von
Neumann entropy.  Layer 1 is the Bloch ball of mixed 2x2 density operators,
where von Neumann entropy is positive in the interior.  The proposed
ratcheting map is partial trace of a pure bipartite state on C^2 tensor C^2.

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
              "reason": "Exact Schmidt partial-trace and entanglement-entropy checks."},
    "numpy": {"tried": True, "used": True,
              "reason": "Finite Bloch-ball, pure-boundary, purification-witness, and control calculations."},
    "z3": {"tried": True, "used": True,
           "reason": "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding -- the load-bearing evidence is the numpy/sympy witness (psi/phi purification pair with identical partial trace plus the exact symbolic entanglement-entropy formula)."},
    "cvc5": {"tried": cvc5 is not None, "used": False,
             "reason": "Cross-check attempted when bindings are available; updated at runtime with its actual solver result."},
    "jax": {"tried": False, "used": False,
            "reason": "Queued: memory below 0.40 threshold at build time; explicitly not run."},
    "julia": {"tried": False, "used": False,
              "reason": "Queued: memory below 0.40 threshold at build time; explicitly not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing", "numpy": "load_bearing", "z3": "supportive",
    "cvc5": None, "jax": None, "julia": None,
}


def density_from_bloch(x: float, y: float, z: float) -> np.ndarray:
    """Return (I + x X + y Y + z Z)/2."""
    return np.array([[1.0 + z, x - 1j * y], [x + 1j * y, 1.0 - z]], dtype=complex) / 2.0


def vn_entropy(rho: np.ndarray) -> float:
    """Von Neumann entropy with the convention 0 log(0)=0."""
    eigenvalues = np.clip(np.real(np.linalg.eigvalsh(rho)), 0.0, 1.0)
    positive = eigenvalues[eigenvalues > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def partial_trace_b(pure_density: np.ndarray) -> np.ndarray:
    """Trace B from a 4x4 AB density matrix in the computational basis."""
    return np.trace(pure_density.reshape(2, 2, 2, 2), axis1=1, axis2=3)


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
    for theta in np.linspace(0.0, math.pi, 7):
        for phi in np.linspace(0.0, 2.0 * math.pi, 8, endpoint=False):
            vector = np.array([math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)])
            states.append(("pure_boundary", vector, density_from_bloch(*vector)))
    return states


def symbolic_checks() -> dict[str, Any]:
    t = sp.symbols("t", real=True)
    c, s = sp.cos(t), sp.sin(t)
    psi = sp.Matrix([c, 0, 0, s])
    rho_ab = psi * psi.T
    rho_a = sp.Matrix([[rho_ab[0, 0] + rho_ab[1, 1], rho_ab[0, 2] + rho_ab[1, 3]],
                       [rho_ab[2, 0] + rho_ab[3, 1], rho_ab[2, 2] + rho_ab[3, 3]]])
    expected = -c**2 * sp.log(c**2) - s**2 * sp.log(s**2)
    derived = -rho_a[0, 0] * sp.log(rho_a[0, 0]) - rho_a[1, 1] * sp.log(rho_a[1, 1])
    exact = sp.simplify(derived - expected) == 0
    midpoint = sp.simplify(expected.subs(t, sp.pi / 4))
    # Direct substitution produces SymPy's 0*log(0) sentinel; take the
    # entropy-continuous limits instead.
    endpoints_zero = all(sp.simplify(sp.limit(expected, t, value, dir="+")) == 0
                         for value in (0, sp.pi / 2, sp.pi, 3 * sp.pi / 2))
    generic_positive = all(float(sp.N(expected.subs(t, value))) > 0.0 for value in (sp.pi / 6, sp.pi / 4, sp.pi / 3))
    return {"entropy_formula": str(expected), "formula_exact": bool(exact), "rho_a": str(rho_a),
            "entropy_pi_over_4": float(sp.N(midpoint)), "endpoints_zero": bool(endpoints_zero),
            "generic_samples_positive": bool(generic_positive),
            "zero_iff_note": "For real t, the binary entropy is zero iff cos^2(t) is 0 or 1, equivalently t is a multiple of pi/2."}


def z3_noninjectivity() -> dict[str, str]:
    half, zero, one = RealVal("1/2"), RealVal(0), RealVal(1)
    recovered_phase = Function("recover_purification_phase", RealSort(), RealSort())
    solver = Solver()
    solver.add(recovered_phase(half) == zero, recovered_phase(half) == one)
    result = solver.check()
    assert result == unsat
    relaxed = Solver()
    relaxed.add(recovered_phase(half) == zero)
    relaxed_result = relaxed.check()
    assert relaxed_result == sat
    return {"encoding": "same rho_A=I/2 must recover purification phase 0 and phase 1", "result": str(result),
            "erased_constraint_result": str(relaxed_result)}


def cvc5_noninjectivity() -> dict[str, str]:
    if cvc5 is None:
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": "cvc5 Python bindings unavailable"}
    try:
        solver = cvc5.Solver()
        solver.setLogic("QF_UFLRA")
        real = solver.getRealSort()
        function = solver.mkConst(solver.mkFunctionSort([real], real), "recover_purification_phase")
        half, zero, one = solver.mkReal("1/2"), solver.mkReal(0), solver.mkReal(1)
        app = solver.mkTerm(cvc5.Kind.APPLY_UF, function, half)
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, zero))
        solver.assertFormula(solver.mkTerm(cvc5.Kind.EQUAL, app, one))
        result = solver.checkSat()
        if not result.isUnsat():
            raise RuntimeError(f"expected unsat, got {result}")
        relaxed = cvc5.Solver()
        relaxed.setLogic("QF_UFLRA")
        real2 = relaxed.getRealSort()
        function2 = relaxed.mkConst(relaxed.mkFunctionSort([real2], real2), "recover_purification_phase_relaxed")
        app2 = relaxed.mkTerm(cvc5.Kind.APPLY_UF, function2, relaxed.mkReal("1/2"))
        relaxed.assertFormula(relaxed.mkTerm(cvc5.Kind.EQUAL, app2, relaxed.mkReal(0)))
        relaxed_result = relaxed.checkSat()
        if not relaxed_result.isSat():
            raise RuntimeError(f"expected sat after erasure, got {relaxed_result}")
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_MANIFEST["cvc5"]["reason"] = "Cross-check SMT contradiction returned unsat; erased-constraint control returned sat."
        TOOL_INTEGRATION_DEPTH["cvc5"] = "supportive"
        return {"result": str(result), "erased_constraint_result": str(relaxed_result),
                "reason": "same deterministic-recovery purification contradiction"}
    except Exception as error:
        TOOL_MANIFEST["cvc5"]["used"] = False
        TOOL_MANIFEST["cvc5"]["reason"] = f"Bindings available but cross-check did not run successfully: {error}"
        return {"result": "not_run", "erased_constraint_result": "not_run", "reason": str(error)}


def payload(matrix: np.ndarray) -> list[Any]:
    values: list[Any] = []
    for value in matrix.reshape(-1):
        values.append(float(value.real) if abs(value.imag) < TOL else [float(value.real), float(value.imag)])
    return values


def matrix_payload(matrix: np.ndarray) -> list[list[Any]]:
    return [payload(row) for row in matrix]


def main() -> None:
    symbolic = symbolic_checks()
    states = sampled_states()
    boundary_entropies = [abs(vn_entropy(rho)) for kind, _, rho in states if kind == "pure_boundary"]
    interior_entropies = [vn_entropy(rho) for kind, _, rho in states if kind == "interior"]
    max_boundary_entropy, min_interior_entropy = float(max(boundary_entropies)), float(min(interior_entropies))
    boundary_zero_set = max_boundary_entropy < 1.0e-9 and min_interior_entropy > TOL
    pure_zero = all(abs(vn_entropy(rho)) < 1.0e-9 for kind, _, rho in states if kind == "pure_boundary")

    t = math.pi / 4.0
    psi = np.array([math.cos(t), 0.0, 0.0, math.sin(t)], dtype=complex)
    phase = np.array([[1.0, 0.0], [0.0, 1j]], dtype=complex)
    phi = np.kron(np.eye(2), phase) @ psi
    rho_psi, rho_phi = np.outer(psi, psi.conj()), np.outer(phi, phi.conj())
    rho_a_psi, rho_a_phi = partial_trace_b(rho_psi), partial_trace_b(rho_phi)
    not_proportional = not np.allclose(np.outer(psi, psi.conj()), np.outer(phi, phi.conj()), atol=TOL)
    witness_valid = not_proportional and np.allclose(rho_a_psi, rho_a_phi, atol=TOL)
    entanglement_entropy = vn_entropy(rho_a_psi)
    z3_result, cvc5_result = z3_noninjectivity(), cvc5_noninjectivity()

    # Discriminating one-way predicate.  A map is one-way (irreversible) at a
    # witness pair iff it collapses two DISTINCT inputs to the SAME output -- the
    # non-injectivity the probe claims for the partial trace.  The SAME predicate
    # is fed both the partial trace (on the distinct global purifications psi, phi)
    # and a single-system unitary (on two distinct pure states), and must return
    # DIFFERENT answers.  The previous "not invertible" form was a frozen False
    # (every unitary is invertible), so it could never flag anything; this predicate
    # genuinely returns True on the partial trace and False on the unitary.
    def channel_is_one_way(channel, a, b) -> bool:
        """One-way iff distinct inputs a != b are collapsed to a common image."""
        return bool((not np.allclose(a, b, atol=TOL))
                    and np.allclose(channel(a), channel(b), atol=TOL))

    angle = 0.37
    unitary = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]], dtype=complex)
    unitary_dag = unitary.conj().T
    unitary_channel = lambda m: unitary @ m @ unitary_dag  # noqa: E731
    pure_states = [rho for kind, _, rho in states if kind == "pure_boundary"]

    # Two distinct pure states for the unitary control's own domain (C^2):
    ctrl_state_a = density_from_bloch(0.0, 0.0, 1.0)   # |0><0|
    ctrl_state_b = density_from_bloch(1.0, 0.0, 0.0)   # |+><+|

    # Same predicate, both channels:
    partial_trace_is_one_way = channel_is_one_way(partial_trace_b, rho_psi, rho_phi)   # expect True
    control_is_one_way = channel_is_one_way(unitary_channel, ctrl_state_a, ctrl_state_b)  # expect False
    control_discriminates = bool(partial_trace_is_one_way and not control_is_one_way)

    # Corroborating contrast: the unitary is invertible, rank-1 and zero-entropy
    # preserving; the partial trace instead BORNS entropy (rho_A mixed).
    control_recovers = all(np.allclose(unitary_dag @ (unitary @ rho @ unitary_dag) @ unitary, rho, atol=TOL) for rho in pure_states)
    control_rank_preserves = all(np.linalg.matrix_rank(unitary @ rho @ unitary_dag, tol=TOL) == 1 for rho in pure_states)
    control_entropy_preserves = all(abs(vn_entropy(unitary @ rho @ unitary_dag)) < 1.0e-9 and abs(vn_entropy(rho)) < 1.0e-9 for rho in pure_states)
    control_invertible = bool(control_recovers and control_rank_preserves and control_entropy_preserves)
    partial_trace_borns_entropy = bool(entanglement_entropy > TOL)  # pure global -> mixed reduced

    # Mechanism gate (the arrow), independent of the control's discrimination so
    # that BY_CONSTRUCTION is a genuinely reachable branch, not dead code.
    mechanism_ok = (symbolic["formula_exact"] and symbolic["endpoints_zero"] and symbolic["generic_samples_positive"]
                    and pure_zero and boundary_zero_set and witness_valid and abs(entanglement_entropy - math.log(2.0)) < TOL
                    and control_invertible and partial_trace_borns_entropy)
    if not mechanism_ok:
        verdict = "FAILED"
    elif not control_discriminates:
        verdict = "BY_CONSTRUCTION"
    else:
        verdict = "EMERGES_ONE_WAY"
    core_ok = mechanism_ok
    notes = ["Finite sampled probe only; proposed layer ordering is not canon.",
             "Fubini--Study formula for CP^1: ds^2=<dpsi|dpsi>-|<psi|dpsi>|^2.",
             "VN entropy is zero identically for single-system pure states; its nonzero value here is born through the partial-trace cut.",
             symbolic["zero_iff_note"],
             "SMT encodes deterministic recovery of a purification-identifying phase from one reduced state, not a full parametrization of all purifications.",
             "Control is a DISCRIMINATING predicate: the same channel_is_one_way test returns "
             f"partial_trace={partial_trace_is_one_way} vs unitary={control_is_one_way}; it is not a constant."]
    if verdict == "BY_CONSTRUCTION":
        notes.append("The discriminating predicate did not separate the unitary control from the partial trace; directionality is not partial-trace-specific.")
    if not core_ok:
        notes.append("At least one required finite-probe check failed; inspect check details.")

    result = {
        "schema_version": "1.0",
        "layer_before": "Layer 0: pure C^2 rays (rank-1 projectors), CP^1 with Fubini--Study metric ds^2=<dpsi|dpsi>-|<psi|dpsi>|^2; S(|psi><psi|)=0 identically.",
        "layer_vn": "Layer 1: mixed C^2 density operators (Bloch ball), with von Neumann entropy positive in its interior.",
        "vn_zero_on_pure": bool(pure_zero),
        "boundary_is_zero_entropy_set": {"max_abs_S_on_sampled_sphere": max_boundary_entropy, "min_S_off_sphere": min_interior_entropy},
        "entanglement_entropy_born": {"t": "pi/4", "value": entanglement_entropy},
        "one_way_witness_pair": {"description": "psi and phi=(I_A tensor diag(1,i))psi are distinct purifications with the same rho_A=I/2.",
                                 "psi": payload(psi), "phi": payload(phi), "rho_A_from_psi": matrix_payload(rho_a_psi), "rho_A_from_phi": matrix_payload(rho_a_phi)},
        "control_channel": "Single-system real rotation U on C^2. The SAME channel_is_one_way predicate (distinct inputs collapsed to a common image) is fed both the partial trace and this unitary and returns different answers -- a discriminating, non-decorative control.",
        "control_is_one_way": control_is_one_way,
        "control_discrimination": {
            "predicate": "channel_is_one_way(channel, a, b): distinct a != b collapsed to a common image channel(a) == channel(b)",
            "partial_trace_is_one_way": bool(partial_trace_is_one_way),
            "control_is_one_way": bool(control_is_one_way),
            "discriminates": bool(control_discriminates),
            "control_invertible_rank1_zero_entropy": bool(control_invertible),
            "partial_trace_borns_entropy": bool(partial_trace_borns_entropy),
            "note": "Feed-both-and-differ: same predicate returns True on the partial trace (psi, phi collapse to rho_A=I/2) and False on the local unitary; the control can flip and does not.",
        },
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "smt_role": "supportive_nonvacuity_only",
        "load_bearing_evidence": "numpy purification witness pair (psi, phi=(I tensor diag(1,i))psi distinct states, identical partial-trace rho_A) plus sympy exact Schmidt/entanglement-entropy formula and endpoint/generic-sample checks.",
        "floor_claims": [{"key": "ratcheting.pure_to_vn.entanglement_margin", "value": entanglement_entropy, "direction": "higher_is_better"}],
        "hartley_placement": {"note": "Hartley/counting entropy S0=log(V) sits AT the maximally-mixed point of the VN layer: S(I/2)=ln(2), the entropy MAXIMUM on the Bloch ball for a qubit, matching Hartley for V=2 outcomes. Support-Hartley (log of the rank of the support) is a further one-way FORGETTING downstream of VN (drop eigenvalue magnitudes, keep only which eigenvalues are nonzero) -- it is a layer AFTER/BELOW VN in information content, not before it.",
                              "axis0_distinction": "This downstream support-Hartley bookkeeping is DISTINCT from the Axis-0 counting DRIVE (dC = D log(V) over admissible-set size across ticks), which is not a nesting layer in this ladder at all -- it is the entropy gradient/drive framing from the owner's Axis-0 doctrine, not a state-space layer to be ratcheted here. Do not conflate the two."},
        "engines_ran": {"sympy": True, "numpy": True, "z3": True, "cvc5": bool(TOOL_MANIFEST["cvc5"]["used"]), "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": notes,
    }
    output = Path(__file__).resolve().parent / "results" / "pure_to_vn.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(output), "verdict": verdict, "max_abs_S_on_sampled_sphere": max_boundary_entropy,
                      "min_S_off_sphere": min_interior_entropy, "z3": z3_result["result"],
                      "z3_erased_constraint": z3_result["erased_constraint_result"], "cvc5": cvc5_result["result"]}, indent=2))


if __name__ == "__main__":
    main()
