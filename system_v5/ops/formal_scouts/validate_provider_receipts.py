#!/usr/bin/env python3
"""Validate provider proposal receipts for formal-scout work."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RECEIPTS = ROOT / "provider_receipts"
CANONICAL_SCHEMA = "PROVIDER_PROPOSAL_RECEIPT_v1"
LEGACY_GROUNDED_SCHEMAS = {
    "PROVIDER_SELECTOR_ENERGY_CROSS_AUDIT_v1",
}

REQUIRED = [
    "schema",
    "provider",
    "route",
    "status",
    "classification",
    "promotion_allowed",
    "evidence_allowed",
    "claim_ceiling",
    "repo_grounding",
]


LIVE_PROVIDER_NAMES = {
    "gemini",
    "gemini_direct",
    "google_gemini",
    "grok",
    "grok_xai",
    "xai_grok",
}


def sidecar_artifact_reason(path: pathlib.Path) -> str:
    """Return why a local JSON file is not a provider proposal receipt candidate."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if path.name.endswith(".receipt.json") and {"command", "output_path", "receipt_path"} <= set(data):
        return "claude_bridge_command_wrapper"
    if {"type", "subtype", "result", "session_id"} <= set(data) and "schema" not in data:
        return "claude_bridge_raw_output"
    if data.get("schema") == "PROVIDER_AUDIT_RECEIPT_v1":
        return "raw_provider_audit_receipt_requires_normalization"
    return ""


def receipt_candidate_paths(root: pathlib.Path = RECEIPTS) -> list[pathlib.Path]:
    return [
        path
        for path in sorted(root.glob("*.json"))
        if not sidecar_artifact_reason(path)
    ]


def has_live_api_proof(data: dict[str, Any]) -> bool:
    if data.get("raw_response"):
        return True
    proof = data.get("live_api_proof")
    if not isinstance(proof, dict):
        return False
    return bool(proof.get("endpoint") and proof.get("model") and proof.get("answer_sha256"))


def normalized_source_raw_receipt(data: dict[str, Any]) -> str:
    raw = data.get("source_raw_receipt")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    grounding = data.get("repo_grounding")
    if isinstance(grounding, dict):
        raw = grounding.get("source_raw_receipt")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return ""


def source_raw_receipt_exists(ref: str) -> bool:
    path = pathlib.Path(ref)
    if not path.is_absolute():
        path = REPO / path
    return path.exists()


def grounding_targets(data: dict[str, Any], grounding: dict[str, Any]) -> list[str]:
    targets = grounding.get("targets")
    if isinstance(targets, list) and any(str(target).strip() for target in targets):
        return [str(target) for target in targets if str(target).strip()]
    if data.get("schema") not in LEGACY_GROUNDED_SCHEMAS:
        return []
    result_path = str(grounding.get("result_path") or "").strip()
    plan_path = str(grounding.get("plan_path") or "").strip()
    if not result_path or not plan_path:
        return []
    if not grounding.get("result_sha256") or not grounding.get("plan_sha256"):
        return []
    return [result_path, plan_path]


def validate(path: pathlib.Path, *, strict_live: bool = False) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing {key}")
    schema = data.get("schema")
    if schema != CANONICAL_SCHEMA and schema not in LEGACY_GROUNDED_SCHEMAS:
        errors.append("wrong schema")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if data.get("evidence_allowed") is not False:
        errors.append("evidence_allowed must be false")
    if data.get("status") not in {"completed", "blocked", "failed"}:
        errors.append("invalid status")
    if data.get("status") == "completed" and not str(data.get("proposal_text", "")).strip():
        errors.append("completed receipt missing proposal_text")
    if data.get("status") in {"blocked", "failed"} and not str(data.get("blocked_reason", "")).strip():
        errors.append("blocked/failed receipt missing blocked_reason")
    grounding = data.get("repo_grounding")
    if not isinstance(grounding, dict):
        errors.append("repo_grounding is not an object")
    elif data.get("status") == "completed":
        targets = grounding_targets(data, grounding)
        if not targets:
            errors.append("completed receipt has no grounding targets")
    if strict_live and data.get("status") == "completed":
        provider = str(data.get("provider") or "").lower()
        if provider in LIVE_PROVIDER_NAMES and not has_live_api_proof(data):
            errors.append("strict-live completed provider receipt missing raw_response or live_api_proof")
        if "normalized" in path.name:
            source_raw = normalized_source_raw_receipt(data)
            if not source_raw:
                errors.append("strict-live normalized receipt missing source_raw_receipt")
            elif not source_raw_receipt_exists(source_raw):
                errors.append("strict-live normalized receipt source_raw_receipt path missing")
    return {"path": str(path), "pass": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-live", action="store_true", help="Require completed live-provider receipts to carry raw API proof.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    paths = [pathlib.Path(arg) for arg in args.paths] or receipt_candidate_paths()
    rows = [validate(path, strict_live=args.strict_live) for path in paths]
    print(json.dumps({"all_pass": all(row["pass"] for row in rows), "results": rows}, indent=2, sort_keys=True))
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
