#!/usr/bin/env python3
"""Bounded finite identification diagnostic for adaptive observation policies.

This script intentionally stays a scratch diagnostic.  It compares a fixed,
prior-designed query schedule (Policy A) against a greedy version-space policy
(Policy B) on finite Boolean observation arenas.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path


RNG_SEED = 0


class Arena:
    """Finite candidate/query table with deterministic, structural labels."""

    def __init__(
        self,
        name,
        description,
        candidate_records,
        query_records,
        answer_matrix,
        budget,
    ):
        self.name = name
        self.description = description
        self.candidate_records = tuple(candidate_records)
        self.query_records = tuple(query_records)
        self.answer_matrix = tuple(tuple(row) for row in answer_matrix)
        self.budget = budget

        if len(self.candidate_records) != len(self.answer_matrix):
            raise ValueError("candidate records and answer rows must agree")
        if not self.candidate_records:
            raise ValueError("an arena needs at least one candidate")
        expected_queries = len(self.query_records)
        if any(len(row) != expected_queries for row in self.answer_matrix):
            raise ValueError("every answer row must cover the query pool")
        if any(answer not in (0, 1) for row in self.answer_matrix for answer in row):
            raise ValueError("this diagnostic accepts Boolean observations only")


def answer_classes(answer_matrix, version_space, query_index):
    """Return answer classes in sorted answer-value order."""
    classes = {}
    for candidate_index in sorted(version_space):
        answer = answer_matrix[candidate_index][query_index]
        classes.setdefault(answer, []).append(candidate_index)
    return tuple(tuple(classes[answer]) for answer in sorted(classes))


def choose_fixed_prior_queries(answer_matrix, query_count, budget):
    """Choose one non-adaptive schedule from the full prior before any play.

    This is a deterministic greedy *design* procedure.  It refines partitions
    of the original full candidate set while selecting the whole schedule, but
    it never observes a ground-truth answer and never branches on one.
    """
    all_candidates = tuple(range(len(answer_matrix)))
    all_queries = tuple(range(query_count))
    selected = []
    partitions = (all_candidates,)

    for _ in range(min(budget, query_count)):
        scored_choices = []
        for query_index in all_queries:
            if query_index in selected:
                continue
            refined_partitions = []
            for partition in partitions:
                refined_partitions.extend(
                    answer_classes(answer_matrix, partition, query_index)
                )
            largest_answer_class = max(len(partition) for partition in refined_partitions)
            scored_choices.append(
                (largest_answer_class, query_index, tuple(refined_partitions))
            )

        _, chosen_query, chosen_partitions = min(
            scored_choices, key=lambda item: (item[0], item[1])
        )
        selected.append(chosen_query)
        partitions = chosen_partitions

    return tuple(selected)


def run_fixed_policy(answer_matrix, ground_truth_index, fixed_queries, budget):
    """Execute Policy A's already-fixed schedule against one ground truth."""
    version_space = tuple(range(len(answer_matrix)))
    trace = []
    if len(version_space) == 1:
        return True, 0, tuple(trace)

    for step, query_index in enumerate(fixed_queries[:budget], start=1):
        trace.append(query_index)
        observed_answer = answer_matrix[ground_truth_index][query_index]
        version_space = tuple(
            candidate_index
            for candidate_index in version_space
            if answer_matrix[candidate_index][query_index] == observed_answer
        )
        if len(version_space) == 1:
            return True, step, tuple(trace)

    return False, budget + 1, tuple(trace)


def run_adaptive_policy(answer_matrix, ground_truth_index, query_count, budget):
    """Execute Policy B: minimize current largest answer class, then query index."""
    version_space = tuple(range(len(answer_matrix)))
    all_queries = tuple(range(query_count))
    asked_queries = ()
    trace = []
    score_ties = []

    if len(version_space) == 1:
        return True, 0, tuple(trace), tuple(score_ties)

    for step in range(1, budget + 1):
        available_queries = tuple(
            query_index for query_index in all_queries if query_index not in asked_queries
        )
        if not available_queries:
            break

        scored_queries = []
        for query_index in available_queries:
            classes = answer_classes(answer_matrix, version_space, query_index)
            largest_answer_class = max(len(answer_class) for answer_class in classes)
            scored_queries.append((largest_answer_class, query_index))

        lowest_score = min(score for score, _ in scored_queries)
        score_ties.append(all(score == lowest_score for score, _ in scored_queries))
        _, chosen_query = min(scored_queries, key=lambda item: (item[0], item[1]))
        trace.append(chosen_query)
        asked_queries = tuple(sorted(asked_queries + (chosen_query,)))

        observed_answer = answer_matrix[ground_truth_index][chosen_query]
        version_space = tuple(
            candidate_index
            for candidate_index in version_space
            if answer_matrix[candidate_index][chosen_query] == observed_answer
        )
        if len(version_space) == 1:
            return True, step, tuple(trace), tuple(score_ties)

    return False, budget + 1, tuple(trace), tuple(score_ties)


