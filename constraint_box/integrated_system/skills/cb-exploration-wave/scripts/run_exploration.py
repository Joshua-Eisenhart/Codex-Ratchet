#!/usr/bin/env python3
"""Harvest rival readings and keep an antichain.

This is the deterministic floor of cb-exploration-wave.
It does not falsify, pick a winner, or claim a model ran.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RECEIPT_SCHEMA = "constraintbox.exploration-receipt.v1"
ANTICHAIN_SCHEMA = "constraintbox.exploration-antichain.v1"

DEFAULT_READINGS = [
    {
        "id": "R-layer-order",
        "family": "layer_order_after_C0",
        "text": "After C0, later layers may be ordered differently than the seed writes.",
    },
    {
        "id": "R-lr-order-scar",
        "family": "left_right_meaning",
        "text": "L and R are an order scar, not yet chirality.",
    },
    {
        "id": "R-lr-two-manifolds",
        "family": "left_right_meaning",
        "text": "L and R are two functional manifolds, not two times.",
    },
    {
        "id": "R-probe-family",
        "family": "probe_family_M",
        "text": "A rival probe family M may split the same support differently.",
    },
    {
        "id": "R-demand-set",
        "family": "demand_set_D",
        "text": "A rival demand set D may thicken a different edge set.",
    },
    {
        "id": "R-basin-vs-fuzz",
        "family": "static_basin",
        "text": "A static basin may be leftover fuzz, not an attractor.",
    },
    {
        "id": "R-fibre-record",
        "family": "capacity_earning",
        "text": "Fibre or record may become earned later; they are unearned on this seed.",
    },
    {
        "id": "R-heavy-return",
        "family": "heavy_observation",
        "text": "Heavy may return an observation Light must recompute; it must not rewrite F.",
    },
]


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_readings(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return list(DEFAULT_READINGS)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("readings"), list):
        data = data["readings"]
    if not isinstance(data, list):
        raise ValueError("readings must be a list")
    out: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict) or not {"id", "family", "text"} <= item.keys():
            raise ValueError("reading shape")
        out.append(
            {
                "id": str(item["id"]),
                "family": str(item["family"]),
                "text": str(item["text"]),
            }
        )
    return out


def run_wave(
    *,
    root: Path,
    seed: Path,
    out: Path,
    readings_path: Path | None = None,
    pick_winner: bool = False,
    falsify: bool = False,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    seed = seed if seed.is_absolute() else (root / seed)
    if pick_winner:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "REFUSE",
            "reason": "REFUSE_WINNER",
            "winner_selected": True,
            "promotion_allowed": False,
        }
        _write(out, receipt)
        return receipt
    if falsify:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "REFUSE",
            "reason": "REFUSE_DEDUCTION_ON_INDUCTION",
            "winner_selected": False,
            "promotion_allowed": False,
        }
        _write(out, receipt)
        return receipt
    if not seed.is_file():
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": "HOLD_SEED_MISSING",
            "winner_selected": False,
            "promotion_allowed": False,
        }
        _write(out, receipt)
        return receipt

    readings = _load_readings(readings_path)
    families = {item["family"] for item in readings}
    if len(readings) < 2 or len(families) < 2:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "HOLD",
            "reason": "HOLD_COLLAPSED_DIVERSITY",
            "reading_count": len(readings),
            "family_count": len(families),
            "winner_selected": False,
            "promotion_allowed": False,
        }
        _write(out, receipt)
        return receipt

    hidden_third = next(
        (item["id"] for item in readings if item["id"] == "R-lr-two-manifolds"),
        readings[2]["id"] if len(readings) > 2 else readings[0]["id"],
    )
    antichain = {
        "schema": ANTICHAIN_SCHEMA,
        "surface_class": "PROPOSAL_A1",
        "promotion_allowed": False,
        "winner_selected": False,
        "members": readings,
        "family_count": len(families),
        "hidden_third": hidden_third,
        "must_not_do": [
            "pick a winner",
            "run falsification here",
            "collapse L/R into one time",
            "import FEP as Light geometry",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    antichain_path = out.with_name("antichain.draft.json")
    _write(antichain_path, antichain)

    left, right = readings[0], readings[1]
    packet = {
        "schema": "constraintbox.distinguishability.packet.v1",
        "claim": (
            f"harvested readings {left['id']} and {right['id']} belong to "
            "different families under a one-probe family"
        ),
        "claim_ceiling": "exists",
        "candidates": [left["id"], right["id"]],
        "probes": ["family"],
        "probe_domains": {"family": sorted(families)},
        "demand_D": [
            {
                "left": left["id"],
                "right": right["id"],
                "id": "harvest_pair",
                "why_demanded": "rival readings must not collapse into one family",
            }
        ],
        "constraints_C": [],
        "query": "distinguish",
        "theory": "finite",
        "authority": "none",
    }
    packet_path = out.with_name("distinguish.packet.json")
    _write(packet_path, packet)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "captured_at": _now(),
        "status": "ANTICHAIN_OPEN",
        "promotion_allowed": False,
        "seed": str(seed),
        "seed_digest": _sha256_path(seed),
        "reading_count": len(readings),
        "family_count": len(families),
        "antichain_ids": [item["id"] for item in readings],
        "antichain_draft": str(antichain_path),
        "antichain_digest": _sha256_path(antichain_path),
        "distinguish_packet": str(packet_path),
        "distinguish_packet_digest": _sha256_path(packet_path),
        "hidden_third": hidden_third,
        "winner_selected": False,
        "new_rival_readings": len(readings),
        "epistemology": {
            "this_wave": "induction_harvest",
            "not": ["falsification", "deduction", "verify"],
            "later_excludes": "cb-failure-wave and dualsolve",
        },
        "claim_ceiling": (
            "rival-reading harvest only; not a kill; not a quotient; not promotion"
        ),
    }
    _write(out, receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CB exploration harvest")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--readings", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pick-winner", action="store_true")
    parser.add_argument("--falsify", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_wave(
        root=args.root,
        seed=args.seed,
        out=args.out,
        readings_path=args.readings,
        pick_winner=args.pick_winner,
        falsify=args.falsify,
    )
    print(json.dumps({"status": receipt.get("status"), "reason": receipt.get("reason")}, sort_keys=True))
    return 0 if receipt.get("status") == "ANTICHAIN_OPEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
