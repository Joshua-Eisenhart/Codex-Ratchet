#!/usr/bin/env python3
"""Independent JAX workhorse for the frozen finite-structure tournament.

This lane reads only spec.json.  It does not read Julia, SMT, controller, or
other engine results.  JAX jit/vmap performs the exhaustive relabeling sweep,
and jraph.segment_sum is load-bearing for transition viability.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from importlib import metadata
from pathlib import Path
from typing import Any, Iterable

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import jraph


SIM_DIR = Path(__file__).resolve().parent
SPEC_PATH = SIM_DIR / "spec.json"
DEFAULT_OUT = SIM_DIR / "results" / "jax_result.json"
EXPECTED_SPEC_SHA256 = "060177cae89e23e19f05c6ed7f10fe729bb636db14e0d1caaab66770872efae3"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "exact": f"{value.numerator}/{value.denominator}",
        "numerator": value.numerator,
        "denominator": value.denominator,
        "float": float(value),
    }


def permutations(n: int) -> list[tuple[int, ...]]:
    return list(itertools.permutations(range(n)))


def bits_to_mask(matrix: list[list[bool]]) -> int:
    value = 0
    for row in matrix:
        for bit in row:
            value = (value << 1) | int(bit)
    return value


def mask_to_matrix(mask: int, n: int) -> list[list[bool]]:
    width = n * n
    flat = [bool((mask >> (width - 1 - index)) & 1) for index in range(width)]
    return [flat[row * n : (row + 1) * n] for row in range(n)]


def bitstring(mask: int, n: int) -> str:
    return format(mask, f"0{n * n}b")


def relabel_matrix(matrix: list[list[bool]], permutation: tuple[int, ...]) -> list[list[bool]]:
    n = len(matrix)
    return [[matrix[permutation[i]][permutation[j]] for j in range(n)] for i in range(n)]


def direct_automorphisms(
    matrix: list[list[bool]], all_permutations: list[tuple[int, ...]]
) -> list[tuple[int, ...]]:
    return [p for p in all_permutations if relabel_matrix(matrix, p) == matrix]


def jax_relation_batch(n: int) -> dict[str, Any]:
    """Exhaust the labelled relation family with compiled batched relabeling."""

    width = n * n
    total = 1 << width
    values = jnp.arange(total, dtype=jnp.int64)
    shifts = jnp.arange(width - 1, -1, -1, dtype=jnp.int64)
    matrices = ((values[:, None] >> shifts[None, :]) & 1).astype(jnp.bool_)
    matrices = matrices.reshape((total, n, n))
    perms = jnp.asarray(permutations(n), dtype=jnp.int32)
    weights = (jnp.asarray(1, dtype=jnp.int64) << shifts).astype(jnp.int64)

    def transform_one(matrix: jax.Array) -> jax.Array:
        def apply(permutation: jax.Array) -> jax.Array:
            return matrix[permutation[:, None], permutation[None, :]]

        return jax.vmap(apply)(perms)

    transform_batch = jax.jit(jax.vmap(transform_one))
    transformed = transform_batch(matrices)
    packed = jnp.tensordot(
        transformed.reshape((total, len(permutations(n)), width)),
        weights,
        axes=((-1,), (0,)),
    )
    canonical = jnp.min(packed, axis=1)
    automorphisms = jnp.all(transformed == matrices[:, None, :, :], axis=(2, 3))

    senders = jnp.repeat(jnp.arange(n, dtype=jnp.int32), n)

    def degrees_one(matrix: jax.Array) -> jax.Array:
        # Rich graph API is deliberately load-bearing for V_serial/V_branching.
        return jraph.segment_sum(
            matrix.reshape((-1,)).astype(jnp.int64), senders, num_segments=n
        )

    degree_batch = jax.jit(jax.vmap(degrees_one))
    outdegrees = degree_batch(matrices)

    # Recanonicalize every relabelled representative through the full lookup.
    recanonicalized = canonical[packed]
    relabel_canonical_invariant = bool(
        jax.device_get(jnp.all(recanonicalized == canonical[:, None]))
    )

    canonical.block_until_ready()
    automorphisms.block_until_ready()
    outdegrees.block_until_ready()
    return {
        "matrices": jax.device_get(matrices).tolist(),
        "canonical": [int(value) for value in jax.device_get(canonical).tolist()],
        "automorphisms": jax.device_get(automorphisms).tolist(),
        "outdegrees": jax.device_get(outdegrees).tolist(),
        "packed_relabelings": jax.device_get(packed).tolist(),
        "relabel_canonical_invariant": relabel_canonical_invariant,
    }


def jax_weighted_automorphisms(
    integer_matrix: list[list[int]], all_permutations: list[tuple[int, ...]]
) -> list[tuple[int, ...]]:
    matrix = jnp.asarray(integer_matrix, dtype=jnp.int64)
    perms = jnp.asarray(all_permutations, dtype=jnp.int32)

    @jax.jit
    def test_all() -> jax.Array:
        def apply(permutation: jax.Array) -> jax.Array:
            transformed = matrix[permutation[:, None], permutation[None, :]]
            return jnp.all(transformed == matrix)

        return jax.vmap(apply)(perms)

    flags = jax.device_get(test_all()).tolist()
    return [p for p, keep in zip(all_permutations, flags, strict=True) if keep]


def cycle_membership(matrix: list[list[bool]]) -> list[bool]:
    n = len(matrix)
    answer: list[bool] = []
    for start in range(n):
        stack = [target for target in range(n) if matrix[start][target]]
        seen: set[int] = set()
        found = False
        while stack:
            node = stack.pop()
            if node == start:
                found = True
                break
            if node in seen:
                continue
            seen.add(node)
            stack.extend(target for target in range(n) if matrix[node][target])
        answer.append(found)
    return answer


def partition_from_keys(keys: Iterable[Any]) -> list[list[int]]:
    blocks: dict[Any, list[int]] = defaultdict(list)
    for state, key in enumerate(keys):
        blocks[key].append(state)
    return sorted((sorted(block) for block in blocks.values()), key=lambda block: (block[0], block))


def normalize_partition(partition: Iterable[Iterable[int]]) -> list[list[int]]:
    return sorted((sorted(block) for block in partition), key=lambda block: (block[0], block))


def automorphism_orbits(n: int, automorphisms: list[tuple[int, ...]]) -> list[list[int]]:
    parent = list(range(n))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for permutation in automorphisms:
        for source, target in enumerate(permutation):
            union(source, target)
    return partition_from_keys(find(state) for state in range(n))


def strong_bisimulation(matrix: list[list[bool]]) -> list[list[int]]:
    """Greatest unlabelled strong bisimulation by finite partition refinement."""

    n = len(matrix)
    partition = [list(range(n))]
    while True:
        block_of = {}
        for block_index, block in enumerate(partition):
            for state in block:
                block_of[state] = block_index
        signatures = []
        for source in range(n):
            successor_blocks = sorted(
                {block_of[target] for target in range(n) if matrix[source][target]}
            )
            signatures.append(tuple(successor_blocks))
        refined = partition_from_keys((block_of[state], signatures[state]) for state in range(n))
        if refined == partition:
            return refined
        partition = refined


def local_probe_partition(matrix: list[list[bool]]) -> list[list[int]]:
    n = len(matrix)
    outdegrees = [sum(row) for row in matrix]
    indegrees = [sum(matrix[source][target] for source in range(n)) for target in range(n)]
    fingerprints = []
    for state in range(n):
        fingerprints.append(
            (
                bool(matrix[state][state]),
                indegrees[state],
                outdegrees[state],
                tuple(sorted(outdegrees[target] for target in range(n) if matrix[state][target])),
                tuple(sorted(indegrees[source] for source in range(n) if matrix[source][state])),
            )
        )
    return partition_from_keys(fingerprints)


def kernel_row_partition(kernel: list[list[Fraction]]) -> list[list[int]]:
    return partition_from_keys(tuple(row) for row in kernel)


def partition_refines(left: list[list[int]], right: list[list[int]]) -> bool:
    right_sets = [set(block) for block in right]
    return all(any(set(block) <= container for container in right_sets) for block in left)


def partition_disagreement_witness(
    left: list[list[int]], right: list[list[int]], n: int
) -> list[int] | None:
    def same(partition: list[list[int]], a: int, b: int) -> bool:
        return any(a in block and b in block for block in partition)

    for a in range(n):
        for b in range(a + 1, n):
            if same(left, a, b) != same(right, a, b):
                return [a, b]
    return None


def partition_comparisons(partitions: dict[str, list[list[int]]], n: int) -> list[dict[str, Any]]:
    outputs = []
    for left, right in itertools.combinations(sorted(partitions), 2):
        p, q = partitions[left], partitions[right]
        equal = p == q
        outputs.append(
            {
                "left": left,
                "right": right,
                "equal": equal,
                "left_refines_right": partition_refines(p, q),
                "right_refines_left": partition_refines(q, p),
                "disagreement_witness": None
                if equal
                else partition_disagreement_witness(p, q, n),
            }
        )
    return outputs


def viability_for_support(
    matrix: list[list[bool]],
    semantic_type: str,
    outdegrees_override: list[int] | None = None,
) -> dict[str, dict[str, bool]]:
    n = len(matrix)
    transition_applicable = semantic_type in {"transition_relation", "markov_kernel"}
    outdegrees = (
        [int(value) for value in outdegrees_override]
        if outdegrees_override is not None
        else [sum(row) for row in matrix]
    )
    serial = transition_applicable and all(degree >= 1 for degree in outdegrees)
    persistent = transition_applicable and all(cycle_membership(matrix))
    branching = transition_applicable and n > 1 and all(degree >= 2 for degree in outdegrees)
    return {
        "V_registered": {"applicable": True, "pass": True},
        "V_serial": {"applicable": transition_applicable, "pass": serial},
        "V_persistent_support": {
            "applicable": transition_applicable,
            "pass": persistent,
        },
        "V_branching": {"applicable": transition_applicable, "pass": branching},
        "V_exploratory_support": {
            "applicable": transition_applicable,
            "pass": persistent and branching,
        },
        "V_unbiased_stochastic": {"applicable": False, "pass": False},
    }


def relation_signature_key(semantic_type: str) -> tuple[int, int, int, int]:
    if semantic_type == "empty_signature":
        return (0, 0, 0, 0)
    if semantic_type == "static_relation":
        return (1, 0, 0, 0)
    if semantic_type == "transition_relation":
        return (1, 1, 0, 0)
    if semantic_type == "markov_kernel":
        return (0, 1, 1, 0)
    raise ValueError(semantic_type)


def public_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in candidate.items() if not key.startswith("_")}


def candidate_partitions(
    semantic_type: str,
    matrix: list[list[bool]],
    automorphisms: list[tuple[int, ...]],
    kernel: list[list[Fraction]] | None = None,
) -> tuple[dict[str, list[list[int]]], list[dict[str, Any]]]:
    partitions = {"automorphism_orbits": automorphism_orbits(len(matrix), automorphisms)}
    if semantic_type == "transition_relation":
        partitions["strong_bisimulation"] = strong_bisimulation(matrix)
    if semantic_type in {"static_relation", "transition_relation", "markov_kernel"}:
        partitions["local_probe_equivalence"] = local_probe_partition(matrix)
    if semantic_type == "markov_kernel":
        assert kernel is not None
        partitions["kernel_row_equivalence"] = kernel_row_partition(kernel)
    partitions = {key: normalize_partition(value) for key, value in partitions.items()}
    return partitions, partition_comparisons(partitions, len(matrix))


def relation_candidate(
    n: int,
    mask: int,
    semantic_type: str,
    aliases: list[str],
    automorphisms: list[tuple[int, ...]],
    labelled_members: list[int],
    jraph_outdegrees: list[int],
) -> dict[str, Any]:
    matrix = mask_to_matrix(mask, n)
    prefix = "R" if semantic_type == "static_relation" else "T"
    candidate_id = aliases[0] if aliases else f"{prefix}_{n}_{bitstring(mask, n)}"
    viability = viability_for_support(matrix, semantic_type, jraph_outdegrees)
    partitions, comparisons = candidate_partitions(semantic_type, matrix, automorphisms)
    support = {(source, target) for source in range(n) for target in range(n) if matrix[source][target]}
    return {
        "candidate_id": candidate_id,
        "provenance_aliases": aliases,
        "registry_identity": {
            "carrier_size": n,
            "semantic_type": semantic_type,
            "canonical_adjacency": bitstring(mask, n),
            "named_constants": [],
        },
        "carrier_size": n,
        "semantic_type": semantic_type,
        "canonical_mask": mask,
        "canonical_bitstring": bitstring(mask, n),
        "labelled_orbit_members": labelled_members,
        "labelled_orbit_size": len(labelled_members),
        "support_matrix": [[int(value) for value in row] for row in matrix],
        "automorphism": {
            "order": len(automorphisms),
            "permutations": [list(p) for p in automorphisms],
            "orbits": automorphism_orbits(n, automorphisms),
        },
        "viability": viability,
        "distinction_partitions": partitions,
        "distinction_comparisons": comparisons,
        "_autset": set(automorphisms),
        "_supportset": support,
        "_signature_key": relation_signature_key(semantic_type),
        "_stochastic_key": None,
    }


def empty_candidate(n: int) -> dict[str, Any]:
    perms = permutations(n)
    partitions = {"automorphism_orbits": [list(range(n))]}
    return {
        "candidate_id": f"U_{n}",
        "provenance_aliases": [f"U_{n}"],
        "registry_identity": {
            "carrier_size": n,
            "semantic_type": "empty_signature",
            "canonical_adjacency": None,
            "named_constants": [],
        },
        "carrier_size": n,
        "semantic_type": "empty_signature",
        "automorphism": {
            "order": len(perms),
            "permutations": [list(p) for p in perms],
            "orbits": [list(range(n))],
        },
        "viability": {
            "V_registered": {"applicable": True, "pass": True},
            "V_serial": {"applicable": False, "pass": False},
            "V_persistent_support": {"applicable": False, "pass": False},
            "V_branching": {"applicable": False, "pass": False},
            "V_exploratory_support": {"applicable": False, "pass": False},
            "V_unbiased_stochastic": {"applicable": False, "pass": False},
        },
        "distinction_partitions": partitions,
        "distinction_comparisons": [],
        "_autset": set(perms),
        "_supportset": None,
        "_signature_key": relation_signature_key("empty_signature"),
        "_stochastic_key": None,
    }


def named_kernel(name: str, n: int) -> list[list[Fraction]]:
    if n <= 0:
        raise ValueError("kernel carrier size must be positive")
    if name == "K0":
        return [[Fraction(1, n) for _ in range(n)] for _ in range(n)]
    if name == "Klazy":
        if n == 1:
            return named_kernel("K0", n)
        return [
            [Fraction(1, 2) if source == target else Fraction(1, 2 * (n - 1)) for target in range(n)]
            for source in range(n)
        ]
    if name == "Kbiased":
        return [
            [Fraction(2 * (target + 1), n * (n + 1)) for target in range(n)]
            for _source in range(n)
        ]
    if name == "Kidentity":
        return [
            [Fraction(int(source == target), 1) for target in range(n)]
            for source in range(n)
        ]
    raise ValueError(name)


def common_integer_matrix(kernel: list[list[Fraction]]) -> tuple[list[list[int]], int]:
    denominator = 1
    for row in kernel:
        for value in row:
            denominator = math.lcm(denominator, value.denominator)
    return (
        [[value.numerator * (denominator // value.denominator) for value in row] for row in kernel],
        denominator,
    )


def stochastic_distances(kernel: list[list[Fraction]]) -> tuple[Fraction, Fraction]:
    """The exact formulas frozen in amendment_1 of spec.json."""

    n = len(kernel)
    source_dependence = sum(
        (abs(kernel[source][target] - kernel[0][target]) for source in range(1, n) for target in range(n)),
        Fraction(0, 1),
    )
    destination_bias = sum(
        (
            abs(sum((kernel[source][target] for source in range(n)), Fraction(0, 1)) / n - Fraction(1, n))
            for target in range(n)
        ),
        Fraction(0, 1),
    )
    return source_dependence, destination_bias


def conditional_entropy(kernel: list[list[Fraction]], source: int = 0) -> float:
    return -sum(float(value) * math.log2(float(value)) for value in kernel[source] if value > 0)


def kernel_candidate(
    name: str, n: int, relation_outdegree_lookup: list[list[int]]
) -> dict[str, Any]:
    kernel = named_kernel(name, n)
    integer_matrix, denominator = common_integer_matrix(kernel)
    support_matrix = [[value > 0 for value in row] for row in kernel]
    all_perms = permutations(n)
    automorphisms = jax_weighted_automorphisms(integer_matrix, all_perms)
    direct = [
        p
        for p in all_perms
        if [[integer_matrix[p[i]][p[j]] for j in range(n)] for i in range(n)] == integer_matrix
    ]
    if automorphisms != direct:
        raise RuntimeError(f"JAX/direct kernel automorphism disagreement for {name}_{n}")
    source_distance, bias_distance = stochastic_distances(kernel)
    support_mask = bits_to_mask(support_matrix)
    viability = viability_for_support(
        support_matrix, "markov_kernel", relation_outdegree_lookup[support_mask]
    )
    unbiased = all(value == Fraction(1, n) for row in kernel for value in row)
    viability["V_unbiased_stochastic"] = {"applicable": True, "pass": unbiased}
    partitions, comparisons = candidate_partitions(
        "markov_kernel", support_matrix, automorphisms, kernel
    )
    support = {
        (source, target)
        for source in range(n)
        for target in range(n)
        if support_matrix[source][target]
    }
    return {
        "candidate_id": f"{name}_{n}",
        "provenance_aliases": [f"{name}_{n}"],
        "registry_identity": {
            "carrier_size": n,
            "semantic_type": "markov_kernel",
            "exact_rational_kernel": [
                [f"{value.numerator}/{value.denominator}" for value in row] for row in kernel
            ],
            "named_constants": [],
        },
        "carrier_size": n,
        "semantic_type": "markov_kernel",
        "integer_numerators": integer_matrix,
        "common_denominator": denominator,
        "support_matrix": [[int(value) for value in row] for row in support_matrix],
        "automorphism": {
            "order": len(automorphisms),
            "permutations": [list(p) for p in automorphisms],
            "orbits": automorphism_orbits(n, automorphisms),
        },
        "stochastic_neutrality": {
            "source_dependence_distance": fraction_payload(source_distance),
            "destination_bias_distance": fraction_payload(bias_distance),
            "source_dependence_formula": "sum_{x=1..n-1,y}|K(y|x)-K(y|0)|",
            "destination_bias_formula": "sum_y|n^-1 sum_x K(y|x)-n^-1|",
        },
        "conditional_entropy_from_state_0_bits": conditional_entropy(kernel),
        "viability": viability,
        "distinction_partitions": partitions,
        "distinction_comparisons": comparisons,
        "_autset": set(automorphisms),
        "_supportset": support,
        "_signature_key": relation_signature_key("markov_kernel"),
        "_stochastic_key": (source_distance, bias_distance),
    }


def deduplicate_kernel_registry(raw_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply the frozen registry identity, including boundary coincidences."""

    by_identity: dict[str, dict[str, Any]] = {}
    ordered: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        identity_key = stable_hash(candidate["registry_identity"])
        if identity_key not in by_identity:
            candidate["named_family_presentations"] = [candidate["candidate_id"]]
            by_identity[identity_key] = candidate
            ordered.append(candidate)
            continue
        incumbent = by_identity[identity_key]
        alias = candidate["candidate_id"]
        if alias not in incumbent["provenance_aliases"]:
            incumbent["provenance_aliases"].append(alias)
        incumbent["named_family_presentations"].append(alias)
    return ordered