def summarize_policy(outcomes):
    query_counts = [outcome["queries_to_identification"] for outcome in outcomes]
    identified_count = sum(1 for outcome in outcomes if outcome["identified"])
    total = len(outcomes)
    return {
        "ident_rate": identified_count / total,
        "mean_q": sum(query_counts) / total,
        "max_q": max(query_counts),
        "identified_count": identified_count,
    }


def evaluate_arena(arena):
    """Run both policies for every candidate ground truth in one arena."""
    fixed_queries = choose_fixed_prior_queries(
        arena.answer_matrix, len(arena.query_records), arena.budget
    )
    policy_a_outcomes = []
    policy_b_outcomes = []
    per_ground_truth = []

    for candidate_index in range(len(arena.candidate_records)):
        a_identified, a_queries, _ = run_fixed_policy(
            arena.answer_matrix, candidate_index, fixed_queries, arena.budget
        )
        b_identified, b_queries, _, _ = run_adaptive_policy(
            arena.answer_matrix,
            candidate_index,
            len(arena.query_records),
            arena.budget,
        )
        policy_a_outcome = {
            "identified": a_identified,
            "queries_to_identification": a_queries,
        }
        policy_b_outcome = {
            "identified": b_identified,
            "queries_to_identification": b_queries,
        }
        policy_a_outcomes.append(policy_a_outcome)
        policy_b_outcomes.append(policy_b_outcome)
        per_ground_truth.append(
            {
                "candidate": arena.candidate_records[candidate_index],
                "A": policy_a_outcome,
                "B": policy_b_outcome,
            }
        )

    return {
        "description": arena.description,
        "candidate_count": len(arena.candidate_records),
        "query_pool_count": len(arena.query_records),
        "query_budget": arena.budget,
        "policy_a_fixed_query_indices": list(fixed_queries),
        "policy_a_fixed_queries": [arena.query_records[index] for index in fixed_queries],
        "policies": {
            "A": summarize_policy(policy_a_outcomes),
            "B": summarize_policy(policy_b_outcomes),
        },
        "per_ground_truth": per_ground_truth,
    }


def make_transition_table_arena(budget=4):
    """All Boolean tables f:{0,1}^2 -> {0,1}, queried by input pair."""
    input_pairs = tuple((left, right) for left in range(2) for right in range(2))
    candidate_records = []
    answer_matrix = []
    for table_index in range(16):
        outputs = tuple((table_index >> input_index) & 1 for input_index in range(4))
        candidate_records.append(
            {
                "table_index": table_index,
                "outputs_by_input_pair": list(outputs),
            }
        )
        answer_matrix.append(outputs)
    query_records = tuple({"input_pair": list(pair)} for pair in input_pairs)
    return Arena(
        "transition_table_exhaustive_k16",
        "Exhaustive Boolean transition tables f:{0,1}^2->{0,1} queried by input pair.",
        candidate_records,
        query_records,
        answer_matrix,
        budget,
    )


def eca_step(rule_number, configuration):
    """One periodic elementary-cellular-automaton step for an eight-bit state."""
    width = len(configuration)
    return tuple(
        (
            rule_number
            >> (
                (configuration[(cell_index - 1) % width] << 2)
                | (configuration[cell_index] << 1)
                | configuration[(cell_index + 1) % width]
            )
        )
        & 1
        for cell_index in range(width)
    )


def eca_trajectory(rule_number, initial_configuration, steps):
    states = [tuple(initial_configuration)]
    for _ in range(steps):
        states.append(eca_step(rule_number, states[-1]))
    return tuple(states)


