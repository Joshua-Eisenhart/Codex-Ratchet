#!/usr/bin/env python3
"""Symbolic microfit for the 2x2 normalization constraint.

This bounded tool-lego fit splits normalization away from trace-one. It checks
finite two-amplitude state-vector normalization and two-weight mixture
normalization before any density-matrix, bridge, QIT, GStack, axis, engine, or
nonclassical admission claim.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import numpy as np
import sympy as sp
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded symbolic microfit for the normalization constraint on finite 2x2 "
    "state carriers. Sympy proves state-vector and mixture normalization "
    "identities; z3 is supportive for explicit invalid witness rejection; numpy "
    "crosschecks finite witnesses. This is not trace admission, density-matrix "
    "admission, bridge, QIT, GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["normalization_constraint"]
PRIMARY_LEGO_IDS = ["normalization_constraint"]

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic normalization identities for 2-amplitude and 2-weight carriers",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive UNSAT checks rejecting explicit non-normalized witnesses",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite norm, trace, and eigenvalue witness checks",
    },
    "scipy": {"tried": False, "used": False, "reason": "not needed for this exact normalization microfit"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no autograd or tensor dynamics"},
    "cvc5": {"tried": False, "used": False, "reason": "deferred; z3 covers explicit invalid witness rejection"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "supportive",
    "numpy": "supportive",
    "scipy": None,
    "pytorch": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULT = RESULT_DIR / "density_hopf_geometry_results.json"
EPS = 1e-12


def source_receipt() -> dict[str, object]:
    if not PARENT_RESULT.exists():
        return {"path": str(PARENT_RESULT), "exists": False, "all_pass": False}
    data = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(PARENT_RESULT),
        "exists": True,
        "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
        "classification": data.get("classification"),
    }


def sympy_state_vector_normalization() -> dict[str, object]:
    a, b = sp.symbols("a b", real=True)
    norm_expr = sp.simplify(a**2 + b**2)
    denom = sp.sqrt(a**2 + b**2)
    normalized_general_residual = sp.simplify((a / denom) ** 2 + (b / denom) ** 2 - 1)
    theta = sp.symbols("theta", real=True)
    trig_residual = sp.trigsimp(sp.cos(theta) ** 2 + sp.sin(theta) ** 2 - 1)
    bad_norm = sp.simplify(norm_expr.subs({a: sp.Rational(3, 5), b: sp.Rational(3, 5)}))
    return {
        "carrier": "psi=(a,b), real finite 2-amplitude slice",
        "norm_expression": str(norm_expr),
        "normalized_general_residual": str(normalized_general_residual),
        "trig_parametrized_residual": str(trig_residual),
        "bad_witness_norm": str(bad_norm),
        "pass": normalized_general_residual == 0 and trig_residual == 0 and bad_norm != 1,
    }


def sympy_mixture_weight_normalization() -> dict[str, object]:
    p, q = sp.symbols("p q", real=True)
    total = sp.simplify(p + q)
    normalized_residual = sp.simplify(total.subs(q, 1 - p) - 1)
    bad_total = sp.simplify(total.subs({p: sp.Rational(2, 3), q: sp.Rational(2, 3)}))
    return {
        "carrier": "two-weight convex mixture",
        "normalization_expression": str(total),
        "normalized_residual": str(normalized_residual),
        "bad_witness_total": str(bad_total),
        "pass": normalized_residual == 0 and bad_total != 1,
    }


def z3_rejects_invalid_normalization_witnesses() -> dict[str, object]:
    a, b = z3.Reals("a b")
    bad_vector = z3.Solver()
    bad_vector.add(a == z3.RealVal("3") / 5, b == z3.RealVal("3") / 5)
    bad_vector.add(a * a + b * b == 1)
    bad_vector_result = bad_vector.check()

    p, q = z3.Reals("p q")
    bad_weights = z3.Solver()
    bad_weights.add(p == z3.RealVal("2") / 3, q == z3.RealVal("2") / 3)
    bad_weights.add(p + q == 1)
    bad_weight_result = bad_weights.check()
    return {
        "bad_vector_norm_rejected": {"z3_result": str(bad_vector_result), "pass": bad_vector_result == z3.unsat},
        "bad_mixture_weight_sum_rejected": {"z3_result": str(bad_weight_result), "pass": bad_weight_result == z3.unsat},
        "pass": bad_vector_result == z3.unsat and bad_weight_result == z3.unsat,
    }


def numpy_witnesses() -> dict[str, object]:
    valid_vectors = {
        "basis_0": np.asarray([1.0, 0.0]),
        "balanced": np.asarray([1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)]),
    }
    invalid_vectors = {
        "short": np.asarray([0.3, 0.4]),
        "long": np.asarray([0.8, 0.8]),
    }
    valid_rows = {
        name: {"norm_sq": float(np.vdot(vec, vec).real), "pass": bool(abs(float(np.vdot(vec, vec).real) - 1.0) < EPS)}
        for name, vec in valid_vectors.items()
    }
    invalid_rows = {
        name: {"norm_sq": float(np.vdot(vec, vec).real), "pass": bool(abs(float(np.vdot(vec, vec).real) - 1.0) > EPS)}
        for name, vec in invalid_vectors.items()
    }

    normalized_vec = valid_vectors["balanced"]
    rho = np.outer(normalized_vec, normalized_vec)
    trace_check = {
        "normalized_vector_density_trace": float(np.trace(rho)),
        "eigenvalues": [float(v) for v in np.linalg.eigvalsh(rho)],
        "pass": bool(abs(float(np.trace(rho)) - 1.0) < EPS and np.min(np.linalg.eigvalsh(rho)) >= -EPS),
    }
    return {
        "valid_vectors": valid_rows,
        "invalid_vectors": invalid_rows,
        "normalized_vector_density_trace_check": trace_check,
        "pass": all(row["pass"] for row in valid_rows.values())
        and all(row["pass"] for row in invalid_rows.values())
        and trace_check["pass"],
    }


def normalization_alone_does_not_admit_density_matrix() -> dict[str, object]:
    nonhermitian_trace_one = np.asarray([[1.0, 1.0], [0.0, 0.0]], dtype=float)
    hermitian_residual = float(np.max(np.abs(nonhermitian_trace_one - nonhermitian_trace_one.T)))
    return {
        "witness": "[[1,1],[0,0]]",
        "trace": float(np.trace(nonhermitian_trace_one)),
        "hermitian_residual": hermitian_residual,
        "claim_killed": "normalization microfit alone admits density matrix layer",
        "pass": bool(abs(float(np.trace(nonhermitian_trace_one)) - 1.0) < EPS and hermitian_residual > EPS),
    }


def finite_real_2x2_scope_check() -> dict[str, object]:
    vector = np.asarray([1.0, 0.0], dtype=float)
    density = np.outer(vector, vector)
    result = {
        "vector_shape_is_2": {"shape": list(vector.shape), "pass": vector.shape == (2,)},
        "density_shape_is_2x2": {"shape": list(density.shape), "pass": density.shape == (2, 2)},
        "real_dtype_only": {"dtype": str(density.dtype), "pass": np.issubdtype(density.dtype, np.floating)},
    }
    result["pass"] = all(row["pass"] for row in result.values())
    return result


def promotion_boundary_check() -> dict[str, object]:
    result = {
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
        "primary_lego_is_single_normalization_row": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "pass": PRIMARY_LEGO_IDS == ["normalization_constraint"],
        },
        "lego_ids_do_not_credit_neighbor_rows": {
            "lego_ids": LEGO_IDS,
            "pass": LEGO_IDS == ["normalization_constraint"],
        },
    }
    result["pass"] = all(row["pass"] for row in result.values())
    return result


def main() -> None:
    parent = source_receipt()
    positive = {
        "parent_density_hopf_receipt_available": {
            "parent": parent,
            "pass": bool(parent["exists"]),
        },
        "sympy_state_vector_normalization": sympy_state_vector_normalization(),
        "sympy_mixture_weight_normalization": sympy_mixture_weight_normalization(),
        "numpy_witnesses_match_symbolic_boundary": numpy_witnesses(),
    }
    negative = {
        "z3_rejects_invalid_normalization_witnesses": z3_rejects_invalid_normalization_witnesses(),
        "not_full_density_matrix_admission": normalization_alone_does_not_admit_density_matrix(),
    }
    boundary = {
        "finite_real_2x2_family_only": finite_real_2x2_scope_check(),
        "no_qit_gstack_axis_bridge_engine_or_nonclassical_admission": promotion_boundary_check(),
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "normalization_constraint_sympy_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"normalization_constraint": str(PARENT_RESULT)},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "sympy",
            "claim_ceiling": "local_real_2x2_normalization_constraint_microfit_only",
            "parent_receipt_dependency": "source receipt is checked for availability only; parent canonical status is not promoted",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "normalization_constraint_sympy_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
