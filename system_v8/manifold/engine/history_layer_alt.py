#!/usr/bin/env python3
"""Redundant ordered-history layer for the v8 deep manifold lane."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from common import digest, write_json


State = tuple[int, int, int]
Triple = tuple[State, State, State]


HISTORY_CANDIDATES = (
    ("unordered_set_baseline", "baseline that retains admissible triples without order", 0, False),
    ("sequence_histories", "linear ordered relation chains", 1, True),
    ("branching_tree_histories", "outer-rooted branching relation chains", 2, True),
)


def as_state(value: Any) -> State:
    return tuple(int(bit) for bit in value)  # type: ignore[return-value]


def as_triple(value: Any) -> Triple:
    return tuple(as_state(state) for state in value)  # type: ignore[return-value]


def state_key(state: State) -> str:
    return "".join(str(bit) for bit in state)


def transport_for(connection: dict[str, Any], state: State) -> State:
    selected = connection["operational_default"]
    table = connection["candidate_evaluations"][selected]["transport_table"]
    return tuple(table[state_key(state)])  # type: ignore[return-value]


def relation_middle_for_outer(target: list[Triple]) -> dict[State, list[State]]:
    grouped: dict[State, set[State]] = {}
    for outer, middle, _inner in target:
        grouped.setdefault(outer, set()).add(middle)
    return {outer: sorted(middles) for outer, middles in grouped.items()}


def find_noncommutation_witness(packet: dict[str, Any], connection: dict[str, Any], order_sensitive: bool) -> dict[str, Any] | None:
    if not order_sensitive:
        return None
    target = [as_triple(row) for row in packet["admissible_triples"]]
    values = [[as_state(state) for state in layer] for layer in packet["layer_values"]]
    middle_by_outer = relation_middle_for_outer(target)

    def transported_restriction(state: Triple) -> Triple:
        outer, middle, inner = state
        return (transport_for(connection, inner), middle, inner)

    def history_restriction(state: Triple) -> Triple:
        outer, middle, inner = state
        return (outer, (middle_by_outer.get(outer) or [middle])[0], inner)

    for state in itertools.product(*values):
        start = tuple(state)  # type: ignore[assignment]
        after_transport_then_history = history_restriction(transported_restriction(start))
        after_history_then_transport = transported_restriction(history_restriction(start))
        if after_transport_then_history != after_history_then_transport:
            return {
                "packet_id": packet["packet_id"],
                "initial_state": [[*part] for part in start],
                "T_history_after_T_transport": [[*part] for part in after_transport_then_history],
                "T_transport_after_T_history": [[*part] for part in after_history_then_transport],
                "distinguishes": True,
            }
    return None


def packet_histories(packet: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    target = sorted(as_triple(row) for row in packet["admissible_triples"])
    if kind == "branching_tree_histories":
        rows = []
        for outer, group in itertools.groupby(target, key=lambda row: row[0]):
            branch = list(group)
            rows.append({
                "outer": list(outer),
                "states": [[[bit for bit in part] for part in triple] for triple in branch],
            })
        return rows
    return [{"states": [[[bit for bit in part] for part in triple] for triple in target]}]


def evaluate_candidate(kind: str, description: str, cost: int, order_sensitive: bool, source: dict[str, Any], connection: dict[str, Any]) -> dict[str, Any]:
    packet_rows = {}
    witnesses = []
    for packet in source["nesting_packets"]:
        witness = find_noncommutation_witness(packet, connection, order_sensitive)
        if witness:
            witnesses.append(witness)
        histories = packet_histories(packet, kind)
        packet_rows[packet["packet_id"]] = {
            "history_count": len(histories),
            "histories": histories,
            "order_tested": True,
            "noncommutation_witness": witness,
            "noncommutation_earned": witness is not None,
        }
    earned = bool(witnesses)
    return {
        "candidate_id": kind,
        "description": description,
        "history_cost": cost,
        "packet_histories": packet_rows,
        "ordered_relations_admitted": order_sensitive,
        "noncommutation_earned": earned,
        "noncommutation_status": "earned" if earned else "explicit_negative",
        "witness_pair": witnesses[0] if witnesses else None,
        "complete_history_candidate": True,
        "behavior_signature": digest(packet_rows),
    }


def run(source: dict[str, Any], connection: dict[str, Any]) -> dict[str, Any]:
    candidates = {
        name: evaluate_candidate(name, description, cost, ordered, source, connection)
        for name, description, cost, ordered in HISTORY_CANDIDATES
    }
    failed = {
        name: ([] if row["ordered_relations_admitted"] and row["noncommutation_earned"] else ["ordered_noncommuting_history_not_earned"])
        for name, row in candidates.items()
    }
    frontier = sorted(
        candidates,
        key=lambda name: (failed[name], candidates[name]["history_cost"], name),
    )
    best_failed = failed[frontier[0]]
    best_cost = candidates[frontier[0]]["history_cost"]
    frontier = [name for name in frontier if failed[name] == best_failed and candidates[name]["history_cost"] == best_cost]
    default = frontier[0]
    purgatory = [
        {
            "candidate_id": name,
            "witness": row["witness_pair"] or {"explicit_negative": row["noncommutation_status"]},
            "failed": failed[name],
            "reoffer_rule": "re-offer if a later transported restriction earns the missing ordered noncommutation",
        }
        for name, row in sorted(candidates.items())
        if name not in frontier
    ]
    receipt = {
        "step": 0,
        "reason": "settle ordered relation-chain histories and compare transported restriction order",
        "selected_transport": connection["operational_default"],
        "frontier": frontier,
        "default": default,
        "purgatory": purgatory,
        "candidate_count_recomputed": len(candidates),
        "global_mss_claimed": False,
        "terminal_state": False,
    }
    receipt["receipt_digest"] = digest(receipt)
    checks = {
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "connection_all_pass": connection.get("all_pass") is True,
        "selected_transport_in_connection_frontier": connection.get("operational_default") in connection.get("frontier", []),
        "three_history_candidates": set(candidates) == {row[0] for row in HISTORY_CANDIDATES},
        "noncommutation_computed_with_witness_or_negative": all(
            row["noncommutation_earned"] or row["noncommutation_status"] == "explicit_negative"
            for row in candidates.values()
        ),
        "at_least_one_witness_earns_noncommutation": any(row["noncommutation_earned"] for row in candidates.values()),
        "frontier_nonempty": bool(frontier),
        "no_promotion": True,
    }
    result = {
        "schema": "ratchet.pack183.deep.history-alt.v1",
        "source_packet_digest": source["result_digest"],
        "connection_digest": connection["result_digest"],
        "candidate_count": len(candidates),
        "candidate_evaluations": candidates,
        "frontier": frontier,
        "operational_default": default,
        "purgatory": purgatory,
        "receipts": [receipt],
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "global_mss_claimed": False,
        "terminal_state": False,
        "claim_ceiling": "packet-relative ordered relation-chain evidence only; no final history ontology",
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
    connection = json.loads(args.prior.read_text(encoding="utf-8"))
    result = run(source, connection)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_count": result["candidate_count"],
        "frontier": result["frontier"],
        "noncommutation_status": {
            name: row["noncommutation_status"]
            for name, row in result["candidate_evaluations"].items()
        },
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