def make_eca_arena(budget=5):
    """Seeded sample of 40 ECA rules with a finite structural query pool."""
    random.seed(RNG_SEED)
    rule_numbers = tuple(sorted(random.sample(range(256), 40)))
    initial_configurations = (
        (0, 0, 0, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 0, 0, 0),
        (0, 1, 0, 1, 0, 1, 0, 1),
        (1, 1, 0, 0, 1, 1, 0, 0),
    )
    width = 8
    max_time_step = 4
    query_specs = tuple(
        (initial_config_index, cell_index, time_step)
        for initial_config_index in range(len(initial_configurations))
        for cell_index in range(width)
        for time_step in range(1, max_time_step + 1)
    )
    query_records = tuple(
        {
            "initial_config_index": initial_config_index,
            "cell_index": cell_index,
            "time_step": time_step,
        }
        for initial_config_index, cell_index, time_step in query_specs
    )

    candidate_records = []
    answer_matrix = []
    for rule_number in rule_numbers:
        trajectories = tuple(
            eca_trajectory(rule_number, initial_configuration, max_time_step)
            for initial_configuration in initial_configurations
        )
        candidate_records.append({"rule_number": rule_number})
        answer_matrix.append(
            tuple(
                trajectories[initial_config_index][time_step][cell_index]
                for initial_config_index, cell_index, time_step in query_specs
            )
        )

    return Arena(
        "eca_seeded_k40",
        "Seed-0 sample of 40 distinct ECA rule numbers; periodic width-8 states and structural observation triples.",
        candidate_records,
        query_records,
        answer_matrix,
        budget,
    )


def make_null_arena(budget=3):
    """Symmetric three-bit negative where unused queries tie at every step."""
    candidate_bit_vectors = tuple(
        tuple((candidate_index >> (2 - bit_index)) & 1 for bit_index in range(3))
        for candidate_index in range(8)
    )
    candidate_records = tuple(
        {"bit_vector": list(bit_vector)} for bit_vector in candidate_bit_vectors
    )
    query_records = tuple({"coordinate": bit_index} for bit_index in range(3))
    answer_matrix = candidate_bit_vectors
    return Arena(
        "null_symmetric_bit_cube_k8",
        "All eight three-bit strings; every unused coordinate query exactly halves each reachable version-space subcube.",
        candidate_records,
        query_records,
        answer_matrix,
        budget,
    )


def make_single_candidate_boundary_arena():
    return Arena(
        "boundary_single_candidate_k1",
        "K=1 boundary: the initial version space is already identified.",
        ({"only_candidate": 0},),
        ({"unused_boundary_query": 0},),
        ((0,),),
        0,
    )


def make_zero_budget_boundary_arena():
    transition = make_transition_table_arena(budget=0)
    return Arena(
        "boundary_budget_zero_transition_k16",
        "Budget=0 boundary on the exhaustive K=16 transition-table family.",
        transition.candidate_records,
        transition.query_records,
        transition.answer_matrix,
        0,
    )


def run_degeneracy_check(null_arena):
    """Verify that all-score ties in the null arena reduce B to a fixed order."""
    fixed_order = choose_fixed_prior_queries(
        null_arena.answer_matrix, len(null_arena.query_records), null_arena.budget
    )
    candidate_checks = []
    all_scores_equal = True
    all_traces_match_fixed_order = True

    for candidate_index in range(len(null_arena.candidate_records)):
        _, _, trace, score_ties = run_adaptive_policy(
            null_arena.answer_matrix,
            candidate_index,
            len(null_arena.query_records),
            null_arena.budget,
        )
        scores_equal_for_candidate = all(score_ties)
        trace_matches_fixed_order = trace == fixed_order[: len(trace)]
        all_scores_equal = all_scores_equal and scores_equal_for_candidate
        all_traces_match_fixed_order = (
            all_traces_match_fixed_order and trace_matches_fixed_order
        )
        candidate_checks.append(
            {
                "candidate": null_arena.candidate_records[candidate_index],
                "adaptive_query_trace": list(trace),
                "all_greedy_scores_equal": scores_equal_for_candidate,
                "trace_matches_fixed_order": trace_matches_fixed_order,
            }
        )

    return {
        "arena": null_arena.name,
        "fixed_order": list(fixed_order),
        "all_greedy_scores_equal_at_every_step": all_scores_equal,
        "all_adaptive_trajectories_reduce_to_fixed_order": all_traces_match_fixed_order,
        "passed": all_scores_equal and all_traces_match_fixed_order,
        "candidate_checks": candidate_checks,
    }


