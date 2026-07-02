#!/usr/bin/env python3
"""
sim_clifford_pseudoscalar_sandwich_micro.py -- Clifford pseudoscalar sandwich MICRO packet.

Tool-stage authoring packet for one Clifford surface:

    clifford.Cl(3) rotor sandwich product R * I * ~R on the fixed pseudoscalar
    blade I = e123.

The originally requested fixed-blade vector rotor sandwich surface is already
covered by load-bearing Clifford receipts. This file switches to the nearest
uncovered neighbor: fixed pseudoscalar blade invariance under the same sandwich
API surface. It is pre-lego and cannot promote a lego, bridge, axis, coupling,
or manifold claim.
"""

import json
import math
import os
from typing import Any, Dict, Iterable, Tuple

import numpy as np

classification = "tool_lego_fit_probe"
NAME = "sim_clifford_pseudoscalar_sandwich_micro"
PROBE_FAMILY = "M_clifford_pseudoscalar_sandwich_micro"
CONSTRAINT_SET = "C_cl3_unit_rotor_fixed_pseudoscalar_sandwich"
EPS = 1e-10

_NOT_USED_REASON = (
    "not used: this micro isolates one Clifford Cl(3) pseudoscalar sandwich "
    "surface only; proof, graph, topology, tensor, coupling, bridge, axis, and "
    "promotion claims are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": "under test"},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

MICRO = {
    "tool_target": "clifford",
    "function_surface": "clifford.Cl(3) rotor sandwich product R*I*~R on fixed pseudoscalar blade I=e123",
    "micro_claim": (
        "In the finite Cl(3) basis, a unit even rotor sandwich leaves the fixed "
        "pseudoscalar blade e123 invariant while non-central comparison blades "
        "remain distinguishable."
    ),
    "lego_target": "minimal finite Cl(3) pseudoscalar fixture; pre-lego tool-depth row only",
    "carrier": "finite Cl(3) basis {1,e1,e2,e3,e12,e13,e23,e123} with fixed blade I=e123",
    "function_receipt": "switched_from_covered_vector_rotor_sandwich",
    "prior_function_receipts": [
        "system_v4/probes/a2_state/sim_results/clifford_capability_results.json",
        "system_v4/probes/a2_state/sim_results/sim_sympy_clifford_cross_check_results.json",
    ],
    "covered_check": (
        "Requested fixed-vector rotor sandwich surface already has load-bearing "
        "Clifford receipts; this packet targets the nearest fixed-blade neighbor."
    ),
    "one_variable": "Only Clifford's rotor sandwich behavior on the fixed pseudoscalar blade is uncertain.",
    "ledger_loopback": "clifford tool-depth row: rotor sandwich fixed-blade/pseudoscalar neighbor, shallow-tool checker threshold >=10 load-bearing receipts",
    "positive_case": "Unit rotors in e12/e13/e23 planes leave e123 invariant under R*I*~R.",
    "negative_case": "A non-central vector blade is excluded as a pseudoscalar-invariance substitute under a nontrivial rotor sandwich.",
    "boundary_case": "Identity, 2*pi, 4*pi, and tiny-angle rotors stay on the expected pseudoscalar boundary.",
    "demotion_condition": (
        "Demote this surface if any unit rotor moves e123 beyond 1e-10, if a "
        "non-central comparison blade is admitted as invariant under a "
        "nontrivial rotor, or if identity/2pi/4pi/tiny-angle boundaries drift."
    ),
    "out_of_scope": [
        "fixed-vector rotor sandwich surface already covered",
        "lego promotion",
        "tool-tool coupling",
        "bridge, axis, engine, emergence, topology, manifold, or physics claims",
        "result or registry edits from this authoring packet",
    ],
}

try:
    from clifford import Cl

    CLIFFORD_AVAILABLE = True
    CLIFFORD_ERROR = None
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "load-bearing: Cl(3) blades, MultiVector geometric product, reverse (~), "
        "and rotor sandwich R*I*~R decide the fixed-pseudoscalar claim"
    )
