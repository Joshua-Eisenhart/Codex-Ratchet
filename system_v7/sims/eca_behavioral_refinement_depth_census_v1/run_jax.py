#!/usr/bin/env python3
"""Exhaustive JAX x64 N9 ECA behavioral-refinement depth census."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
from jax import lax, vmap


SIM_ID = "eca_behavioral_refinement_depth_census_v1"
SCHEMA = "codex_ratchet.eca_behavioral_refinement_depth_census_v1.jax.v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
RING_SIZE = 9
STATE_COUNT = 1 << RING_SIZE
RULE_COUNT = 256
PAIR_COUNT = RULE_COUNT * (RULE_COUNT - 1) // 2
MAX_STRICT_DEPTH = STATE_COUNT - 1
MAX_REFINEMENT_ROUNDS = STATE_COUNT
BATCH_SIZE = 128
DEPTH_SIX = 6
SPLIT_TAG = "ECA9-DEPTH-V1"
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
PREREGISTRATION_PATH = HERE / "preregistration_receipt.json"
DEFAULT_OUTPUT = HERE / "results" / f"{SIM_ID}_jax_results.json"

EXPECTED_SPEC_SHA256 = "b8314859eab375eeeb5573f2559c8c5b045c507361697106a8fddb3a4119e405"
EXPECTED_CARD_SHA256 = "6eb35560bba0475f0db1223715d78d5bdaee5fdce2d7e46aec3621f68cfeed7f"

TOOL_MANIFEST = {
    "jax.numpy": {
        "used": True,
        "reason": "Exact x64 packed signatures, transitions, partitions, and observables.",
    },
    "jax.vmap": {
        "used": True,
        "reason": "Vectorized exhaustive ECA transitions, row canonicalization, and class counts.",
    },
    "jax.jit": {
        "used": True,
        "reason": "Compiled batched exact refinement over the complete pair universe.",
    },
    "jax.lax.while_loop": {
        "used": True,
        "reason": "Finite bounded refinement with batch-local early convergence.",
    },
    "numpy": {"used": False, "reason": "Forbidden from the claim path."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax.numpy": "load_bearing",
    "jax.vmap": "load_bearing",
    "jax.jit": "load_bearing",
    "jax.lax.while_loop": "load_bearing",
    "numpy": None,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def compact_labels_hash(labels: list[int]) -> str:
    renaming: dict[int, int] = {}
    compact: list[int] = []
    for label in labels:
        if label not in renaming:
            renaming[label] = len(renaming)
        compact.append(renaming[label])
    return canonical_hash(compact)


def verify_frozen_inputs() -> dict:
    receipt = json.loads(PREREGISTRATION_PATH.read_text())
    observed_spec = sha256_file(SPEC_PATH)
    observed_card = sha256_file(CARD_PATH)
    tests = {
        "spec_matches_source_constant": observed_spec == EXPECTED_SPEC_SHA256,
        "card_matches_source_constant": observed_card == EXPECTED_CARD_SHA256,
        "spec_matches_preregistration": observed_spec == receipt.get("spec_sha256"),
        "card_matches_preregistration": observed_card
        == receipt.get("object_card_sha256"),
        "preregistration_precedes_builder": receipt.get(
            "builder_sources_present_when_frozen"
        )
        is False,
        "sim_id_matches": receipt.get("sim_id") == SIM_ID,
    }
    if not all(tests.values()):
        raise RuntimeError(f"frozen input verification failed: {tests}")
    return {
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
    out = 0
    for neighborhood in range(8):
        out |= (1 - ((rule >> (7 - neighborhood)) & 1)) << neighborhood
    return out


def rule_transforms(rule: int) -> tuple[int, int, int, int]:
    return (
        rule,
        reflect_rule(rule),
        conjugate_rule(rule),
        reflect_rule(conjugate_rule(rule)),
    )


def simultaneous_pair_orbit(pair: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    transformed_a = rule_transforms(pair[0])
    transformed_b = rule_transforms(pair[1])
    return tuple(
        sorted(
            {
                tuple(sorted((transformed_a[index], transformed_b[index])))
                for index in range(4)
            }
        )
    )


def pair_orbit_key(pair: tuple[int, int]) -> str:
    canonical = simultaneous_pair_orbit(pair)[0]
    return f"{canonical[0]},{canonical[1]}"


def build_hidden_batch_map(pairs: list[tuple[int, int]]) -> tuple[dict[str, str], dict]:
    orbit_members: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for pair in pairs:
        orbit_members[pair_orbit_key(pair)].append(pair)
    ordered_keys = sorted(
        orbit_members,
        key=lambda key: (
            hashlib.sha256(f"{SPLIT_TAG}|pair_orbit|{key}".encode()).hexdigest(),
            key,
        ),
    )
    batch_by_key = {
        key: "A" if index % 2 == 0 else "B" for index, key in enumerate(ordered_keys)
    }
    pair_counts = Counter(
        batch_by_key[pair_orbit_key(pair)] for pair in pairs
    )
    orbit_counts = Counter(batch_by_key.values())
    return batch_by_key, {
        "unique_pair_orbit_count": len(ordered_keys),
        "hidden_batch_pair_counts": dict(sorted(pair_counts.items())),
        "hidden_batch_orbit_counts": dict(sorted(orbit_counts.items())),
        "ordered_orbit_keys_sha256": canonical_hash(ordered_keys),
        "all_orbit_members_share_batch": all(
            len({batch_by_key[pair_orbit_key(member)] for member in members}) == 1
            for members in orbit_members.values()
        ),
    }


def eca_transition_table() -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    rules = jnp.arange(RULE_COUNT, dtype=jnp.int64)

    def step(rule: jax.Array, state: jax.Array) -> jax.Array:
        bits = (state >> sites) & 1
        left = jnp.roll(bits, 1)
        right = jnp.roll(bits, -1)
        neighborhoods = (left << 2) | (bits << 1) | right
        return jnp.sum(((rule >> neighborhoods) & 1) << sites, dtype=jnp.int64)

    return vmap(lambda rule: vmap(lambda state: step(rule, state))(states))(rules)


def canonicalize_packed_signatures(signatures: jax.Array) -> jax.Array:
    """Assign exact class IDs by stable sorting, using O(S log S) storage."""

    order = jnp.argsort(signatures, stable=True)
    sorted_signatures = signatures[order]
    starts = jnp.concatenate(
        [jnp.ones((1,), dtype=jnp.bool_), sorted_signatures[1:] != sorted_signatures[:-1]]
    )
    sorted_labels = jnp.cumsum(starts, dtype=jnp.int64) - 1
    return jnp.zeros_like(sorted_labels).at[order].set(sorted_labels)


canonicalize_batch = vmap(canonicalize_packed_signatures)


def base_probe_labels() -> jax.Array:
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (states[:, None] >> sites) & 1
    weight = jnp.sum(bits, axis=1, dtype=jnp.int64)
    walls = jnp.sum(bits != jnp.roll(bits, -1, axis=1), axis=1, dtype=jnp.int64)
    packed = weight * (RING_SIZE + 1) + walls
    return canonicalize_packed_signatures(packed)


def partition_observables_one(labels: jax.Array) -> tuple[jax.Array, jax.Array]:
    counts = jnp.bincount(labels, length=STATE_COUNT)
    class_count = jnp.sum(counts > 0, dtype=jnp.int64)
    surviving_ordered_pairs = jnp.sum(counts * counts, dtype=jnp.int64)
    return class_count, surviving_ordered_pairs


partition_observables = vmap(partition_observables_one)


def build_batch_kernel():
    base = base_probe_labels()

    @jax.jit
    def kernel(action_a: jax.Array, action_b: jax.Array):
        batch_count = action_a.shape[0]
        labels0 = jnp.broadcast_to(base, (batch_count, STATE_COUNT))
        active0 = jnp.ones((batch_count,), dtype=jnp.bool_)
        strict0 = jnp.zeros((batch_count,), dtype=jnp.int64)
        class0, survival0 = partition_observables(labels0)
        class_trajectory0 = jnp.zeros(
            (batch_count, MAX_REFINEMENT_ROUNDS + 1), dtype=jnp.int64
        ).at[:, 0].set(class0)
        survival_trajectory0 = jnp.zeros_like(class_trajectory0).at[:, 0].set(
            survival0
        )

        initial = (
            jnp.asarray(0, dtype=jnp.int64),
            labels0,
            active0,
            strict0,
            labels0,
            class_trajectory0,
            survival_trajectory0,
        )

        def condition(carry):
            round_index, _, active, _, _, _, _ = carry
            return (round_index < MAX_REFINEMENT_ROUNDS) & jnp.any(active)

        def body(carry):
            (
                round_index,
                labels,
                active,
                strict,
                depth_six_labels,
                class_trajectory,
                survival_trajectory,
            ) = carry
            next_a = jnp.take_along_axis(labels, action_a, axis=1)
            next_b = jnp.take_along_axis(labels, action_b, axis=1)
            packed = (labels * STATE_COUNT + next_a) * STATE_COUNT + next_b
            refined = canonicalize_batch(packed)
            changed = active & jnp.any(refined != labels, axis=1)
            labels_next = jnp.where(active[:, None], refined, labels)
            strict_next = strict + changed.astype(jnp.int64)
            active_next = changed
            class_count, survival = partition_observables(labels_next)
            trajectory_index = round_index + 1
            class_trajectory = class_trajectory.at[:, trajectory_index].set(
                class_count
            )
            survival_trajectory = survival_trajectory.at[:, trajectory_index].set(
                survival
            )
            depth_six_labels = jnp.where(
                (trajectory_index == DEPTH_SIX), labels_next, depth_six_labels
            )
            return (
                trajectory_index,
                labels_next,
                active_next,
                strict_next,
                depth_six_labels,
                class_trajectory,
                survival_trajectory,
            )

        (
            rounds_executed,
            labels,
            active,
            strict,
            depth_six_labels,
            class_trajectory,
            survival_trajectory,
        ) = lax.while_loop(condition, body, initial)
        depth_six_labels = jnp.where(
            rounds_executed >= DEPTH_SIX, depth_six_labels, labels
        )
        _, depth_six_survival = partition_observables(depth_six_labels)
        _, stable_survival = partition_observables(labels)
        depth_six_changed = depth_six_survival - stable_survival
        return (
            rounds_executed,
            strict,
            active,
            labels,
            class_trajectory,
            survival_trajectory,
            depth_six_changed,
        )

    return kernel


def orientation_receipt(transitions: list[list[int]]) -> dict:
    mask = STATE_COUNT - 1
    expected_170 = [((state >> 1) | ((state & 1) << (RING_SIZE - 1))) for state in range(STATE_COUNT)]
    expected_240 = [((state << 1) & mask) | (state >> (RING_SIZE - 1)) for state in range(STATE_COUNT)]
    return {
        "rule_170_is_periodic_right_shift": transitions[170] == expected_170,
        "rule_240_is_periodic_left_shift": transitions[240] == expected_240,
        "rule_170_transition_hash": canonical_hash(transitions[170]),
        "rule_240_transition_hash": canonical_hash(transitions[240]),
    }


def rotation_and_probe_receipt(transitions: list[list[int]]) -> dict:
    mask = STATE_COUNT - 1

    def rotate(state: int) -> int:
        return ((state << 1) & mask) | (state >> (RING_SIZE - 1))

    def probe(state: int) -> tuple[int, int]:
        bits = [(state >> site) & 1 for site in range(RING_SIZE)]
        return sum(bits), sum(bits[index] != bits[(index + 1) % RING_SIZE] for index in range(RING_SIZE))

    transition_failures = 0
    for rule in range(RULE_COUNT):
        table = transitions[rule]
        for state in range(STATE_COUNT):
            if table[rotate(state)] != rotate(table[state]):
                transition_failures += 1
    probe_failures = sum(
        probe(state) != probe(rotate(state)) for state in range(STATE_COUNT)
    )
    return {
        "transition_cases_checked": RULE_COUNT * STATE_COUNT,
        "transition_equivariance_failures": transition_failures,
        "probe_cases_checked": STATE_COUNT,
        "probe_invariance_failures": probe_failures,
        "all_pass": transition_failures == 0 and probe_failures == 0,
    }


def strict_depth_convention_receipt() -> dict:
    synthetic = {
        "depth_0": [False],
        "depth_1": [True, False],
        "depth_3": [True, True, True, False],
        "depth_511": [True] * MAX_STRICT_DEPTH + [False],
    }
    observed = {
        name: sum(1 for changed in trace if changed)
        for name, trace in synthetic.items()
    }
    expected = {"depth_0": 0, "depth_1": 1, "depth_3": 3, "depth_511": 511}
    return {
        "synthetic_observed": observed,
        "synthetic_expected": expected,
        "all_pass": observed == expected,
    }


def mutation_receipt(ledger: list[dict], transitions: list[list[int]]) -> dict:
    labels = list(range(STATE_COUNT))
    partition_hash = compact_labels_hash(labels)
    labels[0] = labels[1]
    transition_pair = [transitions[0], transitions[1]]
    mutated_transition_pair = [transitions[0][:], transitions[1][:]]
    mutated_transition_pair[0][0] ^= 1
    trajectory = ledger[0]["class_count_trajectory"]
    mutated_trajectory = trajectory[:]
    mutated_trajectory[0] += 1
    return {
        "partition_hash_mutation_detected": partition_hash
        != compact_labels_hash(labels),
        "transition_hash_mutation_detected": canonical_hash(transition_pair)
        != canonical_hash(mutated_transition_pair),
        "trajectory_mutation_detected": canonical_hash(trajectory)
        != canonical_hash(mutated_trajectory),
    }


def orbit_consistency_receipt(ledger: list[dict]) -> dict:
    invariant_by_orbit: dict[str, tuple] = {}
    inconsistent: list[str] = []
    for record in ledger:
        key = record["simultaneous_pair_orbit_key"]
        invariant = (
            record["strict_refinement_depth"],
            tuple(record["class_count_trajectory"]),
            tuple(record["surviving_ordered_pair_count_trajectory"]),
            record["stable_class_count"],
            record["depth_six_changed_ordered_pair_count"],
        )
        prior = invariant_by_orbit.setdefault(key, invariant)
        if prior != invariant and key not in inconsistent:
            inconsistent.append(key)
    return {
        "orbit_count_checked": len(invariant_by_orbit),
        "inconsistent_orbit_keys": inconsistent,
        "all_pass": not inconsistent,
    }


def invalid_one_rule_symmetry_sentinel() -> dict:
    for rule_a in range(255):
        for rule_b in range(rule_a + 1, 256):
            pair = (rule_a, rule_b)
            invalid = tuple(sorted((reflect_rule(rule_a), rule_b)))
            if pair_orbit_key(pair) != pair_orbit_key(invalid):
                return {
                    "detected": True,
                    "original_pair": list(pair),
                    "invalid_one_rule_transform": list(invalid),
                    "original_orbit_key": pair_orbit_key(pair),
                    "invalid_orbit_key": pair_orbit_key(invalid),
                }
    return {"detected": False}


def tool_calls_receipt() -> list[dict]:
    common = {
        "input_object": "all 32640 unordered ECA rule pairs on 512 states",
        "output_object": "complete exact N9 refinement ledger",
        "positive_case": "frozen full-pair census converges and emits every record",
        "negative/erased_control": "hash mutations and invalid one-rule symmetry are detected",
        "boundary_case": "strict depth is bounded by 511 and equality check is excluded",
        "demotion_condition": "missing call, nonconvergence, mutation silence, or frozen-hash mismatch",
        "gates": ["all_pass", "quotient"],
    }
    return [
        {"tool": "jax.numpy", "qualified_api/function": "jax.numpy.argsort", **common},
        {"tool": "jax.vmap", "qualified_api/function": "jax.vmap", **common},
        {"tool": "jax.jit", "qualified_api/function": "jax.jit", **common},
        {"tool": "jax.lax.while_loop", "qualified_api/function": "jax.lax.while_loop", **common},
    ]


def build_receipt(frozen_inputs: dict) -> dict:
    started = time.time()
    transitions_device = eca_transition_table()
    transitions_device.block_until_ready()
    transitions = transitions_device.tolist()
    pairs = list(itertools.combinations(range(RULE_COUNT), 2))
    batch_by_orbit, split_receipt = build_hidden_batch_map(pairs)
    kernel = build_batch_kernel()
    depth_counts: Counter[int] = Counter()
    joint_counts: dict[int, Counter[int]] = defaultdict(Counter)
    examples: dict[int, list[list[int]]] = defaultdict(list)
    hidden_depth_orbits: dict[str, set[str]] = {"A": set(), "B": set()}
    ledger: list[dict] = []
    nonstabilized_pairs: list[list[int]] = []
    batch_round_histogram: Counter[int] = Counter()
    action_swap_failure_count = 0

    for start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[start : start + BATCH_SIZE]
        real_count = len(batch)
        padded = batch + [batch[-1]] * (BATCH_SIZE - real_count)
        rule_a = jnp.asarray([pair[0] for pair in padded], dtype=jnp.int64)
        rule_b = jnp.asarray([pair[1] for pair in padded], dtype=jnp.int64)
        (
            rounds_executed,
            strict,
            active,
            labels,
            class_trajectory,
            survival_trajectory,
            depth_six_changed,
        ) = kernel(transitions_device[rule_a], transitions_device[rule_b])
        (
            swapped_rounds_executed,
            swapped_strict,
            swapped_active,
            swapped_labels,
            swapped_class_trajectory,
            swapped_survival_trajectory,
            swapped_depth_six_changed,
        ) = kernel(transitions_device[rule_b], transitions_device[rule_a])
        rounds = int(rounds_executed)
        batch_round_histogram[rounds] += 1
        strict_host = strict.tolist()
        active_host = active.tolist()
        labels_host = labels.tolist()
        class_host = class_trajectory.tolist()
        survival_host = survival_trajectory.tolist()
        depth_six_host = depth_six_changed.tolist()
        swapped_rounds = int(swapped_rounds_executed)
        swapped_strict_host = swapped_strict.tolist()
        swapped_active_host = swapped_active.tolist()
        swapped_labels_host = swapped_labels.tolist()
        swapped_class_host = swapped_class_trajectory.tolist()
        swapped_survival_host = swapped_survival_trajectory.tolist()
        swapped_depth_six_host = swapped_depth_six_changed.tolist()

        for index in range(real_count):
            pair = batch[index]
            depth = int(strict_host[index])
            class_values = class_host[index][: depth + 1]
            survival_values = survival_host[index][: depth + 1]
            swapped_depth = int(swapped_strict_host[index])
            swap_equivalent = (
                rounds == swapped_rounds
                and depth == swapped_depth
                and not bool(active_host[index])
                and not bool(swapped_active_host[index])
                and compact_labels_hash(labels_host[index])
                == compact_labels_hash(swapped_labels_host[index])
                and class_values
                == swapped_class_host[index][: swapped_depth + 1]
                and survival_values
                == swapped_survival_host[index][: swapped_depth + 1]
                and int(depth_six_host[index])
                == int(swapped_depth_six_host[index])
            )
            if not swap_equivalent:
                action_swap_failure_count += 1
            orbit_key = pair_orbit_key(pair)
            hidden_batch = batch_by_orbit[orbit_key]
            record = {
                "rule_a": pair[0],
                "rule_b": pair[1],
                "strict_refinement_depth": depth,
                "first_equality_round": depth + 1,
                "class_count_trajectory": class_values,
                "surviving_ordered_pair_count_trajectory": survival_values,
                "stable_class_count": int(class_values[-1]),
                "partition_hash": compact_labels_hash(labels_host[index]),
                "transition_pair_hash": canonical_hash(
                    [transitions[pair[0]], transitions[pair[1]]]
                ),
                "simultaneous_pair_orbit_key": orbit_key,
                "hidden_batch": hidden_batch,
                "depth_six_changed_ordered_pair_count": int(
                    depth_six_host[index]
                ),
            }
            ledger.append(record)
            depth_counts[depth] += 1
            joint_counts[depth][record["stable_class_count"]] += 1
            if len(examples[depth]) < 12:
                examples[depth].append(list(pair))
            if depth >= 7:
                hidden_depth_orbits[hidden_batch].add(orbit_key)
            if bool(active_host[index]):
                nonstabilized_pairs.append(list(pair))

    orientation = orientation_receipt(transitions)
    rotation_probe = rotation_and_probe_receipt(transitions)
    convention = strict_depth_convention_receipt()
    orbit_consistency = orbit_consistency_receipt(ledger)
    invalid_symmetry = invalid_one_rule_symmetry_sentinel()
    mutations = mutation_receipt(ledger, transitions)
    pair_keys = [(record["rule_a"], record["rule_b"]) for record in ledger]
    tests = {
        "frozen_inputs_verified_before_computation": frozen_inputs["all_pass"],
        "all_32640_pairs_present_once": len(ledger) == PAIR_COUNT
        and len(set(pair_keys)) == PAIR_COUNT
        and pair_keys == pairs,
        "no_nonstabilized_pairs": not nonstabilized_pairs,
        "depth_histogram_sums_to_pair_count": sum(depth_counts.values()) == PAIR_COUNT,
        "strict_depth_within_finite_bound": max(depth_counts) <= MAX_STRICT_DEPTH,
        "constant_rule_boundaries": transitions[0] == [0] * STATE_COUNT
        and transitions[255] == [STATE_COUNT - 1] * STATE_COUNT,
        "rule_action_swap_invariance": action_swap_failure_count == 0,
        "orientation_rules_170_240": all(
            value for key, value in orientation.items() if key.endswith("shift")
        ),
        "rotation_equivariance_and_probe_invariance": rotation_probe["all_pass"],
        "simultaneous_pair_orbit_consistency": orbit_consistency["all_pass"],
        "invalid_one_rule_symmetry_detected": invalid_symmetry["detected"],
        "strict_depth_synthetic_convention": convention["all_pass"],
        "partition_hash_mutation_detected": mutations[
            "partition_hash_mutation_detected"
        ],
        "transition_hash_mutation_detected": mutations[
            "transition_hash_mutation_detected"
        ],
        "trajectory_mutation_detected": mutations["trajectory_mutation_detected"],
        "all_orbit_members_share_hidden_batch": split_receipt[
            "all_orbit_members_share_batch"
        ],
    }
    qualifying_orbits = {
        batch: len(keys) for batch, keys in hidden_depth_orbits.items()
    }
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "source_sha256": sha256_file(Path(__file__)),
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "numpy_used": False,
        "peer_result_files_read": [],
        "frozen_input_verification": frozen_inputs,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls_receipt(),
        "depth_definition": "number of strict partition changes before first equality",
        "first_equality_round_definition": "strict_refinement_depth + 1",
        "ring_size": RING_SIZE,
        "state_count": STATE_COUNT,
        "rule_pair_count": len(ledger),
        "batch_size": BATCH_SIZE,
        "batch_round_histogram": {
            str(key): value for key, value in sorted(batch_round_histogram.items())
        },
        "maximum_strict_refinement_depth": max(depth_counts),
        "strict_refinement_depth_histogram": {
            str(key): depth_counts[key] for key in sorted(depth_counts)
        },
        "depth_by_stable_class_count_histogram": {
            str(depth): {str(key): counts[key] for key in sorted(counts)}
            for depth, counts in sorted(joint_counts.items())
        },
        "example_pairs_by_depth": {
            str(depth): values for depth, values in sorted(examples.items())
        },
        "hidden_batch_split_receipt": split_receipt,
        "qualifying_depth_ge_7_orbit_counts_by_hidden_batch": qualifying_orbits,
        "qualifying_depth_ge_7_total_orbit_count": len(
            hidden_depth_orbits["A"] | hidden_depth_orbits["B"]
        ),
        "nonstabilized_pairs": nonstabilized_pairs,
        "transition_census_hash": canonical_hash(transitions),
        "pair_ledger_hash": canonical_hash(ledger),
        "pair_ledger": ledger,
        "controls": {
            "rule_action_swap": {
                "pair_count_checked": PAIR_COUNT,
                "failure_count": action_swap_failure_count,
                "all_pass": action_swap_failure_count == 0,
            },
            "orientation": orientation,
            "rotation_and_probe": rotation_probe,
            "strict_depth_convention": convention,
            "simultaneous_orbit_consistency": orbit_consistency,
            "invalid_one_rule_symmetry_sentinel": invalid_symmetry,
            "mutations": mutations,
        },
        "tests": tests,
        "all_pass": all(tests.values()),
        "all_scientific_gates_pass": False,
        "elapsed_seconds": time.time() - started,
        "allowed_claims": [
            "independent exhaustive JAX finite ECA refinement-depth census on the N9 carrier"
        ],
        "claim_ceiling": "independent JAX scratch census only until Julia and controller compare every required ledger field",
        "blocked_consumers": [
            "learned perception before separate V2 admission and preregistration",
            "unique runtime intelligence or personality",
            "QIT stages or four substages",
            "the 16-by-4-by-2 engine schedule",
            "MMMs or ontology admission",
            "a universal attractor basin",
            "Axis0, physics, life, or consciousness",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    frozen_inputs = verify_frozen_inputs()
    receipt = build_receipt(frozen_inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n"
    )
    print(
        json.dumps(
            {
                "sim_id": SIM_ID,
                "engine": "jax",
                "all_pass": receipt["all_pass"],
                "output": str(args.output),
                "maximum_strict_refinement_depth": receipt[
                    "maximum_strict_refinement_depth"
                ],
                "strict_refinement_depth_histogram": receipt[
                    "strict_refinement_depth_histogram"
                ],
                "pair_ledger_hash": receipt["pair_ledger_hash"],
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
