#!/usr/bin/env python3
"""
Tier A A0.6 tool-capability probe for clifford.

Thin capability scope only: clifford is the only manifested tool, and every test
uses geometric algebra operations that stop being meaningful if the package is
removed. This probe is canonical by process, but it remains a capability probe
rather than a tool-lego-integration probe.
"""

import json
import os
from math import isclose, sqrt

classification = "canonical"
NAME = "tool_capability_clifford"
SCOPE_NOTE = "Tier A clifford capability probe: isolated blade, rotor, reverse, and norm behavior only."

TOOL_MANIFEST = {
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "clifford is the sole geometric algebra substrate used to compose blades, rotors, reverses, and norm checks in every test section.",
    }
}

TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing"}
CANONICAL_TOOL_NAMES = (
    "pytorch",
    "pyg",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
)
for _tool_name in CANONICAL_TOOL_NAMES:
    TOOL_MANIFEST.setdefault(
        _tool_name,
        {
            "tried": False,
            "used": False,
            "reason": f"not used; {NAME} isolates clifford capability only",
        },
    )
    TOOL_INTEGRATION_DEPTH.setdefault(_tool_name, None)


def _row_passes(row):
    if row.get("status") == "skipped":
        return False
    if "pass" in row:
        return bool(row["pass"])
    if "claim_excluded" in row:
        return bool(row["claim_excluded"])
    return False


def _section_passes(section):
    return bool(section) and all(_row_passes(row) for row in section.values())

try:
    from clifford import Cl

    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    Cl = None
    TOOL_MANIFEST["clifford"]["reason"] = "clifford import failed on this machine; queue execution will show whether the package is installed."


def _mark_clifford_used() -> None:
    TOOL_MANIFEST["clifford"]["used"] = True


def _serialize(value):
    if isinstance(value, dict):
        return {str(k): _serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(v) for v in value]
    if hasattr(value, "value"):
        return [float(x) for x in value.value]
    return value


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["clifford"]["tried"]:
        results["clifford_import_gate"] = {
            "status": "skipped",
            "reason": "clifford not importable",
        }
        return results

    layout, blades = Cl(2)
    one = blades[""]
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]

    _mark_clifford_used()
    results["basis_metric_and_orientation"] = {
        "e1_sq": str(e1 * e1),
        "e2_sq": str(e2 * e2),
        "e12_sq": str(e12 * e12),
        "e1e2": str(e1 * e2),
        "e2e1": str(e2 * e1),
        "expected": {
            "e1_sq": "1",
            "e2_sq": "1",
            "e12_sq": "-1",
            "e1e2": "(1^e12)",
            "e2e1": "-(1^e12)",
        },
        "pass": (e1 * e1 == one) and (e2 * e2 == one) and (e12 * e12 == -one) and (e1 * e2 == e12) and (e2 * e1 == -e12),
    }

    rotor = (one - e12) / sqrt(2)
    rotated = rotor * e1 * ~rotor
    _mark_clifford_used()
    results["quarter_turn_rotor_maps_e1_to_e2"] = {
        "rotor": str(rotor),
        "rotated": str(rotated),
        "rotated_coefficients": _serialize(rotated),
        "expected": str(e2),
        "pass": all(isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-9) for a, b in zip(rotated.value, e2.value)),
    }

    vector = 3 * e1 - 4 * e2
    norm_sq = float((vector * ~vector)[()])
    _mark_clifford_used()
    results["vector_norm_from_geometric_product"] = {
        "vector": str(vector),
        "vector_coefficients": _serialize(vector),
        "norm_sq": norm_sq,
        "expected_norm_sq": 25.0,
        "pass": isclose(norm_sq, 25.0, rel_tol=0.0, abs_tol=1e-9),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["clifford"]["tried"]:
        results["clifford_import_gate"] = {
            "status": "skipped",
            "reason": "clifford not importable",
        }
        return results

    layout, blades = Cl(2)
    one = blades[""]
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]

    _mark_clifford_used()
    results["basis_vectors_do_not_commute"] = {
        "e1e2": str(e1 * e2),
        "e2e1": str(e2 * e1),
        "incorrect_claim": "e1*e2 == e2*e1",
        "claim_excluded": (e1 * e2) != (e2 * e1),
    }

    _mark_clifford_used()
    results["bivector_square_is_not_positive_one"] = {
        "e12_sq": str(e12 * e12),
        "incorrect_claim": "e12*e12 == 1",
        "claim_excluded": (e12 * e12) != one,
    }

    bad_rotor = one - e12
    bad_image = bad_rotor * e1 * ~bad_rotor
    bad_norm_sq = float((bad_image * ~bad_image)[()])
    _mark_clifford_used()
    results["unnormalized_rotor_fails_norm_preservation"] = {
        "bad_rotor": str(bad_rotor),
        "image": str(bad_image),
        "image_coefficients": _serialize(bad_image),
        "image_norm_sq": bad_norm_sq,
        "expected_if_normalized": 1.0,
        "claim_excluded": not isclose(bad_norm_sq, 1.0, rel_tol=0.0, abs_tol=1e-9),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["clifford"]["tried"]:
        results["clifford_import_gate"] = {
            "status": "skipped",
            "reason": "clifford not importable",
        }
        return results

    layout, blades = Cl(2)
    one = blades[""]
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]
    zero = 0 * one

    zero_norm_sq = float((zero * ~zero)[()])
    _mark_clifford_used()
    results["zero_vector_stays_null"] = {
        "zero": str(zero),
        "norm_sq": zero_norm_sq,
        "pass": isclose(zero_norm_sq, 0.0, rel_tol=0.0, abs_tol=1e-9),
    }

    identity_image = one * (e1 + e2) * ~one
    target = e1 + e2
    _mark_clifford_used()
    results["identity_rotor_is_exact_boundary_case"] = {
        "identity_rotor": str(one),
        "image": str(identity_image),
        "expected": str(target),
        "pass": all(isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-9) for a, b in zip(identity_image.value, target.value)),
    }

    half_turn = e12
    flipped = half_turn * e1 * ~half_turn
    expected = -e1
    _mark_clifford_used()
    results["half_turn_rotor_flips_e1"] = {
        "rotor": str(half_turn),
        "image": str(flipped),
        "expected": str(expected),
        "pass": all(isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-9) for a, b in zip(flipped.value, expected.value)),
    }

    return results


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    summary = {
        "positive_all_pass": _section_passes(positive),
        "negative_all_pass": _section_passes(negative),
        "boundary_all_pass": _section_passes(boundary),
        "promotion_allowed": False,
        "claim_ceiling": "isolated_clifford_capability_only",
        "scope_note": SCOPE_NOTE,
    }
    summary["all_pass"] = bool(summary["positive_all_pass"] and summary["negative_all_pass"] and summary["boundary_all_pass"])
    results = {
        "name": NAME,
        "classification": classification,
        "classification_note": SCOPE_NOTE,
        "divergence_log": SCOPE_NOTE,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(_serialize(results), handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
