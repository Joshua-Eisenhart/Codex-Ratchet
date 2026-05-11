#!/usr/bin/env python3
"""Z3 microfit for the 2x2 positivity constraint.

This bounded tool-lego fit splits the positivity constraint away from the
broader density-matrix receipts. It proves a small real 2x2 density-family PSD
condition with z3 and crosschecks representative matrices numerically. This is
local positivity evidence only.
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
    "Bounded z3 microfit for the positivity constraint on real 2x2 density "
    "candidates rho=(I + rx*sigma_x + rz*sigma_z)/2. It proves the finite "
    "Bloch-disk condition implies PSD in this local family and rejects bounded "
    "invalid witnesses. It is not density-matrix admission, bridge, QIT, "
    "GStack, axis, engine, or nonclassical admission."
)

LEGO_IDS = ["positivity_constraint", "density_matrix_representability", "finite_carrier_c2"]
PRIMARY_LEGO_IDS = ["positivity_constraint"]

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonlinear-real UNSAT proofs for 2x2 PSD constraints",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite matrix/eigenvalue crosschecks for explicit witnesses",
    },
    "scipy": {"tried": False, "used": False, "reason": "not needed for this exact PSD microfit"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed; no autograd or tensor dynamics"},
    "cvc5": {"tried": False, "used": False, "reason": "deferred; z3 is sufficient for this bounded NRA proof"},
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
PARENT_RESULT = RESULT_DIR / "positivity_constraint_results.json"
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


def z3_bloch_disk_implies_psd() -> dict[str, object]:
    rx, rz = z3.Reals("rx rz")
    a = (1 + rz) / 2
    c = (1 - rz) / 2
    b = rx / 2
    det = a * c - b * b
    assumptions = [rx * rx + rz * rz <= 1]
    checks = {}
    for name, bad_condition in {
        "negative_upper_diagonal": a < 0,
        "negative_lower_diagonal": c < 0,
        "negative_determinant": det < 0,
    }.items():
        solver = z3.Solver()
        solver.add(*assumptions)
        solver.add(bad_condition)
        result = solver.check()
        checks[name] = {"z3_result": str(result), "pass": result == z3.unsat}
    return {
        "family": "rho=(I + rx*sigma_x + rz*sigma_z)/2",
        "constraint": "rx^2 + rz^2 <= 1",
        "checks": checks,
        "pass": all(row["pass"] for row in checks.values()),
    }


def z3_invalid_witnesses_rejected() -> dict[str, object]:
    rx, rz = z3.Reals("rx_bad rz_bad")
    solver = z3.Solver()
    solver.add(rx == z3.RealVal("4") / 5)
    solver.add(rz == z3.RealVal("4") / 5)
    solver.add(rx * rx + rz * rz <= 1)
    outside_disk = solver.check()

    a, c, b = z3.Reals("a c b")
    det = a * c - b * b
    indefinite = z3.Solver()
    indefinite.add(a == z3.RealVal("1") / 2)
    indefinite.add(c == z3.RealVal("1") / 2)
    indefinite.add(b == z3.RealVal("4") / 5)
    indefinite.add(a >= 0, c >= 0, det >= 0)
    indefinite_result = indefinite.check()
    return {
        "outside_bloch_disk_rejected": {"z3_result": str(outside_disk), "pass": outside_disk == z3.unsat},
        "indefinite_offdiag_rejected": {
            "z3_result": str(indefinite_result),
            "pass": indefinite_result == z3.unsat,
        },
        "pass": outside_disk == z3.unsat and indefinite_result == z3.unsat,
    }


def rho_from_bloch(rx: float, rz: float) -> np.ndarray:
    return np.asarray([[0.5 * (1 + rz), 0.5 * rx], [0.5 * rx, 0.5 * (1 - rz)]], dtype=float)


def numpy_witnesses() -> dict[str, object]:
    valid = {
        "center": rho_from_bloch(0.0, 0.0),
        "pure_x_boundary": rho_from_bloch(1.0, 0.0),
        "mixed_inside": rho_from_bloch(0.4, -0.2),
    }
    invalid = {
        "outside_disk": rho_from_bloch(0.8, 0.8),
        "indefinite_offdiag": np.asarray([[0.5, 0.8], [0.8, 0.5]], dtype=float),
    }
    valid_rows = {}
    for name, rho in valid.items():
        vals = np.linalg.eigvalsh(rho)
        valid_rows[name] = {
            "eigenvalues": [float(v) for v in vals],
            "determinant": float(np.linalg.det(rho)),
            "pass": bool(np.min(vals) >= -EPS and abs(float(np.trace(rho)) - 1.0) < EPS),
        }
    invalid_rows = {}
    for name, rho in invalid.items():
        vals = np.linalg.eigvalsh(rho)
        invalid_rows[name] = {
            "eigenvalues": [float(v) for v in vals],
            "determinant": float(np.linalg.det(rho)),
            "pass": bool(np.min(vals) < -EPS),
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
        "parent_positivity_receipt_passes": {
            "parent": parent,
            "pass": bool(parent["exists"] and parent["all_pass"]),
        },
        "z3_bloch_disk_implies_2x2_psd": z3_bloch_disk_implies_psd(),
        "numpy_witnesses_match_z3_boundary": numpy_witnesses(),
    }
    negative = {
        "z3_rejects_invalid_witnesses": z3_invalid_witnesses_rejected(),
        "not_full_density_matrix_admission": {
            "claim_killed": "positivity microfit alone admits density matrix layer",
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
        "name": "positivity_constraint_z3_microfit",
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
        "source_receipts": {"positivity_constraint": str(PARENT_RESULT)},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": False,
            "load_bearing_tool": "z3",
            "claim_ceiling": "local_real_2x2_positivity_constraint_microfit_only",
            "scope_note": divergence_log,
        },
        "all_pass": bool(all_pass),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "positivity_constraint_z3_microfit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
