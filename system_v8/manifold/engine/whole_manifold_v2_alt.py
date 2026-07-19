#!/usr/bin/env python3
"""Redundant full feedback tournament with deep connection and history axes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from common import digest, write_json
from nesting_ratchet import NESTING_KINDS
from whole_feedback_ratchet import FULL_REQUIREMENTS, GEOMETRY_PROFILES


DEEP_REQUIREMENTS = (
    "finite_nonempty_whole",
    "base_survives_all_source_packets",
    "baseline_source_exact",
    "expanded_source_exact",
    "outer_restriction_changes_inner",
    "inner_restriction_changes_outer",
    "baseline_persists_under_expansion",
    "expansion_adds_configuration",
    "potential_and_metric_cogenerated",
    "nested_entropy_chain_rule",
    "nested_metric_chain_rule",
    "factor_geometry_uses_same_histories",
    "outer_geometry_changes_inner_geometry",
    "expansion_changes_effective_inner_geometry",
    "renesting_changes_effective_inner_geometry",
    "source_ancestry_retained",
    "connection_transport_admissible",
    "history_candidate_complete",
    "history_noncommutation_status_computed",
    "history_ordered_noncommutation_earned",
    "persistence_inventory_survives",
    "chirality_expressible",
    "chirality_not_forced",
    "chirality_installable_not_forced",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_view(row: dict[str, Any], requirements: list[str]) -> dict[str, Any]:
    return {
        "failed": sorted(name for name in requirements if not row["requirement_results"].get(name)),
        "vector": row["presumption_vector"],
    }


def beats(left: dict[str, Any], right: dict[str, Any]) -> tuple[bool, str]:
    left_failed, right_failed = set(left["failed"]), set(right["failed"])
    if left_failed < right_failed:
        return True, "strictly fewer failed deep requirements"
    if left_failed != right_failed:
        return False, "incomparable failure sets"
    keys = sorted(left["vector"])
    no_worse = all(left["vector"][key] <= right["vector"][key] for key in keys)
    better = any(left["vector"][key] < right["vector"][key] for key in keys)
    return no_worse and better, "Pareto-smaller base/nesting/geometry/connection/history vector" if better and no_worse else "incomparable vectors"


def recompute(rows: dict[str, dict[str, Any]], requirements: list[str], previous_frontier: list[str], previous_purgatory: set[str], default: str):
    views = {name: compare_view(row, requirements) for name, row in rows.items()}
    beaten_by = {name: [] for name in rows}
    comparison_count = 0
    comparison_hasher = hashlib.sha256()
    for left in sorted(rows):
        for right in sorted(rows):
            if left == right:
                continue
            won, reason = beats(views[left], views[right])
            comparison_count += 1
            comparison_hasher.update(f"{left}\0{right}\0{int(won)}\0{reason}\n".encode("utf-8"))
            if won and not beaten_by[right]:
                beaten_by[right].append({"candidate_id": left, "reason": reason})
    frontier = sorted(name for name in rows if not beaten_by[name])
    purgatory = set(rows) - set(frontier)
    if default not in frontier:
        default = frontier[0]
    return {
        "requirements": requirements,
        "frontier": frontier,
        "previous_frontier": previous_frontier,
        "purgatory": sorted(purgatory),
        "reentered_from_purgatory": sorted(previous_purgatory & set(frontier)),
        "newly_in_purgatory": sorted(purgatory - previous_purgatory),
        "default": default,
        "beaten_by": beaten_by,
        "candidate_count_recomputed": len(rows),
        "comparison_count": comparison_count,
        "comparison_digest": "sha256:" + comparison_hasher.hexdigest(),
        "views_digest": digest(views),
    }, purgatory, default


def make_rows(
    source: dict[str, Any],
    base: dict[str, Any],
    prior_whole: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = {}
    for whole_id, whole_row in sorted(prior_whole["candidate_evaluations"].items()):
        base_id = whole_row["base_candidate"]
        nesting_kind = whole_row["nesting_kind"]
        geometry_profile = whole_row["geometry_profile"]
        for connection_id, connection_row in sorted(connection["candidate_evaluations"].items()):
            for history_id, history_row in sorted(history["candidate_evaluations"].items()):
                candidate_id = f"{whole_id}__{connection_id}__{history_id}"
                persistence_row = persistence["candidate_inventories"].get(history_id)
                requirement_results = dict(whole_row["requirement_results"])
                requirement_results.update({
                    "connection_transport_admissible": connection_row["all_transports_admissible"],
                    "history_candidate_complete": history_row["complete_history_candidate"],
                    "history_noncommutation_status_computed": (
                        history_row["noncommutation_earned"]
                        or history_row["noncommutation_status"] == "explicit_negative"
                    ),
                    "history_ordered_noncommutation_earned": history_row["noncommutation_earned"],
                    "persistence_inventory_survives": bool(persistence_row and persistence_row["surviving_count"] > 0),
                    "chirality_expressible": chirality["status"]["expressible"],
                    "chirality_not_forced": not chirality["status"]["forced"],
                    "chirality_installable_not_forced": chirality["status"]["installable"] and not chirality["status"]["forced"],
                })
                vector = dict(whole_row["presumption_vector"])
                vector.update({
                    "connection_cost": connection_row["connection_cost"],
                    "connection_violation_count": sum(
                        len(packet["violations"])
                        for packet in connection_row["packet_results"].values()
                    ),
                    "history_cost": history_row["history_cost"],
                    "history_noncommutation_missing": int(not history_row["noncommutation_earned"]),
                    "persistence_surviving_distinctions": -(persistence_row["surviving_count"] if persistence_row else 0),
                    "chirality_forcing_penalty": int(chirality["status"]["forced"]),
                })
                rows[candidate_id] = {
                    "candidate_id": candidate_id,
                    "base_candidate": base_id,
                    "nesting_kind": nesting_kind,
                    "geometry_profile": geometry_profile,
                    "connection_candidate": connection_id,
                    "history_candidate": history_id,
                    "source_packet_digest": source["result_digest"],
                    "base_census_digest": base["result_digest"],
                    "prior_whole_digest": prior_whole["result_digest"],
                    "connection_digest": connection["result_digest"],
                    "history_digest": history["result_digest"],
                    "persistence_digest": persistence["result_digest"],
                    "chirality_digest": chirality["result_digest"],
                    "requirement_results": requirement_results,
                    "presumption_vector": vector,
                    "complete_whole_candidate": True,
                    "behavior_signature": digest({
                        "whole": whole_row["behavior_signature"],
                        "connection": connection_id,
                        "history": history_row["behavior_signature"],
                        "requirements": requirement_results,
                    }),
                }
    return rows


def purgatory_records(final_purgatory: list[str], rows: dict[str, dict[str, Any]], final_receipt: dict[str, Any], connection: dict[str, Any], history: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for candidate_id in final_purgatory:
        row = rows[candidate_id]
        failed = sorted(name for name, value in row["requirement_results"].items() if not value)
        witness: dict[str, Any]
        if not row["requirement_results"]["connection_transport_admissible"]:
            witness = connection["candidate_evaluations"][row["connection_candidate"]]["first_violation"]
        elif not row["requirement_results"]["history_ordered_noncommutation_earned"]:
            witness = history["candidate_evaluations"][row["history_candidate"]]["witness_pair"] or {"explicit_negative": True}
        elif final_receipt["beaten_by"].get(candidate_id):
            witness = final_receipt["beaten_by"][candidate_id][0]
        else:
            witness = {"failed_requirements": failed}
        records.append({
            "candidate_id": candidate_id,
            "failed": failed,
            "witness": witness,
            "reoffer_rule": "re-offer after any source packet, transport, history, persistence, or chirality receipt changes",
        })
    return records


def run(
    source: dict[str, Any],
    base: dict[str, Any],
    nesting: dict[str, Any],
    prior_whole: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
) -> dict[str, Any]:
    rows = make_rows(source, base, prior_whole, connection, history, persistence, chirality)
    default = "classical_distribution__complete_pairwise__shannon_fisher__qca_permutation_transport__sequence_histories"
    if default not in rows:
        default = sorted(rows)[0]
    campaigns = (
        ("settle the old whole object inside the expanded grammar", list(FULL_REQUIREMENTS)),
        ("add connection admissibility and re-offer every base, nesting, and geometry", list(FULL_REQUIREMENTS) + ["connection_transport_admissible"]),
        ("add ordered histories and recompute every complete candidate", list(FULL_REQUIREMENTS) + [
            "connection_transport_admissible",
            "history_candidate_complete",
            "history_noncommutation_status_computed",
            "history_ordered_noncommutation_earned",
        ]),
        ("add persistence and chirality readouts without forcing orientation", list(DEEP_REQUIREMENTS)),
        ("open continuation tick with complete deep grammar retained", list(DEEP_REQUIREMENTS)),
    )
    receipts = []
    purgatory: set[str] = set()
    previous_frontier: list[str] = []
    for step, (reason, requirements) in enumerate(campaigns):
        receipt, purgatory, default = recompute(rows, requirements, previous_frontier, purgatory, default)
        receipt.update({
            "step": step,
            "reason": reason,
            "global_mss_claimed": False,
            "terminal_state": False,
        })
        receipt["receipt_digest"] = digest(receipt)
        receipts.append(receipt)
        previous_frontier = receipt["frontier"]

    final_frontier = receipts[-1]["frontier"]
    final_rows = [rows[name] for name in final_frontier]
    final_purgatory = purgatory_records(receipts[-1]["purgatory"], rows, receipts[-1], connection, history)
    expected_count = (
        base["candidate_count"]
        * len(NESTING_KINDS)
        * len(GEOMETRY_PROFILES)
        * connection["candidate_count"]
        * history["candidate_count"]
    )
    checks = {
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "candidate_count_matches_deep_cross_product": len(rows) == expected_count == 4752,
        "every_base_reoffered": {row["base_candidate"] for row in rows.values()} == set(base["candidate_evaluations"]),
        "every_nesting_reoffered": {row["nesting_kind"] for row in rows.values()} == set(NESTING_KINDS),
        "every_geometry_reoffered": {row["geometry_profile"] for row in rows.values()} == set(GEOMETRY_PROFILES),
        "every_connection_reoffered": {row["connection_candidate"] for row in rows.values()} == set(connection["candidate_evaluations"]),
        "every_history_reoffered": {row["history_candidate"] for row in rows.values()} == set(history["candidate_evaluations"]),
        "final_frontier_plural": len(final_frontier) > 1,
        "final_frontier_uses_surviving_connection": (
            {row["connection_candidate"] for row in final_rows} <= set(connection["frontier"])
            and "identity_transport" not in {row["connection_candidate"] for row in final_rows}
        ),
        "final_frontier_uses_ordered_history": {row["history_candidate"] for row in final_rows} == {"sequence_histories"},
        "final_frontier_passes_all_requirements": all(all(row["requirement_results"][name] for name in DEEP_REQUIREMENTS) for row in final_rows),
        "receipts_recompute_all_candidates": len(receipts) == 5 and all(receipt["candidate_count_recomputed"] == 4752 for receipt in receipts),
        "idle_tick_continues_without_error": receipts[-1]["frontier"] == receipts[-2]["frontier"],
        "purgatory_has_witness_and_reoffer": all(row["witness"] and row["reoffer_rule"] for row in final_purgatory),
        "no_promotion_or_terminal_claim": True,
    }
    result = {
        "schema": "ratchet.pack183.deep.whole-manifold-v2-alt.v1",
        "source_packet_digest": source["result_digest"],
        "base_census_digest": base["result_digest"],
        "nesting_digest": nesting["result_digest"],
        "prior_whole_digest": prior_whole["result_digest"],
        "connection_digest": connection["result_digest"],
        "history_digest": history["result_digest"],
        "persistence_digest": persistence["result_digest"],
        "chirality_digest": chirality["result_digest"],
        "base_candidate_count": base["candidate_count"],
        "nesting_candidate_count": len(NESTING_KINDS),
        "geometry_profile_count": len(GEOMETRY_PROFILES),
        "connection_candidate_count": connection["candidate_count"],
        "history_candidate_count": history["candidate_count"],
        "candidate_count": len(rows),
        "candidate_evaluations": rows,
        "receipts": receipts,
        "final_frontier": final_frontier,
        "final_frontier_evaluations": {name: rows[name] for name in final_frontier},
        "operational_default": default,
        "purgatory": final_purgatory,
        "checks": checks,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "global_mss_claimed": False,
        "candidate_universe_exhausted": False,
        "terminal_state": False,
        "status": "OPEN_DEEP_ALT_FRONTIER_COMPUTED",
        "claim_ceiling": "finite source-relative deep feedback comparison; no official rung, final manifold, or physical admission",
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
    root_results = args.source.parent
    source = load_json(args.source)
    base = load_json(root_results / "base_mss.json")
    nesting = load_json(root_results / "nesting.json")
    prior_whole = load_json(root_results / "whole_manifold.json")
    connection = load_json(args.prior / "connection_alt.json")
    history = load_json(args.prior / "history_alt.json")
    persistence = load_json(args.prior / "persistence_alt.json")
    chirality = load_json(args.prior / "chirality_alt.json")
    result = run(source, base, nesting, prior_whole, connection, history, persistence, chirality)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "candidate_count": result["candidate_count"],
        "final_frontier": result["final_frontier"],
        "default": result["operational_default"],
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
