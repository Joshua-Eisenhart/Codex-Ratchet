"""Normalized provider-call envelope for CB model route observations.

This module does not launch models. It wraps an already-observed provider call
under one CB schema so Luna, Grok, Claude, and later adapters can be compared
without treating provider-specific receipts as authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "constraintbox.provider-call.v1"
VERIFIED_REASON = "MMM_CALL_VERIFIED"
PROMOTION_ALLOWED = False
_HEX64 = frozenset("0123456789abcdef")
_TERMINAL_STATES = frozenset(
    {
        "OBSERVED",
        "REFUSED",
        "CANCELLED",
        "TIMEOUT",
        "ERROR",
        "BLOCKED",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    """CB-style canonical JSON bytes for hashes."""

    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_obj(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _is_hex64(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _HEX64


def build_provider_call_envelope(
    *,
    run_id: str,
    agent_id: str,
    parent_id: str | None,
    wave_id: str,
    round_index: int,
    depth: int,
    preload_receipt_sha256: str,
    provider: str,
    route: str,
    model_requested: str,
    model_observed: str | None,
    prompt_sha256: str,
    request_sha256: str,
    response_sha256: str | None,
    terminal_state: str,
    source_receipt_schema: str,
    source_receipt_sha256: str,
    started_at: str | None = None,
    completed_at: str | None = None,
    budget: dict[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a normalized provider-call envelope.

    The envelope binds route identity, hierarchy position, MMM preload evidence,
    provider request/response digests, and terminal state. It does not assert the
    model was intelligent or semantically correct.
    """

    body: dict[str, Any] = {
        "schema": SCHEMA,
        "run_id": run_id,
        "agent_id": agent_id,
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round_index": round_index,
        "depth": depth,
        "preload_receipt_sha256": preload_receipt_sha256,
        "provider": provider,
        "route": route,
        "model_requested": model_requested,
        "model_observed": model_observed,
        "prompt_sha256": prompt_sha256,
        "request_sha256": request_sha256,
        "response_sha256": response_sha256,
        "terminal_state": terminal_state,
        "started_at": started_at,
        "completed_at": completed_at,
        "budget": dict(budget or {}),
        "usage": dict(usage or {}),
        "source_receipt_schema": source_receipt_schema,
        "source_receipt_sha256": source_receipt_sha256,
        "claim_ceiling": (
            "one normalized provider call envelope; route/preload/request/terminal "
            "binding only; no semantic correctness or promotion"
        ),
        "promotion_allowed": PROMOTION_ALLOWED,
    }
    body["provider_call_sha256"] = sha256_obj(body)
    return body


def provider_call_validation_reasons(envelope: dict[str, Any]) -> list[str]:
    """Return reason codes preventing the envelope from earning MMM_CALL_VERIFIED."""

    reasons: list[str] = []
    if envelope.get("schema") != SCHEMA:
        reasons.append("WRONG_SCHEMA")
    for key in (
        "run_id",
        "agent_id",
        "wave_id",
        "provider",
        "route",
        "model_requested",
        "source_receipt_schema",
    ):
        if not isinstance(envelope.get(key), str) or not envelope[key].strip():
            reasons.append(f"MISSING_{key.upper()}")
    if not isinstance(envelope.get("round_index"), int) or envelope["round_index"] < 0:
        reasons.append("INVALID_ROUND_INDEX")
    if not isinstance(envelope.get("depth"), int) or envelope["depth"] < 0:
        reasons.append("INVALID_DEPTH")
    for key in (
        "preload_receipt_sha256",
        "prompt_sha256",
        "request_sha256",
        "source_receipt_sha256",
        "provider_call_sha256",
    ):
        if not _is_hex64(envelope.get(key)):
            reasons.append(f"INVALID_{key.upper()}")
    response_sha256 = envelope.get("response_sha256")
    if response_sha256 is not None and not _is_hex64(response_sha256):
        reasons.append("INVALID_RESPONSE_SHA256")
    if envelope.get("terminal_state") not in _TERMINAL_STATES:
        reasons.append("INVALID_TERMINAL_STATE")
    if envelope.get("promotion_allowed") is not PROMOTION_ALLOWED:
        reasons.append("PROMOTION_ALLOWED_NOT_FALSE")

    expected_hash = sha256_obj(
        {k: v for k, v in envelope.items() if k != "provider_call_sha256"}
    )
    if envelope.get("provider_call_sha256") != expected_hash:
        reasons.append("PROVIDER_CALL_HASH_MISMATCH")
    return reasons


def provider_call_verdict(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic verdict for a normalized provider-call envelope."""

    reasons = provider_call_validation_reasons(envelope)
    return {
        "schema": "constraintbox.provider-call-verdict.v1",
        "provider_call_sha256": envelope.get("provider_call_sha256"),
        "verdict": "VERIFIED" if not reasons else "HOLD",
        "reason_code": VERIFIED_REASON if not reasons else "PROVIDER_CALL_ENVELOPE_INVALID",
        "reasons": reasons,
        "claim_ceiling": "provider-call envelope shape and hash binding only",
        "promotion_allowed": PROMOTION_ALLOWED,
    }
