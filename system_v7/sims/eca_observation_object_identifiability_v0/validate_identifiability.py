#!/usr/bin/env python3
"""Closed-receipt controller for the exact observation-identifiability scout."""

from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

from validate_preregistration import build_manifests, simultaneous_pair_orbit


SIM_ID = "eca_observation_object_identifiability_v0"
CLASSIFICATION = "scratch_diagnostic"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SPEC_PATH = HERE / "spec.json"
JAX_PATH = RESULTS / f"{SIM_ID}_jax_results.json"
JULIA_PATH = RESULTS / f"{SIM_ID}_julia_results.json"
OUTPUT_PATH = RESULTS / f"{SIM_ID}_validation.json"
QUERY_COUNT = 9636


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(result: dict) -> list[dict]:
    for key in ("budget_ledger", "budget_records", "fixture_budget_ledger", "records", "ledger"):
        if isinstance(result.get(key), list):
            return result[key]
    return []


def expected_fixture_budget_keys(spec: dict) -> list[tuple[int, int, int]]:
    manifests = build_manifests()
    fixtures = [min(tuple(map(tuple, orbit))) for orbit in manifests["pair_orbits"]["test"]]
    budgets = spec["observation_packet"]["cumulative_trajectory_budgets"]
    return [(a, b, budget) for a, b in fixtures for budget in budgets]


def record_keys(rows: list[dict]) -> list[tuple[object, object, object]]:
    return [(row.get("rule_A"), row.get("rule_B"), row.get("trajectory_budget")) for row in rows]


def compare(jax_result: dict, julia_result: dict, spec: dict) -> dict:
    left = records(jax_result)
    right = records(julia_result)
    expected = expected_fixture_budget_keys(spec)
    required = spec["required_budget_record_fields"]
    left_keys = record_keys(left)
    right_keys = record_keys(right)
    mismatch_counts = {field: 0 for field in required}
    missing_counts = {"jax": {field: 0 for field in required}, "julia": {field: 0 for field in required}}
    first_mismatch = None
    for index in range(min(len(left), len(right))):
        for engine, row in (("jax", left[index]), ("julia", right[index])):
            for field in required:
                if field not in row:
                    missing_counts[engine][field] += 1
        for field in required:
            if left[index].get(field) != right[index].get(field):
                mismatch_counts[field] += 1
                if first_mismatch is None:
                    first_mismatch = {
                        "index": index,
                        "field": field,
                        "jax": left[index].get(field),
                        "julia": right[index].get(field),
                    }
    exact_universes = left_keys == expected and right_keys == expected
    no_missing = not any(value for engine in missing_counts.values() for value in engine.values())
    all_fields_match = exact_universes and no_missing and not any(mismatch_counts.values())
    return {
        "expected_record_count": len(expected),
        "jax_record_count": len(left),
        "julia_record_count": len(right),
        "jax_record_universe_exact": left_keys == expected,
        "julia_record_universe_exact": right_keys == expected,
        "missing_required_field_counts": missing_counts,
        "mismatch_count_by_field": mismatch_counts,
        "first_mismatch": first_mismatch,
        "all_fields_match": all_fields_match,
    }


