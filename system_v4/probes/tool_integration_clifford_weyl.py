#!/usr/bin/env python3
"""
Tier A A4.4 tool-lego-integration probe for clifford + SymPy Weyl data.

SymPy is load-bearing for exact Weyl spinor amplitudes, Bloch-vector expectations,
and symbolic half-angle coefficients. clifford is load-bearing for rotor transport in
Cl(3) using those SymPy-derived coefficients. Each test section feeds symbolic output
into clifford, then pulls the clifford image back against the symbolic target.

Hermes workers save and enqueue this probe but do not execute it directly.
"""

import json
import os
from math import isclose
from typing import Any, Dict, List

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"
NAME = "tool_integration_clifford_weyl"

_NOT_USED_REASON = (
    "not used: this integration probe isolates SymPy Weyl symbolic data and "
    "clifford Cl(3) rotor transport; other tools and promotion surfaces are out of scope."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "clifford is the load-bearing geometric algebra layer: it consumes the SymPy-derived half-angle data to build rotors in Cl(3) and transport the reference axis into the Weyl Bloch direction.",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "SymPy is the load-bearing symbolic layer: it constructs exact Weyl spinors, extracts Bloch-vector expectations, and provides the half-angle coefficients that feed clifford rotor construction.",
    },
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "clifford": "load_bearing",
    "sympy": "load_bearing",
}

CANDIDATE_SIM_SPEC = {
    "operation_sequence": [
        "construct exact normalized two-component Weyl spinor amplitudes with SymPy from finite theta/phi fixtures",
        "derive exact Bloch-vector expectation coordinates and half-angle coefficients from the spinor",
        "build a Cl(3) rotor from the SymPy-derived half-angle coefficients",
        "transport the reference axis e3 by R * e3 * ~R in clifford",
        "compare clifford vector coefficients against the SymPy Bloch-vector target",
        "run wrong-azimuth, unnormalized-spinor, north-pole, and south-pole controls",
    ],
    "carrier_topology": (
        "finite Cl(3) rotor and Bloch-vector fixture derived from exact "
        "two-component Weyl spinor coordinates; tool-integration only, with "
        "no broad Weyl transport, GStack, axis, bridge, QIT, or nonclassical claim"
    ),
    "observable": (
        "maximum absolute coordinate error and residual norm between the "
        "clifford-transported vector and SymPy Bloch target, plus wrong-azimuth "
        "residual, unnormalized target norm mismatch, and pole-boundary transport"
    ),
    "pass_fail_predicate": (
        "pass iff equatorial and generic rotor transports match their SymPy "
        "targets within tolerance; wrong azimuth is excluded; unnormalized spinor "
        "target is excluded; north- and south-pole boundaries match declared vectors"
    ),
    "graveyards": [
        "wrong azimuth sign must fail target matching",
        "unnormalized spinor target must fail unit-transport norm agreement",
        "north-pole boundary must reduce to identity transport onto +e3",
        "south-pole boundary must survive half-turn transport onto -e3",
        "missing SymPy or clifford import gate blocks execution",
    ],
    "baselines": [
        "SymPy Bloch-vector target",
        "unit-vector norm baseline for rotor transport",
        "wrong-azimuth counterfactual",
        "unnormalized-spinor counterfactual",
        "north- and south-pole boundary baselines",
    ],
    "alternative_formulations": [
        "explicit Pauli-matrix spinor expectation numeric baseline",
        "quaternion or SU(2) rotor construction for the same fixtures",
        "additional finite theta/phi fixture sweep before any broad transport claim",
    ],
    "tool_function_needs": [
        "sympy.cos, sympy.sin, sympy.exp, sympy.simplify, sympy.re, sympy.im, sympy.Abs",
        "clifford.Cl(3), basis blades e1/e2/e3/e12/e13, rotor product, and reverse",
    ],
    "lego_coupling_target": (
        "bounded SymPy-to-clifford rotor transport tool-integration evidence "
        "before Weyl transport lego-fit or coupling-stage packets"
    ),
    "claim_ceiling": (
        "finite tool_integration_clifford_weyl tool-integration receipt only; "
        "no bridge, GStack, axis, QIT, or nonclassical admission"
    ),
}

try:
    import sympy as sp

    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "SymPy import failed on this machine; queue execution will decide whether exact Weyl symbolic data is available."

try:
    from clifford import Cl

    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    Cl = None
    TOOL_MANIFEST["clifford"]["reason"] = "clifford import failed on this machine; queue execution will decide whether rotor transport over Weyl targets is available."


if Cl is not None:
    LAYOUT, BLADES = Cl(3)
    ONE = BLADES[""]
    E1 = BLADES["e1"]
    E2 = BLADES["e2"]
    E3 = BLADES["e3"]
    E12 = BLADES["e12"]
    E13 = BLADES["e13"]
else:
    LAYOUT = BLADES = ONE = E1 = E2 = E3 = E12 = E13 = None


def _mark_used(*tools: str) -> None:
    for tool in tools:
        TOOL_MANIFEST[tool]["used"] = True


