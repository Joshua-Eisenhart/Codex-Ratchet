#!/usr/bin/env python3
"""Audit agreement between Z3 and cvc5 bare-Pauli/no-carrier controls."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

from receipt_boundary import apply_default_receipt_boundary


NAME = "smt_bare_pauli_no_carrier_fiber_base_metric_backend_agreement_audit"
CLASSIFICATION = "audit"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
Z3_RESULT = RESULT_DIR / "z3_bare_pauli_no_carrier_fiber_base_metric_unsat_results.json"
CVC5_RESULT = RESULT_DIR / "cvc5_bare_pauli_no_carrier_fiber_base_metric_unsat_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

TOOL_MANIFEST = {
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior z3 receipt and checks its recorded verdicts against cvc5",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not executed here; this audit reads the prior cvc5 receipt and checks its recorded verdicts against z3",
    },
}
TOOL_INTEGRATION_DEPTH = {"z3": None, "cvc5": None}

CLAIM_CEILING = (
    "backend-agreement audit only: compares existing Z3 and cvc5 bare-Pauli/no-carrier SAT/UNSAT receipts; "
    "no new solver proof, no carrier geometry, no flux, no QIT, GStack, axis, bridge, engine, or nonclassical admission"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def solver_value(row: dict[str, Any]) -> str:
    if "z3_result" in row:
        return str(row["z3_result"])
    if "cvc5_result" in row:
        return str(row["cvc5_result"])
    raise KeyError(f"missing solver result in {row}")


def compare_sections(z3_data: dict[str, Any], cvc5_data: dict[str, Any], section: str) -> list[dict[str, Any]]:
    z3_rows = z3_data[section]
    cvc5_rows = cvc5_data[section]
    shared = sorted(set(z3_rows) & set(cvc5_rows))
    rows = []
    for key in shared:
        left = z3_rows[key]
        right = cvc5_rows[key]
        rows.append(
            {
                "check": key,
                "z3_result": solver_value(left),
                "cvc5_result": solver_value(right),
                "expected": left.get("expected"),
                "expected_matches": left.get("expected") == right.get("expected"),
                "passed_matches": bool(left.get("passed")) == bool(right.get("passed")),
                "solver_agreement": solver_value(left) == solver_value(right),
            }
        )
    return rows


def main() -> dict[str, Any]:
    started = time.time()
    z3_data = load(Z3_RESULT)
    cvc5_data = load(CVC5_RESULT)

    positive_rows = compare_sections(z3_data, cvc5_data, "positive")
    graveyard_rows = compare_sections(z3_data, cvc5_data, "graveyards_detail")
    all_rows = positive_rows + graveyard_rows
    all_pass = bool(
        z3_data.get("classification") == "classical_baseline"
        and cvc5_data.get("classification") == "classical_baseline"
        and z3_data.get("promotion_allowed") is False
        and cvc5_data.get("promotion_allowed") is False
        and all(row["expected_matches"] and row["passed_matches"] and row["solver_agreement"] for row in all_rows)
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none; backend agreement audit for bare-Pauli/no-carrier negative controls",
        "promotion_condition": "No promotion from this audit; use only to confirm the two SMT backends agree on this negative-control receipt family.",
        "blocked_until": "blocked from carrier, topology, flux, QIT, GStack, axis, bridge, engine, or nonclassical claims until separate carrier receipts exist",
        "demotion_condition": "Demote if cited as fresh solver execution or as carrier-geometry evidence.",
        "source_receipts": [rel(Z3_RESULT), rel(CVC5_RESULT)],
        "operation_sequence": [
            "load existing Z3 bare-Pauli/no-carrier metric receipt",
            "load existing cvc5 bare-Pauli/no-carrier metric receipt",
            "compare matching positive and graveyard SAT/UNSAT checks",
            "verify both receipts are classical baselines with promotion disallowed",
        ],
        "carrier_topology": "none; finite Boolean predicate receipt comparison only",
        "observable": "agreement of recorded z3_result and cvc5_result fields on shared predicate checks",
        "pass_fail_predicate": "both receipts are classical baselines with promotion_allowed false and every shared predicate has matching expected verdict, pass flag, and solver verdict",
        "graveyards": [
            "mismatched SAT/UNSAT verdict between Z3 and cvc5 would fail agreement",
            "either source receipt allowing promotion would fail agreement",
            "missing shared graveyard checks would block agreement",
        ],
        "baselines": [
            "Z3 bare-Pauli/no-carrier fiber-base metric negative control",
            "cvc5 bare-Pauli/no-carrier fiber-base metric negative control",
        ],
        "alternative_formulations": [
            "rerun both SMT encodings in one source file",
            "add an SMT-LIB export and replay through both solvers",
            "translate the Boolean predicate family into a proof-table receipt",
        ],
        "exact_tool_function_needs": {
            "python_json": ["json.loads", "pathlib.Path.read_text"],
            "prior_z3_receipt": ["z3_result fields"],
            "prior_cvc5_receipt": ["cvc5_result fields"],
        },
        "lego_or_coupling_target": "bare_pauli_no_carrier_negative_control_backend_agreement",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "positive_shared_count": len(positive_rows),
            "graveyard_shared_count": len(graveyard_rows),
            "all_shared_checks_agree": all(row["solver_agreement"] for row in all_rows),
            "promotion_allowed": False,
            "all_pass": all_pass,
        },
        "positive": {"shared_positive_checks": positive_rows},
        "negative": {"shared_graveyard_checks": graveyard_rows},
        "boundary": {
            "source_receipt_fences": {
                "z3_classification": z3_data.get("classification"),
                "cvc5_classification": cvc5_data.get("classification"),
                "z3_promotion_allowed": z3_data.get("promotion_allowed"),
                "cvc5_promotion_allowed": cvc5_data.get("promotion_allowed"),
            }
        },
        "out_of_scope": [
            "No fresh solver execution.",
            "No carrier construction.",
            "No physical geometry, flux, QIT, GStack, axis, bridge, engine, or nonclassical claim.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    result = apply_default_receipt_boundary(result, source_name=f"sim_{NAME}")
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {result['all_pass']}")
    return result


if __name__ == "__main__":
    main()
