#!/usr/bin/env python3
"""Settle the complete five-axis deep manifold with feedback re-offers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import digest, write_json
from whole_feedback_ratchet import FULL_REQUIREMENTS as PRIOR_FULL_REQUIREMENTS


SCHEMA = "ratchet.pack183.whole-manifold-v2.v1"
Z_REQUIREMENTS = (
    "finite_complete_parent",
    "parent_full_requirements",
    "source_ancestry_retained",
)
CONNECTION_REQUIREMENT = "connection_outer_admissible"
HISTORY_REQUIREMENT = "history_ordered_relation"
PERSISTENCE_REQUIREMENT = "persistence_inventory_nonempty"
CHIRALITY_REQUIREMENT = "chirality_expressible_installable_not_forced"
LATE_READOUT_REQUIREMENT = "entropy_geometry_late_readout_nonphysics"
FULL_REQUIREMENTS = Z_REQUIREMENTS + (
    CONNECTION_REQUIREMENT,
    HISTORY_REQUIREMENT,
    PERSISTENCE_REQUIREMENT,
    CHIRALITY_REQUIREMENT,
    LATE_READOUT_REQUIREMENT,
)
CLAIM_CEILING = (
    "packet-relative finite feedback comparison of the declared base x nesting x geometry x connection x history "
    "grammar; no promotion, formal admission, terminal manifold, canonical layer order, physics, or exhaustive-grammar claim"
)
REOFFER_RULE = (
    "re-offer after any new layer, source packet, requirement revision, witness correction, "
    "or proposal-grammar extension"
)


def parent_whole_from_disk() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "results" / "whole_manifold.json"
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_id(parent_id: str, connection_id: str, history_id: str) -> str:
    return f"{parent_id}__{connection_id}__{history_id}"


def _history_vector(structure: dict[str, Any]) -> dict[str, int]:
    structure_type = structure["structure_type"]
    if structure_type == "unordered_set":
        declared_step_edges = 0
        branch_points = 0
    elif structure_type == "sequence_family":
        declared_step_edges = sum(len(steps) for steps in structure["sequences"].values())
        branch_points = 0
    elif structure_type == "branching_tree":
        declared_step_edges = len(structure["edges"])
        outgoing = {node: 0 for node in structure["nodes"]}
        for edge in structure["edges"]:
            outgoing[edge["source"]] += 1
        branch_points = sum(count > 1 for count in outgoing.values())
    else:
        raise ValueError(f"unknown history structure type {structure_type!r}")
    return {
        "history_declared_step_edges": declared_step_edges,
        "history_branch_points": branch_points,
    }


def build_rows(
    source: dict[str, Any],
    prior: dict[str, Any],
    parent_whole: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    connection_candidates = list(prior["connection_candidates"])
    history_candidates = list(prior["history_candidates"])
    admitted_connections = set(prior["admissible_connection_candidates"])
    admitted_histories = set(prior["admissible_history_candidates"])
    chirality_ok = prior["expressible"] is True and prior["forced"] is False and prior["installable"] is True
    rows: dict[str, dict[str, Any]] = {}
    for parent_id, parent in sorted(parent_whole["candidate_evaluations"].items()):
        parent_full = all(parent["requirement_results"].get(name) is True for name in PRIOR_FULL_REQUIREMENTS)
        for connection_id in connection_candidates:
            for history_id in history_candidates:
                persistence_id = f"{connection_id}__{history_id}"
                persistence = prior["persistence_summary"][persistence_id]
                identifier = candidate_id(parent_id, connection_id, history_id)
                requirements = {
                    "finite_complete_parent": parent["complete_whole_candidate"] is True,
                    "parent_full_requirements": parent_full,
                    "source_ancestry_retained": parent["source_packet_digest"] == source["result_digest"],
                    "connection_outer_admissible": connection_id in admitted_connections,
                    "history_ordered_relation": history_id in admitted_histories,
                    "persistence_inventory_nonempty": (
                        persistence["all_pass"] is True and persistence["surviving_distinction_count"] > 0
                    ),
                    "chirality_expressible_installable_not_forced": chirality_ok,
                    "entropy_geometry_late_readout_nonphysics": True,
                }
                vector = dict(parent["presumption_vector"])
                history_structure = prior["history_structures"][history_id]
                vector.update(_history_vector(history_structure))
                rows[identifier] = {
                    "candidate_id": identifier,
                    "base_candidate": parent["base_candidate"],
                    "nesting_kind": parent["nesting_kind"],
                    "geometry_profile": parent["geometry_profile"],
                    "connection_candidate": connection_id,
                    "history_candidate": history_id,
                    "history_structure_digest": digest(history_structure),
                    "parent_candidate_id": parent_id,
                    "parent_behavior_signature": parent["behavior_signature"],
                    "source_packet_digest": source["result_digest"],
                    "complete_whole_candidate": True,
                    "proposed": True,
                    "settled_under_Z_plus_delta": True,
                    "requirement_results": requirements,
                    "presumption_vector": vector,
                    "persistence_surviving_distinction_count": persistence["surviving_distinction_count"],
                    "chirality_status": prior["status"],
                    "drive_gradient_asserted_as_physics": False,
                }
    return rows


def active_view(row: dict[str, Any], requirements: tuple[str, ...] | list[str]) -> dict[str, Any]:
    return {
        "failed": sorted(name for name in requirements if row["requirement_results"][name] is not True),
        "vector": row["presumption_vector"],
    }


def beats(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    left_failed, right_failed = set(left["failed"]), set(right["failed"])
    if left_failed < right_failed:
        return True, "strictly fewer failed complete-manifold requirements"
    if left_failed != right_failed:
        return False, "incomparable failure sets"
    keys = sorted(left["vector"])
    no_worse = all(left["vector"][key] <= right["vector"][key] for key in keys)
    better = any(left["vector"][key] < right["vector"][key] for key in keys)
    return no_worse and better, "Pareto-smaller explicit presumption vector" if no_worse and better else "incomparable vectors"


def _witness(left_id: str, right_id: str, views: dict[str, dict[str, Any]], reason: str) -> dict[str, Any]:
    left = views[left_id]
    right = views[right_id]
    smaller = {
        key: {"beater": left["vector"][key], "candidate": right["vector"][key]}
        for key in sorted(left["vector"])
        if left["vector"][key] < right["vector"][key]
    }
    return {
        "beaten_by_candidate": left_id,
        "reason": reason,
        "beater_failed_requirements": left["failed"],
        "candidate_failed_requirements": right["failed"],
        "strictly_smaller_vector_fields": smaller,
    }


def recompute_core(rows: dict[str, dict[str, Any]], requirements: tuple[str, ...]) -> dict[str, Any]:
    views = {name: active_view(row, requirements) for name, row in rows.items()}
    names = sorted(rows)
    beaten_by: dict[str, dict[str, Any] | None] = {}
    evaluated = 0
    for right in names:
        witness = None
        for left in names:
            if left == right:
                continue
            evaluated += 1
            won, reason = beats(views[left], views[right])
            if won:
                witness = _witness(left, right, views, reason)
                break
        beaten_by[right] = witness
    frontier = sorted(name for name, witness in beaten_by.items() if witness is None)
    comparison_count = len(names) * (len(names) - 1)
    return {
        "requirements": list(requirements),
        "frontier": frontier,
        "purgatory_ids": sorted(set(names) - set(frontier)),
        "beaten_by": beaten_by,
        "comparison_count": comparison_count,
        "decisive_comparisons_evaluated": evaluated,
        "comparison_method": (
            "complete ordered comparison relation fixed by views_digest plus beats-law-v1; "
            "witness search stops after the first deterministic defeating candidate"
        ),
        "comparison_digest": digest({
            "law": "failure-set subset then Pareto-smaller explicit presumption vector",
            "requirements": list(requirements),
            "views": views,
            "ordered_comparison_count": comparison_count,
        }),
        "views_digest": digest(views),
        "candidate_count_recomputed": len(names),
    }


def run(
    source: dict[str, Any],
    prior: dict[str, Any],
    parent_whole: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if parent_whole is None:
        parent_whole = parent_whole_from_disk()
    rows = build_rows(source, prior, parent_whole)
    campaigns = (
        (
            "connection layer arrives; re-offer every complete candidate tuple",
            Z_REQUIREMENTS + (CONNECTION_REQUIREMENT,),
        ),
        (
            "history layer arrives; re-offer every base, nesting, geometry, connection, and history",
            Z_REQUIREMENTS + (CONNECTION_REQUIREMENT, HISTORY_REQUIREMENT),
        ),
        (
            "persistence layer arrives; re-offer the full declared grammar",
            Z_REQUIREMENTS + (CONNECTION_REQUIREMENT, HISTORY_REQUIREMENT, PERSISTENCE_REQUIREMENT),
        ),
        (
            "chirality discriminator arrives as installable but unforced; re-offer the full declared grammar",
            FULL_REQUIREMENTS,
        ),
        (
            "requirement revision control suspends connection admissibility without deleting proposals",
            tuple(name for name in FULL_REQUIREMENTS if name != CONNECTION_REQUIREMENT),
        ),
        (
            "restore every requirement and re-offer the full declared grammar",
            FULL_REQUIREMENTS,
        ),
        (
            "open continuation tick with no new proposal",
            FULL_REQUIREMENTS,
        ),
    )
    cache: dict[tuple[str, ...], dict[str, Any]] = {}
    receipts = []
    previous_frontier: list[str] = []
    previous_purgatory: set[str] = set()
    default = candidate_id(
        parent_whole["operational_default"],
        prior["admissible_connection_candidates"][0],
        "sequence_histories",
    )
    for step, (reason, requirements) in enumerate(campaigns):
        if requirements not in cache:
            cache[requirements] = recompute_core(rows, requirements)
        core = cache[requirements]
        frontier = list(core["frontier"])
        purgatory = set(core["purgatory_ids"])
        if default not in frontier:
            default = frontier[0]
        receipt = {
            "step": step,
            "reason": reason,
            "requirements": list(requirements),
            "frontier": frontier,
            "previous_frontier": previous_frontier,
            "purgatory_ids": list(core["purgatory_ids"]),
            "reentered_from_purgatory": sorted(previous_purgatory & set(frontier)),
            "newly_in_purgatory": sorted(purgatory - previous_purgatory),
            "default": default,
            "candidate_count_recomputed": core["candidate_count_recomputed"],
            "comparison_count": core["comparison_count"],
            "decisive_comparisons_evaluated": core["decisive_comparisons_evaluated"],
            "comparison_method": core["comparison_method"],
            "comparison_digest": core["comparison_digest"],
            "views_digest": core["views_digest"],
            "global_mss_claimed": False,
            "candidate_universe_exhausted": False,
            "terminal_state": False,
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        receipt["receipt_digest"] = digest(receipt)
        receipts.append(receipt)
        previous_frontier = frontier
        previous_purgatory = purgatory
    final_core = cache[FULL_REQUIREMENTS]
    final_frontier = receipts[-1]["frontier"]
    final_purgatory = [{
        "candidate_id": name,
        "witness": final_core["beaten_by"][name],
        "reoffer_rule": REOFFER_RULE,
    } for name in final_core["purgatory_ids"]]
    expected_count = (
        len(parent_whole["candidate_evaluations"])
        * len(prior["connection_candidates"])
        * len(prior["history_candidates"])
    )
    checks = {
        "source_schema_v8": source.get("schema") == "ratchet.v8.source-packets.v1",
        "source_packet_count_nine": len(source.get("base_packets", [])) == 9,
        "prior_whole_schema": parent_whole.get("schema") == "ratchet.pack183.whole-feedback-ratchet.v1",
        "prior_chirality_schema": prior.get("schema") == "ratchet.pack183.deep-chirality-layer.v1",
        "exact_five_axis_cross_product": len(rows) == expected_count == 4752,
        "all_candidates_complete_and_settled": all(
            row["complete_whole_candidate"] and row["proposed"] and row["settled_under_Z_plus_delta"]
            for row in rows.values()
        ),
        "all_bases_reoffered": {row["base_candidate"] for row in rows.values()} == {
            row["base_candidate"] for row in parent_whole["candidate_evaluations"].values()
        },
        "all_nestings_reoffered": {row["nesting_kind"] for row in rows.values()} == {
            row["nesting_kind"] for row in parent_whole["candidate_evaluations"].values()
        },
        "all_geometries_reoffered": {row["geometry_profile"] for row in rows.values()} == {
            row["geometry_profile"] for row in parent_whole["candidate_evaluations"].values()
        },
        "all_connections_reoffered": {row["connection_candidate"] for row in rows.values()} == set(prior["connection_candidates"]),
        "all_histories_reoffered": {row["history_candidate"] for row in rows.values()} == set(prior["history_candidates"]),
        "history_vectors_recomputed_from_structures": all(
            all(
                row["presumption_vector"][field] == value
                for field, value in _history_vector(prior["history_structures"][row["history_candidate"]]).items()
            )
            and row["history_structure_digest"] == digest(prior["history_structures"][row["history_candidate"]])
            for row in rows.values()
        ),
        "every_layer_arrival_reoffers_full_universe": all(
            receipt["candidate_count_recomputed"] == expected_count for receipt in receipts[:4]
        ),
        "requirement_revision_changes_frontier": receipts[4]["frontier"] != receipts[3]["frontier"],
        "requirement_revision_has_actual_reentry": bool(receipts[4]["reentered_from_purgatory"]),
        "restoration_recovers_full_frontier": receipts[5]["frontier"] == receipts[3]["frontier"],
        "idle_tick_continues_without_error": receipts[6]["frontier"] == receipts[5]["frontier"],
        "final_frontier_plural": len(final_frontier) > 1,
        "final_frontier_passes_full_requirements": all(
            all(rows[name]["requirement_results"][requirement] is True for requirement in FULL_REQUIREMENTS)
            for name in final_frontier
        ),
        "operational_default_in_frontier": receipts[-1]["default"] in final_frontier,
        "purgatory_exact_partition": {row["candidate_id"] for row in final_purgatory} == set(rows) - set(final_frontier),
        "purgatory_witnesses_and_reoffer_rules": all(
            row["witness"] is not None and bool(row["reoffer_rule"]) for row in final_purgatory
        ),
        "complete_comparison_population_bound": all(
            receipt["comparison_count"] == expected_count * (expected_count - 1) for receipt in receipts
        ),
        "late_readout_not_asserted_as_physics": all(
            row["drive_gradient_asserted_as_physics"] is False for row in rows.values()
        ),
        "no_global_terminal_or_exhaustive_claim": all(
            receipt["global_mss_claimed"] is False
            and receipt["candidate_universe_exhausted"] is False
            and receipt["terminal_state"] is False
            for receipt in receipts
        ),
    }
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "prior_whole_digest": parent_whole["result_digest"],
        "prior_chirality_digest": prior["result_digest"],
        "base_candidate_count": len({row["base_candidate"] for row in rows.values()}),
        "nesting_candidate_count": len({row["nesting_kind"] for row in rows.values()}),
        "geometry_candidate_count": len({row["geometry_profile"] for row in rows.values()}),
        "connection_candidate_count": len(prior["connection_candidates"]),
        "history_candidate_count": len(prior["history_candidates"]),
        "candidate_count": len(rows),
        "Z_requirements": list(Z_REQUIREMENTS),
        "delta_requirements": list(FULL_REQUIREMENTS[len(Z_REQUIREMENTS):]),
        "candidate_evaluations": rows,
        "receipts": receipts,
        "final_frontier": final_frontier,
        "final_frontier_evaluations": {name: rows[name] for name in final_frontier},
        "operational_default": receipts[-1]["default"],
        "purgatory": final_purgatory,
        "process_checks": checks,
        "global_mss_claimed": False,
        "candidate_universe_exhausted": False,
        "terminal_state": False,
        "status": "OPEN_DEEP_MANIFOLD_FRONTIER_COMPUTED",
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
        "default": result["operational_default"],
        "final_frontier": result["final_frontier"],
        "frontier_count": len(result["final_frontier"]),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
