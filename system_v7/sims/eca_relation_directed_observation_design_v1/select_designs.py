#!/usr/bin/env python3
"""Closed-receipt controller for the train-only observation-design search."""

from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
from pathlib import Path


SIM_ID = "eca_relation_directed_observation_design_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
JAX_SOURCE = HERE / "search_jax.py"
JULIA_SOURCE = HERE / "search_julia.jl"
JAX_RESULT = RESULTS / f"{SIM_ID}_jax_search_results.json"
JULIA_RESULT = RESULTS / f"{SIM_ID}_julia_search_results.json"
OUTPUT_PATH = RESULTS / f"{SIM_ID}_selection_validation.json"
WINNER_RECEIPT = HERE / "selected_design_receipt.json"
CONFIRMATION_SOURCES = ("confirm_jax.py", "confirm_julia.jl", "validate_confirmation.py")
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Closed JSON comparison, source/result hashing, mutation attacks, and fail-closed winner receipt construction.",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def source_hash(result: dict, engine: str) -> object:
    if engine == "jax":
        return result.get("source_sha256") or result.get("hashes", {}).get("search_jax_sha256")
    return result.get("source_sha256") or result.get("hashes", {}).get("search_julia_sha256")


def screen_records(result: dict) -> list[dict]:
    return result.get("complete_screen_records") or result.get("screen_records") or []


def exact_records(result: dict) -> list[dict]:
    return result.get("complete_exact_score_records") or result.get("exact_score_records") or []


def shortlists(result: dict) -> dict:
    return result.get("shortlists") or result.get("shortlist_identity") or {}


def winner_subset(result: dict, size: str) -> list[int]:
    if result.get("winners"):
        return result["winners"][size]["subset_indices"]
    return result["winner_summary"][size]["subset"]


def normalize_screen(row: dict) -> dict:
    effective = row.get("effective_unordered_hypothesis_counts", [])
    relations = row.get("distinct_partition_relation_counts", [])
    return {
        "subset_size": row["subset_size"],
        "subset_indices": row.get("subset_indices", row.get("subset")),
        "diversity_fixture_count": row["diversity_fixture_count"],
        "system_identified_fixture_count": row["system_identified_fixture_count"],
        "capped_effective_hypothesis_sum": row.get(
            "capped_effective_hypothesis_sum", sum(min(value, 64) for value in effective)
        ),
        "capped_partition_relation_sum": row.get(
            "capped_partition_relation_sum", sum(min(value, 64) for value in relations)
        ),
        "total_ordered_version_space_size": row["total_ordered_version_space_size"],
        "screen_objective": row["screen_objective"],
    }


def normalize_exact(row: dict) -> dict:
    fixtures = row.get("fixture_scores", [])
    return {
        "subset_size": row["subset_size"],
        "subset_indices": row.get("subset_indices", row.get("subset")),
        "minimum_robust_query_count": row.get(
            "minimum_robust_query_count", min((item["robust_query_count"] for item in fixtures), default=0)
        ),
        "sum_robust_query_count": row.get(
            "sum_robust_query_count", sum(item["robust_query_count"] for item in fixtures)
        ),
        "balanced_fixture_count": row["balanced_fixture_count"],
        "minimum_query_disjoint_robust_identifiable_count": row.get(
            "minimum_query_disjoint_robust_identifiable_count",
            min((item["query_disjoint_robust_count"] for item in fixtures), default=0),
        ),
        "sum_query_disjoint_robust_identifiable_count": row.get(
            "sum_query_disjoint_robust_identifiable_count",
            sum(item["query_disjoint_robust_count"] for item in fixtures),
        ),
        "total_identifiable_query_count": row.get(
            "total_identifiable_query_count", row.get("global_identifiable_query_count")
        ),
        "total_identifiable_same_count": row.get(
            "total_identifiable_same_count", sum(item["identifiable_same_count"] for item in fixtures)
        ),
        "total_identifiable_different_count": row.get(
            "total_identifiable_different_count", sum(item["identifiable_different_count"] for item in fixtures)
        ),
        "total_query_disjoint_identifiable_count": row.get(
            "total_query_disjoint_identifiable_count", row.get("query_disjoint_identifiable_query_count")
        ),
        "total_query_disjoint_query_count": row.get(
            "total_query_disjoint_query_count", sum(item["query_disjoint_query_count"] for item in fixtures)
        ),
        "exact_objective": row["exact_objective"],
    }


