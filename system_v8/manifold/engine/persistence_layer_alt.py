#!/usr/bin/env python3
"""Redundant persistence layer for surviving distinctions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import digest, write_json


def flatten_histories(candidate: dict[str, Any], packet_id: str) -> list[list[list[int]]]:
    rows = []
    for history in candidate["packet_histories"][packet_id]["histories"]:
        rows.extend(history["states"])
    return rows


def parity(state: list[int]) -> int:
    return sum(state) % 2


def distinction_values(triple: list[list[int]]) -> dict[str, Any]:
    outer, middle, inner = triple
    return {
        "outer_state": outer,
        "middle_state": middle,
        "inner_state": inner,
        "outer_inner_pair": [outer, inner],
        "middle_inner_pair": [middle, inner],
        "outer_parity": parity(outer),
        "middle_parity": parity(middle),
        "inner_parity": parity(inner),
        "path_parity": (parity(outer) + parity(middle) + parity(inner)) % 2,
        "endpoint_equal": outer == inner,
    }


def inventory_for(candidate: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    packet_ids = [packet["packet_id"] for packet in source["nesting_packets"]]
    values_by_distinction: dict[str, dict[str, set[str]]] = {}
    for packet_id in packet_ids:
        histories = flatten_histories(candidate, packet_id)
        for triple in histories:
            for name, value in distinction_values(triple).items():
                values_by_distinction.setdefault(name, {}).setdefault(packet_id, set()).add(json.dumps(value, sort_keys=True))
    survived = {}
    constants = {}
    for name, packet_values in sorted(values_by_distinction.items()):
        present_everywhere = set(packet_values) == set(packet_ids) and all(packet_values[packet_id] for packet_id in packet_ids)
        if not present_everywhere:
            continue
        decoded = {
            packet_id: [json.loads(value) for value in sorted(packet_values[packet_id])]
            for packet_id in packet_ids
        }
        if any(len(values) > 1 for values in decoded.values()):
            survived[name] = decoded
        else:
            constants[name] = decoded
    return {
        "surviving_distinctions": survived,
        "constant_distinctions": constants,
        "surviving_count": len(survived),
        "constant_count": len(constants),
        "packet_ids": packet_ids,
    }


def run(source: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for name in history["frontier"]:
        candidate = history["candidate_evaluations"][name]
        rows[name] = {
            "candidate_id": name,
            **inventory_for(candidate, source),
        }
    purgatory = [
        {
            "candidate_id": name,
            "witness": {"not_in_current_history_frontier": True},
            "reoffer_rule": "re-offer if the history layer readmits this candidate to the current frontier",
        }
        for name in sorted(set(history["candidate_evaluations"]) - set(history["frontier"]))
    ]
    receipt = {
        "step": 0,
        "reason": "inventory derived distinctions that survive every allowed current-frontier history",
        "history_frontier": history["frontier"],
        "candidate_count_recomputed": len(rows),
        "purgatory": purgatory,
        "global_mss_claimed": False,
        "terminal_state": False,
    }
    receipt["receipt_digest"] = digest(receipt)
    checks = {
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "history_all_pass": history.get("all_pass") is True,
        "frontier_histories_inventoried": set(rows) == set(history.get("frontier", [])),
        "each_frontier_history_has_surviving_distinction": all(row["surviving_count"] > 0 for row in rows.values()),
        "purgatory_has_reoffer_rules": all(row["reoffer_rule"] for row in purgatory),
        "no_promotion": True,
    }
    result = {
        "schema": "ratchet.pack183.deep.persistence-alt.v1",
        "source_packet_digest": source["result_digest"],
        "history_digest": history["result_digest"],
        "candidate_count": len(rows),
        "candidate_inventories": rows,
        "frontier": sorted(rows),
        "purgatory": purgatory,
        "receipts": [receipt],
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "global_mss_claimed": False,
        "terminal_state": False,
        "claim_ceiling": "packet-relative persistence inventory over current history frontier only",
    }
    result["all_pass"] = all(checks.values())
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    history = json.loads(args.prior.read_text(encoding="utf-8"))
    result = run(source, history)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_count": result["candidate_count"],
        "frontier": result["frontier"],
        "surviving_counts": {
            name: row["surviving_count"]
            for name, row in result["candidate_inventories"].items()
        },
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
