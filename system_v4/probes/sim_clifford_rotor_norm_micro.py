#!/usr/bin/env python3
"""
sim_clifford_rotor_norm_micro.py -- Clifford rotor-norm MICRO packet.

This is stage-1/3 tool-stage evidence for one function surface:

    clifford.Cl(3) blades -> unit bivector rotor construction ->
    geometric product with reverse (~) -> R * ~R == 1 and R*v*~R norm gate.

It is intentionally pre-lego. It does not promote a Clifford lego, does not
couple to deap/geomstats/e3nn, and does not claim Hopf or bridge evidence.
"""

import json
import math
import os
from typing import Any, Dict, Iterable, Tuple

import numpy as np

classification = "canonical"

MICRO = {
    "tool_target": "clifford",
    "function_surface": "clifford.Cl(3) MultiVector geometric product, reverse (~), and rotor sandwich R*v*~R",
    "micro_claim": "A Cl(3) unit-bivector rotor has scalar norm R*~R == 1, preserves vector norm under sandwich action, and remains unit under rotor composition.",
    "lego_target": "minimal Cl(3) rotor fixture; pre-lego anchor for later Hopf/spinor targets",
    "function_receipt": "new",
    "prior_function_receipts": [],
    "why_this_lego": "The fixture isolates the rotor norm gate required before Clifford rotor surfaces are used in tool-lego or tool-tool coupling work.",
    "positive_case": "Unit rotors built from e12/e13/e23 at several angles satisfy R*~R == ~R*R == 1 and preserve vector norm.",
    "negative_case": "A non-unit even multivector and a non-unit bivector coefficient are excluded by the same norm gate.",
    "boundary_case": "Identity, 2*pi, 4*pi, and tiny-angle rotors stay inside the expected Spin(3) norm boundary.",
    "demotion_condition": "Any unit rotor with |scalar(R*~R)-1| > 1e-10, non-scalar norm residue > 1e-10, or sandwich vector-norm drift > 1e-10 demotes this function surface.",
    "out_of_scope": [
        "Hopf fibration topology",
        "spinor chirality",
        "deap/clifford evolutionary coupling",
        "tool-tool coupling",
        "bridge, coexistence, topology-variant, emergence, or axis-level claims",
    ],
}

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no tensor/autograd surface in this Clifford micro"},
    "pyg": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "z3": {"tried": False, "used": False, "reason": "not needed; this micro isolates numeric Clifford MultiVector operations"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed; no SMT encoding in this micro"},
    "sympy": {"tried": False, "used": False, "reason": "not needed; closed-form trigonometric rotor fixture is evaluated directly"},
    "clifford": {"tried": False, "used": False, "reason": "under test"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; SO(3) matrix geometry is outside this Clifford API micro"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed; Wigner-D/equivariance surfaces are separate"},
    "rustworkx": {"tried": False, "used": False, "reason": "not graph-relevant"},
    "xgi": {"tried": False, "used": False, "reason": "not hypergraph-relevant"},
    "toponetx": {"tried": False, "used": False, "reason": "not topology-relevant"},
    "gudhi": {"tried": False, "used": False, "reason": "not persistence-relevant"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    from clifford import Cl

    CLIFFORD_AVAILABLE = True
    CLIFFORD_ERROR = None
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "load-bearing: Cl(3) blades, MultiVector geometric product, reverse (~), and rotor sandwich certify the norm gate"
    )
except Exception as exc:
    Cl = None
    CLIFFORD_AVAILABLE = False
    CLIFFORD_ERROR = repr(exc)
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {CLIFFORD_ERROR}"
    TOOL_INTEGRATION_DEPTH["clifford"] = None

EPS = 1e-10
NAME = "sim_clifford_rotor_norm_micro"


def _setup_cl3() -> Tuple[Any, Dict[str, Any], Any, Any, Any]:
    layout, blades = Cl(3)
    return layout, blades, blades["e1"], blades["e2"], blades["e3"]


def _coeffs(mv: Any) -> np.ndarray:
    return np.asarray(mv.value, dtype=float).reshape(-1)


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
        "pass": (
            abs(_scalar_part(right) - 1.0) < EPS
            and abs(_scalar_part(left) - 1.0) < EPS
            and _non_scalar_norm(right) < EPS
            and _non_scalar_norm(left) < EPS
        ),
    }


def _vector_norm2(v: Any) -> float:
    return _scalar_part(v * v)


def _is_vector(mv: Any) -> bool:
    return _non_scalar_norm(mv - mv(1)) < EPS and abs(_scalar_part(mv - mv(1))) < EPS


def _unit_rotor_cases(blades: Dict[str, Any]) -> Iterable[Tuple[str, Any, float]]:
    return (
        ("e12_pi_over_6", blades["e12"], math.pi / 6.0),
        ("e12_pi_over_2", blades["e12"], math.pi / 2.0),
        ("e13_pi_over_4", blades["e13"], math.pi / 4.0),
        ("e23_pi", blades["e23"], math.pi),
    )


def run_positive_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, e2, e3 = _setup_cl3()
    test_vector = 0.5 * e1 - 0.25 * e2 + 0.75 * e3

    for label, bivector, theta in _unit_rotor_cases(blades):
        R = _rotor(bivector, theta)
        rotated = R * test_vector * ~R
        before_norm = _vector_norm2(test_vector)
        after_norm = _vector_norm2(rotated)
        norm_report = _rotor_norm_report(R)
        results[f"{label}_unit_rotor_norm_and_sandwich"] = {
            **norm_report,
            "vector_norm_before": before_norm,
            "vector_norm_after": after_norm,
            "sandwich_vector_norm_preserved": abs(after_norm - before_norm) < EPS,
            "sandwich_output_is_vector": _is_vector(rotated),
            "pass": norm_report["pass"] and abs(after_norm - before_norm) < EPS and _is_vector(rotated),
        }

    R1 = _rotor(blades["e12"], math.pi / 5.0)
    R2 = _rotor(blades["e23"], math.pi / 7.0)
    composed = R2 * R1
    results["different_axis_rotor_composition_remains_unit"] = _rotor_norm_report(composed)
    return results