def normalize_fixture(row: dict) -> dict:
    return {
        "fixture_index": row["fixture_index"],
        "ordered_version_space_size": row["ordered_version_space_size"],
        "effective_unordered_hypothesis_count": row["effective_unordered_hypothesis_count"],
        "distinct_partition_relation_count": row["distinct_partition_relation_count"],
        "system_identified": row["system_identified"],
        "diversity_fixture": row["diversity_fixture"],
        "identifiable_query_count": row["identifiable_query_count"],
        "identifiable_same_count": row["identifiable_same_count"],
        "identifiable_different_count": row["identifiable_different_count"],
        "query_disjoint_query_count": row["query_disjoint_query_count"],
        "query_disjoint_identifiable_count": row["query_disjoint_identifiable_count"],
        "query_disjoint_same_count": row["query_disjoint_same_count"],
        "query_disjoint_different_count": row["query_disjoint_different_count"],
        "relation_vector_hash": row.get("relation_vector_hash", row.get("identifiability_vector_hash")),
    }


def winner_fixture_ledgers(result: dict) -> dict:
    if result.get("winner_fixture_ledgers"):
        return result["winner_fixture_ledgers"]
    lookup = {
        (row["subset_size"], tuple(row["subset"])): row["fixture_scores"]
        for row in result.get("exact_score_records", [])
    }
    return {
        size: lookup[(int(size), tuple(winner_subset(result, size)))]
        for size in ("2", "3", "4")
    }


def normalized_winners(result: dict) -> dict:
    lookup = {
        (row["subset_size"], tuple(row.get("subset_indices", row.get("subset")))): normalize_exact(row)
        for row in exact_records(result)
    }
    return {
        size: lookup[(int(size), tuple(winner_subset(result, size)))]
        for size in ("2", "3", "4")
    }


def normalized_baselines(result: dict) -> dict:
    if result.get("winners"):
        return {
            size: {name: normalize_exact(value) for name, value in rows.items()}
            for size, rows in result["baselines"].items()
        }
    baseline_exact = result["baseline_exact_scores"]["records"]
    directed = normalized_winners(result)
    output = {}
    for size in ("2", "3", "4"):
        output[size] = {"relation_directed": directed[size]}
        for name in ("hash_order", "system_identification"):
            output[size][name] = normalize_exact(baseline_exact[size][name]["score"])
    return output


def compare_records(left: list[dict], right: list[dict], key: str) -> dict:
    mismatch_count = 0
    first_mismatch = None
    for index in range(min(len(left), len(right))):
        if left[index] != right[index]:
            mismatch_count += 1
            if first_mismatch is None:
                first_mismatch = {"index": index, "jax": left[index], "julia": right[index]}
    return {
        "ledger": key,
        "jax_count": len(left),
        "julia_count": len(right),
        "mismatch_count": mismatch_count,
        "first_mismatch": first_mismatch,
        "all_match": len(left) == len(right) and mismatch_count == 0,
        "jax_canonical_sha256": canonical_hash(left),
        "julia_canonical_sha256": canonical_hash(right),
    }


def engine_receipt_valid(result: dict, engine: str, actual_source_hash: str) -> bool:
    validation_reads = result.get(
        "validation_or_test_files_read",
        result.get("validation_or_test_fixture_files_read"),
    )
    confirmation_reads = result.get("confirmation_source_files_read")
    if confirmation_reads is None:
        frozen = result.get("frozen_input_verification", {})
        confirmation_presence = frozen.get("confirmation_source_presence", {})
        confirmation_reads_valid = (
            bool(confirmation_presence)
            and not any(confirmation_presence.values())
            and "no_confirmation_source_exists" in result.get("tests", [])
        )
    else:
        confirmation_reads_valid = confirmation_reads == []
    return (
        result.get("sim_id") == SIM_ID
        and result.get("engine") == engine
        and result.get("phase") in ("train_only_search", "search")
        and result.get("classification") == CLASSIFICATION
        and result.get("promotion_allowed") is False
        and result.get("formal_admission_allowed") is False
        and result.get("ran") is True
        and result.get("reads_peer_result") is False
        and result.get("all_pass") is True
        and result.get("peer_result_files_read") == []
        and result.get("parent_result_files_read") == []
        and validation_reads == []
        and confirmation_reads_valid
        and source_hash(result, engine) == actual_source_hash
    )


