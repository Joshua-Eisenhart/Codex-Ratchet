#!/usr/bin/env python3
"""Independent cross-runtime gate for the reserved-family confirmation."""

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
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Closed JSON normalization, fieldwise cross-runtime comparison, exact integer gates, hashes, and mutation control.",
    }
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
JAX_SOURCE = HERE / "confirm_jax.py"
JULIA_SOURCE = HERE / "confirm_julia.jl"
JAX_RESULT = RESULTS / f"{SIM_ID}_jax_confirmation_results.json"
JULIA_RESULT = RESULTS / f"{SIM_ID}_julia_confirmation.json"
OUTPUT = RESULTS / f"{SIM_ID}_confirmation_validation.json"
DESIGN_IDS = [f"size_{size}.{role}" for size in (2, 3, 4) for role in (
    "relation_directed", "hash_order", "system_identification"
)]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def normalize_jax(row: dict) -> dict:
    return {
        "fixture_index": row["fixture_index"],
        "fixture": row["pair_orbit_representative"],
        "ordered_version_space_size": row["ordered_version_space_size"],
        "effective_unordered_hypothesis_count": row["effective_unordered_hypothesis_count"],
        "distinct_partition_relation_count": row["distinct_full_partition_relation_count"],
        "system_identified": row["system_identified"],
        "true_pair_retained": row["true_pair_retained"],
        "diversity_fixture": row["diversity_fixture"],
        "identifiable_query_count": row["identifiable_query_count"],
        "identifiable_same_count": row["identifiable_same_count"],
        "identifiable_different_count": row["identifiable_different_count"],
        "robust_query_count": row["robust_query_count"],
        "query_disjoint_query_count": row["query_disjoint_query_count"],
        "query_disjoint_identifiable_count": row["query_disjoint_identifiable_count"],
        "query_disjoint_same_count": row["query_disjoint_same_count"],
        "query_disjoint_different_count": row["query_disjoint_different_count"],
        "query_disjoint_robust_count": row["query_disjoint_robust_count"],
        "balanced_fixture": row["balanced_fixture"],
        "relation_vector_sha256": row["relation_vector_sha256"],
    }


def normalize_julia(row: dict, fixture_index: int) -> dict:
    return {
        "fixture_index": fixture_index,
        "fixture": row["fixture"],
        "ordered_version_space_size": row["ordered_version_space_size"],
        "effective_unordered_hypothesis_count": row["effective_unordered_hypothesis_count"],
        "distinct_partition_relation_count": row["distinct_partition_relation_count"],
        "system_identified": row["system_identified"],
        "true_pair_retained": row["true_pair_in_version_space"],
        "diversity_fixture": row["diversity_fixture"],
        "identifiable_query_count": row["identifiable_query_count"],
        "identifiable_same_count": row["identifiable_same_count"],
        "identifiable_different_count": row["identifiable_different_count"],
        "robust_query_count": row["robust_query_count"],
        "query_disjoint_query_count": row["query_disjoint_query_count"],
        "query_disjoint_identifiable_count": row["query_disjoint_identifiable_count"],
        "query_disjoint_same_count": row["query_disjoint_identifiable_same_count"],
        "query_disjoint_different_count": row["query_disjoint_identifiable_different_count"],
        "query_disjoint_robust_count": row["query_disjoint_robust_identifiable_count"],
        "balanced_fixture": row["fixture_balance"],
        "relation_vector_sha256": row["identifiability_vector_sha256"],
    }


def ledgers(jax: dict, julia: dict) -> tuple[dict, dict]:
    jax_ledgers = {
        design_id: [normalize_jax(row) for row in jax["validation_scores"][design_id]["fixture_ledger"]]
        for design_id in DESIGN_IDS
    }
    julia_ledgers = {}
    for design_id in DESIGN_IDS:
        size_role, family = design_id.split(".")
        size = size_role.removeprefix("size_")
        rows = julia["validation"]["fixture_records"][size][family]
        julia_ledgers[design_id] = [normalize_julia(row, index) for index, row in enumerate(rows)]
    return jax_ledgers, julia_ledgers


