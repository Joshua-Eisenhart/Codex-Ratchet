#!/usr/bin/env python3
"""Fail-closed validator for provider catalog and advisory preflight receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CATALOG_SCHEMA = "codex_ratchet.provider_catalog_receipt.v1"
PREFLIGHT_SCHEMA = "codex_ratchet.provider_advisory_preflight.v1"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
PRODUCER = HERE / "provider_advisory_control.py"
ROUTES = json.loads((HERE / "provider_routes.json").read_text(encoding="utf-8"))
SAFE_RATE_HEADERS = {
    "retry-after",
    "ratelimit-limit",
    "ratelimit-remaining",
    "ratelimit-reset",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_fences = {
        "classification": "provider_advisory_control",
        "advisory_only": True,
        "gate_authority": False,
        "evidence_allowed": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "scientific_claim_proven": False,
    }
    for key, expected in required_fences.items():
        if payload.get(key) != expected:
            errors.append(f"{key} fence mismatch")
    if "deterministic local Ratchet gates decide truth" not in str(
        payload.get("claim_ceiling")
    ):
        errors.append("claim ceiling is not provider-nonauthoritative")
    schema = payload.get("schema")
    if schema == CATALOG_SCHEMA:
        models = payload.get("models")
        provider = payload.get("provider")
        route = ROUTES.get("providers", {}).get(provider)
        if not isinstance(route, dict):
            errors.append("catalog provider is not configured")
        else:
            if payload.get("endpoint") != route.get("catalog_endpoint"):
                errors.append("catalog endpoint mismatch")
            if payload.get("key_env") != route.get("key_env"):
                errors.append("catalog key_env mismatch")
        if not isinstance(payload.get("key_present"), bool):
            errors.append("catalog key_present must be boolean")
        source = payload.get("source")
        expected_source = str(PRODUCER.relative_to(REPO_ROOT))
        if not isinstance(source, dict):
            errors.append("catalog source binding missing")
        else:
            if source.get("path") != expected_source:
                errors.append("catalog source path mismatch")
            if source.get("sha256") != file_sha256(PRODUCER):
                errors.append("catalog source hash mismatch")
        headers = payload.get("rate_limit_observations")
        if not isinstance(headers, dict) or not set(headers) <= SAFE_RATE_HEADERS:
            errors.append("catalog rate-limit headers contain unsupported keys")
        if payload.get("status") not in {"completed", "blocked", "failed"}:
            errors.append("catalog status invalid")
        if payload.get("status") == "completed":
            if (
                not isinstance(models, list)
                or not models
                or models != sorted(set(models))
            ):
                errors.append("catalog models must be nonempty, sorted, and unique")
            else:
                if payload.get("model_count") != len(models):
                    errors.append("catalog model_count mismatch")
                if payload.get("model_catalog_sha256") != canonical_sha256(models):
                    errors.append("catalog hash mismatch")
    elif schema == PREFLIGHT_SCHEMA:
        decision = payload.get("decision")
        reason = payload.get("reason")
        if decision not in {"HOLD", "ADVISORY_DISPATCH_ALLOWED"}:
            errors.append("preflight decision invalid")
        if decision == "ADVISORY_DISPATCH_ALLOWED":
            if reason != "catalog_and_quota_green":
                errors.append("dispatch opened without green reason")
            if (
                not isinstance(payload.get("max_requests"), int)
                or payload["max_requests"] <= 0
            ):
                errors.append("dispatch opened without positive max_requests")
            if (
                not isinstance(payload.get("window_seconds"), int)
                or payload["window_seconds"] <= 0
            ):
                errors.append("dispatch opened without positive window_seconds")
            if (
                not isinstance(payload.get("remaining_requests"), int)
                or payload["remaining_requests"] <= 0
            ):
                errors.append("dispatch opened without remaining quota")
        elif reason == "catalog_and_quota_green":
            errors.append("HOLD cannot carry green reason")
        for key in ("catalog", "quota_policy"):
            binding = payload.get(key)
            if not isinstance(binding, dict):
                errors.append(f"{key} binding missing")
                continue
            raw_path = binding.get("path")
            expected_hash = binding.get("sha256")
            if not isinstance(raw_path, str) or not Path(raw_path).is_file():
                errors.append(f"{key} bound file missing")
            elif expected_hash != file_sha256(Path(raw_path)):
                errors.append(f"{key} bound file hash mismatch")
    else:
        errors.append("unsupported schema")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.receipt.read_text(encoding="utf-8"))
        errors = validate(payload)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        errors = [f"parse failure: {type(error).__name__}"]
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
