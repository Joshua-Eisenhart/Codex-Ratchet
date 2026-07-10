#!/usr/bin/env python3
"""Exhaustive JAX x64 census of finite ECA behavioral-refinement depth."""

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


SIM_ID = "eca_behavioral_refinement_depth_census_v0"
SCHEMA = "codex_ratchet.eca_behavioral_refinement_depth_census_v0.jax.v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
RING_SIZES = (6, 7, 8)
RULE_COUNT = 256
MAX_STEPS = 16
BATCH_BY_RING = {6: 256, 7: 128, 8: 32}
HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "results" / f"{SIM_ID}_jax_results.json"

TOOL_MANIFEST = {
    "jax.numpy": {
        "used": True,
        "reason": "Exact x64 integer and Boolean arrays for transitions and partitions.",
    },
    "jax.vmap": {
        "used": True,
        "reason": "Exhaustive vectorized construction of every ECA transition table.",
    },
    "jax.lax.scan": {
        "used": True,
        "reason": "Compiled fixed-budget monotone partition refinement.",
    },
    "jax.jit": {
        "used": True,
        "reason": "Compiled batched census over all unordered rule pairs.",
    },
    "numpy": {"used": False, "reason": "Forbidden from the claim path."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax.numpy": "load_bearing",
    "jax.vmap": "load_bearing",
    "jax.lax.scan": "load_bearing",
    "jax.jit": "load_bearing",
    "numpy": None,
}


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


def eca_transition_table(ring_size: int) -> jax.Array:
    state_count = 1 << ring_size
    sites = jnp.arange(ring_size, dtype=jnp.int64)
    states = jnp.arange(state_count, dtype=jnp.int64)
    rules = jnp.arange(RULE_COUNT, dtype=jnp.int64)

    def step(rule: jax.Array, state: jax.Array) -> jax.Array:
        bits = (state >> sites) & 1
        left = jnp.roll(bits, 1)
        right = jnp.roll(bits, -1)
        neighborhoods = (left << 2) | (bits << 1) | right
        return jnp.sum(((rule >> neighborhoods) & 1) << sites, dtype=jnp.int64)

    return vmap(lambda rule: vmap(lambda state: step(rule, state))(states))(rules)


def canonicalize_rows(rows: jax.Array) -> jax.Array:
    state_count = rows.shape[-2]
    equal = jnp.all(rows[..., :, None, :] == rows[..., None, :, :], axis=-1)
    indices = jnp.arange(state_count, dtype=jnp.int64)
    return jnp.min(jnp.where(equal, indices, state_count), axis=-1)


def base_probe_labels(ring_size: int) -> jax.Array:
    state_count = 1 << ring_size
    states = jnp.arange(state_count, dtype=jnp.int64)
    sites = jnp.arange(ring_size, dtype=jnp.int64)
    bits = (states[:, None] >> sites) & 1
    weight = jnp.sum(bits, axis=1, dtype=jnp.int64)
    walls = jnp.sum(bits != jnp.roll(bits, -1, axis=1), axis=1, dtype=jnp.int64)
    return canonicalize_rows(jnp.stack([weight, walls], axis=-1))


def build_batch_kernel(ring_size: int):
    state_count = 1 << ring_size
    base = base_probe_labels(ring_size)

    @jax.jit
    def kernel(action_a: jax.Array, action_b: jax.Array):
        labels0 = jnp.broadcast_to(base, action_a.shape)
        active0 = jnp.ones((action_a.shape[0],), dtype=jnp.bool_)
        strict0 = jnp.zeros((action_a.shape[0],), dtype=jnp.int64)

        def observables(labels: jax.Array) -> tuple[jax.Array, jax.Array]:
            representatives = jnp.arange(state_count, dtype=jnp.int64)[None, :]
            class_count = jnp.sum(labels == representatives, axis=1)
            survival = jnp.sum(labels[:, :, None] == labels[:, None, :], axis=(1, 2))
            return class_count, survival

        class0, survival0 = observables(labels0)

        def body(carry, _):
            labels, active, strict = carry
            next_a = jnp.take_along_axis(labels, action_a, axis=1)
            next_b = jnp.take_along_axis(labels, action_b, axis=1)
            refined = canonicalize_rows(jnp.stack([labels, next_a, next_b], axis=-1))
            changed = jnp.any(refined != labels, axis=1)
            strict = strict + (active & changed).astype(jnp.int64)
            active = active & changed
            labels = refined
            class_count, survival = observables(labels)
            return (labels, active, strict), (class_count, survival)

        (labels, active, strict), (class_steps, survival_steps) = lax.scan(
            body, (labels0, active0, strict0), xs=None, length=MAX_STEPS
        )
        class_trajectory = jnp.concatenate([class0[None, :], class_steps], axis=0).T
        survival_trajectory = jnp.concatenate(
            [survival0[None, :], survival_steps], axis=0
        ).T
        return strict, active, labels, class_trajectory, survival_trajectory

    return kernel


def trim_strict_trajectory(values: list[int], strict_depth: int) -> list[int]:
    return values[: strict_depth + 1]


def census(ring_size: int) -> dict:
    started = time.time()
    state_count = 1 << ring_size
    transitions = eca_transition_table(ring_size)
    transitions.block_until_ready()
    transitions_host = transitions.tolist()
    pairs = list(itertools.combinations(range(RULE_COUNT), 2))
    batch_size = BATCH_BY_RING[ring_size]
    kernel = build_batch_kernel(ring_size)
    depth_counts: Counter[int] = Counter()
    joint_counts: dict[int, Counter[int]] = defaultdict(Counter)
    examples: dict[int, list[list[int]]] = defaultdict(list)
    ledger: list[dict] = []
    nonstabilized: list[list[int]] = []

    for start in range(0, len(pairs), batch_size):
        batch = pairs[start : start + batch_size]
        real_count = len(batch)
        padded = batch + [batch[-1]] * (batch_size - real_count)
        a = jnp.asarray([pair[0] for pair in padded], dtype=jnp.int64)
        b = jnp.asarray([pair[1] for pair in padded], dtype=jnp.int64)
        strict, active, labels, class_traj, survival_traj = kernel(
            transitions[a], transitions[b]
        )
        for index in range(real_count):
            rule_a, rule_b = batch[index]
            depth = int(strict[index])
            final_labels = labels[index].tolist()
            first_equality_round = depth + 1
            class_values = trim_strict_trajectory(
                class_traj[index].tolist(), depth
            )
            survival_values = trim_strict_trajectory(
                survival_traj[index].tolist(), depth
            )
            stable_class_count = int(class_values[-1])
            depth_counts[depth] += 1
            joint_counts[depth][stable_class_count] += 1
            if len(examples[depth]) < 12:
                examples[depth].append([rule_a, rule_b])
            if bool(active[index]):
                nonstabilized.append([rule_a, rule_b])
            ledger.append(
                {
                    "rule_a": rule_a,
                    "rule_b": rule_b,
                    "strict_refinement_depth": depth,
                    "first_equality_round": first_equality_round,
                    "class_count_trajectory": class_values,
                    "surviving_ordered_pair_count_trajectory": survival_values,
                    "stable_class_count": stable_class_count,
                    "partition_hash": compact_labels_hash(final_labels),
                    "transition_pair_hash": canonical_hash(
                        [transitions_host[rule_a], transitions_host[rule_b]]
                    ),
                }
            )

    histogram = {str(key): depth_counts[key] for key in sorted(depth_counts)}
    tests = {
        "all_unordered_distinct_pairs_present": len(ledger) == 32640,
        "no_nonstabilized_pairs": not nonstabilized,
        "depth_histogram_sums_to_pair_count": sum(depth_counts.values()) == 32640,
        "strict_depth_bounded_by_state_count": max(depth_counts) < state_count,
        "constant_rule_boundaries": transitions_host[0] == [0] * state_count
        and transitions_host[255] == [state_count - 1] * state_count,
    }
    return {
        "ring_size": ring_size,
        "state_count": state_count,
        "rule_pair_count": len(ledger),
        "batch_size": batch_size,
        "maximum_strict_refinement_depth": max(depth_counts),
        "strict_refinement_depth_histogram": histogram,
        "depth_by_stable_class_count_histogram": {
            str(depth): {str(key): counts[key] for key in sorted(counts)}
            for depth, counts in sorted(joint_counts.items())
        },
        "example_pairs_by_depth": {
            str(depth): values for depth, values in sorted(examples.items())
        },
        "nonstabilized_pairs": nonstabilized,
        "transition_census_hash": canonical_hash(transitions_host),
        "pair_ledger_hash": canonical_hash(ledger),
        "pair_ledger": ledger,
        "tests": tests,
        "all_pass": all(tests.values()),
        "elapsed_seconds": time.time() - started,
    }


def build_receipt() -> dict:
    rings = [census(ring_size) for ring_size in RING_SIZES]
    all_pass = all(ring["all_pass"] for ring in rings)
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "jax_version": jax.__version__,
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "numpy_used": False,
        "peer_result_files_read": [],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "depth_definition": "number of strict partition changes before first equality",
        "first_equality_round_definition": "strict_refinement_depth + 1",
        "rings": rings,
        "all_pass": all_pass,
        "all_scientific_gates_pass": False,
        "allowed_claims": [
            "independent exhaustive finite ECA refinement-depth census for rings 6 through 8"
        ],
        "claim_ceiling": "independent JAX scratch census only until Julia and controller compare every ledger record",
        "blocked_consumers": [
            "learned perception",
            "QIT engine stages or substages",
            "general object formation",
            "MMMs and ontology admission",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    receipt = build_receipt()
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
                "depth_histograms": {
                    str(ring["ring_size"]): ring["strict_refinement_depth_histogram"]
                    for ring in receipt["rings"]
                },
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