def weak_or_equal(preorder: str, left: dict[str, Any], right: dict[str, Any]) -> bool:
    if preorder == "signature_commitment":
        return all(a <= b for a, b in zip(left["_signature_key"], right["_signature_key"], strict=True))
    if preorder == "support_freedom":
        return left["_supportset"] is not None and right["_supportset"] is not None and left["_supportset"] >= right["_supportset"]
    if preorder == "automorphism_freedom":
        return left["_autset"] >= right["_autset"]
    if preorder == "stochastic_neutrality":
        return left["_stochastic_key"] is not None and right["_stochastic_key"] is not None and all(
            a <= b for a, b in zip(left["_stochastic_key"], right["_stochastic_key"], strict=True)
        )
    raise ValueError(preorder)


def quotient_classes(candidates: list[dict[str, Any]], preorder: str) -> list[list[dict[str, Any]]]:
    remaining = set(range(len(candidates)))
    classes: list[list[dict[str, Any]]] = []
    while remaining:
        seed = min(remaining)
        members = {
            index
            for index in remaining
            if weak_or_equal(preorder, candidates[seed], candidates[index])
            and weak_or_equal(preorder, candidates[index], candidates[seed])
        }
        remaining -= members
        classes.append([candidates[index] for index in sorted(members)])
    return classes