except Exception as exc:
    Cl = None
    CLIFFORD_AVAILABLE = False
    CLIFFORD_ERROR = repr(exc)
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {CLIFFORD_ERROR}"
    TOOL_INTEGRATION_DEPTH["clifford"] = None


def _setup_cl3() -> Tuple[Any, Dict[str, Any]]:
    _, blades = Cl(3)
    return _, blades


def _coeffs(mv: Any) -> np.ndarray:
    return np.asarray(mv.value, dtype=float).reshape(-1)


def _coeff_max_abs(mv: Any) -> float:
    return float(np.linalg.norm(_coeffs(mv), ord=np.inf))


def _mv_close(a: Any, b: Any, tol: float = EPS) -> bool:
    return bool(np.allclose(_coeffs(a - b), 0.0, atol=tol))


def _scalar_part(mv: Any) -> float:
    return float(_coeffs(mv)[0])


def _non_scalar_norm(mv: Any) -> float:
    coeffs = _coeffs(mv).copy()
    coeffs[0] = 0.0
    return float(np.linalg.norm(coeffs, ord=np.inf))


def _rotor(unit_bivector: Any, theta: float) -> Any:
    return math.cos(theta / 2.0) - math.sin(theta / 2.0) * unit_bivector


def _rotor_norm_report(R: Any) -> Dict[str, Any]:
    right = R * ~R
    left = ~R * R
    return {
        "right_scalar": _scalar_part(right),
        "left_scalar": _scalar_part(left),
        "right_non_scalar_norm": _non_scalar_norm(right),
        "left_non_scalar_norm": _non_scalar_norm(left),
        "admitted_by_unit_norm_gate": (
            abs(_scalar_part(right) - 1.0) <= EPS
            and abs(_scalar_part(left) - 1.0) <= EPS
            and _non_scalar_norm(right) <= EPS
            and _non_scalar_norm(left) <= EPS
        ),
    }


def _unit_rotor_cases(blades: Dict[str, Any]) -> Iterable[Tuple[str, Any, float]]:
    return (
        ("e12_pi_over_3", blades["e12"], math.pi / 3.0),
        ("e13_pi_over_5", blades["e13"], math.pi / 5.0),
        ("e23_pi_over_7", blades["e23"], math.pi / 7.0),
    )


def _all_entries_pass(section: Dict[str, Any]) -> bool:
    return all(bool(entry.get("pass", False)) for entry in section.values())


def run_positive_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    pseudoscalar = blades["e123"]
    results: Dict[str, Any] = {}

    for label, bivector, theta in _unit_rotor_cases(blades):
        R = _rotor(bivector, theta)
        sandwiched = R * pseudoscalar * ~R
        delta = _coeff_max_abs(sandwiched - pseudoscalar)
        norm_report = _rotor_norm_report(R)
        results[f"{label}_fixed_pseudoscalar_admitted"] = {
            "rotor_norm": norm_report,
            "sandwich_delta_inf": delta,
            "pseudoscalar_admitted_as_fixed_blade": delta <= EPS,
            "pass": norm_report["admitted_by_unit_norm_gate"] and delta <= EPS,
        }
    return results


def run_negative_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    nontrivial_rotor = _rotor(blades["e12"], math.pi / 2.0)
    vector_blade = blades["e1"]
    bivector_blade = blades["e13"]
    vector_sandwiched = nontrivial_rotor * vector_blade * ~nontrivial_rotor
    bivector_sandwiched = nontrivial_rotor * bivector_blade * ~nontrivial_rotor
    vector_delta = _coeff_max_abs(vector_sandwiched - vector_blade)
    bivector_delta = _coeff_max_abs(bivector_sandwiched - bivector_blade)

    non_unit_candidate = 1.0 + 0.5 * blades["e12"]
    non_unit_norm = _rotor_norm_report(non_unit_candidate)

    return {
        "vector_blade_excluded_as_fixed_pseudoscalar_substitute": {
            "comparison_blade": "e1",
            "sandwich_delta_inf": vector_delta,
            "fixed_blade_admitted": vector_delta <= EPS,
            "pass": vector_delta > EPS,
        },
        "bivector_blade_excluded_as_fixed_pseudoscalar_substitute": {
            "comparison_blade": "e13",
            "sandwich_delta_inf": bivector_delta,
            "fixed_blade_admitted": bivector_delta <= EPS,
            "pass": bivector_delta > EPS,
        },
        "non_unit_even_multivector_excluded_by_norm_gate": {
            "candidate_norm": non_unit_norm,
            "unit_norm_gate_admitted": non_unit_norm["admitted_by_unit_norm_gate"],
            "pass": not non_unit_norm["admitted_by_unit_norm_gate"],
        },
    }


