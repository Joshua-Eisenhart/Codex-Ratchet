#!/usr/bin/env python3
"""
sim_clifford_fixed_bivector_sandwich_micro.py -- Clifford fixed-bivector sandwich MICRO packet.

Tool-stage authoring packet for one Clifford surface:

    clifford.Cl(3) rotor sandwich product R * B * ~R on the fixed bivector
    blade B = e13.

The requested fixed-blade rotor sandwich family overlaps existing vector and
pseudoscalar source coverage plus broader load-bearing Clifford receipts. This
packet switches to the nearest uncovered fixed-blade neighbor: bivector grade
and plane readout under the same sandwich API. It is pre-lego and cannot
promote a lego, bridge, axis, coupling, or manifold claim.
"""

import json
import math
import os
from typing import Any, Dict, Iterable, Tuple

classification = "tool_lego_fit_probe"
NAME = "sim_clifford_fixed_bivector_sandwich_micro"
PROBE_FAMILY = "M_clifford_fixed_bivector_sandwich_micro"
CONSTRAINT_SET = "C_cl3_unit_rotor_fixed_bivector_sandwich"
EPS = 1e-10

_NOT_USED_REASON = (
    "not used: this micro isolates one Clifford Cl(3) fixed-bivector sandwich "
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
    "function_surface": "clifford.Cl(3) rotor sandwich product R*B*~R on fixed bivector blade B=e13",
    "micro_claim": (
        "In the finite Cl(3) basis, a unit even rotor sandwich maps the fixed "
        "bivector blade e13 to an admitted grade-2 blade readout, while "
        "non-unit and wrong-grade controls are excluded."
    ),
    "lego_target": "minimal finite Cl(3) bivector fixture; pre-lego tool-depth row only",
    "carrier": "finite Cl(3) basis {1,e1,e2,e3,e12,e13,e23,e123} with fixed blade B=e13",
    "covered_check": (
        "switched: vector sandwich behavior and pseudoscalar fixed-blade source "
        "coverage already exist; this targets the nearest uncovered fixed "
        "bivector sandwich neighbor."
    ),
    "one_variable": "Only Clifford's rotor sandwich behavior on the fixed bivector blade is uncertain.",
    "ledger_loopback": "clifford tool-depth row: rotor sandwich fixed-blade/bivector neighbor, shallow-tool checker threshold >=10 load-bearing receipts",
    "positive_case": "Unit rotors in e12/e13/e23 planes keep R*B*~R inside the bivector-grade readout.",
    "negative_case": "A vector blade and a non-unit even candidate are excluded as substitutes for the fixed-bivector surface.",
    "boundary_case": "Identity, same-plane half-turn, full-turn, and tiny-angle rotors stay on the expected bivector boundary.",
    "demotion_condition": (
        "Demote this surface if any unit rotor moves B=e13 outside grade 2 "
        "beyond 1e-10, if a wrong-grade comparison blade is admitted, or if "
        "identity/half-turn/full-turn/tiny-angle boundaries drift."
    ),
    "out_of_scope": [
        "result JSON writes from this authoring packet",
        "runner execution",
        "registry or doc edits",
        "lego promotion",
        "tool-tool coupling",
        "bridge, axis, engine, emergence, topology, manifold, or physics claims",
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
        "grade projection, and rotor sandwich R*B*~R decide the fixed-bivector claim"
    )
except Exception as exc:
    Cl = None
    CLIFFORD_AVAILABLE = False
    CLIFFORD_ERROR = repr(exc)
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {CLIFFORD_ERROR}"
    TOOL_INTEGRATION_DEPTH["clifford"] = None


def _setup_cl3() -> Tuple[Any, Dict[str, Any]]:
    layout, blades = Cl(3)
    return layout, blades


def _coeffs(mv: Any) -> Tuple[float, ...]:
    return tuple(float(value) for value in mv.value)


def _coeff_max_abs(mv: Any) -> float:
    return max(abs(value) for value in _coeffs(mv))


def _mv_close(a: Any, b: Any, tol: float = EPS) -> bool:
    return _coeff_max_abs(a - b) <= tol


def _scalar_part(mv: Any) -> float:
    return _coeffs(mv)[0]


def _grade_residue(mv: Any, allowed_indices: Iterable[int]) -> float:
    allowed = set(allowed_indices)
    return max(
        abs(value)
        for index, value in enumerate(_coeffs(mv))
        if index not in allowed
    )


def _rotor(unit_bivector: Any, theta: float) -> Any:
    return math.cos(theta / 2.0) - math.sin(theta / 2.0) * unit_bivector


def _rotor_norm_report(R: Any) -> Dict[str, Any]:
    right = R * ~R
    left = ~R * R
    return {
        "right_scalar": _scalar_part(right),
        "left_scalar": _scalar_part(left),
        "right_non_scalar_residue": _grade_residue(right, {0}),
        "left_non_scalar_residue": _grade_residue(left, {0}),
        "admitted_by_unit_norm_gate": (
            abs(_scalar_part(right) - 1.0) <= EPS
            and abs(_scalar_part(left) - 1.0) <= EPS
            and _grade_residue(right, {0}) <= EPS
            and _grade_residue(left, {0}) <= EPS
        ),
    }


def _unit_rotor_cases(blades: Dict[str, Any]) -> Iterable[Tuple[str, Any, float]]:
    return (
        ("same_plane_e13_pi_over_3", blades["e13"], math.pi / 3.0),
        ("cross_plane_e12_pi_over_5", blades["e12"], math.pi / 5.0),
        ("cross_plane_e23_pi_over_7", blades["e23"], math.pi / 7.0),
    )


def _all_entries_survived(section: Dict[str, Any]) -> bool:
    return all(bool(entry.get("survived", False)) for entry in section.values())


def run_positive_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"survived": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    fixed_bivector = blades["e13"]
    bivector_grade_indices = {4, 5, 6}
    results: Dict[str, Any] = {}

    for label, bivector, theta in _unit_rotor_cases(blades):
        R = _rotor(bivector, theta)
        sandwiched = R * fixed_bivector * ~R
        grade_residue = _grade_residue(sandwiched, bivector_grade_indices)
        norm_report = _rotor_norm_report(R)
        results[f"{label}_bivector_grade_admitted"] = {
            "rotor_norm": norm_report,
            "sandwich_grade_residue": grade_residue,
            "fixed_bivector_surface_admitted": grade_residue <= EPS,
            "survived": norm_report["admitted_by_unit_norm_gate"] and grade_residue <= EPS,
        }
    return results


def run_negative_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"survived": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    nontrivial_rotor = _rotor(blades["e12"], math.pi / 2.0)
    vector_blade = blades["e1"]
    vector_sandwiched = nontrivial_rotor * vector_blade * ~nontrivial_rotor
    vector_grade_residue = _grade_residue(vector_sandwiched, {4, 5, 6})

    non_unit_candidate = 1.0 + 0.5 * blades["e13"]
    non_unit_norm = _rotor_norm_report(non_unit_candidate)

    wrong_reference = blades["e1"]
    fixed_bivector = blades["e13"]

    return {
        "vector_blade_excluded_as_bivector_surface_substitute": {
            "comparison_blade": "e1",
            "bivector_grade_residue": vector_grade_residue,
            "bivector_surface_admitted": vector_grade_residue <= EPS,
            "survived": vector_grade_residue > EPS,
        },
        "non_unit_even_multivector_excluded_by_norm_gate": {
            "candidate_norm": non_unit_norm,
            "unit_norm_gate_admitted": non_unit_norm["admitted_by_unit_norm_gate"],
            "survived": not non_unit_norm["admitted_by_unit_norm_gate"],
        },
        "wrong_grade_reference_excluded_from_fixed_blade_e13": {
            "comparison_blade": "e1",
            "delta_from_fixed_bivector": _coeff_max_abs(wrong_reference - fixed_bivector),
            "fixed_bivector_reference_admitted": _mv_close(wrong_reference, fixed_bivector),
            "survived": not _mv_close(wrong_reference, fixed_bivector),
        },
    }


def run_boundary_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"survived": False, "error": CLIFFORD_ERROR}}

    _, blades = _setup_cl3()
    fixed_bivector = blades["e13"]
    one = 1.0 + 0.0 * blades["e1"]
    minus_one = -1.0 + 0.0 * blades["e1"]
    boundary_rotors = {
        "zero_angle_identity": _rotor(blades["e13"], 0.0),
        "same_plane_pi_half_turn": _rotor(blades["e13"], math.pi),
        "two_pi_minus_one": _rotor(blades["e13"], 2.0 * math.pi),
        "tiny_angle_near_identity": _rotor(blades["e13"], 1e-8),
    }

    results: Dict[str, Any] = {}
    for label, R in boundary_rotors.items():
        sandwiched = R * fixed_bivector * ~R
        delta = _coeff_max_abs(sandwiched - fixed_bivector)
        norm_report = _rotor_norm_report(R)
        results[f"{label}_fixed_bivector_boundary"] = {
            "rotor_norm": norm_report,
            "is_identity_representative": _mv_close(R, one),
            "is_minus_one_representative": _mv_close(R, minus_one),
            "sandwich_delta_from_fixed_bivector": delta,
            "survived": norm_report["admitted_by_unit_norm_gate"] and delta <= EPS,
        }
    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_survived = (
        _all_entries_survived(positive)
        and _all_entries_survived(negative)
        and _all_entries_survived(boundary)
    )

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
            "all_survived": bool(all_survived),
            "promotion_allowed": False,
            "classification": "tool_lego_fit_probe",
            "scope_note": (
                "Tool-lego fit probe only. This switched neighbor checks the "
                "Cl(3) fixed-bivector sandwich surface and cannot be cited as "
                "canonical, bridge, QIT, GStack, axis, manifold, or "
                "nonclassical admission."
            ),
            "survived_sections": {
                "positive": _all_entries_survived(positive),
                "negative": _all_entries_survived(negative),
                "boundary": _all_entries_survived(boundary),
            },
        },
        "all_survived": bool(all_survived),
        "criteria_checked": [
            "C1_unit_rotor_reverse_product_norm_gate",
            "C2_fixed_bivector_e13_remains_grade_2_under_R_B_reverse_R",
            "C3_wrong_grade_vector_blade_excluded_as_bivector_surface_substitute",
            "C4_non_unit_even_candidate_excluded_by_norm_gate",
            "C5_identity_same_plane_half_turn_full_turn_tiny_angle_boundaries_keep_fixed_bivector",
        ],
        "surviving_alternatives": [
            "Other fixed bivector blades and signatures remain separate micro surfaces.",
            "Vector and pseudoscalar fixed-blade sandwich surfaces are not re-promoted here.",
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
    print(f"{'SURVIVED' if all_survived else 'EXCLUDED'} -> {out_path}")
    if not all_survived:
        raise SystemExit(1)