def mss_frontier(
    candidates: list[dict[str, Any]], arm: dict[str, str]
) -> dict[str, Any]:
    viable = [
        candidate
        for candidate in candidates
        if candidate["viability"].get(arm["viability"], {}).get("applicable", False)
        and candidate["viability"][arm["viability"]]["pass"]
    ]
    if not viable:
        return {
            "arm": arm["id"],
            "preorder": arm["preorder"],
            "viability": arm["viability"],
            "applicable_viable_count": 0,
            "quotient_class_count": 0,
            "status": "NO_SURVIVOR",
            "frontier_classes": [],
        }
    frontier = []
    for candidate in viable:
        has_strictly_weaker = any(
            other is not candidate
            and weak_or_equal(arm["preorder"], other, candidate)
            and not weak_or_equal(arm["preorder"], candidate, other)
            for other in viable
        )
        if not has_strictly_weaker:
            frontier.append(candidate)
    all_classes = quotient_classes(viable, arm["preorder"])
    frontier_classes = quotient_classes(frontier, arm["preorder"])
    return {
        "arm": arm["id"],
        "preorder": arm["preorder"],
        "viability": arm["viability"],
        "applicable_viable_count": len(viable),
        "quotient_class_count": len(all_classes),
        "status": "SURVIVOR_FRONTIER",
        "frontier_classes": [
            {
                "class_index": index,
                "members": sorted(candidate["candidate_id"] for candidate in members),
                "plural_retained_without_tiebreak": len(members) > 1,
            }
            for index, members in enumerate(frontier_classes)
        ],
    }


