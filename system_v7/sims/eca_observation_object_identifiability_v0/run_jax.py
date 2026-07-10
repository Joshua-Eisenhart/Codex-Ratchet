#!/usr/bin/env python3
"""Exhaustive JAX ECA partial-observation object-identifiability census."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from collections import Counter
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
from jax import lax, vmap


SIM_ID = "eca_observation_object_identifiability_v0"
SCHEMA = "codex_ratchet.eca_observation_object_identifiability_v0.jax.v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TAG = "ECA-OBS-ID-V0"
RING_SIZE = 9
STATE_COUNT = 1 << RING_SIZE
RULE_COUNT = 256
PAIR_COUNT = RULE_COUNT * (RULE_COUNT - 1) // 2
FIXTURE_COUNT = 531
QUERY_COUNT = 9636
BUDGETS = (1, 2, 4, 8, 16)
REFINEMENT_BATCH_SIZE = 128
CONSENSUS_BATCH_SIZE = 256
MAX_REFINEMENT_ROUNDS = STATE_COUNT
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
PREREGISTRATION_PATH = HERE / "preregistration_receipt.json"
DEFAULT_OUTPUT = HERE / "results" / f"{SIM_ID}_jax_results.json"

EXPECTED_SPEC_SHA256 = "909abe7eb98543329cf18e36343a03377bdea1453bd0cc807a43340b73cf95d9"
EXPECTED_CARD_SHA256 = "2558ba2f31cf7962cafa97c9c09bddd5237a48b3976cb63c3b04820c7709b07f"

TOOL_MANIFEST = {
    "jax.numpy": {
        "used": True,
        "reason": "Exact x64 transitions, packed refinement, version masks, and query consensus.",
    },
    "jax.vmap": {
        "used": True,
        "reason": "Vectorized transition generation and exhaustive row canonicalization.",
    },
    "jax.jit": {
        "used": True,
        "reason": "Compiled stable-partition, compatibility-mask, and consensus kernels.",
    },
    "jax.lax.while_loop": {
        "used": True,
        "reason": "Proof-bounded refinement to the first unchanged partition.",
    },
    "jax.lax.fori_loop": {
        "used": True,
        "reason": "Exact cumulative observation compatibility masks without host-side approximation.",
    },
    "numpy": {"used": False, "reason": "Forbidden from the claim path."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax.numpy": "load_bearing",
    "jax.vmap": "load_bearing",
    "jax.jit": "load_bearing",
    "jax.lax.while_loop": "load_bearing",
    "jax.lax.fori_loop": "load_bearing",
    "numpy": None,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def compact_partition(labels: list[int]) -> list[int]:
    renaming: dict[int, int] = {}
    compact: list[int] = []
    for label in labels:
        if label not in renaming:
            renaming[label] = len(renaming)
        compact.append(renaming[label])
    return compact


def verify_frozen_inputs() -> tuple[dict, dict]:
    spec = json.loads(SPEC_PATH.read_text())
    receipt = json.loads(PREREGISTRATION_PATH.read_text())
    observed_spec = sha256_file(SPEC_PATH)
    observed_card = sha256_file(CARD_PATH)
    tests = {
        "spec_matches_source_constant": observed_spec == EXPECTED_SPEC_SHA256,
        "card_matches_source_constant": observed_card == EXPECTED_CARD_SHA256,
        "spec_matches_preregistration": observed_spec == receipt.get("spec_sha256"),
        "card_matches_preregistration": observed_card == receipt.get("object_card_sha256"),
        "preregistration_precedes_builder": receipt.get("builder_sources_present_when_frozen") is False,
        "sim_id_matches": receipt.get("sim_id") == spec.get("sim_id") == SIM_ID,
        "peer_result_reads_forbidden": spec["engine_contract"]["peer_result_reads_forbidden"] is True,
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen input verification failed: {tests}")
    return spec, {
        "spec_sha256": observed_spec,
        "object_card_sha256": observed_card,
        "preregistration_sha256": sha256_file(PREREGISTRATION_PATH),
        "verified_before_computation": True,
        "tests": tests,
        "all_pass": True,
    }


def reflect_rule(rule: int) -> int:
    out = 0
    for neighborhood in range(8):
        reversed_neighborhood = (
            ((neighborhood & 1) << 2)
            | (neighborhood & 2)
            | ((neighborhood & 4) >> 2)
        )
        out |= ((rule >> reversed_neighborhood) & 1) << neighborhood
    return out


def conjugate_rule(rule: int) -> int:
    return sum(
        (1 - ((rule >> (7 - neighborhood)) & 1)) << neighborhood
        for neighborhood in range(8)
    )


def rule_orbit(rule: int) -> tuple[int, ...]:
    return tuple(sorted({rule, reflect_rule(rule), conjugate_rule(rule), reflect_rule(conjugate_rule(rule))}))


def ordered_rule_orbits() -> list[tuple[int, ...]]:
    orbits = {rule_orbit(rule) for rule in range(RULE_COUNT)}
    return sorted(
        orbits,
        key=lambda orbit: (
            hashlib.sha256((f"{TAG}|rule_orbit|" + ",".join(map(str, orbit))).encode()).hexdigest(),
            orbit,
        ),
    )


def simultaneous_pair_orbit(pair: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    a, b = pair
    ta = (a, reflect_rule(a), conjugate_rule(a), reflect_rule(conjugate_rule(a)))
    tb = (b, reflect_rule(b), conjugate_rule(b), reflect_rule(conjugate_rule(b)))
    return tuple(sorted({tuple(sorted((ta[index], tb[index]))) for index in range(4)}))


def build_manifests(spec: dict) -> tuple[list[tuple[int, int]], list[list[int]], dict]:
    orbits = ordered_rule_orbits()
    blocks = {"train": orbits[:52], "validation": orbits[52:70], "test": orbits[70:88]}
    rule_block = {
        rule: block
        for block, block_orbits in blocks.items()
        for orbit in block_orbits
        for rule in orbit
    }
    pair_orbits: dict[str, list[list[list[int]]]] = {}
    counts = {}
    for block, block_orbits in blocks.items():
        raw_pairs = [
            (a, b)
            for a in range(RULE_COUNT - 1)
            for b in range(a + 1, RULE_COUNT)
            if rule_block[a] == rule_block[b] == block
        ]
        unique_orbits = sorted({simultaneous_pair_orbit(pair) for pair in raw_pairs})
        pair_orbits[block] = [[list(pair) for pair in orbit] for orbit in unique_orbits]
        counts[block] = {
            "rule_orbits": len(block_orbits),
            "rules": len({rule for orbit in block_orbits for rule in orbit}),
            "raw_pairs": len(raw_pairs),
            "simultaneous_pair_orbits": len(unique_orbits),
        }
    fixtures = [tuple(orbit[0]) for orbit in sorted({simultaneous_pair_orbit(tuple(orbit[0])) for orbit in pair_orbits["test"]})]

    def probe(state: int) -> tuple[int, int]:
        bits = [(state >> site) & 1 for site in range(RING_SIZE)]
        return sum(bits), sum(bits[index] != bits[(index + 1) % RING_SIZE] for index in range(RING_SIZE))

    queries = [
        [a, b]
        for a in range(STATE_COUNT - 1)
        for b in range(a + 1, STATE_COUNT)
        if probe(a) == probe(b)
    ]
    assignments = spec["observation_packet"]["ordered_word_state_assignments"]
    hashes = {
        "rule_orbits": canonical_hash(orbits),
        "pair_orbits": canonical_hash(pair_orbits),
        "assignments": canonical_hash(assignments),
        "queries": canonical_hash(queries),
    }
    tests = {
        "rule_orbit_manifest_matches": hashes["rule_orbits"] == spec["rule_family_split"]["rule_orbit_manifest_sha256"],
        "pair_orbit_manifest_matches": hashes["pair_orbits"] == spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"],
        "assignment_manifest_matches": hashes["assignments"] == spec["observation_packet"]["word_state_assignment_sha256"],
        "query_manifest_matches": hashes["queries"] == spec["query_universe"]["query_manifest_sha256"],
        "all_88_rule_orbits_present": len(orbits) == 88,
        "all_531_fixtures_present_once": len(fixtures) == len(set(fixtures)) == FIXTURE_COUNT,
        "all_9636_queries_present_once": len(queries) == len({tuple(query) for query in queries}) == QUERY_COUNT,
        "expected_block_counts_match": all(
            counts[block] == spec["rule_family_split"]["expected_counts"][block]
            for block in blocks
        ),
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen manifest verification failed: {tests}")
    return fixtures, queries, {"counts": counts, "hashes": hashes, "tests": tests, "all_pass": True}


def eca_transition_table() -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    rules = jnp.arange(RULE_COUNT, dtype=jnp.int64)

    def step(rule: jax.Array, state: jax.Array) -> jax.Array:
        bits = (state >> sites) & 1
        neighborhoods = (jnp.roll(bits, 1) << 2) | (bits << 1) | jnp.roll(bits, -1)
        return jnp.sum(((rule >> neighborhoods) & 1) << sites, dtype=jnp.int64)

    return vmap(lambda rule: vmap(lambda state: step(rule, state))(states))(rules)


def canonicalize_signatures(signatures: jax.Array) -> jax.Array:
    order = jnp.argsort(signatures, stable=True)
    sorted_signatures = signatures[order]
    starts = jnp.concatenate((jnp.ones((1,), dtype=jnp.bool_), sorted_signatures[1:] != sorted_signatures[:-1]))
    sorted_labels = jnp.cumsum(starts, dtype=jnp.int64) - 1
    return jnp.zeros_like(sorted_labels).at[order].set(sorted_labels)


canonicalize_batch = vmap(canonicalize_signatures)


def base_probe_labels() -> jax.Array:
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (states[:, None] >> sites) & 1
    weight = jnp.sum(bits, axis=1, dtype=jnp.int64)
    walls = jnp.sum(bits != jnp.roll(bits, -1, axis=1), axis=1, dtype=jnp.int64)
    return canonicalize_signatures(weight * (RING_SIZE + 1) + walls)


def build_refinement_kernel():
    base = base_probe_labels()

    @jax.jit
    def kernel(action_a: jax.Array, action_b: jax.Array):
        batch_count = action_a.shape[0]
        labels0 = jnp.broadcast_to(base, (batch_count, STATE_COUNT))
        active0 = jnp.ones((batch_count,), dtype=jnp.bool_)
        initial = (jnp.asarray(0, dtype=jnp.int64), labels0, active0)

        def condition(carry):
            round_index, _, active = carry
            return (round_index < MAX_REFINEMENT_ROUNDS) & jnp.any(active)

        def body(carry):
            round_index, labels, active = carry
            next_a = jnp.take_along_axis(labels, action_a, axis=1)
            next_b = jnp.take_along_axis(labels, action_b, axis=1)
            packed = (labels * STATE_COUNT + next_a) * STATE_COUNT + next_b
            refined = canonicalize_batch(packed)
            changed = active & jnp.any(refined != labels, axis=1)
            return round_index + 1, jnp.where(active[:, None], refined, labels), changed

        return lax.while_loop(condition, body, initial)

    return kernel


def compute_all_stable_partitions(transitions: jax.Array) -> tuple[jax.Array, dict]:
    pairs = list(itertools.combinations(range(RULE_COUNT), 2))
    kernel = build_refinement_kernel()
    chunks = []
    nonconverged = []
    round_histogram: Counter[int] = Counter()
    for start in range(0, PAIR_COUNT, REFINEMENT_BATCH_SIZE):
        batch = pairs[start : start + REFINEMENT_BATCH_SIZE]
        real_count = len(batch)
        padded = batch + [batch[-1]] * (REFINEMENT_BATCH_SIZE - real_count)
        a = jnp.asarray([pair[0] for pair in padded], dtype=jnp.int64)
        b = jnp.asarray([pair[1] for pair in padded], dtype=jnp.int64)
        rounds, labels, active = kernel(transitions[a], transitions[b])
        rounds_host = int(rounds)
        active_host = active[:real_count].tolist()
        round_histogram[rounds_host] += 1
        nonconverged.extend(list(batch[index]) for index, value in enumerate(active_host) if value)
        chunks.append(labels[:real_count].astype(jnp.int16))
    partitions = jnp.concatenate(chunks, axis=0)
    partitions.block_until_ready()
    return partitions, {
        "pair_count": PAIR_COUNT,
        "nonconverged_pairs": nonconverged,
        "batch_round_histogram": {str(key): value for key, value in sorted(round_histogram.items())},
        "all_pass": not nonconverged and partitions.shape == (PAIR_COUNT, STATE_COUNT),
    }


def pair_index(a: int, b: int) -> int:
    if a == b:
        raise ValueError("diagonal rule pair has no partition")
    if a > b:
        a, b = b, a
    return a * (2 * RULE_COUNT - a - 1) // 2 + (b - a - 1)


def generate_observations(rule_a: int, rule_b: int, assignments: list[list[object]], transitions: list[list[int]]) -> list[list[tuple[int, int, int]]]:
    trajectories = []
    for word, initial_state in assignments:
        state = int(initial_state)
        trajectory = []
        for token in str(word):
            rule = rule_a if token == "A" else rule_b
            successor = transitions[rule][state]
            trajectory.append((state, 0 if token == "A" else 1, successor))
            state = successor
        trajectories.append(trajectory)
    return trajectories


@jax.jit
def compatible_rule_mask(transitions: jax.Array, predecessors: jax.Array, successors: jax.Array, valid: jax.Array) -> jax.Array:
    def body(index, mask):
        matches = transitions[:, predecessors[index]] == successors[index]
        return mask & jnp.where(valid[index], matches, True)

    return lax.fori_loop(0, predecessors.shape[0], body, jnp.ones((RULE_COUNT,), dtype=jnp.bool_))


@jax.jit
def consensus_chunk(partitions: jax.Array, partition_indices: jax.Array, valid: jax.Array, query_a: jax.Array, query_b: jax.Array):
    labels = partitions[partition_indices]
    equal = labels[:, query_a] == labels[:, query_b]
    return jnp.all(jnp.where(valid[:, None], equal, True), axis=0), jnp.any(jnp.where(valid[:, None], equal, False), axis=0)


def masks_for_budget(transitions_device: jax.Array, observations: list[list[tuple[int, int, int]]], budget: int) -> tuple[list[int], list[int]]:
    flat = [item for trajectory in observations[:budget] for item in trajectory]
    result = []
    for token in (0, 1):
        selected = [item for item in flat if item[1] == token]
        predecessors = [item[0] for item in selected]
        successors = [item[2] for item in selected]
        width = 4 * budget
        pred = jnp.asarray(predecessors + [0] * (width - len(predecessors)), dtype=jnp.int64)
        succ = jnp.asarray(successors + [0] * (width - len(successors)), dtype=jnp.int64)
        valid = jnp.arange(width) < len(predecessors)
        mask = compatible_rule_mask(transitions_device, pred, succ, valid)
        result.append([index for index, value in enumerate(mask.tolist()) if value])
    return result[0], result[1]


def effective_pairs(compatible_a: list[int], compatible_b: list[int]) -> tuple[list[tuple[int, int]], int]:
    ordered_size = len(compatible_a) * len(compatible_b) - len(set(compatible_a) & set(compatible_b))
    unordered = sorted({tuple(sorted((a, b))) for a in compatible_a for b in compatible_b if a != b})
    return unordered, ordered_size


def relation_consensus(partitions: jax.Array, unordered_pairs: list[tuple[int, int]], query_a: jax.Array, query_b: jax.Array) -> list[int]:
    must_equal = jnp.ones((QUERY_COUNT,), dtype=jnp.bool_)
    possible_equal = jnp.zeros((QUERY_COUNT,), dtype=jnp.bool_)
    indices = [pair_index(*pair) for pair in unordered_pairs]
    for start in range(0, len(indices), CONSENSUS_BATCH_SIZE):
        chunk = indices[start : start + CONSENSUS_BATCH_SIZE]
        real_count = len(chunk)
        padded = chunk + [chunk[-1]] * (CONSENSUS_BATCH_SIZE - real_count)
        valid = jnp.arange(CONSENSUS_BATCH_SIZE) < real_count
        all_equal, any_equal = consensus_chunk(
            partitions,
            jnp.asarray(padded, dtype=jnp.int64),
            valid,
            query_a,
            query_b,
        )
        must_equal &= all_equal
        possible_equal |= any_equal
    return jnp.where(must_equal, 2, jnp.where(possible_equal, 0, 1)).tolist()


def partition_hashes(partitions: jax.Array) -> list[str]:
    return [canonical_hash(compact_partition(labels)) for labels in partitions.tolist()]


def brute_force_version_space(
    transitions: list[list[int]],
    observations: list[list[tuple[int, int, int]]],
    budget: int,
) -> list[tuple[int, int]]:
    """Replay every ordered hypothesis directly, without factorized masks."""

    flat = [item for trajectory in observations[:budget] for item in trajectory]
    compatible = []
    for rule_a in range(RULE_COUNT):
        for rule_b in range(RULE_COUNT):
            if rule_a == rule_b:
                continue
            if all(
                transitions[rule_a if token == 0 else rule_b][predecessor]
                == successor
                for predecessor, token, successor in flat
            ):
                compatible.append((rule_a, rule_b))
    return compatible


def tool_calls_receipt() -> list[dict]:
    common = {
        "input_object": "531 frozen ECA fixtures, five budgets, and 9636 same-P0 queries",
        "output_object": "complete exact ordered-version-space and three-valued identifiability ledger",
        "positive_case": "all compatible hypotheses contribute to every relation consensus",
        "negative/erased_control": "transition, token, query-order, and vector mutations are detected",
        "boundary_case": "budget one and sixteen plus first and last fixture brute-force checks",
        "demotion_condition": "frozen-hash drift, nonconvergence, missing fixture, empty version space, or control silence",
        "gates": ["all_pass", "quotient"],
    }
    return [
        {"tool": "jax.numpy", "qualified_api/function": "jax.numpy.argsort", **common},
        {"tool": "jax.vmap", "qualified_api/function": "jax.vmap", **common},
        {"tool": "jax.jit", "qualified_api/function": "jax.jit", **common},
        {"tool": "jax.lax.while_loop", "qualified_api/function": "jax.lax.while_loop", **common},
        {"tool": "jax.lax.fori_loop", "qualified_api/function": "jax.lax.fori_loop", **common},
    ]


def build_receipt(spec: dict, frozen_inputs: dict) -> dict:
    started = time.time()
    fixtures, queries, manifest = build_manifests(spec)
    assignments = spec["observation_packet"]["ordered_word_state_assignments"]
    transitions_device = eca_transition_table()
    transitions_device.block_until_ready()
    transitions = transitions_device.tolist()
    partitions, refinement = compute_all_stable_partitions(transitions_device)
    if not refinement["all_pass"]:
        raise RuntimeError("stable partition refinement did not converge")
    invariant_partition_hashes = partition_hashes(partitions)
    query_a = jnp.asarray([query[0] for query in queries], dtype=jnp.int64)
    query_b = jnp.asarray([query[1] for query in queries], dtype=jnp.int64)

    ledger = []
    nested_failures = []
    ambiguity_failures = []
    factorized_controls = []
    action_swap_failures = []
    prior_by_fixture: dict[str, dict] = {}
    vector_by_key: dict[tuple[str, int], list[int]] = {}

    for fixture_index, (rule_a, rule_b) in enumerate(fixtures):
        orbit_key = f"{rule_a},{rule_b}"
        observations = generate_observations(rule_a, rule_b, assignments, transitions)
        previous_a: set[int] | None = None
        previous_b: set[int] | None = None
        previous_ambiguous: set[int] | None = None
        for budget in BUDGETS:
            compatible_a, compatible_b = masks_for_budget(transitions_device, observations, budget)
            unordered, ordered_size = effective_pairs(compatible_a, compatible_b)
            if not unordered or ordered_size == 0:
                raise RuntimeError(f"empty version space for {orbit_key} budget {budget}")
            vector = relation_consensus(partitions, unordered, query_a, query_b)
            vector_by_key[(orbit_key, budget)] = vector
            counts = Counter(vector)
            distinct_hashes = {invariant_partition_hashes[pair_index(*pair)] for pair in unordered}
            true_in = rule_a in compatible_a and rule_b in compatible_b
            effective_count = len(unordered)
            consensus_without = counts[1] + counts[2] if effective_count >= 8 and len(distinct_hashes) >= 2 else 0
            record = {
                "rule_A": rule_a,
                "rule_B": rule_b,
                "pair_orbit_key": orbit_key,
                "trajectory_budget": budget,
                "compatible_A_count": len(compatible_a),
                "compatible_A_hash": canonical_hash(compatible_a),
                "compatible_B_count": len(compatible_b),
                "compatible_B_hash": canonical_hash(compatible_b),
                "ordered_version_space_size": ordered_size,
                "effective_unordered_hypothesis_count": effective_count,
                "distinct_partition_relation_count": len(distinct_hashes),
                "whole_partition_identifiable": len(distinct_hashes) == 1,
                "true_pair_in_version_space": true_in,
                "system_identified": ordered_size == 1,
                "identifiable_query_count": counts[1] + counts[2],
                "unidentifiable_query_count": counts[0],
                "consensus_without_identification_query_count": consensus_without,
                "identifiable_same_count": counts[2],
                "identifiable_different_count": counts[1],
                "identifiability_vector_hash": canonical_hash(vector),
            }
            ledger.append(record)

            current_a, current_b = set(compatible_a), set(compatible_b)
            current_ambiguous = {index for index, value in enumerate(vector) if value == 0}
            if previous_a is not None and not (current_a <= previous_a and current_b <= previous_b):
                nested_failures.append([orbit_key, budget, "version_space"])
            if previous_ambiguous is not None and not current_ambiguous <= previous_ambiguous:
                ambiguity_failures.append([orbit_key, budget])
            previous_a, previous_b, previous_ambiguous = current_a, current_b, current_ambiguous

            swapped_observations = [
                [(predecessor, 1 - token, successor) for predecessor, token, successor in trajectory]
                for trajectory in observations
            ]
            swapped_a, swapped_b = masks_for_budget(
                transitions_device, swapped_observations, budget
            )
            swapped_unordered, swapped_ordered_size = effective_pairs(swapped_a, swapped_b)
            if (
                swapped_a != compatible_b
                or swapped_b != compatible_a
                or swapped_unordered != unordered
                or swapped_ordered_size != ordered_size
            ):
                action_swap_failures.append([orbit_key, budget])

            if fixture_index in (0, FIXTURE_COUNT - 1) and budget in (1, 16):
                brute = brute_force_version_space(transitions, observations, budget)
                factorized = [(a, b) for a in compatible_a for b in compatible_b if a != b]
                factorized_controls.append({
                    "pair_orbit_key": orbit_key,
                    "trajectory_budget": budget,
                    "ordered_version_space_size": len(factorized),
                    "factorized_hash": canonical_hash(factorized),
                    "brute_force_hash": canonical_hash(brute),
                    "passed": factorized == brute,
                })

        prior_by_fixture[orbit_key] = {
            "compatible_A_at_16": sorted(previous_a or set()),
            "compatible_B_at_16": sorted(previous_b or set()),
        }

    budget_summaries = {}
    candidate_flags = []
    for budget in BUDGETS:
        records = [record for record in ledger if record["trajectory_budget"] == budget]
        total_queries = FIXTURE_COUNT * QUERY_COUNT
        identifiable = sum(record["identifiable_query_count"] for record in records)
        unidentifiable = sum(record["unidentifiable_query_count"] for record in records)
        system_count = sum(record["system_identified"] for record in records)
        qualifying = [record for record in records if record["effective_unordered_hypothesis_count"] >= 8 and record["distinct_partition_relation_count"] >= 2]
        consensus_total = sum(record["consensus_without_identification_query_count"] for record in qualifying)
        consensus_same = sum(record["identifiable_same_count"] for record in qualifying)
        consensus_different = sum(record["identifiable_different_count"] for record in qualifying)
        construction_valid = all(record["true_pair_in_version_space"] and record["ordered_version_space_size"] > 0 for record in records)
        global_coverage = identifiable / total_queries
        floor_coverage = min(record["identifiable_query_count"] / QUERY_COUNT for record in records)
        same_fraction = consensus_same / consensus_total if consensus_total else 0.0
        different_fraction = consensus_different / consensus_total if consensus_total else 0.0
        conditions = {
            "construction_valid": construction_valid,
            "global_identifiable_coverage_ge_0_95": global_coverage >= 0.95,
            "per_fixture_floor_ge_0_80": floor_coverage >= 0.80,
            "qualifying_fixture_count_ge_100": len(qualifying) >= 100,
            "consensus_query_count_ge_50000": consensus_total >= 50000,
            "consensus_same_fraction_ge_0_20": same_fraction >= 0.20,
            "consensus_different_fraction_ge_0_20": different_fraction >= 0.20,
            "system_identified_fixture_fraction_lt_0_50": system_count / FIXTURE_COUNT < 0.50,
        }
        candidate = all(conditions.values())
        candidate_flags.append(candidate)
        budget_summaries[str(budget)] = {
            "fixture_count": len(records),
            "total_query_count": total_queries,
            "identifiable_query_count": identifiable,
            "unidentifiable_query_count": unidentifiable,
            "global_identifiable_coverage": global_coverage,
            "minimum_fixture_identifiable_coverage": floor_coverage,
            "system_identified_fixture_count": system_count,
            "system_identified_fixture_fraction": system_count / FIXTURE_COUNT,
            "qualifying_consensus_fixture_count": len(qualifying),
            "consensus_without_identification_query_count": consensus_total,
            "consensus_identifiable_same_count": consensus_same,
            "consensus_identifiable_different_count": consensus_different,
            "consensus_same_fraction": same_fraction,
            "consensus_different_fraction": different_fraction,
            "candidate_conditions": conditions,
            "consensus_candidate_budget": candidate,
        }

    consecutive = [BUDGETS[index] for index in range(len(BUDGETS) - 1) if candidate_flags[index] and candidate_flags[index + 1]]
    earliest_admitted = min(consecutive) if consecutive else None

    first_fixture = fixtures[0]
    first_observations = generate_observations(*first_fixture, assignments, transitions)
    corrupted = [trajectory[:] for trajectory in first_observations]
    predecessor, token, successor = corrupted[0][0]
    corrupted[0][0] = (predecessor, token, successor ^ 1)
    corrupt_a, corrupt_b = masks_for_budget(transitions_device, corrupted, 1)
    corrupt_true_in = first_fixture[0] in corrupt_a and first_fixture[1] in corrupt_b
    corrupt_unordered, corrupt_ordered_size = effective_pairs(corrupt_a, corrupt_b)

    sample_key = (f"{fixtures[0][0]},{fixtures[0][1]}", BUDGETS[0])
    sample_vector = vector_by_key[sample_key]
    reversed_vector = list(reversed(sample_vector))
    mutated_vector = sample_vector[:]
    mutated_vector[0] = (mutated_vector[0] + 1) % 3
    controls = {
        "factorized_vs_brute_force": {
            "cases": factorized_controls,
            "all_pass": len(factorized_controls) == 4 and all(case["passed"] for case in factorized_controls),
        },
        "action_token_swap": {
            "fixture_budget_cases_checked": FIXTURE_COUNT * len(BUDGETS),
            "failure_count": len(action_swap_failures),
            "failures": action_swap_failures,
            "all_pass": not action_swap_failures,
        },
        "corrupted_observed_transition": {
            "fixture": list(first_fixture),
            "budget": 1,
            "ordered_version_space_size": corrupt_ordered_size,
            "effective_unordered_hypothesis_count": len(corrupt_unordered),
            "true_pair_still_present": corrupt_true_in,
            "passed": corrupt_ordered_size == 0 or not corrupt_true_in,
        },
        "query_order_permutation": {
            "counts_preserved": Counter(sample_vector) == Counter(reversed_vector),
            "ordered_hash_changed": canonical_hash(sample_vector) != canonical_hash(reversed_vector),
        },
        "identifiability_vector_mutation": {
            "hash_changed": canonical_hash(sample_vector) != canonical_hash(mutated_vector),
        },
    }
    controls["query_order_permutation"]["all_pass"] = all(controls["query_order_permutation"].values())
    controls["identifiability_vector_mutation"]["all_pass"] = controls["identifiability_vector_mutation"]["hash_changed"]

    required_fields = spec["required_budget_record_fields"]
    tests = {
        "frozen_inputs_verified_before_computation": frozen_inputs["all_pass"],
        "frozen_manifests_verified": manifest["all_pass"],
        "stable_partition_census_converged": refinement["all_pass"],
        "complete_531_by_5_ledger": len(ledger) == FIXTURE_COUNT * len(BUDGETS),
        "every_required_budget_field_present": all(all(field in record for field in required_fields) for record in ledger),
        "true_pair_present_and_version_nonempty": all(record["true_pair_in_version_space"] and record["ordered_version_space_size"] > 0 for record in ledger),
        "version_spaces_nested_monotonically": not nested_failures,
        "unidentifiable_sets_monotonically_nonincreasing": not ambiguity_failures,
        "factorized_matches_brute_force": controls["factorized_vs_brute_force"]["all_pass"],
        "action_token_swap_preserves_object_relation": controls["action_token_swap"]["all_pass"],
        "corrupted_transition_excludes_truth_or_empties_version": controls["corrupted_observed_transition"]["passed"],
        "query_order_permutation_detected": controls["query_order_permutation"]["all_pass"],
        "identifiability_vector_mutation_detected": controls["identifiability_vector_mutation"]["all_pass"],
        "all_budget_query_counts_close": all(record["identifiable_query_count"] + record["unidentifiable_query_count"] == QUERY_COUNT for record in ledger),
    }

    if earliest_admitted is not None:
        regime_label = "PERCEPTION_LIKE_INFORMATION_WINDOW_PRESENT_JAX_ONLY"
    elif all(summary["system_identified_fixture_fraction"] >= 0.90 for summary in budget_summaries.values()):
        regime_label = spec["regime_classification"]["failure_labels"]["system_identification"]
    elif all(summary["global_identifiable_coverage"] < 0.95 for summary in budget_summaries.values()):
        regime_label = spec["regime_classification"]["failure_labels"]["information_missing"]
    else:
        regime_label = spec["regime_classification"]["failure_labels"]["mixed_or_no_window"]

    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "ran": True,
        "reads_peer_result": False,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_sha256": sha256_file(Path(__file__)),
        "source_path": str(Path(__file__).resolve().relative_to(HERE.parents[2])),
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "numpy_used": False,
        "peer_result_files_read": [],
        "parent_result_files_read": [],
        "source_semantics_read": ["system_v7/sims/eca_behavioral_refinement_depth_census_v1/run_jax.py"],
        "frozen_input_verification": frozen_inputs,
        "manifest_receipt": manifest,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls_receipt(),
        "carrier": {"ring_size": RING_SIZE, "state_count": STATE_COUNT, "rule_count": RULE_COUNT},
        "fixture_count": FIXTURE_COUNT,
        "budget_count": len(BUDGETS),
        "query_count_per_fixture": QUERY_COUNT,
        "stable_partition_census": refinement,
        "transition_census_hash": canonical_hash(transitions),
        "stable_partition_census_hash": canonical_hash(invariant_partition_hashes),
        "budget_summaries": budget_summaries,
        "perception_like_regime_admitted": earliest_admitted is not None,
        "earliest_admitted_budget": earliest_admitted,
        "regime_label": regime_label,
        "ledger_hash": canonical_hash(ledger),
        "budget_ledger": ledger,
        "controls": controls,
        "control_failures": {
            "version_space_nesting": nested_failures,
            "ambiguity_monotonicity": ambiguity_failures,
        },
        "tests": tests,
        "all_pass": all(tests.values()),
        "all_scientific_gates_pass": False,
        "elapsed_seconds": time.time() - started,
        "allowed_claims": ["independent exhaustive JAX finite ECA partial-observation identifiability census"],
        "claim_ceiling": "independent JAX scratch census only until Julia and a controller compare every required ledger field",
        "blocked_consumers": spec["blocked_consumers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    spec, frozen_inputs = verify_frozen_inputs()
    receipt = build_receipt(spec, frozen_inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({
        "sim_id": SIM_ID,
        "engine": "jax",
        "all_pass": receipt["all_pass"],
        "output": str(args.output),
        "regime_label": receipt["regime_label"],
        "perception_like_regime_admitted": receipt["perception_like_regime_admitted"],
        "earliest_admitted_budget": receipt["earliest_admitted_budget"],
        "ledger_hash": receipt["ledger_hash"],
        "elapsed_seconds": receipt["elapsed_seconds"],
    }, sort_keys=True))
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
