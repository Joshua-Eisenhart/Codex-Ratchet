#!/usr/bin/env python3
"""Small helpers for conservative sim receipt boundary fields."""

from __future__ import annotations

from typing import Any


OUT_OF_SCOPE = [
    "QIT engine admission",
    "GStack promotion",
    "axis promotion",
    "nonclassical admission",
    "bridge admission",
]


def _set_missing_or_empty(results: dict[str, Any], key: str, value: Any) -> None:
    if not results.get(key):
        results[key] = value


def apply_default_receipt_boundary(
    results: dict[str, Any],
    *,
    source_name: str,
    target: str = "Use as bounded lego evidence for later coupling packets after exact companion receipts.",
) -> dict[str, Any]:
    """Backfill conservative run-boundary fields without changing sim math."""
    receipt_name = str(results.get("name") or source_name)
    _set_missing_or_empty(
        results,
        "claim_ceiling",
        f"finite {receipt_name} lego receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
    )
    _set_missing_or_empty(results, "next_lego_target", target)
    _set_missing_or_empty(
        results,
        "promotion_condition",
        "Requires separate coupling/coexistence receipts and explicit stage-gate approval.",
    )
    _set_missing_or_empty(
        results,
        "blocked_until",
        "explicit coupling-stage admission and companion receipts",
    )
    _set_missing_or_empty(
        results,
        "demotion_condition",
        "Demote if rerun fails, tool-depth evidence disappears, or boundary controls fail.",
    )
    _set_missing_or_empty(results, "out_of_scope", OUT_OF_SCOPE)
    return results