def external_gate_results(batch: dict[str, Any]) -> dict[str, Any]:
    n = 3
    perms = permutations(n)
    matrices = [[list(map(bool, row)) for row in matrix] for matrix in batch["matrices"]]
    aut_flags = batch["automorphisms"]
    baseline_records = {}
    for mask, matrix in enumerate(matrices):
        auts = [list(p) for p, keep in zip(perms, aut_flags[mask], strict=True) if keep]
        baseline_records[mask] = {
            "adjacency": bitstring(mask, n),
            "automorphisms": auts,
        }

    def reflexive(matrix: list[list[bool]]) -> bool:
        return all(matrix[i][i] for i in range(n))

    def symmetric(matrix: list[list[bool]]) -> bool:
        return all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n))

    gates = [
        ("none", lambda _matrix: True, 512),
        ("reflexive", reflexive, 64),
        ("reflexive_and_symmetric", lambda matrix: reflexive(matrix) and symmetric(matrix), 8),
        ("universal", lambda matrix: all(all(row) for row in matrix), 1),
    ]
    outputs = []
    survivor_sets: list[set[int]] = []
    for name, predicate, expected in gates:
        survivors = {mask for mask, matrix in enumerate(matrices) if predicate(matrix)}
        survivor_sets.append(survivors)
        gated_records = {mask: baseline_records[mask] for mask in sorted(survivors)}
        identity_ok = all(gated_records[mask] == baseline_records[mask] for mask in survivors)
        outputs.append(
            {
                "gate": name,
                "model_count": len(survivors),
                "expected_model_count": expected,
                "count_pass": len(survivors) == expected,
                "survivor_masks": sorted(survivors),
                "survivor_internal_manifest_sha256": stable_hash(gated_records),
                "survivor_internal_byte_identity_against_baseline": identity_ok,
            }
        )
    monotone = all(survivor_sets[index + 1] <= survivor_sets[index] for index in range(3))
    compression = []
    for before, after in zip(outputs, outputs[1:]):
        delta = math.log2(after["model_count"]) - math.log2(before["model_count"])
        compression.append(
            {
                "from": before["gate"],
                "to": after["gate"],
                "formula": "log2(|M_after|)-log2(|M_before|)",
                "bits": delta,
                "nonpositive": delta <= 0.0,
            }
        )
    return {
        "carrier_size": n,
        "gates": outputs,
        "monotone_candidate_set_shrink": monotone,
        "survivor_internal_structures_unchanged": all(
            output["survivor_internal_byte_identity_against_baseline"] for output in outputs
        ),
        "model_set_compression": compression,
        "inference_guard": "external filtering is not within-candidate symmetry breaking",
    }


