#!/usr/bin/env python3
"""Dynamic provider catalog and quota preflight for advisory-only model lanes.

This module never performs inference. Catalog discovery is a GET against a
configured /models endpoint. Dispatch preflight is local and fails closed when
the exact model or account/model quota is unknown.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from typing import Any


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
ROUTES_PATH = HERE / "provider_routes.json"
CATALOG_SCHEMA = "codex_ratchet.provider_catalog_receipt.v1"
PREFLIGHT_SCHEMA = "codex_ratchet.provider_advisory_preflight.v1"
NONAUTHORITY = {
    "classification": "provider_advisory_control",
    "advisory_only": True,
    "gate_authority": False,
    "evidence_allowed": False,
    "promotion_allowed": False,
    "formal_admission_allowed": False,
    "scientific_claim_proven": False,
    "claim_ceiling": "Provider routing and quota control only; deterministic local Ratchet gates decide truth.",
}
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


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route_config(provider: str, routes_path: Path = ROUTES_PATH) -> dict[str, str]:
    routes = load_json(routes_path)
    if routes.get("schema") != "codex_ratchet.provider_routes.v1":
        raise ValueError("provider route schema mismatch")
    config = routes.get("providers", {}).get(provider)
    if not isinstance(config, dict):
        raise ValueError(f"unknown provider: {provider}")
    endpoint = config.get("catalog_endpoint")
    key_env = config.get("key_env")
    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        raise ValueError("catalog endpoint must be HTTPS")
    if not isinstance(key_env, str) or not key_env.endswith("_API_KEY"):
        raise ValueError("provider key environment name is invalid")
    return {"catalog_endpoint": endpoint, "key_env": key_env}


def parse_models(payload: Any) -> list[str]:
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("catalog response must contain a data array")
    models = sorted(
        {
            row.get("id").strip()
            for row in payload["data"]
            if isinstance(row, dict)
            and isinstance(row.get("id"), str)
            and row.get("id").strip()
        }
    )
    if not models:
        raise ValueError("catalog returned no model IDs")
    return models


def safe_rate_headers(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    return {
        str(key).lower(): str(value)
        for key, value in headers.items()
        if str(key).lower() in SAFE_RATE_HEADERS
    }


def fetch_catalog(endpoint: str, key: str, timeout: float) -> tuple[Any, int, dict[str, str]]:
    request = urllib.request.Request(
        endpoint,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return (
            json.loads(response.read().decode("utf-8")),
            int(response.status),
            safe_rate_headers(response.headers),
        )


def catalog_receipt(
    provider: str,
    *,
    fixture: Path | None = None,
    timeout: float = 10.0,
    routes_path: Path = ROUTES_PATH,
) -> tuple[dict[str, Any], int]:
    started = utc_now()
    config = route_config(provider, routes_path)
    key_present = bool(os.environ.get(config["key_env"]))
    base: dict[str, Any] = {
        "schema": CATALOG_SCHEMA,
        **NONAUTHORITY,
        "provider": provider,
        "endpoint": config["catalog_endpoint"],
        "key_env": config["key_env"],
        "key_present": key_present,
        "started_at": started,
        "completed_at": utc_now(),
        "source": {
            "path": str(Path(__file__).resolve().relative_to(REPO_ROOT)),
            "sha256": file_sha256(Path(__file__).resolve()),
        },
        "fixture_used": fixture is not None,
        "http_status": None,
        "rate_limit_observations": {},
        "models": [],
        "model_count": 0,
        "model_catalog_sha256": canonical_sha256([]),
        "blocked_reason": None,
    }
    try:
        if fixture is not None:
            payload = load_json(fixture)
            status = 200
            headers: dict[str, str] = {}
        elif not key_present:
            base.update(status="blocked", blocked_reason=f"{config['key_env']} not set")
            return base, 2
        else:
            payload, status, headers = fetch_catalog(
                config["catalog_endpoint"], os.environ[config["key_env"]], timeout
            )
        models = parse_models(payload)
        base.update(
            status="completed",
            completed_at=utc_now(),
            http_status=status,
            rate_limit_observations=headers,
            models=models,
            model_count=len(models),
            model_catalog_sha256=canonical_sha256(models),
        )
        return base, 0
    except (OSError, ValueError, json.JSONDecodeError, urllib.error.URLError) as error:
        base.update(
            status="failed",
            completed_at=utc_now(),
            blocked_reason=f"catalog probe failed: {type(error).__name__}",
        )
        return base, 3


def select_policy(policy_payload: Any, provider: str, model: str) -> dict[str, Any] | None:
    if (
        not isinstance(policy_payload, dict)
        or policy_payload.get("schema") != "codex_ratchet.provider_quota_policy.v1"
    ):
        raise ValueError("quota policy schema mismatch")
    policies = policy_payload.get("policies")
    if not isinstance(policies, list):
        raise ValueError("quota policies must be an array")
    exact = [
        row
        for row in policies
        if isinstance(row, dict)
        and row.get("provider") == provider
        and row.get("model") == model
    ]
    wildcard = [
        row
        for row in policies
        if isinstance(row, dict)
        and row.get("provider") == provider
        and row.get("model") == "*"
    ]
    return (exact or wildcard or [None])[0]


def ledger_count(
    ledger_path: Path | None,
    provider: str,
    model: str,
    now: dt.datetime,
    window_seconds: int,
) -> int:
    if ledger_path is None or not ledger_path.exists():
        return 0
    cutoff = now - dt.timedelta(seconds=window_seconds)
    count = 0
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            when = dt.datetime.fromisoformat(
                str(row.get("timestamp", "")).replace("Z", "+00:00")
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
        if when.tzinfo is None:
            continue
        if (
            row.get("provider") == provider
            and row.get("model") == model
            and when.astimezone(dt.UTC) >= cutoff
        ):
            count += 1
    return count


def preflight_receipt(
    catalog_path: Path,
    policy_path: Path,
    provider: str,
    model: str,
    *,
    ledger_path: Path | None = None,
    now: dt.datetime | None = None,
) -> tuple[dict[str, Any], int]:
    now = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC)
    catalog = load_json(catalog_path)
    policy = select_policy(load_json(policy_path), provider, model)
    decision = "HOLD"
    reason = "unknown"
    used = 0
    remaining: int | None = None
    max_requests: int | None = None
    window_seconds: int | None = None
    if catalog.get("schema") != CATALOG_SCHEMA or catalog.get("status") != "completed":
        reason = "catalog_not_completed"
    elif catalog.get("provider") != provider:
        reason = "catalog_provider_mismatch"
    elif catalog.get("model_catalog_sha256") != canonical_sha256(catalog.get("models")):
        reason = "catalog_hash_mismatch"
    elif model not in catalog.get("models", []):
        reason = "model_not_in_catalog"
    elif not policy:
        reason = "quota_policy_missing"
    else:
        max_requests = policy.get("max_requests")
        window_seconds = policy.get("window_seconds")
        if (
            not isinstance(max_requests, int)
            or max_requests <= 0
            or not isinstance(window_seconds, int)
            or window_seconds <= 0
        ):
            reason = "quota_unknown"
        else:
            used = ledger_count(ledger_path, provider, model, now, window_seconds)
            remaining = max(0, max_requests - used)
            if remaining <= 0:
                reason = "quota_exhausted"
            else:
                decision = "ADVISORY_DISPATCH_ALLOWED"
                reason = "catalog_and_quota_green"
    receipt = {
        "schema": PREFLIGHT_SCHEMA,
        **NONAUTHORITY,
        "generated_at": now.isoformat(),
        "provider": provider,
        "model": model,
        "catalog": {
            "path": str(catalog_path.resolve()),
            "sha256": file_sha256(catalog_path),
        },
        "quota_policy": {
            "path": str(policy_path.resolve()),
            "sha256": file_sha256(policy_path),
        },
        "ledger": (
            None
            if ledger_path is None
            else {"path": str(ledger_path.resolve()), "exists": ledger_path.exists()}
        ),
        "max_requests": max_requests,
        "window_seconds": window_seconds,
        "observed_requests_in_window": used,
        "remaining_requests": remaining,
        "decision": decision,
        "reason": reason,
    }
    return receipt, 0 if decision == "ADVISORY_DISPATCH_ALLOWED" else 2


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    catalog = sub.add_parser("catalog")
    catalog.add_argument("--provider", required=True, choices=("nvidia", "xai"))
    catalog.add_argument("--fixture", type=Path)
    catalog.add_argument("--timeout", type=float, default=10.0)
    catalog.add_argument("--out", type=Path, required=True)
    preflight = sub.add_parser("preflight")
    preflight.add_argument("--provider", required=True, choices=("nvidia", "xai"))
    preflight.add_argument("--model", required=True)
    preflight.add_argument("--catalog", type=Path, required=True)
    preflight.add_argument("--quota-policy", type=Path, required=True)
    preflight.add_argument("--ledger", type=Path)
    preflight.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "catalog":
        receipt, code = catalog_receipt(
            args.provider, fixture=args.fixture, timeout=args.timeout
        )
    else:
        receipt, code = preflight_receipt(
            args.catalog,
            args.quota_policy,
            args.provider,
            args.model,
            ledger_path=args.ledger,
        )
    write_receipt(args.out, receipt)
    print(
        json.dumps(
            {
                "schema": receipt["schema"],
                "status": receipt.get("status"),
                "decision": receipt.get("decision"),
                "reason": receipt.get("reason"),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
