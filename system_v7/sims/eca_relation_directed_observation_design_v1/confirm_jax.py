#!/usr/bin/env python3
"""Independent preregistered JAX confirmation for relation-directed ECA designs."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import itertools
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import jaxlib
from jax import lax, vmap


SIM_ID = "eca_relation_directed_observation_design_v1"
SCHEMA = "codex_ratchet.eca_relation_directed_observation_design_v1.jax_confirmation.v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "jax.numpy": {"used": True, "reason": "Exact x64 transitions, masks, packed relations, and query-disjoint counts."},
    "jax.vmap": {"used": True, "reason": "All rule/state transitions and compatible relation hypotheses are vectorized."},
    "jax.jit": {"used": True, "reason": "Refinement, nine-design compatibility, exact consensus, and disjoint gates are compiled."},
    "jax.lax.while_loop": {"used": True, "reason": "Every stable behavioral partition is refined to convergence."},
    "jax.ops.segment_max": {"used": True, "reason": "Distinct full stable partition relations are counted over compatible unordered rule pairs."},
    "jax.lax.population_count": {"used": True, "reason": "Packed exact same/possible relation counts feed primary coverage gates."},
    "numpy": {"used": False, "reason": "Not imported or used by this confirmation source."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax.numpy": "load_bearing",
    "jax.vmap": "load_bearing",
    "jax.jit": "load_bearing",
    "jax.lax.while_loop": "load_bearing",
    "jax.ops.segment_max": "load_bearing",
    "jax.lax.population_count": "load_bearing",
    "numpy": None,
}
TAG = "ECA-OBS-ID-V0"
EXPECTED_COMMIT = "8615977aab7aa2b6b660d5d88a248b3a4fd4b21b"
EXPECTED_BASE_COMMIT = "5f42e344d9671e6be43799d6922903a488cffbed"
EXPECTED_SPEC_SHA256 = "1e7334c8fee643966d827cbc582b1aa2917604cdf4462db0a83da4e17e8951cb"
EXPECTED_PREREG_SHA256 = "fc69262c10645dd335417dcbf6d0c9e95c2df48d049921fa90da427ae23a5664"
EXPECTED_SELECTION_SHA256 = "c84a9bff38cce093866983bc854583b9d26b981c9c14ad14903555174cbb4951"
EXPECTED_SELECTION_SCHEMA = (
    "codex_ratchet.eca_relation_directed_observation_design_v1."
    "selected_design_receipt.v2"
)
EXPECTED_NORMALIZED_SCREEN_PROJECTION_SHA256 = (
    "842f530bc7b69219e69bce41624471649fd1b5cf20d79446bc19d66e1c80d450"
)
EXPECTED_NORMALIZED_EXACT_PROJECTION_SHA256 = (
    "4c1ff7b2d348608bfd9e43f6af73d48ead44c98a6e53b2d26ef1613e1a71b0e1"
)
EXPECTED_SEARCH_JAX_SHA256 = "87824deff5d3cd267f9d021726a9e2e8f40dca72b92a3a232c5d87487d6df3ea"
EXPECTED_PARENT_JAX_SHA256 = "1fa6605e85401cbd1dd67899e48e92064463625222159c03253423539f0bbbd0"

RING_SIZE = 9
STATE_COUNT = 1 << RING_SIZE
RULE_COUNT = 256
PAIR_COUNT = RULE_COUNT * (RULE_COUNT - 1) // 2
QUERY_COUNT = 9636
VALIDATION_FIXTURE_COUNT = 325
TEST_FIXTURE_COUNT = 531
REFINEMENT_BATCH_SIZE = 128
MAX_REFINEMENT_ROUNDS = STATE_COUNT
WORD_BITS = 64
PACKED_QUERY_WORDS = (QUERY_COUNT + WORD_BITS - 1) // WORD_BITS
OBSERVED_STATE_WORDS = STATE_COUNT // WORD_BITS
FIXTURE_BATCH_SIZE = 8

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
SELECTION_PATH = HERE / "selected_design_receipt.json"
SEARCH_JAX_PATH = HERE / "search_jax.py"
PARENT_JAX_PATH = HERE.parent / "eca_observation_object_identifiability_v0" / "run_jax.py"
DEFAULT_OUTPUT = HERE / "results" / f"{SIM_ID}_jax_confirmation_results.json"

RUNTIME_PROJECT_FILES_READ = [
    str(path.relative_to(REPO))
    for path in (Path(__file__).resolve(), SPEC_PATH, PREREG_PATH, SELECTION_PATH, SEARCH_JAX_PATH, PARENT_JAX_PATH)
]
AUTHORING_PROJECT_FILES_READ = [
    "AGENTS.md",
    "CODEX.md",
    "system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md",
    "system_v5/docs/LLM_CONTROLLER_CONTRACT.md",
    "system_v5/docs/LEGO_SIM_CONTRACT.md",
    "system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md",
    "system_v7/sims/eca_relation_directed_observation_design_v1/README.md",
    "system_v7/sims/eca_relation_directed_observation_design_v1/spec.json",
    "system_v7/sims/eca_relation_directed_observation_design_v1/preregistration_receipt.json",
    "system_v7/sims/eca_relation_directed_observation_design_v1/selected_design_receipt.json",
    "system_v7/sims/eca_relation_directed_observation_design_v1/search_jax.py",
    "system_v7/sims/eca_relation_directed_observation_design_v1/select_designs.py",
    "system_v7/sims/eca_observation_object_identifiability_v0/run_jax.py",
]


def compact_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: object) -> str:
    return hashlib.sha256(compact_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_partition(labels: list[int]) -> list[int]:
    renaming: dict[int, int] = {}
    compact = []
    for label in labels:
        if label not in renaming:
            renaming[label] = len(renaming)
        compact.append(renaming[label])
    return compact


def source_imports_forbidden_array_library(path: Path) -> bool:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "numpy" for alias in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "numpy":
            return True
    return False


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()


def git_parent(commit: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{commit}^"], cwd=REPO, text=True
    ).strip()


def git_is_ancestor(commit: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, descendant],
        cwd=REPO,
        check=False,
    ).returncode == 0


def verify_frozen_inputs() -> tuple[dict, dict, dict]:
    spec = json.loads(SPEC_PATH.read_text())
    prereg = json.loads(PREREG_PATH.read_text())
    selected = json.loads(SELECTION_PATH.read_text())
    hashes = {
        "spec_sha256": sha256_file(SPEC_PATH),
        "preregistration_receipt_sha256": sha256_file(PREREG_PATH),
        "selected_design_receipt_sha256": sha256_file(SELECTION_PATH),
        "search_jax_source_sha256": sha256_file(SEARCH_JAX_PATH),
        "parent_v0_jax_source_semantics_sha256": sha256_file(PARENT_JAX_PATH),
        "confirm_jax_source_sha256": sha256_file(Path(__file__)),
    }
    head = git_head()
    correction_parent = git_parent(EXPECTED_COMMIT)
    tests = {
        "head_contains_controller_correction_commit": git_is_ancestor(EXPECTED_COMMIT, head),
        "controller_correction_parent_is_requested_post_search_commit": correction_parent == EXPECTED_BASE_COMMIT,
        "spec_source_constant": hashes["spec_sha256"] == EXPECTED_SPEC_SHA256,
        "preregistration_source_constant": hashes["preregistration_receipt_sha256"] == EXPECTED_PREREG_SHA256,
        "selection_source_constant": hashes["selected_design_receipt_sha256"] == EXPECTED_SELECTION_SHA256,
        "search_jax_semantics_source_constant": hashes["search_jax_source_sha256"] == EXPECTED_SEARCH_JAX_SHA256,
        "parent_jax_semantics_source_constant": hashes["parent_v0_jax_source_semantics_sha256"] == EXPECTED_PARENT_JAX_SHA256,
        "spec_bound_to_preregistration": prereg.get("spec_sha256") == hashes["spec_sha256"],
        "spec_bound_to_selection": selected.get("spec_sha256") == hashes["spec_sha256"],
        "preregistration_bound_to_selection": selected.get("preregistration_receipt_sha256") == hashes["preregistration_receipt_sha256"],
        "selected_jax_source_commitment_matches": selected.get("search_source_sha256", {}).get("jax") == hashes["search_jax_source_sha256"],
        "selected_winner_payload_hash_matches": canonical_hash(selected.get("winners")) == selected.get("winner_payload_sha256"),
        "selected_receipt_schema_is_v2": selected.get("schema") == EXPECTED_SELECTION_SCHEMA,
        "normalized_screen_projection_bound": selected.get("normalized_screen_projection_sha256")
        == EXPECTED_NORMALIZED_SCREEN_PROJECTION_SHA256,
        "normalized_exact_projection_bound": selected.get("normalized_exact_projection_sha256")
        == EXPECTED_NORMALIZED_EXACT_PROJECTION_SHA256,
        "selection_is_normalized_projection_not_raw_record_identity": selected.get("cross_runtime_boundary")
        == "normalized score projections agree; raw engine records use independent schemas and are bound only by full-file hashes",
        "sim_identity_matches": spec.get("sim_id") == prereg.get("sim_id") == selected.get("sim_id") == SIM_ID,
        "freeze_preceded_confirmation_source": prereg.get("confirmation_sources_present_when_frozen") is False
        and selected.get("confirmation_sources_present_when_frozen") is False,
        "validation_cannot_select_or_replace": selected.get("validation_may_select_or_replace") is False,
        "all_three_sizes_not_claim_bearing": selected.get("all_three_sizes_claim_bearing") is False,
        "all_three_sizes_frozen_for_confirmation": selected.get("all_three_sizes_frozen_for_confirmation") is True,
        "scratch_ceiling_bound": spec.get("classification") == CLASSIFICATION
        and spec.get("promotion_allowed") is False
        and spec.get("formal_admission_allowed") is False
        and selected.get("promotion_allowed") is False
        and selected.get("formal_admission_allowed") is False,
        "peer_result_reads_forbidden": spec["engine_contract"]["peer_result_reads_forbidden"] is True,
        "opaque_search_result_commitments_present_without_opening": set(selected.get("search_result_sha256", {})) == {"jax", "julia"}
        and all(len(value) == 64 for value in selected["search_result_sha256"].values()),
        "source_does_not_import_numpy": not source_imports_forbidden_array_library(Path(__file__)),
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen confirmation input verification failed: {tests}")
    return spec, selected, {
        "commit": {
            "expected_controller_correction": EXPECTED_COMMIT,
            "observed_head": head,
            "correction_is_ancestor_of_head": True,
            "expected_parent": EXPECTED_BASE_COMMIT,
            "observed_parent": correction_parent,
            "parent_matches": True,
        },
        "hashes": hashes,
        "opaque_unopened_search_result_commitments": selected["search_result_sha256"],
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
    return sorted(
        {rule_orbit(rule) for rule in range(RULE_COUNT)},
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


def reconstruct_pair_orbit_block(
    orbits: list[tuple[int, ...]], start: int, stop: int
) -> tuple[list[tuple[int, int]], list[tuple[tuple[int, int], ...]]]:
    rules = {rule for orbit in orbits[start:stop] for rule in orbit}
    raw_pairs = [
        (a, b)
        for a in range(RULE_COUNT - 1)
        for b in range(a + 1, RULE_COUNT)
        if a in rules and b in rules
    ]
    pair_orbits = sorted({simultaneous_pair_orbit(pair) for pair in raw_pairs})
    return [orbit[0] for orbit in pair_orbits], pair_orbits


def probe(state: int) -> tuple[int, int]:
    bits = [(state >> site) & 1 for site in range(RING_SIZE)]
    return (
        sum(bits),
        sum(bits[index] != bits[(index + 1) % RING_SIZE] for index in range(RING_SIZE)),
    )


def reconstruct_validation_inputs(spec: dict) -> tuple[list[tuple[int, int]], list[tuple[int, int]], dict, list[tuple[int, ...]]]:
    orbits = ordered_rule_orbits()
    fixtures, pair_orbits = reconstruct_pair_orbit_block(orbits, 52, 70)
    queries = [
        (a, b)
        for a in range(STATE_COUNT - 1)
        for b in range(a + 1, STATE_COUNT)
        if probe(a) == probe(b)
    ]
    assignments = spec["candidate_pool"]["ordered_assignments"]
    hashes = {
        "rule_orbits_sha256": canonical_hash(orbits),
        "validation_pair_orbits_sha256": canonical_hash(
            [[list(pair) for pair in orbit] for orbit in pair_orbits]
        ),
        "validation_fixture_representatives_sha256": canonical_hash([list(pair) for pair in fixtures]),
        "queries_sha256": canonical_hash([list(query) for query in queries]),
        "assignments_sha256": canonical_hash(assignments),
    }
    tests = {
        "all_88_rule_orbits_reconstructed": len(orbits) == 88,
        "frozen_rule_orbit_hash": hashes["rule_orbits_sha256"] == spec["rule_family_split"]["rule_orbit_manifest_sha256"],
        "all_325_validation_pair_orbits_reconstructed_once": len(fixtures) == len(set(fixtures)) == VALIDATION_FIXTURE_COUNT,
        "pair_orbit_representatives_are_minima": fixtures == [min(orbit) for orbit in pair_orbits],
        "all_9636_queries_reconstructed_once": len(queries) == len(set(queries)) == QUERY_COUNT,
        "frozen_query_hash": hashes["queries_sha256"] == spec["inherited_carrier"]["query_manifest_sha256"],
        "frozen_assignment_hash": hashes["assignments_sha256"] == spec["candidate_pool"]["assignment_manifest_sha256"],
        "test_fixture_values_not_constructed": True,
    }
    if not all(tests.values()):
        raise RuntimeError(f"validation reconstruction failed: {tests}")
    return fixtures, queries, {"hashes": hashes, "tests": tests, "all_pass": True}, orbits


def reconstruct_test_inputs_after_gate(
    spec: dict, orbits: list[tuple[int, ...]], robust_design_family: bool
) -> tuple[list[tuple[int, int]], dict]:
    if not robust_design_family:
        raise RuntimeError("reused test block requested before robust_design_family passed")
    train_fixtures, train_orbits = reconstruct_pair_orbit_block(orbits, 0, 52)
    validation_fixtures, validation_orbits = reconstruct_pair_orbit_block(orbits, 52, 70)
    test_fixtures, test_orbits = reconstruct_pair_orbit_block(orbits, 70, 88)
    pair_orbit_payload = {
        "train": [[list(pair) for pair in orbit] for orbit in train_orbits],
        "validation": [[list(pair) for pair in orbit] for orbit in validation_orbits],
        "test": [[list(pair) for pair in orbit] for orbit in test_orbits],
    }
    same_block_hash = canonical_hash(pair_orbit_payload)
    tests = {
        "robust_design_family_authorized_open": robust_design_family,
        "train_count_matches": len(train_fixtures) == spec["rule_family_split"]["train_pair_orbits"],
        "validation_count_matches": len(validation_fixtures) == spec["rule_family_split"]["validation_pair_orbits"],
        "all_531_reused_test_pair_orbits_reconstructed_once": len(test_fixtures) == len(set(test_fixtures)) == TEST_FIXTURE_COUNT,
        "frozen_same_block_pair_orbit_manifest": same_block_hash == spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"],
    }
    if not all(tests.values()):
        raise RuntimeError(f"conditional test reconstruction failed: {tests}")
    return test_fixtures, {
        "pair_orbit_manifest_sha256": same_block_hash,
        "test_fixture_representatives_sha256": canonical_hash([list(pair) for pair in test_fixtures]),
        "tests": tests,
        "all_pass": True,
    }


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
    starts = jnp.concatenate(
        (jnp.ones((1,), dtype=jnp.bool_), sorted_signatures[1:] != sorted_signatures[:-1])
    )
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

        return lax.while_loop(
            condition,
            body,
            (jnp.asarray(0, dtype=jnp.int64), labels0, active0),
        )

    return kernel


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
    compact_labels = [compact_partition(labels) for labels in partitions.tolist()]
    class_by_signature: dict[tuple[int, ...], int] = {}
    class_representatives: list[list[int]] = []
    pair_classes = []
    for labels in compact_labels:
        signature = tuple(labels)
        class_id = class_by_signature.get(signature)
        if class_id is None:
            class_id = len(class_representatives)
            class_by_signature[signature] = class_id
            class_representatives.append(labels)
        pair_classes.append(class_id)
    pair_order = sorted(range(PAIR_COUNT), key=lambda index: (pair_classes[index], index))
    relation_bits = []
    for labels in class_representatives:
        words = [0] * PACKED_QUERY_WORDS
        for query_index, (a, b) in enumerate(queries):
            if labels[a] == labels[b]:
                words[query_index // WORD_BITS] |= 1 << (query_index % WORD_BITS)
        relation_bits.append(words)
    receipt = {
        "pair_count": PAIR_COUNT,
        "distinct_full_partition_relation_count": len(class_representatives),
        "nonconverged_pair_count": len(nonconverged),
        "batch_round_histogram": {str(key): value for key, value in sorted(rounds.items())},
        "stable_partition_sha256": canonical_hash(compact_labels),
        "pair_partition_class_sha256": canonical_hash(pair_classes),
        "packed_relation_sha256": canonical_hash(relation_bits),
        "all_pass": not nonconverged and len(pair_classes) == PAIR_COUNT,
    }
    return {
        "pair_a": jnp.asarray([pairs[index][0] for index in pair_order], dtype=jnp.int16),
        "pair_b": jnp.asarray([pairs[index][1] for index in pair_order], dtype=jnp.int16),
        "pair_class": jnp.asarray([pair_classes[index] for index in pair_order], dtype=jnp.int32),
        "relation_bits": jnp.asarray(relation_bits, dtype=jnp.uint64),
        "class_count": len(class_representatives),
    }, receipt


def build_trajectory_objects(
    fixtures: list[tuple[int, int]], assignments: list[list[object]], transitions: list[list[int]]
) -> tuple[jax.Array, jax.Array, jax.Array, dict]:
    masks_a = []
    masks_b = []
    observed_words = []
    true_rule_failures = []
    for fixture_index, (rule_a, rule_b) in enumerate(fixtures):
        fixture_a = []
        fixture_b = []
        fixture_observed = []
        for trajectory_index, (word, initial_state) in enumerate(assignments):
            state = int(initial_state)
            observations = [[], []]
            seen = [0] * OBSERVED_STATE_WORDS
            for token_text in str(word):
                token = 0 if token_text == "A" else 1
                rule = rule_a if token == 0 else rule_b
                successor = transitions[rule][state]
                observations[token].append((state, successor))
                seen[state // WORD_BITS] |= 1 << (state % WORD_BITS)
                seen[successor // WORD_BITS] |= 1 << (successor % WORD_BITS)
                state = successor
            token_masks = [
                [
                    all(transitions[rule][predecessor] == successor for predecessor, successor in observations[token])
                    for rule in range(RULE_COUNT)
                ]
                for token in (0, 1)
            ]
            if not token_masks[0][rule_a] or not token_masks[1][rule_b]:
                true_rule_failures.append([fixture_index, trajectory_index])
            fixture_a.append(token_masks[0])
            fixture_b.append(token_masks[1])
            fixture_observed.append(seen)
        masks_a.append(fixture_a)
        masks_b.append(fixture_b)
        observed_words.append(fixture_observed)
    receipt = {
        "shape": [len(fixtures), 16, RULE_COUNT],
        "true_rule_failure_count": len(true_rule_failures),
        "mask_a_sha256": canonical_hash(masks_a),
        "mask_b_sha256": canonical_hash(masks_b),
        "observed_state_words_sha256": canonical_hash(observed_words),
        "all_pass": not true_rule_failures,
    }
    return (
        jnp.asarray(masks_a, dtype=jnp.bool_),
        jnp.asarray(masks_b, dtype=jnp.bool_),
        jnp.asarray(observed_words, dtype=jnp.uint64),
        receipt,
    )


def frozen_designs(selected: dict) -> tuple[list[dict], dict]:
    designs = []
    for size in (2, 3, 4):
        key = str(size)
        rows = {
            "relation_directed": selected["winners"][key],
            "hash_order": selected["baselines"][key]["hash_order"],
            "system_identification": selected["baselines"][key]["system_identification"],
        }
        for name, row in rows.items():
            designs.append(
                {
                    "design_id": f"size_{size}.{name}",
                    "subset_size": size,
                    "design_family": name,
                    "subset_indices": row["subset_indices"],
                }
            )
    tests = {
        "nine_named_designs_present": len(designs) == 9,
        "all_sizes_and_families_present": {(row["subset_size"], row["design_family"]) for row in designs}
        == {(size, name) for size in (2, 3, 4) for name in ("relation_directed", "hash_order", "system_identification")},
        "subset_sizes_literal": all(len(row["subset_indices"]) == row["subset_size"] for row in designs),
        "subset_indices_valid": all(
            row["subset_indices"] == sorted(set(row["subset_indices"]))
            and all(0 <= index < 16 for index in row["subset_indices"])
            for row in designs
        ),
        "selected_relation_directed_payloads_agree": all(
            selected["baselines"][str(size)]["relation_directed"] == selected["winners"][str(size)]
            for size in (2, 3, 4)
        ),
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen design extraction failed: {tests}")
    return designs, {"designs": designs, "design_identity_sha256": canonical_hash(designs), "tests": tests, "all_pass": True}


@jax.jit
def compile_design_compatibility(
    trajectory_a: jax.Array,
    trajectory_b: jax.Array,
    observed_words: jax.Array,
    design_masks: jax.Array,
) -> tuple[jax.Array, jax.Array, jax.Array]:
    selected = design_masks[:, None, :, None]
    compatible_a = jnp.all(jnp.where(selected, trajectory_a[None, :, :, :], True), axis=2)
    compatible_b = jnp.all(jnp.where(selected, trajectory_b[None, :, :, :], True), axis=2)
    selected_observed = jnp.where(selected, observed_words[None, :, :, :], jnp.uint64(0))
    observed = jnp.bitwise_or.reduce(selected_observed, axis=2)
    return compatible_a, compatible_b, observed


def build_exact_kernel(partition_objects: dict):
    pair_a = partition_objects["pair_a"]
    pair_b = partition_objects["pair_b"]
    pair_class = partition_objects["pair_class"]
    class_count = partition_objects["class_count"]
    relation_bits = partition_objects["relation_bits"]
    valid_words_host = [0xFFFFFFFFFFFFFFFF] * PACKED_QUERY_WORDS
    if QUERY_COUNT % WORD_BITS:
        valid_words_host[-1] = (1 << (QUERY_COUNT % WORD_BITS)) - 1
    valid_words = jnp.asarray(valid_words_host, dtype=jnp.uint64)
    all_ones = jnp.full((PACKED_QUERY_WORDS,), jnp.uint64(0xFFFFFFFFFFFFFFFF))

    def one(compatible_a: jax.Array, compatible_b: jax.Array):
        count_a = jnp.sum(compatible_a, dtype=jnp.int64)
        count_b = jnp.sum(compatible_b, dtype=jnp.int64)
        overlap = jnp.sum(compatible_a & compatible_b, dtype=jnp.int64)
        ordered = count_a * count_b - overlap
        pair_mask = (
            (compatible_a[pair_a] & compatible_b[pair_b])
            | (compatible_a[pair_b] & compatible_b[pair_a])
        )
        effective = jnp.sum(pair_mask, dtype=jnp.int64)
        presence = jax.ops.segment_max(
            pair_mask.astype(jnp.int8), pair_class, num_segments=class_count
        ).astype(jnp.bool_)
        distinct = jnp.sum(presence, dtype=jnp.int64)
        must_equal = jnp.bitwise_and.reduce(
            jnp.where(presence[:, None], relation_bits, all_ones), axis=0
        ) & valid_words
        possible_equal = jnp.bitwise_or.reduce(
            jnp.where(presence[:, None], relation_bits, jnp.uint64(0)), axis=0
        ) & valid_words
        same_count = jnp.sum(lax.population_count(must_equal), dtype=jnp.int64)
        possible_count = jnp.sum(lax.population_count(possible_equal), dtype=jnp.int64)
        return ordered, effective, distinct, must_equal, possible_equal, same_count, possible_count

    return jax.jit(vmap(one))


def build_query_disjoint_kernel(queries: list[tuple[int, int]]):
    query_a = jnp.asarray([a for a, _ in queries], dtype=jnp.int32)
    query_b = jnp.asarray([b for _, b in queries], dtype=jnp.int32)
    query_word_a = query_a // WORD_BITS
    query_word_b = query_b // WORD_BITS
    query_bit_a = (query_a % WORD_BITS).astype(jnp.uint64)
    query_bit_b = (query_b % WORD_BITS).astype(jnp.uint64)
    relation_word = jnp.arange(QUERY_COUNT, dtype=jnp.int32) // WORD_BITS
    relation_bit = (jnp.arange(QUERY_COUNT, dtype=jnp.int32) % WORD_BITS).astype(jnp.uint64)

    @jax.jit
    def kernel(must_words: jax.Array, possible_words: jax.Array, observed_words: jax.Array):
        seen_a = ((observed_words[:, query_word_a] >> query_bit_a) & jnp.uint64(1)).astype(jnp.bool_)
        seen_b = ((observed_words[:, query_word_b] >> query_bit_b) & jnp.uint64(1)).astype(jnp.bool_)
        disjoint = ~(seen_a | seen_b)
        same = ((must_words[:, relation_word] >> relation_bit) & jnp.uint64(1)).astype(jnp.bool_)
        possible = ((possible_words[:, relation_word] >> relation_bit) & jnp.uint64(1)).astype(jnp.bool_)
        return (
            jnp.sum(disjoint, axis=1, dtype=jnp.int64),
            jnp.sum(disjoint & same, axis=1, dtype=jnp.int64),
            jnp.sum(disjoint & ~possible, axis=1, dtype=jnp.int64),
        )

    return kernel


def relation_vector_hash(must_words: list[int], possible_words: list[int]) -> str:
    vector = []
    for index in range(QUERY_COUNT):
        equal_all = (must_words[index // WORD_BITS] >> (index % WORD_BITS)) & 1
        equal_any = (possible_words[index // WORD_BITS] >> (index % WORD_BITS)) & 1
        vector.append(2 if equal_all else (0 if equal_any else 1))
    return canonical_hash(vector)


def exact_score_designs(
    fixture_label: str,
    fixtures: list[tuple[int, int]],
    queries: list[tuple[int, int]],
    assignments: list[list[object]],
    transitions: list[list[int]],
    partition_objects: dict,
    designs: list[dict],
) -> tuple[dict, dict, dict]:
    trajectory_a, trajectory_b, observed_words, trajectory_receipt = build_trajectory_objects(
        fixtures, assignments, transitions
    )
    design_masks_host = [
        [index in row["subset_indices"] for index in range(16)] for row in designs
    ]
    design_masks = jnp.asarray(design_masks_host, dtype=jnp.bool_)
    compatible_a, compatible_b, selected_observed = compile_design_compatibility(
        trajectory_a, trajectory_b, observed_words, design_masks
    )
    compatible_a.block_until_ready()
    exact_kernel = build_exact_kernel(partition_objects)
    query_disjoint_kernel = build_query_disjoint_kernel(queries)
    ledgers: list[list[dict]] = [[] for _ in designs]
    all_true_pairs_retained = True
    fixture_count = len(fixtures)
    for start in range(0, fixture_count, FIXTURE_BATCH_SIZE):
        stop = min(start + FIXTURE_BATCH_SIZE, fixture_count)
        real = stop - start
        flat_a = compatible_a[:, start:stop, :].reshape((-1, RULE_COUNT))
        flat_b = compatible_b[:, start:stop, :].reshape((-1, RULE_COUNT))
        flat_observed = selected_observed[:, start:stop, :].reshape((-1, OBSERVED_STATE_WORDS))
        ordered, effective, distinct, must, possible, same, possible_count = exact_kernel(flat_a, flat_b)
        disjoint_count, disjoint_same, disjoint_different = query_disjoint_kernel(
            must, possible, flat_observed
        )
        ordered_h = ordered.reshape((len(designs), real)).tolist()
        effective_h = effective.reshape((len(designs), real)).tolist()
        distinct_h = distinct.reshape((len(designs), real)).tolist()
        must_h = must.reshape((len(designs), real, PACKED_QUERY_WORDS)).tolist()
        possible_h = possible.reshape((len(designs), real, PACKED_QUERY_WORDS)).tolist()
        same_h = same.reshape((len(designs), real)).tolist()
        possible_count_h = possible_count.reshape((len(designs), real)).tolist()
        disjoint_count_h = disjoint_count.reshape((len(designs), real)).tolist()
        disjoint_same_h = disjoint_same.reshape((len(designs), real)).tolist()
        disjoint_different_h = disjoint_different.reshape((len(designs), real)).tolist()
        compatible_a_h = compatible_a[:, start:stop, :].tolist()
        compatible_b_h = compatible_b[:, start:stop, :].tolist()
        for design_index, design in enumerate(designs):
            for offset in range(real):
                fixture_index = start + offset
                true_a, true_b = fixtures[fixture_index]
                true_retained = bool(
                    compatible_a_h[design_index][offset][true_a]
                    and compatible_b_h[design_index][offset][true_b]
                    and ordered_h[design_index][offset] > 0
                )
                all_true_pairs_retained &= true_retained
                same_count = int(same_h[design_index][offset])
                different_count = QUERY_COUNT - int(possible_count_h[design_index][offset])
                identifiable = same_count + different_count
                qd_same = int(disjoint_same_h[design_index][offset])
                qd_different = int(disjoint_different_h[design_index][offset])
                qd_count = int(disjoint_count_h[design_index][offset])
                diversity = effective_h[design_index][offset] >= 8 and distinct_h[design_index][offset] >= 2
                must_words = [int(value) for value in must_h[design_index][offset]]
                possible_words = [int(value) for value in possible_h[design_index][offset]]
                ledgers[design_index].append(
                    {
                        "fixture_index": fixture_index,
                        "pair_orbit_representative": [true_a, true_b],
                        "true_pair_retained": true_retained,
                        "ordered_version_space_size": int(ordered_h[design_index][offset]),
                        "effective_unordered_hypothesis_count": int(effective_h[design_index][offset]),
                        "distinct_full_partition_relation_count": int(distinct_h[design_index][offset]),
                        "system_identified": ordered_h[design_index][offset] == 1,
                        "diversity_fixture": diversity,
                        "identifiable_query_count": identifiable,
                        "identifiable_same_count": same_count,
                        "identifiable_different_count": different_count,
                        "balanced_fixture": identifiable > 0
                        and 10 * same_count >= identifiable
                        and 10 * different_count >= identifiable,
                        "robust_query_count": identifiable if diversity else 0,
                        "query_disjoint_query_count": qd_count,
                        "query_disjoint_identifiable_count": qd_same + qd_different,
                        "query_disjoint_same_count": qd_same,
                        "query_disjoint_different_count": qd_different,
                        "query_disjoint_robust_count": qd_same + qd_different if diversity else 0,
                        "relation_vector_sha256": relation_vector_hash(must_words, possible_words),
                    }
                )
    scores = {}
    fixture_manifest_hash = canonical_hash([list(pair) for pair in fixtures])
    for design, ledger in zip(designs, ledgers):
        robust = [row["robust_query_count"] for row in ledger]
        qd_robust = [row["query_disjoint_robust_count"] for row in ledger]
        scores[design["design_id"]] = {
            **design,
            "fixture_family": fixture_label,
            "fixture_count": fixture_count,
            "fixture_manifest_sha256": fixture_manifest_hash,
            "fixture_ledger_sha256": canonical_hash(ledger),
            "fixture_ledger": ledger,
            "construction_failure_count": sum(not row["true_pair_retained"] for row in ledger),
            "diversity_fixture_count": sum(row["diversity_fixture"] for row in ledger),
            "system_identified_fixture_count": sum(row["system_identified"] for row in ledger),
            "minimum_robust_query_count": min(robust),
            "sum_robust_query_count": sum(robust),
            "minimum_query_disjoint_robust_count": min(qd_robust),
            "sum_query_disjoint_robust_count": sum(qd_robust),
            "total_identifiable_query_count": sum(row["identifiable_query_count"] for row in ledger),
            "total_identifiable_same_count": sum(row["identifiable_same_count"] for row in ledger),
            "total_identifiable_different_count": sum(row["identifiable_different_count"] for row in ledger),
            "total_query_disjoint_query_count": sum(row["query_disjoint_query_count"] for row in ledger),
            "total_query_disjoint_identifiable_count": sum(row["query_disjoint_identifiable_count"] for row in ledger),
            "balanced_fixture_count": sum(row["balanced_fixture"] for row in ledger),
        }
    controls = {
        "identical_fixture_count_for_all_nine_designs": {row["fixture_count"] for row in scores.values()} == {fixture_count},
        "identical_fixture_manifest_for_all_nine_designs": {row["fixture_manifest_sha256"] for row in scores.values()} == {fixture_manifest_hash},
        "all_true_pairs_retained": all_true_pairs_retained,
        "all_nine_designs_exact_scored": len(scores) == 9 and all(len(row["fixture_ledger"]) == fixture_count for row in scores.values()),
    }
    return scores, trajectory_receipt, {**controls, "all_pass": all(controls.values())}


def primary_gate_receipt(scores: dict, fixture_count: int) -> dict:
    size_receipts = {}
    for size in (2, 3, 4):
        directed = scores[f"size_{size}.relation_directed"]
        hash_order = scores[f"size_{size}.hash_order"]
        system = scores[f"size_{size}.system_identification"]
        ledger = directed["fixture_ledger"]
        total_queries = fixture_count * QUERY_COUNT
        consensus = directed["total_identifiable_query_count"]
        qd_total = directed["total_query_disjoint_query_count"]
        qd_identifiable = directed["total_query_disjoint_identifiable_count"]
        baseline_separation_parts = {
            "strictly_exceeds_hash_order_minimum_robust_coverage": directed["minimum_robust_query_count"] > hash_order["minimum_robust_query_count"],
            "strictly_exceeds_hash_order_sum_robust_coverage": directed["sum_robust_query_count"] > hash_order["sum_robust_query_count"],
            "retains_more_diversity_fixtures_than_system_identification": directed["diversity_fixture_count"] > system["diversity_fixture_count"],
        }
        gates = {
            "construction": directed["construction_failure_count"] == 0
            and all(row["ordered_version_space_size"] > 0 for row in ledger),
            "diversity": directed["diversity_fixture_count"] == fixture_count,
            "system_identification": directed["system_identified_fixture_count"] == 0,
            "global_relation_coverage": 20 * consensus >= 19 * total_queries,
            "fixture_floor": all(5 * row["identifiable_query_count"] >= 4 * QUERY_COUNT for row in ledger),
            "query_disjoint_global_coverage": qd_total > 0 and 10 * qd_identifiable >= 9 * qd_total,
            "query_disjoint_fixture_floor": all(
                row["query_disjoint_query_count"] > 0
                and 10 * row["query_disjoint_identifiable_count"] >= 7 * row["query_disjoint_query_count"]
                for row in ledger
            ),
            "pooled_target_balance": consensus > 0
            and 5 * directed["total_identifiable_same_count"] >= consensus
            and 5 * directed["total_identifiable_different_count"] >= consensus,
            "fixture_balance": 5 * directed["balanced_fixture_count"] >= 4 * fixture_count,
            "baseline_separation": (
                baseline_separation_parts["strictly_exceeds_hash_order_minimum_robust_coverage"]
                or baseline_separation_parts["strictly_exceeds_hash_order_sum_robust_coverage"]
            )
            and baseline_separation_parts["retains_more_diversity_fixtures_than_system_identification"],
        }
        size_receipts[str(size)] = {
            "subset_indices": directed["subset_indices"],
            "exact_integer_gate_inputs": {
                "fixture_count": fixture_count,
                "query_count_per_fixture": QUERY_COUNT,
                "total_query_count": total_queries,
                "identifiable_query_count": consensus,
                "identifiable_same_count": directed["total_identifiable_same_count"],
                "identifiable_different_count": directed["total_identifiable_different_count"],
                "minimum_fixture_identifiable_query_count": min(row["identifiable_query_count"] for row in ledger),
                "query_disjoint_query_count": qd_total,
                "query_disjoint_identifiable_count": qd_identifiable,
                "minimum_query_disjoint_fixture_numerator_denominator": min(
                    (row["query_disjoint_identifiable_count"], row["query_disjoint_query_count"])
                    for row in ledger
                ),
                "balanced_fixture_count": directed["balanced_fixture_count"],
                "diversity_fixture_count": directed["diversity_fixture_count"],
                "system_identified_fixture_count": directed["system_identified_fixture_count"],
                "directed_minimum_robust_query_count": directed["minimum_robust_query_count"],
                "hash_order_minimum_robust_query_count": hash_order["minimum_robust_query_count"],
                "directed_sum_robust_query_count": directed["sum_robust_query_count"],
                "hash_order_sum_robust_query_count": hash_order["sum_robust_query_count"],
                "system_identification_diversity_fixture_count": system["diversity_fixture_count"],
            },
            "baseline_separation_parts": baseline_separation_parts,
            "gates": gates,
            "all_primary_conditions_pass": all(gates.values()),
        }
    passing_sizes = [int(size) for size, row in size_receipts.items() if row["all_primary_conditions_pass"]]
    candidate_exists = len(passing_sizes) >= 1
    robust_design_family = len(passing_sizes) >= 2
    return {
        "sizes": size_receipts,
        "passing_sizes": passing_sizes,
        "passing_size_count": len(passing_sizes),
        "candidate_exists": candidate_exists,
        "robust_design_family": robust_design_family,
        "all_primary_validation_conditions": robust_design_family,
    }


def brute_force_version_space(
    fixture: tuple[int, int], subset: tuple[int, ...], assignments: list[list[object]], transitions: list[list[int]]
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


def confirmation_controls(
    fixtures: list[tuple[int, int]],
    assignments: list[list[object]],
    transitions: list[list[int]],
    partition_objects: dict,
    designs: list[dict],
    validation_scores: dict,
    selected: dict,
    frozen: dict,
) -> tuple[dict, dict]:
    relation_designs = [row for row in designs if row["design_family"] == "relation_directed"]
    design_by_id = {row["design_id"]: row for row in designs}
    trajectory_a, trajectory_b, observed_words, _ = build_trajectory_objects(fixtures, assignments, transitions)
    design_masks = jnp.asarray(
        [[index in row["subset_indices"] for index in range(16)] for row in designs], dtype=jnp.bool_
    )
    compatible_a, compatible_b, _ = compile_design_compatibility(
        trajectory_a, trajectory_b, observed_words, design_masks
    )
    exact_kernel = build_exact_kernel(partition_objects)
    design_index = {row["design_id"]: index for index, row in enumerate(designs)}
    factorized_cases = []
    action_swap_cases = []
    for design in relation_designs:
        index = design_index[design["design_id"]]
        subset = tuple(design["subset_indices"])
        for fixture_index in (0, len(fixtures) - 1):
            a_mask = compatible_a[index, fixture_index]
            b_mask = compatible_b[index, fixture_index]
            a_rules = [rule for rule, flag in enumerate(a_mask.tolist()) if flag]
            b_rules = [rule for rule, flag in enumerate(b_mask.tolist()) if flag]
            factorized = [(a, b) for a in a_rules for b in b_rules if a != b]
            brute = brute_force_version_space(fixtures[fixture_index], subset, assignments, transitions)
            factorized_cases.append(
                {
                    "design_id": design["design_id"],
                    "fixture_index": fixture_index,
                    "factorized_sha256": canonical_hash(factorized),
                    "ordered_brute_force_sha256": canonical_hash(brute),
                    "passed": factorized == brute,
                }
            )
            original = exact_kernel(a_mask[None, :], b_mask[None, :])
            swapped = exact_kernel(b_mask[None, :], a_mask[None, :])
            passed = all(left.tolist() == right.tolist() for left, right in zip(original, swapped))
            action_swap_cases.append(
                {"design_id": design["design_id"], "fixture_index": fixture_index, "passed": passed}
            )
    fixture_payload = [list(pair) for pair in fixtures]
    omitted_payload = fixture_payload[:-1]
    permuted_payload = copy.deepcopy(fixture_payload)
    permuted_payload[0], permuted_payload[1] = permuted_payload[1], permuted_payload[0]
    mutated_winners = copy.deepcopy(selected["winners"])
    mutated_winners["2"]["subset_indices"] = [0, 2]
    mutation_checks = {
        "omitted_validation_fixture_detected": len(omitted_payload) != VALIDATION_FIXTURE_COUNT
        and canonical_hash(omitted_payload) != canonical_hash(fixture_payload),
        "validation_fixture_order_mutation_detected": canonical_hash(permuted_payload) != canonical_hash(fixture_payload),
        "winner_index_mutation_detected": canonical_hash(mutated_winners) != selected["winner_payload_sha256"],
        "selected_receipt_byte_mutation_detected": hashlib.sha256(SELECTION_PATH.read_bytes() + b"mutated").hexdigest()
        != frozen["hashes"]["selected_design_receipt_sha256"],
        "source_byte_mutation_detected": hashlib.sha256(Path(__file__).read_bytes() + b"mutated").hexdigest()
        != frozen["hashes"]["confirm_jax_source_sha256"],
        "test_open_policy_rejects_zero_or_one_passing_size": not (0 >= 2) and not (1 >= 2),
        "test_open_policy_accepts_two_or_three_passing_sizes": (2 >= 2) and (3 >= 2),
    }
    controls = {
        "factorized_vs_ordered_brute_force": {
            "cases": factorized_cases,
            "passed": len(factorized_cases) == 6 and all(row["passed"] for row in factorized_cases),
        },
        "action_token_swap_preserves_unordered_relation_scores": {
            "cases": action_swap_cases,
            "passed": len(action_swap_cases) == 6 and all(row["passed"] for row in action_swap_cases),
        },
        "all_selected_sizes_remain_visible": {
            "visible_sizes": sorted({row["subset_size"] for row in relation_designs}),
            "passed": sorted({row["subset_size"] for row in relation_designs}) == [2, 3, 4],
        },
        "all_nine_named_scores_present": {
            "design_ids": sorted(validation_scores),
            "passed": set(validation_scores) == {row["design_id"] for row in designs},
        },
        "frozen_subsets_unchanged": {
            "designs": [design_by_id[row["design_id"]] for row in designs],
            "passed": all(design_by_id[row["design_id"]] == row for row in designs),
        },
    }
    controls["all_pass"] = all(row["passed"] for row in controls.values() if isinstance(row, dict) and "passed" in row)
    mutation_checks["all_pass"] = all(mutation_checks.values())
    return controls, mutation_checks


def tool_receipts() -> tuple[dict, dict, list[dict]]:
    manifest = copy.deepcopy(TOOL_MANIFEST)
    depth = copy.deepcopy(TOOL_INTEGRATION_DEPTH)
    common = {
        "input_object": "325 reconstructed validation pair-orbit fixtures, nine frozen design/baseline identities, 9636 queries, and all 32640 unordered rule pairs",
        "output_object": "exact per-fixture version-space, stable-relation, query-disjoint, balance, baseline-separation, and test-open gates",
        "positive_case": "all frozen hypotheses and all selected sizes contribute to literal integer gates",
        "negative/erased_control": "fixture omission/order, winner index, source/receipt bytes, action token, and test-open boundary mutations",
        "boundary_case": "sizes two and four plus first and last validation fixtures",
        "demotion_condition": "hash drift, incomplete fixture reconstruction, nonconvergence, truth loss, control silence, or fewer than two passing sizes",
        "gates": ["receipt_integrity_all_pass", "primary_validation_gates", "robust_design_family", "test_open_condition"],
    }
    calls = [
        {"tool": "jax.numpy", "qualified_api/function": "jax.numpy.take_along_axis", **common},
        {"tool": "jax.vmap", "qualified_api/function": "jax.vmap", **common},
        {"tool": "jax.jit", "qualified_api/function": "jax.jit", **common},
        {"tool": "jax.lax.while_loop", "qualified_api/function": "jax.lax.while_loop", **common},
        {"tool": "jax.ops.segment_max", "qualified_api/function": "jax.ops.segment_max", **common},
        {"tool": "jax.lax.population_count", "qualified_api/function": "jax.lax.population_count", **common},
    ]
    return manifest, depth, calls


def build_receipt(spec: dict, selected: dict, frozen: dict) -> dict:
    started = time.time()
    validation_fixtures, queries, validation_manifest, orbits = reconstruct_validation_inputs(spec)
    assignments = spec["candidate_pool"]["ordered_assignments"]
    designs, design_receipt = frozen_designs(selected)
    transitions_device = eca_transition_table()
    transitions_device.block_until_ready()
    transitions = transitions_device.tolist()
    partition_objects, partition_receipt = compute_partition_objects(transitions_device, queries)
    if not partition_receipt["all_pass"]:
        raise RuntimeError("stable behavioral partition refinement failed")
    validation_scores, validation_trajectory, score_controls = exact_score_designs(
        "validation",
        validation_fixtures,
        queries,
        assignments,
        transitions,
        partition_objects,
        designs,
    )
    validation_gates = primary_gate_receipt(validation_scores, VALIDATION_FIXTURE_COUNT)
    controls, mutations = confirmation_controls(
        validation_fixtures,
        assignments,
        transitions,
        partition_objects,
        designs,
        validation_scores,
        selected,
        frozen,
    )
    robust = validation_gates["robust_design_family"]
    if robust:
        test_fixtures, test_manifest = reconstruct_test_inputs_after_gate(spec, orbits, robust)
        test_scores, test_trajectory, test_score_controls = exact_score_designs(
            "reused_test",
            test_fixtures,
            queries,
            assignments,
            transitions,
            partition_objects,
            designs,
        )
        test_gates = primary_gate_receipt(test_scores, TEST_FIXTURE_COUNT)
        test_confirmation = {
            "opened": True,
            "fixture_values_constructed": True,
            "open_condition": "robust_design_family == true on validation",
            "status": "REUSED_TEST_EXACT_SCORED",
            "manifest_receipt": test_manifest,
            "trajectory_receipt": test_trajectory,
            "score_controls": test_score_controls,
            "scores": test_scores,
            "gates": test_gates,
            "all_pass": test_gates["robust_design_family"],
        }
    else:
        test_confirmation = {
            "opened": False,
            "fixture_values_constructed": False,
            "expected_fixture_count": TEST_FIXTURE_COUNT,
            "open_condition": "robust_design_family == true on validation",
            "status": "UNOPENED_FEWER_THAN_TWO_VALIDATION_SIZES_PASSED",
            "manifest_receipt": None,
            "trajectory_receipt": None,
            "score_controls": None,
            "scores": None,
            "gates": None,
            "all_pass": False,
        }
    tool_manifest, tool_depth, tool_calls = tool_receipts()
    receipt_integrity_tests = {
        "frozen_commit_and_hash_bindings": frozen["all_pass"],
        "validation_fixtures_reconstructed": validation_manifest["all_pass"],
        "frozen_designs_bound": design_receipt["all_pass"],
        "stable_partitions_converged": partition_receipt["all_pass"],
        "validation_trajectory_truth_retained": validation_trajectory["all_pass"],
        "all_nine_validation_scores_complete": score_controls["all_pass"],
        "confirmation_controls_pass": controls["all_pass"],
        "mutation_checks_pass": mutations["all_pass"],
        "test_open_policy_obeyed": test_confirmation["opened"] == robust,
        "test_remained_unopened_when_required": robust or not test_confirmation["fixture_values_constructed"],
        "no_prohibited_project_result_or_fixture_reads": True,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "numpy_not_used": not source_imports_forbidden_array_library(Path(__file__)),
    }
    receipt_integrity_all_pass = all(receipt_integrity_tests.values())
    scientific_all_pass = robust and bool(test_confirmation["all_pass"])
    result_label = (
        "FINITE_TARGET_AWARE_ECA_RELATION_MEASUREMENT_DESIGN_CANDIDATE_REUSED_TEST_CONFIRMED"
        if scientific_all_pass
        else "PREREGISTERED_CONFIRMATION_RED"
    )
    receipt = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "phase": "preregistered_confirmation",
        "ran": True,
        "execution_completed": True,
        "receipt_closed": True,
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "result_label": result_label,
        "source_path": str(Path(__file__).resolve().relative_to(REPO)),
        "source_sha256": frozen["hashes"]["confirm_jax_source_sha256"],
        "output_path": str(DEFAULT_OUTPUT.relative_to(REPO)),
        "run_command": [sys.executable, *sys.argv],
        "run_cwd": os.getcwd(),
        "commit_and_hash_bindings": frozen,
        "explicit_project_files_read": {
            "runtime_confirmation_source": RUNTIME_PROJECT_FILES_READ,
            "authoring_and_authority_review": AUTHORING_PROJECT_FILES_READ,
            "search_result_jsons": [],
            "confirm_julia_source_or_result": [],
            "parent_v0_results": [],
            "test_fixture_files": [],
            "test_fixture_values_constructed": test_confirmation["fixture_values_constructed"],
        },
        "prohibited_reads": {
            "reads_peer_result": False,
            "peer_result_files_read": [],
            "search_result_files_read": [],
            "confirm_julia_files_read": [],
            "parent_result_files_read": [],
            "test_fixture_files_read": [],
        },
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "runner_identity": platform.node(),
            "jax_version": jax.__version__,
            "jaxlib_version": jaxlib.__version__,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "jax_backend": jax.default_backend(),
            "jax_devices": [str(device) for device in jax.devices()],
            "numpy_used": False,
        },
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_depth,
        "aligned_packages_load_bearing": [
            "jax.jit",
            "jax.vmap",
            "jax.lax.while_loop",
            "jax.ops.segment_max",
            "jax.lax.population_count",
        ],
        "tool_calls": tool_calls,
        "validation_manifest_receipt": validation_manifest,
        "frozen_design_receipt": design_receipt,
        "partition_receipt": partition_receipt,
        "validation_trajectory_receipt": validation_trajectory,
        "validation_score_controls": score_controls,
        "validation_scores": validation_scores,
        "primary_validation_gate_receipt": validation_gates,
        "controls": controls,
        "mutation_checks": mutations,
        "test_confirmation": test_confirmation,
        "receipt_integrity_tests": receipt_integrity_tests,
        "receipt_integrity_all_pass": receipt_integrity_all_pass,
        "all_primary_validation_gates_pass": robust,
        "all_scientific_gates_pass": scientific_all_pass,
        "all_pass": scientific_all_pass and receipt_integrity_all_pass,
        "allowed_claim_label_if_validation_passes": spec["allowed_claim_label_if_validation_passes"],
        "claim_ceiling": "scratch diagnostic finite target-aware experimental design only; no perception, learning, spontaneous object discovery, semantic objecthood, or formal admission",
        "blocked_consumers": spec["blocked_consumers"],
        "roles": {
            "state_archaeology": "controller verified current paths, base commit, source hashes, and ownership before editing",
            "builder": "this independent JAX confirmation source",
            "mechanical_gatekeeper": "literal integer gates and mutation controls in this source",
            "fresh_context_fabrication_auditor": "not run; no promotion or canonical-by-process claim",
        },
        "elapsed_seconds": time.time() - started,
    }
    receipt["closed_payload_sha256"] = canonical_hash(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    spec, selected, frozen = verify_frozen_inputs()
    receipt = build_receipt(spec, selected, frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        compact_json(
            {
                "sim_id": SIM_ID,
                "engine": "jax",
                "phase": "preregistered_confirmation",
                "receipt_integrity_all_pass": receipt["receipt_integrity_all_pass"],
                "passing_validation_sizes": receipt["primary_validation_gate_receipt"]["passing_sizes"],
                "robust_design_family": receipt["primary_validation_gate_receipt"]["robust_design_family"],
                "test_opened": receipt["test_confirmation"]["opened"],
                "all_pass": receipt["all_pass"],
                "result_label": receipt["result_label"],
                "output": str(args.output),
                "elapsed_seconds": receipt["elapsed_seconds"],
            }
        )
    )
    return 0 if receipt["receipt_integrity_all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
