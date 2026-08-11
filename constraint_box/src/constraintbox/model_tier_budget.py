"""Deterministic model-tier admission and a receipt-backed spend ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .ledger import GENESIS, HashChainLedger


def tier_for_slug(slug: str, policy: Mapping[str, Any]) -> str:
    """Return the declared tier for an exact or trailing-prefix slug match."""

    if not isinstance(slug, str):
        return "UNKNOWN"
    for tier in ("cheap", "standard", "premium"):
        for pattern in policy.get("tiers", {}).get(tier, {}).get("slugs", ()):
            if not isinstance(pattern, str):
                continue
            if pattern.endswith("*"):
                if slug.startswith(pattern[:-1]):
                    return tier
            elif slug == pattern:
                return tier
    return "UNKNOWN"


def model_tier_reasons(
    model_requested: str,
    model_resolved: str,
    role: str,
    policy: Mapping[str, Any],
    spend: Mapping[str, Any],
    *,
    task_id: str | None = None,
) -> list[str]:
    """Return deterministic refusal codes for receipt-backed tier admission.

    ``spend`` contains projected counters by tier plus optional ``_attempts``
    and ``_owner_escalations`` receipt rows.  Rows are admitted only when they
    carry the stable root ``task_id`` from ``AgentTask``; attempt-specific IDs
    are not accepted as a second task identity.
    """

    del model_requested
    tier = tier_for_slug(model_resolved, policy)
    if tier == "UNKNOWN":
        return ["MODEL_TIER_UNKNOWN"]
    role_policy = policy.get("roles", {}).get(role, ())
    if isinstance(role_policy, Mapping):
        permitted = tuple(role_policy.get("permitted_tiers", ()))
        floor = role_policy.get("floor_tier")
    else:
        permitted = tuple(role_policy)
        floor = permitted[0] if permitted else None
    if tier not in permitted:
        return ["MODEL_TIER_ROLE_FORBIDDEN"]
    ceiling = policy.get("ceilings", {}).get(tier, {})
    current = spend.get(tier, {})
    max_dispatches = ceiling.get("max_dispatches")
    max_output_tokens = ceiling.get("max_output_tokens")
    if (
        max_dispatches is not None
        and current.get("dispatches", 0) >= max_dispatches
    ) or (
        max_output_tokens is not None
        and current.get("output_tokens", 0) >= max_output_tokens
    ):
        return ["MODEL_TIER_CEILING_EXHAUSTED"]

    if tier == floor:
        return []

    order = ("cheap", "standard", "premium")
    attempts = [
        row for row in spend.get("_attempts", ())
        if isinstance(row, Mapping) and row.get("task_id") == task_id
    ]
    escalations = [
        row for row in spend.get("_owner_escalations", ())
        if isinstance(row, Mapping) and row.get("task_id") == task_id
    ]
    if any(row.get("to_tier") == tier for row in escalations):
        return []

    failed = {
        row.get("tier") for row in attempts
        if str(row.get("outcome", "")).lower() not in {"success", "succeeded"}
    }
    attempted = {row.get("tier") for row in attempts}
    highest_attempted = max(
        (order.index(row.get("tier")) for row in attempts if row.get("tier") in order),
        default=-1,
    )
    target_index = order.index(tier)
    if tier == "premium" and "cheap" in failed and "standard" not in attempted:
        return ["MODEL_TIER_ESCALATION_SKIPS_RUNG"]
    if highest_attempted >= 0 and target_index == highest_attempted + 1:
        if order[highest_attempted] in failed:
            return []
    return ["MODEL_TIER_ESCALATION_UNJUSTIFIED"]


class ModelTierLedger:
    """Append model spend records using the repository hash-chain primitive."""

    def __init__(self, path: Path):
        self._ledger = HashChainLedger(Path(path))

    def _next_seq(self) -> int:
        if not self._ledger.path.exists():
            return 1
        return len(self._ledger.path.read_text(encoding="utf-8").splitlines()) + 1

    def _previous_sha256(self) -> str:
        if not self._ledger.path.exists() and not self._ledger.head_path.exists():
            return GENESIS
        return self._ledger.head_path.read_text(encoding="ascii").strip()

    def append(
        self,
        *,
        model_resolved: str,
        tier: str,
        role: str,
        output_tokens: int,
        dispatch_index: int,
        task_id: str = "",
        outcome: str = "failed",
    ) -> str:
        record = {
            "seq": self._next_seq(),
            "prev_sha256": self._previous_sha256(),
            "model_resolved": model_resolved,
            "tier": tier,
            "role": role,
            "output_tokens": output_tokens,
            "dispatch_index": dispatch_index,
            "task_id": task_id,
            "outcome": outcome,
        }
        return self._ledger.append(record)

    def verify(self) -> tuple[bool, str]:
        return self._ledger.verify()


def spend_from_ledger(path: Path) -> dict[str, dict[str, int]]:
    """Build projected spend counters from a verified ledger."""

    ledger = HashChainLedger(Path(path))
    valid, reason = ledger.verify()
    if not valid:
        raise ValueError(f"invalid model tier ledger: {reason}")
    totals: dict[str, Any] = {"_attempts": []}
    if not ledger.path.exists():
        return totals
    for line in ledger.path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        record = row["record"]
        tier = record["tier"]
        bucket = totals.setdefault(tier, {"dispatches": 0, "output_tokens": 0})
        bucket["dispatches"] += 1
        bucket["output_tokens"] += record["output_tokens"]
        totals["_attempts"].append(
            {key: record.get(key) for key in ("task_id", "tier", "outcome")}
        )
    return totals