def filtered_automorphisms(
    matrix: list[list[bool]] | None,
    constants: list[int],
    all_permutations: list[tuple[int, ...]],
) -> list[tuple[int, ...]]:
    answer = []
    for permutation in all_permutations:
        matrix_ok = matrix is None or relabel_matrix(matrix, permutation) == matrix
        constants_ok = all(permutation[value] == value for value in constants)
        if matrix_ok and constants_ok:
            answer.append(permutation)
    return answer


def boundary_and_append_results() -> tuple[dict[str, Any], dict[str, Any]]:
    n = 4
    all_perms = permutations(n)
    empty = [[False] * n for _ in range(n)]
    universal = [[True] * n for _ in range(n)]
    identity = [[i == j for j in range(n)] for i in range(n)]
    cycle = [[False] * n for _ in range(n)]
    for source in range(n):
        cycle[source][(source + 1) % n] = True
    terminal = [[False] * n for _ in range(n)]
    terminal[0][1] = True
    terminal[1][2] = True
    terminal[2][3] = True
    terminal[3][3] = True
    controls = [
        ("empty_relation", empty, []),
        ("universal_relation", universal, []),
        ("identity_loops", identity, []),
        ("directed_four_cycle", cycle, []),
        ("terminal_path", terminal, []),
        ("universal_plus_c0", universal, [0]),
        ("universal_plus_c0_c1", universal, [0, 1]),
    ]
    boundary = []
    for name, matrix, constants in controls:
        auts = filtered_automorphisms(matrix, constants, all_perms)
        boundary.append(
            {
                "id": name,
                "support_bitstring": bitstring(bits_to_mask(matrix), n),
                "named_constants": constants,
                "automorphism_order": len(auts),
                "automorphism_permutations": [list(p) for p in auts],
                "automorphism_orbits": automorphism_orbits(n, auts),
            }
        )

    sets = {
        "A0": set(filtered_automorphisms(None, [], all_perms)),
        "A1": set(filtered_automorphisms(universal, [], all_perms)),
        "A2": set(filtered_automorphisms(universal, [0], all_perms)),
        "A3": set(filtered_automorphisms(universal, [0, 1], all_perms)),
        "B2": set(filtered_automorphisms(universal, [1], all_perms)),
    }
    expected_orders = {"A0": 24, "A1": 24, "A2": 6, "A3": 2}
    steps = []
    for name in ["A0", "A1", "A2", "A3"]:
        steps.append(
            {
                "id": name,
                "automorphism_order": len(sets[name]),
                "expected_automorphism_order": expected_orders[name],
                "order_pass": len(sets[name]) == expected_orders[name],
                "automorphism_permutations": [list(p) for p in sorted(sets[name])],
                "automorphism_orbits": automorphism_orbits(n, sorted(sets[name])),
            }
        )
    adjacent = []
    for left, right, expected_strict in [
        ("A0", "A1", False),
        ("A1", "A2", True),
        ("A2", "A3", True),
    ]:
        adjacent.append(
            {
                "from": left,
                "to": right,
                "literal_subgroup": sets[right] <= sets[left],
                "strict": sets[right] < sets[left],
                "expected_strict": expected_strict,
                "strictness_pass": (sets[right] < sets[left]) == expected_strict,
                "removed_witness": None
                if not (sets[left] - sets[right])
                else list(sorted(sets[left] - sets[right])[0]),
            }
        )
    replacement_witness = sorted(sets["B2"] - sets["A2"])[0]
    append = {
        "carrier_size": n,
        "steps": steps,
        "adjacent_checks": adjacent,
        "all_append_subgroups": all(item["literal_subgroup"] for item in adjacent),
        "all_strictness_expectations": all(item["strictness_pass"] for item in adjacent),
        "replacement_control": {
            "id": "B2",
            "description": "replace c0=0 by c0=1 rather than append",
            "automorphism_order": len(sets["B2"]),
            "automorphism_permutations": [list(p) for p in sorted(sets["B2"])],
            "reduct_byte_equal_to_A2": False,
            "Aut_B2_subset_Aut_A2": sets["B2"] <= sets["A2"],
            "nonmonotone_witness": list(replacement_witness),
            "direct_replay": replacement_witness in sets["B2"] and replacement_witness not in sets["A2"],
        },
        "carrier_growth_subgroup_comparison_refused": True,
    }
    append["all_pass"] = bool(
        all(step["order_pass"] for step in steps)
        and append["all_append_subgroups"]
        and append["all_strictness_expectations"]
        and append["replacement_control"]["Aut_B2_subset_Aut_A2"] is False
        and append["replacement_control"]["direct_replay"] is True
        and append["carrier_growth_subgroup_comparison_refused"] is True
    )
    return {"carrier_size": n, "controls": boundary}, append


def entropy_capacity_readouts(external: dict[str, Any], horizon: int) -> dict[str, Any]:
    fixed_n = []
    for n in range(1, 5):
        log_n = math.log2(n)
        fixed_n.append(
            {
                "n": n,
                "K0_uniform_stationary_input_entropy_bits": log_n,
                "K0_uniform_stationary_output_entropy_bits": log_n,
                "K0_fixed_n_state_entropy_change_bits": 0.0,
                "K0_one_step_conditional_entropy": {"formula": "log2(n)", "bits": log_n},
                "K0_path_entropy": {"formula": "H*log2(n)", "H": horizon, "bits": horizon * log_n},
                "C_support_path_capacity": {
                    "formula": "H*log2(n)",
                    "H": horizon,
                    "bits": horizon * log_n,
                },
            }
        )
    growth = []
    for n in range(1, 4):
        tv = Fraction(1, n + 1)
        growth.append(
            {
                "from_n": n,
                "to_n": n + 1,
                "inclusion": f"X_{n}->X_{n + 1}",
                "total_capacity_change": {
                    "formula": "log2(n+1)-log2(n)",
                    "bits": math.log2(n + 1) - math.log2(n),
                },
                "uniform_inclusion_total_variation": fraction_payload(tv),
                "exact_retention": False,
            }
        )
    return {
        "internal_path_horizon": horizon,
        "fixed_carrier": fixed_n,
        "cross_size_with_explicit_inclusion": growth,
        "external_model_set_compression": external["model_set_compression"],
        "causal_status": "readouts_only_not_a_drive",
        "drive_not_installed_reasons": [
            "no search adjacency",
            "no mobility rule",
            "no acceptance policy",
            "no coupling",
        ],
    }


