#!/usr/bin/env python3
"""Independent controller for the finite dual-ratchet object battery."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


HERE = Path(__file__).resolve().parent
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "Independent RNG reconstruction, exact finite refinement, hashing, and corruption tests."},
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}
REPO_ROOT = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
JAX_SOURCE = HERE / "run_jax.py"
JULIA_SOURCE = HERE / "run_julia.jl"
JAX_RESULT = HERE / "results" / "finite_dual_ratchet_object_formation_v0_jax_results.json"
JULIA_RESULT = HERE / "results" / "finite_dual_ratchet_object_formation_v0_julia_results.json"
DEFAULT_OUTPUT = HERE / "results" / "finite_dual_ratchet_object_formation_v0_validation.json"

EXPECTED_CENSUS = {
    "all": {"1": 4636, "2": 14656, "3": 692, "4": 16},
    "non_discrete": {"1": 618, "2": 1523, "3": 75, "4": 3},
}
TARGET_SEEDS = [8565, 10288, 19937]
EXPECTED_CONTROL_DEPTHS = {
    1: [4, 5, 8],
    2: [1, 2, 3],
    3: [11, 19, 37],
}
LOCAL_GATES = [f"G{index}_{name}" for index, name in (
    (1, "census_exact"),
    (2, "target_depth_exactly_four"),
    (3, "cross_view_relation_exact"),
    (4, "unlabeled_quotient_isomorphic"),
    (5, "probe_erasure_changes_relation"),
    (6, "depth3_truncation_fails_all_targets"),
    (7, "quotient_congruent_and_at_most_15_classes"),
    (8, "all_corruptions_rejected"),
)]
GREEN = "BOUNDED_EXACT_FOUR_ROLE_OBJECT_FORMATION_ON_FROZEN_FINITE_AUTOMATA"
RED = "FOUR_ROLE_OBJECT_FORMATION_NOT_ESTABLISHED"
AUDIT_CEILING = "EXACT_JULIA_JAX_PARITY_FOR_PROBE_RELATIVE_PARTITION_REFINEMENT_ON_THREE_POST_CENSUS_SELECTED_FINITE_AUTOMATA"


class ValidationError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValidationError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain one object")
    return value


def require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{path}: {message}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalize(values: Sequence[Any]) -> list[int]:
    seen: dict[Any, int] = {}
    labels: list[int] = []
    for value in values:
        if value not in seen:
            seen[value] = len(seen)
        labels.append(seen[value])
    return labels


def probe(state: int) -> int:
    return ((state.bit_count() & 1) << 1) | (state & 1)


def transitions(seed: int, state_count: int = 16) -> list[list[int]]:
    generator = random.Random(seed)
    return [
        [generator.randrange(state_count) for _ in range(state_count)]
        for _ in range(2)
    ]


def refine(labels: Sequence[int], actions: Sequence[Sequence[int]]) -> list[int]:
    return canonicalize([
        (labels[state], labels[actions[0][state]], labels[actions[1][state]])
        for state in range(len(labels))
    ])


def stable_partition(
    actions: Sequence[Sequence[int]], initial: Sequence[int]
) -> tuple[list[int], int, list[int]]:
    labels = canonicalize(initial)
    history = [len(set(labels))]
    depth = 0
    for _ in range(len(labels) - 1):
        next_labels = refine(labels, actions)
        history.append(len(set(next_labels)))
        if next_labels == labels:
            return labels, depth, history
        labels = next_labels
        depth += 1
    raise ValidationError("controller refinement did not stabilize")


def lift(actions: Sequence[Sequence[int]]) -> list[list[int]]:
    return [
        [actions[action][state // 4] * 4 + state % 4 for state in range(64)]
        for action in range(2)
    ]


def relation_hash(labels: Sequence[int]) -> str:
    payload = bytes(int(left == right) for left in labels for right in labels)
    return hashlib.sha256(payload).hexdigest()


def recompute_controller_truth() -> dict[str, Any]:
    all_depths: Counter[int] = Counter()
    non_discrete: Counter[int] = Counter()
    fixtures: dict[int, dict[str, Any]] = {}
    fixture_set = set(TARGET_SEEDS)
    for seeds in EXPECTED_CONTROL_DEPTHS.values():
        fixture_set.update(seeds)
    for seed in range(1, 20001):
        labels, depth, history = stable_partition(
            transitions(seed), [probe(state) for state in range(16)]
        )
        all_depths[depth] += 1
        if len(set(labels)) < 16:
            non_discrete[depth] += 1
        if seed in fixture_set:
            lifted_labels, lifted_depth, lifted_history = stable_partition(
                lift(transitions(seed)), [probe(state // 4) for state in range(64)]
            )
            fixtures[seed] = {
                "base_depth": depth,
                "base_class_count": len(set(labels)),
                "base_history": history,
                "lifted_depth": lifted_depth,
                "lifted_class_count": len(set(lifted_labels)),
                "lifted_history": lifted_history,
                "relation_sha256": relation_hash(lifted_labels),
            }
    return {
        "census": {
            "all": {str(key): all_depths[key] for key in sorted(all_depths)},
            "non_discrete": {str(key): non_discrete[key] for key in sorted(non_discrete)},
        },
        "fixtures": fixtures,
    }


def validate_packet(
    spec: dict[str, Any], prereg: dict[str, Any], jax: dict[str, Any], julia: dict[str, Any],
    truth: dict[str, Any],
) -> dict[str, Any]:
    require(spec["accepted_green_ceiling"] == GREEN, "spec", "green ceiling drift")
    require(spec["accepted_red_ceiling"] == RED, "spec", "red ceiling drift")
    require(prereg["spec_sha256"] == sha256(SPEC_PATH), "prereg", "spec hash mismatch")
    require(jax["source_sha256"] == sha256(JAX_SOURCE), "jax.source_sha256", "source mismatch")
    require(julia["source"]["sha256"] == sha256(JULIA_SOURCE), "julia.source.sha256", "source mismatch")
    require(jax["spec_sha256"] == prereg["spec_sha256"], "jax.spec_sha256", "frozen binding mismatch")
    require(julia["source"]["spec_sha256"] == prereg["spec_sha256"], "julia.source.spec_sha256", "frozen binding mismatch")
    require(jax["preregistration_sha256"] == sha256(PREREG_PATH), "jax.preregistration_sha256", "binding mismatch")
    require(julia["source"]["preregistration_sha256"] == sha256(PREREG_PATH), "julia.source.preregistration_sha256", "binding mismatch")
    require(jax["reads_peer_result"] is False, "jax.reads_peer_result", "peer read forbidden")
    require(julia["julia"]["reads_peer_result"] is False, "julia.reads_peer_result", "peer read forbidden")
    require(jax["numpy_imported_by_source"] is False, "jax.numpy", "NumPy claim-path import")
    require(jax["all_pass"] is False, "jax.all_pass", "must fail closed before controller")
    require(julia["all_pass"] is False, "julia.all_pass", "must fail closed before controller")
    require(jax["all_local_gates_pass"] is True, "jax.local", "local gates red")
    require(julia["local_all_pass"] is True, "julia.local", "local gates red")

    require(truth["census"] == EXPECTED_CENSUS, "controller.census", "frozen census mismatch")
    require(jax["depth_census"]["observed"] == truth["census"], "jax.depth_census", "controller mismatch")
    require(julia["depth_census"]["all"] == truth["census"]["all"], "julia.depth_census.all", "controller mismatch")
    require(julia["depth_census"]["non_discrete"] == truth["census"]["non_discrete"], "julia.depth_census.non_discrete", "controller mismatch")

    for gate in LOCAL_GATES:
        require(jax["gates"].get(gate) is True, f"jax.gates.{gate}", "not true")
        require(julia["gates"].get(gate) is True, f"julia.gates.{gate}", "not true")
    require(jax["gates"].get("G9_julia_jax_exact_parity") is None, "jax.G9", "builder self-graded G9")
    require(julia["gates"].get("G9_julia_jax_exact_parity") is None, "julia.G9", "builder self-graded G9")

    jax_targets = {row["seed"]: row for row in jax["target_fixtures"]}
    julia_targets = {row["seed"]: row for row in julia["fixtures"]["targets_depth4_non_discrete"]}
    require(sorted(jax_targets) == TARGET_SEEDS, "jax.targets", "target seeds drifted")
    require(sorted(julia_targets) == TARGET_SEEDS, "julia.targets", "target seeds drifted")
    for seed in TARGET_SEEDS:
        exact = truth["fixtures"][seed]
        jax_row = jax_targets[seed]
        julia_row = julia_targets[seed]
        require(exact["base_depth"] == 4, f"controller.target.{seed}", "not depth four")
        require(exact["lifted_class_count"] == 15, f"controller.target.{seed}", "not 15 classes")
        require(jax_row["strict_refinement_depth"] == exact["lifted_depth"], f"jax.target.{seed}", "depth mismatch")
        require(jax_row["stable_lifted_class_count"] == 15, f"jax.target.{seed}", "class mismatch")
        require(jax_row["stable_relation_sha256"] == exact["relation_sha256"], f"jax.target.{seed}", "relation mismatch")
        require(julia_row["lifted_refinement_depth"] == exact["lifted_depth"], f"julia.target.{seed}", "depth mismatch")
        require(julia_row["lifted_class_count"] == 15, f"julia.target.{seed}", "class mismatch")
        require(len(jax_row["views"]) == 5, f"jax.target.{seed}.views", "expected five")
        require(len(julia_row["perspectives"]) == 5, f"julia.target.{seed}.views", "expected five")
        for view in jax_row["views"]:
            require(view["full_relation_pullback_exact"] is True, f"jax.target.{seed}.view", "pullback failed")
            require(view["color_preserving_directed_quotient_isomorphic"] is True, f"jax.target.{seed}.view", "iso failed")
            require(view["corruption_rejected_by_known_projection_gate"] is True, f"jax.target.{seed}.view", "corruption accepted")
        for view in julia_row["perspectives"]:
            require(view["known_bijection_pullback_exact"] is True, f"julia.target.{seed}.view", "pullback failed")
            require(view["graphs_vf2_color_preserving_isomorphic"] is True, f"julia.target.{seed}.view", "iso failed")
            require(view["corruption"]["rejected"] is True, f"julia.target.{seed}.view", "corruption accepted")

    for depth, seeds in EXPECTED_CONTROL_DEPTHS.items():
        for seed in seeds:
            require(truth["fixtures"][seed]["base_depth"] == depth, f"controller.control.{seed}", "depth mislabeled")
            require(jax["fixture_depth_controls"][str(seed)]["depth"] == depth, f"jax.control.{seed}", "depth mismatch")

    for role, passed in jax["role_controls"].items():
        require(passed is True, f"jax.role_controls.{role}", "removal tooth failed")
    for role, receipt in julia["four_role_ablations"].items():
        require(receipt["tooth_pass"] is True, f"julia.four_role_ablations.{role}", "removal tooth failed")
    require(set(julia["four_role_ablations"]) == {"measure", "distinguish", "quotient", "gate"}, "julia.roles", "role set drifted")
    require(julia["blocked_consumers"] == spec["blocked_consumers"], "julia.blocked_consumers", "claim boundary drifted")

    return {
        "census": truth["census"],
        "target_depths": {str(seed): truth["fixtures"][seed]["lifted_depth"] for seed in TARGET_SEEDS},
        "target_class_counts": {str(seed): truth["fixtures"][seed]["lifted_class_count"] for seed in TARGET_SEEDS},
        "target_relation_sha256": {str(seed): truth["fixtures"][seed]["relation_sha256"] for seed in TARGET_SEEDS},
        "perspectives_checked_per_target": 5,
        "corruptions_rejected": 15,
        "G9_julia_jax_exact_parity": True,
    }


def corruption_tests(
    spec: dict[str, Any], prereg: dict[str, Any], jax: dict[str, Any], julia: dict[str, Any], truth: dict[str, Any]
) -> dict[str, Any]:
    cases: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    mutated_jax = copy.deepcopy(jax)
    mutated_jax["source_sha256"] = "0" * 64
    cases["jax_source_hash"] = (mutated_jax, julia)
    mutated_julia = copy.deepcopy(julia)
    mutated_julia["depth_census"]["all"]["4"] = 17
    cases["julia_census"] = (jax, mutated_julia)
    mutated_jax_gate = copy.deepcopy(jax)
    mutated_jax_gate["gates"]["G8_all_corruptions_rejected"] = False
    cases["jax_gate"] = (mutated_jax_gate, julia)
    mutated_julia_boundary = copy.deepcopy(julia)
    mutated_julia_boundary["blocked_consumers"] = mutated_julia_boundary["blocked_consumers"][:-1]
    cases["claim_boundary"] = (jax, mutated_julia_boundary)
    results: dict[str, Any] = {}
    for name, (candidate_jax, candidate_julia) in cases.items():
        try:
            validate_packet(spec, prereg, candidate_jax, candidate_julia, truth)
        except ValidationError as exc:
            results[name] = {"rejected": True, "reason": str(exc)}
        else:
            results[name] = {"rejected": False, "reason": "corruption accepted"}
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    spec = load_strict(SPEC_PATH)
    prereg = load_strict(PREREG_PATH)
    jax = load_strict(JAX_RESULT)
    julia = load_strict(JULIA_RESULT)
    truth = recompute_controller_truth()
    try:
        parity = validate_packet(spec, prereg, jax, julia, truth)
        corruptions = corruption_tests(spec, prereg, jax, julia, truth)
        corruption_pass = all(row["rejected"] for row in corruptions.values())
        require(corruption_pass, "corruption_tests", "one or more corruptions accepted")
        result = {
            "schema": "codex_ratchet.finite_dual_ratchet_object_formation_v0.controller_validation.v1",
            "sim_id": spec["sim_id"],
            "classification": "scratch_diagnostic",
            "artifact_validation_all_pass": True,
            "all_scientific_gates_pass": False,
            "accepted_claim_label": AUDIT_CEILING,
            "provisional_pre_fabrication_label": GREEN,
            "found_fabrication": True,
            "scientific_red_gates": [
                "targets_are_all_post_census_selected_non_discrete_depth_four_cases",
                "perspectives_are_exact_generated_relabelings_with_known_bijections",
                "copy_lift_and_64_to_15_compression_are_by_construction",
                "corruption_rejection_compares_a_forced_mutation_to_the_trusted_original",
                "controller_does_not_independently_recompute_all_G3_through_G8_scientific_controls",
            ],
            "G9": parity,
            "corruption_tests": corruptions,
            "four_count_forced": False,
            "four_count_interpretation": "selected depth-four stress fixtures inside a census dominated by depths one and two; no universal or QIT four-count derivation",
            "T9_output_vector": {
                "role_contribution": "candidate role checks execute, but fabrication audit rejects necessity and object-formation language",
                "runtime_replaceability": "unearned; Julia and JAX independently implement overlapping exact roles",
                "resource_advantage": "unearned; no equal-budget replacement matrix",
                "diversity_gain": "independent RNG and graph implementations agree, but unique-fault detection was not preregistered",
                "claim_ceiling": AUDIT_CEILING,
            },
            "blocked_consumers": spec["blocked_consumers"],
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "source_result_bindings": {
                "jax_source_sha256": sha256(JAX_SOURCE),
                "julia_source_sha256": sha256(JULIA_SOURCE),
                "jax_result_sha256": sha256(JAX_RESULT),
                "julia_result_sha256": sha256(JULIA_RESULT),
                "spec_sha256": sha256(SPEC_PATH),
                "preregistration_sha256": sha256(PREREG_PATH),
                "validator_source_sha256": sha256(Path(__file__).resolve()),
            },
        }
    except ValidationError as exc:
        result = {
            "schema": "codex_ratchet.finite_dual_ratchet_object_formation_v0.controller_validation.v1",
            "sim_id": "finite_dual_ratchet_object_formation_v0",
            "classification": "scratch_diagnostic",
            "artifact_validation_all_pass": False,
            "all_scientific_gates_pass": False,
            "accepted_claim_label": RED,
            "error": str(exc),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["artifact_validation_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