def compare_results(jax: dict, julia: dict) -> dict:
    screen_key = lambda row: (row["subset_size"], tuple(row["subset_indices"]))
    screen = compare_records(
        sorted((normalize_screen(row) for row in screen_records(jax)), key=screen_key),
        sorted((normalize_screen(row) for row in screen_records(julia)), key=screen_key),
        "complete_screen_records",
    )
    exact = compare_records(
        [normalize_exact(row) for row in exact_records(jax)],
        [normalize_exact(row) for row in exact_records(julia)],
        "complete_exact_score_records",
    )
    surfaces = {}
    normalized_surfaces = {
        "shortlists": (shortlists(jax), shortlists(julia)),
        "winners": (normalized_winners(jax), normalized_winners(julia)),
        "baselines": (normalized_baselines(jax), normalized_baselines(julia)),
        "winner_fixture_ledgers": (
            {size: [normalize_fixture(row) for row in rows] for size, rows in winner_fixture_ledgers(jax).items()},
            {size: [normalize_fixture(row) for row in rows] for size, rows in winner_fixture_ledgers(julia).items()},
        ),
    }
    for key, (left, right) in normalized_surfaces.items():
        surfaces[key] = {"match": left == right, "jax_sha256": canonical_hash(left), "julia_sha256": canonical_hash(right)}
    return {
        "screen": screen,
        "exact": exact,
        "surfaces": surfaces,
        "all_match": screen["all_match"] and exact["all_match"]
        and all(item["match"] for item in surfaces.values()),
    }


def expected_universes(result: dict) -> dict:
    screens = screen_records(result)
    exact = exact_records(result)
    screen_keys = [(row.get("subset_size"), tuple(row.get("subset_indices", row.get("subset", [])))) for row in screens]
    expected_screen = [
        (size, subset)
        for size in (2, 3, 4)
        for subset in __import__("itertools").combinations(range(16), size)
    ]
    exact_keys = [(row.get("subset_size"), tuple(row.get("subset_indices", row.get("subset", [])))) for row in exact]
    expected_exact = [
        (size, tuple(subset))
        for size in (2, 3, 4)
        for subset in shortlists(result).get(str(size), [])
    ]
    return {
        "screen_universe_exact": (
            len(screen_keys) == len(expected_screen)
            and len(set(screen_keys)) == len(expected_screen)
            and sorted(screen_keys) == expected_screen
        ),
        "exact_universe_matches_shortlists": exact_keys == expected_exact,
        "screen_count": len(screens),
        "exact_count": len(exact),
        "all_three_winners_present": all(winner_subset(result, size) for size in ("2", "3", "4")),
    }


def mutation_attacks(jax: dict, julia: dict) -> dict:
    attacks = {}
    mutations = {
        "screen_row": ("complete_screen_records", "diversity_fixture_count", -1),
        "exact_row": ("complete_exact_score_records", "sum_robust_query_count", -1),
    }
    for name, (ledger, field, value) in mutations.items():
        changed = copy.deepcopy(julia)
        changed[ledger][0][field] = value
        comparison = compare_results(jax, changed)
        attacks[name] = {"detected": not comparison["all_match"], "field": field}
    changed = copy.deepcopy(julia)
    changed["winners"]["2"]["subset_indices"] = copy.deepcopy(changed["shortlists"]["2"][1])
    attacks["winner"] = {
        "detected": not compare_results(jax, changed)["all_match"],
        "field": "winners.2.subset_indices",
    }
    changed = copy.deepcopy(julia)
    changed["complete_screen_records"] = changed["complete_screen_records"][:-1]
    attacks["omitted_candidate"] = {
        "detected": not compare_results(jax, changed)["all_match"],
        "field": "complete_screen_records",
    }
    changed = copy.deepcopy(julia)
    changed["shortlists"]["3"][0], changed["shortlists"]["3"][1] = (
        changed["shortlists"]["3"][1],
        changed["shortlists"]["3"][0],
    )
    attacks["shortlist_order"] = {
        "detected": not compare_results(jax, changed)["all_match"],
        "field": "shortlists.3",
    }
    return attacks


