#!/usr/bin/env python3
"""Regression guard for clean, refused, and unknown producer tier floors."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import producer_standing


REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "claimgate_plugin" / "fixtures" / "standing"
EXPECTATIONS = FIXTURES / "standing_regression_v1.json"
def _reason(expected: dict[str, Any], actual: dict[str, Any]) -> str:
    expected_floor = expected["expected_floor_tiers"]
    actual_floor = actual["floor_tiers"]
    if len(set(actual_floor)) != len(actual_floor):
        return "FLOOR_SHAPE_CHANGED"
    if actual_floor[: len(expected_floor)] == expected_floor and len(
        actual_floor
    ) > len(expected_floor):
        return "FLOOR_RAISED"
    if expected_floor[: len(actual_floor)] == actual_floor and len(
        actual_floor
    ) < len(expected_floor):
        return "FLOOR_LOWERED"
    if actual_floor != expected_floor:
        return "FLOOR_SHAPE_CHANGED"
    if actual["registry_tiers"] != expected["expected_registry_tiers"]:
        return "REGISTRY_TIERS_CHANGED"
    if actual["effective_tiers"] != expected["expected_effective_tiers"]:
        return "EFFECTIVE_TIERS_CHANGED"
    if actual["standing_band"] != expected["expected_standing_band"]:
        return "STANDING_BAND_CHANGED"
    return "MATCH"


def main() -> int:
    if not EXPECTATIONS.is_file():
        print("FIXTURE_MISSING expectations=" + str(EXPECTATIONS))
        return 1
    try:
        spec = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FIXTURE_MISSING expectations unreadable: {exc}")
        return 1
    cases = spec.get("cases")
    if not isinstance(cases, list) or not cases:
        print("NO_CASES_DECLARED")
        return 1

    claim_kind = spec.get("claim_kind")
    rows = []
    failed = False
    floors = set()
    for case in cases:
        ledger = FIXTURES / case["ledger"]
        if not ledger.is_file():
            rows.append((case["case"], case["producer"], "FIXTURE_MISSING", None))
            failed = True
            continue
        try:
            actual = producer_standing.floor_detail(
                claim_kind, case["producer"], ledger, REPO
            )
        except Exception as exc:  # regression reports infrastructure distinctly
            rows.append((case["case"], case["producer"], f"FIXTURE_ERROR:{exc}", None))
            failed = True
            continue
        verdict = _reason(case, actual)
        failed |= verdict != "MATCH"
        floors.add(tuple(actual["floor_tiers"]))
        rows.append((case["case"], case["producer"], verdict, (case, actual)))

    if len(floors) != len(cases):
        print("FLOORS_NOT_DISTINCT")
        failed = True

    headers = (
        "case",
        "producer",
        "claim_kind",
        "registry tiers",
        "floor tiers",
        "effective tiers",
        "expected",
        "actual",
        "verdict",
    )
    print(" | ".join(headers))
    print("-|-|-|-|-|-|-|-|-")
    for case_name, producer, verdict, payload in rows:
        if payload is None:
            print(
                f"{case_name} | {producer} | {claim_kind} | - | - | - | - | - | {verdict}"
            )
            continue
        expected, actual = payload
        expected_text = json.dumps(
            {
                "floor": expected["expected_floor_tiers"],
                "registry": expected["expected_registry_tiers"],
                "effective": expected["expected_effective_tiers"],
                "band": expected["expected_standing_band"],
            },
            separators=(",", ":"),
        )
        actual_text = json.dumps(
            {
                "floor": actual["floor_tiers"],
                "registry": actual["registry_tiers"],
                "effective": actual["effective_tiers"],
                "band": actual["standing_band"],
            },
            separators=(",", ":"),
        )
        print(
            " | ".join(
                [
                    case_name,
                    producer,
                    claim_kind,
                    json.dumps(actual["registry_tiers"]),
                    json.dumps(actual["floor_tiers"]),
                    json.dumps(actual["effective_tiers"]),
                    expected_text,
                    actual_text,
                    verdict,
                ]
            )
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