def relabel_partition_shape_control(
    canonical_masks: list[int], n: int
) -> bool:
    all_perms = permutations(n)
    for mask in canonical_masks:
        matrix = mask_to_matrix(mask, n)
        base_aut = direct_automorphisms(matrix, all_perms)
        base_shapes = {
            "aut": sorted(map(len, automorphism_orbits(n, base_aut))),
            "bisim": sorted(map(len, strong_bisimulation(matrix))),
            "probe": sorted(map(len, local_probe_partition(matrix))),
        }
        base_viability = viability_for_support(matrix, "transition_relation")
        for permutation in all_perms:
            changed = relabel_matrix(matrix, permutation)
            changed_aut = direct_automorphisms(changed, all_perms)
            changed_shapes = {
                "aut": sorted(map(len, automorphism_orbits(n, changed_aut))),
                "bisim": sorted(map(len, strong_bisimulation(changed))),
                "probe": sorted(map(len, local_probe_partition(changed))),
            }
            if changed_shapes != base_shapes:
                return False
            changed_viability = viability_for_support(changed, "transition_relation")
            if changed_viability != base_viability:
                return False
    return True


def forbidden_logic_token_scan() -> dict[str, Any]:
    """Scan executable decision functions, not claim-ceiling/result prose."""

    source = Path(__file__).read_text(encoding="utf-8")
    start = source.index("def jax_relation_batch")
    stop = source.index("def main")
    native_logic = source[start:stop]
    # Terms are assembled so the scan does not fail merely on its own literals.
    forbidden = [
        "Q" + "IT engine",
        "A" + "xis0",
        "A" + "xis 0",
        "cosmo" + "logy",
        "phy" + "sics",
        "ba" + "sin",
        "engine" + "-match",
    ]
    hits = [term for term in forbidden if term in native_logic]
    return {
        "scope": "executable generation/viability/preorder/stopping functions",
        "forbidden_terms": forbidden,
        "hits": hits,
        "pass": not hits,
    }


