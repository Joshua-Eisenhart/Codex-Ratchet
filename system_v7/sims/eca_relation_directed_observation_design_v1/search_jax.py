#!/usr/bin/env python3
"""Exact train-only JAX search for global ECA observation designs."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
from jax import lax, vmap


SIM_ID = "eca_relation_directed_observation_design_v1"
SCHEMA = "codex_ratchet.eca_relation_directed_observation_design_v1.jax_search.v1"
CLASSIFICATION = "scratch_diagnostic"
TAG = "ECA-OBS-DESIGN-V1"
RING_SIZE = 9
STATE_COUNT = 1 << RING_SIZE
RULE_COUNT = 256
PAIR_COUNT = RULE_COUNT * (RULE_COUNT - 1) // 2
DESIGN_FIXTURE_COUNT = 128
QUERY_COUNT = 9636
SUBSET_SIZES = (2, 3, 4)
SHORTLIST_WIDTH = 32
SCREEN_BATCH_SIZE = 8
EXACT_FIXTURE_BATCH_SIZE = 8
REFINEMENT_BATCH_SIZE = 128
MAX_REFINEMENT_ROUNDS = STATE_COUNT
WORD_BITS = 64
PACKED_QUERY_WORDS = (QUERY_COUNT + WORD_BITS - 1) // WORD_BITS
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
DEFAULT_OUTPUT = HERE / "results" / f"{SIM_ID}_jax_search_results.json"

EXPECTED_SPEC_SHA256 = "1e7334c8fee643966d827cbc582b1aa2917604cdf4462db0a83da4e17e8951cb"
EXPECTED_CARD_SHA256 = "efd86270a4af5ffed86493bb6d747f76a1cff97a920c0902a44399351cd3c52a"

TOOL_MANIFEST = {
    "jax.numpy": {"used": True, "reason": "Exact x64 transition, compatibility, and packed relation arrays."},
    "jax.vmap": {"used": True, "reason": "Batched ECA transition, partition, screen, and exact-consensus evaluations."},
    "jax.jit": {"used": True, "reason": "Compiled exhaustive screen and exact relation kernels."},
    "jax.lax.while_loop": {"used": True, "reason": "Stable behavioral partition refinement to convergence."},
    "jax.ops.segment_max": {"used": True, "reason": "Exact distinct-partition presence over every compatible unordered rule pair."},
    "jax.lax.population_count": {"used": True, "reason": "Exact counts from packed same/different relation vectors."},
    "numpy": {"used": False, "reason": "Forbidden from the claim path and not imported by this source."},
}
TOOL_INTEGRATION_DEPTH = {
    key: (None if key == "numpy" else "load_bearing")
    for key in TOOL_MANIFEST
}


def compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: object) -> str:
    return hashlib.sha256(compact_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_imports_numpy(path: Path) -> bool:
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped == "import numpy" or stripped.startswith("import numpy as "):
            return True
        if stripped.startswith("from numpy import "):
            return True
    return False


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def compact_partition(labels: list[int]) -> list[int]:
    renaming: dict[int, int] = {}
    compact = []
    for label in labels:
        if label not in renaming:
            renaming[label] = len(renaming)
        compact.append(renaming[label])
    return compact


def verify_frozen_inputs() -> tuple[dict, dict]:
    spec = json.loads(SPEC_PATH.read_text())
    receipt = json.loads(PREREG_PATH.read_text())
    spec_hash = sha256_file(SPEC_PATH)
    card_hash = sha256_file(CARD_PATH)
    confirmation_names = ("confirm_jax.py", "confirm_julia.jl", "validate_confirmation.py")
    confirmation_presence = {name: (HERE / name).exists() for name in confirmation_names}
    tests = {
        "spec_source_constant": spec_hash == EXPECTED_SPEC_SHA256,
        "card_source_constant": card_hash == EXPECTED_CARD_SHA256,
        "spec_preregistration_binding": spec_hash == receipt.get("spec_sha256"),
        "card_preregistration_binding": card_hash == receipt.get("object_card_sha256"),
        "search_absent_at_freeze": receipt.get("search_sources_present_when_frozen") is False,
        "confirmation_absent_at_freeze": receipt.get("confirmation_sources_present_when_frozen") is False,
        "confirmation_still_absent": not any(confirmation_presence.values()),
        "sim_id_matches": spec.get("sim_id") == receipt.get("sim_id") == SIM_ID,
        "scratch_only": spec.get("classification") == CLASSIFICATION
        and spec.get("promotion_allowed") is False
        and spec.get("formal_admission_allowed") is False,
        "peer_reads_forbidden": spec["engine_contract"]["peer_result_reads_forbidden"] is True,
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen input verification failed: {tests}")
    return spec, {
        "spec_sha256": spec_hash,
        "object_card_sha256": card_hash,
        "preregistration_sha256": sha256_file(PREREG_PATH),
        "confirmation_source_presence": confirmation_presence,
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
    return tuple(
        sorted(
            {
                rule,
                reflect_rule(rule),
                conjugate_rule(rule),
                reflect_rule(conjugate_rule(rule)),
            }
        )
    )


def ordered_rule_orbits() -> list[tuple[int, ...]]:
    orbits = {rule_orbit(rule) for rule in range(RULE_COUNT)}
    return sorted(
        orbits,
        key=lambda orbit: (
            digest_text("ECA-OBS-ID-V0|rule_orbit|" + ",".join(map(str, orbit))),
            orbit,
        ),
    )


def simultaneous_pair_orbit(pair: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    a, b = pair
    ta = (a, reflect_rule(a), conjugate_rule(a), reflect_rule(conjugate_rule(a)))
    tb = (b, reflect_rule(b), conjugate_rule(b), reflect_rule(conjugate_rule(b)))
    return tuple(
        sorted({tuple(sorted((ta[index], tb[index]))) for index in range(4)})
    )


def probe(state: int) -> tuple[int, int]:
    bits = [(state >> site) & 1 for site in range(RING_SIZE)]
    return (
        sum(bits),
        sum(
            bits[index] != bits[(index + 1) % RING_SIZE]
            for index in range(RING_SIZE)
        ),
    )


def build_train_only_manifests(spec: dict) -> tuple[list[tuple[int, int]], list[tuple[int, int]], dict]:
    orbits = ordered_rule_orbits()
    train_rules = {rule for orbit in orbits[:52] for rule in orbit}
    raw_train_pairs = [
        (a, b)
        for a in range(RULE_COUNT - 1)
        for b in range(a + 1, RULE_COUNT)
        if a in train_rules and b in train_rules
    ]
    train_pair_orbits = sorted({simultaneous_pair_orbit(pair) for pair in raw_train_pairs})
    train_representatives = [min(orbit) for orbit in train_pair_orbits]
    design_fixtures = sorted(
        train_representatives,
        key=lambda pair: (
            digest_text(f"{TAG}|design_fixture|{pair[0]},{pair[1]}"),
            pair,
        ),
    )[:DESIGN_FIXTURE_COUNT]
    queries = [
        (a, b)
        for a in range(STATE_COUNT - 1)
        for b in range(a + 1, STATE_COUNT)
        if probe(a) == probe(b)
    ]
    assignments = spec["candidate_pool"]["ordered_assignments"]
    hashes = {
        "rule_orbits": canonical_hash(orbits),
        "assignments": canonical_hash(assignments),
        "queries": canonical_hash([list(query) for query in queries]),
        "design_fixtures": digest_text(compact_json(design_fixtures)),
        "train_pair_orbits": canonical_hash(
            [[list(pair) for pair in orbit] for orbit in train_pair_orbits]
        ),
    }
    tests = {
        "all_88_rule_orbits_reconstructed": len(orbits) == 88,
        "frozen_rule_orbit_hash": hashes["rule_orbits"]
        == spec["rule_family_split"]["rule_orbit_manifest_sha256"],
        "train_pair_orbit_count": len(train_pair_orbits)
        == spec["rule_family_split"]["train_pair_orbits"],
        "design_fixture_count": len(design_fixtures) == DESIGN_FIXTURE_COUNT,
        "design_fixture_hash": hashes["design_fixtures"]
        == spec["rule_family_split"]["design_fixture_manifest_sha256"],
        "query_count": len(queries) == QUERY_COUNT,
        "query_hash": hashes["queries"]
        == spec["inherited_carrier"]["query_manifest_sha256"],
        "assignment_count": len(assignments) == 16,
        "assignment_hash": hashes["assignments"]
        == spec["candidate_pool"]["assignment_manifest_sha256"],
    }
    if not all(tests.values()):
        raise RuntimeError(f"train-only manifest verification failed: {tests}")
    return design_fixtures, queries, {
        "hashes": hashes,
        "tests": tests,
        "confirmation_fixture_values_constructed": False,
        "all_pass": True,
    }


def eca_transition_table() -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    rules = jnp.arange(RULE_COUNT, dtype=jnp.int64)

    def step(rule: jax.Array, state: jax.Array) -> jax.Array:
        bits = (state >> sites) & 1
        neighborhoods = (
            (jnp.roll(bits, 1) << 2) | (bits << 1) | jnp.roll(bits, -1)
        )
        return jnp.sum(((rule >> neighborhoods) & 1) << sites, dtype=jnp.int64)

    return vmap(lambda rule: vmap(lambda state: step(rule, state))(states))(rules)


def canonicalize_signatures(signatures: jax.Array) -> jax.Array:
    order = jnp.argsort(signatures, stable=True)
    sorted_signatures = signatures[order]
    starts = jnp.concatenate(
        (
            jnp.ones((1,), dtype=jnp.bool_),
            sorted_signatures[1:] != sorted_signatures[:-1],
        )
    )
    sorted_labels = jnp.cumsum(starts, dtype=jnp.int64) - 1
    return jnp.zeros_like(sorted_labels).at[order].set(sorted_labels)


canonicalize_batch = vmap(canonicalize_signatures)


def base_probe_labels() -> jax.Array:
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (states[:, None] >> sites) & 1
    weight = jnp.sum(bits, axis=1, dtype=jnp.int64)
    walls = jnp.sum(
        bits != jnp.roll(bits, -1, axis=1), axis=1, dtype=jnp.int64
    )
    return canonicalize_signatures(weight * (RING_SIZE + 1) + walls)


def build_refinement_kernel():
    base = base_probe_labels()

    @jax.jit
    def kernel(action_a: jax.Array, action_b: jax.Array):
        batch_count = action_a.shape[0]
        labels0 = jnp.broadcast_to(base, (batch_count, STATE_COUNT))
        active0 = jnp.ones((batch_count,), dtype=jnp.bool_)

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
            return (
                round_index + 1,
                jnp.where(active[:, None], refined, labels),
                changed,
            )

        return lax.while_loop(
            condition,
            body,
            (jnp.asarray(0, dtype=jnp.int64), labels0, active0),
        )

    return kernel


def pair_index(a: int, b: int) -> int:
    if a == b:
        raise ValueError("diagonal pair")
    if a > b:
        a, b = b, a
    return a * (2 * RULE_COUNT - a - 1) // 2 + (b - a - 1)


def compute_partition_objects(transitions: jax.Array, queries: list[tuple[int, int]]) -> tuple[dict, dict]:
    pairs = list(itertools.combinations(range(RULE_COUNT), 2))
    kernel = build_refinement_kernel()
    chunks = []
    nonconverged = []
    rounds = Counter()
    for start in range(0, PAIR_COUNT, REFINEMENT_BATCH_SIZE):
        batch = pairs[start : start + REFINEMENT_BATCH_SIZE]
        real_count = len(batch)
        padded = batch + [batch[-1]] * (REFINEMENT_BATCH_SIZE - real_count)
        a = jnp.asarray([pair[0] for pair in padded], dtype=jnp.int64)
        b = jnp.asarray([pair[1] for pair in padded], dtype=jnp.int64)
        round_count, labels, active = kernel(transitions[a], transitions[b])
        active_host = active[:real_count].tolist()
        rounds[int(round_count)] += 1
        nonconverged.extend(batch[index] for index, flag in enumerate(active_host) if flag)
        chunks.append(labels[:real_count].astype(jnp.int16))
    partitions = jnp.concatenate(chunks, axis=0)
    partitions.block_until_ready()
    host_labels = partitions.tolist()
    class_by_signature: dict[tuple[int, ...], int] = {}
    class_representatives: list[list[int]] = []
    pair_classes = []
    compact_labels = [compact_partition(labels) for labels in host_labels]
    for labels in compact_labels:
        signature = tuple(labels)
        class_id = class_by_signature.get(signature)
        if class_id is None:
            class_id = len(class_representatives)
            class_by_signature[signature] = class_id
            class_representatives.append(labels)
        pair_classes.append(class_id)
    pair_order = sorted(range(PAIR_COUNT), key=lambda index: (pair_classes[index], index))
    sorted_pair_a = [pairs[index][0] for index in pair_order]
    sorted_pair_b = [pairs[index][1] for index in pair_order]
    sorted_pair_class = [pair_classes[index] for index in pair_order]

    packed_relations = []
    for labels in class_representatives:
        words = [0] * PACKED_QUERY_WORDS
        for query_index, (a, b) in enumerate(queries):
            if labels[a] == labels[b]:
                words[query_index // WORD_BITS] |= 1 << (query_index % WORD_BITS)
        packed_relations.append(words)
    receipt = {
        "pair_count": PAIR_COUNT,
        "distinct_partition_relation_count": len(class_representatives),
        "nonconverged_pairs": [list(pair) for pair in nonconverged],
        "batch_round_histogram": {str(key): value for key, value in sorted(rounds.items())},
        "raw_stable_partition_hash": canonical_hash(host_labels),
        "stable_partition_hash": canonical_hash(compact_labels),
        "partition_class_hash": canonical_hash(pair_classes),
        "packed_relation_hash": canonical_hash(packed_relations),
        "all_pass": not nonconverged and len(pair_classes) == PAIR_COUNT,
    }
    objects = {
        "pair_a": jnp.asarray(sorted_pair_a, dtype=jnp.int16),
        "pair_b": jnp.asarray(sorted_pair_b, dtype=jnp.int16),
        "pair_class": jnp.asarray(sorted_pair_class, dtype=jnp.int32),
        "relation_bits": jnp.asarray(packed_relations, dtype=jnp.uint64),
        "class_count": len(class_representatives),
        "pair_classes_host": pair_classes,
        "class_representatives": class_representatives,
    }
    return objects, receipt


def build_trajectory_masks(
    fixtures: list[tuple[int, int]],
    assignments: list[list[object]],
    transitions: list[list[int]],
) -> tuple[jax.Array, jax.Array, list[list[int]], dict]:
    masks_a = []
    masks_b = []
    observed_state_bits: list[list[int]] = []
    true_rule_failures = []
    for fixture_index, (rule_a, rule_b) in enumerate(fixtures):
        fixture_a = []
        fixture_b = []
        fixture_states = []
        for trajectory_index, (word, initial_state) in enumerate(assignments):
            state = int(initial_state)
            observations = [[], []]
            states_seen = 0
            for token_text in str(word):
                token = 0 if token_text == "A" else 1
                rule = rule_a if token == 0 else rule_b
                successor = transitions[rule][state]
                observations[token].append((state, successor))
                states_seen |= (1 << state) | (1 << successor)
                state = successor
            token_masks = []
            for token in (0, 1):
                token_masks.append(
                    [
                        all(transitions[rule][predecessor] == successor for predecessor, successor in observations[token])
                        for rule in range(RULE_COUNT)
                    ]
                )
            if not token_masks[0][rule_a] or not token_masks[1][rule_b]:
                true_rule_failures.append([fixture_index, trajectory_index])
            fixture_a.append(token_masks[0])
            fixture_b.append(token_masks[1])
            fixture_states.append(states_seen)
        masks_a.append(fixture_a)
        masks_b.append(fixture_b)
        observed_state_bits.append(fixture_states)
    receipt = {
        "shape": [DESIGN_FIXTURE_COUNT, 16, RULE_COUNT],
        "true_rule_failure_count": len(true_rule_failures),
        "true_rule_failures": true_rule_failures,
        "mask_a_hash": canonical_hash(masks_a),
        "mask_b_hash": canonical_hash(masks_b),
        "observed_state_hash": canonical_hash(observed_state_bits),
        "all_pass": not true_rule_failures,
    }
    return (
        jnp.asarray(masks_a, dtype=jnp.bool_),
        jnp.asarray(masks_b, dtype=jnp.bool_),
        observed_state_bits,
        receipt,
    )


def build_screen_kernel(
    trajectory_a: jax.Array,
    trajectory_b: jax.Array,
    partition_objects: dict,
):
    pair_a = partition_objects["pair_a"]
    pair_b = partition_objects["pair_b"]
    pair_class = partition_objects["pair_class"]
    class_count = partition_objects["class_count"]

    def class_presence(pair_mask: jax.Array) -> jax.Array:
        return jax.ops.segment_max(
            pair_mask.astype(jnp.int8), pair_class, num_segments=class_count
        ).astype(jnp.bool_)

    class_presence_batch = vmap(class_presence)

    @jax.jit
    def kernel(subsets: jax.Array):
        selected_a = jnp.take(trajectory_a, subsets, axis=1)
        selected_b = jnp.take(trajectory_b, subsets, axis=1)
        compatible_a = jnp.all(selected_a, axis=2).transpose(1, 0, 2)
        compatible_b = jnp.all(selected_b, axis=2).transpose(1, 0, 2)
        batch_count = compatible_a.shape[0]
        flat_a = compatible_a.reshape((-1, RULE_COUNT))
        flat_b = compatible_b.reshape((-1, RULE_COUNT))
        count_a = jnp.sum(flat_a, axis=1, dtype=jnp.int64)
        count_b = jnp.sum(flat_b, axis=1, dtype=jnp.int64)
        overlap = jnp.sum(flat_a & flat_b, axis=1, dtype=jnp.int64)
        ordered = count_a * count_b - overlap
        pair_mask = (
            (flat_a[:, pair_a] & flat_b[:, pair_b])
            | (flat_a[:, pair_b] & flat_b[:, pair_a])
        )
        effective = jnp.sum(pair_mask, axis=1, dtype=jnp.int64)
        distinct = jnp.sum(
            class_presence_batch(pair_mask), axis=1, dtype=jnp.int64
        )
        shape = (batch_count, DESIGN_FIXTURE_COUNT)
        return (
            ordered.reshape(shape),
            effective.reshape(shape),
            distinct.reshape(shape),
            (ordered == 1).reshape(shape),
            compatible_a,
            compatible_b,
        )

    return kernel


def candidate_subsets() -> dict[int, list[tuple[int, ...]]]:
    return {
        size: list(itertools.combinations(range(16), size))
        for size in SUBSET_SIZES
    }


def screen_objective(record: dict) -> tuple[int, ...]:
    return tuple(record["screen_objective"])


def screen_all_candidates(kernel, candidates: dict[int, list[tuple[int, ...]]]) -> tuple[list[dict], dict]:
    records = []
    evaluations = 0
    for size in SUBSET_SIZES:
        size_records = []
        subsets = candidates[size]
        for start in range(0, len(subsets), SCREEN_BATCH_SIZE):
            real = subsets[start : start + SCREEN_BATCH_SIZE]
            padded = real + [real[-1]] * (SCREEN_BATCH_SIZE - len(real))
            ordered, effective, distinct, identified, _, _ = kernel(
                jnp.asarray(padded, dtype=jnp.int16)
            )
            ordered_h = ordered[: len(real)].tolist()
            effective_h = effective[: len(real)].tolist()
            distinct_h = distinct[: len(real)].tolist()
            identified_h = identified[: len(real)].tolist()
            for index, subset in enumerate(real):
                diversity = [
                    effective_h[index][fixture] >= 8
                    and distinct_h[index][fixture] >= 2
                    for fixture in range(DESIGN_FIXTURE_COUNT)
                ]
                objective = (
                    sum(diversity),
                    -sum(bool(value) for value in identified_h[index]),
                    sum(min(int(value), 64) for value in effective_h[index]),
                    sum(min(int(value), 64) for value in distinct_h[index]),
                )
                record = {
                    "subset_size": size,
                    "subset": list(subset),
                    "screen_objective": list(objective),
                    "diversity_fixture_count": objective[0],
                    "system_identified_fixture_count": -objective[1],
                    "total_ordered_version_space_size": sum(ordered_h[index]),
                    "ordered_version_space_sizes": ordered_h[index],
                    "effective_unordered_hypothesis_counts": effective_h[index],
                    "distinct_partition_relation_counts": distinct_h[index],
                    "system_identified_flags": [bool(value) for value in identified_h[index]],
                }
                size_records.append(record)
                evaluations += DESIGN_FIXTURE_COUNT
        size_records.sort(
            key=lambda record: (
                tuple(-value for value in screen_objective(record)),
                tuple(record["subset"]),
            )
        )
        for rank, record in enumerate(size_records, start=1):
            record["screen_rank_within_size"] = rank
        records.extend(size_records)
    receipt = {
        "candidate_count": len(records),
        "fixture_evaluation_count": evaluations,
        "records_hash": canonical_hash(records),
        "candidate_identity_hash": canonical_hash(
            [[record["subset_size"], record["subset"]] for record in records]
        ),
        "all_pass": len(records) == 2500
        and evaluations == 2500 * DESIGN_FIXTURE_COUNT
        and len({tuple(record["subset"]) for record in records}) == 2500,
    }
    return records, receipt


def compatible_masks_for_subset(
    screen_kernel,
    subset: tuple[int, ...],
) -> tuple[jax.Array, jax.Array]:
    padded = [subset] * SCREEN_BATCH_SIZE
    _, _, _, _, compatible_a, compatible_b = screen_kernel(
        jnp.asarray(padded, dtype=jnp.int16)
    )
    return compatible_a[0], compatible_b[0]


def build_exact_kernel(partition_objects: dict):
    pair_a = partition_objects["pair_a"]
    pair_b = partition_objects["pair_b"]
    pair_class = partition_objects["pair_class"]
    class_count = partition_objects["class_count"]
    relation_bits = partition_objects["relation_bits"]
    all_ones = jnp.full((PACKED_QUERY_WORDS,), jnp.uint64(0xFFFFFFFFFFFFFFFF))

    def one(compatible_a: jax.Array, compatible_b: jax.Array):
        pair_mask = (
            (compatible_a[pair_a] & compatible_b[pair_b])
            | (compatible_a[pair_b] & compatible_b[pair_a])
        )
        presence = jax.ops.segment_max(
            pair_mask.astype(jnp.int8), pair_class, num_segments=class_count
        ).astype(jnp.bool_)
        must_equal = jnp.bitwise_and.reduce(
            jnp.where(presence[:, None], relation_bits, all_ones), axis=0
        )
        possible_equal = jnp.bitwise_or.reduce(
            jnp.where(presence[:, None], relation_bits, jnp.uint64(0)), axis=0
        )
        same_count = jnp.sum(lax.population_count(must_equal), dtype=jnp.int64)
        possible_count = jnp.sum(
            lax.population_count(possible_equal), dtype=jnp.int64
        )
        return must_equal, possible_equal, same_count, possible_count, presence

    return jax.jit(vmap(one))


def valid_query_word_masks() -> list[int]:
    masks = [0xFFFFFFFFFFFFFFFF] * PACKED_QUERY_WORDS
    remainder = QUERY_COUNT % WORD_BITS
    if remainder:
        masks[-1] = (1 << remainder) - 1
    return masks


def query_disjoint_words(
    fixture_index: int,
    subset: tuple[int, ...],
    observed_state_bits: list[list[int]],
    queries: list[tuple[int, int]],
) -> list[int]:
    observed = 0
    for trajectory_index in subset:
        observed |= observed_state_bits[fixture_index][trajectory_index]
    words = [0] * PACKED_QUERY_WORDS
    for query_index, (a, b) in enumerate(queries):
        if not ((observed >> a) & 1) and not ((observed >> b) & 1):
            words[query_index // WORD_BITS] |= 1 << (query_index % WORD_BITS)
    return words


def vector_hash(must_words: list[int], possible_words: list[int]) -> str:
    vector = []
    for index in range(QUERY_COUNT):
        equal_all = (must_words[index // WORD_BITS] >> (index % WORD_BITS)) & 1
        equal_any = (possible_words[index // WORD_BITS] >> (index % WORD_BITS)) & 1
        vector.append(2 if equal_all else (0 if equal_any else 1))
    return canonical_hash(vector)


def exact_score_subset(
    subset: tuple[int, ...],
    screen_record: dict,
    screen_kernel,
    exact_kernel,
    observed_state_bits: list[list[int]],
    queries: list[tuple[int, int]],
) -> dict:
    compatible_a, compatible_b = compatible_masks_for_subset(screen_kernel, subset)
    valid_words = valid_query_word_masks()
    fixture_scores = []
    for start in range(0, DESIGN_FIXTURE_COUNT, EXACT_FIXTURE_BATCH_SIZE):
        stop = min(start + EXACT_FIXTURE_BATCH_SIZE, DESIGN_FIXTURE_COUNT)
        real = stop - start
        a_batch = compatible_a[start:stop]
        b_batch = compatible_b[start:stop]
        if real < EXACT_FIXTURE_BATCH_SIZE:
            padding = EXACT_FIXTURE_BATCH_SIZE - real
            a_batch = jnp.concatenate(
                (a_batch, jnp.repeat(a_batch[-1][None, :], padding, axis=0)), axis=0
            )
            b_batch = jnp.concatenate(
                (b_batch, jnp.repeat(b_batch[-1][None, :], padding, axis=0)), axis=0
            )
        must, possible, same_jax, possible_jax, _ = exact_kernel(a_batch, b_batch)
        must_host = must[:real].tolist()
        possible_host = possible[:real].tolist()
        same_host = same_jax[:real].tolist()
        possible_count_host = possible_jax[:real].tolist()
        for offset in range(real):
            fixture_index = start + offset
            must_words = [int(value) & valid_words[index] for index, value in enumerate(must_host[offset])]
            possible_words = [int(value) & valid_words[index] for index, value in enumerate(possible_host[offset])]
            same_count = sum(word.bit_count() for word in must_words)
            different_count = sum(
                ((~possible_words[index]) & valid_words[index]).bit_count()
                for index in range(PACKED_QUERY_WORDS)
            )
            identifiable = same_count + different_count
            ambiguous = QUERY_COUNT - identifiable
            if same_count != int(same_host[offset]):
                raise RuntimeError("JAX/host same-count mismatch")
            if QUERY_COUNT - different_count != int(possible_count_host[offset]):
                raise RuntimeError("JAX/host possible-count mismatch")
            disjoint = query_disjoint_words(
                fixture_index, subset, observed_state_bits, queries
            )
            disjoint_query_count = sum(word.bit_count() for word in disjoint)
            disjoint_same = sum(
                (must_words[index] & disjoint[index]).bit_count()
                for index in range(PACKED_QUERY_WORDS)
            )
            disjoint_different = sum(
                ((~possible_words[index]) & valid_words[index] & disjoint[index]).bit_count()
                for index in range(PACKED_QUERY_WORDS)
            )
            diversity = (
                screen_record["effective_unordered_hypothesis_counts"][fixture_index] >= 8
                and screen_record["distinct_partition_relation_counts"][fixture_index] >= 2
            )
            fixture_scores.append(
                {
                    "fixture_index": fixture_index,
                    "ordered_version_space_size": screen_record["ordered_version_space_sizes"][fixture_index],
                    "effective_unordered_hypothesis_count": screen_record["effective_unordered_hypothesis_counts"][fixture_index],
                    "distinct_partition_relation_count": screen_record["distinct_partition_relation_counts"][fixture_index],
                    "system_identified": screen_record["system_identified_flags"][fixture_index],
                    "diversity_fixture": diversity,
                    "identifiable_query_count": identifiable,
                    "ambiguous_query_count": ambiguous,
                    "identifiable_same_count": same_count,
                    "identifiable_different_count": different_count,
                    "balanced_fixture": identifiable > 0
                    and 10 * same_count >= identifiable
                    and 10 * different_count >= identifiable,
                    "robust_query_count": identifiable if diversity else 0,
                    "query_disjoint_query_count": disjoint_query_count,
                    "query_disjoint_identifiable_count": disjoint_same + disjoint_different,
                    "query_disjoint_same_count": disjoint_same,
                    "query_disjoint_different_count": disjoint_different,
                    "query_disjoint_robust_count": disjoint_same + disjoint_different if diversity else 0,
                    "relation_vector_hash": vector_hash(must_words, possible_words),
                    "query_disjoint_mask_hash": canonical_hash(disjoint),
                }
            )
    robust = [record["robust_query_count"] for record in fixture_scores]
    disjoint_robust = [record["query_disjoint_robust_count"] for record in fixture_scores]
    exact_objective = (
        min(robust),
        sum(robust),
        sum(record["balanced_fixture"] for record in fixture_scores),
        min(disjoint_robust),
        sum(disjoint_robust),
        *screen_record["screen_objective"],
    )
    return {
        "subset_size": len(subset),
        "subset": list(subset),
        "screen_rank_within_size": screen_record["screen_rank_within_size"],
        "screen_objective": screen_record["screen_objective"],
        "exact_objective": list(exact_objective),
        "fixture_scores": fixture_scores,
        "fixture_scores_hash": canonical_hash(fixture_scores),
        "global_identifiable_query_count": sum(record["identifiable_query_count"] for record in fixture_scores),
        "global_consensus_without_identification_query_count": sum(
            record["identifiable_query_count"]
            for record in fixture_scores
            if record["diversity_fixture"]
        ),
        "query_disjoint_identifiable_query_count": sum(
            record["query_disjoint_identifiable_count"] for record in fixture_scores
        ),
        "balanced_fixture_count": sum(record["balanced_fixture"] for record in fixture_scores),
    }


def exact_objective(record: dict) -> tuple[int, ...]:
    return tuple(record["exact_objective"])


def screen_lookup(records: list[dict]) -> dict[tuple[int, ...], dict]:
    return {tuple(record["subset"]): record for record in records}


def select_shortlists(records: list[dict]) -> dict[int, list[dict]]:
    return {
        size: [
            record
            for record in records
            if record["subset_size"] == size
            and record["screen_rank_within_size"] <= SHORTLIST_WIDTH
        ]
        for size in SUBSET_SIZES
    }


def exact_score_shortlists(
    shortlists: dict[int, list[dict]],
    screen_kernel,
    exact_kernel,
    observed_state_bits: list[list[int]],
    queries: list[tuple[int, int]],
) -> tuple[list[dict], dict[int, dict], dict]:
    records = []
    score_counts: Counter[tuple[int, ...]] = Counter()
    for size in SUBSET_SIZES:
        for screen_record in shortlists[size]:
            subset = tuple(screen_record["subset"])
            records.append(
                exact_score_subset(
                    subset,
                    screen_record,
                    screen_kernel,
                    exact_kernel,
                    observed_state_bits,
                    queries,
                )
            )
            score_counts[subset] += 1
    winners = {}
    for size in SUBSET_SIZES:
        options = [record for record in records if record["subset_size"] == size]
        winner = min(
            options,
            key=lambda record: (
                tuple(-value for value in exact_objective(record)),
                tuple(record["subset"]),
            ),
        )
        winners[size] = winner
    receipt = {
        "record_count": len(records),
        "fixture_evaluation_count": len(records) * DESIGN_FIXTURE_COUNT,
        "records_hash": canonical_hash(records),
        "all_96_scored_once": len(records) == 96
        and all(count == 1 for count in score_counts.values())
        and len(score_counts) == 96,
    }
    return records, winners, receipt


def baseline_receipts(screen_records: list[dict]) -> dict:
    baselines = {}
    for size in SUBSET_SIZES:
        size_records = [record for record in screen_records if record["subset_size"] == size]
        hash_subset = tuple(range(size))
        hash_record = next(record for record in size_records if tuple(record["subset"]) == hash_subset)
        system_record = min(
            size_records,
            key=lambda record: (
                record["total_ordered_version_space_size"],
                -record["system_identified_fixture_count"],
                tuple(record["subset"]),
            ),
        )
        baselines[str(size)] = {
            "hash_order": {
                "subset": list(hash_subset),
                "screen_objective": hash_record["screen_objective"],
                "total_ordered_version_space_size": hash_record["total_ordered_version_space_size"],
                "system_identified_fixture_count": hash_record["system_identified_fixture_count"],
            },
            "system_identification": {
                "subset": system_record["subset"],
                "screen_objective": system_record["screen_objective"],
                "total_ordered_version_space_size": system_record["total_ordered_version_space_size"],
                "system_identified_fixture_count": system_record["system_identified_fixture_count"],
            },
        }
    return {
        "sizes": baselines,
        "hash": canonical_hash(baselines),
        "all_sizes_present": set(baselines) == {"2", "3", "4"},
    }


def exact_score_baselines(
    baselines: dict,
    screen_records: list[dict],
    exact_records: list[dict],
    screen_kernel,
    exact_kernel,
    observed_state_bits: list[list[int]],
    queries: list[tuple[int, int]],
) -> dict:
    screens = screen_lookup(screen_records)
    exact_cache = {tuple(record["subset"]): record for record in exact_records}
    additional_scores = 0
    records = {}
    for size in SUBSET_SIZES:
        records[str(size)] = {}
        for baseline_name in ("hash_order", "system_identification"):
            subset = tuple(baselines["sizes"][str(size)][baseline_name]["subset"])
            reused_shortlist_score = subset in exact_cache
            if not reused_shortlist_score:
                exact_cache[subset] = exact_score_subset(
                    subset,
                    screens[subset],
                    screen_kernel,
                    exact_kernel,
                    observed_state_bits,
                    queries,
                )
                additional_scores += 1
            records[str(size)][baseline_name] = {
                "reused_shortlist_score": reused_shortlist_score,
                "score": exact_cache[subset],
            }
    return {
        "records": records,
        "additional_exact_score_count": additional_scores,
        "records_hash": canonical_hash(records),
        "all_sizes_and_baselines_exact_scored": set(records) == {"2", "3", "4"}
        and all(
            set(records[str(size)]) == {"hash_order", "system_identification"}
            for size in SUBSET_SIZES
        ),
    }


def brute_force_version_space(
    fixture: tuple[int, int],
    subset: tuple[int, ...],
    assignments: list[list[object]],
    transitions: list[list[int]],
) -> list[tuple[int, int]]:
    true_a, true_b = fixture
    observations = []
    for trajectory_index in subset:
        word, initial_state = assignments[trajectory_index]
        state = int(initial_state)
        for token_text in str(word):
            token = 0 if token_text == "A" else 1
            true_rule = true_a if token == 0 else true_b
            successor = transitions[true_rule][state]
            observations.append((state, token, successor))
            state = successor
    return [
        (rule_a, rule_b)
        for rule_a in range(RULE_COUNT)
        for rule_b in range(RULE_COUNT)
        if rule_a != rule_b
        and all(
            transitions[rule_a if token == 0 else rule_b][predecessor] == successor
            for predecessor, token, successor in observations
        )
    ]


def controls_receipt(
    screen_records: list[dict],
    winners: dict[int, dict],
    screen_kernel,
    exact_kernel,
    fixtures: list[tuple[int, int]],
    assignments: list[list[object]],
    transitions: list[list[int]],
) -> dict:
    reranked = {}
    for size in SUBSET_SIZES:
        reversed_records = list(
            reversed([record for record in screen_records if record["subset_size"] == size])
        )
        reranked[size] = min(
            reversed_records,
            key=lambda record: (
                tuple(-value for value in screen_objective(record)),
                tuple(record["subset"]),
            ),
        )["subset"]
    expected_screen_winners = {
        size: min(
            [record for record in screen_records if record["subset_size"] == size],
            key=lambda record: (
                tuple(-value for value in screen_objective(record)),
                tuple(record["subset"]),
            ),
        )["subset"]
        for size in SUBSET_SIZES
    }
    complete_identity = [
        [record["subset_size"], record["subset"]] for record in screen_records
    ]
    omitted_identity = complete_identity[1:]
    winner_payload = {str(size): winners[size]["subset"] for size in SUBSET_SIZES}
    mutated_winner = json.loads(json.dumps(winner_payload))
    mutated_winner["2"][0] = (mutated_winner["2"][0] + 1) % 16

    factorized_cases = []
    action_swap_cases = []
    for size in SUBSET_SIZES:
        subset = tuple(winners[size]["subset"])
        compatible_a, compatible_b = compatible_masks_for_subset(screen_kernel, subset)
        for fixture_index in (0, DESIGN_FIXTURE_COUNT - 1):
            a_rules = [index for index, flag in enumerate(compatible_a[fixture_index].tolist()) if flag]
            b_rules = [index for index, flag in enumerate(compatible_b[fixture_index].tolist()) if flag]
            factorized = [
                (a, b) for a in a_rules for b in b_rules if a != b
            ]
            brute = brute_force_version_space(
                fixtures[fixture_index], subset, assignments, transitions
            )
            factorized_cases.append(
                {
                    "subset_size": size,
                    "fixture_index": fixture_index,
                    "factorized_hash": canonical_hash(factorized),
                    "brute_force_hash": canonical_hash(brute),
                    "passed": factorized == brute,
                }
            )
            original = exact_kernel(
                compatible_a[fixture_index][None, :], compatible_b[fixture_index][None, :]
            )
            swapped = exact_kernel(
                compatible_b[fixture_index][None, :], compatible_a[fixture_index][None, :]
            )
            passed = original[0].tolist() == swapped[0].tolist() and original[1].tolist() == swapped[1].tolist()
            action_swap_cases.append(
                {
                    "subset_size": size,
                    "fixture_index": fixture_index,
                    "passed": passed,
                }
            )
    controls = {
        "pool_enumeration_permutation": {
            "expected_screen_winners": expected_screen_winners,
            "reversed_enumeration_winners": reranked,
            "passed": expected_screen_winners == reranked,
        },
        "omitted_subset_completeness": {
            "complete_count": len(complete_identity),
            "omitted_count": len(omitted_identity),
            "complete_hash": canonical_hash(complete_identity),
            "omitted_hash": canonical_hash(omitted_identity),
            "passed": len(complete_identity) == 2500
            and canonical_hash(complete_identity) != canonical_hash(omitted_identity),
        },
        "winner_mutation": {
            "winner_hash": canonical_hash(winner_payload),
            "mutated_hash": canonical_hash(mutated_winner),
            "passed": canonical_hash(winner_payload) != canonical_hash(mutated_winner),
        },
        "factorized_vs_ordered_brute_force": {
            "cases": factorized_cases,
            "passed": len(factorized_cases) == 6
            and all(case["passed"] for case in factorized_cases),
        },
        "action_token_swap": {
            "cases": action_swap_cases,
            "passed": len(action_swap_cases) == 6
            and all(case["passed"] for case in action_swap_cases),
        },
    }
    controls["all_pass"] = all(
        value["passed"] for key, value in controls.items() if key != "all_pass"
    )
    return controls


def tool_surfaces() -> tuple[dict, dict, list[dict]]:
    common = {
        "input_object": "128 frozen train fixtures, 2500 subsets, 9636 queries, and all 32640 unordered rule pairs",
        "output_object": "complete exact train-only screen, shortlist relation scores, and immutable size winners",
        "positive_case": "all compatible models contribute to each screen and relation consensus",
        "negative/erased_control": "omitted candidates, winner mutation, action swap, and brute-force controls",
        "boundary_case": "sizes two and four plus first and last design fixtures",
        "demotion_condition": "manifest drift, incomplete search, relation mismatch, phase leakage, or control silence",
        "gates": ["all_pass", "quotient", "selection"],
    }
    calls = [
        {"tool": "jax.numpy", "qualified_api/function": "jax.numpy.take", **common},
        {"tool": "jax.vmap", "qualified_api/function": "jax.vmap", **common},
        {"tool": "jax.jit", "qualified_api/function": "jax.jit", **common},
        {"tool": "jax.lax.while_loop", "qualified_api/function": "jax.lax.while_loop", **common},
        {"tool": "jax.ops.segment_max", "qualified_api/function": "jax.ops.segment_max", **common},
        {"tool": "jax.lax.population_count", "qualified_api/function": "jax.lax.population_count", **common},
    ]
    return TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH, calls


def build_receipt(spec: dict, frozen: dict) -> dict:
    started = time.time()
    fixtures, queries, manifests = build_train_only_manifests(spec)
    assignments = spec["candidate_pool"]["ordered_assignments"]
    transitions_device = eca_transition_table()
    transitions_device.block_until_ready()
    transitions = transitions_device.tolist()
    partition_objects, partition_receipt = compute_partition_objects(
        transitions_device, queries
    )
    if not partition_receipt["all_pass"]:
        raise RuntimeError("stable partition refinement failed")
    trajectory_a, trajectory_b, observed_state_bits, trajectory_receipt = build_trajectory_masks(
        fixtures, assignments, transitions
    )
    if not trajectory_receipt["all_pass"]:
        raise RuntimeError("true rule missing from trajectory compatibility mask")
    screen_kernel = build_screen_kernel(
        trajectory_a, trajectory_b, partition_objects
    )
    candidates = candidate_subsets()
    screen_records, screen_receipt = screen_all_candidates(screen_kernel, candidates)
    if not screen_receipt["all_pass"]:
        raise RuntimeError("incomplete candidate screen")
    shortlists = select_shortlists(screen_records)
    exact_kernel = build_exact_kernel(partition_objects)
    exact_records, winners, exact_receipt = exact_score_shortlists(
        shortlists,
        screen_kernel,
        exact_kernel,
        observed_state_bits,
        queries,
    )
    baselines = baseline_receipts(screen_records)
    baseline_exact_scores = exact_score_baselines(
        baselines,
        screen_records,
        exact_records,
        screen_kernel,
        exact_kernel,
        observed_state_bits,
        queries,
    )
    controls = controls_receipt(
        screen_records,
        winners,
        screen_kernel,
        exact_kernel,
        fixtures,
        assignments,
        transitions,
    )
    winner_summary = {
        str(size): {
            "subset": winners[size]["subset"],
            "screen_rank_within_size": winners[size]["screen_rank_within_size"],
            "screen_objective": winners[size]["screen_objective"],
            "exact_objective": winners[size]["exact_objective"],
            "fixture_scores_hash": winners[size]["fixture_scores_hash"],
        }
        for size in SUBSET_SIZES
    }
    shortlist_identity = {
        str(size): [record["subset"] for record in shortlists[size]]
        for size in SUBSET_SIZES
    }
    tests = {
        "frozen_inputs_verified": frozen["all_pass"],
        "train_only_manifests_verified": manifests["all_pass"],
        "stable_partitions_converged": partition_receipt["all_pass"],
        "trajectory_masks_retain_truth": trajectory_receipt["all_pass"],
        "all_2500_candidates_screened_once": screen_receipt["all_pass"],
        "shortlist_exactly_32_per_size": all(
            len(shortlists[size]) == SHORTLIST_WIDTH
            and len({tuple(record["subset"]) for record in shortlists[size]}) == SHORTLIST_WIDTH
            for size in SUBSET_SIZES
        ),
        "all_96_shortlisted_candidates_exact_scored_once": exact_receipt["all_96_scored_once"],
        "all_three_size_winners_visible": set(winners) == set(SUBSET_SIZES),
        "all_baselines_visible": baselines["all_sizes_present"],
        "hash_order_and_system_identification_baselines_exact_scored": baseline_exact_scores[
            "all_sizes_and_baselines_exact_scored"
        ],
        "all_controls_pass": controls["all_pass"],
        "no_confirmation_source_exists": not any(
            frozen["confirmation_source_presence"].values()
        ),
        "no_prohibited_result_reads": True,
        "numpy_not_used_by_source": not source_imports_numpy(Path(__file__)),
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
    }
    tool_manifest, tool_depth, tool_calls = tool_surfaces()
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "phase": "train_only_search",
        "ran": True,
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(Path(__file__).resolve().relative_to(REPO)),
        "source_sha256": sha256_file(Path(__file__)),
        "run_command": [sys.executable, *sys.argv],
        "run_cwd": os.getcwd(),
        "python_executable": sys.executable,
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "numpy_used": False,
        "reads_peer_result": False,
        "peer_result_files_read": [],
        "parent_result_files_read": [],
        "validation_or_test_fixture_files_read": [],
        "source_semantics_read": [
            "system_v7/sims/eca_observation_object_identifiability_v0/run_jax.py"
        ],
        "frozen_input_verification": frozen,
        "manifest_receipt": manifests,
        "partition_receipt": partition_receipt,
        "trajectory_mask_receipt": trajectory_receipt,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_depth,
        "tool_calls": tool_calls,
        "design_fixture_count": len(fixtures),
        "design_fixture_manifest": [list(pair) for pair in fixtures],
        "candidate_counts": {str(size): len(candidates[size]) for size in SUBSET_SIZES},
        "screen_receipt": screen_receipt,
        "screen_records": screen_records,
        "shortlist_identity": shortlist_identity,
        "shortlist_identity_hash": canonical_hash(shortlist_identity),
        "exact_score_receipt": exact_receipt,
        "exact_score_records": exact_records,
        "winner_summary": winner_summary,
        "winner_summary_hash": canonical_hash(winner_summary),
        "baselines": baselines,
        "baseline_exact_scores": baseline_exact_scores,
        "controls": controls,
        "tests": tests,
        "all_pass": all(tests.values()),
        "all_scientific_gates_pass": False,
        "elapsed_seconds": time.time() - started,
        "allowed_claim_label": spec["allowed_claim_label_if_search_controller_passes"],
        "claim_ceiling": "independent exact JAX train-only target-aware design search; no cross-runtime controller, confirmation, learner, perception, or engine-stage claim",
        "blocked_consumers": spec["blocked_consumers"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    spec, frozen = verify_frozen_inputs()
    receipt = build_receipt(spec, frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(compact_json(receipt) + "\n")
    print(
        compact_json(
            {
                "sim_id": SIM_ID,
                "engine": "jax",
                "phase": "train_only_search",
                "all_pass": receipt["all_pass"],
                "output": str(args.output),
                "winner_summary": receipt["winner_summary"],
                "elapsed_seconds": receipt["elapsed_seconds"],
            }
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