def _to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if sp is not None and isinstance(value, sp.Basic):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _to_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(v) for v in value]
    if hasattr(value, "value"):
        return [float(x) for x in value.value]
    return value


def _gate_results(section: str) -> Dict[str, Any]:
    missing = []
    if not TOOL_MANIFEST["sympy"]["tried"]:
        missing.append("sympy")
    if not TOOL_MANIFEST["clifford"]["tried"]:
        missing.append("clifford")
    return {f"{section}_import_gate": {"status": "skipped", "missing": missing}}


def _weyl_symbolics(theta, phi, *, normalized: bool = True) -> Dict[str, Any]:
    alpha = sp.simplify(sp.cos(theta / 2))
    beta = sp.simplify(sp.exp(sp.I * phi) * sp.sin(theta / 2))
    norm = sp.simplify(sp.conjugate(alpha) * alpha + sp.conjugate(beta) * beta)
    if normalized:
        alpha = sp.simplify(alpha / sp.sqrt(norm))
        beta = sp.simplify(beta / sp.sqrt(norm))
        norm = sp.Integer(1)

    x = sp.simplify(2 * sp.re(sp.conjugate(alpha) * beta))
    y = sp.simplify(2 * sp.im(sp.conjugate(alpha) * beta))
    z = sp.simplify(sp.conjugate(alpha) * alpha - sp.conjugate(beta) * beta)
    half_angle = {
        "cos_theta_over_2": sp.simplify(sp.Abs(alpha)),
        "sin_theta_over_2": sp.simplify(sp.Abs(beta)),
        "phi": sp.simplify(phi),
    }
    return {
        "spinor": [sp.simplify(alpha), sp.simplify(beta)],
        "bloch": [sp.simplify(x), sp.simplify(y), sp.simplify(z)],
        "norm": sp.simplify(norm),
        "half_angle": half_angle,
    }


def _rotor_from_symbolics(half_angle: Dict[str, Any], phi_override=None):
    phi_value = half_angle["phi"] if phi_override is None else phi_override
    cos_half = float(sp.N(half_angle["cos_theta_over_2"]))
    sin_half = float(sp.N(half_angle["sin_theta_over_2"]))
    cos_phi = float(sp.N(sp.cos(phi_value / 2)))
    sin_phi = float(sp.N(sp.sin(phi_value / 2)))

    polar_rotor = cos_half * ONE + sin_half * E13
    azimuth_rotor = cos_phi * ONE - sin_phi * E12
    rotor = azimuth_rotor * polar_rotor
    _mark_used("sympy", "clifford")
    return rotor


def _coefficients(multivector) -> List[float]:
    return [float(multivector[E1]), float(multivector[E2]), float(multivector[E3])]


def _transport_from_symbolics(symbolics: Dict[str, Any], *, phi_override=None) -> Dict[str, Any]:
    rotor = _rotor_from_symbolics(symbolics["half_angle"], phi_override=phi_override)
    rotated = rotor * E3 * ~rotor
    clifford_xyz = _coefficients(rotated)
    expected_xyz = [float(sp.N(component)) for component in symbolics["bloch"]]
    abs_errors = [abs(a - b) for a, b in zip(clifford_xyz, expected_xyz)]
    target_mv = expected_xyz[0] * E1 + expected_xyz[1] * E2 + expected_xyz[2] * E3
    delta = rotated - target_mv
    residual_norm = float(abs((delta * ~delta)[()]) ** 0.5)
    return {
        "spinor_from_sympy": [str(v) for v in symbolics["spinor"]],
        "bloch_from_sympy": [str(v) for v in symbolics["bloch"]],
        "expected_xyz": expected_xyz,
        "rotor": str(rotor),
        "clifford_xyz": clifford_xyz,
        "abs_errors": abs_errors,
        "max_abs_error": max(abs_errors) if abs_errors else 0.0,
        "residual_norm": residual_norm,
        "matches_target": all(error <= 1e-9 for error in abs_errors),
    }


def _is_identity_rotor(rotor) -> bool:
    if ONE is None:
        return False
    delta = rotor - ONE
    return isclose(float(abs((delta * ~delta)[()]) ** 0.5), 0.0, rel_tol=0.0, abs_tol=1e-9)


def run_positive_tests():
    if sp is None or Cl is None:
        return _gate_results("positive")

    results = {}

    equatorial = _weyl_symbolics(sp.pi / 2, sp.pi / 2)
    results["sympy_weyl_spinor_feeds_clifford_equatorial_transport"] = _transport_from_symbolics(equatorial)

    generic = _weyl_symbolics(sp.pi / 3, sp.pi / 4)
    results["generic_weyl_symbolics_feed_clifford_rotor_transport"] = _transport_from_symbolics(generic)

    return results


