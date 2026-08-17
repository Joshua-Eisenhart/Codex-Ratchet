"""Quotient and static basins from bound observation rows only.

Light verb 6 in LIGHT_CONTRACT: components come from bound rows.
Solver-chosen ``obs__*`` witnesses are not rows. Missing rows HOLD.
Geometry here is the indistinguishability relation, not a metric.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


PACKET_SCHEMA = "constraintbox.bound-observation.packet.v1"
RECEIPT_SCHEMA = "constraintbox.bound-observation.receipt.v1"
OPERATION = "bound_observation_quotient.v1"


class BoundQuotientError(ValueError):
    """The packet is not a finite bound-observation object."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BoundQuotientError(f"{path} must be an object")
    actual = set(value)
    if actual != expected:
        raise BoundQuotientError(
            f"{path} fields differ: missing={sorted(expected - actual)!r}, "
            f"extra={sorted(actual - expected)!r}"
        )
    return value


def _unique_names(values: Any, path: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise BoundQuotientError(f"{path} must be a nonempty list")
    if any(not isinstance(item, str) or not item for item in values):
        raise BoundQuotientError(f"{path} entries must be nonempty text")
    if len(set(values)) != len(values):
        raise BoundQuotientError(f"{path} entries must be unique")
    return list(values)


def parse_bound_packet(raw: dict[str, Any]) -> dict[str, Any]:
    root = _exact_keys(
        raw,
        {
            "schema",
            "claim",
            "candidates",
            "probes",
            "rows",
            "authority",
            "promotion_allowed",
        },
        "$",
    )
    if root["schema"] != PACKET_SCHEMA:
        raise BoundQuotientError("unsupported bound-observation schema")
    if root["authority"] != "none":
        raise BoundQuotientError("authority must be none")
    if root["promotion_allowed"] is not False:
        raise BoundQuotientError("promotion_allowed must be false")
    candidates = _unique_names(root["candidates"], "$.candidates")
    probes = _unique_names(root["probes"], "$.probes")
    rows = root["rows"]
    if not isinstance(rows, list) or not rows:
        raise BoundQuotientError("$.rows must be a nonempty list")
    table: dict[tuple[str, str], Any] = {}
    for index, row in enumerate(rows):
        item = _exact_keys(
            row, {"candidate", "probe", "value"}, f"$.rows[{index}]"
        )
        candidate = item["candidate"]
        probe = item["probe"]
        if candidate not in candidates:
            raise BoundQuotientError(f"unknown candidate in row {index}")
        if probe not in probes:
            raise BoundQuotientError(f"unknown probe in row {index}")
        key = (candidate, probe)
        if key in table:
            raise BoundQuotientError(f"duplicate row for {candidate}/{probe}")
        table[key] = item["value"]
    missing = [
        f"{candidate}/{probe}"
        for candidate in candidates
        for probe in probes
        if (candidate, probe) not in table
    ]
    return {
        "claim": root["claim"],
        "candidates": candidates,
        "probes": probes,
        "table": table,
        "missing": missing,
    }


def _same_under_probes(
    left: str, right: str, probes: list[str], table: dict[tuple[str, str], Any]
) -> bool:
    return all(table[(left, probe)] == table[(right, probe)] for probe in probes)


def induce_quotient(parsed: dict[str, Any]) -> dict[str, Any]:
    """Build S/~_P from a complete bound table. Incomplete tables HOLD."""

    candidates: list[str] = parsed["candidates"]
    probes: list[str] = parsed["probes"]
    table: dict[tuple[str, str], Any] = parsed["table"]
    if parsed["missing"]:
        return {
            "schema": RECEIPT_SCHEMA,
            "operation": OPERATION,
            "status": "HOLD",
            "reason": "REFUSE_UNBOUND_OBSERVATION",
            "missing_rows": list(parsed["missing"]),
            "quotient_admitted": False,
            "promotion_allowed": False,
            "claim_ceiling": (
                "incomplete bound rows; no quotient, no basin, no measured distinguishability"
            ),
        }

    split: list[dict[str, Any]] = []
    fuzz: list[dict[str, str]] = []
    parent = {name: name for name in candidates}

    def find(name: str) -> str:
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            if _same_under_probes(left, right, probes, table):
                fuzz.append({"left": left, "right": right})
                parent[find(right)] = find(left)
            else:
                differing = [
                    probe
                    for probe in probes
                    if table[(left, probe)] != table[(right, probe)]
                ]
                split.append({"left": left, "right": right, "probes": differing})

    classes: dict[str, list[str]] = {}
    for name in candidates:
        classes.setdefault(find(name), []).append(name)
    basins = [
        {"id": f"B{index}", "members": members, "size": len(members)}
        for index, members in enumerate(classes.values())
    ]
    tuples = [
        tuple(table[(candidate, probe)] for probe in probes) for candidate in candidates
    ]
    distinct = len(set(tuples))
    record_k = math.log2(distinct) if distinct > 0 else 0.0
    support_k = math.log2(len(candidates))
    return {
        "schema": RECEIPT_SCHEMA,
        "operation": OPERATION,
        "status": "PASS",
        "quotient_admitted": True,
        "promotion_allowed": False,
        "claim": parsed["claim"],
        "claim_ceiling": (
            "probe-relative quotient from bound observation rows only; "
            "static basins are leftover classes, not attractors or engines"
        ),
        "relation": "~_P",
        "fuzz": fuzz,
        "split": split,
        "basins": basins,
        "geometry": "indistinguishability_relation",
        "not": ["metric", "attractor", "engine", "tda", "solver_chosen_obs"],
        "capacities": {
            "support": {
                "status": "computed",
                "W": len(candidates),
                "K": support_k,
            },
            "fibre": {
                "status": "unearned",
                "reason": "no projection declared; classes are not fibres",
            },
            "record": {
                "status": "computed",
                "row_count": len(candidates) * len(probes),
                "distinct_observation_tuples": distinct,
                "K_distinct_tuples": record_k,
            },
        },
    }


def decide_bound_packet(raw: dict[str, Any]) -> dict[str, Any]:
    try:
        parsed = parse_bound_packet(raw)
    except BoundQuotientError as exc:
        payload = {
            "schema": RECEIPT_SCHEMA,
            "operation": OPERATION,
            "status": "HOLD",
            "reason": str(exc),
            "quotient_admitted": False,
            "promotion_allowed": False,
            "packet_sha256": _sha256(raw),
        }
        payload["receipt_sha256"] = _sha256(payload)
        return payload
    payload = induce_quotient(parsed)
    payload["packet_sha256"] = _sha256(raw)
    payload["receipt_sha256"] = _sha256(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )
    return payload
