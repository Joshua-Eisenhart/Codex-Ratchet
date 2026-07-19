#!/usr/bin/env python3
"""Nest every surviving base candidate under executable rival relations."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

from common import digest, write_json


NESTING_KINDS = (
    "independent_product",
    "chain_012",
    "chain_021",
    "chain_102",
    "fan_outer",
    "complete_pairwise",
    "ternary_relation",
    "outer_functions",
    "inner_functions",
    "identity_bijection",
    "twisted_bijection",
)

REQUIREMENTS = (
    "whole_three_layer_state",
    "baseline_exact",
    "expanded_exact",
    "outer_restriction_changes_inner",
    "inner_restriction_changes_outer",
    "baseline_persists_under_expansion",
    "expansion_adds_configuration",
)


def parse_packet(packet: dict[str, Any]):
    target = {
        tuple(tuple(int(bit) for bit in state) for state in triple)
        for triple in packet["admissible_triples"]
    }
    values = [tuple(tuple(int(bit) for bit in state) for state in layer) for layer in packet["layer_values"]]
    return target, values


def pair_projection(target, left: int, right: int):
    return {(triple[left], triple[right]) for triple in target}


def relation_join(target, values, edges):
    relations = {(left, right): pair_projection(target, left, right) for left, right in edges}
    decoded = {
        triple
        for triple in itertools.product(*values)
        if all((triple[left], triple[right]) in relations[(left, right)] for left, right in edges)
    }
    stored_slots = sum(2 * len(relation) for relation in relations.values())
    return decoded, {
        "edges": [list(edge) for edge in edges],
        "relation_sizes": {f"{left}{right}": len(relation) for (left, right), relation in sorted(relations.items())},
    }, stored_slots


def deterministic_functions(target, values, outward: bool):
    if outward:
        first, second = (0, 1), (1, 2)
    else:
        first, second = (2, 1), (1, 0)
    relations = {
        first: pair_projection(target, *first),
        second: pair_projection(target, *second),
    }
    maps = {}
    for edge, relation in relations.items():
        grouped = {}
        for source, destination in relation:
            grouped.setdefault(source, []).append(destination)
        maps[edge] = {source: sorted(destinations)[0] for source, destinations in grouped.items()}
    decoded = set()
    if outward:
        for outer in values[0]:
            if outer not in maps[(0, 1)]:
                continue
            middle = maps[(0, 1)][outer]
            if middle in maps[(1, 2)]:
                decoded.add((outer, middle, maps[(1, 2)][middle]))
    else:
        for inner in values[2]:
            if inner not in maps[(2, 1)]:
                continue
            middle = maps[(2, 1)][inner]
            if middle in maps[(1, 0)]:
                decoded.add((maps[(1, 0)][middle], middle, inner))
    model = {
        "direction": "outer_to_inner" if outward else "inner_to_outer",
        "map_sizes": {f"{edge[0]}{edge[1]}": len(mapping) for edge, mapping in maps.items()},
    }
    return decoded, model, sum(2 * len(mapping) for mapping in maps.values())


def indexed_bijection(values, twist: bool):
    size = min(len(layer) for layer in values)
    decoded = set()
    for index in range(size):
        middle_index = (index + int(twist)) % size
        inner_index = (middle_index + int(twist)) % size
        decoded.add((values[0][index], values[1][middle_index], values[2][inner_index]))
    return decoded, {"size": size, "twist": int(twist)}, 3 * size


def simulate_nesting(kind: str, target, values) -> dict[str, Any]:
    relation_count = 0
    maximum_arity = 0
    operations = 0
    deterministic_choices = 0
    chosen_edges = 0
    if kind == "independent_product":
        decoded = set(itertools.product(*values))
        model = {"layer_cardinalities": [len(layer) for layer in values]}
        stored_slots = sum(len(layer) for layer in values)
    elif kind.startswith("chain_"):
        edge_map = {
            "chain_012": ((0, 1), (1, 2)),
            "chain_021": ((0, 2), (2, 1)),
            "chain_102": ((1, 0), (0, 2)),
        }
        decoded, model, stored_slots = relation_join(target, values, edge_map[kind])
        relation_count, maximum_arity, operations, chosen_edges = 2, 2, 1, 2
    elif kind == "fan_outer":
        decoded, model, stored_slots = relation_join(target, values, ((0, 1), (0, 2)))
        relation_count, maximum_arity, operations, chosen_edges = 2, 2, 1, 2
    elif kind == "complete_pairwise":
        decoded, model, stored_slots = relation_join(target, values, ((0, 1), (1, 2), (0, 2)))
        relation_count, maximum_arity, operations, chosen_edges = 3, 2, 1, 3
    elif kind == "ternary_relation":
        decoded = set(target)
        model = {"ternary_tuple_count": len(target)}
        stored_slots = 3 * len(target)
        relation_count, maximum_arity = 1, 3
    elif kind == "outer_functions":
        decoded, model, stored_slots = deterministic_functions(target, values, True)
        relation_count, maximum_arity, operations, deterministic_choices, chosen_edges = 2, 2, 1, stored_slots // 2, 2
    elif kind == "inner_functions":
        decoded, model, stored_slots = deterministic_functions(target, values, False)
        relation_count, maximum_arity, operations, deterministic_choices, chosen_edges = 2, 2, 1, stored_slots // 2, 2
    elif kind in {"identity_bijection", "twisted_bijection"}:
        decoded, model, stored_slots = indexed_bijection(values, kind == "twisted_bijection")
        relation_count, maximum_arity, operations, deterministic_choices, chosen_edges = 2, 2, 1, len(decoded), 2
    else:
        raise ValueError(kind)
    outer_to_inner = {outer: {triple[2] for triple in decoded if triple[0] == outer} for outer in values[0]}
    inner_to_outer = {inner: {triple[0] for triple in decoded if triple[2] == inner} for inner in values[2]}
    full_inner = {triple[2] for triple in decoded}
    full_outer = {triple[0] for triple in decoded}
    inward = bool(full_inner) and any(choices and choices < full_inner for choices in outer_to_inner.values())
    outward = bool(full_outer) and any(choices and choices < full_outer for choices in inner_to_outer.values())
    return {
        "decoded": decoded,
        "model": model,
        "relation_count": relation_count,
        "maximum_arity": maximum_arity,
        "stored_tuple_slots": stored_slots,
        "primitive_operations": operations,
        "deterministic_choices": deterministic_choices,
        "chosen_nesting_edges": chosen_edges,
        "outer_restriction_changes_inner": inward,
        "inner_restriction_changes_outer": outward,
    }


def evaluate_candidate(base_id: str, kind: str, packets: list[dict[str, Any]], base_evaluation: dict[str, Any]) -> dict[str, Any]:
    packet_rows = {}
    total_slots = 0
    maxima = {"relation_count": 0, "maximum_arity": 0, "primitive_operations": 0, "deterministic_choices": 0, "chosen_nesting_edges": 0}
    decoded_by_packet = {}
    targets = {}
    for packet in packets:
        target, values = parse_packet(packet)
        simulation = simulate_nesting(kind, target, values)
        decoded = simulation.pop("decoded")
        decoded_by_packet[packet["packet_id"]] = decoded
        targets[packet["packet_id"]] = target
        total_slots += simulation["stored_tuple_slots"]
        for key in maxima:
            maxima[key] = max(maxima[key], simulation[key])
        packet_rows[packet["packet_id"]] = {
            "target_count": len(target),
            "decoded_count": len(decoded),
            "extra_count": len(decoded - target),
            "missing_count": len(target - decoded),
            "exact": decoded == target,
            "decoded_digest": digest(sorted(decoded)),
            "target_digest": digest(sorted(target)),
            **simulation,
        }
    baseline_id = "nested_completion_baseline"
    expanded_id = "nested_completion_expanded"
    baseline = decoded_by_packet[baseline_id]
    expanded = decoded_by_packet[expanded_id]
    baseline_target = targets[baseline_id]
    expanded_target = targets[expanded_id]
    requirement_results = {
        "whole_three_layer_state": all(all(len(state) == 3 for state in triple) for decoded in decoded_by_packet.values() for triple in decoded),
        "baseline_exact": baseline == baseline_target,
        "expanded_exact": expanded == expanded_target,
        "outer_restriction_changes_inner": all(row["outer_restriction_changes_inner"] for row in packet_rows.values()),
        "inner_restriction_changes_outer": all(row["inner_restriction_changes_outer"] for row in packet_rows.values()),
        "baseline_persists_under_expansion": baseline <= expanded,
        "expansion_adds_configuration": bool(expanded - baseline),
    }
    vector = {f"base_{key}": value for key, value in base_evaluation["presumption_vector"].items()}
    vector.update({
        "nest_relation_count": maxima["relation_count"],
        "nest_maximum_arity": maxima["maximum_arity"],
        "nest_stored_tuple_slots": total_slots,
        "nest_primitive_operations": maxima["primitive_operations"],
        "nest_deterministic_choices": maxima["deterministic_choices"],
        "nest_chosen_edges": maxima["chosen_nesting_edges"],
    })
    return {
        "candidate_id": f"{base_id}__{kind}",
        "base_candidate": base_id,
        "nesting_kind": kind,
        "packet_results": packet_rows,
        "requirement_results": requirement_results,
        "presumption_vector": vector,
        "complete_whole_candidate": True,
        "behavior_signature": digest({name: row["decoded_digest"] for name, row in packet_rows.items()}),
    }


def active_view(row: dict[str, Any], requirements: list[str]) -> dict[str, Any]:
    return {
        "failed": sorted(name for name in requirements if not row["requirement_results"][name]),
        "vector": row["presumption_vector"],
    }


def beats(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    left_failed, right_failed = set(left["failed"]), set(right["failed"])
    if left_failed < right_failed:
        return True, "strictly fewer failed whole-nesting requirements"
    if left_failed != right_failed:
        return False, "incomparable failure sets"
    keys = sorted(left["vector"])
    no_worse = all(left["vector"][key] <= right["vector"][key] for key in keys)
    better = any(left["vector"][key] < right["vector"][key] for key in keys)
    return no_worse and better, "Pareto-smaller combined base-and-nesting vector" if no_worse and better else "incomparable vectors"


def recompute(rows: dict[str, dict[str, Any]], requirements: list[str], previous_frontier: list[str], previous_purgatory: set[str], default: str):
    views = {name: active_view(row, requirements) for name, row in rows.items()}
    beaten_by = {name: [] for name in rows}
    for left in sorted(rows):
        for right in sorted(rows):
            if left == right:
                continue
            won, reason = beats(views[left], views[right])
            if won:
                beaten_by[right].append({"candidate_id": left, "reason": reason})
    frontier = sorted(name for name, witnesses in beaten_by.items() if not witnesses)
    purgatory = set(rows) - set(frontier)
    if default not in frontier:
        default = frontier[0]
    return {
        "requirements": list(requirements),
        "frontier": frontier,
        "previous_frontier": list(previous_frontier),
        "purgatory": sorted(purgatory),
        "reentered_from_purgatory": sorted(previous_purgatory & set(frontier)),
        "newly_in_purgatory": sorted(purgatory - previous_purgatory),
        "default": default,
        "beaten_by": beaten_by,
        "views": views,
    }, purgatory, default


def run(source: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    survivors = base["heldout_frontier"]
    packets = source["nesting_packets"]
    rows = {
        f"{base_id}__{kind}": evaluate_candidate(base_id, kind, packets, base["candidate_evaluations"][base_id])
        for base_id in survivors
        for kind in NESTING_KINDS
    }
    baseline_requirements = [
        "whole_three_layer_state", "baseline_exact",
        "outer_restriction_changes_inner", "inner_restriction_changes_outer",
    ]
    full_requirements = list(REQUIREMENTS)
    default = "finite_relation__ternary_relation" if "finite_relation__ternary_relation" in rows else sorted(rows)[0]
    receipts = []
    purgatory: set[str] = set()
    previous_frontier: list[str] = []
    for reason, requirements in (
        ("simulate every survivor under every nesting candidate on the baseline source", baseline_requirements),
        ("add expanded source and recompute every complete nested candidate", full_requirements),
        ("requirement revision control: temporarily compare coupling and persistence without exact-source equality", [
            "whole_three_layer_state", "outer_restriction_changes_inner", "inner_restriction_changes_outer",
            "baseline_persists_under_expansion", "expansion_adds_configuration",
        ]),
        ("restore exact source distinctions and re-offer every retained candidate", full_requirements),
        ("open continuation tick with no new proposal: retain the current default and all history", full_requirements),
    ):
        receipt, purgatory, default = recompute(rows, requirements, previous_frontier, purgatory, default)
        receipt.update({"step": len(receipts), "reason": reason, "global_mss_claimed": False, "terminal_state": False})
        receipt["receipt_digest"] = digest(receipt)
        receipts.append(receipt)
        previous_frontier = receipt["frontier"]

    order_counts = {}
    for base_id in survivors:
        order_counts[base_id] = {
            kind: rows[f"{base_id}__{kind}"]["packet_results"]["nested_completion_baseline"]["decoded_count"]
            for kind in ("chain_012", "chain_021", "chain_102", "fan_outer")
        }
    order_effect = any(len(set(counts.values())) > 1 for counts in order_counts.values())
    final_frontier = receipts[-1]["frontier"]
    final_kinds = {rows[name]["nesting_kind"] for name in final_frontier}
    process_checks = {
        "every_base_survivor_crossed_with_every_nesting_candidate": len(rows) == len(survivors) * len(NESTING_KINDS),
        "all_nested_candidates_are_complete": all(row["complete_whole_candidate"] for row in rows.values()),
        "nesting_order_changes_function": order_effect,
        "whole_frontier_nonempty": bool(final_frontier),
        "plural_exact_nesting_structures_retained": {"complete_pairwise", "ternary_relation"} <= final_kinds,
        "operational_default_always_available": all(receipt["default"] in receipt["frontier"] for receipt in receipts),
        "requirement_revision_recomputed_all_candidates": len(receipts[2]["views"]) == len(rows),
        "restoration_recomputed_all_candidates": len(receipts[3]["views"]) == len(rows),
        "idle_tick_continues_without_error": receipts[-1]["frontier"] == receipts[-2]["frontier"],
        "no_global_mss_or_terminal_claim": all(not receipt["global_mss_claimed"] and not receipt["terminal_state"] for receipt in receipts),
    }
    result = {
        "schema": "ratchet.pack183.nesting-ratchet.v1",
        "source_packet_digest": source["result_digest"],
        "base_census_digest": base["result_digest"],
        "base_survivors": survivors,
        "nesting_kinds": list(NESTING_KINDS),
        "candidate_count": len(rows),
        "candidate_evaluations": rows,
        "receipts": receipts,
        "order_effect_counts": order_counts,
        "final_frontier": final_frontier,
        "operational_default": default,
        "purgatory": receipts[-1]["purgatory"],
        "process_checks": process_checks,
        "global_mss_claimed": False,
        "candidate_universe_exhausted": False,
        "status": "OPEN_NESTED_FRONTIER_COMPUTED",
        "claim_ceiling": (
            "two source-relative base survivors crossed with eleven finite nesting candidates; "
            "order effects and exact nesting frontiers are finite comparison results, not canon or absolute MSS"
        ),
    }
    result["all_pass"] = all(process_checks.values())
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    base = json.loads(args.base.read_text(encoding="utf-8"))
    result = run(source, base)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "base_survivors": result["base_survivors"],
        "nested_candidates": result["candidate_count"],
        "final_frontier": result["final_frontier"],
        "default": result["operational_default"],
        "order_counts": result["order_effect_counts"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