def canonical_hash(payload):
    """Hash the canonical result payload without volatile time or self-hash fields."""
    hash_payload = {
        key: payload[key]
        for key in sorted(payload)
        if key not in ("generated_at", "determinism_hash")
    }
    canonical = json.dumps(
        hash_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_append_only(payload, directory):
    """Create result_v0.json once, then monotonically version later results."""
    suffix = 0
    while True:
        filename = "result_v0.json" if suffix == 0 else f"result_v0_{suffix}.json"
        result_path = directory / filename
        try:
            with result_path.open("x", encoding="utf-8") as result_file:
                json.dump(payload, result_file, indent=2, sort_keys=True)
                result_file.write("\n")
            return result_path
        except FileExistsError:
            suffix += 1


def make_payload():
    transition_arena = make_transition_table_arena()
    eca_arena = make_eca_arena()
    null_arena = make_null_arena()

    arena_results = {
        transition_arena.name: evaluate_arena(transition_arena),
        eca_arena.name: evaluate_arena(eca_arena),
        null_arena.name: evaluate_arena(null_arena),
    }
    null_a = arena_results[null_arena.name]["policies"]["A"]
    null_b = arena_results[null_arena.name]["policies"]["B"]
    null_gap = {
        "mean_q_a_minus_b": null_a["mean_q"] - null_b["mean_q"],
        "ident_rate_b_minus_a": null_b["ident_rate"] - null_a["ident_rate"],
        "max_q_a_minus_b": null_a["max_q"] - null_b["max_q"],
    }
    degeneracy_check = run_degeneracy_check(null_arena)

    boundary_results = {
        "k_equals_1": evaluate_arena(make_single_candidate_boundary_arena()),
        "budget_equals_0": evaluate_arena(make_zero_budget_boundary_arena()),
    }
    eca_a = arena_results[eca_arena.name]["policies"]["A"]
    eca_b = arena_results[eca_arena.name]["policies"]["B"]
    invariants = {
        "transition_table_all_identified_by_budget": (
            arena_results[transition_arena.name]["policies"]["A"]["ident_rate"] == 1.0
            and arena_results[transition_arena.name]["policies"]["B"]["ident_rate"] == 1.0
        ),
        "null_arena_no_b_advantage": (
            null_gap["mean_q_a_minus_b"] == 0.0
            and null_gap["ident_rate_b_minus_a"] == 0.0
            and null_gap["max_q_a_minus_b"] == 0
        ),
        "null_degeneracy_check_passed": degeneracy_check["passed"],
        "k_equals_1_identified_with_zero_queries": (
            boundary_results["k_equals_1"]["policies"]["A"]["mean_q"] == 0.0
            and boundary_results["k_equals_1"]["policies"]["B"]["mean_q"] == 0.0
        ),
        "budget_zero_records_budget_plus_one_for_nonidentified": (
            boundary_results["budget_equals_0"]["policies"]["A"]["mean_q"] == 1.0
            and boundary_results["budget_equals_0"]["policies"]["B"]["mean_q"] == 1.0
        ),
        "eca_mean_q_a_minus_b": eca_a["mean_q"] - eca_b["mean_q"],
    }

    payload = {
        "schema": "adaptive_observation_policy_result_v0",
        "sim_id": "adaptive_observation_policy_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "rng_seed": RNG_SEED,
        "policy_definitions": {
            "A": "A fixed query schedule chosen once by greedy partition refinement on the full prior; it never branches on observed answers.",
            "B": "At each step, choose the unasked query minimizing the largest answer class in the current version space; ties use the lowest query index.",
        },
        "arenas": arena_results,
        "null_arena_gap": null_gap,
        "degeneracy_check": degeneracy_check,
        "boundary": boundary_results,
        "invariants": invariants,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["determinism_hash"] = canonical_hash(payload)
    return payload


def print_headline_invariants(payload, result_path):
    eca = payload["arenas"]["eca_seeded_k40"]
    eca_a = eca["policies"]["A"]
    eca_b = eca["policies"]["B"]
    null_gap = payload["null_arena_gap"]
    gap_status = (
        "RED_FLAG_B_ADVANTAGE"
        if null_gap["mean_q_a_minus_b"] > 0.0
        else "OK_NO_B_ADVANTAGE"
    )

    print("adaptive_observation_policy_v0 headline invariants")
    print(
        "structured_eca "
        f"budget={eca['query_budget']} "
        f"A(mean_q={eca_a['mean_q']:.6f},max_q={eca_a['max_q']},ident_rate={eca_a['ident_rate']:.6f}) "
        f"B(mean_q={eca_b['mean_q']:.6f},max_q={eca_b['max_q']},ident_rate={eca_b['ident_rate']:.6f})"
    )
    print(
        "null_arena_gap_mean_q_A_minus_B="
        f"{null_gap['mean_q_a_minus_b']:.6f} {gap_status}"
    )
    print(
        "degeneracy_check_passed="
        f"{payload['degeneracy_check']['passed']} "
        "k1_zero_query="
        f"{payload['invariants']['k_equals_1_identified_with_zero_queries']} "
        "budget0_boundary="
        f"{payload['invariants']['budget_zero_records_budget_plus_one_for_nonidentified']}"
    )
    print(f"determinism_hash={payload['determinism_hash']}")
    print(f"result_path={result_path.name}")


def main():
    payload = make_payload()
    result_path = write_append_only(payload, Path(__file__).resolve().parent)
    print_headline_invariants(payload, result_path)


if __name__ == "__main__":
    main()
