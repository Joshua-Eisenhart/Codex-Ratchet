#!/usr/bin/env python3
"""Fail-closed semantic verification for the redundant deep alt lane."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from common import digest, write_json


SCHEMAS = {
    "source": "ratchet.v8.source-packets.v1",
    "connection": "ratchet.pack183.deep.connection-alt.v1",
    "history": "ratchet.pack183.deep.history-alt.v1",
    "persistence": "ratchet.pack183.deep.persistence-alt.v1",
    "chirality": "ratchet.pack183.deep.chirality-alt.v1",
    "whole": "ratchet.pack183.deep.whole-manifold-v2-alt.v1",
}


def result_digest_valid(value: dict[str, Any]) -> bool:
    expected = value.get("result_digest")
    body = {key: item for key, item in value.items() if key != "result_digest"}
    return expected == digest(body)


def receipt_digests_valid(value: dict[str, Any]) -> bool:
    for receipt in value.get("receipts", []):
        expected = receipt.get("receipt_digest")
        body = {key: item for key, item in receipt.items() if key != "receipt_digest"}
        if expected != digest(body):
            return False
    return True


def validate(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> dict[str, bool]:
    connection_ids = set(connection.get("candidate_evaluations", {}))
    history_ids = set(history.get("candidate_evaluations", {}))
    final_rows = [whole.get("candidate_evaluations", {}).get(name, {}) for name in whole.get("final_frontier", [])]
    checks = {
        "source_schema": source.get("schema") == SCHEMAS["source"],
        "source_result_digest": result_digest_valid(source),
        "source_all_pass": source.get("all_pass") is True and all(source.get("checks", {}).values()),
        "source_packet_count_pinned_9": len(source.get("base_packets", [])) == 9,
        "connection_schema": connection.get("schema") == SCHEMAS["connection"],
        "connection_result_digest": result_digest_valid(connection),
        "connection_receipt_digests": receipt_digests_valid(connection),
        "connection_all_pass": connection.get("all_pass") is True and all(connection.get("checks", {}).values()),
        "connection_candidate_count": connection.get("candidate_count") == 3 and connection_ids == {
            "identity_transport", "spinor_parity_sign_transport", "qca_permutation_transport",
        },
        "connection_frontier": (
            "qca_permutation_transport" in connection.get("frontier", [])
            and set(connection.get("frontier", [])) <= {
                "qca_permutation_transport", "spinor_parity_sign_transport",
            }
        ),
        "connection_default": connection.get("operational_default") in connection.get("frontier", []),
        "connection_witnesses": all(row.get("witness") for row in connection.get("purgatory", [])),
        "connection_no_promotion": connection.get("promotion_allowed") is False and connection.get("formal_admission_allowed") is False,
        "history_schema": history.get("schema") == SCHEMAS["history"],
        "history_result_digest": result_digest_valid(history),
        "history_receipt_digests": receipt_digests_valid(history),
        "history_all_pass": history.get("all_pass") is True and all(history.get("checks", {}).values()),
        "history_candidate_count": history.get("candidate_count") == 3 and history_ids == {
            "unordered_set_baseline", "sequence_histories", "branching_tree_histories",
        },
        "history_frontier": history.get("frontier") == ["sequence_histories"],
        "history_noncommutation_witness": any(
            row.get("noncommutation_earned") and row.get("witness_pair")
            for row in history.get("candidate_evaluations", {}).values()
        ),
        "history_frontier_witness": all(
            history.get("candidate_evaluations", {}).get(name, {}).get("noncommutation_earned")
            and history.get("candidate_evaluations", {}).get(name, {}).get("witness_pair")
            for name in history.get("frontier", [])
        ),
        "history_explicit_negative": history.get("candidate_evaluations", {}).get("unordered_set_baseline", {}).get("noncommutation_status") == "explicit_negative",
        "history_no_promotion": history.get("promotion_allowed") is False and history.get("formal_admission_allowed") is False,
        "persistence_schema": persistence.get("schema") == SCHEMAS["persistence"],
        "persistence_result_digest": result_digest_valid(persistence),
        "persistence_receipt_digests": receipt_digests_valid(persistence),
        "persistence_all_pass": persistence.get("all_pass") is True and all(persistence.get("checks", {}).values()),
        "persistence_frontier_matches_history": set(persistence.get("frontier", [])) == set(history.get("frontier", [])),
        "persistence_inventory_nonempty": all(
            row.get("surviving_count", 0) > 0
            for row in persistence.get("candidate_inventories", {}).values()
        ),
        "persistence_no_promotion": persistence.get("promotion_allowed") is False and persistence.get("formal_admission_allowed") is False,
        "chirality_schema": chirality.get("schema") == SCHEMAS["chirality"],
        "chirality_result_digest": result_digest_valid(chirality),
        "chirality_receipt_digests": receipt_digests_valid(chirality),
        "chirality_all_pass": chirality.get("all_pass") is True and all(chirality.get("checks", {}).values()),
        "chirality_expressible": chirality.get("status", {}).get("expressible") is True,
        "chirality_not_forced": chirality.get("status", {}).get("forced") is False,
        "chirality_installable": chirality.get("status", {}).get("installable") is True,
        "chirality_no_promotion": chirality.get("promotion_allowed") is False and chirality.get("formal_admission_allowed") is False,
        "whole_schema": whole.get("schema") == SCHEMAS["whole"],
        "whole_result_digest": result_digest_valid(whole),
        "whole_receipt_digests": receipt_digests_valid(whole),
        "whole_all_pass": whole.get("all_pass") is True and all(whole.get("checks", {}).values()),
        "whole_candidate_count": whole.get("candidate_count") == 4752,
        "whole_final_frontier_plural": len(whole.get("final_frontier", [])) > 1,
        "whole_final_connection": (
            {row.get("connection_candidate") for row in final_rows} <= set(connection.get("frontier", []))
            and "identity_transport" not in {row.get("connection_candidate") for row in final_rows}
        ),
        "whole_final_history": {row.get("history_candidate") for row in final_rows} == {"sequence_histories"},
        "whole_final_chirality_status_link": whole.get("chirality_digest") == chirality.get("result_digest"),
        "whole_receipt_count": len(whole.get("receipts", [])) == 5,
        "whole_purgatory_witnesses": all(row.get("witness") and row.get("reoffer_rule") for row in whole.get("purgatory", [])),
        "whole_no_promotion_terminal_or_exhaustion": (
            whole.get("promotion_allowed") is False
            and whole.get("formal_admission_allowed") is False
            and whole.get("terminal_state") is False
            and whole.get("candidate_universe_exhausted") is False
        ),
        "links_chain": (
            connection.get("source_packet_digest") == source.get("result_digest")
            and history.get("source_packet_digest") == source.get("result_digest")
            and history.get("connection_digest") == connection.get("result_digest")
            and persistence.get("history_digest") == history.get("result_digest")
            and chirality.get("persistence_digest") == persistence.get("result_digest")
            and whole.get("source_packet_digest") == source.get("result_digest")
            and whole.get("connection_digest") == connection.get("result_digest")
            and whole.get("history_digest") == history.get("result_digest")
            and whole.get("persistence_digest") == persistence.get("result_digest")
            and whole.get("chirality_digest") == chirality.get("result_digest")
        ),
    }
    return checks


def reseal(value: dict[str, Any]) -> None:
    value.pop("result_digest", None)
    value["result_digest"] = digest(value)


def mutation_tests(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> list[dict[str, Any]]:
    tests = []

    def run_one(name: str, target: str, mutate, expected_check: str) -> None:
        copies = [copy.deepcopy(source), copy.deepcopy(connection), copy.deepcopy(history), copy.deepcopy(persistence), copy.deepcopy(chirality), copy.deepcopy(whole)]
        index = {"source": 0, "connection": 1, "history": 2, "persistence": 3, "chirality": 4, "whole": 5}[target]
        mutate(copies[index])
        reseal(copies[index])
        checks = validate(*copies)
        tests.append({
            "mutation": name,
            "target": target,
            "expected_failed_check": expected_check,
            "rejected": checks.get(expected_check) is False,
        })

    run_one("drop_source_packet", "source", lambda d: d["base_packets"].pop(), "source_packet_count_pinned_9")
    run_one("rename_connection_schema", "connection", lambda d: d.__setitem__("schema", "bad"), "connection_schema")
    run_one("drop_connection_candidate", "connection", lambda d: d["candidate_evaluations"].pop("qca_permutation_transport"), "connection_candidate_count")
    run_one("collapse_connection_frontier", "connection", lambda d: d.__setitem__("frontier", []), "connection_frontier")
    run_one("erase_connection_witness", "connection", lambda d: d["purgatory"][0].__setitem__("witness", None), "connection_witnesses")
    run_one("drop_history_candidate", "history", lambda d: d["candidate_evaluations"].pop("sequence_histories"), "history_candidate_count")
    run_one("erase_history_witness", "history", lambda d: d["candidate_evaluations"]["sequence_histories"].__setitem__("witness_pair", None), "history_frontier_witness")
    run_one("change_history_frontier", "history", lambda d: d.__setitem__("frontier", ["unordered_set_baseline"]), "history_frontier")
    run_one("empty_persistence_inventory", "persistence", lambda d: d["candidate_inventories"]["sequence_histories"].__setitem__("surviving_count", 0), "persistence_inventory_nonempty")
    run_one("force_chirality", "chirality", lambda d: d["status"].__setitem__("forced", True), "chirality_not_forced")
    run_one("erase_chirality_installable", "chirality", lambda d: d["status"].__setitem__("installable", False), "chirality_installable")
    run_one("collapse_whole_frontier", "whole", lambda d: d.__setitem__("final_frontier", d["final_frontier"][:1]), "whole_final_frontier_plural")
    run_one("alter_whole_candidate_count", "whole", lambda d: d.__setitem__("candidate_count", 528), "whole_candidate_count")
    run_one("promote_whole", "whole", lambda d: d.__setitem__("promotion_allowed", True), "whole_no_promotion_terminal_or_exhaustion")
    run_one("break_deep_link", "whole", lambda d: d.__setitem__("chirality_digest", "sha256:" + "0" * 64), "whole_final_chirality_status_link")
    return tests


def run(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> dict[str, Any]:
    checks = validate(source, connection, history, persistence, chirality, whole)
    mutations = mutation_tests(source, connection, history, persistence, chirality, whole)
    result = {
        "schema": "ratchet.pack183.deep.verification-alt.v1",
        "pinned_schemas": SCHEMAS,
        "checks": checks,
        "mutation_tests": mutations,
        "mutation_count": len(mutations),
        "all_pass": all(checks.values()) and len(mutations) >= 12 and all(row["rejected"] for row in mutations),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "semantic verification of redundant deep alt receipts only",
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
    connection = json.loads((args.prior / "connection_alt.json").read_text(encoding="utf-8"))
    history = json.loads((args.prior / "history_alt.json").read_text(encoding="utf-8"))
    persistence = json.loads((args.prior / "persistence_alt.json").read_text(encoding="utf-8"))
    chirality = json.loads((args.prior / "chirality_alt.json").read_text(encoding="utf-8"))
    whole = json.loads((args.prior / "whole_manifold_v2_alt.json").read_text(encoding="utf-8"))
    result = run(source, connection, history, persistence, chirality, whole)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": len(result["checks"]),
        "mutations_rejected": sum(row["rejected"] for row in result["mutation_tests"]),
        "mutation_count": result["mutation_count"],
        "failed_checks": sorted(key for key, value in result["checks"].items() if not value),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
