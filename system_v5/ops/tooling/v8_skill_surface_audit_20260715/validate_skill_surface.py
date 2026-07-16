#!/usr/bin/env python3
"""Fail-closed validator for the V8 skill-surface inventory receipt."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from audit_skill_surface import (
    AUDIT_KIND,
    CLASSIFICATION as AUDIT_CLASSIFICATION,
    SCHEMA,
    SCOPE,
    build_audit,
)


CLASSIFICATION = "audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Standard-library recomputation and hashing validate the live skill inventory fail closed.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
VALIDATION_SCHEMA = "codex-ratchet-skill-surface-validation-v1"
REQUIRED_FALSE_BOUNDARIES = (
    "all_skills_updated",
    "all_operational_body_parity_green",
    "candidate_installed",
    "skill_sync_authorized",
    "provider_calls_made",
    "llm_gate_authority",
    "promotion_allowed",
    "formal_admission_allowed",
    "release_allowed",
    "official_launch_allowed",
    "scientific_claim_allowed",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        dt.datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def validate_document(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if document.get("classification") != AUDIT_CLASSIFICATION:
        errors.append("classification must be audit")
    if document.get("audit_kind") != AUDIT_KIND:
        errors.append("audit_kind mismatch")
    if document.get("TOOL_MANIFEST") != {
        "python_stdlib": {
            "used": True,
            "reason": "Standard-library path, hash, and text inspection builds the read-only skill inventory.",
        }
    }:
        errors.append("TOOL_MANIFEST mismatch")
    if document.get("TOOL_INTEGRATION_DEPTH") != {"python_stdlib": "supportive"}:
        errors.append("TOOL_INTEGRATION_DEPTH mismatch")
    if document.get("scope") != list(SCOPE):
        errors.append("scope mismatch")
    if not validate_timestamp(document.get("observed_at_utc")):
        errors.append("observed_at_utc is not a UTC ISO timestamp")

    boundaries = document.get("claim_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("claim_boundaries missing")
    else:
        for key in REQUIRED_FALSE_BOUNDARIES:
            if boundaries.get(key) is not False:
                errors.append(f"claim boundary {key} must be false")

    roots = document.get("roots")
    if not isinstance(roots, dict):
        errors.append("roots missing")
        return errors
    try:
        repo_skill_root = Path(roots["repo_held"]).resolve()
        repo_root = repo_skill_root.parents[1]
        codex_root = Path(roots["codex_installed"]).resolve()
        agents_root = Path(roots["agents_installed"]).resolve()
    except (KeyError, IndexError, TypeError):
        errors.append("roots are malformed")
        return errors
    if repo_skill_root != repo_root / "system_v5/codex_skills":
        errors.append("repo_held root is not under repo_root/system_v5/codex_skills")

    expected = build_audit(
        repo_root=repo_root,
        codex_root=codex_root,
        agents_root=agents_root,
        observed_at_utc=document.get("observed_at_utc") if validate_timestamp(document.get("observed_at_utc")) else None,
    )
    for field in (
        "roots",
        "normalization_policy",
        "skills",
        "summary",
        "claim_boundaries",
        "verdict",
        "_selected_sources",
        "_index",
    ):
        if document.get(field) != expected.get(field):
            errors.append(f"{field} does not match live deterministic recomputation")

    summary = document.get("summary", {})
    if summary.get("missing_repo_source") != []:
        errors.append("sim-audit-spine repo-source repair regressed")
    if summary.get("candidate_not_installed") != ["claude-bridge"]:
        errors.append("claude-bridge candidate-not-installed state must remain explicit")
    drift = summary.get("repo_codex_body_drift")
    if drift != ["claude-bridge"]:
        errors.append("only the remaining claude-bridge operational-body drift is expected")
    exact = summary.get("exact_repo_codex_body_parity")
    if not isinstance(exact, list) or not {
        "codex-ratchet-sim-audit-spine",
        "codex-ratchet-deep-stack-stress",
    } <= set(exact):
        errors.append("repaired sim-audit-spine/deep-stack parity regressed")
    if document.get("verdict", {}).get("operational_surface_ready") is not False:
        errors.append("operational_surface_ready must remain false")

    return sorted(set(errors))


def validation_receipt(audit_path: Path, document: dict[str, Any]) -> dict[str, Any]:
    errors = validate_document(document)
    return {
        "schema": VALIDATION_SCHEMA,
        "classification": CLASSIFICATION,
        "audit_kind": "v8_skill_surface_validation",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "audit_path": str(audit_path.resolve()),
        "audit_sha256": sha256_file(audit_path),
        "validator_path": str(Path(__file__).resolve()),
        "validator_sha256": sha256_file(Path(__file__).resolve()),
        "checks": {
            "schema_and_scope": not any("schema" in item or "scope" in item for item in errors),
            "live_hashes_counts_and_routes": not any("recomputation" in item for item in errors),
            "claim_boundaries_fail_closed": not any("claim boundary" in item for item in errors),
            "known_red_gaps_preserved": not any(
                "must remain explicit" in item
                or "regressed" in item
                or "only the remaining" in item
                or "operational_surface_ready" in item
                for item in errors
            ),
        },
        "ok": not errors,
        "errors": errors,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "official_launch_allowed": False,
        "scientific_claim_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        document = json.loads(args.audit.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        document = {}
        receipt = {
            "schema": VALIDATION_SCHEMA,
            "classification": CLASSIFICATION,
            "audit_kind": "v8_skill_surface_validation",
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
            "audit_path": str(args.audit.resolve()),
            "audit_sha256": sha256_file(args.audit) if args.audit.is_file() else None,
            "validator_path": str(Path(__file__).resolve()),
            "validator_sha256": sha256_file(Path(__file__).resolve()),
            "checks": {},
            "ok": False,
            "errors": [f"could not load audit: {exc}"],
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
            "official_launch_allowed": False,
            "scientific_claim_allowed": False,
        }
    else:
        receipt = validation_receipt(args.audit, document)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": receipt["ok"], "errors": receipt["errors"]}, sort_keys=True))
    return 0 if receipt["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