def build_winner_receipt(jax: dict, julia: dict, comparison: dict) -> dict:
    winners = normalized_winners(julia)
    return {
        "schema": "codex_ratchet.eca_relation_directed_observation_design_v1.selected_design_receipt.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "status": "frozen_after_train_search_before_confirmation_source",
        "spec_sha256": sha256_file(SPEC_PATH),
        "preregistration_receipt_sha256": sha256_file(PREREG_PATH),
        "search_source_sha256": {
            "jax": sha256_file(JAX_SOURCE),
            "julia": sha256_file(JULIA_SOURCE),
        },
        "search_result_sha256": {
            "jax": sha256_file(JAX_RESULT),
            "julia": sha256_file(JULIA_RESULT),
        },
        "complete_screen_records_sha256": comparison["screen"]["jax_canonical_sha256"],
        "complete_exact_score_records_sha256": comparison["exact"]["jax_canonical_sha256"],
        "shortlists_sha256": comparison["surfaces"]["shortlists"]["jax_sha256"],
        "winner_payload_sha256": canonical_hash(winners),
        "winners": winners,
        "baselines": normalized_baselines(julia),
        "all_three_sizes_claim_bearing": True,
        "confirmation_sources_present_when_frozen": False,
        "optimization_boundary": "exact winners within preregistered screened shortlists; no global relation-optimum claim",
        "validation_may_select_or_replace": False,
        "test_is_blind": False,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": json.loads(SPEC_PATH.read_text())["blocked_consumers"],
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    jax = json.loads(JAX_RESULT.read_text())
    julia = json.loads(JULIA_RESULT.read_text())
    actual_sources = {"jax": sha256_file(JAX_SOURCE), "julia": sha256_file(JULIA_SOURCE)}
    comparison = compare_results(jax, julia)
    universes = {"jax": expected_universes(jax), "julia": expected_universes(julia)}
    attacks = mutation_attacks(jax, julia)
    confirmation_absent = not any((HERE / name).exists() for name in CONFIRMATION_SOURCES)
    tests = {
        "C1_jax_receipt_valid": engine_receipt_valid(jax, "jax", actual_sources["jax"]),
        "C2_julia_receipt_valid": engine_receipt_valid(julia, "julia", actual_sources["julia"]),
        "C3_complete_cross_runtime_match": comparison["all_match"],
        "C4_jax_universes_exact": all(universes["jax"].values()),
        "C5_julia_universes_exact": all(universes["julia"].values()),
        "C6_all_mutations_detected": all(item["detected"] for item in attacks.values()),
        "C7_confirmation_sources_absent": confirmation_absent,
        "C8_all_sizes_visible": sorted(julia.get("winners", {})) == ["2", "3", "4"],
    }
    all_pass = all(tests.values())
    result = {
        "schema": "codex_ratchet.eca_relation_directed_observation_design_v1.selection_validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "phase": "train_only_selection_controller",
        "controller_runtime": {
            "command": [sys.executable, str(Path(__file__).resolve())],
            "cwd": str(Path.cwd()),
            "runner_identity": platform.node(),
            "python_version": platform.python_version(),
            "validator_path": str(Path(__file__).resolve().relative_to(HERE.parents[2])),
            "validator_sha256": sha256_file(Path(__file__)),
        },
        "source_and_result_receipts": {
            "spec_sha256": sha256_file(SPEC_PATH),
            "search_source_sha256": actual_sources,
            "search_result_sha256": {"jax": sha256_file(JAX_RESULT), "julia": sha256_file(JULIA_RESULT)},
        },
        "comparison": comparison,
        "universes": universes,
        "mutation_attacks": attacks,
        "tests": tests,
        "all_pass": all_pass,
        "result_label": spec["allowed_claim_label_if_search_controller_passes"] if all_pass else "TRAIN_ONLY_SEARCH_CONTROLLER_FAILED",
        "scientific_interpretation_deferred": True,
        "confirmation_opened": False,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "exact train-only screened-set search and frozen winners only; no validation, measurement-design candidate, learner, or perception claim",
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if all_pass:
        WINNER_RECEIPT.write_text(json.dumps(build_winner_receipt(jax, julia, comparison), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "tests": tests, "winners": julia.get("winners")}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