def score_summary(rows: list[dict]) -> dict:
    return {
        "fixture_count": len(rows),
        "construction_valid": all(row["true_pair_retained"] and row["ordered_version_space_size"] > 0 for row in rows),
        "diversity_fixture_count": sum(row["diversity_fixture"] for row in rows),
        "system_identified_fixture_count": sum(row["system_identified"] for row in rows),
        "identifiable_query_count": sum(row["identifiable_query_count"] for row in rows),
        "identifiable_same_count": sum(row["identifiable_same_count"] for row in rows),
        "identifiable_different_count": sum(row["identifiable_different_count"] for row in rows),
        "minimum_identifiable_query_count": min(row["identifiable_query_count"] for row in rows),
        "minimum_robust_query_count": min(row["robust_query_count"] for row in rows),
        "sum_robust_query_count": sum(row["robust_query_count"] for row in rows),
        "query_disjoint_query_count": sum(row["query_disjoint_query_count"] for row in rows),
        "query_disjoint_identifiable_count": sum(row["query_disjoint_identifiable_count"] for row in rows),
        "minimum_query_disjoint_coverage": min(
            row["query_disjoint_identifiable_count"] / row["query_disjoint_query_count"] for row in rows
        ),
        "minimum_query_disjoint_robust_count": min(row["query_disjoint_robust_count"] for row in rows),
        "sum_query_disjoint_robust_count": sum(row["query_disjoint_robust_count"] for row in rows),
        "balanced_fixture_count": sum(row["balanced_fixture"] for row in rows),
        "ledger_sha256": canonical_hash(rows),
    }


def derive_gates(summaries: dict) -> dict:
    sizes = {}
    for size in (2, 3, 4):
        directed = summaries[f"size_{size}.relation_directed"]
        hash_order = summaries[f"size_{size}.hash_order"]
        system_id = summaries[f"size_{size}.system_identification"]
        rows = directed["rows"]
        total_queries = len(rows) * 9636
        gates = {
            "construction": directed["construction_valid"],
            "diversity": directed["diversity_fixture_count"] == len(rows),
            "system_identification": directed["system_identified_fixture_count"] == 0,
            "global_relation_coverage": 20 * directed["identifiable_query_count"] >= 19 * total_queries,
            "fixture_floor": all(5 * row["identifiable_query_count"] >= 4 * 9636 for row in rows),
            "query_disjoint_global_coverage": (
                10 * directed["query_disjoint_identifiable_count"] >= 9 * directed["query_disjoint_query_count"]
            ),
            "query_disjoint_fixture_floor": all(
                10 * row["query_disjoint_identifiable_count"] >= 7 * row["query_disjoint_query_count"]
                for row in rows
            ),
            "pooled_target_balance": (
                5 * directed["identifiable_same_count"] >= directed["identifiable_query_count"]
                and 5 * directed["identifiable_different_count"] >= directed["identifiable_query_count"]
            ),
            "fixture_balance": 5 * directed["balanced_fixture_count"] >= 4 * len(rows),
            "baseline_separation": (
                (
                    directed["minimum_robust_query_count"] > hash_order["minimum_robust_query_count"]
                    or directed["sum_robust_query_count"] > hash_order["sum_robust_query_count"]
                )
                and directed["diversity_fixture_count"] > system_id["diversity_fixture_count"]
            ),
        }
        sizes[str(size)] = {"gates": gates, "all_primary_conditions_pass": all(gates.values())}
    passing = [size for size, row in sizes.items() if row["all_primary_conditions_pass"]]
    return {
        "sizes": sizes,
        "passing_sizes": passing,
        "candidate_exists": len(passing) >= 1,
        "robust_design_family": len(passing) >= 2,
    }


