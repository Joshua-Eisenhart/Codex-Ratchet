#!/usr/bin/env python3
"""Settle unordered, sequential, and branching finite relation histories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import digest, write_json
from connection_layer import CANDIDATES as CONNECTION_CANDIDATES, parse_state, state_key


SCHEMA = "ratchet.pack183.deep-history-layer.v1"
CANDIDATES = ("unordered_set_baseline", "sequence_histories", "branching_tree_histories")
DEFAULT = "sequence_histories"
CLAIM_CEILING = (
    "packet-relative finite ordered-history and explicit noncommutation witness only; "
    "no promotion, formal admission, canonical history, causation, or exhaustive-history claim"
)
REOFFER_RULE = (
    "re-offer after any transport table, allowed state, ordering requirement, "
    "or later-layer persistence condition changes"
)


def apply_table(table: dict[str, list[int]], state: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(int(bit) for bit in table[state_key(state)])  # type: ignore[return-value]


def compose_tables(
    first: dict[str, list[int]],
    second: dict[str, list[int]],
) -> dict[str, list[int]]:
    """Return second(first(state)); names remain explicit at the call site."""
    return {
        key: list(apply_table(second, tuple(first[key])))
        for key in sorted(first)
    }


def history_tables(connection: dict[str, Any]) -> dict[str, dict[str, list[int]]]:
    transports = {
        candidate: connection["transport_evaluations"][candidate]["transport_table"]
        for candidate in CONNECTION_CANDIDATES
    }
    parity = transports["parity_sign_transport"]
    qca = transports["qca_permutation_transport"]
    identity = transports["identity_transport"]
    parity_then_qca = compose_tables(parity, qca)
    qca_then_parity = compose_tables(qca, parity)
    return {
        "identity": identity,
        "parity_sign": parity,
        "qca_permutation": qca,
        "parity_then_qca": parity_then_qca,
        "qca_then_parity": qca_then_parity,
    }


def computed_order_witness(tables: dict[str, dict[str, list[int]]]) -> dict[str, Any] | None:
    preferred = "010"
    ordered_keys = [preferred] + [key for key in sorted(tables["parity_sign"]) if key != preferred]
    for key in ordered_keys:
        left = tables["parity_then_qca"][key]
        right = tables["qca_then_parity"][key]
        if left != right:
            return {
                "input_state": list(parse_state(key)),
                "T1": "parity_sign_transport",
                "T2": "qca_permutation_transport",
                "T2_after_T1": list(left),
                "T1_after_T2": list(right),
                "distinguishes_order": True,
            }
    return None


def branching_tree_recomputes(
    structure: dict[str, Any],
    tables: dict[str, dict[str, list[int]]],
) -> bool:
    root = structure.get("root")
    nodes = structure.get("nodes", [])
    edges = structure.get("edges", [])
    history_at_node = structure.get("history_at_node", {})
    parent_edge = {edge.get("target"): edge for edge in edges}
    outgoing = {node: 0 for node in nodes}
    for edge in edges:
        if edge.get("source") not in outgoing:
            return False
        outgoing[edge["source"]] += 1
    if set(structure.get("leaves", [])) != {node for node, count in outgoing.items() if count == 0}:
        return False
    restriction_tables = {
        "parity_sign_transport": tables["parity_sign"],
        "qca_permutation_transport": tables["qca_permutation"],
    }
    if set(history_at_node) != set(nodes) or history_at_node.get(root) != "identity":
        return False
    for node in nodes:
        restrictions = []
        cursor = node
        seen = set()
        while cursor != root:
            if cursor in seen or cursor not in parent_edge:
                return False
            seen.add(cursor)
            edge = parent_edge[cursor]
            restrictions.append(edge.get("restriction"))
            cursor = edge.get("source")
        composed = tables["identity"]
        for restriction in reversed(restrictions):
            if restriction not in restriction_tables:
                return False
            composed = compose_tables(composed, restriction_tables[restriction])
        if composed != tables.get(history_at_node[node]):
            return False
    return True


def _candidate_receipt(
    candidate: str,
    tables: dict[str, dict[str, list[int]]],
    witness: dict[str, Any] | None,
) -> dict[str, Any]:
    ordered = candidate != "unordered_set_baseline"
    branching = candidate == "branching_tree_histories"
    allowed = {
        "unordered_set_baseline": ["parity_sign", "qca_permutation"],
        "sequence_histories": [
            "identity", "parity_sign", "qca_permutation", "parity_then_qca", "qca_then_parity"
        ],
        "branching_tree_histories": [
            "identity", "parity_sign", "qca_permutation", "parity_then_qca", "qca_then_parity"
        ],
    }[candidate]
    history_structure = {
        "unordered_set_baseline": {
            "structure_type": "unordered_set",
            "members": ["parity_sign_transport", "qca_permutation_transport"],
        },
        "sequence_histories": {
            "structure_type": "sequence_family",
            "sequences": {
                "identity": [],
                "parity_sign": ["parity_sign_transport"],
                "qca_permutation": ["qca_permutation_transport"],
                "parity_then_qca": ["parity_sign_transport", "qca_permutation_transport"],
                "qca_then_parity": ["qca_permutation_transport", "parity_sign_transport"],
            },
        },
        "branching_tree_histories": {
            "structure_type": "branching_tree",
            "root": "root",
            "nodes": ["root", "after_parity", "after_qca", "after_parity_qca", "after_qca_parity"],
            "edges": [
                {"source": "root", "target": "after_parity", "restriction": "parity_sign_transport"},
                {"source": "root", "target": "after_qca", "restriction": "qca_permutation_transport"},
                {"source": "after_parity", "target": "after_parity_qca", "restriction": "qca_permutation_transport"},
                {"source": "after_qca", "target": "after_qca_parity", "restriction": "parity_sign_transport"},
            ],
            "leaves": ["after_parity_qca", "after_qca_parity"],
            "history_at_node": {
                "root": "identity",
                "after_parity": "parity_sign",
                "after_qca": "qca_permutation",
                "after_parity_qca": "parity_then_qca",
                "after_qca_parity": "qca_then_parity",
            },
        },
    }[candidate]
    noncommutation_earned = ordered and witness is not None
    checks = {
        "history_maps_finite_total": all(len(tables[name]) == 8 for name in allowed),
        "order_status_explicit": ordered == (candidate != "unordered_set_baseline"),
        "noncommutation_has_witness_or_explicit_negative": (
            noncommutation_earned and witness is not None and witness["distinguishes_order"] is True
        ) or (
            not noncommutation_earned and candidate == "unordered_set_baseline"
        ),
        "branching_status_exact": branching == (candidate == "branching_tree_histories"),
        "history_structure_typed": history_structure["structure_type"] == {
            "unordered_set_baseline": "unordered_set",
            "sequence_histories": "sequence_family",
            "branching_tree_histories": "branching_tree",
        }[candidate],
        "branching_tree_has_two_ordered_branches": (not branching) or (
            len(history_structure["nodes"]) == 5
            and len(history_structure["edges"]) == 4
            and {edge["target"] for edge in history_structure["edges"]}
            == set(history_structure["nodes"]) - {history_structure["root"]}
            and set(history_structure["leaves"]) == {"after_parity_qca", "after_qca_parity"}
            and set(history_structure["history_at_node"].values())
            == {"identity", "parity_sign", "qca_permutation", "parity_then_qca", "qca_then_parity"}
            and branching_tree_recomputes(history_structure, tables)
        ),
    }
    receipt = {
        "candidate_id": candidate,
        "ordered_relation_chain": ordered,
        "branching": branching,
        "admissible": ordered,
        "allowed_histories": allowed,
        "history_structure": history_structure,
        "history_tables": {name: tables[name] for name in allowed},
        "noncommutation_earned": noncommutation_earned,
        "noncommutation_witness": witness if noncommutation_earned else None,
        "noncommutation_negative": (
            None if noncommutation_earned else
            "unordered set baseline carries no composition order and therefore earns no noncommutation claim"
        ),
        "checks": checks,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    receipt["receipt_digest"] = digest(receipt)
    return receipt


def run(source: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    tables = history_tables(prior)
    witness = computed_order_witness(tables)
    receipts = [_candidate_receipt(candidate, tables, witness) for candidate in CANDIDATES]
    evaluations = {receipt["candidate_id"]: receipt for receipt in receipts}
    frontier = sorted(candidate for candidate, row in evaluations.items() if row["admissible"])
    purgatory = [{
        "candidate_id": "unordered_set_baseline",
        "witness": {
            "failed_requirement": "ordered relation chain R2",
            "unordered_members": ["parity_sign_transport", "qca_permutation_transport"],
            "computed_order_witness": witness,
        },
        "reoffer_rule": REOFFER_RULE,
    }]
    checks = {
        "source_schema_v8": source.get("schema") == "ratchet.v8.source-packets.v1",
        "prior_connection_schema": prior.get("schema") == "ratchet.pack183.deep-connection-layer.v1",
        "candidate_grammar_exact": tuple(evaluations) == CANDIDATES,
        "both_composition_orders_computed": (
            tables["parity_then_qca"] == compose_tables(tables["parity_sign"], tables["qca_permutation"])
            and tables["qca_then_parity"] == compose_tables(tables["qca_permutation"], tables["parity_sign"])
        ),
        "noncommutation_iff_concrete_witness": (witness is not None) == any(
            tables["parity_then_qca"][key] != tables["qca_then_parity"][key]
            for key in tables["parity_sign"]
        ),
        "order_witness_recomputes": witness is not None and (
            witness["T2_after_T1"]
            == tables["parity_then_qca"][state_key(tuple(witness["input_state"]))]
            and witness["T1_after_T2"]
            == tables["qca_then_parity"][state_key(tuple(witness["input_state"]))]
            and witness["T2_after_T1"] != witness["T1_after_T2"]
        ),
        "ordered_frontier_plural": set(frontier) == {"sequence_histories", "branching_tree_histories"},
        "default_in_frontier": DEFAULT in frontier,
        "proposal_receipts_pass": all(receipt["all_pass"] for receipt in receipts),
        "purgatory_has_witness_and_reoffer": all(row["witness"] and row["reoffer_rule"] for row in purgatory),
    }
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "prior_connection_digest": prior["result_digest"],
        "connection_candidates": list(CONNECTION_CANDIDATES),
        "connection_frontier": list(prior["frontier"]),
        "connection_default": prior["operational_default"],
        "transport_tables": {
            candidate: prior["transport_evaluations"][candidate]["transport_table"]
            for candidate in CONNECTION_CANDIDATES
        },
        "candidate_count": len(CANDIDATES),
        "candidates": list(CANDIDATES),
        "history_evaluations": evaluations,
        "noncommutation_earned": witness is not None,
        "noncommutation_witness": witness,
        "noncommutation_negative": None if witness is not None else "both finite orders agree on every tested state",
        "frontier": frontier,
        "operational_default": DEFAULT,
        "purgatory": purgatory,
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
        "candidate_count": result["candidate_count"],
        "frontier": result["frontier"],
        "noncommutation_earned": result["noncommutation_earned"],
        "witness": result["noncommutation_witness"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
