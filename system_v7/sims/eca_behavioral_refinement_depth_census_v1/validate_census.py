#!/usr/bin/env python3
"""Closed-receipt controller and downstream V2 admission gate for N9."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path


SIM_ID = "eca_behavioral_refinement_depth_census_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
SPEC_PATH = HERE / "spec.json"
JAX_PATH = RESULTS / f"{SIM_ID}_jax_results.json"
JULIA_PATH = RESULTS / f"{SIM_ID}_julia_results.json"
OUTPUT_PATH = RESULTS / f"{SIM_ID}_validation.json"
REQUIRED_FIELDS = (
    "rule_a",
    "rule_b",
    "strict_refinement_depth",
    "first_equality_round",
    "class_count_trajectory",
    "surviving_ordered_pair_count_trajectory",
    "stable_class_count",
    "partition_hash",
    "transition_pair_hash",
    "simultaneous_pair_orbit_key",
    "hidden_batch",
    "depth_six_changed_ordered_pair_count",
)

TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Closed JSON comparison, independent split reconstruction, exact metric arithmetic, SHA receipts, and mutation attacks.",
    },
    "numpy": {"used": False, "reason": "No numerical bridge is needed."},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "numpy": None}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(result: dict) -> list[dict]:
    if isinstance(result.get("pair_ledger"), list):
        return result["pair_ledger"]
    if isinstance(result.get("pairs"), list):
        return result["pairs"]
    rings = result.get("rings", [])
    if len(rings) == 1:
        return records(rings[0])
    return []


def compare(jax_result: dict, julia_result: dict) -> dict:
    left = records(jax_result)
    right = records(julia_result)
    expected_pairs = [(a, b) for a in range(255) for b in range(a + 1, 256)]
    left_pairs = [(record.get("rule_a"), record.get("rule_b")) for record in left]
    right_pairs = [(record.get("rule_a"), record.get("rule_b")) for record in right]
    left_pair_universe_exact = left_pairs == expected_pairs
    right_pair_universe_exact = right_pairs == expected_pairs
    compared = min(len(left), len(right))
    mismatch_counts = {field: 0 for field in REQUIRED_FIELDS}
    first_mismatch = None
    for index in range(compared):
        for field in REQUIRED_FIELDS:
            if left[index].get(field) != right[index].get(field):
                mismatch_counts[field] += 1
                if first_mismatch is None:
                    first_mismatch = {
                        "index": index,
                        "field": field,
                        "jax": left[index].get(field),
                        "julia": right[index].get(field),
                    }
    return {
        "jax_pair_count": len(left),
        "julia_pair_count": len(right),
        "compared_pair_count": compared,
        "jax_pair_universe_exact": left_pair_universe_exact,
        "julia_pair_universe_exact": right_pair_universe_exact,
        "mismatch_count_by_field": mismatch_counts,
        "first_mismatch": first_mismatch,
        "all_fields_match": left_pair_universe_exact
        and right_pair_universe_exact
        and not any(mismatch_counts.values()),
    }


def mcc(tp: int, tn: int, fp: int, fn: int) -> float:
    numerator = tp * tn - fp * fn
    denominator = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return numerator / denominator if denominator else 0.0


def v2_admission(ledger: list[dict], spec: dict) -> dict:
    gate = spec["downstream_v2_admission_gate"]
    total_ordered_pairs = spec["carrier"]["state_count"] ** 2
    qualifying = [record for record in ledger if record["strict_refinement_depth"] >= 7]
    qualifying_orbits = {record["simultaneous_pair_orbit_key"] for record in qualifying}
    orbits_by_batch = {
        batch: {
            record["simultaneous_pair_orbit_key"]
            for record in qualifying
            if record["hidden_batch"] == batch
        }
        for batch in ("A", "B")
    }
    changed_mass_total_carrier = [
        record["depth_six_changed_ordered_pair_count"] / total_ordered_pairs
        for record in qualifying
    ]
    changed_mass_decisive_subset = [
        record["depth_six_changed_ordered_pair_count"]
        / record["surviving_ordered_pair_count_trajectory"][6]
        for record in qualifying
    ]
    aggregate_changed_mass_total_carrier = (
        sum(record["depth_six_changed_ordered_pair_count"] for record in qualifying)
        / (len(qualifying) * total_ordered_pairs)
        if qualifying
        else 0.0
    )
    aggregate_changed_mass_decisive_subset = (
        sum(record["depth_six_changed_ordered_pair_count"] for record in qualifying)
        / sum(
            record["surviving_ordered_pair_count_trajectory"][6]
            for record in qualifying
        )
        if qualifying
        else 0.0
    )
    baseline_mccs = []
    malformed_trajectories = []
    for record in qualifying:
        trajectory = record["surviving_ordered_pair_count_trajectory"]
        if len(trajectory) <= 6:
            malformed_trajectories.append([record["rule_a"], record["rule_b"]])
            continue
        predicted_positive = trajectory[6]
        target_positive = trajectory[-1]
        tp = target_positive
        fp = predicted_positive - target_positive
        fn = 0
        tn = total_ordered_pairs - predicted_positive
        baseline_mccs.append(mcc(tp, tn, fp, fn))
    full_carrier_macro_mcc = (
        sum(baseline_mccs) / len(baseline_mccs) if baseline_mccs else 1.0
    )
    decisive_subset_macro_mcc = 0.0 if qualifying else 1.0
    checks = {
        "enough_total_deep_orbits": len(qualifying_orbits)
        >= gate["minimum_total_symmetry_distinct_qualifying_orbits"],
        "enough_deep_orbits_batch_A": len(orbits_by_batch["A"])
        >= gate["minimum_qualifying_orbits_per_hidden_batch"],
        "enough_deep_orbits_batch_B": len(orbits_by_batch["B"])
        >= gate["minimum_qualifying_orbits_per_hidden_batch"],
        "minimum_changed_mass_each_fixture": bool(changed_mass_decisive_subset)
        and min(changed_mass_decisive_subset)
        >= gate["minimum_changed_target_mass_per_qualifying_fixture"],
        "aggregate_changed_mass": aggregate_changed_mass_decisive_subset
        >= gate["minimum_aggregate_changed_target_mass"],
        "depth_six_baseline_is_weak_on_full_carrier": full_carrier_macro_mcc
        <= gate["depth_six_baseline_maximum_macro_mcc"],
        "metric_scope_unambiguously_frozen": False,
        "all_qualifying_trajectories_cover_depth_six": not malformed_trajectories,
    }
    admitted = all(checks.values())
    return {
        "qualifying_fixture_count": len(qualifying),
        "qualifying_symmetry_orbit_count": len(qualifying_orbits),
        "qualifying_orbits_by_hidden_batch": {
            batch: len(values) for batch, values in orbits_by_batch.items()
        },
        "changed_mass_denominator": "ordered state pairs equivalent after six strict refinements, as named by decisive_state_pair_subset",
        "minimum_fixture_changed_mass": min(changed_mass_decisive_subset)
        if changed_mass_decisive_subset
        else 0.0,
        "aggregate_changed_mass": aggregate_changed_mass_decisive_subset,
        "minimum_fixture_changed_mass_over_total_carrier": min(
            changed_mass_total_carrier
        )
        if changed_mass_total_carrier
        else 0.0,
        "aggregate_changed_mass_over_total_carrier": aggregate_changed_mass_total_carrier,
        "depth_six_baseline_macro_mcc_full_carrier": full_carrier_macro_mcc,
        "depth_six_baseline_macro_mcc_decisive_subset": decisive_subset_macro_mcc,
        "metric_scope_ambiguity": "The frozen spec names a decisive subset and an MCC threshold but does not state whether MCC is fixture-wide or subset-only. Subset-only depth-six predictions are constant-positive, yielding conventional MCC 0 without informative discrimination.",
        "malformed_trajectory_examples": malformed_trajectories[:12],
        "checks": checks,
        "learned_v2_preregistration_admitted": admitted,
        "result_label": "DEPTH_NOVEL_MASS_ADMITS_SEPARATE_LEARNED_V2_CARD"
        if admitted
        else gate["failure_label"],
        "block_reasons": [name for name, passed in checks.items() if not passed],
        "admission_is_not_learning_success": True,
    }


def mutation_attacks(jax_result: dict, julia_result: dict) -> dict:
    attacks = {}
    mutations = {
        "strict_depth": ("strict_refinement_depth", -1),
        "trajectory": ("class_count_trajectory", [999]),
        "partition_hash": ("partition_hash", "0" * 64),
        "transition_hash": ("transition_pair_hash", "f" * 64),
        "hidden_batch": ("hidden_batch", "INVALID"),
        "depth_six_mass": ("depth_six_changed_ordered_pair_count", -1),
    }
    for name, (field, value) in mutations.items():
        mutated = copy.deepcopy(julia_result)
        records(mutated)[0][field] = value
        comparison = compare(jax_result, mutated)
        attacks[name] = {
            "field": field,
            "detected": not comparison["all_fields_match"],
            "reported_mismatches": comparison["mismatch_count_by_field"][field],
        }
    duplicated = copy.deepcopy(julia_result)
    duplicate_records = records(duplicated)
    duplicate_records[1]["rule_a"] = duplicate_records[0]["rule_a"]
    duplicate_records[1]["rule_b"] = duplicate_records[0]["rule_b"]
    duplicate_comparison = compare(jax_result, duplicated)
    attacks["duplicate_pair"] = {
        "field": "rule_pair_universe",
        "detected": not duplicate_comparison["all_fields_match"]
        and not duplicate_comparison["julia_pair_universe_exact"],
        "reported_mismatches": duplicate_comparison["mismatch_count_by_field"][
            "rule_a"
        ]
        + duplicate_comparison["mismatch_count_by_field"]["rule_b"],
    }
    return attacks


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    jax_result = json.loads(JAX_PATH.read_text())
    julia_result = json.loads(JULIA_PATH.read_text())
    comparison = compare(jax_result, julia_result)
    attacks = mutation_attacks(jax_result, julia_result)
    admission = v2_admission(records(jax_result), spec)
    tests = {
        "C1_engine_receipts_green": jax_result.get("all_pass") is True
        and julia_result.get("all_pass") is True,
        "C2_engine_identity": jax_result.get("sim_id") == SIM_ID
        and julia_result.get("sim_id") == SIM_ID
        and jax_result.get("engine") == "jax"
        and julia_result.get("engine") == "julia",
        "C3_no_peer_reads": not jax_result.get("peer_result_files_read")
        and not julia_result.get("peer_result_files_read")
        and julia_result.get("reads_peer_result") in (False, None),
        "C4_all_32640_records_match": comparison["all_fields_match"],
        "C5_all_mutation_attacks_detected": all(
            attack["detected"] and attack["reported_mismatches"] >= 1
            for attack in attacks.values()
        ),
    }
    all_pass = all(tests.values())
    result = {
        "schema": "codex_ratchet.eca_behavioral_refinement_depth_census_v1.validation.v1",
        "sim_id": SIM_ID,
        "engine": "independent_closed_receipt_controller",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "input_hashes": {
            "spec_sha256": sha256_file(SPEC_PATH),
            "jax_result_sha256": sha256_file(JAX_PATH),
            "julia_result_sha256": sha256_file(JULIA_PATH),
        },
        "comparison": comparison,
        "mutation_attacks": attacks,
        "tests": tests,
        "all_pass": all_pass,
        "all_scientific_gates_pass": all_pass,
        "result_label": spec["allowed_claim_label_if_all_gates_pass"]
        if all_pass
        else "CROSS_RUNTIME_N9_CENSUS_RED",
        "downstream_v2_admission": admission if all_pass else {"not_evaluated": True},
        "claim_ceiling": "exact finite full-state N9 ECA refinement-depth census under the frozen probe; V2 admission is only permission to write a separate card",
        "blocked_consumers": spec["blocked_consumers"],
    }
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "result_label": result["result_label"],
                "downstream_v2_admission": result["downstream_v2_admission"],
            },
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