def run_negative_tests():
    if sp is None or Cl is None:
        return _gate_results("negative")

    results = {}

    target = _weyl_symbolics(sp.pi / 3, sp.pi / 4)
    wrong_azimuth = _transport_from_symbolics(target, phi_override=-sp.pi / 4)
    wrong_azimuth["counterfactual_phi"] = str(-sp.pi / 4)
    wrong_azimuth["claim_excluded"] = wrong_azimuth["matches_target"] is False
    results["wrong_azimuth_sign_excludes_weyl_transport_match"] = wrong_azimuth

    alpha = sp.Integer(1)
    beta = sp.Integer(1)
    malformed_bloch = [
        sp.simplify(2 * sp.re(sp.conjugate(alpha) * beta)),
        sp.simplify(2 * sp.im(sp.conjugate(alpha) * beta)),
        sp.simplify(sp.conjugate(alpha) * alpha - sp.conjugate(beta) * beta),
    ]
    invalid_target = [float(sp.N(component)) for component in malformed_bloch]
    valid_transport = _transport_from_symbolics(_weyl_symbolics(sp.pi / 2, 0))
    invalid_norm_sq = sum(component * component for component in invalid_target)
    valid_norm_sq = sum(component * component for component in valid_transport["clifford_xyz"])
    _mark_used("sympy", "clifford")
    results["unnormalized_sympy_spinor_excludes_rotor_target_agreement"] = {
        "spinor_from_sympy": [str(alpha), str(beta)],
        "norm_from_sympy": str(sp.simplify(sp.conjugate(alpha) * alpha + sp.conjugate(beta) * beta)),
        "bloch_from_non_normalized_sympy": [str(v) for v in malformed_bloch],
        "invalid_target_xyz": invalid_target,
        "invalid_target_norm_sq": invalid_norm_sq,
        "clifford_unit_transport_xyz": valid_transport["clifford_xyz"],
        "clifford_unit_transport_norm_sq": valid_norm_sq,
        "claim_excluded": not isclose(invalid_norm_sq, valid_norm_sq, rel_tol=0.0, abs_tol=1e-9),
    }

    return results


def run_boundary_tests():
    if sp is None or Cl is None:
        return _gate_results("boundary")

    results = {}

    north_pole = _weyl_symbolics(sp.Integer(0), sp.Integer(0))
    north_transport = _transport_from_symbolics(north_pole)
    north_transport["identity_rotor_expected"] = _is_identity_rotor(_rotor_from_symbolics(north_pole["half_angle"]))
    results["north_pole_boundary_uses_identity_rotor"] = north_transport

    south_pole = _weyl_symbolics(sp.pi, sp.Integer(0))
    south_transport = _transport_from_symbolics(south_pole)
    south_transport["expected_boundary_vector"] = [0.0, 0.0, -1.0]
    south_transport["boundary_match"] = all(
        isclose(a, b, rel_tol=0.0, abs_tol=1e-9)
        for a, b in zip(south_transport["clifford_xyz"], [0.0, 0.0, -1.0])
    )
    results["south_pole_boundary_survives_half_turn_transport"] = south_transport

    return results


def _case_passed(case: Dict[str, Any]) -> bool:
    if case.get("status") == "skipped":
        return False
    if "claim_excluded" in case:
        return bool(case["claim_excluded"])
    if "matches_target" in case:
        return bool(case["matches_target"])
    if "boundary_match" in case:
        return bool(case["boundary_match"])
    if "identity_rotor_expected" in case:
        return bool(case["identity_rotor_expected"])
    return False


def _summarize(*sections: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    cases = []
    for section in sections:
        cases.extend(section.values())
    passed = sum(1 for case in cases if _case_passed(case))
    total = len(cases)
    return {"passed": passed, "total": total, "all_pass": passed == total}


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = _summarize(positive, negative, boundary)
    results = {
        "name": NAME,
        "classification": classification,
        "candidate_sim_spec": CANDIDATE_SIM_SPEC,
        **CANDIDATE_SIM_SPEC,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "surviving_alternatives": [
            "This receipt covers only the named SymPy Weyl spinor fixtures feeding clifford Cl(3) rotor transport; it does not prove broad Weyl transport, bridge, axis, or GStack behavior."
        ],
        "demotion_condition": (
            "Demote this integration surface if SymPy symbolic Bloch vectors no longer "
            "match clifford rotor transport, if wrong azimuth signs are not excluded, "
            "or if unnormalized spinor targets are accepted."
        ),
        "out_of_scope": [
            "no bridge promotion",
            "no axis claim",
            "no GStack claim",
            "no proof of broad Weyl transport",
            "no coupling-stage promotion",
        ],
        "criteria_checked": [
            "SymPy Weyl spinor amplitudes feed clifford equatorial rotor transport",
            "SymPy Weyl spinor amplitudes feed clifford generic rotor transport",
            "wrong azimuth sign is excluded",
            "unnormalized spinor target is excluded",
            "north-pole and south-pole boundary transports survive",
        ],
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }
    results = apply_default_receipt_boundary(
        results,
        source_name=NAME,
        target=(
            "Use as bounded clifford plus SymPy Weyl tool-integration evidence "
            "before any Weyl transport lego-fit or coupling-stage packet."
        ),
    )

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_to_serializable(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
