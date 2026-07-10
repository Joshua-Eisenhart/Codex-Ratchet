#!/usr/bin/env python3
"""Independent JAX x64 exhaustive lane for the v1 behavioral-object card.

This scratch-diagnostic builder reads only the frozen local specification,
preregistration receipt, and object card. It never reads peer-engine results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
from jax import lax, vmap


SIM_ID = "finite_probe_behavioral_object_engine_v1"
SCHEMA = "codex_ratchet.finite_probe_behavioral_object_engine_v1.jax_result.v1"
CLASSIFICATION = "scratch_diagnostic"
SOURCE_PATH = Path(__file__).resolve()
SIM_DIR = SOURCE_PATH.parent
REPO_ROOT = SIM_DIR.parents[2]
SPEC_PATH = SIM_DIR / "spec.json"
PREREG_PATH = SIM_DIR / "preregistration_receipt.json"
OBJECT_CARD_PATH = SIM_DIR / "wizard_v4_3_object_card.json"
DEFAULT_OUTPUT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"

TAG = "ECA6-PRBOG-v1"
RING_SIZE = 6
STATE_COUNT = 1 << RING_SIZE
RULE_COUNT = 256
MAX_REFINEMENT_DEPTH = STATE_COUNT - 1
ORDERED_PAIR_COUNT = STATE_COUNT * STATE_COUNT
EXPECTED_ORBIT_COUNT = 88
EXPECTED_STRUCTURAL_HASHES = {
    "5acf9e8048dcffd3a82c090e72a27e080926471d5a0e06430c516012a8d1ea33",
    "d588f62c217f478e533475df0f998289058f5a5e4179bc3697a99c3e4fc3a471",
}


TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Required independent x64 exhaustive runtime for all 256 ECA rules and all frozen fixtures.",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "Exact integer and Boolean array substrate for transitions, probes, partitions, labels, and baselines.",
    },
    "jax.vmap": {
        "tried": True,
        "used": True,
        "reason": "Batches rule transitions, symmetry transforms, fixtures, mutations, and baseline confusion censuses.",
    },
    "jax.lax.fori_loop": {
        "tried": True,
        "used": True,
        "reason": "Executes the frozen 63-step monotone partition-refinement closure without host branching.",
    },
    "jax.jit": {
        "tried": True,
        "used": True,
        "reason": "Compiles the complete finite transition, partition, mutation, and baseline census.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Frozen-input parsing, canonical SHA-256 ordering, and terminal JSON receipt serialization only.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Forbidden on the claim path; no NumPy import or bridge is present.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "Peer runtime and peer result reads are forbidden in this independent lane.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "The learned proxy belongs to its independent engine lane.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "load_bearing",
    "jax.vmap": "load_bearing",
    "jax.lax.fori_loop": "load_bearing",
    "jax.jit": "supportive",
    "python_stdlib": "supportive",
    "numpy": None,
    "julia": None,
    "pytorch": None,
}

TOOL_CALLS = [
    {
        "tool": "jax.vmap",
        "qualified_api/function": "jax.vmap(run_jax.eca_step)",
        "input_object": "all 256 ECA rules crossed with all 64 six-bit ring states",
        "output_object": "exact 256x64 int64 transition census",
        "positive_case": "every transition is in the closed carrier and every frozen fixture indexes the census",
        "negative/erased_control": "a one-bit transition mutation is independently refined for every fixture",
        "boundary_case": "rules 0 and 255 map every state to the two constant carrier states",
        "demotion_condition": "demote all exact JAX claims if coverage, range, or constant-rule checks fail",
        "gates": ["all_pass", "exact_transition_census", "mutation_control"],
    },
    {
        "tool": "jax.vmap",
        "qualified_api/function": "jax.vmap(run_jax.rule_symmetry_images)",
        "input_object": "all 256 eight-bit ECA truth tables",
        "output_object": "identity, reflection, black-white conjugate, and reflected-conjugate rule images",
        "positive_case": "canonical closure yields exactly 88 frozen symmetry orbits with no split intersection",
        "negative/erased_control": "an injected train-orbit member in test is rejected before any learning result can be consumed",
        "boundary_case": "self-symmetric rules retain an orbit smaller than four",
        "demotion_condition": "reject the packet if orbit count, frozen block membership, uniqueness, or leakage sentinel differs",
        "gates": ["all_pass", "split_integrity", "leakage_control"],
    },
    {
        "tool": "jax.lax.fori_loop",
        "qualified_api/function": "jax.lax.fori_loop(run_jax.refine_stable_partition)",
        "input_object": "probe labels and two exact successor tables for each of 96 frozen rule-pair fixtures",
        "output_object": "canonical stable labels, class counts, first stable depths, and depth-one/depth-two labels",
        "positive_case": "all partitions stabilize by the finite 63-step bound and are congruent under both actions",
        "negative/erased_control": "each fixture is rerun after one deterministic output-bit transition mutation",
        "boundary_case": "already-stable partitions remain unchanged after closure",
        "demotion_condition": "demote exact object claims if any fixture does not stabilize or has a successor conflict",
        "gates": ["all_pass", "stable_partition", "quotient", "exact_oracle"],
    },
    {
        "tool": "jax.vmap",
        "qualified_api/function": "jax.vmap(run_jax.binary_metrics)",
        "input_object": "ordered 4096-pair exact labels and every preregistered rule-blind baseline",
        "output_object": "per-fixture confusion counts, MCC, balanced accuracy, positive recall, and false-positive rate",
        "positive_case": "the exact stable-refinement oracle is perfect on every fixture",
        "negative/erased_control": "always-negative, probe-only, shallow-refinement, rotation, and train-prevalence baselines remain separately visible",
        "boundary_case": "zero-denominator MCC is reported as zero while raw confusion counts remain authoritative",
        "demotion_condition": "demote the baseline census if the exact oracle is imperfect or any confusion total is not 4096",
        "gates": ["all_pass", "baseline_census", "exact_oracle"],
    },
    {
        "tool": "jax.numpy",
        "qualified_api/function": "run_jax.canonicalize_rows via jax.numpy.all, where, and min",
        "input_object": "64 finite state signatures per refinement step",
        "output_object": "minimum-representative canonical equivalence labels",
        "positive_case": "equal signatures receive equal labels and each label is the minimum state in its class",
        "negative/erased_control": "shallow probe and one-bit transition mutations produce independently canonicalized comparison partitions",
        "boundary_case": "a singleton class labels itself",
        "demotion_condition": "demote partition and baseline claims if canonical labels are non-idempotent or leave the state carrier",
        "gates": ["all_pass", "stable_partition", "baseline_census"],
    },
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def compact_labels_hash(labels: Sequence[int]) -> str:
    renaming: dict[int, int] = {}
    canonical: list[int] = []
    for label in labels:
        key = int(label)
        if key not in renaming:
            renaming[key] = len(renaming)
        canonical.append(renaming[key])
    payload = json.dumps(canonical, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def relative_repo_path(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT))


def eca_step(state: jax.Array, rule: jax.Array) -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (state >> sites) & jnp.int64(1)
    left = jnp.roll(bits, 1)
    right = jnp.roll(bits, -1)
    neighborhoods = (left << 2) | (bits << 1) | right
    next_bits = (rule >> neighborhoods) & jnp.int64(1)
    return jnp.sum(next_bits << sites, dtype=jnp.int64)


def all_transition_tables(rules: jax.Array, states: jax.Array) -> jax.Array:
    return vmap(lambda rule: vmap(lambda state: eca_step(state, rule))(states))(rules)


def transform_rule(rule: jax.Array, reflect: bool, conjugate: bool) -> jax.Array:
    neighborhoods = jnp.arange(8, dtype=jnp.int64)
    left = (neighborhoods >> 2) & 1
    center = (neighborhoods >> 1) & 1
    right = neighborhoods & 1
    source_left = jnp.where(reflect, right, left)
    source_right = jnp.where(reflect, left, right)
    source_center = center
    source_left = jnp.where(conjugate, 1 - source_left, source_left)
    source_center = jnp.where(conjugate, 1 - source_center, source_center)
    source_right = jnp.where(conjugate, 1 - source_right, source_right)
    source = (source_left << 2) | (source_center << 1) | source_right
    outputs = (rule >> source) & 1
    outputs = jnp.where(conjugate, 1 - outputs, outputs)
    return jnp.sum(outputs << neighborhoods, dtype=jnp.int64)


def rule_symmetry_images(rule: jax.Array) -> jax.Array:
    return jnp.stack(
        [
            transform_rule(rule, False, False),
            transform_rule(rule, True, False),
            transform_rule(rule, False, True),
            transform_rule(rule, True, True),
        ]
    )


def canonical_probe_labels(states: jax.Array) -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (states[:, None] >> sites) & jnp.int64(1)
    weight = jnp.sum(bits, axis=1, dtype=jnp.int64)
    walls = jnp.sum(bits != jnp.roll(bits, -1, axis=1), axis=1, dtype=jnp.int64)
    rows = jnp.stack([weight, walls], axis=1)
    return canonicalize_rows(rows)


def canonicalize_rows(rows: jax.Array) -> jax.Array:
    flat = rows.reshape((STATE_COUNT, -1))
    equal = jnp.all(flat[:, None, :] == flat[None, :, :], axis=-1)
    indices = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    return jnp.min(jnp.where(equal, indices[None, :], STATE_COUNT), axis=1)


def refine_once(labels: jax.Array, action_a: jax.Array, action_b: jax.Array) -> jax.Array:
    signatures = jnp.stack([labels, labels[action_a], labels[action_b]], axis=1)
    return canonicalize_rows(signatures)


def refine_stable_partition(
    probe_labels: jax.Array, action_a: jax.Array, action_b: jax.Array
) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    depth_one = refine_once(probe_labels, action_a, action_b)
    depth_two = refine_once(depth_one, action_a, action_b)

    def body(_: int, carry: tuple[jax.Array, jax.Array, jax.Array]) -> tuple[jax.Array, jax.Array, jax.Array]:
        labels, first_stable_depth, depth = carry
        refined = refine_once(labels, action_a, action_b)
        now_stable = jnp.all(refined == labels)
        first_stable_depth = jnp.where(
            (first_stable_depth < 0) & now_stable, depth + 1, first_stable_depth
        )
        return refined, first_stable_depth, depth + 1

    stable, first_stable_depth, _ = lax.fori_loop(
        0,
        MAX_REFINEMENT_DEPTH,
        body,
        (probe_labels, jnp.int64(-1), jnp.int64(0)),
    )
    class_count = jnp.sum(
        stable == jnp.arange(STATE_COUNT, dtype=jnp.int64), dtype=jnp.int64
    )
    return stable, class_count, first_stable_depth, depth_one, depth_two


def quotient_congruence(
    labels: jax.Array, action_a: jax.Array, action_b: jax.Array
) -> tuple[jax.Array, jax.Array, jax.Array]:
    same = labels[:, None] == labels[None, :]
    conflict_a = same & (labels[action_a][:, None] != labels[action_a][None, :])
    conflict_b = same & (labels[action_b][:, None] != labels[action_b][None, :])
    return (
        ~(jnp.any(conflict_a) | jnp.any(conflict_b)),
        jnp.sum(conflict_a, dtype=jnp.int64),
        jnp.sum(conflict_b, dtype=jnp.int64),
    )


def equivalence_vector(labels: jax.Array) -> jax.Array:
    return (labels[:, None] == labels[None, :]).reshape((ORDERED_PAIR_COUNT,))


def rotation_equivalence(states: jax.Array) -> jax.Array:
    def rotate(state: jax.Array, amount: jax.Array) -> jax.Array:
        shift = amount % RING_SIZE
        inverse = (RING_SIZE - shift) % RING_SIZE
        return ((state << shift) | (state >> inverse)) & (STATE_COUNT - 1)

    rotations = vmap(
        lambda amount: vmap(lambda state: rotate(state, amount))(states)
    )(jnp.arange(RING_SIZE, dtype=jnp.int64))
    labels = jnp.min(rotations, axis=0)
    return equivalence_vector(labels)


def binary_metrics(target: jax.Array, prediction: jax.Array) -> jax.Array:
    target = target.astype(jnp.bool_)
    prediction = prediction.astype(jnp.bool_)
    tp = jnp.sum(target & prediction, dtype=jnp.int64)
    tn = jnp.sum(~target & ~prediction, dtype=jnp.int64)
    fp = jnp.sum(~target & prediction, dtype=jnp.int64)
    fn = jnp.sum(target & ~prediction, dtype=jnp.int64)
    tp_f, tn_f, fp_f, fn_f = [x.astype(jnp.float64) for x in (tp, tn, fp, fn)]
    positive_recall = jnp.where(tp + fn > 0, tp_f / (tp_f + fn_f), 0.0)
    negative_recall = jnp.where(tn + fp > 0, tn_f / (tn_f + fp_f), 0.0)
    false_positive_rate = jnp.where(tn + fp > 0, fp_f / (tn_f + fp_f), 0.0)
    denominator = jnp.sqrt(
        (tp_f + fp_f) * (tp_f + fn_f) * (tn_f + fp_f) * (tn_f + fn_f)
    )
    mcc = jnp.where(denominator > 0, (tp_f * tn_f - fp_f * fn_f) / denominator, 0.0)
    return jnp.array(
        [
            tp_f,
            tn_f,
            fp_f,
            fn_f,
            mcc,
            (positive_recall + negative_recall) / 2.0,
            positive_recall,
            false_positive_rate,
        ],
        dtype=jnp.float64,
    )


def mutate_transition(action_a: jax.Array, fixture_index: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    source = fixture_index % STATE_COUNT
    bit = (fixture_index // STATE_COUNT) % RING_SIZE
    original = action_a[source]
    mutated = original ^ (jnp.int64(1) << bit)
    return action_a.at[source].set(mutated), source, bit


def fixture_census(
    transition_census: jax.Array, fixture_pairs: jax.Array, probe_labels: jax.Array
) -> Mapping[str, jax.Array]:
    action_a = transition_census[fixture_pairs[:, 0]]
    action_b = transition_census[fixture_pairs[:, 1]]
    stable, class_count, stable_depth, depth_one, depth_two = vmap(
        lambda a, b: refine_stable_partition(probe_labels, a, b)
    )(action_a, action_b)
    congruent, conflict_a, conflict_b = vmap(quotient_congruence)(
        stable, action_a, action_b
    )
    fixture_indices = jnp.arange(fixture_pairs.shape[0], dtype=jnp.int64)
    mutated_a, mutation_source, mutation_bit = vmap(mutate_transition)(
        action_a, fixture_indices
    )
    mutated_stable, _, _, _, _ = vmap(
        lambda a, b: refine_stable_partition(probe_labels, a, b)
    )(mutated_a, action_b)
    return {
        "action_a": action_a,
        "action_b": action_b,
        "stable_labels": stable,
        "class_count": class_count,
        "stable_depth": stable_depth,
        "depth_one_labels": depth_one,
        "depth_two_labels": depth_two,
        "congruent": congruent,
        "conflict_a": conflict_a,
        "conflict_b": conflict_b,
        "mutated_stable_labels": mutated_stable,
        "mutation_source": mutation_source,
        "mutation_bit": mutation_bit,
        "mutation_changed_partition": jnp.any(mutated_stable != stable, axis=1),
    }


def symmetry_orbits(symmetry_images: Sequence[Sequence[int]]) -> list[list[int]]:
    unseen = set(range(RULE_COUNT))
    orbits: list[list[int]] = []
    while unseen:
        seed = min(unseen)
        pending = [seed]
        orbit: set[int] = set()
        while pending:
            rule = pending.pop()
            if rule in orbit:
                continue
            orbit.add(rule)
            pending.extend(int(image) for image in symmetry_images[rule])
        members = sorted(orbit)
        unseen.difference_update(members)
        orbits.append(members)
    return sorted(
        orbits,
        key=lambda members: sha256_bytes(
            f"{TAG}|orbit|{','.join(str(rule) for rule in members)}".encode()
        ),
    )


def flatten_fixture_groups(
    fixtures: Mapping[str, Sequence[Sequence[int]]]
) -> tuple[list[list[int]], list[str], dict[str, tuple[int, int]]]:
    ordered_names = ["train", "validation", "test_primary", "test_structural_holdout"]
    pairs: list[list[int]] = []
    split_names: list[str] = []
    slices: dict[str, tuple[int, int]] = {}
    for name in ordered_names:
        start = len(pairs)
        group = [[int(pair[0]), int(pair[1])] for pair in fixtures[name]]
        pairs.extend(group)
        split_names.extend([name] * len(group))
        slices[name] = (start, len(pairs))
    return pairs, split_names, slices


def validate_frozen_split(
    orbits: Sequence[Sequence[int]],
    fixtures: Mapping[str, Sequence[Sequence[int]]],
) -> dict[str, Any]:
    orbit_by_rule = {
        int(rule): orbit_index
        for orbit_index, members in enumerate(orbits)
        for rule in members
    }
    block_by_group = {
        "train": range(0, 60),
        "validation": range(60, 74),
        "test_primary": range(74, 88),
        "test_structural_holdout": range(74, 88),
    }
    expected_fixture_counts = {
        "train": 64,
        "validation": 16,
        "test_primary": 14,
        "test_structural_holdout": 2,
    }
    group_receipts: dict[str, Any] = {}
    for name, pairs in fixtures.items():
        rules = [int(rule) for pair in pairs for rule in pair]
        pair_orbits = [[orbit_by_rule[int(rule)] for rule in pair] for pair in pairs]
        pair_hashes = [
            sha256_bytes(f"{TAG}|pair|{int(a)},{int(b)}".encode()) for a, b in pairs
        ]
        allowed = set(block_by_group[name])
        group_receipts[name] = {
            "fixture_count": len(pairs),
            "fixture_count_matches_frozen_spec": len(pairs)
            == expected_fixture_counts[name],
            "rule_count": len(rules),
            "rules_unique": len(rules) == len(set(rules)),
            "pair_members_are_distinct": all(int(a) < int(b) for a, b in pairs),
            "pair_order_matches_frozen_sha256_order": name == "test_structural_holdout"
            or pair_hashes == sorted(pair_hashes),
            "pair_constituents_from_distinct_orbits": all(a != b for a, b in pair_orbits),
            "all_orbits_in_frozen_block": all(
                orbit_index in allowed for pair in pair_orbits for orbit_index in pair
            ),
            "orbit_indices": sorted({index for pair in pair_orbits for index in pair}),
        }

    train_orbits = set(group_receipts["train"]["orbit_indices"])
    validation_orbits = set(group_receipts["validation"]["orbit_indices"])
    test_orbits = set(group_receipts["test_primary"]["orbit_indices"]) | set(
        group_receipts["test_structural_holdout"]["orbit_indices"]
    )
    combined_test_pairs = list(fixtures["test_primary"]) + list(
        fixtures["test_structural_holdout"]
    )
    combined_test_rules = [int(rule) for pair in combined_test_pairs for rule in pair]
    combined_test_pair_hashes = [
        sha256_bytes(f"{TAG}|pair|{int(a)},{int(b)}".encode())
        for a, b in combined_test_pairs
    ]
    combined_test_integrity = {
        "fixture_count": len(combined_test_pairs),
        "fixture_count_matches_frozen_spec": len(combined_test_pairs) == 16,
        "rules_unique": len(combined_test_rules) == len(set(combined_test_rules)),
        "pair_order_matches_frozen_sha256_order": True,
    }
    no_cross_split_orbit = not (
        train_orbits & validation_orbits
        or train_orbits & test_orbits
        or validation_orbits & test_orbits
    )
    valid = (
        len(orbits) == EXPECTED_ORBIT_COUNT
        and all(
            receipt[gate]
            for receipt in group_receipts.values()
            for gate in (
                "fixture_count_matches_frozen_spec",
                "rules_unique",
                "pair_members_are_distinct",
                "pair_order_matches_frozen_sha256_order",
                "pair_constituents_from_distinct_orbits",
                "all_orbits_in_frozen_block",
            )
        )
        and all(combined_test_integrity.values())
        and no_cross_split_orbit
    )
    return {
        "valid": valid,
        "expected_orbit_count": EXPECTED_ORBIT_COUNT,
        "actual_orbit_count": len(orbits),
        "no_symmetry_orbit_crosses_splits": no_cross_split_orbit,
        "combined_test_integrity": combined_test_integrity,
        "groups": group_receipts,
    }


def leakage_sentinel_receipt(
    orbits: Sequence[Sequence[int]], fixtures: Mapping[str, Sequence[Sequence[int]]]
) -> dict[str, Any]:
    injected = {
        name: [[int(a), int(b)] for a, b in pairs]
        for name, pairs in fixtures.items()
    }
    train_rule = int(injected["train"][0][0])
    orbit = next(members for members in orbits if train_rule in members)
    injected_rule = int(next((rule for rule in orbit if rule != train_rule), train_rule))
    original_pair = injected["test_primary"][0]
    partner = original_pair[1]
    if injected_rule >= partner:
        injected["test_primary"][0] = [partner, injected_rule]
    else:
        injected["test_primary"][0] = [injected_rule, partner]
    injected_validation = validate_frozen_split(orbits, injected)
    return {
        "injected_train_rule": train_rule,
        "injected_symmetry_relative_rule": injected_rule,
        "test_pair_before": original_pair,
        "test_pair_after": injected["test_primary"][0],
        "validator_rejected_before_training": not injected_validation["valid"],
        "injected_validation": injected_validation,
    }


def metric_receipt(values: Sequence[float]) -> dict[str, Any]:
    names = [
        "true_positive",
        "true_negative",
        "false_positive",
        "false_negative",
        "mcc",
        "balanced_accuracy",
        "positive_recall",
        "false_positive_rate",
    ]
    receipt = {name: float(value) for name, value in zip(names, values)}
    for name in names[:4]:
        receipt[name] = int(round(receipt[name]))
    receipt["pair_total"] = sum(receipt[name] for name in names[:4])
    return receipt


def summarize_baseline_metrics(
    split_names: Sequence[str], metrics: Mapping[str, Sequence[Sequence[float]]]
) -> dict[str, Any]:
    return {
        baseline: [
            {"fixture_index": index, "split": split_names[index], **metric_receipt(row)}
            for index, row in enumerate(rows)
        ]
        for baseline, rows in metrics.items()
    }


def build_receipt(output_path: Path) -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    object_card = json.loads(OBJECT_CARD_PATH.read_text(encoding="utf-8"))
    spec_sha256 = sha256_file(SPEC_PATH)
    prereg_sha256 = sha256_file(PREREG_PATH)
    object_card_sha256 = sha256_file(OBJECT_CARD_PATH)

    fixture_pairs_host, split_names, split_slices = flatten_fixture_groups(spec["fixtures"])
    fixture_pairs = jnp.asarray(fixture_pairs_host, dtype=jnp.int64)
    rules = jnp.arange(RULE_COUNT, dtype=jnp.int64)
    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)

    transition_census = jax.jit(all_transition_tables)(rules, states)
    symmetry_images = jax.jit(vmap(rule_symmetry_images))(rules)
    orbits = symmetry_orbits(symmetry_images.tolist())
    split_validation = validate_frozen_split(orbits, spec["fixtures"])
    leakage_sentinel = leakage_sentinel_receipt(orbits, spec["fixtures"])

    probe_labels = canonical_probe_labels(states)
    census = jax.jit(fixture_census)(transition_census, fixture_pairs, probe_labels)
    stable_labels = census["stable_labels"]
    target = vmap(equivalence_vector)(stable_labels)
    depth_zero = jnp.broadcast_to(
        equivalence_vector(probe_labels), (fixture_pairs.shape[0], ORDERED_PAIR_COUNT)
    )
    depth_one = vmap(equivalence_vector)(census["depth_one_labels"])
    depth_two = vmap(equivalence_vector)(census["depth_two_labels"])
    rotation = jnp.broadcast_to(
        rotation_equivalence(states), (fixture_pairs.shape[0], ORDERED_PAIR_COUNT)
    )
    always_negative = jnp.zeros_like(target, dtype=jnp.bool_)

    train_start, train_stop = split_slices["train"]
    train_prevalence = jnp.mean(
        target[train_start:train_stop].astype(jnp.float64), axis=0
    )
    rule_blind_prediction = jnp.broadcast_to(
        train_prevalence > 0.5, (fixture_pairs.shape[0], ORDERED_PAIR_COUNT)
    )
    baseline_predictions = {
        "always_negative": always_negative,
        "probe_only_depth_zero": depth_zero,
        "exact_depth_one": depth_one,
        "exact_depth_two": depth_two,
        "cyclic_rotation_equivalence": rotation,
        "rule_blind_state_pair_prevalence_gt_half": rule_blind_prediction,
        "exact_stable_refinement_oracle": target,
    }
    baseline_metrics_jax = {
        name: vmap(binary_metrics)(target, prediction)
        for name, prediction in baseline_predictions.items()
    }

    stable_labels_host = stable_labels.tolist()
    mutated_labels_host = census["mutated_stable_labels"].tolist()
    partition_hashes = [compact_labels_hash(labels) for labels in stable_labels_host]
    mutated_partition_hashes = [
        compact_labels_hash(labels) for labels in mutated_labels_host
    ]
    structural_start, structural_stop = split_slices["test_structural_holdout"]
    train_validation_stop = split_slices["validation"][1]
    structural_hashes = partition_hashes[structural_start:structural_stop]
    train_validation_hashes = set(partition_hashes[:train_validation_stop])

    fixture_receipts = []
    class_counts = census["class_count"].tolist()
    stable_depths = census["stable_depth"].tolist()
    congruent = census["congruent"].tolist()
    conflict_a = census["conflict_a"].tolist()
    conflict_b = census["conflict_b"].tolist()
    mutation_sources = census["mutation_source"].tolist()
    mutation_bits = census["mutation_bit"].tolist()
    mutation_changed = census["mutation_changed_partition"].tolist()
    for index, pair in enumerate(fixture_pairs_host):
        fixture_receipts.append(
            {
                "fixture_index": index,
                "split": split_names[index],
                "rules": pair,
                "stable_depth": int(stable_depths[index]),
                "class_count": int(class_counts[index]),
                "stable_labels": stable_labels_host[index],
                "stable_partition_sha256": partition_hashes[index],
                "quotient_congruent": bool(congruent[index]),
                "action_a_conflicting_ordered_pairs": int(conflict_a[index]),
                "action_b_conflicting_ordered_pairs": int(conflict_b[index]),
                "one_bit_transition_mutation": {
                    "action": "first rule in fixture pair",
                    "source_state": int(mutation_sources[index]),
                    "target_output_bit_flipped": int(mutation_bits[index]),
                    "mutated_partition_sha256": mutated_partition_hashes[index],
                    "changed_exact_label_hash": partition_hashes[index]
                    != mutated_partition_hashes[index],
                    "classification": "label_hash_changed"
                    if mutation_changed[index]
                    else "behaviorally_silent",
                },
            }
        )

    exact_oracle_metrics = baseline_metrics_jax["exact_stable_refinement_oracle"]
    transition_range_pass = bool(
        jnp.all((transition_census >= 0) & (transition_census < STATE_COUNT))
    )
    tests = {
        "C_input_integrity": {
            "pass": spec_sha256 == prereg["spec_sha256"]
            and object_card_sha256 == prereg["object_card_sha256"]
            and prereg["builder_sources_present_when_frozen"] is False
            and spec["sim_id"] == SIM_ID
            and prereg["sim_id"] == SIM_ID
            and object_card["schema_version"]
            == "wizard_v4_3_primary_object_card_v1",
            "spec_hash_matches_preregistration": spec_sha256 == prereg["spec_sha256"],
            "object_card_hash_matches_preregistration": object_card_sha256
            == prereg["object_card_sha256"],
            "builder_sources_absent_when_frozen": prereg[
                "builder_sources_present_when_frozen"
            ]
            is False,
            "object_card_schema_matches": object_card["schema_version"]
            == "wizard_v4_3_primary_object_card_v1",
        },
        "C_jax_x64": {
            "pass": bool(jax.config.read("jax_enable_x64")),
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        },
        "T1_transition_census": {
            "pass": transition_census.shape == (RULE_COUNT, STATE_COUNT)
            and transition_range_pass
            and bool(jnp.all(transition_census[0] == 0))
            and bool(jnp.all(transition_census[255] == STATE_COUNT - 1)),
            "shape": list(transition_census.shape),
            "all_targets_in_carrier": transition_range_pass,
            "constant_rule_boundaries_pass": bool(
                jnp.all(transition_census[0] == 0)
                & jnp.all(transition_census[255] == STATE_COUNT - 1)
            ),
        },
        "T2_symmetry_and_split": {
            "pass": split_validation["valid"],
            **split_validation,
        },
        "C_split_leakage_sentinel": {
            "pass": leakage_sentinel["validator_rejected_before_training"],
            **leakage_sentinel,
        },
        "T3_stable_partition": {
            "pass": all(depth >= 0 for depth in stable_depths)
            and all(bool(value) for value in congruent),
            "all_96_fixtures_stabilized": all(depth >= 0 for depth in stable_depths),
            "maximum_observed_stable_depth": max(stable_depths),
            "all_96_quotients_congruent": all(bool(value) for value in congruent),
        },
        "T4_structural_holdout_hashes": {
            "pass": set(structural_hashes) == EXPECTED_STRUCTURAL_HASHES
            and all(value not in train_validation_hashes for value in structural_hashes),
            "expected_hashes": sorted(EXPECTED_STRUCTURAL_HASHES),
            "actual_hashes": structural_hashes,
            "excluded_from_train_and_validation": all(
                value not in train_validation_hashes for value in structural_hashes
            ),
        },
        "T5_exact_oracle": {
            "pass": bool(
                jnp.all(exact_oracle_metrics[:, 0] + exact_oracle_metrics[:, 1] == ORDERED_PAIR_COUNT)
                & jnp.all(exact_oracle_metrics[:, 2:4] == 0)
            ),
            "all_fixture_confusion_totals": (
                exact_oracle_metrics[:, :4].sum(axis=1).astype(jnp.int64).tolist()
            ),
            "all_false_positive_and_false_negative_counts_zero": bool(
                jnp.all(exact_oracle_metrics[:, 2:4] == 0)
            ),
        },
        "C_one_bit_transition_mutations": {
            "pass": len(mutation_changed) == len(fixture_pairs_host),
            "fixture_count": len(mutation_changed),
            "label_hash_changed_count": sum(bool(value) for value in mutation_changed),
            "behaviorally_silent_count": sum(not bool(value) for value in mutation_changed),
            "every_mutation_explicitly_classified": len(mutation_changed)
            == len(fixture_pairs_host),
        },
        "T9_adaptive_replaceability_boundary": {
            "pass": False,
            "reason": "This JAX lane replicates exact construction and baseline roles only; no full role-neutral 3x3 adaptive replacement matrix was executed.",
            "runtime_uniqueness_claimed": False,
            "role_contribution": "exact exhaustive replication receipt present",
            "runtime_replaceability": "not measured by this lane",
            "resource_advantage": "not measured by this lane",
            "diversity_gain": "not measured by this lane",
            "claim_ceiling": "independent JAX exact census only",
        },
    }
    scientific_tests_excluding_t9 = {
        name: receipt
        for name, receipt in tests.items()
        if name != "T9_adaptive_replaceability_boundary"
    }
    exact_lane_pass = all(bool(receipt["pass"]) for receipt in scientific_tests_excluding_t9.values())
    all_scientific_gates_pass = all(bool(receipt["pass"]) for receipt in tests.values())

    baseline_metrics_host = {
        name: values.tolist() for name, values in baseline_metrics_jax.items()
    }
    return {
        "schema": SCHEMA,
        "schema_version": "three_engine_sim_lane_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "engine_role": spec["engine_contract"]["roles"]["jax"],
        "engine_contract": spec["engine_contract"],
        "source_path": relative_repo_path(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "output_path": str(output_path),
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "classical_finite_exhaustive",
        "sim_class": "cross_rule_behavioral_partition_census",
        "purpose": "Independently reconstruct exact probe-relative behavioral objects and rule-blind baselines for every frozen v1 fixture.",
        "scientific_question": spec["claim"],
        "carrier_layer": "all 64 binary states on a periodic six-site ring",
        "geometry_layer": "cyclic ring presentation and ECA reflection/conjugacy rule symmetries",
        "bridge_layer": "none",
        "cut_layer": "finite stable refinement bounded by 63 strict refinements",
        "branch_status_before_run": prereg["status"],
        "required_inputs": [
            relative_repo_path(SPEC_PATH),
            relative_repo_path(PREREG_PATH),
            relative_repo_path(OBJECT_CARD_PATH),
        ],
        "data_or_artifact_dependencies": [],
        "reads_peer_result": False,
        "peer_result_paths_read": [],
        "numpy_on_claim_path": False,
        "forbidden_bridges_used": [],
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "jax_version": jax.__version__,
        "packages_used": ["jax", "jax.numpy", "jax.vmap", "jax.lax", "jax.jit"],
        "aligned_packages_load_bearing": [
            "jax.numpy",
            "jax.vmap",
            "jax.lax.fori_loop",
        ],
        "required_tools": ["jax", "jax.numpy", "jax.vmap", "jax.lax.fori_loop"],
        "actual_tools_used": [
            "jax",
            "jax.numpy",
            "jax.vmap",
            "jax.lax.fori_loop",
            "jax.jit",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": TOOL_CALLS,
        "claim_path_tools": [
            "jax.vmap(run_jax.eca_step)",
            "jax.vmap(run_jax.rule_symmetry_images)",
            "jax.lax.fori_loop(run_jax.refine_stable_partition)",
            "jax.vmap(run_jax.binary_metrics)",
        ],
        "proof_surfaces_used": ["exact exhaustive finite equality"],
        "foreign_runtime_manifest": {
            "jax": {
                "role": spec["engine_contract"]["roles"]["jax"],
                "packages": ["jax", "jax.numpy", "jax.vmap", "jax.lax", "jax.jit"],
                "x64": True,
            },
            "julia": {"used": False, "reason": "peer result reads forbidden"},
            "pytorch": {"used": False, "reason": "peer result reads forbidden"},
            "tensor_exchange": "none",
        },
        "input_integrity": {
            "spec_path": relative_repo_path(SPEC_PATH),
            "spec_sha256": spec_sha256,
            "preregistered_spec_sha256": prereg["spec_sha256"],
            "object_card_path": relative_repo_path(OBJECT_CARD_PATH),
            "object_card_sha256": object_card_sha256,
            "preregistered_object_card_sha256": prereg["object_card_sha256"],
            "preregistration_path": relative_repo_path(PREREG_PATH),
            "preregistration_sha256": prereg_sha256,
        },
        "fixture_summary": {
            "ring_size": RING_SIZE,
            "state_count": STATE_COUNT,
            "rule_count": RULE_COUNT,
            "ordered_state_pair_count_per_fixture": ORDERED_PAIR_COUNT,
            "fixture_count": len(fixture_pairs_host),
            "fixture_slices": {
                name: {"start_inclusive": start, "stop_exclusive": stop}
                for name, (start, stop) in split_slices.items()
            },
            "probe_labels": probe_labels.tolist(),
            "rule_transition_table_sha256": canonical_hash(transition_census.tolist()),
        },
        "rule_symmetry": {
            "tag": TAG,
            "orbit_count": len(orbits),
            "ordered_orbits": orbits,
            "ordered_orbits_sha256": canonical_hash(orbits),
            "split_validation": split_validation,
        },
        "behavioral_partitions": {
            "canonical_label_convention": "minimum state index in each equivalence class",
            "maximum_refinement_depth": MAX_REFINEMENT_DEPTH,
            "fixtures": fixture_receipts,
            "all_stable_labels_sha256": canonical_hash(stable_labels_host),
            "all_ordered_pair_targets_sha256": canonical_hash(target.tolist()),
        },
        "baselines": {
            "rule_blind_prevalence_definition": "training-fixture positive prevalence for each ordered state pair; positive iff prevalence is strictly greater than 0.5",
            "rule_blind_train_prevalence": train_prevalence.tolist(),
            "per_fixture_metrics": summarize_baseline_metrics(
                split_names, baseline_metrics_host
            ),
            "metric_vector_order": [
                "true_positive",
                "true_negative",
                "false_positive",
                "false_negative",
                "mcc",
                "balanced_accuracy",
                "positive_recall",
                "false_positive_rate",
            ],
        },
        "controls": {
            "split_leakage_sentinel": leakage_sentinel,
            "one_bit_transition_mutations": [
                receipt["one_bit_transition_mutation"] for receipt in fixture_receipts
            ],
            "constant_rule_boundaries": {
                "rule_0_all_zero": bool(jnp.all(transition_census[0] == 0)),
                "rule_255_all_one": bool(
                    jnp.all(transition_census[255] == STATE_COUNT - 1)
                ),
            },
        },
        "tests": tests,
        "exact_lane_pass": exact_lane_pass,
        "all_pass": exact_lane_pass,
        "all_scientific_gates_pass": all_scientific_gates_pass,
        "scientific_red_gates": [
            name for name, receipt in tests.items() if not bool(receipt["pass"])
        ],
        "artifact_hashes": {
            "transition_census_sha256": canonical_hash(transition_census.tolist()),
            "partition_labels_sha256": canonical_hash(stable_labels_host),
            "ordered_pair_targets_sha256": canonical_hash(target.tolist()),
            "baseline_metrics_sha256": canonical_hash(baseline_metrics_host),
            "fixture_receipts_sha256": canonical_hash(fixture_receipts),
        },
        "T9_output_vector": {
            "role_contribution": "independent exact exhaustive construction and baseline census",
            "runtime_replaceability": "not tested",
            "resource_advantage": "not tested",
            "diversity_gain": "not tested",
            "claim_ceiling": "independent JAX exact census; no runtime uniqueness or three-engine nonredundancy",
        },
        "allowed_claims": [
            "independent exact x64 transition census for all 256 ECA rules on the six-bit ring",
            "independent exact stable behavioral partitions for the 96 frozen fixtures",
            "independent exact rule-blind baseline census",
            "split-symmetry and transition-mutation control receipts",
        ],
        "claim_ceiling": "independent bounded JAX exact census only; learned transfer, engine nonredundancy, and downstream object admission require controller evidence",
        "blocked_consumers": spec["blocked_consumers"],
        "eligible_consumers": ["bounded closed-receipt controller comparison only"],
        "demotion_condition": "demote every JAX-scoped exact claim if exact_lane_pass is false, any peer-result read occurs, or NumPy enters the claim path",
        "result_summary": "independent exact JAX census passed"
        if exact_lane_pass
        else "one or more independent exact JAX gates failed",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = build_receipt(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
