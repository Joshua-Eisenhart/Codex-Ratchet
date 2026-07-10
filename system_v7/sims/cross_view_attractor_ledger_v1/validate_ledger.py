#!/usr/bin/env python3
"""Fail closed when a cross-view row outruns its executable receipts."""

from __future__ import annotations

import copy
import json
from pathlib import Path


CLASSIFICATION = "controller_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Closed JSON schema validation, evidence-level ordering, and fail-closed claim-level mutation control.",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.json"
RESULT = HERE / "ledger_validation.json"
LEVELS = [
    "analogy",
    "structural_match",
    "shared_invariant",
    "semiconjugate_dynamics",
    "cross_domain_prediction",
    "constraint_necessity",
]
REQUIRED = {
    "domain", "probe_family", "quotient_objects", "domain_dynamics",
    "shared_invariant_candidate", "projection", "lift", "cross_view_prediction",
    "ablation", "claim_level", "evidence_refs", "semiconjugacy_receipt",
    "prediction_receipt", "ablation_receipt", "necessity_receipt",
}


def validate_rows(ledger: dict) -> list[str]:
    failures: list[str] = []
    domains: set[str] = set()
    for index, row in enumerate(ledger["rows"]):
        path = f"rows[{index}]"
        missing = REQUIRED - set(row)
        extra = set(row) - REQUIRED
        if missing or extra:
            failures.append(f"{path}: closed schema mismatch missing={sorted(missing)} extra={sorted(extra)}")
            continue
        domain = row["domain"]
        if domain in domains:
            failures.append(f"{path}: duplicate domain {domain}")
        domains.add(domain)
        level = row["claim_level"]
        if level not in LEVELS:
            failures.append(f"{path}: unknown claim level {level}")
            continue
        if LEVELS.index(level) >= LEVELS.index("shared_invariant") and not row["ablation_receipt"]:
            failures.append(f"{path}: shared-invariant claim lacks paired ablation receipt")
        if LEVELS.index(level) >= LEVELS.index("semiconjugate_dynamics") and not row["semiconjugacy_receipt"]:
            failures.append(f"{path}: semiconjugacy claim lacks executable residual receipt")
        if LEVELS.index(level) >= LEVELS.index("cross_domain_prediction") and not row["prediction_receipt"]:
            failures.append(f"{path}: prediction claim lacks frozen transported-prediction receipt")
        if level == "constraint_necessity" and not row["necessity_receipt"]:
            failures.append(f"{path}: constraint-necessity claim lacks root-constraint ablation receipt")
    return failures


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    failures = validate_rows(ledger)
    mutated = copy.deepcopy(ledger)
    mutated["rows"][0]["claim_level"] = "constraint_necessity"
    necessity_mutation_failures = validate_rows(mutated)
    necessity_mutation_detected = any(
        "constraint-necessity claim lacks root-constraint ablation receipt" in failure
        for failure in necessity_mutation_failures
    )
    all_pass = not failures and necessity_mutation_detected

    result = {
        "schema": "codex_ratchet.cross_view_attractor_ledger.validation.v2",
        "classification": CLASSIFICATION,
        "proposal_role": "proposal_schema_and_ceiling_validation_only",
        "row_count": len(ledger["rows"]),
        "failures": failures,
        "all_pass": all_pass,
        "highest_claim_level": max(
            (row["claim_level"] for row in ledger["rows"]),
            key=LEVELS.index,
        ),
        "shared_attractor_admitted": False,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "mutation_controls": {
            "unreceipted_constraint_necessity_rejected": necessity_mutation_detected,
        },
        "note": "A green result means no row outran its receipts. It is not cross-domain evidence.",
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