def main() -> int:
    jax = json.loads(JAX_RESULT.read_text())
    julia = json.loads(JULIA_RESULT.read_text())
    jax_ledgers, julia_ledgers = ledgers(jax, julia)
    comparison = {}
    for design_id in DESIGN_IDS:
        left, right = jax_ledgers[design_id], julia_ledgers[design_id]
        comparison[design_id] = {
            "record_count": len(left),
            "match": left == right,
            "jax_sha256": canonical_hash(left),
            "julia_sha256": canonical_hash(right),
        }
    summaries = {}
    for design_id, rows in jax_ledgers.items():
        summary = score_summary(rows)
        summary["rows"] = rows
        summaries[design_id] = summary
    derived = derive_gates(summaries)
    reported_jax = jax["primary_validation_gate_receipt"]
    reported_julia = julia["validation"]["family_gate"]
    tests = {
        "C1_all_2925_shared_fixture_records_match": all(row["match"] for row in comparison.values())
        and sum(row["record_count"] for row in comparison.values()) == 2925,
        "C2_confirmation_source_hashes_bind": (
            jax["source_sha256"] == sha256_file(JAX_SOURCE)
            and julia["source_sha256"] == sha256_file(JULIA_SOURCE)
        ),
        "C3_result_integrity_controls_pass": (
            jax["receipt_integrity_all_pass"] is True
            and julia["closed_json_validation"]["passed"] is True
            and all(julia["tests"].values())
        ),
        "C4_fixture_manifest_matches": (
            jax["validation_manifest_receipt"]["hashes"]["validation_fixture_representatives_sha256"]
            == julia["validation"]["fixture_representatives_sha256"]
        ),
        "C5_controller_gate_derivation_matches_jax": (
            derived["candidate_exists"] == reported_jax["candidate_exists"]
            and derived["robust_design_family"] == reported_jax["robust_design_family"]
            and derived["passing_sizes"] == [str(value) for value in reported_jax["passing_sizes"]]
            and all(
                derived["sizes"][size]["gates"] == reported_jax["sizes"][size]["gates"]
                for size in ("2", "3", "4")
            )
        ),
        "C6_controller_gate_derivation_matches_julia": (
            derived["candidate_exists"] == reported_julia["candidate_exists"]
            and derived["robust_design_family"] == reported_julia["robust_design_family"]
            and len(derived["passing_sizes"]) == reported_julia["size_pass_count"]
            and all(
                derived["sizes"][size]["gates"]
                == julia["validation"]["primary_size_gates"][size]["conditions"]
                for size in ("2", "3", "4")
            )
        ),
        "C7_test_block_unopened_in_both_runtimes": (
            jax["test_confirmation"]["opened"] is False
            and jax["test_confirmation"]["fixture_values_constructed"] is False
            and julia["reused_test"] is None
            and julia["test_fixture_files_read"] == []
        ),
        "C8_no_peer_parent_or_search_result_reads": (
            jax["prohibited_reads"]["peer_result_files_read"] == []
            and jax["prohibited_reads"]["parent_result_files_read"] == []
            and jax["prohibited_reads"]["search_result_files_read"] == []
            and julia["peer_result_files_read"] == []
            and julia["parent_result_files_read"] == []
            and julia["search_result_files_read"] == []
            and julia["confirm_jax_source_or_result_files_read"] == []
        ),
    }
    mechanical_all_pass = all(tests.values())
    scientific_pass = derived["robust_design_family"]
    mutated = copy.deepcopy(julia_ledgers)
    mutated[DESIGN_IDS[0]][0]["identifiable_query_count"] += 1
    mutation_detected = mutated != jax_ledgers
    output = {
        "schema": "codex_ratchet.eca_relation_directed_observation_design_v1.confirmation_validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "phase": "cross_runtime_reserved_family_confirmation",
        "controller_runtime": {
            "command": [sys.executable, str(Path(__file__).resolve())],
            "cwd": str(Path.cwd()),
            "runner_identity": platform.node(),
            "python_version": platform.python_version(),
            "source_sha256": sha256_file(Path(__file__)),
        },
        "source_and_result_sha256": {
            "jax_source": sha256_file(JAX_SOURCE),
            "julia_source": sha256_file(JULIA_SOURCE),
            "jax_result": sha256_file(JAX_RESULT),
            "julia_result": sha256_file(JULIA_RESULT),
        },
        "shared_fixture_record_comparison": comparison,
        "shared_fixture_record_projection_sha256": canonical_hash(jax_ledgers),
        "derived_primary_validation_gate": derived,
        "mutation_control": {"shared_record_mutation_detected": mutation_detected},
        "tests": tests,
        "mechanical_all_pass": mechanical_all_pass,
        "scientific_pass": scientific_pass,
        "all_pass": mechanical_all_pass and scientific_pass,
        "result_label": "PREREGISTERED_CONFIRMATION_RED" if mechanical_all_pass and not scientific_pass else (
            "FINITE_TARGET_AWARE_ECA_RELATION_MEASUREMENT_DESIGN_CANDIDATE"
            if mechanical_all_pass else "CONFIRMATION_CONTROLLER_INVALID"
        ),
        "test_block_opened": False,
        "claim_ceiling": "exact cross-runtime reserved-family rejection of these frozen target-aware designs; no learner, perception, object discovery, or schedule promotion",
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": json.loads((HERE / "spec.json").read_text())["blocked_consumers"],
    }
    OUTPUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "mechanical_all_pass": mechanical_all_pass,
        "scientific_pass": scientific_pass,
        "result_label": output["result_label"],
        "passing_sizes": derived["passing_sizes"],
        "tests": tests,
    }, sort_keys=True))
    return 0 if mechanical_all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
