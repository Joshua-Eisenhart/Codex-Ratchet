#!/usr/bin/env python3
"""Validate provider proposal receipts for formal-scout work."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RECEIPTS = ROOT / "provider_receipts"

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


def has_live_api_proof(data: dict[str, Any]) -> bool:
    if data.get("raw_response"):
        return True
    proof = data.get("live_api_proof")
    if not isinstance(proof, dict):
        return False
    return bool(proof.get("endpoint") and proof.get("model") and proof.get("answer_sha256"))


def validate(path: pathlib.Path, *, strict_live: bool = False) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing {key}")
    if data.get("schema") != "PROVIDER_PROPOSAL_RECEIPT_v1":
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
        targets = grounding.get("targets")
        if not isinstance(targets, list) or not targets:
            errors.append("completed receipt has no grounding targets")
    if strict_live and data.get("status") == "completed":
        provider = str(data.get("provider") or "").lower()
        if provider in LIVE_PROVIDER_NAMES and not has_live_api_proof(data):
            errors.append("strict-live completed provider receipt missing raw_response or live_api_proof")
        if "normalized" in path.name and not data.get("source_raw_receipt"):
            errors.append("strict-live normalized receipt missing source_raw_receipt")
    return {"path": str(path), "pass": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-live", action="store_true", help="Require completed live-provider receipts to carry raw API proof.")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    paths = [pathlib.Path(arg) for arg in args.paths] or sorted(RECEIPTS.glob("*.json"))
    rows = [validate(path, strict_live=args.strict_live) for path in paths]
    print(json.dumps({"all_pass": all(row["pass"] for row in rows), "results": rows}, indent=2, sort_keys=True))
    return 0 if all(row["pass"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
