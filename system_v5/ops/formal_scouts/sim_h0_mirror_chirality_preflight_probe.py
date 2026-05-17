#!/usr/bin/env python3
"""Exact H0/mirror chirality preflight.

Before any broad gamma5/chirality replacement, test the smallest source-native
algebraic precondition: the current `MIRROR = SX` comment can be read as
mapping H_TYPE_ONE to H_TYPE_TWO, but H0 contains an SX component. Exact
conjugation by SX flips SZ and preserves SX, so it is not the same as the full
H sign flip unless H0 is purely diagonal.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np
import sympy as sp
import z3

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "h0_mirror_chirality_preflight_probe_results.json"

NAME = "h0_mirror_chirality_preflight_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "h0_mirror_chirality_preflight"
CLAIM_CEILING = (
    "Formal scout only: exact-matrix preflight for the current H0/SX mirror "
    "chirality convention. It does not admit gamma5 replacement, final "
    "chirality, terrain dynamics, manifold promotion, physics, or canonical "
    "architecture claims."
)

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact rational matrix algebra for H0 and mirror conjugation",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-code matrix comparison against canonical_qit_engine_specs",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness over mirror failure and sign-flip predicates",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, sp.MatrixBase):
        return [[str(value[i, j]) for j in range(value.shape[1])] for i in range(value.shape[0])]
    if isinstance(value, sp.Basic):
        return str(value)
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def max_abs_np(arr: np.ndarray) -> float:
    return float(np.max(np.abs(arr)))


def matrix_equal(a: sp.Matrix, b: sp.Matrix) -> bool:
    return all(sp.simplify(x) == 0 for x in list(a - b))


def z3_preflight_witness(mirror_fails_full_flip: bool, sign_flip_passes: bool, diagonal_control_hides: bool) -> dict[str, Any]:
    solver = z3.Solver()
    mirror_fails = z3.Bool("sx_mirror_does_not_equal_full_h_sign_flip")
    sign_flip = z3.Bool("h_type_two_equals_negative_h0")
    diagonal_hides = z3.Bool("pure_sz_diagonal_control_would_hide_mirror_failure")
    solver.add(mirror_fails == mirror_fails_full_flip)
    solver.add(sign_flip == sign_flip_passes)
    solver.add(diagonal_hides == diagonal_control_hides)
    solver.add(z3.Not(z3.And(mirror_fails, sign_flip, diagonal_hides)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness over exact H0/mirror preflight predicates only.",
    }


def main() -> int:
    started = time.time()
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    h0 = sp.Rational(77, 100) * sz + sp.Rational(13, 100) * sx
    h_type_one = h0
    h_type_two = -h0
    mirror_h = sx * h_type_one * sx
    diagonal_h = sp.Rational(77, 100) * sz
    offdiag_h = sp.Rational(13, 100) * sx
    mirror_diagonal_h = sx * diagonal_h * sx
    mirror_offdiag_h = sx * offdiag_h * sx

    source_h0 = np.asarray(specs.H0, dtype=np.complex128)
    source_type_two = np.asarray(specs.H_TYPE_TWO, dtype=np.complex128)
    exact_h0 = np.asarray(h0.tolist(), dtype=np.complex128)
    exact_type_two = -exact_h0
    source_matches_exact = max_abs_np(source_h0 - exact_h0) < 1e-12
    source_type_two_matches = max_abs_np(source_type_two - exact_type_two) < 1e-12
    mirror_equals_full_flip = matrix_equal(mirror_h, h_type_two)
    sign_flip_passes = matrix_equal(h_type_two, -h0)
    diagonal_control_hides = matrix_equal(mirror_diagonal_h, -diagonal_h)
    offdiag_preserved = matrix_equal(mirror_offdiag_h, offdiag_h)
    residual = sp.simplify(mirror_h - h_type_two)
    z3_witness = z3_preflight_witness(
        mirror_fails_full_flip=not mirror_equals_full_flip,
        sign_flip_passes=sign_flip_passes and source_type_two_matches,
        diagonal_control_hides=diagonal_control_hides and offdiag_preserved,
    )

    repair_receipt = {
        "weak_link": "Gamma5/chirality replacement proposals inherit a local convention risk: canonical_qit_engine_specs comments call SX a mirror, but SX conjugation does not implement the full H0 sign flip when H0 has an SX component.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Any D4/gamma5 chirality replacement must first distinguish SX-conjugation from H sign flip plus ladder swap.",
        "dependency_subset": ["canonical_qit_engine_specs.H0/H_TYPE_ONE/H_TYPE_TWO/MIRROR"],
        "stage_fields_touched_or_consumed": [],
        "before_baseline/hash": {
            "source_file": str(ROOT / "canonical_qit_engine_specs.py"),
            "source_h0_matches_exact_77_100_sz_plus_13_100_sx": source_matches_exact,
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "h0_exact": h0,
            "h_type_two_exact": h_type_two,
            "sx_conjugated_h0": mirror_h,
            "sx_conjugation_minus_full_sign_flip": residual,
            "diagonal_control": {
                "mirror_diagonal_equals_negative_diagonal": diagonal_control_hides,
                "mirror_offdiag_equals_offdiag": offdiag_preserved,
            },
        },
        "axis0_outputs_or_blockers": {
            "not_axis0": True,
            "why_relevant": "D4/gamma5 follow-on should not reuse a false mirror identity as a chirality proxy.",
        },
        "provider_inputs_used": {
            "peirce_explorer": "read_only_precondition_scout_recommended_h0_mirror_micro_probe",
            "opus_grok_gemini": "advisory_context_only_not_local_evidence",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "If D4 proceeds, use source-native rho_L/rho_R histories and explicit H sign flip plus ladder swap, not a detached gamma5/SX proxy.",
    }
    positive = {
        "source_h0_coefficients_match_current_code_exactly": {
            "pass": bool(source_matches_exact and source_type_two_matches),
            "source_h0_minus_exact_max_abs": max_abs_np(source_h0 - exact_h0),
            "source_type_two_minus_exact_max_abs": max_abs_np(source_type_two - exact_type_two),
        },
        "sx_mirror_conjugation_is_not_full_h_sign_flip": {
            "pass": bool(not mirror_equals_full_flip),
            "sx_h0_sx": mirror_h,
            "h_type_two": h_type_two,
            "residual_sx_h0_sx_minus_h_type_two": residual,
        },
        "h_type_two_is_explicit_negative_h0": {
            "pass": bool(sign_flip_passes and source_type_two_matches),
            "h_type_two_exact": h_type_two,
        },
        "z3_h0_mirror_preflight_witness_executes": z3_witness,
    }
    graveyards = {
        "diagonal_only_control_would_false_green_the_mirror_claim": {
            "pass": bool(diagonal_control_hides),
            "mirror_diagonal_equals_negative_diagonal": diagonal_control_hides,
            "claim": "A pure SZ H0 would make SX conjugation look like full sign flip; the current SX component prevents that.",
        },
        "sx_component_is_preserved_under_sx_conjugation": {
            "pass": bool(offdiag_preserved),
            "mirror_offdiag_equals_offdiag": offdiag_preserved,
        },
        "detached_gamma5_replacement_not_admitted": {
            "pass": PROMOTION_ALLOWED is False and "does not admit gamma5 replacement" in CLAIM_CEILING,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    boundary = {
        "claim_ceiling_blocks_chirality_or_physics_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "gamma5 replacement", "physics", "canonical"]
            ),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 source-convention preflight over canonical_qit_engine_specs.",
            "It does not promote or replace older gamma/chirality probes.",
        ],
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