def aggregate_budgets(rows: list[dict], spec: dict) -> dict:
    budgets = spec["observation_packet"]["cumulative_trajectory_budgets"]
    fixture_count = spec["rule_family_split"]["claim_bearing_fixture_count"]
    aggregates = {}
    for budget in budgets:
        subset = [row for row in rows if row.get("trajectory_budget") == budget]
        identifiable = sum(row.get("identifiable_query_count", 0) for row in subset)
        consensus = sum(row.get("consensus_without_identification_query_count", 0) for row in subset)
        same = sum(
            row.get("identifiable_same_count", 0)
            for row in subset
            if row.get("effective_unordered_hypothesis_count", 0) >= 8
            and row.get("distinct_partition_relation_count", 0) >= 2
        )
        different = sum(
            row.get("identifiable_different_count", 0)
            for row in subset
            if row.get("effective_unordered_hypothesis_count", 0) >= 8
            and row.get("distinct_partition_relation_count", 0) >= 2
        )
        qualifying = sum(
            row.get("effective_unordered_hypothesis_count", 0) >= 8
            and row.get("distinct_partition_relation_count", 0) >= 2
            for row in subset
        )
        construction_valid = (
            len(subset) == fixture_count
            and all(row.get("ordered_version_space_size", 0) > 0 for row in subset)
            and all(row.get("true_pair_in_version_space") is True for row in subset)
        )
        global_coverage = identifiable / (fixture_count * QUERY_COUNT) if len(subset) == fixture_count else 0.0
        fixture_floor = min((row.get("identifiable_query_count", 0) / QUERY_COUNT for row in subset), default=0.0)
        system_fraction = sum(row.get("system_identified") is True for row in subset) / fixture_count if len(subset) == fixture_count else 1.0
        same_fraction = same / consensus if consensus else 0.0
        different_fraction = different / consensus if consensus else 0.0
        checks = {
            "construction_valid": construction_valid,
            "global_identifiable_coverage": global_coverage >= 0.95,
            "every_fixture_at_least_80_percent": fixture_floor >= 0.80,
            "at_least_100_qualifying_fixtures": qualifying >= 100,
            "at_least_50000_consensus_without_identification_queries": consensus >= 50000,
            "identifiable_same_at_least_20_percent": same_fraction >= 0.20,
            "identifiable_different_at_least_20_percent": different_fraction >= 0.20,
            "fewer_than_half_system_identified": system_fraction < 0.50,
        }
        candidate = all(checks.values())
        if system_fraction >= 0.90:
            regime = "OBSERVATIONS_IDENTIFY_DYNAMICS_NOT_OBJECT_CONSENSUS"
        elif global_coverage < 0.95 or fixture_floor < 0.80:
            regime = "OBSERVATION_OBJECT_RELATION_UNIDENTIFIABLE"
        elif same_fraction in (0.0, 1.0) or different_fraction in (0.0, 1.0):
            regime = "OBJECT_CONSENSUS_TARGET_ONE_CLASS"
        elif candidate:
            regime = "CONSENSUS_WITHOUT_IDENTIFICATION_CANDIDATE"
        else:
            regime = "NO_STABLE_CONSENSUS_WITHOUT_IDENTIFICATION_WINDOW"
        aggregates[str(budget)] = {
            "fixture_count": len(subset),
            "global_identifiable_coverage": global_coverage,
            "minimum_fixture_identifiable_coverage": fixture_floor,
            "system_identified_fraction": system_fraction,
            "qualifying_fixture_count": qualifying,
            "consensus_without_identification_query_count": consensus,
            "consensus_identifiable_same_count": same,
            "consensus_identifiable_different_count": different,
            "consensus_identifiable_same_fraction": same_fraction,
            "consensus_identifiable_different_fraction": different_fraction,
            "checks": checks,
            "consensus_candidate": candidate,
            "regime": regime,
        }
    qualifying_budgets = [budget for budget in budgets if aggregates[str(budget)]["consensus_candidate"]]
    consecutive = [
        (budgets[index], budgets[index + 1])
        for index in range(len(budgets) - 1)
        if aggregates[str(budgets[index])]["consensus_candidate"]
        and aggregates[str(budgets[index + 1])]["consensus_candidate"]
    ]
    return {
        "budgets": aggregates,
        "qualifying_budgets": qualifying_budgets,
        "qualifying_consecutive_pairs": consecutive,
        "perception_like_regime_admitted": bool(consecutive),
        "earliest_admitted_budget": consecutive[0][0] if consecutive else None,
    }


def structural_controls(rows: list[dict], spec: dict) -> dict:
    grouped: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row.get("rule_A"), row.get("rule_B")), []).append(row)
    budgets = spec["observation_packet"]["cumulative_trajectory_budgets"]
    nested_version_sizes = True
    nonincreasing_ambiguity = True
    count_identities = True
    orbit_keys_exact = True
    for pair, sequence in grouped.items():
        sequence.sort(key=lambda row: row.get("trajectory_budget"))
        nested_version_sizes &= [row.get("trajectory_budget") for row in sequence] == budgets
        nested_version_sizes &= all(
            sequence[index + 1].get("ordered_version_space_size", -1)
            <= sequence[index].get("ordered_version_space_size", -1)
            for index in range(len(sequence) - 1)
        )
        nonincreasing_ambiguity &= all(
            sequence[index + 1].get("unidentifiable_query_count", QUERY_COUNT + 1)
            <= sequence[index].get("unidentifiable_query_count", QUERY_COUNT + 1)
            for index in range(len(sequence) - 1)
        )
        expected_pair = min(simultaneous_pair_orbit(pair))
        expected_orbit = f"{expected_pair[0]},{expected_pair[1]}"
        for row in sequence:
            count_identities &= row.get("identifiable_query_count", -1) + row.get("unidentifiable_query_count", -1) == QUERY_COUNT
            count_identities &= row.get("identifiable_same_count", -1) + row.get("identifiable_different_count", -1) == row.get("identifiable_query_count", -2)
            orbit_keys_exact &= row.get("pair_orbit_key") == expected_orbit
    return {
        "version_space_sizes_monotone_nonincreasing": nested_version_sizes,
        "unidentifiable_query_counts_monotone_nonincreasing": nonincreasing_ambiguity,
        "query_count_identities_exact": count_identities,
        "pair_orbit_keys_exact": orbit_keys_exact,
    }


