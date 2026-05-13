#!/usr/bin/env python3
"""Audit result consumers that could confuse a local pass flag with promotion.

This receipt is a guard around
hopf_spinor_density_operator_placement_readout_collision_audit_results.json.
It checks that the known controller indexes do not accept that receipt merely
because ``all_pass`` is true.
"""

from __future__ import annotations

import ast
import json
import pathlib
import time
from typing import Any


NAME = "result_pass_flag_promotion_gate_consumer_audit"
CLASSIFICATION = "audit"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
ROOT = PROBE_DIR.parents[1]
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
TARGET_RESULT = RESULT_DIR / "hopf_spinor_density_operator_placement_readout_collision_audit_results.json"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CONSUMER_PATHS = [
    ROOT / "scripts" / "qit_engine_evidence_index.py",
    ROOT / "scripts" / "sim_inventory_index.py",
    ROOT / "scripts" / "tool_function_receipt_matrix.py",
    ROOT / "scripts" / "receipt_schema.py",
]

TOOL_MANIFEST = {
    "python_ast": {
        "tried": True,
        "used": True,
        "reason": "load-bearing for static inspection of result consumer code paths",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: this is static controller-code audit, not numeric simulation",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used: consumer guard is syntactic and path-specific",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_ast": "load_bearing",
    "numpy": None,
    "z3": None,
}

CLAIM_CEILING = (
    "consumer-side guard only: verifies selected controller readers do not promote the Hopf "
    "placement collision audit from all_pass alone; no placement distinguishability, QIT, "
    "GStack, axis, bridge, engine, flux, bundle, or nonclassical claim"
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_target() -> dict[str, Any]:
    payload = json.loads(TARGET_RESULT.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("target receipt is not a JSON object")
    return payload


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def string_literals(node: ast.AST) -> list[str]:
    values: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.append(child.value)
    return values


def consumer_features(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text, filename=str(path))
    all_pass_refs: list[dict[str, Any]] = []
    promotion_refs: list[dict[str, Any]] = []
    classification_refs: list[dict[str, Any]] = []
    target_name_refs: list[int] = []
    for node in ast.walk(tree):
        literals = string_literals(node)
        if "hopf_spinor_density_operator_placement_readout_collision_audit" in literals:
            target_name_refs.append(getattr(node, "lineno", 0))
        if any(text in {"all_pass", "overall_pass", "passed"} for text in literals):
            all_pass_refs.append(
                {
                    "line": getattr(node, "lineno", 0),
                    "node": type(node).__name__,
                    "call": call_name(node.func) if isinstance(node, ast.Call) else "",
                    "literals": sorted(set(v for v in literals if v in {"all_pass", "overall_pass", "passed"})),
                }
            )
        if "promotion_allowed" in literals:
            promotion_refs.append({"line": getattr(node, "lineno", 0), "node": type(node).__name__})
        if "classification" in literals or "canonical" in literals or "classical_baseline" in literals:
            classification_refs.append(
                {
                    "line": getattr(node, "lineno", 0),
                    "node": type(node).__name__,
                    "literals": sorted(set(v for v in literals if v in {"classification", "canonical", "classical_baseline"})),
                }
            )
    return {
        "path": rel(path),
        "target_name_refs": sorted(set(line for line in target_name_refs if line)),
        "all_pass_ref_count": len(all_pass_refs),
        "all_pass_refs": all_pass_refs[:20],
        "promotion_allowed_ref_count": len(promotion_refs),
        "classification_ref_count": len(classification_refs),
        "classification_refs": classification_refs[:20],
    }


def main() -> dict[str, Any]:
    started = time.time()
    target = load_target()
    features = [consumer_features(path) for path in CONSUMER_PATHS]
    qit_index = next(row for row in features if row["path"] == "scripts/qit_engine_evidence_index.py")
    sim_inventory = next(row for row in features if row["path"] == "scripts/sim_inventory_index.py")
    tool_matrix = next(row for row in features if row["path"] == "scripts/tool_function_receipt_matrix.py")
    receipt_schema = next(row for row in features if row["path"] == "scripts/receipt_schema.py")

    target_guarded = (
        target.get("classification") == "classical_baseline"
        and target.get("promotion_allowed") is False
        and "does not mean 16 placements are operationally distinguished" in str(target.get("all_pass_meaning") or "")
    )
    qit_blocks_noncanonical = qit_index["classification_ref_count"] > 0 and qit_index["all_pass_ref_count"] == 0
    inventory_records_classification = sim_inventory["classification_ref_count"] > 0
    matrix_not_targeted = not tool_matrix["target_name_refs"]
    schema_validates_pass_but_not_promotion = (
        receipt_schema["all_pass_ref_count"] > 0 and receipt_schema["classification_ref_count"] > 0
    )

    all_pass = all(
        [
            target_guarded,
            qit_blocks_noncanonical,
            inventory_records_classification,
            matrix_not_targeted,
            schema_validates_pass_but_not_promotion,
        ]
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "none; controller guard for blocking baseline receipt consumers",
        "promotion_condition": "No promotion from this audit; it only records selected consumer guard behavior.",
        "blocked_until": (
            "future consumers that route on all_pass for blocking baseline receipts must also check "
            "classification, promotion_allowed, and admission status"
        ),
        "demotion_condition": "Demote if cited as placement distinguishability or admission evidence.",
        "target_result": rel(TARGET_RESULT),
        "operation_sequence": [
            "load the Hopf placement collision audit receipt",
            "parse selected controller consumer scripts with Python ast",
            "record all_pass, classification, promotion_allowed, and target-name references",
            "verify non-canonical/classical-baseline gates protect against all_pass-only promotion",
        ],
        "carrier_topology": "controller result-consumer graph over selected index and validation scripts",
        "observable": "AST-level references to all_pass, classification, canonical, classical_baseline, and promotion_allowed",
        "pass_fail_predicate": (
            "pass iff the target receipt is explicitly guarded, QIT evidence indexing blocks non-canonical receipts, "
            "inventory records classification, the tool-function matrix does not target this receipt, and receipt "
            "validation does not imply promotion"
        ),
        "graveyards": [
            "target receipt lacks promotion_allowed=false or all_pass_meaning",
            "QIT evidence index accepts all_pass without classification/admission blocking",
            "tool-function matrix includes the target receipt as a passing target row",
            "inventory drops classification when linking results",
        ],
        "baselines": [
            "target collision audit receipt",
            "QIT evidence index non-canonical blocker",
            "sim inventory classification recording",
            "receipt schema pass validation",
        ],
        "alternative_formulations": [
            "dynamic import instrumentation of consumer functions",
            "golden snapshot of target receipt status in each generated index",
            "repo-wide AST taint pass from target result path to admission candidates",
        ],
        "exact_tool_function_needs": {
            "python_ast": ["ast.parse", "ast.walk"],
            "json": ["json.loads"],
            "pathlib": ["Path.read_text"],
        },
        "lego_or_coupling_target": "controller promotion-gate safety for blocking baseline receipts",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "target_guarded": target_guarded,
            "qit_blocks_noncanonical": qit_blocks_noncanonical,
            "inventory_records_classification": inventory_records_classification,
            "tool_matrix_not_targeted": matrix_not_targeted,
            "receipt_schema_validates_pass_but_not_promotion": schema_validates_pass_but_not_promotion,
            "consumer_count": len(features),
            "all_pass": all_pass,
            "promotion_allowed": False,
        },
        "positive": {
            "target_guard_fields_present": {"passed": target_guarded},
            "qit_index_noncanonical_gate_present": {"passed": qit_blocks_noncanonical},
            "tool_matrix_not_targeted": {"passed": matrix_not_targeted},
        },
        "negative": {
            "all_pass_only_promotion_path": {
                "passed": matrix_not_targeted and qit_blocks_noncanonical,
                "target_name_refs_in_tool_matrix": tool_matrix["target_name_refs"],
            }
        },
        "consumer_features": features,
        "out_of_scope": [
            "No proof that every possible future consumer checks promotion_allowed.",
            "No proof of 16-placement distinguishability.",
            "No canonical or nonclassical admission.",
        ],
        "elapsed_seconds": round(time.time() - started, 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(OUT_PATH)
    print(f"ALL PASS: {all_pass}")
    return result


if __name__ == "__main__":
    main()
