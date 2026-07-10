#!/usr/bin/env python3
"""Independent JAX exhaustive builder for the frozen UFPO-v0 registry.

The claim path uses JAX x64 plus exact integer numerators.  It does not import
the manifest generator, NumPy, peer-engine receipts, or learned metric files.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from jax import config

config.update("jax_enable_x64", True)

import cvc5
import jax
import jax.numpy as jnp
import z3


SIM_ID = "unseen_finite_predictive_objects_v0"
SCHEMA = "codex_ratchet.unseen_finite_predictive_objects_v0.jax_result.v1"
CLASSIFICATION = "scratch_diagnostic"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"
TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 batched exact-numerator reconstruction and lossy-view census",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing split-disjointness proof with an injected-overlap control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent split-disjointness proof with the same control polarity",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}
PREREGISTRATION_COMMIT = "44d733e484b8fd767c2ab40612f0cb8ba5b355ce"
EXPECTED_PREREGISTRATION_SHA256 = (
    "5cacd6aeea11fc844449b4c48d2971d43f6307b31fda5248203a47548dd0682d"
)
SUPERSEDED_PREREGISTRATION_SHA256 = (
    "be65a924c48150a24866515fc256a3a191768d6908c287d7f3f7326a94e65e2f"
)
FROZEN_HASH_FIELDS = {
    "spec_sha256": "spec.json",
    "readme_sha256": "README.md",
    "manifest_generator_sha256": "generate_manifest.py",
    "object_manifest_sha256": "object_manifest.json",
    "wizard_v4_3_object_card_sha256": "wizard_v4_3_object_card.json",
}
ORIGINAL_FROZEN_HASHES = {
    "spec_sha256": "b8660e4b05066a6dbb733e443989bbde50a74caa3145892d0baf0a740b89536f",
    "readme_sha256": "17ac513d6faeb4e36fa4a8f7c7097f89870e5e1a0e6e4945d6d8b2e2b2c5af8f",
    "manifest_generator_sha256": "fe9649ba5c64fd87d33b0c230f3b16695c10e120c22ea78499ec9500bd5dd2a2",
    "object_manifest_sha256": "2894501dad5d689c00a2dd4ef7dc378803e5282f10f52122c064a6c028caa462",
    "wizard_v4_3_object_card_sha256": "f3728aafc779570d9379aaa91e26a92b39fb59f0e6fdfa974fe330f89f66f790",
}
STATE_COUNT = 4
MAX_WORD_LENGTH = 8
TRAJECTORIES_PER_VIEW = 8
TRAJECTORY_LENGTH = 128
ERASURE_PROBABILITY = 0.35
SUBSTITUTION_PROBABILITY = 0.10

SOURCE_PATH = Path(__file__).resolve()
SIM_DIR = SOURCE_PATH.parent
REPO_ROOT = SOURCE_PATH.parents[3]
SPEC_PATH = SIM_DIR / "spec.json"
MANIFEST_PATH = SIM_DIR / "object_manifest.json"
PREREGISTRATION_PATH = SIM_DIR / "preregistration_receipt.json"
CORRECTION_PATH = SIM_DIR / "PREREGISTRATION_CORRECTION.md"
DEFAULT_OUTPUT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"


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


def git_blob(commit: str, path: Path) -> bytes:
    relative = path.relative_to(REPO_ROOT).as_posix()
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def verify_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    preregistration_hash = sha256_file(PREREGISTRATION_PATH)
    if preregistration_hash != EXPECTED_PREREGISTRATION_SHA256:
        raise RuntimeError("preregistration receipt hash drift")
    preregistration = json.loads(PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    current_hashes: dict[str, str] = {}
    commit_tree_hashes: dict[str, str] = {}
    for field, filename in FROZEN_HASH_FIELDS.items():
        path = SIM_DIR / filename
        current_hashes[field] = sha256_file(path)
        commit_tree_hashes[field] = sha256_bytes(git_blob(PREREGISTRATION_COMMIT, path))
        if current_hashes[field] != preregistration[field]:
            raise RuntimeError(f"corrected working-tree hash drift: {field}")
        if commit_tree_hashes[field] != ORIGINAL_FROZEN_HASHES[field]:
            raise RuntimeError(f"preregistration commit hash drift: {field}")
    if (
        preregistration["superseded_preregistration_sha256"]
        != SUPERSEDED_PREREGISTRATION_SHA256
        or preregistration["original_frozen_spec_sha256"]
        != ORIGINAL_FROZEN_HASHES["spec_sha256"]
    ):
        raise RuntimeError("corrected receipt does not bind original preregistration")

    frozen_spec = json.loads(git_blob(PREREGISTRATION_COMMIT, SPEC_PATH))
    current_spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if not CORRECTION_PATH.is_file():
        raise RuntimeError("declared preregistration correction is missing")
    if sha256_file(CORRECTION_PATH) != preregistration["correction_sha256"]:
        raise RuntimeError("preregistration correction hash drift")
    corrected_view = dict(current_spec["view_process"])
    corrected_view["model_forbidden_fields"] = [
        "hard_negative_partner" if value == "short_horizon_matched_partner" else value
        for value in corrected_view["model_forbidden_fields"]
    ]
    corrected_controls = [
        "hard_negative_pairs_selected_from_exact_short_horizon_similarity_before_training"
        if value == "short_horizon_matched_test_pairs_frozen_before_training"
        else value
        for value in current_spec["controls"]
    ]
    corrected_metrics = dict(current_spec["metrics_and_gates"])
    corrected_metrics["hard_negative_own_target_preference_min"] = corrected_metrics.pop(
        "short_horizon_matched_own_target_preference_min"
    )
    preserved_sections = all(
        (
            current_spec["sim_id"] == frozen_spec["sim_id"],
            current_spec["classification"] == frozen_spec["classification"],
            current_spec["promotion_allowed"] == frozen_spec["promotion_allowed"],
            current_spec["formal_admission_allowed"] == frozen_spec["formal_admission_allowed"],
            current_spec["claim"] == frozen_spec["claim"],
            current_spec["object_family"] == frozen_spec["object_family"],
            current_spec["frozen_splits"] == frozen_spec["frozen_splits"],
            corrected_view == frozen_spec["view_process"],
            current_spec["learner"] == frozen_spec["learner"],
            corrected_controls == frozen_spec["controls"],
            corrected_metrics == frozen_spec["metrics_and_gates"],
            current_spec["accepted_green_ceiling"] == frozen_spec["accepted_green_ceiling"],
            current_spec["accepted_red_ceiling"] == frozen_spec["accepted_red_ceiling"],
            current_spec["blocked_consumers"] == frozen_spec["blocked_consumers"],
        )
    )
    corrected_engine = current_spec["engine_contract"]
    correction_linked = (
        current_spec["schema"] == "codex_ratchet.unseen_finite_predictive_objects_v0.spec.v2"
        and corrected_engine["original_frozen_spec_sha256"]
        == preregistration["original_frozen_spec_sha256"]
        and corrected_engine["correction_path"]
        == "system_v7/sims/unseen_finite_predictive_objects_v0/PREREGISTRATION_CORRECTION.md"
        and corrected_engine["mode"] == frozen_spec["engine_contract"]["mode"]
        and corrected_engine["pytorch"] == frozen_spec["engine_contract"]["pytorch"]
        and corrected_engine["peer_result_reads"]
        == frozen_spec["engine_contract"]["peer_result_reads"]
        and corrected_engine["numpy_on_claim_path"]
        == frozen_spec["engine_contract"]["numpy_on_claim_path"]
    )
    if not preserved_sections or not correction_linked:
        raise RuntimeError("current v2 spec changes frozen scientific content")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["spec_sha256"] != preregistration["original_frozen_spec_sha256"]:
        raise RuntimeError("manifest/spec hash linkage drift")
    return frozen_spec, manifest, {
        "preregistration_sha256": preregistration_hash,
        "receipt_declared_hashes": {
            field: preregistration[field] for field in FROZEN_HASH_FIELDS
        },
        "current_file_hashes": current_hashes,
        "preregistration_commit_tree_hashes": commit_tree_hashes,
        "working_tree_original_hash_matches": {
            field: current_hashes[field] == ORIGINAL_FROZEN_HASHES[field]
            for field in FROZEN_HASH_FIELDS
        },
        "correction_sha256": sha256_file(CORRECTION_PATH),
        "correction_preserves_frozen_scientific_content": preserved_sections,
        "correction_links_original_frozen_spec": correction_linked,
        "reconstruction_spec_source": f"git:{PREREGISTRATION_COMMIT}:spec.json",
        "all_verified": True,
    }


Machine = tuple[tuple[int, int, int], ...]


def candidate(counter: int) -> Machine:
    digest = hashlib.sha256(f"ufpo-v0|candidate|{counter}".encode()).digest()
    return tuple(
        (digest[state] % 4, digest[4 + state] % 4, 2 + digest[8 + state] % 5)
        for state in range(STATE_COUNT)
    )


def relabel(machine: Machine, order: tuple[int, ...]) -> Machine:
    inverse = {old: new for new, old in enumerate(order)}
    return tuple(
        (inverse[machine[old][0]], inverse[machine[old][1]], machine[old][2])
        for old in order
    )


def canonical_machine(machine: Machine) -> Machine:
    return min(relabel(machine, order) for order in itertools.permutations(range(4)))


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


WORDS: tuple[tuple[int, ...], ...] = tuple(
    word
    for length in range(1, MAX_WORD_LENGTH + 1)
    for word in itertools.product((0, 1), repeat=length)
)
WORD_LENGTHS: tuple[int, ...] = tuple(len(word) for word in WORDS)
PADDED_WORDS: tuple[tuple[int, ...], ...] = tuple(
    word + (0,) * (MAX_WORD_LENGTH - len(word)) for word in WORDS
)
DENOMINATORS: tuple[int, ...] = tuple(8**length for length in WORD_LENGTHS)


def machine_numerators(machine: jax.Array) -> tuple[jax.Array, jax.Array]:
    """Exact state and uniform-start numerators in the frozen word order."""
    words = jnp.asarray(PADDED_WORDS, dtype=jnp.int64)
    lengths = jnp.asarray(WORD_LENGTHS, dtype=jnp.int64)
    transitions = machine[:, :2]
    p_one = machine[:, 2]

    def from_state(start: jax.Array) -> jax.Array:
        states = jnp.full((len(WORDS),), start, dtype=jnp.int64)
        numerators = jnp.ones((len(WORDS),), dtype=jnp.int64)
        for step in range(MAX_WORD_LENGTH):
            active = step < lengths
            symbols = words[:, step]
            weights = jnp.where(symbols == 1, p_one[states], 8 - p_one[states])
            numerators = numerators * jnp.where(active, weights, 1)
            successors = transitions[states, symbols]
            states = jnp.where(active, successors, states)
        return numerators

    state_values = jax.vmap(from_state)(jnp.arange(STATE_COUNT, dtype=jnp.int64))
    return state_values, jnp.sum(state_values, axis=0, dtype=jnp.int64)


batched_machine_numerators = jax.jit(jax.vmap(machine_numerators))


def rational_signature_hash(numerators: Sequence[int], uniform_start: bool) -> str:
    encoded: list[list[int]] = []
    for numerator, denominator in zip(numerators, DENOMINATORS, strict=True):
        full_denominator = denominator * (STATE_COUNT if uniform_start else 1)
        divisor = math.gcd(int(numerator), full_denominator)
        encoded.append([int(numerator) // divisor, full_denominator // divisor])
    return sha256_bytes(canonical_json(encoded))


def machine_hash(machine: Machine) -> str:
    return sha256_bytes(canonical_json(machine))


def reconstruct_registry(spec: dict[str, Any]) -> dict[str, Any]:
    start, stop = spec["object_family"]["candidate_counter_interval"]
    candidates: list[tuple[int, Machine, str, bool]] = []
    unique_connected: dict[str, Machine] = {}
    for counter in range(start, stop + 1):
        machine = canonical_machine(candidate(counter))
        digest = machine_hash(machine)
        connected = strongly_connected(machine)
        candidates.append((counter, machine, digest, connected))
        if connected:
            unique_connected.setdefault(digest, machine)

    ordered_hashes = list(unique_connected)
    machine_batch = jnp.asarray(
        [unique_connected[digest] for digest in ordered_hashes], dtype=jnp.int64
    )
    state_batch, predictive_batch = batched_machine_numerators(machine_batch)
    state_host = jax.device_get(state_batch).tolist()
    predictive_host = jax.device_get(predictive_batch).tolist()
    exact_by_machine = {
        digest: (state_host[index], predictive_host[index])
        for index, digest in enumerate(ordered_hashes)
    }

    accepted: dict[str, dict[str, Any]] = {}
    signature_seen: set[str] = set()
    rejected = {
        "not_strongly_connected": 0,
        "not_minimal": 0,
        "machine_duplicate": 0,
        "signature_duplicate": 0,
    }
    for counter, machine, digest, connected in candidates:
        if digest in accepted:
            rejected["machine_duplicate"] += 1
            continue
        if not connected:
            rejected["not_strongly_connected"] += 1
            continue
        state_values, predictive_values = exact_by_machine[digest]
        if len({tuple(values) for values in state_values}) != STATE_COUNT:
            rejected["not_minimal"] += 1
            continue
        predictive_hash = rational_signature_hash(predictive_values, True)
        if predictive_hash in signature_seen:
            rejected["signature_duplicate"] += 1
            continue
        signature_seen.add(predictive_hash)
        accepted[digest] = {
            "counter": counter,
            "machine": [list(row) for row in machine],
            "machine_sha256": digest,
            "predictive_signature_sha256": predictive_hash,
            "state_signature_sha256": [
                rational_signature_hash(values, False) for values in state_values
            ],
            "state_numerators": state_values,
            "predictive_numerators": predictive_values,
        }
    required = sum(
        spec["frozen_splits"][name]
        for name in ("train_objects", "validation_objects", "test_objects")
    )
    selected = [accepted[digest] for digest in sorted(accepted)[:required]]
    train_stop = spec["frozen_splits"]["train_objects"]
    validation_stop = train_stop + spec["frozen_splits"]["validation_objects"]
    splits = {
        "train": selected[:train_stop],
        "validation": selected[train_stop:validation_stop],
        "test": selected[validation_stop:],
    }
    return {
        "accepted_candidate_count": len(accepted),
        "rejected_counts": rejected,
        "splits": splits,
    }


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "counter",
            "machine",
            "machine_sha256",
            "predictive_signature_sha256",
            "state_signature_sha256",
        )
    }


def hard_negative_pairs(test_rows: Sequence[dict[str, Any]]) -> list[list[str]]:
    signatures = {
        row["machine_sha256"]: row["predictive_numerators"] for row in test_rows
    }
    remaining = [row["machine_sha256"] for row in test_rows]
    pairs: list[list[str]] = []
    while remaining:
        left = remaining.pop(0)

        def distance_key(right: str) -> tuple[int, int, str]:
            left_values = signatures[left]
            right_values = signatures[right]
            scaled_distances = [
                abs(left_values[index] - right_values[index])
                * 8 ** (MAX_WORD_LENGTH - WORD_LENGTHS[index])
                for index in range(len(WORDS))
            ]
            short = sum(scaled_distances[:6])
            long = sum(
                scaled_distances[index] for index in range(6, len(WORDS))
            )
            return short, -long, right

        right = min(remaining, key=distance_key)
        remaining.remove(right)
        pairs.append([left, right])
    return pairs


def predictive_distribution_receipt(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    numerators = jnp.asarray(
        [row["predictive_numerators"] for row in rows], dtype=jnp.int64
    )
    denominators = jnp.asarray(DENOMINATORS, dtype=jnp.float64) * STATE_COUNT
    distributions = jax.jit(lambda values: values.astype(jnp.float64) / denominators)(
        numerators
    )
    values = jax.device_get(distributions).tolist()
    normalization_errors: list[float] = []
    for row in values:
        cursor = 0
        for length in range(1, MAX_WORD_LENGTH + 1):
            width = 2**length
            normalization_errors.append(abs(sum(row[cursor : cursor + width]) - 1.0))
            cursor += width
    packed = b"".join(struct.pack(">d", value) for row in values for value in row)
    exact_normalization = all(
        sum(
            row["predictive_numerators"][
                (2**length - 2) : (2 ** (length + 1) - 2)
            ]
        )
        == STATE_COUNT * 8**length
        for row in rows
        for length in range(1, MAX_WORD_LENGTH + 1)
    )
    return {
        "object_count": len(rows),
        "coordinates_per_object": len(WORDS),
        "lengths": [1, 2, 3, 4, 5, 6, 7, 8],
        "dtype": str(distributions.dtype),
        "exact_integer_normalization": exact_normalization,
        "maximum_float64_normalization_error": max(normalization_errors),
        "float64_big_endian_sha256": sha256_bytes(packed),
    }


def key_data(label: str) -> tuple[int, int]:
    digest = hashlib.sha256(label.encode("utf-8")).digest()
    return (
        int.from_bytes(digest[:4], "big"),
        int.from_bytes(digest[4:8], "big"),
    )


def simulate_trajectory(machine: jax.Array, keys: jax.Array) -> jax.Array:
    initial_key, output_key, erasure_key, substitution_key = (
        jax.random.wrap_key_data(keys[index]) for index in range(4)
    )
    initial_state = jax.random.randint(initial_key, (), 0, STATE_COUNT)
    output_draws = jax.random.randint(
        output_key, (TRAJECTORY_LENGTH,), 0, 8, dtype=jnp.int64
    )
    erasure_draws = jax.random.uniform(
        erasure_key, (TRAJECTORY_LENGTH,), dtype=jnp.float64
    )
    substitution_draws = jax.random.uniform(
        substitution_key, (TRAJECTORY_LENGTH,), dtype=jnp.float64
    )

    def step(state: jax.Array, draws: tuple[jax.Array, ...]):
        output_draw, erasure_draw, substitution_draw = draws
        original = output_draw < machine[state, 2]
        erased = erasure_draw < ERASURE_PROBABILITY
        substituted = (~erased) & (substitution_draw < SUBSTITUTION_PROBABILITY)
        corrupted = jnp.logical_xor(original, substituted)
        next_state = machine[state, original.astype(jnp.int64)]
        counts = jnp.asarray(
            [original, ~erased, corrupted & ~erased, erased, substituted],
            dtype=jnp.int64,
        )
        return next_state, counts

    _, counts = jax.lax.scan(
        step,
        initial_state,
        (output_draws, erasure_draws, substitution_draws),
    )
    return jnp.sum(counts, axis=0, dtype=jnp.int64)


simulate_view = jax.vmap(simulate_trajectory, in_axes=(None, 0))
simulate_views = jax.jit(jax.vmap(simulate_view, in_axes=(0, 0)))


def expected_original_ones(machine: jax.Array) -> jax.Array:
    distribution = jnp.full((STATE_COUNT,), 0.25, dtype=jnp.float64)
    total = jnp.asarray(0.0, dtype=jnp.float64)
    for _ in range(TRAJECTORY_LENGTH):
        p_one = machine[:, 2].astype(jnp.float64) / 8.0
        total = total + jnp.sum(distribution * p_one)
        next_distribution = jnp.zeros_like(distribution)
        next_distribution = next_distribution.at[machine[:, 0]].add(
            distribution * (1.0 - p_one)
        )
        next_distribution = next_distribution.at[machine[:, 1]].add(
            distribution * p_one
        )
        distribution = next_distribution
    return total


expected_original_ones_batch = jax.jit(jax.vmap(expected_original_ones))


def lossy_view_diagnostics(
    spec: dict[str, Any], splits: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    view_machines: list[list[list[int]]] = []
    view_keys: list[list[list[tuple[int, int]]]] = []
    view_splits: list[str] = []
    all_key_pairs: list[tuple[int, int]] = []
    for split_name, rows in splits.items():
        views_per_object = spec["frozen_splits"][f"{split_name}_views_per_object"]
        for row in rows:
            for view_index in range(views_per_object):
                view_machines.append(row["machine"])
                view_splits.append(split_name)
                trajectory_keys: list[list[tuple[int, int]]] = []
                for trajectory_index in range(TRAJECTORIES_PER_VIEW):
                    channel_keys = [
                        key_data(
                            f"ufpo-v0|view|{row['machine_sha256']}|{view_index}|"
                            f"{trajectory_index}|{channel}"
                        )
                        for channel in ("initial", "output", "erasure", "substitution")
                    ]
                    all_key_pairs.extend(channel_keys)
                    trajectory_keys.append(channel_keys)
                view_keys.append(trajectory_keys)
    machines = jnp.asarray(view_machines, dtype=jnp.int64)
    keys = jnp.asarray(view_keys, dtype=jnp.uint32)
    observed = jax.device_get(simulate_views(machines, keys)).tolist()
    expected_ones = jax.device_get(expected_original_ones_batch(machines)).tolist()
    split_receipts: dict[str, Any] = {}
    for split_name in splits:
        indices = [index for index, value in enumerate(view_splits) if value == split_name]
        totals = [
            sum(observed[index][trajectory][field] for index in indices for trajectory in range(TRAJECTORIES_PER_VIEW))
            for field in range(5)
        ]
        token_count = len(indices) * TRAJECTORIES_PER_VIEW * TRAJECTORY_LENGTH
        expected_original = sum(expected_ones[index] for index in indices) * TRAJECTORIES_PER_VIEW
        expected_corrupted_visible_ones = (1.0 - ERASURE_PROBABILITY) * (
            expected_original * (1.0 - SUBSTITUTION_PROBABILITY)
            + (token_count - expected_original) * SUBSTITUTION_PROBABILITY
        )
        split_receipts[split_name] = {
            "view_count": len(indices),
            "trajectory_count": len(indices) * TRAJECTORIES_PER_VIEW,
            "token_count": token_count,
            "observed_original_one_rate": totals[0] / token_count,
            "expected_original_one_rate": expected_original / token_count,
            "observed_erasure_rate": totals[3] / token_count,
            "expected_erasure_rate": ERASURE_PROBABILITY,
            "observed_substitution_after_non_erasure_rate": totals[4] / totals[1],
            "expected_substitution_after_non_erasure_rate": SUBSTITUTION_PROBABILITY,
            "observed_corrupted_visible_one_rate": totals[2] / totals[1],
            "expected_corrupted_visible_one_rate": (
                expected_corrupted_visible_ones
                / ((1.0 - ERASURE_PROBABILITY) * token_count)
            ),
        }
    return {
        "generator": "JAX random from independent SHA-256-derived typed-key data",
        "total_view_count": len(view_machines),
        "total_prng_subtree_count": len(all_key_pairs),
        "prng_subtree_collision_count": len(all_key_pairs) - len(set(all_key_pairs)),
        "model_visible_payload_fields": [
            "corrupted_binary_tokens",
            "erasure_mask",
            "trajectory_boundary",
        ],
        "aggregate_split_diagnostics": split_receipts,
    }


def z3_overlap_status(left: Sequence[str], right: Sequence[str], label: str) -> str:
    witness = z3.BitVec(f"z3_{label}", 256)
    solver = z3.Solver()
    solver.add(
        z3.Or([witness == z3.BitVecVal(int(value, 16), 256) for value in left])
    )
    solver.add(
        z3.Or([witness == z3.BitVecVal(int(value, 16), 256) for value in right])
    )
    return str(solver.check())


def cvc5_overlap_status(left: Sequence[str], right: Sequence[str], label: str) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_BV")
    sort = solver.mkBitVectorSort(256)
    witness = solver.mkConst(sort, f"cvc5_{label}")

    def membership(values: Sequence[str]):
        equalities = [
            solver.mkTerm(
                cvc5.Kind.EQUAL,
                witness,
                solver.mkBitVector(256, value, 16),
            )
            for value in values
        ]
        return equalities[0] if len(equalities) == 1 else solver.mkTerm(cvc5.Kind.OR, *equalities)

    solver.assertFormula(membership(left))
    solver.assertFormula(membership(right))
    return str(solver.checkSat())


def split_solver_receipt(splits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    hashes = {
        name: [row["machine_sha256"] for row in rows] for name, rows in splits.items()
    }
    pair_names = (("train", "validation"), ("train", "test"), ("validation", "test"))
    z3_intact = {
        f"{left}_vs_{right}": z3_overlap_status(hashes[left], hashes[right], f"{left}_{right}")
        for left, right in pair_names
    }
    cvc5_intact = {
        f"{left}_vs_{right}": cvc5_overlap_status(hashes[left], hashes[right], f"{left}_{right}")
        for left, right in pair_names
    }
    injected = hashes["test"] + [hashes["train"][0]]
    z3_erased = z3_overlap_status(hashes["train"], injected, "erased_control")
    cvc5_erased = cvc5_overlap_status(hashes["train"], injected, "erased_control")
    return {
        "intact_overlap_queries": {"z3": z3_intact, "cvc5": cvc5_intact},
        "erased_control": {
            "mutation": "inject first train machine hash into test hash set",
            "z3": z3_erased,
            "cvc5": cvc5_erased,
        },
        "intact_disjoint": all(value == "unsat" for value in z3_intact.values())
        and all(value == "unsat" for value in cvc5_intact.values()),
        "erased_control_detected": z3_erased == "sat" and cvc5_erased == "sat",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()
    started = time.perf_counter()

    spec, manifest, frozen_receipt = verify_frozen_inputs()
    reconstructed = reconstruct_registry(spec)
    split_names = ("train", "validation", "test")
    reconstructed_public = {
        name: [public_row(row) for row in reconstructed["splits"][name]]
        for name in split_names
    }
    manifest_match = all(
        reconstructed_public[name] == manifest["splits"][name] for name in split_names
    )
    accepted_count_match = (
        reconstructed["accepted_candidate_count"] == manifest["accepted_candidate_count"]
    )
    rejected_counts_match = reconstructed["rejected_counts"] == manifest["rejected_counts"]
    reconstructed_pairs = hard_negative_pairs(reconstructed["splits"]["test"])
    hard_pairs_match = reconstructed_pairs == manifest["hard_negative_test_pairs"]

    all_rows = [row for name in split_names for row in reconstructed["splits"][name]]
    distribution_receipt = predictive_distribution_receipt(all_rows)
    view_receipt = lossy_view_diagnostics(spec, reconstructed["splits"])
    solver_receipt = split_solver_receipt(reconstructed["splits"])

    visible = set(spec["view_process"]["model_visible_fields"])
    forbidden = set(spec["view_process"]["model_forbidden_fields"])
    expected_controls = {
        "optimizer_erased_learning_rate_zero",
        "architecture_only_untrained",
        "fixed_deranged_object_targets_and_positive_pairs",
        "temporal_shuffle_preserving_token_and_mask_counts",
        "marginal_histogram_parameter_matched_mlp",
        "hard_negative_pairs_selected_from_exact_short_horizon_similarity_before_training",
    }
    split_hash_sets = {
        name: {row["machine_sha256"] for row in reconstructed["splits"][name]}
        for name in split_names
    }
    leakage_census = {
        "split_counts": {name: len(split_hash_sets[name]) for name in split_names},
        "pairwise_machine_hash_overlap_counts": {
            "train_validation": len(split_hash_sets["train"] & split_hash_sets["validation"]),
            "train_test": len(split_hash_sets["train"] & split_hash_sets["test"]),
            "validation_test": len(split_hash_sets["validation"] & split_hash_sets["test"]),
        },
        "predictive_signature_unique_count": len(
            {row["predictive_signature_sha256"] for row in all_rows}
        ),
        "counter_unique_count": len({row["counter"] for row in all_rows}),
        "visible_forbidden_field_overlap": sorted(visible & forbidden),
        "model_input_excludes_manifest_identity_fields": manifest[
            "model_input_excludes_manifest_identity_fields"
        ],
        "prng_subtree_collision_count": view_receipt["prng_subtree_collision_count"],
        "learned_metric_files_opened": [],
        "peer_result_files_opened": [],
    }
    control_census = {
        "declared_count": len(spec["controls"]),
        "unique_count": len(set(spec["controls"])),
        "exact_frozen_control_set": set(spec["controls"]) == expected_controls,
        "hard_negative_pair_count": len(reconstructed_pairs),
        "all_test_hashes_used_exactly_once_in_pairs": sorted(
            value for pair in reconstructed_pairs for value in pair
        )
        == sorted(split_hash_sets["test"]),
        "test_labels_forbidden_from_training_and_threshold_selection": spec[
            "metrics_and_gates"
        ]["test_labels_forbidden_from_training_and_threshold_selection"],
    }

    gates = {
        "G1_all_frozen_hashes_and_commit_blobs_verified": frozen_receipt["all_verified"],
        "G2_registry_counts_reconstructed_exactly": accepted_count_match
        and rejected_counts_match,
        "G3_all_192_manifest_rows_reconstructed_exactly": manifest_match,
        "G4_all_signature_hashes_and_hard_pairs_exact": manifest_match and hard_pairs_match,
        "G5_exact_and_float64_predictive_distributions_normalized": (
            distribution_receipt["dtype"] == "float64"
            and distribution_receipt["exact_integer_normalization"]
            and distribution_receipt["maximum_float64_normalization_error"] <= 2.0e-15
        ),
        "G6_independent_lossy_view_subtrees_and_counts": (
            view_receipt["total_view_count"] == 1280
            and view_receipt["prng_subtree_collision_count"] == 0
        ),
        "G7_split_and_leakage_census_clean": (
            all(value == 0 for value in leakage_census["pairwise_machine_hash_overlap_counts"].values())
            and leakage_census["predictive_signature_unique_count"] == 192
            and leakage_census["counter_unique_count"] == 192
            and not leakage_census["visible_forbidden_field_overlap"]
        ),
        "G8_control_census_exact": all(
            (
                control_census["declared_count"] == 6,
                control_census["unique_count"] == 6,
                control_census["exact_frozen_control_set"],
                control_census["hard_negative_pair_count"] == 16,
                control_census["all_test_hashes_used_exactly_once_in_pairs"],
                control_census["test_labels_forbidden_from_training_and_threshold_selection"],
            )
        ),
        "G9_z3_cvc5_disjointness_with_erased_control": (
            solver_receipt["intact_disjoint"]
            and solver_receipt["erased_control_detected"]
        ),
        "G10_controller_three_engine_and_learner_evaluation": None,
    }
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
        "controller_blocker": (
            "G10 requires controller-side three-engine parity and sealed PyTorch learner/control evaluation"
        ),
        "source_path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "frozen_inputs": frozen_receipt,
        "reads_peer_result": False,
        "learned_metric_files_read": [],
        "numpy_imported_by_source": False,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "runtime": {
            "python": "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
            "jax": jax.__version__,
            "z3": z3.get_version_string(),
            "cvc5": cvc5.__version__,
        },
        "registry_reconstruction": {
            "candidate_interval": manifest["candidate_interval"],
            "accepted_candidate_count": reconstructed["accepted_candidate_count"],
            "rejected_counts": reconstructed["rejected_counts"],
            "selected_count": len(all_rows),
            "split_counts": {name: len(reconstructed["splits"][name]) for name in split_names},
            "manifest_rows_exact": manifest_match,
            "hard_negative_pairs_exact": hard_pairs_match,
            "reconstructed_registry_sha256": canonical_hash(reconstructed_public),
        },
        "predictive_distributions": distribution_receipt,
        "lossy_view_diagnostics": view_receipt,
        "leakage_census": leakage_census,
        "control_census": control_census,
        "split_solver_receipt": solver_receipt,
        "gates": gates,
        "tool_manifest": {
            "jax.jit": "load_bearing",
            "jax.vmap": "load_bearing",
            "jax.numpy": "load_bearing exact integer and float64 arrays",
            "z3.Solver": "load_bearing split-disjointness proof with erased control",
            "cvc5.Solver": "load_bearing split-disjointness proof with erased control",
            "numpy": None,
        },
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(machine_numerators))",
                "input_object": "independently canonicalized strongly connected candidates from counters 0..4095",
                "output_object": "exact int64 state and uniform-start predictive numerators through length eight",
                "positive_case": "all 192 rows, 960 signature hashes, and 16 hard pairs match the frozen manifest",
                "negative/erased_control": "normalization is checked against exact 4*8^length totals",
                "boundary_case": "all lengths one through eight and all 510 coordinates",
                "demotion_condition": "any registry, signature, hard-pair, x64, or normalization mismatch",
                "gates": ["all_pass", "distribution"],
            },
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(simulate_view))",
                "input_object": "1,280 views with 40,960 distinct SHA-256-derived trajectory/channel subtrees",
                "output_object": "aggregate lossy-view distribution diagnostics over 10,240 trajectories",
                "positive_case": "frozen view census generated with no PRNG subtree collision",
                "negative/erased_control": "forbidden identity fields are excluded from the visible payload schema",
                "boundary_case": "train, validation, and test aggregates emitted without per-test learned metrics",
                "demotion_condition": "view-count, key-collision, visible-field, or runtime mismatch",
                "gates": ["all_pass", "leakage"],
            },
            {
                "tool": "z3+cvc5",
                "qualified_api/function": "z3.Solver.check and cvc5.Solver.checkSat",
                "input_object": "256-bit machine-hash memberships derived independently inside each solver",
                "output_object": "three UNSAT pairwise-overlap proofs per solver",
                "positive_case": "train, validation, and test are pairwise disjoint",
                "negative/erased_control": "first train hash injected into test gives SAT in both solvers",
                "boundary_case": "all 192 full-width hashes, without truncated identifiers",
                "demotion_condition": "any intact query is not UNSAT or erased control is not SAT",
                "gates": ["all_pass", "split_disjointness"],
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
    strict_write_json(args.output, payload)
    print(
        json.dumps(
            {
                "all_local_gates_pass": all_local_gates_pass,
                "all_pass": False,
                "elapsed_seconds": elapsed,
                "output": str(args.output),
                "source_sha256": payload["source_sha256"],
                "status": payload["status"],
            },
            sort_keys=True,
        )
    )
    return 0 if all_local_gates_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
