#!/usr/bin/env python3
"""Validate the learned stage-interior artifact without promoting its science."""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
SOURCE_PATH = HERE / "dual_ratchet_stage_interior_learning_v0_pytorch.py"
RESULT_PATH = HERE / "results" / "dual_ratchet_stage_interior_learning_v0_pytorch_results.json"
JAX_SOURCE_PATH = HERE / "dual_ratchet_stage_interior_learning_v0_jax_sweep.py"
JAX_RESULT_PATH = (
    HERE / "results" / "dual_ratchet_stage_interior_learning_v0_jax_sweep_results.json"
)
VALIDATION_PATH = HERE / "results" / "dual_ratchet_stage_interior_learning_v0_validation.json"
OPS = {"Ti", "Te", "Fi", "Fe"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any] | list[dict[str, Any]]:
    return json.loads(path.read_text())


def main() -> int:
    spec = load(SPEC_PATH)
    result = load(RESULT_PATH)
    jax_result = load(JAX_RESULT_PATH)
    if not all(isinstance(value, dict) for value in (spec, result, jax_result)):
        raise TypeError("spec and results must be JSON objects")

    schedule_path = REPO / spec["source_schedule"]
    dependency_path = REPO / spec["operator_basis_dependency"]
    base_path = (
        REPO
        / "system_v7"
        / "constraint_core"
        / "sims_and_scripts"
        / "stage_interior_architecture_tournament_sim.py"
    )
    source_schedule = load(schedule_path)
    if not isinstance(source_schedule, list):
        raise TypeError("source schedule must be a JSON list")
    source_by_slot = {row["slot_id"]: row for row in source_schedule}

    expected_cycles = {
        ("Ti",) + tail for tail in itertools.permutations(("Te", "Fi", "Fe"))
    }
    runs = result["runs"]
    run_keys = {
        (row["engine"], tuple(row["cycle"]), int(row["seed"]))
        for row in runs
    }
    expected_run_keys = {
        (engine, cycle, int(seed))
        for engine in ("Type1_left", "Type2_right")
        for cycle in expected_cycles
        for seed in spec["seeds"]
    }

    microsteps = result["candidate_64_microstep_schedule"]
    by_slot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in microsteps:
        by_slot[row["slot_id"]].append(row)
    slot_shapes_ok = True
    for slot_id, rows in by_slot.items():
        source = source_by_slot.get(slot_id)
        ordered = sorted(rows, key=lambda row: int(row["position"]))
        if source is None:
            slot_shapes_ok = False
            continue
        slot_shapes_ok = slot_shapes_ok and (
            len(ordered) == 4
            and {row["operator"] for row in ordered} == OPS
            and {row["axis6_sign"] for row in ordered} == {source["axis6_sign"]}
            and ordered[0]["operator"] == source["canonical_operator"]
            and ordered[0]["native_phase_anchor"] is True
            and sum(bool(row["native_phase_anchor"]) for row in ordered) == 1
            and [int(row["position"]) for row in ordered] == [1, 2, 3, 4]
        )

    selected_stability = all(
        engine["selected_cycle_stable_across_seeds"]
        == all(row["matches_aggregate_selection"] for row in engine["seed_winners"])
        for engine in result["engine_selections"].values()
    )
    recomputed_local_pass = all(bool(value) for value in result["checks"].values())
    expected_verdict = (
        "finite_learned_stage_interior_candidate_only"
        if recomputed_local_pass
        else "stage_interior_candidate_failed_or_remains_underdetermined"
    )
    source_hash_paths = [SPEC_PATH, SOURCE_PATH, schedule_path, dependency_path, base_path]
    source_hashes_match = all(
        result["source_hashes"].get(str(path.relative_to(REPO))) == digest(path)
        for path in source_hash_paths
    )
    jax_source_hash_paths = [
        SPEC_PATH,
        SOURCE_PATH,
        RESULT_PATH,
        JAX_SOURCE_PATH,
        schedule_path,
        dependency_path,
        base_path,
    ]
    jax_source_hashes_match = all(
        jax_result["source_hashes"].get(str(path.relative_to(REPO))) == digest(path)
        for path in jax_source_hash_paths
    )
    jax_type1 = jax_result["ranking_stability"]["rankings"]["Type1_left"][
        "all_scenarios"
    ]
    jax_type2 = jax_result["ranking_stability"]["rankings"]["Type2_right"][
        "all_scenarios"
    ]

    engine_counts = Counter(row["engine"] for row in microsteps)
    checks = {
        "scratch_ceiling_is_fail_closed": result["classification"] == "scratch_diagnostic"
        and result["promotion_allowed"] is False
        and result["formal_admission_allowed"] is False
        and result["stage_movement_allowed"] is False,
        "source_hashes_match": source_hashes_match,
        "jax_source_hashes_match": jax_source_hashes_match,
        "exact_36_run_matrix_present": len(runs) == 36 and run_keys == expected_run_keys,
        "all_run_weights_are_bounded_native_first": all(
            len(row["learned_weights_native_first"]) == 4
            and row["learned_weights_native_first"][0] == 1.0
            and all(0.0 < float(weight) <= 1.0 for weight in row["learned_weights_native_first"])
            for row in runs
        ),
        "exact_64_microstep_candidate_present": result["candidate_microstep_count"] == 64
        and len(microsteps) == 64
        and len({row["microstep_id"] for row in microsteps}) == 64,
        "all_16_source_slots_realized": set(by_slot) == set(source_by_slot) and len(by_slot) == 16,
        "each_slot_has_four_operators_one_sign_and_native_phase": slot_shapes_ok,
        "each_engine_has_32_microsteps": engine_counts
        == Counter({"Type1_left": 32, "Type2_right": 32}),
        "selection_stability_fields_are_coherent": selected_stability,
        "engine_cycle_relation_is_observational_not_gating": result["engine_cycle_relation"]["gating"]
        is False
        and result["engine_cycle_relation"]["same_selected_cycle"]
        == (len({tuple(cycle) for cycle in result["selected_cycles"].values()}) == 1),
        "local_gate_recomputes_from_checks": result["local_stage_interior_candidate_pass"]
        is recomputed_local_pass,
        "scientific_verdict_matches_local_gate": result["scientific_verdict"] == expected_verdict,
        "global_claims_remain_blocked": result["global_per_stage_four_substages_earned"] is False
        and result["axis0_alignment_earned"] is False
        and result["universal_four_operator_basis_earned"] is False,
        "jax_receipt_is_fail_closed": jax_result["classification"] == "scratch_diagnostic"
        and jax_result["promotion_allowed"] is False
        and jax_result["formal_admission_allowed"] is False
        and jax_result["stage_movement_allowed"] is False,
        "jax_declared_sweep_size_is_present": jax_result["jax"]["batched_scenario_count"]
        == 1080
        and jax_result["jax"]["batched_cycle_score_count"] == 6480,
        "jax_controls_all_pass": jax_result["controls"]["all_pass"] is True
        and len(jax_result["controls"]["checks"]) == 18
        and all(jax_result["controls"]["checks"].values()),
        "jax_peer_read_ceiling_is_explicit": jax_result["jax"]["reads_peer_result"] is True
        and jax_result["jax"]["independent_scoring_implementation"] is True
        and jax_result["jax"]["peer_read_ceiling"]
        == "robustness_consumer_only_not_independent_learning_or_cross_engine_confirmation",
        "jax_type1_candidate_survives_declared_sweep": jax_type1[
            "reference_cycle_wins_every_scenario"
        ]
        is True
        and jax_type1["tie_count"] == 0
        and jax_type1["winner_counts"]["Ti>Fe>Fi>Te"] == 540,
        "jax_type2_candidate_fails_declared_sweep": jax_type2[
            "reference_cycle_wins_every_scenario"
        ]
        is False
        and jax_type2["tie_count"] == 8
        and jax_type2["winner_counts"]["Ti>Te>Fi>Fe"] == 385,
        "jax_scientific_failure_is_recorded": jax_result["ranking_stability"]["pass"]
        is False
        and jax_result["verdict_pass"] is False
        and jax_result["verdict"]
        == "cycle_ranking_unstable_or_tied_under_declared_jax_sweep",
        "jax_global_claims_remain_blocked": jax_result[
            "global_per_stage_four_substages_earned"
        ]
        is False
        and jax_result["axis0_alignment_earned"] is False
        and jax_result["universal_four_operator_basis_earned"] is False
        and jax_result["perception_claim_earned"] is False
        and jax_result["object_claim_earned"] is False,
    }
    all_pass = all(checks.values())
    receipt = {
        "schema": "codex_ratchet.dual_ratchet_stage_interior_learning_v0.validation.v1",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "artifact_validation_all_pass": all_pass,
        "scientific_candidate_pass": result["local_stage_interior_candidate_pass"],
        "scientific_verdict": result["scientific_verdict"],
        "jax_ranking_stability_pass": jax_result["ranking_stability"]["pass"],
        "jax_verdict": jax_result["verdict"],
        "checks": checks,
        "source_hashes": {
            str(SPEC_PATH.relative_to(REPO)): digest(SPEC_PATH),
            str(SOURCE_PATH.relative_to(REPO)): digest(SOURCE_PATH),
            str(RESULT_PATH.relative_to(REPO)): digest(RESULT_PATH),
            str(JAX_SOURCE_PATH.relative_to(REPO)): digest(JAX_SOURCE_PATH),
            str(JAX_RESULT_PATH.relative_to(REPO)): digest(JAX_RESULT_PATH),
        },
        "claim_ceiling": result["claim_ceiling"],
        "blocked_consumers": result["blocked_consumers"],
    }
    VALIDATION_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result_path": str(VALIDATION_PATH), **receipt}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
