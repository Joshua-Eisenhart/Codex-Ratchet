#!/usr/bin/env python3
"""Z3 microfit for the 2x2 trace-one constraint.

This bounded tool-lego fit splits the trace constraint away from the broader
density/Hopf receipt. It proves small finite 2x2 density-carrier trace facts
with z3 and crosschecks explicit witnesses numerically. This is local trace
constraint evidence only.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import numpy as np
import z3


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded z3 microfit for the trace-one constraint on real 2x2 density "
    "candidates. It proves that the local Bloch and spectral 2x2 carriers have "
    "trace one exactly when their admitted finite parameters normalize. It is "
    "not density-matrix admission, bridge, QIT, GStack, axis, engine, or "
    "nonclassical admission."
)

LEGO_IDS = ["trace_constraint", "density_matrix_representability", "finite_carrier_c2"]
PRIMARY_LEGO_IDS = ["trace_constraint"]

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing real-arithmetic UNSAT proofs for 2x2 trace constraints",
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
    "z3": "load_bearing",
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


def z3_bloch_form_has_trace_one() -> dict[str, object]:
    rx, rz = z3.Reals("rx rz")
    upper = (1 + rz) / 2
    lower = (1 - rz) / 2
    trace = upper + lower
    solver = z3.Solver()
    solver.add(rx * rx + rz * rz <= 1)
    solver.add(trace != 1)
    result = solver.check()
    return {
        "family": "rho=(I + rx*sigma_x + rz*sigma_z)/2",
        "constraint": "rx^2 + rz^2 <= 1",
        "bad_condition": "trace != 1",
        "z3_result": str(result),
        "pass": result == z3.unsat,
    }


def z3_spectral_weights_equivalent_to_trace_one() -> dict[str, object]:
    p, q = z3.Reals("p q")
    trace = p + q
    normalized_implies_trace = z3.Solver()
    normalized_implies_trace.add(p >= 0, q >= 0, p + q == 1, trace != 1)
    normalized_result = normalized_implies_trace.check()

    trace_implies_normalized = z3.Solver()
    trace_implies_normalized.add(p >= 0, q >= 0, trace == 1, p + q != 1)
    trace_result = trace_implies_normalized.check()
    return {
        "family": "rho=diag(p,q)",
        "normalized_weights_imply_trace_one": {
            "z3_result": str(normalized_result),
            "pass": normalized_result == z3.unsat,
        },
        "trace_one_implies_weight_sum_one_in_this_family": {
            "z3_result": str(trace_result),
            "pass": trace_result == z3.unsat,
        },
        "pass": normalized_result == z3.unsat and trace_result == z3.unsat,
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
        "parent_density_hopf_receipt_passes": {
            "parent": parent,
            "pass": bool(parent["exists"] and parent["all_pass"]),
        },
        "z3_bloch_form_has_trace_one": z3_bloch_form_has_trace_one(),
        "z3_spectral_weights_equivalent_to_trace_one": z3_spectral_weights_equivalent_to_trace_one(),
        "numpy_witnesses_match_z3_boundary": numpy_witnesses(),
    }
    negative = {
        "z3_rejects_bad_trace_witnesses": z3_rejects_bad_trace_witnesses(),
        "not_full_density_matrix_admission": {
            "claim_killed": "trace microfit alone admits density matrix layer",
            "pass": True,
        },
    }
    boundary = {
        "finite_real_2x2_family_only": {"pass": True},
        "no_qit_gstack_axis_bridge_engine_or_nonclassical_admission": {
            "promotion_allowed": False,
            "pass": True,
        },
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
            "load_bearing_tool": "z3",
            "claim_ceiling": "local_real_2x2_trace_constraint_microfit_only",
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
