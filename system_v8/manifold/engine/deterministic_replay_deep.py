#!/usr/bin/env python3
"""Replay the complete deep-manifold pipeline twice in process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from chirality_layer import run as run_chirality
from common import digest, write_json
from connection_layer import run as run_connection
from history_layer import run as run_history
from persistence_layer import run as run_persistence
from verify_deep import STAGE_FILES, run as run_verification, strict_load
from whole_manifold_v2 import parent_whole_from_disk, run as run_whole


SCHEMA = "ratchet.pack183.deep-deterministic-replay.v1"
CLAIM_CEILING = (
    "packet-relative deterministic replay and semantic equality only; no promotion, formal admission, "
    "canonical manifold, proof, physics, terminal state, or exhaustive-grammar claim"
)
NAMES = ("connection", "history", "persistence", "chirality", "whole_manifold_v2", "verification")
ARCHIVED_FILES = STAGE_FILES + ("verification.json",)


def one_replay(source: dict[str, Any], parent_whole: dict[str, Any]):
    connection = run_connection(source, parent_whole)
    history = run_history(source, connection)
    persistence = run_persistence(source, history)
    chirality = run_chirality(source, persistence)
    whole = run_whole(source, chirality, parent_whole)
    verification = run_verification(source, connection, history, persistence, chirality, whole)
    return connection, history, persistence, chirality, whole, verification


def run(source: dict[str, Any], archived: list[dict[str, Any]]) -> dict[str, Any]:
    parent_whole = parent_whole_from_disk()
    source_before = digest(source)
    parent_before = digest(parent_whole)
    first = one_replay(source, parent_whole)
    first_snapshot = tuple((row["result_digest"], digest(row)) for row in first)
    second = one_replay(source, parent_whole)
    replay_rows = {}
    checks = {}
    for index, name in enumerate(NAMES):
        archived_row = archived[index]
        first_row = first[index]
        second_row = second[index]
        replay_rows[name] = {
            "archived_result_digest": archived_row["result_digest"],
            "first_result_digest": first_row["result_digest"],
            "second_result_digest": second_row["result_digest"],
            "archived_canonical_digest": digest(archived_row),
            "first_canonical_digest": digest(first_row),
            "second_canonical_digest": digest(second_row),
            "first_snapshot_result_digest": first_snapshot[index][0],
            "first_snapshot_canonical_digest": first_snapshot[index][1],
        }
        checks[f"{name}_result_digest_stable"] = (
            archived_row["result_digest"] == first_row["result_digest"] == second_row["result_digest"]
            == first_snapshot[index][0]
        )
        checks[f"{name}_canonical_digest_stable"] = (
            digest(archived_row) == digest(first_row) == digest(second_row) == first_snapshot[index][1]
        )
        checks[f"{name}_all_pass"] = (
            archived_row.get("all_pass") is True
            and first_row.get("all_pass") is True
            and second_row.get("all_pass") is True
        )
    checks.update({
        "source_unchanged_across_replays": source_before == digest(source),
        "parent_whole_unchanged_across_replays": parent_before == digest(parent_whole),
        "first_semantic_verification": first[-1]["all_pass"] is True and all(first[-1]["checks"].values()),
        "second_semantic_verification": second[-1]["all_pass"] is True and all(second[-1]["checks"].values()),
        "frontier_stable": (
            archived[4]["final_frontier"] == first[4]["final_frontier"] == second[4]["final_frontier"]
        ),
        "purgatory_stable": digest(archived[4]["purgatory"]) == digest(first[4]["purgatory"]) == digest(second[4]["purgatory"]),
        "noncommutation_status_and_witness_stable": (
            archived[1]["noncommutation_earned"] == first[1]["noncommutation_earned"] == second[1]["noncommutation_earned"]
            and digest(archived[1]["noncommutation_witness"])
            == digest(first[1]["noncommutation_witness"])
            == digest(second[1]["noncommutation_witness"])
        ),
        "persistence_inventory_stable": (
            digest(archived[2]["inventories"]) == digest(first[2]["inventories"]) == digest(second[2]["inventories"])
        ),
        "chirality_tristate_stable": (
            (archived[3]["expressible"], archived[3]["forced"], archived[3]["installable"])
            == (first[3]["expressible"], first[3]["forced"], first[3]["installable"])
            == (second[3]["expressible"], second[3]["forced"], second[3]["installable"])
        ),
        "mutation_inventory_stable": (
            [row["mutation"] for row in archived[5]["mutation_tests"]]
            == [row["mutation"] for row in first[5]["mutation_tests"]]
            == [row["mutation"] for row in second[5]["mutation_tests"]]
        ),
    })
    result = {
        "schema": SCHEMA,
        "source_packet_digest": source["result_digest"],
        "parent_whole_digest": parent_whole["result_digest"],
        "replays": replay_rows,
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
    parser.add_argument("--prior", type=Path, required=True, help="directory containing archived deep results")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = strict_load(args.source)
    archived = [strict_load(args.prior / filename) for filename in ARCHIVED_FILES]
    result = run(source, archived)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": len(result["checks"]),
        "failed_checks": sorted(name for name, value in result["checks"].items() if not value),
        "replayed_stages": list(NAMES),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
