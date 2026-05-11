#!/usr/bin/env python3
"""Hermiticity microfit for finite 2x2 density-carrier candidates.

This bounded tool-lego fit makes the structural Hermitian condition explicit:
rho = rho^dagger. It is a carrier/admission pre-test only, not a full density
matrix admission or a bridge, QIT, GStack, axis, engine, or nonclassical claim.
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
    "Bounded hermiticity microfit for finite 2x2 carrier candidates. Sympy is "
    "load-bearing for deriving the real/imaginary equality constraints of "
    "rho = rho^dagger; z3 rejects explicit non-Hermitian witnesses; numpy "
    "crosschecks finite matrices. This does not admit the full density-matrix "
    "object, bridge, QIT, GStack, axis, engine, or nonclassical layer."
)

LEGO_IDS = ["carrier_admission_density_matrix"]
PRIMARY_LEGO_IDS = ["carrier_admission_density_matrix"]
SUB_LEGO_IDS = ["hermiticity_constraint"]

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic conjugate-transpose residual and Hermitian constraint derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive linear-real UNSAT checks for explicit non-Hermitian witnesses",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite matrix hermiticity/eigenvalue witness checks",
    },
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no tensor/autograd dynamics"},
    "cvc5": {"tried": False, "used": False, "reason": "deferred; z3 is sufficient for explicit witness rejection"},
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "supportive",
    "numpy": "supportive",
    "pytorch": None,
    "cvc5": None,
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
PARENT_RESULTS = {
    "density_hopf_geometry": RESULT_DIR / "density_hopf_geometry_results.json",
    "pure_lego_density_matrices": RESULT_DIR / "pure_lego_density_matrices_results.json",
}
REGISTRY_PATH = PROBE_DIR.parents[1] / "system_v5" / "docs" / "16_lego_build_catalog.md"
EPS = 1e-12


def source_receipts() -> dict[str, object]:
    out = {}
    for key, path in PARENT_RESULTS.items():
        if not path.exists():
            out[key] = {"path": str(path), "exists": False, "all_pass": False}
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        out[key] = {
            "path": str(path),
            "exists": True,
            "all_pass": bool(data.get("all_pass") or data.get("summary", {}).get("all_pass")),
            "classification": data.get("classification"),
        }
    return out


def sympy_hermiticity_constraints() -> dict[str, object]:
    a, d, b_re, b_im, c_re, c_im = sp.symbols("a d b_re b_im c_re c_im", real=True)
    rho = sp.Matrix([[a, b_re + sp.I * b_im], [c_re + sp.I * c_im, d]])
    residual = sp.simplify(rho - rho.conjugate().T)
    constraints = {
        "diagonal_a_imaginary_part_zero_by_real_param": True,
        "diagonal_d_imaginary_part_zero_by_real_param": True,
        "offdiag_real_equal": str(sp.simplify(b_re - c_re)),
        "offdiag_imag_opposite": str(sp.simplify(b_im + c_im)),
    }
    valid_subs = {a: sp.Rational(1, 2), d: sp.Rational(1, 2), b_re: sp.Rational(1, 5), c_re: sp.Rational(1, 5), b_im: sp.Rational(1, 7), c_im: -sp.Rational(1, 7)}
    invalid_subs = {a: sp.Rational(1, 2), d: sp.Rational(1, 2), b_re: sp.Rational(1, 5), c_re: sp.Rational(2, 5), b_im: sp.Rational(1, 7), c_im: sp.Rational(1, 7)}
    valid_residual = sp.simplify(residual.subs(valid_subs))
    invalid_residual = sp.simplify(residual.subs(invalid_subs))
    return {
        "family": "[[a, b_re+i b_im], [c_re+i c_im, d]] with real parameters",
        "residual_matrix": str(residual),
        "constraints": constraints,
        "valid_residual_zero": bool(valid_residual == sp.zeros(2)),
        "invalid_residual": str(invalid_residual),
        "pass": bool(valid_residual == sp.zeros(2) and invalid_residual != sp.zeros(2)),
    }


def z3_rejects_nonhermitian_witnesses() -> dict[str, object]:
    b_re, b_im, c_re, c_im = z3.Reals("b_re b_im c_re c_im")
    real_witness_exists = z3.Solver()
    real_witness_exists.add(b_re != c_re)
    real_witness_result = real_witness_exists.check()

    real_witness_fenced = z3.Solver()
    real_witness_fenced.add(b_re != c_re)
    real_witness_fenced.add(b_re == c_re)
    real_fenced_result = real_witness_fenced.check()

    imag_witness_exists = z3.Solver()
    imag_witness_exists.add(b_im + c_im != 0)
    imag_witness_result = imag_witness_exists.check()

    imag_witness_fenced = z3.Solver()
    imag_witness_fenced.add(b_im + c_im != 0)
    imag_witness_fenced.add(b_im + c_im == 0)
    imag_fenced_result = imag_witness_fenced.check()

    valid_complex_hermitian = z3.Solver()
    valid_complex_hermitian.add(b_re == c_re)
    valid_complex_hermitian.add(b_im + c_im == 0)
    valid_complex_hermitian.add(b_im != 0)
    valid_result = valid_complex_hermitian.check()
    rows = {
        "nonhermitian_real_mismatch_witness_exists_without_fence": {
            "z3_result": str(real_witness_result),
            "pass": real_witness_result == z3.sat,
        },
        "nonhermitian_real_mismatch_rejected_by_fence": {
            "z3_result": str(real_fenced_result),
            "pass": real_fenced_result == z3.unsat,
        },
        "nonhermitian_imag_mismatch_witness_exists_without_fence": {
            "z3_result": str(imag_witness_result),
            "pass": imag_witness_result == z3.sat,
        },
        "nonhermitian_imag_mismatch_rejected_by_fence": {
            "z3_result": str(imag_fenced_result),
            "pass": imag_fenced_result == z3.unsat,
        },
        "admit_nontrivial_complex_hermitian_pair": {
            "z3_result": str(valid_result),
            "pass": valid_result == z3.sat,
        },
    }
    return {"rows": rows, "pass": all(row["pass"] for row in rows.values())}


def numpy_witnesses() -> dict[str, object]:
    valid = {
        "real_symmetric": np.asarray([[0.5, 0.2], [0.2, 0.5]], dtype=complex),
        "complex_hermitian": np.asarray([[0.5, 0.2 + 0.1j], [0.2 - 0.1j, 0.5]], dtype=complex),
    }
    invalid = {
        "offdiag_real_mismatch": np.asarray([[0.5, 0.1], [0.3, 0.5]], dtype=complex),
        "offdiag_imag_same_sign": np.asarray([[0.5, 0.2 + 0.1j], [0.2 + 0.1j, 0.5]], dtype=complex),
    }
    valid_rows = {}
    for name, rho in valid.items():
        residual = float(np.max(np.abs(rho - rho.conj().T)))
        valid_rows[name] = {
            "hermitian_residual": residual,
            "eigenvalues": [float(v) for v in np.linalg.eigvalsh(rho)],
            "pass": bool(residual < EPS),
        }
    invalid_rows = {}
    for name, rho in invalid.items():
        residual = float(np.max(np.abs(rho - rho.conj().T)))
        invalid_rows[name] = {
            "hermitian_residual": residual,
            "pass": bool(residual > EPS),
        }
    return {
        "valid": valid_rows,
        "invalid": invalid_rows,
        "pass": all(row["pass"] for row in valid_rows.values()) and all(row["pass"] for row in invalid_rows.values()),
    }


def hermiticity_alone_does_not_admit_density_matrix() -> dict[str, object]:
    hermitian_bad_trace = np.asarray([[2.0, 0.0], [0.0, 2.0]], dtype=complex)
    residual = float(np.max(np.abs(hermitian_bad_trace - hermitian_bad_trace.conj().T)))
    trace = float(np.trace(hermitian_bad_trace).real)
    return {
        "witness": "diag(2,2)",
        "hermitian_residual": residual,
        "trace": trace,
        "claim_killed": "hermiticity microfit alone admits density matrix layer",
        "pass": bool(residual < EPS and abs(trace - 1.0) > EPS),
    }


def boundary_checks() -> dict[str, object]:
    registry_text = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    result = {
        "registered_parent_lego": {
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "registry_path": str(REGISTRY_PATH),
            "registry_contains_parent": "carrier_admission_density_matrix" in registry_text,
            "pass": PRIMARY_LEGO_IDS == ["carrier_admission_density_matrix"]
            and "carrier_admission_density_matrix" in registry_text,
        },
        "declared_sub_lego_facet": {
            "sub_lego_ids": SUB_LEGO_IDS,
            "pass": SUB_LEGO_IDS == ["hermiticity_constraint"],
        },
        "classification_is_tool_lego_fit_probe": {"classification": CLASSIFICATION, "pass": CLASSIFICATION == "tool_lego_fit_probe"},
        "no_neighbor_lego_credit": {"lego_ids": LEGO_IDS, "pass": LEGO_IDS == ["carrier_admission_density_matrix"]},
    }
    result["pass"] = all(row["pass"] for row in result.values())
    return result


def main() -> None:
    receipts = source_receipts()
    prerequisite = {
        "source_receipts": receipts,
        "all_source_receipts_available": all(row["exists"] for row in receipts.values()),
        "note": "Prerequisite metadata only; parent canonical status is not promoted.",
    }
    positive = {
        "sympy_hermiticity_constraints": sympy_hermiticity_constraints(),
        "numpy_hermitian_witnesses": numpy_witnesses(),
    }
    negative = {
        "z3_rejects_nonhermitian_witnesses": z3_rejects_nonhermitian_witnesses(),
        "not_full_density_matrix_admission": hermiticity_alone_does_not_admit_density_matrix(),
    }
    boundary = {
        "scope_and_promotion_boundary": boundary_checks(),
    }
    evidence_all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    all_pass = bool(prerequisite["all_source_receipts_available"] and evidence_all_pass)
    result = {
        "name": "hermiticity_constraint_sympy_z3_microfit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "sub_lego_ids": SUB_LEGO_IDS,
        "sim_execution_kind": "tool_lego_fit_probe",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {key: str(path) for key, path in PARENT_RESULTS.items()},
        "prerequisite": prerequisite,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "evidence_rows_all_pass": bool(evidence_all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "sympy",
            "claim_ceiling": "local_2x2_hermiticity_subfacet_of_carrier_admission_only",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "hermiticity_constraint_sympy_z3_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
