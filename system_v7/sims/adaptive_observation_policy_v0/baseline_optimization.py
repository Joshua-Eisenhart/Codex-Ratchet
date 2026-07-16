#!/usr/bin/env python3
"""Audit-required best-found fixed control for the adaptive ECA lane.

This stays a scratch diagnostic.  It uses the runner's own fixed-policy
executor to search ordered, distinct five-query schedules on the exact seeded
ECA arena used by ``run.py``.  It deliberately reports a *best-found* fixed
schedule, not a global optimum, whenever the schedule space is too large for
the declared exhaustive threshold.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from pathlib import Path

from run import (
    RNG_SEED,
    choose_fixed_prior_queries,
    make_eca_arena,
    run_adaptive_policy,
    run_fixed_policy,
)


RESULT_BASENAME = "results_baseline_v1.json"
EXHAUSTIVE_MAX_SCHEDULES = 1_000_000
RANDOM_UNIQUE_SCHEDULES = 100_000
LOCAL_SEED_COUNT = 12
LOCAL_MAX_PASSES = 3


def ordered_distinct_schedule_count(query_count, budget):
    """Return P(query_count, budget) without relying on Python-version APIs."""
    if budget < 0 or budget > query_count:
        return 0
    count = 1
    for offset in range(budget):
        count *= query_count - offset
    return count


def source_sha256(path):
    """Hash a source file so the receipt binds this control to its runner."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(payload):
    """Hash a deterministic payload without recursively hashing its own hash."""
    hash_payload = {
        key: payload[key]
        for key in sorted(payload)
        if key != "determinism_hash"
    }
    encoded = json.dumps(
        hash_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def serialize_payload(payload):
    """Return the one canonical byte representation used for every run."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def metrics_from_fixed_schedule(arena, schedule):
    """Score a fixed schedule only through run.py's own run_fixed_policy."""
    schedule = tuple(schedule)
    if len(schedule) != arena.budget:
        raise ValueError("fixed control must use exactly the arena query budget")
    if len(set(schedule)) != len(schedule):
        raise ValueError("repeated fixed queries are excluded as weakly dominated")

    identified_count = 0
    query_total = 0
    max_queries = 0
    for ground_truth_index in range(len(arena.candidate_records)):
        identified, queries_to_identification, _ = run_fixed_policy(
            arena.answer_matrix,
            ground_truth_index,
            schedule,
            arena.budget,
        )
        identified_count += int(identified)
        query_total += queries_to_identification
        max_queries = max(max_queries, queries_to_identification)

    candidate_count = len(arena.candidate_records)
    return {
        "identified_count": identified_count,
        "ident_rate": identified_count / candidate_count,
        "query_total": query_total,
        "mean_queries": query_total / candidate_count,
        "max_queries": max_queries,
        "unidentified_query_value": arena.budget + 1,
    }


def metrics_from_adaptive_policy(arena):
    """Score B with run.py's own adaptive-policy executor."""
    identified_count = 0
    query_total = 0
    max_queries = 0
    query_count = len(arena.query_records)
    for ground_truth_index in range(len(arena.candidate_records)):
        identified, queries_to_identification, _, _ = run_adaptive_policy(
            arena.answer_matrix,
            ground_truth_index,
            query_count,
            arena.budget,
        )
        identified_count += int(identified)
        query_total += queries_to_identification
        max_queries = max(max_queries, queries_to_identification)

    candidate_count = len(arena.candidate_records)
    return {
        "identified_count": identified_count,
        "ident_rate": identified_count / candidate_count,
        "query_total": query_total,
        "mean_queries": query_total / candidate_count,
        "max_queries": max_queries,
        "unidentified_query_value": arena.budget + 1,
    }


def schedule_rank(schedule, metrics):
    """A deterministic fixed-control objective and total tie-break order."""
    return (
        -metrics["identified_count"],
        metrics["query_total"],
        metrics["max_queries"],
        tuple(schedule),
    )


def schedule_digest(schedules):
    """Digest an evaluated schedule set without writing the large set to JSON."""
    digest = hashlib.sha256()
    for schedule in sorted(schedules):
        digest.update(",".join(str(query_index) for query_index in schedule).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def fixed_schedule_record(arena, schedule, metrics):
    """Return a JSON-ready fixed-policy record with structural query labels."""
    return {
        "fixed_query_indices": list(schedule),
        "fixed_queries": [dict(arena.query_records[index]) for index in schedule],
        "metrics": dict(metrics),
    }


class FixedScheduleSearch:
    """Deterministic cache for an audit receipt and bounded local search."""

    def __init__(self, arena):
        self.arena = arena
        self.metrics_by_schedule = {}
        self.local_neighbor_lookups = 0

    def evaluate(self, schedule):
        schedule = tuple(schedule)
        if schedule not in self.metrics_by_schedule:
            self.metrics_by_schedule[schedule] = metrics_from_fixed_schedule(
                self.arena, schedule
            )
        return self.metrics_by_schedule[schedule]

    def best_schedule(self):
        return min(
            self.metrics_by_schedule,
            key=lambda schedule: schedule_rank(
                schedule, self.metrics_by_schedule[schedule]
            ),
        )


def iter_local_neighbors(schedule, all_query_indices):
    """Yield each distinct one-replacement or one-order-swap neighbor once."""
    schedule = tuple(schedule)
    selected = set(schedule)
    for position in range(len(schedule)):
        for replacement in all_query_indices:
            if replacement in selected:
                continue
            neighbor = list(schedule)
            neighbor[position] = replacement
            yield tuple(neighbor)

    for left_index in range(len(schedule)):
        for right_index in range(left_index + 1, len(schedule)):
            neighbor = list(schedule)
            neighbor[left_index], neighbor[right_index] = (
                neighbor[right_index],
                neighbor[left_index],
            )
            yield tuple(neighbor)


def run_best_improvement_local_search(search, start_schedule, all_query_indices):
    """Run a bounded, deterministic best-improvement search from one seed."""
    current_schedule = tuple(start_schedule)
    current_metrics = search.evaluate(current_schedule)
    passes = []

    for _ in range(LOCAL_MAX_PASSES):
        best_schedule = current_schedule
        best_metrics = current_metrics
        cache_size_before = len(search.metrics_by_schedule)
        neighbor_count = 0

        for neighbor in iter_local_neighbors(current_schedule, all_query_indices):
            neighbor_count += 1
            neighbor_metrics = search.evaluate(neighbor)
            if schedule_rank(neighbor, neighbor_metrics) < schedule_rank(
                best_schedule, best_metrics
            ):
                best_schedule = neighbor
                best_metrics = neighbor_metrics

        search.local_neighbor_lookups += neighbor_count
        improved = best_schedule != current_schedule
        passes.append(
            {
                "neighbor_lookups": neighbor_count,
                "new_unique_evaluations": (
                    len(search.metrics_by_schedule) - cache_size_before
                ),
                "improved": improved,
                "best_schedule_after_pass": list(best_schedule),
                "best_metrics_after_pass": dict(best_metrics),
            }
        )
        if not improved:
            return {
                "seed_schedule": list(start_schedule),
                "final_schedule": list(current_schedule),
                "termination": "local_optimum_within_declared_neighborhood",
                "passes": passes,
            }

        current_schedule = best_schedule
        current_metrics = best_metrics

    return {
        "seed_schedule": list(start_schedule),
        "final_schedule": list(current_schedule),
        "termination": "local_pass_cap_reached",
        "passes": passes,
    }


def search_best_fixed_schedule(arena):
    """Search the fixed-policy space, exhaustively only below a stated limit."""
    all_query_indices = tuple(range(len(arena.query_records)))
    schedule_space_size = ordered_distinct_schedule_count(
        len(all_query_indices), arena.budget
    )
    search = FixedScheduleSearch(arena)
    local_search_traces = []
    random_best_schedule = None
    random_unique_schedules = 0
    local_unique_evaluations = 0

    if schedule_space_size <= EXHAUSTIVE_MAX_SCHEDULES:
        search_method = "exhaustive_ordered_distinct_schedule_enumeration"
        for schedule in itertools.permutations(all_query_indices, arena.budget):
            search.evaluate(schedule)
        best_fixed_status = "globally_optimal_within_ordered_distinct_domain"
    else:
        search_method = "seeded_random_plus_best_improvement_local_search"
        rng = random.Random(0)
        while len(search.metrics_by_schedule) < RANDOM_UNIQUE_SCHEDULES:
            schedule = tuple(rng.sample(all_query_indices, arena.budget))
            search.evaluate(schedule)
        random_unique_schedules = len(search.metrics_by_schedule)
        random_best_schedule = search.best_schedule()

        local_seed_schedules = sorted(
            search.metrics_by_schedule,
            key=lambda schedule: schedule_rank(
                schedule, search.metrics_by_schedule[schedule]
            ),
        )[:LOCAL_SEED_COUNT]
        cache_size_before_local_search = len(search.metrics_by_schedule)
        for seed_schedule in local_seed_schedules:
            local_search_traces.append(
                run_best_improvement_local_search(
                    search, seed_schedule, all_query_indices
                )
            )
        local_unique_evaluations = (
            len(search.metrics_by_schedule) - cache_size_before_local_search
        )
        best_fixed_status = "best_found_not_proven_global"

    best_schedule = search.best_schedule()
    best_metrics = search.evaluate(best_schedule)
    random_best_record = None
    if random_best_schedule is not None:
        random_best_record = fixed_schedule_record(
            arena,
            random_best_schedule,
            search.evaluate(random_best_schedule),
        )

    trace_digest = hashlib.sha256(
        json.dumps(
            local_search_traces,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()
    search_receipt = {
        "method": search_method,
        "rng_seed": 0,
        "schedule_definition": (
            "ordered distinct fixed five-query schedule; order affects "
            "mean_queries and repeated queries are weakly dominated"
        ),
        "schedule_space_size": schedule_space_size,
        "exhaustive_threshold": EXHAUSTIVE_MAX_SCHEDULES,
        "exhaustive": schedule_space_size <= EXHAUSTIVE_MAX_SCHEDULES,
        "random_unique_schedules": random_unique_schedules,
        "minimum_random_unique_schedules_required": RANDOM_UNIQUE_SCHEDULES,
        "local_seed_count": len(local_search_traces),
        "local_max_passes_per_seed": LOCAL_MAX_PASSES,
        "local_neighbor_definition": (
            "one query replacement plus one schedule-order swap"
        ),
        "local_neighbor_lookups": search.local_neighbor_lookups,
        "local_unique_evaluations": local_unique_evaluations,
        "unique_schedules_evaluated": len(search.metrics_by_schedule),
        "evaluated_schedule_digest": schedule_digest(search.metrics_by_schedule),
        "local_search_trace_digest": trace_digest,
        "local_search_traces": local_search_traces,
        "best_fixed_status": best_fixed_status,
        "objective": [
            "maximize identified_count",
            "minimize total_queries_to_identification",
            "minimize max_queries",
            "lexicographically minimize ordered schedule",
        ],
        "best_random_schedule_before_local_search": random_best_record,
    }
    if not search_receipt["exhaustive"] and random_unique_schedules < RANDOM_UNIQUE_SCHEDULES:
        raise RuntimeError("random search did not reach the required 100,000 schedules")
    return best_schedule, best_metrics, search_receipt


def comparison_record(best_fixed_metrics, adaptive_metrics):
    """State the only claim the measured A* versus B comparison supports."""
    ident_rate_delta = adaptive_metrics["ident_rate"] - best_fixed_metrics["ident_rate"]
    mean_query_delta = (
        best_fixed_metrics["mean_queries"] - adaptive_metrics["mean_queries"]
    )

    if best_fixed_metrics["ident_rate"] >= adaptive_metrics["ident_rate"]:
        relation = (
            "matches"
            if best_fixed_metrics["ident_rate"] == adaptive_metrics["ident_rate"]
            else "beats"
        )
        verdict_code = "adaptive_advantage_killed_by_optimized_fixed_control"
        verdict = (
            "On this seeded ECA arena, best-found fixed A* "
            f"{relation} B on identification rate "
            f"(A*={best_fixed_metrics['ident_rate']:.6f}, "
            f"B={adaptive_metrics['ident_rate']:.6f}); the adaptive-advantage "
            "claim is killed for this measured control."
        )
    elif best_fixed_metrics["mean_queries"] >= adaptive_metrics["mean_queries"]:
        verdict_code = "adaptive_advantage_observed_on_seeded_arena_only"
        verdict = (
            "On this single seeded ECA arena and bounded non-exhaustive search, "
            f"B exceeds best-found fixed A* on identification rate "
            f"(B={adaptive_metrics['ident_rate']:.6f}, "
            f"A*={best_fixed_metrics['ident_rate']:.6f}) and uses no more mean "
            "queries; this is a scratch-diagnostic observation, not a global "
            "fixed-schedule optimality proof."
        )
    else:
        verdict_code = "identification_query_tradeoff_no_unqualified_advantage"
        verdict = (
            "On this single seeded ECA arena and bounded non-exhaustive search, "
            f"B has higher identification rate (B={adaptive_metrics['ident_rate']:.6f}, "
            f"A*={best_fixed_metrics['ident_rate']:.6f}) but A* has lower mean "
            "queries; this is an identification/query tradeoff, not an "
            "unqualified adaptive advantage."
        )

    return {
        "primary_comparison_metric": "ident_rate",
        "B_minus_A_star_ident_rate": ident_rate_delta,
        "A_star_minus_B_mean_queries": mean_query_delta,
        "verdict_code": verdict_code,
        "honest_verdict": verdict,
    }


def make_payload():
    """Build the deterministic same-arena baseline-control receipt."""
    if RNG_SEED != 0:
        raise RuntimeError("this control is registered only for run.py RNG seed 0")
    arena = make_eca_arena(budget=5)
    if arena.name != "eca_seeded_k40" or arena.budget != 5:
        raise RuntimeError("expected the seeded ECA K=40 arena with a five-query budget")

    old_a_schedule = choose_fixed_prior_queries(
        arena.answer_matrix, len(arena.query_records), arena.budget
    )
    old_a_metrics = metrics_from_fixed_schedule(arena, old_a_schedule)
    best_schedule, best_metrics, search_receipt = search_best_fixed_schedule(arena)
    adaptive_metrics = metrics_from_adaptive_policy(arena)
    comparison = comparison_record(best_metrics, adaptive_metrics)

    run_source = Path(__file__).resolve().with_name("run.py")
    payload = {
        "schema": "adaptive_observation_policy_baseline_v1",
        "sim_id": "adaptive_observation_policy_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_ceiling": {
            "allowed": "same-seeded-arena baseline comparison only",
            "blocked_consumers": [
                "global fixed-schedule optimality claims",
                "promotion or admission claims",
                "cross-seed or cross-arena generalization claims",
            ],
        },
        "source": {
            "run_py_sha256": source_sha256(run_source),
            "imported_execution_functions": [
                "run_fixed_policy",
                "run_adaptive_policy",
                "choose_fixed_prior_queries",
                "make_eca_arena",
            ],
        },
        "arena": {
            "name": arena.name,
            "description": arena.description,
            "rng_seed": 0,
            "candidate_count": len(arena.candidate_records),
            "query_pool_count": len(arena.query_records),
            "query_budget": arena.budget,
            "unidentified_query_value": arena.budget + 1,
        },
        "policy_definitions": {
            "A_old": (
                "run.py's shipped greedy fixed schedule; provenance only, not "
                "treated as the best fixed baseline"
            ),
            "A_star": (
                "best-found fixed ordered distinct schedule from the declared "
                "same-arena search"
            ),
            "B": "run.py's adaptive current-version-space greedy policy",
        },
        "search": search_receipt,
        "policies": {
            "old_A_provenance": fixed_schedule_record(
                arena, old_a_schedule, old_a_metrics
            ),
            "best_found_fixed_A_star": fixed_schedule_record(
                arena, best_schedule, best_metrics
            ),
            "adaptive_B": {"metrics": adaptive_metrics},
        },
        "comparison": comparison,
        "TOOL_MANIFEST": {
            "python_stdlib": {
                "used": True,
                "reason": (
                    "This is a finite pure-Python scratch control; standard-library "
                    "random, JSON, hashing, and enumeration implement the declared "
                    "deterministic search receipt."
                ),
            }
        },
        "TOOL_INTEGRATION_DEPTH": None,
        "divergence_log": [
            "The former greedy A baseline is retained for provenance only; A* is "
            "the control used in the adaptive comparison."
        ],
    }
    payload["determinism_hash"] = canonical_hash(payload)
    return payload


def write_append_only(payload, directory):
    """Write a versioned result without ever overwriting a prior receipt."""
    serialized = serialize_payload(payload)
    suffix = 0
    while True:
        filename = (
            RESULT_BASENAME
            if suffix == 0
            else f"{Path(RESULT_BASENAME).stem}_{suffix}.json"
        )
        result_path = directory / filename
        try:
            with result_path.open("x", encoding="utf-8") as result_file:
                result_file.write(serialized)
            return result_path
        except FileExistsError:
            suffix += 1


def print_summary(payload, result_path):
    """Print the user-facing, literal comparison without selecting a narrative."""
    old_a = payload["policies"]["old_A_provenance"]
    best_fixed = payload["policies"]["best_found_fixed_A_star"]
    adaptive = payload["policies"]["adaptive_B"]

    def format_metrics(metrics):
        return (
            f"ident_rate={metrics['ident_rate']:.6f} "
            f"mean_queries={metrics['mean_queries']:.6f} "
            f"max_queries={metrics['max_queries']}"
        )

    print("adaptive_observation_policy_v0 optimized fixed baseline control")
    print(
        "A(old) "
        f"schedule={old_a['fixed_query_indices']} "
        f"{format_metrics(old_a['metrics'])}"
    )
    print(
        "A*(best fixed) "
        f"schedule={best_fixed['fixed_query_indices']} "
        f"{format_metrics(best_fixed['metrics'])}"
    )
    print(f"B(adaptive) {format_metrics(adaptive['metrics'])}")
    print(f"VERDICT: {payload['comparison']['honest_verdict']}")
    print(f"determinism_hash={payload['determinism_hash']}")
    print(f"result_path={result_path.name}")


def main():
    payload = make_payload()
    result_path = write_append_only(payload, Path(__file__).resolve().parent)
    print_summary(payload, result_path)


if __name__ == "__main__":
    main()
