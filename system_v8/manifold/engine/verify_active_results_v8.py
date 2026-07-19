#!/usr/bin/env python3
"""Fail-closed semantic verification for the Pack 183 active results."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from common import digest, write_json
from nesting_ratchet import NESTING_KINDS
from whole_feedback_ratchet import FULL_REQUIREMENTS, GEOMETRY_PROFILES


EXPECTED_BASES = {
    "finite_partition", "pairwise_graph", "finite_relation", "probe_incidence",
    "simplicial_complex", "partial_order", "matroid", "finite_automaton",
    "classical_distribution", "rebit_density", "complex_density", "euclidean_jordan",
    "clifford_spinor", "quaternionic", "bracket_register", "octonionic",
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


def validate(source: dict[str, Any], base: dict[str, Any], nesting: dict[str, Any], whole: dict[str, Any]) -> dict[str, bool]:
    base_ids = set(base.get("candidate_evaluations", {}))
    packet_ids = {row.get("packet_id") for row in source.get("base_packets", [])}
    nesting_ids = set(nesting.get("candidate_evaluations", {}))
    whole_ids = set(whole.get("candidate_evaluations", {}))
    expected_nesting = {
        f"{base_id}__{kind}"
        for base_id in base.get("heldout_frontier", [])
        for kind in NESTING_KINDS
    }
    expected_whole = {
        f"{base_id}__{kind}__{profile}"
        for base_id in base_ids
        for kind in NESTING_KINDS
        for profile in GEOMETRY_PROFILES
    }
    final_whole = whole.get("final_frontier", [])
    final_rows = [whole.get("candidate_evaluations", {}).get(name, {}) for name in final_whole]
    whole_receipts = whole.get("receipts", [])
    nesting_receipts = nesting.get("receipts", [])
    base_receipts = base.get("receipts", [])
    checks = {
        "source_schema": source.get("schema") == "ratchet.v8.source-packets.v1",
        "source_result_digest": result_digest_valid(source),
        "source_all_pass": source.get("all_pass") is True and all(source.get("checks", {}).values()),
        "source_base_packet_count": len(source.get("base_packets", [])) == 9 and len(packet_ids) == 9,
        "source_nesting_packet_count": len(source.get("nesting_packets", [])) == 2,
        "source_width_four": all(row.get("width") == 4 for row in source.get("base_packets", [])),
        "source_selection_disclosed": "calibration" in source.get("selection_disclosure", "").lower(),
        "base_schema": base.get("schema") == "ratchet.pack183.base-mss-census.v1",
        "base_result_digest": result_digest_valid(base),
        "base_receipt_digests": receipt_digests_valid(base),
        "base_exact_candidate_universe": base_ids == EXPECTED_BASES and base.get("candidate_count") == 16,
        "base_every_candidate_every_packet": all(
            set(row.get("packet_results", {})) == packet_ids
            for row in base.get("candidate_evaluations", {}).values()
        ),
        "base_current_frontier_plural": set(base.get("heldout_frontier", [])) == {"finite_relation", "finite_automaton"},
        "base_operational_default": base.get("operational_default") in base.get("heldout_frontier", []),
        "base_receipts_complete": len(base_receipts) == 2 and all(receipt.get("default") in receipt.get("frontier", []) for receipt in base_receipts),
        "base_no_global_or_exhaustion": base.get("global_mss_claimed") is False and base.get("candidate_universe_exhausted") is False,
        "base_source_link": base.get("source_packet_digest") == source.get("result_digest"),
        "base_process_checks": base.get("all_pass") is True and all(base.get("process_checks", {}).values()),
        "nesting_schema": nesting.get("schema") == "ratchet.pack183.nesting-ratchet.v1",
        "nesting_result_digest": result_digest_valid(nesting),
        "nesting_receipt_digests": receipt_digests_valid(nesting),
        "nesting_exact_cross_product": nesting_ids == expected_nesting and nesting.get("candidate_count") == 22,
        "nesting_all_complete": all(row.get("complete_whole_candidate") is True for row in nesting.get("candidate_evaluations", {}).values()),
        "nesting_order_effect": all(len(set(counts.values())) > 1 for counts in nesting.get("order_effect_counts", {}).values()),
        "nesting_plural_frontier": len(nesting.get("final_frontier", [])) == 4 and {
            row.get("nesting_kind") for name, row in nesting.get("candidate_evaluations", {}).items()
            if name in nesting.get("final_frontier", [])
        } == {"complete_pairwise", "ternary_relation"},
        "nesting_receipts_open": len(nesting_receipts) == 5 and all(
            receipt.get("terminal_state") is False
            and receipt.get("global_mss_claimed") is False
            and receipt.get("default") in receipt.get("frontier", [])
            for receipt in nesting_receipts
        ),
        "nesting_idle_continuation": len(nesting_receipts) == 5 and nesting_receipts[-1].get("frontier") == nesting_receipts[-2].get("frontier"),
        "nesting_no_global_or_exhaustion": nesting.get("global_mss_claimed") is False and nesting.get("candidate_universe_exhausted") is False,
        "nesting_links": nesting.get("source_packet_digest") == source.get("result_digest") and nesting.get("base_census_digest") == base.get("result_digest"),
        "nesting_process_checks": nesting.get("all_pass") is True and all(nesting.get("process_checks", {}).values()),
        "whole_schema": whole.get("schema") == "ratchet.pack183.whole-feedback-ratchet.v1",
        "whole_result_digest": result_digest_valid(whole),
        "whole_receipt_digests": receipt_digests_valid(whole),
        "whole_exact_cross_product": whole_ids == expected_whole and whole.get("candidate_count") == 528,
        "whole_every_candidate_complete": all(row.get("complete_whole_candidate") is True for row in whole.get("candidate_evaluations", {}).values()),
        "whole_all_base_candidates_reoffered": {row.get("base_candidate") for row in whole.get("candidate_evaluations", {}).values()} == EXPECTED_BASES,
        "whole_all_nestings_reoffered": {row.get("nesting_kind") for row in whole.get("candidate_evaluations", {}).values()} == set(NESTING_KINDS),
        "whole_all_geometries_compared": {row.get("geometry_profile") for row in whole.get("candidate_evaluations", {}).values()} == set(GEOMETRY_PROFILES),
        "whole_final_frontier_six": len(final_whole) == 6,
        "whole_final_base_feedback": {row.get("base_candidate") for row in final_rows} == {"finite_relation", "finite_automaton", "classical_distribution"},
        "whole_final_nesting_plural": {row.get("nesting_kind") for row in final_rows} == {"complete_pairwise", "ternary_relation"},
        "whole_final_shannon_fisher": {row.get("geometry_profile") for row in final_rows} == {"shannon_fisher"},
        "whole_final_passes_requirements": all(
            row and all(row.get("requirement_results", {}).get(name) is True for name in FULL_REQUIREMENTS)
            for row in final_rows
        ),
        "whole_geometry_changes_with_nesting": len({row.get("whole_summary", {}).get("baseline_effective_operator_digest") for row in final_rows}) == 2,
        "whole_expansion_and_renesting_nonzero": all(
            row.get("whole_summary", {}).get("expansion_effective_inner_delta", 0) > 0
            and row.get("whole_summary", {}).get("baseline_renesting_delta", 0) > 0
            for row in final_rows
        ),
        "whole_complete_comparison_counts": len(whole_receipts) == 5 and all(
            receipt.get("candidate_count_recomputed") == 528
            and receipt.get("comparison_count") == 528 * 527
            for receipt in whole_receipts
        ),
        "whole_requirement_revision_changes_frontier": len(whole_receipts) == 5 and whole_receipts[2].get("frontier") != whole_receipts[1].get("frontier"),
        "whole_restoration_reoffers_all": len(whole_receipts) == 5 and whole_receipts[3].get("frontier") == whole_receipts[1].get("frontier"),
        "whole_idle_continuation": len(whole_receipts) == 5 and whole_receipts[4].get("frontier") == whole_receipts[3].get("frontier"),
        "whole_operational_default": whole.get("operational_default") in final_whole and all(receipt.get("default") in receipt.get("frontier", []) for receipt in whole_receipts),
        "whole_no_global_terminal_or_exhaustion": whole.get("global_mss_claimed") is False and whole.get("terminal_state") is False and whole.get("candidate_universe_exhausted") is False,
        "whole_links": whole.get("source_packet_digest") == source.get("result_digest") and whole.get("base_census_digest") == base.get("result_digest"),
        "whole_process_checks": whole.get("all_pass") is True and all(whole.get("process_checks", {}).values()),
    }
    return checks


def reseal(value: dict[str, Any]) -> None:
    value.pop("result_digest", None)
    value["result_digest"] = digest(value)


def mutation_tests(source: dict[str, Any], base: dict[str, Any], nesting: dict[str, Any], whole: dict[str, Any]) -> list[dict[str, Any]]:
    tests = []

    def run(name: str, target: str, mutate, expected_check: str) -> None:
        copies = [copy.deepcopy(source), copy.deepcopy(base), copy.deepcopy(nesting), copy.deepcopy(whole)]
        index = {"source": 0, "base": 1, "nesting": 2, "whole": 3}[target]
        mutate(copies[index])
        reseal(copies[index])
        checks = validate(*copies)
        tests.append({
            "mutation": name,
            "expected_failed_check": expected_check,
            "rejected": checks.get(expected_check) is False,
            "actual_failed_checks": sorted(key for key, value in checks.items() if not value),
        })

    run("drop_source_packet", "source", lambda d: d["base_packets"].pop(), "source_base_packet_count")
    run("claim_global_base_mss", "base", lambda d: d.__setitem__("global_mss_claimed", True), "base_no_global_or_exhaustion")
    run("claim_base_universe_exhausted", "base", lambda d: d.__setitem__("candidate_universe_exhausted", True), "base_no_global_or_exhaustion")
    run("collapse_base_frontier", "base", lambda d: d.__setitem__("heldout_frontier", d["heldout_frontier"][:1]), "base_current_frontier_plural")
    run("erase_base_candidate", "base", lambda d: d["candidate_evaluations"].pop("matroid"), "base_exact_candidate_universe")
    run("skip_base_packet_simulation", "base", lambda d: d["candidate_evaluations"]["finite_relation"]["packet_results"].pop(next(iter(d["candidate_evaluations"]["finite_relation"]["packet_results"]))), "base_every_candidate_every_packet")
    run("erase_nesting_candidate", "nesting", lambda d: d["candidate_evaluations"].pop(next(iter(d["candidate_evaluations"]))), "nesting_exact_cross_product")
    run("erase_nesting_order_effect", "nesting", lambda d: [counts.update({key: 11 for key in counts}) for counts in d["order_effect_counts"].values()], "nesting_order_effect")
    run("terminal_nesting_receipt", "nesting", lambda d: d["receipts"][-1].__setitem__("terminal_state", True), "nesting_receipts_open")
    run("collapse_nesting_frontier", "nesting", lambda d: d.__setitem__("final_frontier", d["final_frontier"][:1]), "nesting_plural_frontier")
    run("erase_whole_candidate", "whole", lambda d: d["candidate_evaluations"].pop(next(iter(d["candidate_evaluations"]))), "whole_exact_cross_product")
    run("claim_global_whole_mss", "whole", lambda d: d.__setitem__("global_mss_claimed", True), "whole_no_global_terminal_or_exhaustion")
    run("claim_terminal_whole_state", "whole", lambda d: d.__setitem__("terminal_state", True), "whole_no_global_terminal_or_exhaustion")
    run("claim_whole_universe_exhausted", "whole", lambda d: d.__setitem__("candidate_universe_exhausted", True), "whole_no_global_terminal_or_exhaustion")
    run("collapse_whole_frontier", "whole", lambda d: d.__setitem__("final_frontier", d["final_frontier"][:1]), "whole_final_frontier_six")
    run("erase_geometry_profile", "whole", lambda d: [d["candidate_evaluations"].pop(key) for key in list(d["candidate_evaluations"]) if key.endswith("__no_geometry")], "whole_exact_cross_product")
    run("break_final_requirement", "whole", lambda d: d["candidate_evaluations"][d["final_frontier"][0]]["requirement_results"].__setitem__("nested_entropy_chain_rule", False), "whole_final_passes_requirements")
    run("falsify_complete_comparison_count", "whole", lambda d: d["receipts"][0].__setitem__("comparison_count", 1), "whole_complete_comparison_counts")
    run("erase_requirement_revision", "whole", lambda d: d["receipts"][2].__setitem__("frontier", list(d["receipts"][1]["frontier"])), "whole_requirement_revision_changes_frontier")
    run("break_idle_continuation", "whole", lambda d: d["receipts"][4].__setitem__("frontier", d["receipts"][4]["frontier"][:1]), "whole_idle_continuation")
    run("erase_base_feedback_reentry", "whole", lambda d: d.__setitem__("final_frontier", [name for name in d["final_frontier"] if not name.startswith("classical_distribution__")]), "whole_final_frontier_six")
    run("break_source_link", "whole", lambda d: d.__setitem__("source_packet_digest", "sha256:" + "0" * 64), "whole_links")
    return tests


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--nesting", type=Path, required=True)
    parser.add_argument("--whole", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    base = json.loads(args.base.read_text(encoding="utf-8"))
    nesting = json.loads(args.nesting.read_text(encoding="utf-8"))
    whole = json.loads(args.whole.read_text(encoding="utf-8"))
    checks = validate(source, base, nesting, whole)
    mutations = mutation_tests(source, base, nesting, whole)
    result = {
        "schema": "ratchet.pack183.active-verification.v1",
        "checks": checks,
        "mutation_tests": mutations,
        "mutation_count": len(mutations),
        "all_pass": all(checks.values()) and all(row["rejected"] for row in mutations),
    }
    result["result_digest"] = digest(result)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": len(checks),
        "mutations_rejected": sum(row["rejected"] for row in mutations),
        "mutation_count": len(mutations),
        "failed_checks": sorted(key for key, value in checks.items() if not value),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