def run_boundary_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    pseudoscalar = blades["e123"]
    one = 1.0 + 0.0 * blades["e1"]
    minus_one = -1.0 + 0.0 * blades["e1"]
    boundary_rotors = {
        "zero_angle_identity": _rotor(blades["e12"], 0.0),
        "two_pi_minus_one": _rotor(blades["e12"], 2.0 * math.pi),
        "four_pi_identity": _rotor(blades["e12"], 4.0 * math.pi),
        "tiny_angle_near_identity": _rotor(blades["e12"], 1e-8),
    }

    results: Dict[str, Any] = {}
    for label, R in boundary_rotors.items():
        sandwiched = R * pseudoscalar * ~R
        delta = _coeff_max_abs(sandwiched - pseudoscalar)
        norm_report = _rotor_norm_report(R)
        results[f"{label}_pseudoscalar_boundary"] = {
            "rotor_norm": norm_report,
            "is_identity_representative": _mv_close(R, one),
            "is_minus_one_representative": _mv_close(R, minus_one),
            "sandwich_delta_inf": delta,
            "pass": norm_report["admitted_by_unit_norm_gate"] and delta <= EPS,
        }
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = _all_entries_pass(positive) and _all_entries_pass(negative) and _all_entries_pass(boundary)

    results = {
        "name": NAME,
        "classification": "tool_lego_fit_probe",
        "probe_family": PROBE_FAMILY,
        "constraint_set": CONSTRAINT_SET,
        "micro": MICRO,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "classification": "tool_lego_fit_probe",
            "scope_note": (
                "Tool-lego fit probe only. The fixed-vector rotor sandwich "
                "surface was already covered; this switched neighbor checks "
                "the Cl(3) fixed-pseudoscalar sandwich surface and cannot be "
                "cited as canonical, bridge, QIT, GStack, axis, manifold, or "
                "nonclassical admission."
            ),
            "passed_sections": {
                "positive": _all_entries_pass(positive),
                "negative": _all_entries_pass(negative),
                "boundary": _all_entries_pass(boundary),
            },
        },
        "all_pass": bool(all_pass),
        "criteria_checked": [
            "C1_unit_rotor_reverse_product_norm_gate",
            "C2_pseudoscalar_e123_fixed_under_R_I_reverse_R",
            "C3_noncentral_vector_and_bivector_comparison_blades_excluded_as_fixed-pseudoscalar_substitutes",
            "C4_non_unit_even_candidate_excluded_by_norm_gate",
            "C5_identity_2pi_4pi_tiny_angle_boundaries_keep_pseudoscalar_fixed",
        ],
        "surviving_alternatives": [
            "Other signatures and higher-dimensional pseudoscalar centers remain separate micro surfaces.",
            "Fixed-vector rotor sandwich behavior remains covered by prior receipts and is not re-promoted here.",
        ],
        "claim_ceiling": "tool_lego_fit_probe_only",
        "next_lego_target": "none",
        "promotion_condition": "promotion_allowed:false; requires a later admitted lego row with exact parent receipts",
        "blocked_until": "blocked until downstream queue, source, result JSON, and ledger loopback are reconciled by the runner process",
        "demotion_condition": MICRO["demotion_condition"],
        "out_of_scope": MICRO["out_of_scope"],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} -> {out_path}")
    if not all_pass:
        raise SystemExit(1)
