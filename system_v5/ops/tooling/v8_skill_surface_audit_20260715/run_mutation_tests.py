#!/usr/bin/env python3
"""Run negative mutations against the fail-closed skill-surface validator."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from validate_skill_surface import validate_document


SCHEMA = "codex-ratchet-skill-surface-mutation-tests-v1"
CLASSIFICATION = "audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Standard-library deep copies and JSON emission exercise negative inventory mutations.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def mutate_boundary(document: dict[str, Any]) -> None:
    document["claim_boundaries"]["all_skills_updated"] = True


def mutate_missing_repo(document: dict[str, Any]) -> None:
    document["summary"]["missing_repo_source"] = ["codex-ratchet-sim-audit-spine"]


def mutate_candidate_install(document: dict[str, Any]) -> None:
    document["summary"]["candidate_not_installed"] = []


def mutate_hash(document: dict[str, Any]) -> None:
    document["skills"][0]["locations"]["codex_installed"]["skill_sha256"] = "0" * 64


def mutate_drift(document: dict[str, Any]) -> None:
    for entry in document["skills"]:
        if entry["name"] == "claude-bridge":
            entry["operational_body_parity"]["repo_vs_codex"]["status"] = "exact"
            return


def mutate_route(document: dict[str, Any]) -> None:
    for entry in document["skills"]:
        if entry["name"] == "codex-ratchet-deep-stack-stress":
            entry["nested_skill_routes"] = []
            return


def mutate_level(document: dict[str, Any]) -> None:
    for entry in document["skills"]:
        if entry["name"] == "claude-bridge":
            entry["selected_implementation_level"] = "guidance_only"
            return


MUTATIONS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("false_update_claim", mutate_boundary),
    ("reintroduce_repaired_missing_source", mutate_missing_repo),
    ("erase_candidate_not_installed", mutate_candidate_install),
    ("corrupt_source_hash", mutate_hash),
    ("launder_claude_drift", mutate_drift),
    ("erase_nested_routes", mutate_route),
    ("demote_tested_candidate_metadata", mutate_level),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = json.loads(args.audit.read_text(encoding="utf-8"))
    baseline_errors = validate_document(baseline)
    cases = []
    for case_id, mutator in MUTATIONS:
        candidate = copy.deepcopy(baseline)
        mutator(candidate)
        errors = validate_document(candidate)
        cases.append(
            {
                "case_id": case_id,
                "rejected": bool(errors),
                "errors": errors,
            }
        )
    all_rejected = not baseline_errors and all(case["rejected"] for case in cases)
    receipt = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "audit_kind": "v8_skill_surface_mutation_test",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "audit_path": str(args.audit.resolve()),
        "audit_sha256": sha256_file(args.audit),
        "baseline_valid": not baseline_errors,
        "baseline_errors": baseline_errors,
        "cases": cases,
        "case_count": len(cases),
        "rejected_count": sum(case["rejected"] for case in cases),
        "all_mutations_rejected": all_rejected,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "official_launch_allowed": False,
        "scientific_claim_allowed": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "baseline_valid": receipt["baseline_valid"],
                "case_count": receipt["case_count"],
                "rejected_count": receipt["rejected_count"],
                "all_mutations_rejected": receipt["all_mutations_rejected"],
            },
            sort_keys=True,
        )
    )
    return 0 if all_rejected else 2


if __name__ == "__main__":
    raise SystemExit(main())