def run_negative_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, e2, e3 = _setup_cl3()
    v = e1 + 0.5 * e2 - 0.2 * e3

    def _excluded_candidate_report(norm_report: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "right_scalar": norm_report["right_scalar"],
            "left_scalar": norm_report["left_scalar"],
            "right_non_scalar_norm": norm_report["right_non_scalar_norm"],
            "left_non_scalar_norm": norm_report["left_non_scalar_norm"],
            "unit_norm_gate_admitted": norm_report["pass"],
        }

    non_unit_even = 1.0 + 0.5 * blades["e12"]
    non_unit_norm = _rotor_norm_report(non_unit_even)
    distorted = non_unit_even * v * ~non_unit_even
    results["non_unit_even_multivector_excluded_by_norm_gate"] = {
        "candidate_norm": _excluded_candidate_report(non_unit_norm),
        "vector_norm_before": _vector_norm2(v),
        "vector_norm_after": _vector_norm2(distorted),
        "pass": not non_unit_norm["pass"] and abs(_vector_norm2(distorted) - _vector_norm2(v)) > EPS,
    }

    bad_bivector_rotor = _rotor(2.0 * blades["e12"], math.pi / 3.0)
    bad_norm = _rotor_norm_report(bad_bivector_rotor)
    bad_rotated = bad_bivector_rotor * v * ~bad_bivector_rotor
    results["non_unit_bivector_coefficient_excluded"] = {
        "candidate_norm": _excluded_candidate_report(bad_norm),
        "vector_norm_before": _vector_norm2(v),
        "vector_norm_after": _vector_norm2(bad_rotated),
        "pass": not bad_norm["pass"] and abs(_vector_norm2(bad_rotated) - _vector_norm2(v)) > EPS,
    }

    odd_candidate = 1.0 + 0.25 * e1
    odd_norm = _rotor_norm_report(odd_candidate)
    results["odd_grade_contamination_excluded"] = {
        "candidate_norm": _excluded_candidate_report(odd_norm),
        "odd_part_norm": float(abs(odd_candidate(1))),
        "pass": not odd_norm["pass"] and float(abs(odd_candidate(1))) > EPS,
    }
    return results


def run_boundary_tests() -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, _, _ = _setup_cl3()
    identity = _rotor(blades["e12"], 0.0)
    two_pi = _rotor(blades["e12"], 2.0 * math.pi)
    four_pi = _rotor(blades["e12"], 4.0 * math.pi)
    tiny = _rotor(blades["e12"], 1e-8)
    near_four_pi = _rotor(blades["e12"], (4.0 * math.pi) + 1e-8)

    results["zero_angle_identity_norm_boundary"] = {
        **_rotor_norm_report(identity),
        "is_identity": _mv_close(identity, 1.0 + 0 * e1),
        "pass": _rotor_norm_report(identity)["pass"] and _mv_close(identity, 1.0 + 0 * e1),
    }
    results["two_pi_is_minus_one_but_unit"] = {
        **_rotor_norm_report(two_pi),
        "is_minus_one": _mv_close(two_pi, -1.0 + 0 * e1),
        "vector_action_identity": _mv_close(two_pi * e1 * ~two_pi, e1),
        "pass": _rotor_norm_report(two_pi)["pass"] and _mv_close(two_pi * e1 * ~two_pi, e1),
    }
    results["four_pi_returns_identity_and_unit"] = {
        **_rotor_norm_report(four_pi),
        "is_identity": _mv_close(four_pi, 1.0 + 0 * e1),
        "pass": _rotor_norm_report(four_pi)["pass"] and _mv_close(four_pi, 1.0 + 0 * e1),
    }
    results["tiny_angle_and_near_four_pi_stay_unit"] = {
        "tiny": _rotor_norm_report(tiny),
        "near_four_pi": _rotor_norm_report(near_four_pi),
        "pass": _rotor_norm_report(tiny)["pass"] and _rotor_norm_report(near_four_pi)["pass"],
    }
    return results


def _all_entries_pass(section: Dict[str, Any]) -> bool:
    return all(bool(entry.get("pass", False)) for entry in section.values())


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = _all_entries_pass(positive) and _all_entries_pass(negative) and _all_entries_pass(boundary)

    results = {
        "name": NAME,
        "classification": "canonical" if all_pass and CLIFFORD_AVAILABLE else "classical_baseline",
        "micro": MICRO,
        "probe_family": "M_clifford_rotor_norm_micro",
        "constraint_set": "C_unit_rotor_reverse_product_norm_gate",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "scope_note": "Pre-lego Clifford rotor norm micro only; no queue, ledger, coupling, Hopf, spinor, or bridge claim.",
        },
        "all_pass": bool(all_pass),
        "criteria_checked": [
            "C1_unit_rotor_reverse_product_is_scalar_one",
            "C2_rotor_sandwich_preserves_vector_norm",
            "C3_rotor_composition_remains_unit",
            "C4_non_unit_even_multivectors_are_excluded",
            "C5_identity_and_2pi_4pi_boundaries_remain_unit",
        ],
        "surviving_alternatives": [
            "The sign convention in cos(theta/2) +/- sin(theta/2)*B remains live for orientation-specific action claims.",
            "Non-Euclidean signatures such as Cl(1,1) remain separate future micro surfaces.",
        ],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if all_pass else 'FAIL'} -> {out_path}")
    if not all_pass:
        raise SystemExit(1)