def mutation_attacks(jax_result: dict, julia_result: dict, spec: dict) -> dict:
    attacks = {}
    mutations = {
        "version_space_size": ("ordered_version_space_size", -1),
        "compatible_count": ("compatible_A_count", -1),
        "compatible_hash": ("compatible_A_hash", "0" * 64),
        "identifiability_hash": ("identifiability_vector_hash", "f" * 64),
    }
    for name, (field, value) in mutations.items():
        mutated = copy.deepcopy(julia_result)
        records(mutated)[0][field] = value
        comparison = compare(jax_result, mutated, spec)
        attacks[name] = {
            "field": field,
            "detected": not comparison["all_fields_match"] and comparison["mismatch_count_by_field"][field] > 0,
        }
    duplicated = copy.deepcopy(julia_result)
    mutated_rows = records(duplicated)
    mutated_rows[1] = copy.deepcopy(mutated_rows[0])
    duplicate_comparison = compare(jax_result, duplicated, spec)
    attacks["duplicate_record"] = {
        "field": "record_universe",
        "detected": not duplicate_comparison["julia_record_universe_exact"],
    }
    return attacks


def declared_source_hash(result: dict, engine: str) -> object:
    if engine == "jax":
        return result.get("source_sha256")
    return result.get("hashes", {}).get("run_julia_sha256")


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    jax_result = json.loads(JAX_PATH.read_text())
    julia_result = json.loads(JULIA_PATH.read_text())
    comparison = compare(jax_result, julia_result, spec)
    controls = structural_controls(records(julia_result), spec)
    attacks = mutation_attacks(jax_result, julia_result, spec)
    census = aggregate_budgets(records(julia_result), spec)
    actual_source_hashes = {
        "jax": sha256_file(HERE / "run_jax.py"),
        "julia": sha256_file(HERE / "run_julia.jl"),
    }
    declared_source_hashes = {
        "jax": declared_source_hash(jax_result, "jax"),
        "julia": declared_source_hash(julia_result, "julia"),
    }
    engine_receipts_valid = all(
        result.get("ran") is True
        and result.get("reads_peer_result") is False
        and result.get("all_pass") is True
        and result.get("peer_result_files_read") == []
        and result.get("parent_result_files_read") == []
        and isinstance(result.get("source_path"), str)
        and bool(result.get("source_path"))
        for result in (jax_result, julia_result)
    ) and actual_source_hashes == declared_source_hashes
    tests = {
        "C1_engine_receipts_valid": engine_receipts_valid,
        "C2_every_required_field_matches": comparison["all_fields_match"],
        "C3_structural_controls_pass": all(controls.values()),
        "C4_all_mutations_detected": all(attack["detected"] for attack in attacks.values()),
        "C5_all_budget_constructions_valid": all(
            row["checks"]["construction_valid"] for row in census["budgets"].values()
        ),
    }
    all_pass = all(tests.values())
    result = {
        "schema": "codex_ratchet.eca_observation_object_identifiability_v0.validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine_mode": spec["engine_contract"]["mode"],
        "controller_runtime": {
            "command": [sys.executable, str(Path(__file__).resolve())],
            "cwd": str(Path.cwd()),
            "runner_identity": platform.node(),
            "python_version": platform.python_version(),
            "validator_path": str(Path(__file__).resolve().relative_to(HERE.parents[2])),
            "validator_sha256": sha256_file(Path(__file__)),
        },
        "source_receipts": {
            "spec_sha256": sha256_file(SPEC_PATH),
            "actual_source_sha256": actual_source_hashes,
            "declared_source_sha256": declared_source_hashes,
            "jax_result_sha256": sha256_file(JAX_PATH),
            "julia_result_sha256": sha256_file(JULIA_PATH),
        },
        "comparison": comparison,
        "structural_controls": controls,
        "mutation_attacks": attacks,
        "budget_census": census,
        "tests": tests,
        "all_pass": all_pass,
        "result_label": spec["allowed_claim_label_if_exact_controller_passes"] if all_pass else "EXACT_CONTROLLER_FAILED",
        "perception_like_regime_admitted": all_pass and census["perception_like_regime_admitted"],
        "neural_training_admitted": False,
        "claim_ceiling": "exact finite ECA partial-observation census only; no learning, general perception, engine-stage, QIT, ontology, or Axis0 claim",
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "tests": tests, "budget_census": census}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
