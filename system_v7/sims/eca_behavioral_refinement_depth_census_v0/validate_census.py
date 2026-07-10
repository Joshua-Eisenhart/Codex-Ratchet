#!/usr/bin/env python3
"""Closed-receipt controller for the cross-runtime ECA depth census."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


SIM_ID = "eca_behavioral_refinement_depth_census_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
JAX_PATH = RESULTS / f"{SIM_ID}_jax_results.json"
JULIA_PATH = RESULTS / f"{SIM_ID}_julia_results.json"
OUTPUT_PATH = RESULTS / f"{SIM_ID}_validation.json"
EXPECTED_RINGS = (6, 7, 8)
EXPECTED_PAIR_COUNT = 32640
LEDGER_FIELDS = (
    "rule_a",
    "rule_b",
    "strict_refinement_depth",
    "first_equality_round",
    "class_count_trajectory",
    "surviving_ordered_pair_count_trajectory",
    "stable_class_count",
    "partition_hash",
    "transition_pair_hash",
)

TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Closed JSON parsing, fieldwise comparison, mutation attacks, and SHA receipts.",
    },
    "numpy": {"used": False, "reason": "No numerical reconstruction occurs in the controller."},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "numpy": None}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_receipts(jax_result: dict, julia_result: dict) -> dict:
    mismatches = {field: 0 for field in LEDGER_FIELDS}
    ring_receipts = []
    jax_rings = {ring["ring_size"]: ring for ring in jax_result.get("rings", [])}
    julia_rings = {ring["ring_size"]: ring for ring in julia_result.get("rings", [])}

    for ring_size in EXPECTED_RINGS:
        jax_ring = jax_rings.get(ring_size, {})
        julia_ring = julia_rings.get(ring_size, {})
        jax_ledger = jax_ring.get("pair_ledger", [])
        julia_ledger = julia_ring.get("pairs", [])
        compared = min(len(jax_ledger), len(julia_ledger))
        local = {field: 0 for field in LEDGER_FIELDS}
        first_mismatch = None
        for index in range(compared):
            for field in LEDGER_FIELDS:
                if jax_ledger[index].get(field) != julia_ledger[index].get(field):
                    local[field] += 1
                    mismatches[field] += 1
                    if first_mismatch is None:
                        first_mismatch = {
                            "index": index,
                            "field": field,
                            "jax": jax_ledger[index].get(field),
                            "julia": julia_ledger[index].get(field),
                        }
        count_match = len(jax_ledger) == len(julia_ledger) == EXPECTED_PAIR_COUNT
        histogram_match = (
            jax_ring.get("strict_refinement_depth_histogram")
            == julia_ring.get("strict_refinement_depth_histogram")
        )
        maximum_match = (
            jax_ring.get("maximum_strict_refinement_depth")
            == julia_ring.get("maximum_strict_refinement_depth")
        )
        ring_receipts.append(
            {
                "ring_size": ring_size,
                "compared_pair_count": compared,
                "pair_count_match": count_match,
                "histogram_match": histogram_match,
                "maximum_depth_match": maximum_match,
                "mismatch_count_by_field": local,
                "first_mismatch": first_mismatch,
                "all_fields_match": count_match
                and histogram_match
                and maximum_match
                and not any(local.values()),
            }
        )

    return {
        "ring_receipts": ring_receipts,
        "total_compared_pair_count": sum(r["compared_pair_count"] for r in ring_receipts),
        "mismatch_count_by_field": mismatches,
        "all_fields_match": all(r["all_fields_match"] for r in ring_receipts),
    }


def mutation_tests(jax_result: dict, julia_result: dict) -> dict:
    tests = {}
    mutations = {
        "strict_depth": ("strict_refinement_depth", -1),
        "class_trajectory": ("class_count_trajectory", [999]),
        "partition_hash": ("partition_hash", "0" * 64),
        "transition_hash": ("transition_pair_hash", "f" * 64),
    }
    for name, (field, value) in mutations.items():
        mutated = copy.deepcopy(julia_result)
        mutated["rings"][0]["pairs"][0][field] = value
        comparison = compare_receipts(jax_result, mutated)
        tests[name] = {
            "mutated_field": field,
            "detected": not comparison["all_fields_match"],
            "reported_mismatch_count": comparison["mismatch_count_by_field"][field],
        }
    return tests


def main() -> int:
    jax_result = json.loads(JAX_PATH.read_text())
    julia_result = json.loads(JULIA_PATH.read_text())
    comparison = compare_receipts(jax_result, julia_result)
    attacks = mutation_tests(jax_result, julia_result)
    tests = {
        "C1_sim_ids_and_engines": jax_result.get("sim_id") == SIM_ID
        and julia_result.get("sim_id") == SIM_ID
        and jax_result.get("engine") == "jax"
        and julia_result.get("engine") == "julia",
        "C2_independent_engine_receipts_green": jax_result.get("all_pass") is True
        and julia_result.get("all_pass") is True,
        "C3_no_peer_reads_in_engine_lanes": not jax_result.get("peer_result_files_read")
        and not julia_result.get("peer_result_files_read")
        and julia_result.get("reads_peer_result") is False,
        "C4_all_97920_ledgers_match": comparison["all_fields_match"]
        and comparison["total_compared_pair_count"] == 97920,
        "C5_all_corruption_attacks_detected": all(
            attack["detected"] and attack["reported_mismatch_count"] == 1
            for attack in attacks.values()
        ),
        "C6_expected_maximum_depths": [
            ring["maximum_strict_refinement_depth"] for ring in jax_result["rings"]
        ]
        == [3, 4, 6],
    }
    all_pass = all(tests.values())
    receipt = {
        "schema": "codex_ratchet.eca_behavioral_refinement_depth_census_v0.validation.v1",
        "sim_id": SIM_ID,
        "engine": "independent_closed_receipt_controller",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "input_files": {
            "jax": str(JAX_PATH.relative_to(HERE.parents[2])),
            "julia": str(JULIA_PATH.relative_to(HERE.parents[2])),
        },
        "input_hashes": {
            "jax_sha256": sha256_file(JAX_PATH),
            "julia_sha256": sha256_file(JULIA_PATH),
        },
        "comparison": comparison,
        "corruption_attacks": attacks,
        "tests": tests,
        "all_pass": all_pass,
        "all_scientific_gates_pass": all_pass,
        "result_label": "EXACT_CROSS_RUNTIME_FINITE_ECA_REFINEMENT_DEPTH_CENSUS_N6_TO_N8"
        if all_pass
        else "CROSS_RUNTIME_CENSUS_RED",
        "claim_ceiling": "exact full-state finite ECA pair-refinement depth census on rings 6 through 8 under the fixed weight/domain-wall probe",
        "blocked_consumers": [
            "learned perception",
            "QIT engine stages or substages",
            "general attractor claims",
            "MMMs and ontology admission",
            "physics, life, or consciousness claims",
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "tests": tests, "result_label": receipt["result_label"]}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
