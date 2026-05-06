#!/usr/bin/env python3
"""
sim_clifford_spinor_double_cover_micro.py -- Clifford Spin(3) sign micro.

This is Tier A tool-stage evidence for one Clifford surface:

    clifford.Cl(3) even rotors -> R and -R sandwich action on vectors.

It is intentionally below lego stage. It does not promote a lego, does not
couple tools, and does not claim Hopf topology, chirality, bridge evidence, or
global spin geometry.
"""

import json
import math
import os
from typing import Any, Dict, Tuple

import numpy as np

classification = "canonical"
NAME = "sim_clifford_spinor_double_cover_micro"
PROBE_FAMILY = "M_clifford_spinor_double_cover_micro"
CONSTRAINT_SET = "C_spin3_rotor_sign_same_vector_sandwich_action"
EPS = 1e-10

_NOT_USED_REASON = (
    "not used: this micro isolates one Clifford Cl(3) rotor sign surface only; "
    "cross-tool coupling, lego promotion, topology, and bridge claims are out of scope."
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
    "function_surface": "clifford.Cl(3) even rotor sign and vector sandwich action",
    "micro_claim": (
        "In Cl(3), a unit even rotor R and its sign partner -R induce the same "
        "sandwich action on vectors, while the rotor signs remain distinct as "
        "spinor-adjacent representatives."
    ),
    "lego_target": "minimal Cl(3) Spin(3) double-cover sign fixture; pre-lego only",
    "function_receipt": "new",
    "prior_function_receipts": [],
    "why_this_lego": (
        "The fixture isolates the sign-equivalence gate needed before any later "
        "spinor-adjacent Clifford work can use rotor representatives safely."
    ),
    "positive_case": "A unit rotor and its negative produce identical vector sandwich outputs for several test vectors.",
    "negative_case": "A non-unit even multivector is excluded by the unit norm gate and by vector norm drift under sandwich action.",
    "boundary_case": "Identity, 2*pi sign flip, and 4*pi return preserve the vector action boundary.",
    "demotion_condition": (
        "Demote this Clifford surface if R and -R differ on any tested vector "
        "sandwich action by more than 1e-10, if either sign fails the unit norm "
        "gate, if a non-unit even candidate is admitted, or if boundary identity/"
        "2*pi/4*pi behavior fails."
    ),
    "out_of_scope": [
        "Hopf fibration topology",
        "spinor chirality",
        "global spin structures",
        "SO(3) matrix reconstruction",
        "non-Euclidean signatures",
        "tool-tool coupling",
        "lego promotion",
        "bridge, coexistence, topology-variant, emergence, or axis-level claims",
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
        "and rotor sandwich action certify the Spin(3) sign-equivalence gate"
    )
except Exception as exc:
    Cl = None
    CLIFFORD_AVAILABLE = False
    CLIFFORD_ERROR = repr(exc)
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = f"import failed: {CLIFFORD_ERROR}"
    TOOL_INTEGRATION_DEPTH["clifford"] = None


def _setup_cl3() -> Tuple[Any, Dict[str, Any], Any, Any, Any]:
    layout, blades = Cl(3)
    return layout, blades, blades["e1"], blades["e2"], blades["e3"]


def _coeffs(mv: Any) -> np.ndarray:
    return np.asarray(mv.value, dtype=float).reshape(-1)


def _mv_close(a: Any, b: Any, tol: float = EPS) -> bool:
    return bool(np.allclose(_coeffs(a - b), 0.0, atol=tol))


def _coeff_max_abs(mv: Any) -> float:
    return float(np.linalg.norm(_coeffs(mv), ord=np.inf))


def _scalar_part(mv: Any) -> float:
    return float(_coeffs(mv)[0])


def _non_scalar_norm(mv: Any) -> float:
    coeffs = _coeffs(mv).copy()
    coeffs[0] = 0.0
    return float(np.linalg.norm(coeffs, ord=np.inf))


def _rotor(unit_bivector: Any, theta: float) -> Any:
    return math.cos(theta / 2.0) - math.sin(theta / 2.0) * unit_bivector


def _vector_norm2(v: Any) -> float:
    return _scalar_part(v * v)


def _rotor_norm_report(R: Any) -> Dict[str, Any]:
    right = R * ~R
    left = ~R * R
    right_scalar = _scalar_part(right)
    left_scalar = _scalar_part(left)
    right_non_scalar = _non_scalar_norm(right)
    left_non_scalar = _non_scalar_norm(left)
    return {
        "right_scalar": right_scalar,
        "left_scalar": left_scalar,
        "right_non_scalar_norm": right_non_scalar,
        "left_non_scalar_norm": left_non_scalar,
        "pass": (
            abs(right_scalar - 1.0) <= EPS
            and abs(left_scalar - 1.0) <= EPS
            and right_non_scalar <= EPS
            and left_non_scalar <= EPS
        ),
    }


def _excluded_norm_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Negative fixtures must not expose nested pass=False fields in canonical JSON."""
    trimmed = dict(report)
    trimmed["unit_norm_gate_admitted"] = bool(trimmed.pop("pass"))
    return trimmed


def _same_sandwich_report(R: Any, v: Any) -> Dict[str, Any]:
    pos = R * v * ~R
    neg = (-R) * v * ~(-R)
    before_norm = _vector_norm2(v)
    pos_norm = _vector_norm2(pos)
    neg_norm = _vector_norm2(neg)
    delta = _coeff_max_abs(pos - neg)
    return {
        "same_action_delta_inf": delta,
        "vector_norm_before": before_norm,
        "positive_sign_vector_norm_after": pos_norm,
        "negative_sign_vector_norm_after": neg_norm,
        "same_action": delta <= EPS,
        "positive_sign_preserves_norm": abs(pos_norm - before_norm) <= EPS,
        "negative_sign_preserves_norm": abs(neg_norm - before_norm) <= EPS,
        "pass": (
            delta <= EPS
            and abs(pos_norm - before_norm) <= EPS
            and abs(neg_norm - before_norm) <= EPS
        ),
    }


def _all_entries_pass(section: Dict[str, Any]) -> bool:
    return all(bool(entry.get("pass", False)) for entry in section.values())


def run_positive_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, e2, e3 = _setup_cl3()
    vectors = {
        "e1": e1,
        "mixed_vector": 0.5 * e1 - 0.25 * e2 + 0.75 * e3,
        "off_axis_vector": -0.2 * e1 + 0.4 * e2 + 0.9 * e3,
    }
    rotors = {
        "e12_pi_over_3": _rotor(blades["e12"], math.pi / 3.0),
        "e13_pi_over_5": _rotor(blades["e13"], math.pi / 5.0),
        "e23_pi_over_7": _rotor(blades["e23"], math.pi / 7.0),
    }

    results: Dict[str, Any] = {}
    for rotor_label, R in rotors.items():
        norm_R = _rotor_norm_report(R)
        norm_neg_R = _rotor_norm_report(-R)
        all_vector_reports = {
            vector_label: _same_sandwich_report(R, v)
            for vector_label, v in vectors.items()
        }
        results[f"{rotor_label}_R_and_minus_R_same_vector_action"] = {
            "R_norm": norm_R,
            "minus_R_norm": norm_neg_R,
            "R_and_minus_R_are_distinct_representatives": not _mv_close(R, -R),
            "vector_reports": all_vector_reports,
            "pass": (
                norm_R["pass"]
                and norm_neg_R["pass"]
                and not _mv_close(R, -R)
                and _all_entries_pass(all_vector_reports)
            ),
        }
    return results


def run_negative_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, e2, e3 = _setup_cl3()
    v = e1 + 0.5 * e2 - 0.2 * e3

    non_unit_even = 1.0 + 0.5 * blades["e12"]
    non_unit_norm = _rotor_norm_report(non_unit_even)
    non_unit_action = non_unit_even * v * ~non_unit_even
    non_unit_drift = abs(_vector_norm2(non_unit_action) - _vector_norm2(v))

    scaled_rotor = 1.25 * _rotor(blades["e23"], math.pi / 4.0)
    scaled_norm = _rotor_norm_report(scaled_rotor)
    scaled_action = scaled_rotor * v * ~scaled_rotor
    scaled_drift = abs(_vector_norm2(scaled_action) - _vector_norm2(v))

    return {
        "non_unit_even_multivector_excluded": {
            "candidate_norm": _excluded_norm_report(non_unit_norm),
            "vector_norm_before": _vector_norm2(v),
            "vector_norm_after": _vector_norm2(non_unit_action),
            "norm_drift": non_unit_drift,
            "unit_norm_gate_admitted": non_unit_norm["pass"],
            "pass": not non_unit_norm["pass"] and non_unit_drift > EPS,
        },
        "scaled_rotor_excluded_despite_same_sign_cancellation_pattern": {
            "candidate_norm": _excluded_norm_report(scaled_norm),
            "vector_norm_before": _vector_norm2(v),
            "vector_norm_after": _vector_norm2(scaled_action),
            "norm_drift": scaled_drift,
            "unit_norm_gate_admitted": scaled_norm["pass"],
            "pass": not scaled_norm["pass"] and scaled_drift > EPS,
        },
    }


def run_boundary_tests() -> Dict[str, Any]:
    if not CLIFFORD_AVAILABLE:
        return {"clifford_import_required": {"pass": False, "error": CLIFFORD_ERROR}}

    _, blades, e1, e2, e3 = _setup_cl3()
    v = 0.3 * e1 - 0.7 * e2 + 0.4 * e3
    one = 1.0 + 0.0 * e1
    minus_one = -1.0 + 0.0 * e1

    identity = _rotor(blades["e12"], 0.0)
    two_pi = _rotor(blades["e12"], 2.0 * math.pi)
    four_pi = _rotor(blades["e12"], 4.0 * math.pi)

    identity_action = identity * v * ~identity
    two_pi_action = two_pi * v * ~two_pi
    four_pi_action = four_pi * v * ~four_pi

    return {
        "identity_rotor_is_positive_sign_boundary": {
            **_rotor_norm_report(identity),
            "is_identity": _mv_close(identity, one),
            "preserves_vector_action": _mv_close(identity_action, v),
            "pass": _rotor_norm_report(identity)["pass"] and _mv_close(identity, one) and _mv_close(identity_action, v),
        },
        "two_pi_rotor_is_minus_one_but_same_vector_action": {
            **_rotor_norm_report(two_pi),
            "is_minus_one": _mv_close(two_pi, minus_one),
            "distinct_from_identity": not _mv_close(two_pi, one),
            "preserves_vector_action": _mv_close(two_pi_action, v),
            "pass": (
                _rotor_norm_report(two_pi)["pass"]
                and _mv_close(two_pi, minus_one)
                and not _mv_close(two_pi, one)
                and _mv_close(two_pi_action, v)
            ),
        },
        "four_pi_rotor_returns_identity_and_same_vector_action": {
            **_rotor_norm_report(four_pi),
            "is_identity": _mv_close(four_pi, one),
            "preserves_vector_action": _mv_close(four_pi_action, v),
            "pass": _rotor_norm_report(four_pi)["pass"] and _mv_close(four_pi, one) and _mv_close(four_pi_action, v),
        },
        "two_pi_and_identity_are_distinct_representatives_same_action": {
            "representative_delta_inf": _coeff_max_abs(two_pi - identity),
            "action_delta_inf": _coeff_max_abs(two_pi_action - identity_action),
            "pass": _coeff_max_abs(two_pi - identity) > 1.0 and _coeff_max_abs(two_pi_action - identity_action) <= EPS,
        },
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = _all_entries_pass(positive) and _all_entries_pass(negative) and _all_entries_pass(boundary)

    results = {
        "name": NAME,
        "classification": classification if all_pass and CLIFFORD_AVAILABLE else "classical_baseline",
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
            "scope_note": (
                "Tier A pre-lego Clifford Spin(3) sign micro only; no queue, "
                "ledger, coupling, Hopf, chirality, topology, or bridge claim."
            ),
            "passed_sections": {
                "positive": _all_entries_pass(positive),
                "negative": _all_entries_pass(negative),
                "boundary": _all_entries_pass(boundary),
            },
        },
        "all_pass": bool(all_pass),
        "criteria_checked": [
            "C1_unit_rotor_and_negative_have_unit_reverse_product_norm",
            "C2_R_and_minus_R_are_distinct_multivector_representatives",
            "C3_R_and_minus_R_have_identical_vector_sandwich_action",
            "C4_non_unit_even_multivectors_are_excluded_by_norm_and_action_checks",
            "C5_identity_2pi_4pi_boundaries_preserve_expected_sign_and_vector_action",
        ],
        "surviving_alternatives": [
            "Orientation-sign conventions for the bivector exponential remain separate from this sign-equivalence claim.",
            "Other signatures and full spinor module actions remain future micro surfaces.",
        ],
        "claim_ceiling": "tool_function_micro_only",
        "next_lego_target": "minimal Spin(3) double-cover sign fixture before spinor-adjacent claims",
        "promotion_condition": (
            "requires a later admitted lego row that names this exact function "
            "receipt and passes strict runner admission; this MICRO row does "
            "not promote the lego"
        ),
        "blocked_until": (
            "blocked until a downstream queue row declares the exact lego "
            "target, parent receipts, and active stage gate for promotion"
        ),
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
