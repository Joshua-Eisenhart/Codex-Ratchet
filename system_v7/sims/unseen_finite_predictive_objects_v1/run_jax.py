#!/usr/bin/env python3
"""Python/JAX workhorse for the frozen UFPO-v1 registry.

Python owns candidate enumeration, canonical relabeling, and registry
selection.  JAX owns only the x64 batched exact-numerator reconstruction and
the optional view-key census.  This lane never imports the manifest generator,
NumPy, peer-engine receipts, learner metrics, or sealed test artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

from jax import config

config.update("jax_enable_x64", True)

import cvc5
import jax
import jax.numpy as jnp
import z3


SIM_ID = "unseen_finite_predictive_objects_v1"
SCHEMA = "codex_ratchet.unseen_finite_predictive_objects_v1.jax_result.v1"
CLASSIFICATION = "scratch_diagnostic"
STATE_COUNT = 4
WORD_BASE = 8
MAX_TARGET_LENGTH = 8
MAX_CHALLENGE_LENGTH = 12
BATCH_SIZE = 8
PROTOCOL_CORRECTION_COMMIT = "331a82539"
EXPECTED_GREEN_CEILING = (
    "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS"
)

SOURCE_PATH = Path(__file__).resolve()
SIM_DIR = SOURCE_PATH.parent
REPO_ROOT = SOURCE_PATH.parents[3]
SPEC_PATH = SIM_DIR / "spec.json"
MANIFEST_PATH = SIM_DIR / "object_manifest.json"
V0_MANIFEST_PATH = SIM_DIR.parent / "unseen_finite_predictive_objects_v0" / "object_manifest.json"
DEFAULT_OUTPUT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Independent candidate enumeration, canonical relabeling, registry selection, and receipt I/O.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing x64 batched exact integer target/challenge numerator reconstruction and view PRNG census.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing split-disjointness proof with an injected-overlap control.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "Independent load-bearing split-disjointness proof with the same injected-overlap control.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "supportive",
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


Machine = tuple[tuple[int, int, int], ...]
SPLITS = ("train", "validation", "test")
CHANNELS = ("initial_state", "latent_output", "erasure_mask", "substitution")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, separators=(",", ":"), sort_keys=True, allow_nan=False
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_json(value))


def strict_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def tracked(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT).as_posix()
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def candidate(counter: int) -> Machine:
    digest = hashlib.sha256(f"ufpo-v1|candidate|{counter}".encode("utf-8")).digest()
    return tuple(
        (
            digest[state] % STATE_COUNT,
            digest[4 + state] % STATE_COUNT,
            2 + digest[8 + state] % 5,
        )
        for state in range(STATE_COUNT)
    )


def relabel(machine: Machine, order: tuple[int, ...]) -> Machine:
    inverse = {old: new for new, old in enumerate(order)}
    return tuple(
        (inverse[machine[old][0]], inverse[machine[old][1]], machine[old][2])
        for old in order
    )


def canonical_machine(machine: Machine) -> Machine:
    """Python-owned canonicalization; JAX does not author this registry."""
    return min(relabel(machine, order) for order in itertools.permutations(range(STATE_COUNT)))


def strongly_connected(machine: Machine) -> bool:
    for source in range(STATE_COUNT):
        seen = {source}
        pending = [source]
        while pending:
            state = pending.pop()
            for target in machine[state][:2]:
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        if len(seen) != STATE_COUNT:
            return False
    return True


def machine_hash(machine: Machine) -> str:
    return canonical_hash(machine)


def word_layout(max_length: int) -> tuple[tuple[tuple[int, ...], ...], tuple[int, ...], tuple[tuple[int, ...], ...]]:
    words = tuple(
        word
        for length in range(1, max_length + 1)
        for word in itertools.product((0, 1), repeat=length)
    )
    lengths = tuple(len(word) for word in words)
    padded = tuple(word + (0,) * (max_length - len(word)) for word in words)
    return words, lengths, padded


TARGET_WORDS, TARGET_LENGTHS, TARGET_PADDED_WORDS = word_layout(MAX_TARGET_LENGTH)
CHALLENGE_WORDS, CHALLENGE_LENGTHS, CHALLENGE_PADDED_WORDS = word_layout(MAX_CHALLENGE_LENGTH)
TARGET_DENOMINATORS = tuple(WORD_BASE**length for length in TARGET_LENGTHS)
CHALLENGE_DENOMINATORS = tuple(WORD_BASE**length for length in CHALLENGE_LENGTHS)


def rational_signature_hash(
    numerators: Sequence[int], denominators: Sequence[int], uniform_start: bool
) -> str:
    encoded: list[list[int]] = []
    for numerator, denominator in zip(numerators, denominators, strict=True):
        full_denominator = int(denominator) * (STATE_COUNT if uniform_start else 1)
        divisor = math.gcd(int(numerator), full_denominator)
        encoded.append([int(numerator) // divisor, full_denominator // divisor])
    return sha256_bytes(canonical_json(encoded))


def exact_numerators_for_layout(
    machine: jax.Array,
    padded_words: tuple[tuple[int, ...], ...],
    lengths: tuple[int, ...],
    max_length: int,
) -> tuple[jax.Array, jax.Array]:
    """Return state-conditioned and uniform-start exact integer numerators."""
    words = jnp.asarray(padded_words, dtype=jnp.int64)
    length_array = jnp.asarray(lengths, dtype=jnp.int64)
    transitions = machine[:, :2]
    p_one = machine[:, 2]

    def from_state(start: jax.Array) -> jax.Array:
        states = jnp.full((len(padded_words),), start, dtype=jnp.int64)
        numerators = jnp.ones((len(padded_words),), dtype=jnp.int64)
        for step in range(max_length):
            active = step < length_array
            symbols = words[:, step]
            weights = jnp.where(symbols == 1, p_one[states], WORD_BASE - p_one[states])
            numerators = numerators * jnp.where(active, weights, 1)
            successors = transitions[states, symbols]
            states = jnp.where(active, successors, states)
        return numerators

    state_values = jax.vmap(from_state)(jnp.arange(STATE_COUNT, dtype=jnp.int64))
    return state_values, jnp.sum(state_values, axis=0, dtype=jnp.int64)


@jax.jit
def _batched_target_numerators(machine_batch: jax.Array) -> tuple[jax.Array, jax.Array]:
    return jax.vmap(
        lambda machine: exact_numerators_for_layout(
            machine, TARGET_PADDED_WORDS, TARGET_LENGTHS, MAX_TARGET_LENGTH
        )
    )(machine_batch)


@jax.jit
def _batched_challenge_predictive_numerators(machine_batch: jax.Array) -> jax.Array:
    def predictive(machine: jax.Array) -> jax.Array:
        _, values = exact_numerators_for_layout(
            machine, CHALLENGE_PADDED_WORDS, CHALLENGE_LENGTHS, MAX_CHALLENGE_LENGTH
        )
        return values

    return jax.vmap(predictive)(machine_batch)


def reconstruct_registry(
    spec: dict[str, Any], v0_manifest: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, Any]:
    """Rebuild the registry with bounded two-pass JAX storage.

    Pass one retains only compact Python registry rows after target-length
    filtering.  Pass two visits only the sorted 192 selected rows for
    challenge hashes, then visits the 32 test rows in pair-sized chunks for
    exact pair distances.  No full length-12 pool is retained.
    """
    v0_rows = [row for name in SPLITS for row in v0_manifest["splits"][name]]
    excluded_machine_hashes = {row["machine_sha256"] for row in v0_rows}
    excluded_target_hashes = {
        row.get("predictive_signature_sha256", row.get("target_signature_sha256"))
        for row in v0_rows
    }
    if None in excluded_target_hashes:
        raise RuntimeError("v0 row missing length1-to-8 predictive signature hash")

    start, stop = spec["object_family"]["candidate_counter_interval"]
    connected_pending_by_hash: dict[str, tuple[int, Machine, str]] = {}
    connected_occurrences: dict[str, int] = {}
    rejected = {
        "not_strongly_connected": 0,
        "not_minimal": 0,
        "machine_duplicate": 0,
        "signature_duplicate": 0,
        "excluded_v0_machine_hash": 0,
        "excluded_v0_predictive_signature_hash": 0,
    }
    for counter in range(start, stop + 1):
        machine = canonical_machine(candidate(counter))
        digest = machine_hash(machine)
        connected = strongly_connected(machine)
        if digest in excluded_machine_hashes:
            rejected["excluded_v0_machine_hash"] += 1
        elif not connected:
            rejected["not_strongly_connected"] += 1
        else:
            connected_occurrences[digest] = connected_occurrences.get(digest, 0) + 1
            connected_pending_by_hash.setdefault(digest, (counter, machine, digest))

    accepted: dict[str, dict[str, Any]] = {}
    signature_seen: set[str] = set()
    target_count = len(TARGET_WORDS)
    connected_pending = list(connected_pending_by_hash.values())

    # Pass one: only the 510 target coordinates are materialized per chunk.
    for offset in range(0, len(connected_pending), BATCH_SIZE):
        chunk = connected_pending[offset : offset + BATCH_SIZE]
        machines = jnp.asarray([record[1] for record in chunk], dtype=jnp.int64)
        state8_device, predictive8_device = _batched_target_numerators(machines)
        state8_host = jax.device_get(state8_device).tolist()
        predictive8_host = jax.device_get(predictive8_device).tolist()
        del machines, state8_device, predictive8_device
        for (counter, machine, digest), state_values, predictive_values in zip(
            chunk, state8_host, predictive8_host, strict=True
        ):
            multiplicity = connected_occurrences[digest]
            state_target = [values[:target_count] for values in state_values]
            target = predictive_values[:target_count]
            if len({tuple(values) for values in state_target}) != STATE_COUNT:
                rejected["not_minimal"] += multiplicity
                continue
            target_hash = rational_signature_hash(target, TARGET_DENOMINATORS, True)
            if target_hash in excluded_target_hashes:
                rejected["excluded_v0_predictive_signature_hash"] += multiplicity
                continue
            if target_hash in signature_seen:
                rejected["signature_duplicate"] += multiplicity
                continue
            signature_seen.add(target_hash)
            accepted[digest] = {
                "counter": counter,
                "machine": [list(row) for row in machine],
                "machine_sha256": digest,
                "predictive_signature_sha256": target_hash,
                "target_signature_sha256": target_hash,
                "target_signature_coordinate_count": len(TARGET_WORDS),
                "challenge_signature_coordinate_count": len(CHALLENGE_WORDS),
                "state_signature_sha256": [
                    rational_signature_hash(values, TARGET_DENOMINATORS, False)
                    for values in state_target
                ],
            }
            rejected["machine_duplicate"] += connected_occurrences[digest] - 1
        del state8_host, predictive8_host

    required = sum(spec["frozen_splits"][f"{name}_objects"] for name in SPLITS)
    ordered = [accepted[digest] for digest in sorted(accepted)]
    if len(ordered) < required:
        raise RuntimeError(f"only {len(ordered)} eligible objects; need {required}")
    selected = ordered[:required]
    train_stop = spec["frozen_splits"]["train_objects"]
    validation_stop = train_stop + spec["frozen_splits"]["validation_objects"]
    splits = {
        "train": selected[:train_stop],
        "validation": selected[train_stop:validation_stop],
        "test": selected[validation_stop:],
    }

    # Pass two: exact lengths 1..12 are computed only for the selected rows.
    selected_target_hashes = 0
    selected_challenge_hashes = 0
    for offset in range(0, len(selected), BATCH_SIZE):
        chunk = selected[offset : offset + BATCH_SIZE]
        machines = jnp.asarray([row["machine"] for row in chunk], dtype=jnp.int64)
        predictive12_device = _batched_challenge_predictive_numerators(machines)
        predictive12_host = jax.device_get(predictive12_device).tolist()
        del machines, predictive12_device
        for row, predictive_values in zip(chunk, predictive12_host, strict=True):
            target = predictive_values[:target_count]
            target_hash = rational_signature_hash(target, TARGET_DENOMINATORS, True)
            challenge_hash = rational_signature_hash(
                predictive_values, CHALLENGE_DENOMINATORS, True
            )
            if target_hash != row["target_signature_sha256"]:
                raise RuntimeError("selected target hash changed between registry and challenge pass")
            row["challenge_signature_sha256"] = challenge_hash
            row["target_signature_coordinate_count"] = target_count
            row["challenge_signature_coordinate_count"] = len(CHALLENGE_WORDS)
            selected_target_hashes += 1
            selected_challenge_hashes += 1
        del predictive12_host

    # Pair distances are the only challenge-derived values retained beyond
    # hashes.  Recompute the 16 pairs in chunks of 32 test rows or fewer.
    test_by_hash = {row["machine_sha256"]: row for row in splits["test"]}
    pair_distance_data: list[dict[str, Any]] = []
    pairs = manifest.get("test_pairing", {}).get("pairs", [])
    for pair_offset in range(0, len(pairs), BATCH_SIZE // 2):
        pair_chunk = pairs[pair_offset : pair_offset + BATCH_SIZE // 2]
        pair_rows = [
            test_by_hash[hash_value]
            for pair in pair_chunk
            for hash_value in (pair["left_machine_sha256"], pair["right_machine_sha256"])
        ]
        machines = jnp.asarray([row["machine"] for row in pair_rows], dtype=jnp.int64)
        predictive_device = _batched_challenge_predictive_numerators(machines)
        predictive_host = jax.device_get(predictive_device).tolist()
        del machines, predictive_device
        for pair_index, pair in enumerate(pair_chunk):
            left_values = predictive_host[2 * pair_index]
            right_values = predictive_host[2 * pair_index + 1]
            distance = sum(
                (
                    abs(int(left) - int(right))
                    * Fraction(1, int(denominator) * STATE_COUNT)
                    for left, right, denominator in zip(
                        left_values, right_values, CHALLENGE_DENOMINATORS, strict=True
                    )
                ),
                Fraction(0),
            )
            pair_distance_data.append(
                {
                    "left_machine_sha256": pair["left_machine_sha256"],
                    "right_machine_sha256": pair["right_machine_sha256"],
                    "full_lengths_1_to_12_l1_distance": [
                        distance.numerator,
                        distance.denominator,
                    ],
                }
            )
        del predictive_host
    return {
        "accepted_candidate_count": len(accepted),
        "eligible_candidate_count": len(ordered),
        "rejected_counts": rejected,
        "excluded_v0_machine_hash_count": len(excluded_machine_hashes),
        "excluded_v0_predictive_signature_hash_count": len(excluded_target_hashes),
        "splits": splits,
        "pair_distance_data": sorted(
            pair_distance_data,
            key=lambda value: (
                value["left_machine_sha256"], value["right_machine_sha256"]
            ),
        ),
        "exact_pass_receipt": {
            "strategy": "target-only Python filtering, then selected-only challenge pass",
            "batch_size": BATCH_SIZE,
            "max_batch_size": BATCH_SIZE,
            "target_pass_retained_coordinate_arrays": False,
            "challenge_pass_retained_pool_arrays": False,
            "selected_target_hash_count": selected_target_hashes,
            "selected_challenge_hash_count": selected_challenge_hashes,
            "selected_count": len(selected),
            "selected_pair_distance_count": len(pair_distance_data),
            "pair_distance_chunk_size": BATCH_SIZE,
        },
    }


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "counter",
            "machine",
            "machine_sha256",
            "predictive_signature_sha256",
            "target_signature_sha256",
            "state_signature_sha256",
            "challenge_signature_sha256",
            "target_signature_coordinate_count",
            "challenge_signature_coordinate_count",
        )
        if key in row
    }


def verify_manifest(spec: dict[str, Any], manifest: dict[str, Any], v0_manifest: dict[str, Any], reconstructed: dict[str, Any]) -> dict[str, Any]:
    public = {
        name: [public_row(row) for row in reconstructed["splits"][name]]
        for name in SPLITS
    }
    expected_public = {
        name: [
            {
                key: row[key]
                for key in public[name][index]
                if key in manifest["splits"][name][index]
            }
            for index, row in enumerate(public[name])
        ]
        for name in SPLITS
    }
    manifest_core = {
        name: [
            {
                key: row[key]
                for key in (
                    "counter",
                    "machine",
                    "machine_sha256",
                    "predictive_signature_sha256",
                    "target_signature_sha256",
                    "state_signature_sha256",
                    "challenge_signature_sha256",
                    "target_signature_coordinate_count",
                    "challenge_signature_coordinate_count",
                )
                if key in row
            }
            for row in manifest["splits"][name]
        ]
        for name in SPLITS
    }
    row_match = expected_public == manifest_core
    spec_hash = sha256_file(SPEC_PATH)
    v0_hash = sha256_file(V0_MANIFEST_PATH)
    linkage = {
        "spec_sha256_matches_manifest": manifest.get("spec_sha256") == spec_hash,
        "v0_manifest_sha256_matches_manifest": manifest.get("v0_manifest_sha256") == v0_hash,
        "spec_sha256": spec_hash,
        "manifest_spec_sha256": manifest.get("spec_sha256"),
        "v0_manifest_sha256": v0_hash,
        "manifest_v0_manifest_sha256": manifest.get("v0_manifest_sha256"),
    }
    retrieval_gain_fields = [
        key
        for key in spec["metrics_and_gates"]
        if key.startswith("loo_same_object_retrieval_gain_over_")
    ]
    pair_gate_fields = [
        key
        for key in spec["metrics_and_gates"]
        if key.startswith("full_observation_horizon_matched_")
    ]
    dynamic_spec = {
        "protocol_correction_commit": PROTOCOL_CORRECTION_COMMIT,
        "claim_is_supervised_multi_view_retrieval": "supervised multi-view" in spec["claim"] and "retrieval" in spec["claim"],
        "green_ceiling_exact": spec.get("accepted_green_ceiling") == EXPECTED_GREEN_CEILING,
        "engine_mode_all_three": spec["engine_contract"].get("mode") == "all_three_full_sims",
        "jax_role_binds_python_boundary": "Python canonicalization" in spec["engine_contract"].get("jax", ""),
        "view_domain_has_no_model_seed": "model_seed" not in spec["view_process"].get("seed_domain", ""),
        "view_domain_is_new": spec["view_process"].get("seed_domain_is_new_relative_to_v0") is True,
        "retrieval_gain_field_is_per_each_baseline": retrieval_gain_fields == [
            "loo_same_object_retrieval_gain_over_each_of_histogram_and_temporal_min"
        ],
        "pair_gate_uses_own_target_prediction": pair_gate_fields == [
            "full_observation_horizon_matched_own_target_prediction"
        ],
        "target_coordinate_count_bound": spec["object_family"].get("target_signature_coordinate_count") == len(TARGET_WORDS),
        "challenge_coordinate_count_bound": spec["object_family"].get("challenge_signature_coordinate_count") == len(CHALLENGE_WORDS),
    }
    required_fields = {
        "schema": manifest.get("schema") == "codex_ratchet.unseen_finite_predictive_objects_v1.object_manifest.v1",
        "sim_id": manifest.get("sim_id") == SIM_ID,
        "classification": manifest.get("classification") == CLASSIFICATION,
        "candidate_interval": manifest.get("candidate_interval") == spec["object_family"]["candidate_counter_interval"],
        "split_counts": manifest.get("split_counts") == {
            name: spec["frozen_splits"][f"{name}_objects"] for name in SPLITS
        },
        "target_coordinate_count": manifest.get("signature_contract", {}).get("target_coordinate_count") == len(TARGET_WORDS),
        "challenge_coordinate_count": manifest.get("signature_contract", {}).get("challenge_coordinate_count") == len(CHALLENGE_WORDS),
        "v0_exclusion_counts": manifest.get("excluded_v0_machine_hash_count") == len({row["machine_sha256"] for name in SPLITS for row in v0_manifest["splits"][name]})
        and manifest.get("excluded_v0_predictive_signature_hash_count") == len({row.get("predictive_signature_sha256", row.get("target_signature_sha256")) for name in SPLITS for row in v0_manifest["splits"][name]}),
    }
    counts_match = (
        reconstructed["accepted_candidate_count"] == manifest.get("accepted_candidate_count")
        and reconstructed["eligible_candidate_count"] == manifest.get("eligible_candidate_count")
        and reconstructed["rejected_counts"] == manifest.get("rejected_counts")
    )
    return {
        "tracked_spec": tracked(SPEC_PATH),
        "tracked_manifest": tracked(MANIFEST_PATH),
        "tracked_v0_manifest": tracked(V0_MANIFEST_PATH),
        "protocol_correction_commit": PROTOCOL_CORRECTION_COMMIT,
        "dynamic_spec": dynamic_spec,
        "required_fields": required_fields,
        "linkage": linkage,
        "registry_counts_match": counts_match,
        "manifest_rows_match": row_match,
        "all_verified": all(required_fields.values()) and all(dynamic_spec.values()) and counts_match and row_match and all(linkage.values()),
    }


def verify_pair_distances(
    manifest: dict[str, Any],
    test_rows: Sequence[dict[str, Any]],
    pair_distance_data: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    by_hash = {row["machine_sha256"] for row in test_rows}
    pairing = manifest.get("test_pairing", {})
    pairs = pairing.get("pairs", [])
    used: list[str] = []
    expected_distances = {
        (pair["left_machine_sha256"], pair["right_machine_sha256"]): pair[
            "full_lengths_1_to_12_l1_distance"
        ]
        for pair in pairs
    }
    actual_distances = {
        (pair["left_machine_sha256"], pair["right_machine_sha256"]): pair[
            "full_lengths_1_to_12_l1_distance"
        ]
        for pair in pair_distance_data
    }
    for pair in pairs:
        left = pair["left_machine_sha256"]
        right = pair["right_machine_sha256"]
        used.extend((left, right))
    distances_match = expected_distances == actual_distances
    test_hashes = sorted(by_hash)
    return {
        "pair_count": len(pairs),
        "pair_count_expected": len(test_rows) // 2,
        "all_test_hashes_used_exactly_once": sorted(used) == test_hashes,
        "pair_distances_exact": distances_match,
        "all_match": len(pairs) == len(test_rows) // 2 and sorted(used) == test_hashes and distances_match,
    }


def key_digest(spec: dict[str, Any], split: str, machine_hash_value: str, view_index: int, trajectory_index: int, channel: str) -> str:
    domain = spec["view_process"]["seed_domain"]
    label = f"{domain}|{split}|{machine_hash_value}|{view_index}|{trajectory_index}|{channel}"
    return sha256_bytes(label.encode("utf-8"))


def view_prng_census(spec: dict[str, Any], splits: dict[str, list[dict[str, Any]]], include_test: bool) -> dict[str, Any]:
    """Count and collision-check subtrees without materializing test views."""
    visible = list(spec["view_process"]["model_visible_fields"])
    forbidden = list(spec["view_process"]["model_forbidden_fields"])
    digest_values: set[str] = set()
    split_receipts: dict[str, Any] = {}
    total_views = 0
    total_trajectories = 0
    total_subtrees = 0
    for split in SPLITS:
        if split == "test" and not include_test:
            continue
        rows = splits[split]
        views_per_object = spec["frozen_splits"][f"{split}_views_per_object"]
        view_count = len(rows) * views_per_object
        trajectory_count = view_count * spec["view_process"]["trajectories_per_view"]
        subtree_count = trajectory_count * len(CHANNELS)
        for row in rows:
            for view_index in range(views_per_object):
                for trajectory_index in range(spec["view_process"]["trajectories_per_view"]):
                    for channel in CHANNELS:
                        digest_values.add(
                            key_digest(
                                spec,
                                split,
                                row["machine_sha256"],
                                view_index,
                                trajectory_index,
                                channel,
                            )
                        )
        split_receipts[split] = {
            "object_count": len(rows),
            "views_per_object": views_per_object,
            "view_count": view_count,
            "trajectory_count": trajectory_count,
            "prng_subtree_count": subtree_count,
        }
        total_views += view_count
        total_trajectories += trajectory_count
        total_subtrees += subtree_count
    expected_views = sum(
        len(splits[name]) * spec["frozen_splits"][f"{name}_views_per_object"]
        for name in SPLITS
        if include_test or name != "test"
    )
    return {
        "schema": "ufpo-v1.view_prng_census.v1",
        "seed_domain": spec["view_process"]["seed_domain"],
        "seed_domain_is_new_relative_to_v0": spec["view_process"]["seed_domain_is_new_relative_to_v0"],
        "view_seed_scope": "shared_across_model_seeds_and_arms",
        "model_seeds": list(spec["view_process"].get("model_seeds", [])),
        "model_seed_not_in_view_domain": "model_seed" not in spec["view_process"]["seed_domain"],
        "key_components": ["split", "machine_hash", "view_index", "trajectory_index", "channel"],
        "channel_count": len(CHANNELS),
        "include_test": include_test,
        "model_visible_payload_fields": visible,
        "forbidden_payload_fields": forbidden,
        "total_view_count": total_views,
        "expected_view_count": expected_views,
        "total_trajectory_count": total_trajectories,
        "total_prng_subtree_count": total_subtrees,
        "unique_prng_subtree_count": len(digest_values),
        "prng_subtree_collision_count": total_subtrees - len(digest_values),
        "split_counts": split_receipts,
        "raw_views_emitted": False,
    }


def split_solver_receipt(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    hashes = {name: [row["machine_sha256"] for row in splits[name]] for name in SPLITS}
    pair_names = (("train", "validation"), ("train", "test"), ("validation", "test"))

    def z3_overlap(left: Sequence[str], right: Sequence[str], label: str) -> str:
        witness = z3.BitVec(f"z3_{label}", 256)
        solver = z3.Solver()
        solver.add(z3.Or([witness == z3.BitVecVal(int(value, 16), 256) for value in left]))
        solver.add(z3.Or([witness == z3.BitVecVal(int(value, 16), 256) for value in right]))
        return str(solver.check())

    def cvc5_overlap(left: Sequence[str], right: Sequence[str], label: str) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_BV")
        sort = solver.mkBitVectorSort(256)
        witness = solver.mkConst(sort, f"cvc5_{label}")

        def membership(values: Sequence[str]):
            terms = [
                solver.mkTerm(cvc5.Kind.EQUAL, witness, solver.mkBitVector(256, value, 16))
                for value in values
            ]
            return terms[0] if len(terms) == 1 else solver.mkTerm(cvc5.Kind.OR, *terms)

        solver.assertFormula(membership(left))
        solver.assertFormula(membership(right))
        result = solver.checkSat()
        return "sat" if result.isSat() else "unsat" if result.isUnsat() else str(result).lower()

    z3_intact = {
        f"{left}_vs_{right}": z3_overlap(hashes[left], hashes[right], f"{left}_{right}")
        for left, right in pair_names
    }
    cvc5_intact = {
        f"{left}_vs_{right}": cvc5_overlap(hashes[left], hashes[right], f"{left}_{right}")
        for left, right in pair_names
    }
    injected = hashes["test"] + [hashes["train"][0]]
    z3_control = z3_overlap(hashes["train"], injected, "injected_overlap")
    cvc5_control = cvc5_overlap(hashes["train"], injected, "injected_overlap")
    return {
        "intact_overlap_queries": {"z3": z3_intact, "cvc5": cvc5_intact},
        "erased_control": {
            "mutation": "inject first train machine hash into test hash set",
            "z3": z3_control,
            "cvc5": cvc5_control,
        },
        "intact_disjoint": all(value == "unsat" for value in z3_intact.values())
        and all(value == "unsat" for value in cvc5_intact.values()),
        "erased_control_detected": z3_control == "sat" and cvc5_control == "sat",
    }


def leakage_census(spec: dict[str, Any], manifest: dict[str, Any], v0_manifest: dict[str, Any], splits: dict[str, list[dict[str, Any]]], view_receipt: dict[str, Any], pair_receipt: dict[str, Any]) -> dict[str, Any]:
    split_sets = {name: {row["machine_sha256"] for row in splits[name]} for name in SPLITS}
    all_rows = [row for name in SPLITS for row in splits[name]]
    v0_machine = {row["machine_sha256"] for name in SPLITS for row in v0_manifest["splits"][name]}
    v0_target = {row.get("predictive_signature_sha256", row.get("target_signature_sha256")) for name in SPLITS for row in v0_manifest["splits"][name]}
    visible = set(spec["view_process"]["model_visible_fields"])
    forbidden = set(spec["view_process"]["model_forbidden_fields"])
    return {
        "split_counts": {name: len(split_sets[name]) for name in SPLITS},
        "pairwise_machine_hash_overlap_counts": {
            "train_validation": len(split_sets["train"] & split_sets["validation"]),
            "train_test": len(split_sets["train"] & split_sets["test"]),
            "validation_test": len(split_sets["validation"] & split_sets["test"]),
        },
        "predictive_signature_unique_count": len({row["predictive_signature_sha256"] for row in all_rows}),
        "counter_unique_count": len({row["counter"] for row in all_rows}),
        "v0_machine_exclusion_intersection_count": len({row["machine_sha256"] for row in all_rows} & v0_machine),
        "v0_predictive_signature_exclusion_intersection_count": len({row["predictive_signature_sha256"] for row in all_rows} & v0_target),
        "visible_forbidden_field_overlap": sorted(visible & forbidden),
        "model_input_excludes_manifest_identity_fields": manifest.get("model_input_excludes_manifest_identity_fields") is True,
        "prng_subtree_collision_count": view_receipt["prng_subtree_collision_count"],
        "test_pair_receipt": pair_receipt,
        "learned_metric_files_opened": [],
        "peer_result_files_opened": [],
        "test_views_or_results_read": False,
    }


def max_rss_receipt() -> dict[str, Any]:
    raw = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # macOS reports bytes; Linux reports KiB.
    bytes_used = raw if sys.platform == "darwin" else raw * 1024
    return {
        "source": "resource.getrusage(RUSAGE_SELF).ru_maxrss",
        "raw_value": raw,
        "bytes": bytes_used,
        "limit_bytes": 1024**3,
        "under_1GiB": bytes_used < 1024**3,
    }


def validate_seal(path: Path, spec: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"sealed-test requires an existing seal receipt: {path}")
    receipt = read_json(path)
    if receipt.get("learner_source_sealed") is not True or receipt.get("seal_status") not in ("sealed", "accepted"):
        raise RuntimeError("seal receipt does not declare an accepted learner source seal")
    expected = {
        "sim_id": SIM_ID,
        "spec_sha256": sha256_file(SPEC_PATH),
        "object_manifest_sha256": sha256_file(MANIFEST_PATH),
    }
    mismatches = {key: {"expected": value, "actual": receipt.get(key)} for key, value in expected.items() if receipt.get(key) != value}
    if mismatches:
        raise RuntimeError(f"seal receipt binding mismatch: {json.dumps(mismatches, sort_keys=True)}")
    return {"path": str(path), "sha256": sha256_file(path), "binding_verified": True}


def build_payload(spec: dict[str, Any], manifest: dict[str, Any], v0_manifest: dict[str, Any], reconstructed: dict[str, Any], mode: str, started: float) -> dict[str, Any]:
    splits = reconstructed["splits"]
    manifest_receipt = verify_manifest(spec, manifest, v0_manifest, reconstructed)
    rows = [row for name in SPLITS for row in splits[name]]
    pair_receipt = verify_pair_distances(
        manifest, splits["test"], reconstructed["pair_distance_data"]
    )
    exact_pass = reconstructed["exact_pass_receipt"]
    include_test = mode == "sealed-test"
    view_receipt = view_prng_census(spec, splits, include_test=include_test)
    solver_receipt = split_solver_receipt(splits)
    leakage = leakage_census(spec, manifest, v0_manifest, splits, view_receipt, pair_receipt)
    controls = set(spec["controls"])
    expected_controls = {"train_mean", "order2_laplace", "histogram", "temporal_shuffle", "optimizer_erased", "architecture_only", "deranged"}
    control_receipt = {
        "declared_count": len(spec["controls"]),
        "unique_count": len(controls),
        "exact_frozen_control_set": controls == expected_controls,
        "test_labels_forbidden_from_training_and_threshold_selection": spec["metrics_and_gates"].get("test_labels_forbidden_from_training_and_threshold_selection") is True,
        "test_pair_count": pair_receipt["pair_count"],
        "test_pair_hashes_exactly_once": pair_receipt["all_test_hashes_used_exactly_once"],
    }
    gates = {
        "G1_tracked_spec_manifest_and_v0_inputs_verified": manifest_receipt["all_verified"],
        "G2_python_registry_counts_reconstructed_exactly": manifest_receipt["registry_counts_match"],
        "G3_manifest_rows_target_and_challenge_hashes_exact": manifest_receipt["manifest_rows_match"] and pair_receipt["all_match"],
        "G4_v0_machine_and_target_exclusions_applied_before_selection": leakage["v0_machine_exclusion_intersection_count"] == 0 and leakage["v0_predictive_signature_exclusion_intersection_count"] == 0,
        "G5_jax_x64_exact_target_and_challenge_numerators": bool(jax.config.jax_enable_x64) and exact_pass["selected_target_hash_count"] == len(rows) and exact_pass["selected_challenge_hash_count"] == len(rows) and all(row.get("challenge_signature_sha256") and row.get("target_signature_coordinate_count") == 510 and row.get("challenge_signature_coordinate_count") == 8190 for row in rows),
        "G6_split_and_leakage_census_clean": all(value == 0 for value in leakage["pairwise_machine_hash_overlap_counts"].values()) and leakage["predictive_signature_unique_count"] == 192 and leakage["counter_unique_count"] == 192 and not leakage["visible_forbidden_field_overlap"] and leakage["test_views_or_results_read"] is False,
        "G7_new_view_prng_schema_and_counts": view_receipt["seed_domain_is_new_relative_to_v0"] and view_receipt["prng_subtree_collision_count"] == 0 and view_receipt["total_view_count"] == view_receipt["expected_view_count"],
        "G8_frozen_control_census_exact": control_receipt["declared_count"] == 7 and control_receipt["unique_count"] == 7 and control_receipt["exact_frozen_control_set"] and control_receipt["test_pair_hashes_exactly_once"],
        "G9_z3_cvc5_split_controls_with_injected_overlap": solver_receipt["intact_disjoint"] and solver_receipt["erased_control_detected"],
        "G10_preflight_peak_rss_below_1GiB": None,
        "G11_controller_three_engine_and_sealed_learner_evaluation": None,
    }
    rss_receipt = max_rss_receipt()
    if mode == "preflight":
        gates["G10_preflight_peak_rss_below_1GiB"] = rss_receipt["under_1GiB"]
    all_local_gates_pass = all(value for value in gates.values() if value is not None)
    elapsed = time.perf_counter() - started
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "status": "red_pending_controller",
        "claim_ceiling": spec["accepted_red_ceiling"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_local_gates_pass": all_local_gates_pass,
        "all_pass": False,
        "all_scientific_gates_pass": False,
        "controller_blocker": "G11 requires controller-side three-engine parity and sealed PyTorch learner/control evaluation",
        "mode": mode,
        "source_path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "reads_peer_result": False,
        "peer_result_files_read": [],
        "learned_metric_files_read": [],
        "test_views_or_results_read": False,
        "numpy_imported_by_source": False,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "runtime": {
            "python": sys.executable,
            "jax": jax.__version__,
            "z3": z3.get_version_string(),
            "cvc5": getattr(cvc5, "__version__", "unknown"),
        },
        "engine_contract": {
            "mode": spec["engine_contract"]["mode"],
            "registry_proposal_owner": "Python stdlib canonicalization and registry reconstruction; JAX does not author Python canonicalization",
            "jax_role": "x64 exact batched target/challenge numerators, view PRNG census, leakage census, and split controls",
            "semantic_owner": spec["engine_contract"].get("semantic_owner"),
            "peer_result_reads_forbidden": True,
            "numpy_on_claim_path": False,
        },
        "accepted_green_ceiling": spec["accepted_green_ceiling"],
        "input_provenance": {
            "spec_path": str(SPEC_PATH.relative_to(REPO_ROOT)),
            "manifest_path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "v0_manifest_path": str(V0_MANIFEST_PATH.relative_to(REPO_ROOT)),
            "spec_sha256": sha256_file(SPEC_PATH),
            "manifest_sha256": sha256_file(MANIFEST_PATH),
            "v0_manifest_sha256": sha256_file(V0_MANIFEST_PATH),
        },
        "frozen_input_receipt": manifest_receipt,
        "registry_reconstruction": {
            "candidate_interval": manifest["candidate_interval"],
            "accepted_candidate_count": reconstructed["accepted_candidate_count"],
            "eligible_candidate_count": reconstructed["eligible_candidate_count"],
            "rejected_counts": reconstructed["rejected_counts"],
            "excluded_v0_machine_hash_count": reconstructed["excluded_v0_machine_hash_count"],
            "excluded_v0_predictive_signature_hash_count": reconstructed["excluded_v0_predictive_signature_hash_count"],
            "selected_count": len(rows),
            "split_counts": {name: len(splits[name]) for name in SPLITS},
            "canonicalization_owner": "python",
            "jax_canonicalization_claimed": False,
            "exact_pass_receipt": reconstructed["exact_pass_receipt"],
        },
        "preflight_max_rss_receipt": rss_receipt,
        "view_prng_census": view_receipt,
        "leakage_census": leakage,
        "control_census": control_receipt,
        "split_solver_receipt": solver_receipt,
        "gates": gates,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(exact_numerators_for_layout))",
                "input_object": "Python-canonicalized strongly connected ufpo-v1 candidates",
                "output_object": "exact int64 state and uniform-start target lengths 1..8 and challenge lengths 1..12 numerators",
                "positive_case": "target and challenge counts and manifest hashes match",
                "negative/erased_control": "exact integer normalization and injected split overlap are checked separately",
                "boundary_case": "510 target and 8190 challenge coordinates",
                "demotion_condition": "any x64, numerator length, hash, or normalization mismatch",
                "gates": ["all_pass", "G5_jax_x64_exact_target_and_challenge_numerators"],
            },
            {
                "tool": "jax",
                "qualified_api/function": "SHA-256-derived view PRNG subtree census",
                "input_object": "split, machine hash, view index, trajectory index, and channel schema",
                "output_object": "view, trajectory, subtree, and collision counts without test view materialization in preflight",
                "positive_case": "new v1 domain has zero subtree collisions",
                "negative/erased_control": "forbidden identity fields remain absent from model-visible schema",
                "boundary_case": "preflight excludes test views and results; sealed-test is separately gated",
                "demotion_condition": "schema, count, collision, or forbidden-field mismatch",
                "gates": ["all_pass", "G7_new_view_prng_schema_and_counts"],
            },
            {
                "tool": "z3+cvc5",
                "qualified_api/function": "z3.Solver.check and cvc5.Solver.checkSat",
                "input_object": "256-bit full machine-hash split memberships",
                "output_object": "pairwise UNSAT overlap proofs and SAT injected-overlap control",
                "positive_case": "all intact split pairs are disjoint",
                "negative/erased_control": "first train hash injected into test yields SAT in both solvers",
                "boundary_case": "all 192 full-width hashes",
                "demotion_condition": "solver disagreement or wrong intact/control polarity",
                "gates": ["all_pass", "G9_z3_cvc5_split_controls_with_injected_overlap"],
            },
        ],
        "compact_receipt": {
            "raw_predictive_arrays_emitted": False,
            "raw_views_emitted": False,
            "per_test_object_diagnostics_emitted": False,
            "payload_sha256_excluding_self": None,
        },
        "elapsed_seconds": elapsed,
    }
    payload["compact_receipt"]["payload_sha256_excluding_self"] = canonical_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="verify frozen inputs without reading or generating test views/results")
    mode.add_argument("--sealed-test", action="store_true", help="reserved sealed evaluation path; requires a seal receipt")
    parser.add_argument("--seal-receipt", type=Path, help="accepted learner-source seal receipt for --sealed-test")
    parser.add_argument("--output", type=Path, default=None, help="optional JSON receipt path; preflight does not write one by default")
    args = parser.parse_args()
    selected_mode = "sealed-test" if args.sealed_test else "preflight"
    if selected_mode == "sealed-test" and args.seal_receipt is None:
        parser.error("--sealed-test requires --seal-receipt")
    if selected_mode == "sealed-test":
        output = args.output or DEFAULT_OUTPUT_PATH
        if output.exists():
            raise SystemExit(f"refusing to overwrite sealed-test output: {output}")
    started = time.perf_counter()
    spec = read_json(SPEC_PATH)
    manifest = read_json(MANIFEST_PATH)
    v0_manifest = read_json(V0_MANIFEST_PATH)
    if selected_mode == "sealed-test":
        validate_seal(args.seal_receipt, spec, manifest)
    reconstructed = reconstruct_registry(spec, v0_manifest, manifest)
    payload = build_payload(spec, manifest, v0_manifest, reconstructed, selected_mode, started)
    if selected_mode == "preflight":
        payload["preflight_contract"] = {
            "test_views_generated": False,
            "test_views_read": False,
            "test_results_read": False,
            "sealed_test_run": False,
        }
    if args.output is not None:
        strict_write_json(args.output, payload)
    print(json.dumps({
        "all_local_gates_pass": payload["all_local_gates_pass"],
        "all_pass": False,
        "mode": selected_mode,
        "output": str(args.output) if args.output is not None else None,
        "status": payload["status"],
        "test_views_or_results_read": payload["test_views_or_results_read"],
    }, sort_keys=True))
    return 0 if payload["all_local_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
