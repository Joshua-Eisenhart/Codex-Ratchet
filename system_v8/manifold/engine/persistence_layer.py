#!/usr/bin/env python3
"""Inventory state distinctions surviving every allowed finite history."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from common import digest, write_json
from connection_layer import state_key
from history_layer import CANDIDATES as HISTORY_CANDIDATES, apply_table


SCHEMA = "ratchet.pack183.deep-persistence-layer.v1"
CLAIM_CEILING = (
    "packet-relative finite R3 distinction persistence inventory only; no promotion, "
    "formal admission, canonical invariant, physics, or exhaustive-history claim"
)


def current_outer_states(source: dict[str, Any]) -> list[tuple[int, int, int]]:
    return sorted({
        tuple(int(bit) for bit in state)
        for packet in source["nesting_packets"]
        for state in packet["layer_values"][2]
    })


def distinction_id(left: tuple[int, int, int], right: tuple[int, int, int]) -> str:
    return f"{state_key(left)}|{state_key(right)}"


def compute_inventories(source: dict[str, Any], history: dict[str, Any]) -> dict[str, dict[str, Any]]:
    states = current_outer_states(source)
    pairs = list(itertools.combinations(states, 2))
    inventories: dict[str, dict[str, Any]] = {}
    for connection_id in history["connection_candidates"]:
        connection_table = history["transport_tables"][connection_id]
        for history_id in HISTORY_CANDIDATES:
            history_row = history["history_evaluations"][history_id]
            allowed_tables = {"selected_connection": connection_table}
            allowed_tables.update(history_row["history_tables"])
            surviving = []
            excluded = []
            for left, right in pairs:
                counterexample = None
                for history_name, table in sorted(allowed_tables.items()):
                    left_output = apply_table(table, left)
                    right_output = apply_table(table, right)
                    if left_output == right_output:
                        counterexample = {
                            "history": history_name,
                            "left_output": list(left_output),
                            "right_output": list(right_output),
                        }
                        break
                row = {
                    "distinction_id": distinction_id(left, right),
                    "left_state": list(left),
                    "right_state": list(right),
                }
                if counterexample is None:
                    surviving.append(row)
                else:
                    row["counterexample"] = counterexample
                    excluded.append(row)
            candidate_id = f"{connection_id}__{history_id}"
            inventories[candidate_id] = {
                "candidate_id": candidate_id,
                "connection_candidate": connection_id,
                "history_candidate": history_id,
                "allowed_histories": sorted(allowed_tables),
                "allowed_history_tables": allowed_tables,
                "derived_distinction_count": len(pairs),
                "surviving_distinctions": surviving,
                "excluded_distinctions": excluded,
                "surviving_distinction_count": len(surviving),
            }
    return inventories


def _inventory_receipt(row: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "all_derived_distinctions_classified": (
            row["derived_distinction_count"]
            == len(row["surviving_distinctions"]) + len(row["excluded_distinctions"])
        ),
        "survivors_have_distinct_outputs_for_every_allowed_history": all(
            all(
                apply_table(table, tuple(distinction["left_state"]))
                != apply_table(table, tuple(distinction["right_state"]))
                for table in row["allowed_history_tables"].values()
            )
            for distinction in row["surviving_distinctions"]
        ),
        "exclusions_have_concrete_counterexample": all(
            distinction["counterexample"]["left_output"]
            == distinction["counterexample"]["right_output"]
            for distinction in row["excluded_distinctions"]
        ),
        "inventory_nonempty": bool(row["surviving_distinctions"]),
    }
    receipt = {
        **row,
        "checks": checks,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    receipt["receipt_digest"] = digest(receipt)
    return receipt


def run(source: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    raw = compute_inventories(source, prior)
    receipts = [_inventory_receipt(raw[name]) for name in sorted(raw)]
    inventories = {receipt["candidate_id"]: receipt for receipt in receipts}
    current_frontier = sorted(
        f"{connection_id}__{history_id}"
        for connection_id in prior["connection_frontier"]
        for history_id in prior["frontier"]
    )
    frontier_sets = [
        {row["distinction_id"] for row in inventories[candidate]["surviving_distinctions"]}
        for candidate in current_frontier
    ]
    shared_inventory = sorted(set.intersection(*frontier_sets)) if frontier_sets else []
    states = current_outer_states(source)
    checks = {
        "source_schema_v8": source.get("schema") == "ratchet.v8.source-packets.v1",
        "prior_history_schema": prior.get("schema") == "ratchet.pack183.deep-history-layer.v1",
        "prior_connection_frontier_exact": prior.get("connection_frontier") == ["parity_sign_transport"],
        "current_outer_state_count_six": len(states) == 6,
        "candidate_manifold_cross_product_exact": len(inventories) == 9,
        "every_candidate_has_full_inventory": all(row["derived_distinction_count"] == 15 for row in inventories.values()),
        "every_allowed_history_covered": all(
            set(row["allowed_histories"]) == set(row["allowed_history_tables"])
            for row in inventories.values()
        ),
        "current_frontier_exact": set(current_frontier) == {
            "parity_sign_transport__sequence_histories",
            "parity_sign_transport__branching_tree_histories",
        },
        "current_frontier_shared_inventory_eleven": len(shared_inventory) == 11,
        "proposal_receipts_pass": all(receipt["all_pass"] for receipt in receipts),
    }
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "prior_history_digest": prior["result_digest"],
        "connection_candidates": list(prior["connection_candidates"]),
        "history_candidates": list(HISTORY_CANDIDATES),
        "history_structures": {
            candidate: prior["history_evaluations"][candidate]["history_structure"]
            for candidate in HISTORY_CANDIDATES
        },
        "current_outer_states": [list(state) for state in states],
        "candidate_manifold_count": len(inventories),
        "inventories": inventories,
        "current_frontier": current_frontier,
        "current_frontier_surviving_distinctions": shared_inventory,
        "purgatory": [],
        "receipts": receipts,
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all(checks.values()),
    }
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    prior = json.loads(args.prior.read_text(encoding="utf-8"))
    result = run(source, prior)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_manifold_count": result["candidate_manifold_count"],
        "current_frontier": result["current_frontier"],
        "shared_surviving_distinctions": len(result["current_frontier_surviving_distinctions"]),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