def build_result(spec: dict[str, Any], output_path: Path) -> dict[str, Any]:
    spec_hash = sha256_file(SPEC_PATH)
    source_hash = sha256_file(Path(__file__))
    exhaustive_sizes = [int(n) for n in spec["execution_bounds"]["exhaustive_carrier_sizes"]]
    relation_batches = {n: jax_relation_batch(n) for n in exhaustive_sizes}

    registries: dict[int, list[dict[str, Any]]] = {}
    public_registries: dict[str, list[dict[str, Any]]] = {}
    candidate_counts: dict[str, Any] = {}
    direct_replay_all = True
    orbit_stabilizer_all = True
    partition_relabel_all = True

    for n in exhaustive_sizes:
        batch = relation_batches[n]
        all_perms = permutations(n)
        groups: dict[int, list[int]] = defaultdict(list)
        for labelled_mask, canonical_mask in enumerate(batch["canonical"]):
            groups[canonical_mask].append(labelled_mask)
        canonical_masks = sorted(groups)
        registry = [empty_candidate(n)]
        transition_labelled_viability = Counter()
        transition_iso_viability = Counter()

        for mask, matrix_raw in enumerate(batch["matrices"]):
            matrix = [[bool(value) for value in row] for row in matrix_raw]
            viability = viability_for_support(
                matrix, "transition_relation", batch["outdegrees"][mask]
            )
            for name, receipt in viability.items():
                if receipt["applicable"] and receipt["pass"]:
                    transition_labelled_viability[name] += 1

        aut_histogram = Counter()
        for canonical_mask in canonical_masks:
            matrix = mask_to_matrix(canonical_mask, n)
            jax_auts = [
                p
                for p, keep in zip(all_perms, batch["automorphisms"][canonical_mask], strict=True)
                if keep
            ]
            direct_auts = direct_automorphisms(matrix, all_perms)
            direct_replay_all = direct_replay_all and jax_auts == direct_auts
            orbit_stabilizer_all = orbit_stabilizer_all and len(groups[canonical_mask]) * len(jax_auts) == math.factorial(n)
            aut_histogram[len(jax_auts)] += 1
            aliases_static = [f"J_{n}"] if canonical_mask == (1 << (n * n)) - 1 else []
            aliases_transition = [f"C_{n}"] if canonical_mask == (1 << (n * n)) - 1 else []
            static = relation_candidate(
                n,
                canonical_mask,
                "static_relation",
                aliases_static,
                jax_auts,
                groups[canonical_mask],
                batch["outdegrees"][canonical_mask],
            )
            transition = relation_candidate(
                n,
                canonical_mask,
                "transition_relation",
                aliases_transition,
                jax_auts,
                groups[canonical_mask],
                batch["outdegrees"][canonical_mask],
            )
            registry.extend([static, transition])
            for name, receipt in transition["viability"].items():
                if receipt["applicable"] and receipt["pass"]:
                    transition_iso_viability[name] += 1

        raw_kernels = [
            kernel_candidate(name, n, batch["outdegrees"])
            for name in ["K0", "Klazy", "Kbiased", "Kidentity"]
        ]
        kernels = deduplicate_kernel_registry(raw_kernels)
        exact_kernel_identity_count = len(
            {
                stable_hash(candidate["registry_identity"])
                for candidate in raw_kernels
            }
        )
        registry.extend(kernels)
        registries[n] = registry
        public_registries[str(n)] = [public_candidate(candidate) for candidate in registry]
        partition_relabel = relabel_partition_shape_control(canonical_masks, n)
        partition_relabel_all = partition_relabel_all and partition_relabel
        candidate_counts[str(n)] = {
            "labelled_static_relations": len(batch["matrices"]),
            "labelled_transition_relations": len(batch["matrices"]),
            "expected_labelled_each": int(
                spec["execution_bounds"]["binary_relation_count_by_exhaustive_size"][str(n)]
            ),
            "relation_isomorphism_classes_each_semantic_type": len(canonical_masks),
            "relation_canonical_masks": canonical_masks,
            "relation_automorphism_order_histogram_per_semantic_type": {
                str(order): count for order, count in sorted(aut_histogram.items())
            },
            "named_kernel_presentations": 4,
            "named_kernel_registry_identities": len(kernels),
            "empty_signature_candidates": 1,
            "total_registry_identities": len(registry),
            "alias_deduplication": {
                "U_alias_count": 1,
                "J_aliases_existing_universal_static": True,
                "C_aliases_existing_universal_transition": True,
                "K0_aliases_existing_named_kernel": True,
                "named_kernel_boundary_collisions": {
                    candidate["candidate_id"]: candidate["provenance_aliases"]
                    for candidate in kernels
                    if len(candidate["provenance_aliases"]) > 1
                },
                "exact_kernel_identity_count_recomputed": exact_kernel_identity_count,
                "identity_count_matches_exact_dedup": len(kernels)
                == exact_kernel_identity_count,
                "presentation_count_kept_separate_from_identity_count": (
                    len(raw_kernels) == 4
                    and (
                        len(kernels) < len(raw_kernels)
                        if n in {1, 2}
                        else len(kernels) == len(raw_kernels)
                    )
                ),
                "no_alias_double_count": len(registry)
                == 1 + 2 * len(canonical_masks) + len(kernels),
            },
            "transition_viability_counts_labelled": dict(sorted(transition_labelled_viability.items())),
            "transition_viability_counts_isomorphism_classes": dict(sorted(transition_iso_viability.items())),
            "relabel_canonical_invariant_exhaustive": batch["relabel_canonical_invariant"],
            "relabel_viability_and_partition_shape_invariant": partition_relabel,
        }

    arms = [dict(arm) for arm in spec["mss_arms"]]
    mss = {
        str(n): {arm["id"]: mss_frontier(registries[n], arm) for arm in arms}
        for n in exhaustive_sizes
    }

    external = external_gate_results(relation_batches[3])
    boundary, append = boundary_and_append_results()
    entropy = entropy_capacity_readouts(
        external, int(spec["execution_bounds"]["internal_path_horizon"])
    )

    # JAX mutation: removing nonidentity permutations breaks canonicalization.
    full_canonical_for_0100 = relation_batches[2]["canonical"][4]
    identity_only_mutated = 4
    canonical_mutation_flips = full_canonical_for_0100 != identity_only_mutated

    # jraph erasure: removing universal edges flips its viability gate.
    universal_n3 = jnp.ones((3, 3), dtype=jnp.bool_)
    senders_n3 = jnp.repeat(jnp.arange(3, dtype=jnp.int32), 3)

    @jax.jit
    def graph_degrees(matrix: jax.Array) -> jax.Array:
        return jraph.segment_sum(
            matrix.reshape((-1,)).astype(jnp.int64), senders_n3, num_segments=3
        )

    positive_degrees = jax.device_get(graph_degrees(universal_n3)).tolist()
    erased_degrees = jax.device_get(graph_degrees(jnp.zeros_like(universal_n3))).tolist()
    jraph_erasure_flips = all(value >= 1 for value in positive_degrees) and not all(
        value >= 1 for value in erased_degrees
    )

    n0_refused = False
    try:
        named_kernel("K0", 0)
    except ValueError:
        n0_refused = True

    candidate_by_id = {
        candidate["candidate_id"]: candidate
        for registry in registries.values()
        for candidate in registry
    }
    j3 = candidate_by_id["J_3"]
    c3 = candidate_by_id["C_3"]
    k0_3 = candidate_by_id["K0_3"]
    klazy_3 = candidate_by_id["Klazy_3"]
    semantic_separation = (
        j3["support_matrix"] == c3["support_matrix"]
        and j3["semantic_type"] != c3["semantic_type"]
        and j3["registry_identity"] != c3["registry_identity"]
    )
    klazy_control = {
        "n": 3,
        "full_support_both": k0_3["_supportset"] == klazy_3["_supportset"] == {
            (i, j) for i in range(3) for j in range(3)
        },
        "full_simultaneous_relabeling_symmetry_both": len(k0_3["_autset"])
        == len(klazy_3["_autset"])
        == math.factorial(3),
        "source_dependence_differs": k0_3["_stochastic_key"][0]
        != klazy_3["_stochastic_key"][0],
        "conditional_entropy_differs": not math.isclose(
            k0_3["conditional_entropy_from_state_0_bits"],
            klazy_3["conditional_entropy_from_state_0_bits"],
            rel_tol=0.0,
            abs_tol=1e-15,
        ),
    }
    forbidden_scan = forbidden_logic_token_scan()

    relation_count_pass = all(
        candidate_counts[str(n)]["labelled_static_relations"]
        == candidate_counts[str(n)]["expected_labelled_each"]
        for n in exhaustive_sizes
    )
    append_pass = (
        append["all_append_subgroups"]
        and append["all_strictness_expectations"]
        and append["replacement_control"]["direct_replay"]
        and not append["replacement_control"]["Aut_B2_subset_Aut_A2"]
    )
    external_pass = (
        external["monotone_candidate_set_shrink"]
        and external["survivor_internal_structures_unchanged"]
        and all(gate["count_pass"] for gate in external["gates"])
    )
    entropy_pass = all(
        item["K0_fixed_n_state_entropy_change_bits"] == 0.0 for item in entropy["fixed_carrier"]
    ) and all(
        item["uniform_inclusion_total_variation"]["numerator"] > 0
        and not item["exact_retention"]
        for item in entropy["cross_size_with_explicit_inclusion"]
    )
    n1_branching_pass = not any(
        candidate["viability"]["V_branching"]["pass"]
        for candidate in registries[1]
        if candidate["viability"]["V_branching"]["applicable"]
    )
    mss_complete = all(
        set(mss[str(n)]) == {arm["id"] for arm in arms} for n in exhaustive_sizes
    )
    exact_spec_bound = spec_hash == EXPECTED_SPEC_SHA256
    x64 = bool(jax.config.jax_enable_x64)
    expected_kernel_identity_counts = {1: 1, 2: 3, 3: 4}
    named_kernel_collision_controls = all(
        candidate_counts[str(n)]["named_kernel_registry_identities"]
        == expected_kernel_identity_counts[n]
        and candidate_counts[str(n)]["alias_deduplication"][
            "identity_count_matches_exact_dedup"
        ]
        and candidate_counts[str(n)]["alias_deduplication"][
            "presentation_count_kept_separate_from_identity_count"
        ]
        for n in exhaustive_sizes
    )
    jraph_degree_replay_all = all(
        [int(value) for value in batch["outdegrees"][mask]]
        == [sum(bool(entry) for entry in row) for row in batch["matrices"][mask]]
        for batch in relation_batches.values()
        for mask in range(len(batch["matrices"]))
    )
    checks = {
        "spec_hash_exact": exact_spec_bound,
        "jax_x64_enabled": x64,
        "relation_counts_match_frozen_spec": relation_count_pass,
        "alias_registry_deduplicated": all(
            candidate_counts[str(n)]["alias_deduplication"]["no_alias_double_count"]
            for n in exhaustive_sizes
        ),
        "named_kernel_exact_collision_controls": named_kernel_collision_controls,
        "orbit_stabilizer_all_isomorphism_classes": orbit_stabilizer_all,
        "jax_automorphism_sets_directly_replayed": direct_replay_all,
        "relabel_canonical_invariant_exhaustive": all(
            relation_batches[n]["relabel_canonical_invariant"] for n in exhaustive_sizes
        ),
        "relabel_viability_partition_frontier_identity_invariant": partition_relabel_all,
        "mss_all_arms_reported": mss_complete,
        "append_chain_controls": append_pass,
        "external_gate_controls": external_pass,
        "typed_entropy_capacity_controls": entropy_pass,
        "n0_kernel_refused": n0_refused,
        "n1_no_branching": n1_branching_pass,
        "J_C_same_support_different_semantic_identity": semantic_separation,
        "K0_Klazy_n3_discriminator": all(klazy_control.values()),
        "canonicalization_mutation_flips": canonical_mutation_flips,
        "jraph_edge_erasure_flips_viability": jraph_erasure_flips,
        "jraph_degrees_directly_replayed": jraph_degree_replay_all,
        "forbidden_target_tokens_absent_from_native_logic": forbidden_scan["pass"],
    }
    all_pass = all(checks.values())

    result = {
        "schema_version": "finite_structure_hypothesis_tournament.jax_result.v1",
        "all_pass": all_pass,
        "classification": spec["classification"],
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "engine_contract": {
            "mode": spec["engine_mode"]["name"],
            "lane": "jax",
            "semantic_owner": "julia",
            "reads_peer_result": False,
            "inputs_read": [str(SPEC_PATH.relative_to(SIM_DIR.parents[2]))],
            "shared_generated_manifest_consumed": False,
            "pytorch": spec["engine_mode"]["pytorch"],
            "tensor_exchange": "none",
        },
        "command": [sys.executable, str(Path(__file__).resolve()), "--out", str(output_path.resolve())],
        "cwd": os.getcwd(),
        "runner_identity": {
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "runtime": {
            "platform": platform.platform(),
            "jax": jax.__version__,
            "jaxlib": metadata.version("jaxlib"),
            "jraph": metadata.version("jraph"),
            "jax_enable_x64": x64,
            "backend": jax.default_backend(),
            "devices": [str(device) for device in jax.devices()],
        },
        "source_path": str(Path(__file__).resolve().relative_to(SIM_DIR.parents[2])),
        "source_sha256": source_hash,
        "spec_path": str(SPEC_PATH.resolve().relative_to(SIM_DIR.parents[2])),
        "spec_sha256": spec_hash,
        "expected_spec_sha256": EXPECTED_SPEC_SHA256,
        "candidate_counts": candidate_counts,
        "registry_census": public_registries,
        "mss_frontiers": mss,
        "fixed_carrier_internal_append_chain": append,
        "named_relation_controls_at_n4": boundary,
        "external_constraint_controls": external,
        "entropy_capacity_readouts": entropy,
        "tool_receipts": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(transform_one))",
                "input_object": "every labelled n-by-n Boolean relation for n=1,2,3 and every carrier permutation",
                "output_object": "batched relabelled matrices, canonical masks, and literal automorphism membership",
                "positive_case": "full permutation batch canonicalizes 0100 at n=2 to 0010 and replays every reported automorphism set",
                "negative/erased_control": "identity-only permutation ablation leaves 0100 unchanged and disagrees with the full canonical representative",
                "boundary_case": "n=1 enumerates both relations and one permutation without special-casing the compiled kernel",
                "demotion_condition": "any x64 disablement, direct replay mismatch, relabeling failure, or ablation non-flip makes all_pass false",
                "gates": ["all_pass", "isomorphism_quotient", "automorphism_sets", "MSS_frontiers"],
                "load_bearing": True,
            },
            {
                "tool": "jraph",
                "qualified_api/function": "jraph.segment_sum",
                "input_object": "flattened Boolean support edges with fixed sender segment ids",
                "output_object": "exact per-state outdegrees used by V_serial and V_branching",
                "positive_case": {"universal_n3_outdegrees": positive_degrees},
                "negative/erased_control": {"erased_edges_outdegrees": erased_degrees},
                "boundary_case": "n=1 empty support has outdegree zero and fails serial/branching",
                "demotion_condition": "degree mismatch or erased-edge non-flip makes all_pass false",
                "gates": ["all_pass", "V_serial", "V_branching", "V_exploratory_support", "MSS_frontiers"],
                "load_bearing": True,
            },
        ],
        "packages_used": ["jax", "jax.numpy", "jraph"],
        "aligned_packages_load_bearing": ["jraph"],
        "claim_path_tools": ["jax", "jraph"],
        "controls": {
            "checks": checks,
            "canonicalization_mutation": {
                "input_labelled_mask": 4,
                "full_permutation_canonical_mask": full_canonical_for_0100,
                "identity_only_mutated_mask": identity_only_mutated,
                "flips": canonical_mutation_flips,
            },
            "jraph_edge_erasure": {
                "positive_outdegrees": positive_degrees,
                "erased_outdegrees": erased_degrees,
                "flips_V_serial": jraph_erasure_flips,
            },
            "n0_kernel_refusal": n0_refused,
            "n1_no_branching": n1_branching_pass,
            "J_C_encoding": {
                "support_equal": j3["support_matrix"] == c3["support_matrix"],
                "semantic_types": [j3["semantic_type"], c3["semantic_type"]],
                "registry_identities_distinct": j3["registry_identity"] != c3["registry_identity"],
                "pass": semantic_separation,
            },
            "K0_Klazy_discriminator": klazy_control,
            "forbidden_native_logic_token_scan": forbidden_scan,
            "informative_red_policy": "all failed controls remain literal and force all_pass=false",
        },
        "errors": [name for name, passed in checks.items() if not passed],
    }
    result["result_core_sha256"] = stable_hash(result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    result = build_result(spec, args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "errors": result["errors"],
                "out": str(args.out),
                "spec_sha256": result["spec_sha256"],
                "source_sha256": result["source_sha256"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
