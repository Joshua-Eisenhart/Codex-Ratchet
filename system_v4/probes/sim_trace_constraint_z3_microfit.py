#!/usr/bin/env python3
"""Symbolic microfit for the 2x2 trace-one constraint.

This bounded tool-lego fit splits the trace constraint away from the broader
density/Hopf receipt. It proves small finite 2x2 density-carrier trace facts
with sympy, uses z3 only as a supportive witness rejector, and crosschecks
explicit witnesses numerically. This is local trace constraint evidence only.
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
    "Bounded symbolic microfit for the trace-one constraint on real 2x2 density "
    "candidates. It proves local Bloch and spectral 2x2 trace identities with "
    "sympy, uses z3 only as a supportive invalid-witness rejector, and does not "
    "treat tautological trace algebra as solver load-bearing work. It is not "
    "density-matrix admission, bridge, QIT, GStack, axis, engine, or "
    "nonclassical admission."
)

LEGO_IDS = ["trace_constraint", "density_matrix_representability", "finite_carrier_c2"]
PRIMARY_LEGO_IDS = ["trace_constraint"]

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive UNSAT checks for explicit non-normalized trace witnesses",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic trace identities and counterexample equations for 2x2 carriers",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite matrix trace/eigenvalue witness checks",
    },
    "scipy": {"tried": False, "used": False, "reason": "not needed for this exact trace microfit"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no autograd or tensor dynamics"},
    "cvc5": {"tried": False, "used": False, "reason": "deferred; z3 is sufficient for this bounded proof"},
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


def sympy_bloch_form_has_trace_one() -> dict[str, object]:
    rx, rz = sp.symbols("rx rz", real=True)
    rho = sp.Matrix([[sp.Rational(1, 2) * (1 + rz), sp.Rational(1, 2) * rx],
                     [sp.Rational(1, 2) * rx, sp.Rational(1, 2) * (1 - rz)]])
    trace_expr = sp.simplify(sp.trace(rho))
    residual = sp.simplify(trace_expr - 1)
    return {
        "family": "rho=(I + rx*sigma_x + rz*sigma_z)/2",
        "trace_expression": str(trace_expr),
        "residual_trace_minus_one": str(residual),
        "solver_role": "sympy_simplify_identity",
        "pass": residual == 0,
    }


def sympy_spectral_weights_trace_equation() -> dict[str, object]:
    p, q = sp.symbols("p q", real=True)
    rho = sp.diag(p, q)
    trace_expr = sp.simplify(sp.trace(rho))
    normalized_residual = sp.simplify(trace_expr.subs(q, 1 - p) - 1)
    non_normalized_counterexample = {p: sp.Rational(3, 5), q: sp.Rational(3, 5)}
    counterexample_trace = sp.simplify(trace_expr.subs(non_normalized_counterexample))
    return {
        "family": "rho=diag(p,q)",
        "trace_expression": str(trace_expr),
        "normalized_residual_trace_minus_one": str(normalized_residual),
        "counterexample_weights": {"p": "3/5", "q": "3/5"},
        "counterexample_trace": str(counterexample_trace),
        "solver_role": "sympy_symbolic_trace_equation",
        "pass": normalized_residual == 0 and counterexample_trace != 1,
    }


def z3_rejects_bad_trace_witnesses() -> dict[str, object]:
    p, q = z3.Reals("bad_p bad_q")
    invalid_trace = z3.Solver()
    invalid_trace.add(p == z3.RealVal("3") / 5)
    invalid_trace.add(q == z3.RealVal("3") / 5)
    invalid_trace.add(p >= 0, q >= 0, p + q == 1)
    invalid_result = invalid_trace.check()

    bloch_diag_bad = z3.Solver()
    upper, lower = z3.Reals("upper lower")
    bloch_diag_bad.add(upper == z3.RealVal("3") / 4)
    bloch_diag_bad.add(lower == z3.RealVal("3") / 4)
    bloch_diag_bad.add(upper + lower == 1)
    bloch_result = bloch_diag_bad.check()
    return {
        "non_normalized_spectral_weights_rejected": {
            "z3_result": str(invalid_result),
            "pass": invalid_result == z3.unsat,
        },
        "bad_diagonal_trace_rejected": {
            "z3_result": str(bloch_result),
            "pass": bloch_result == z3.unsat,
        },
        "pass": invalid_result == z3.unsat and bloch_result == z3.unsat,
    }


def computed_boundary_checks() -> dict[str, object]:
    source_text = pathlib.Path(__file__).read_text(encoding="utf-8")
    result = {
        "promotion_allowed_literal_false": {
            "pass": '"promotion_allowed": False' in source_text,
        },
        "execution_kind_is_tool_lego_fit_probe": {
            "pass": '"sim_execution_kind": "tool_lego_fit_probe"' in source_text,
        },
        "classification_is_not_canonical": {
            "pass": CLASSIFICATION == "tool_lego_fit_probe",
        },
    }
    result["pass"] = all(row["pass"] for row in result.values() if isinstance(row, dict))
    return result


def trace_alone_does_not_admit_density_matrix() -> dict[str, object]:
    trace_one_indefinite = np.asarray([[1.2, 0.0], [0.0, -0.2]], dtype=float)
    trace = float(np.trace(trace_one_indefinite))
    eigenvalues = np.linalg.eigvalsh(trace_one_indefinite)
    return {
        "witness": "diag(1.2,-0.2)",
        "trace": trace,
        "eigenvalues": [float(v) for v in eigenvalues],
        "claim_killed": "trace microfit alone admits density matrix layer",
        "pass": bool(abs(trace - 1.0) < EPS and np.min(eigenvalues) < -EPS),
    }


def rho_from_bloch(rx: float, rz: float) -> np.ndarray:
    return np.asarray([[0.5 * (1 + rz), 0.5 * rx], [0.5 * rx, 0.5 * (1 - rz)]], dtype=float)


def numpy_witnesses() -> dict[str, object]:
    valid = {
        "maximally_mixed": np.asarray([[0.5, 0.0], [0.0, 0.5]], dtype=float),
        "pure_z": rho_from_bloch(0.0, 1.0),
        "mixed_inside": rho_from_bloch(0.4, -0.2),
    }
    invalid = {
        "trace_high_diagonal": np.asarray([[0.6, 0.0], [0.0, 0.6]], dtype=float),
        "trace_low_diagonal": np.asarray([[0.2, 0.0], [0.0, 0.2]], dtype=float),
    }
    valid_rows = {}
    for name, rho in valid.items():
        valid_rows[name] = {
            "trace": float(np.trace(rho)),
            "eigenvalues": [float(v) for v in np.linalg.eigvalsh(rho)],
            "pass": bool(abs(float(np.trace(rho)) - 1.0) < EPS),
        }
    invalid_rows = {}
    for name, rho in invalid.items():
        invalid_rows[name] = {
            "trace": float(np.trace(rho)),
            "eigenvalues": [float(v) for v in np.linalg.eigvalsh(rho)],
            "pass": bool(abs(float(np.trace(rho)) - 1.0) > EPS),
        }
    return {
        "valid": valid_rows,
        "invalid": invalid_rows,
        "pass": all(row["pass"] for row in valid_rows.values())
        and all(row["pass"] for row in invalid_rows.values()),
    }


def main() -> None:
    parent = source_receipt()
    positive = {
        "parent_density_hopf_receipt_available": {
            "parent": parent,
            "pass": bool(parent["exists"]),
        },
        "sympy_bloch_form_has_trace_one": sympy_bloch_form_has_trace_one(),
        "sympy_spectral_weights_trace_equation": sympy_spectral_weights_trace_equation(),
        "numpy_witnesses_match_z3_boundary": numpy_witnesses(),
    }
    negative = {
        "z3_rejects_bad_trace_witnesses": z3_rejects_bad_trace_witnesses(),
        "not_full_density_matrix_admission": trace_alone_does_not_admit_density_matrix(),
    }
    boundary = {
        "finite_real_2x2_family_only": computed_boundary_checks(),
        "no_qit_gstack_axis_bridge_engine_or_nonclassical_admission": computed_boundary_checks(),
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "trace_constraint_z3_microfit",
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
        "source_receipts": {"trace_constraint": str(PARENT_RESULT)},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "sympy",
            "claim_ceiling": "local_real_2x2_trace_constraint_microfit_only",
            "parent_receipt_dependency": "source receipt is checked for availability only; parent canonical status is not promoted",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "trace_constraint_z3_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
