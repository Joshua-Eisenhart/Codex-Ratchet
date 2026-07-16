#!/usr/bin/env python3
"""Fail-closed controller for the frozen finite-structure tournament.

This is the authoritative local result gate.  It reads fixed input paths,
strictly parses every JSON receipt, independently recomputes the small finite
oracles, compares Julia and JAX semantic objects, replays the complete mixed
SAT/UNSAT solver matrix, and exercises corruption controls in memory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
import os
import platform
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable


BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]
SPEC_PATH = BASE / "spec.json"
CARD_PATH = BASE / "wizard_v4_3_object_card.json"
PREREG_PATH = BASE / "preregistration_receipt.json"
PREREG_SOURCE = BASE / "validate_preregistration.py"
JULIA_SOURCE = BASE / "run_julia.jl"
JULIA_RESULT = BASE / "results" / "julia_result.json"
JAX_SOURCE = BASE / "run_jax.py"
JAX_RESULT = BASE / "results" / "jax_result.json"
SMT_SOURCE = BASE / "run_smt.py"
SMT_RESULT = BASE / "results" / "smt_result.json"
DEFAULT_OUT = BASE / "results" / "controller_result.json"
EXPECTED_SPEC_SHA256 = "060177cae89e23e19f05c6ed7f10fe729bb636db14e0d1caaab66770872efae3"
FLOAT_TOLERANCE = 1e-12


class GateError(ValueError):
    pass


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return sha256_bytes(raw)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise GateError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_nonfinite_constant(token: str) -> Any:
    raise GateError(f"non-finite JSON constant: {token}")


def assert_finite(node: Any, path: str = "$") -> None:
    if isinstance(node, float) and not math.isfinite(node):
        raise GateError(f"non-finite float at {path}")
    if isinstance(node, dict):
        for key, value in node.items():
            assert_finite(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            assert_finite(value, f"{path}[{index}]")


def strict_load_bytes(raw: bytes) -> dict[str, Any]:
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite_constant,
    )
    if not isinstance(value, dict):
        raise GateError("top-level JSON value must be an object")
    assert_finite(value)
    json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return value


def strict_load(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved = path.resolve()
    if path.is_symlink():
        raise GateError(f"symlink input refused: {path}")
    try:
        resolved.relative_to(REPO.resolve())
    except ValueError as exc:
        raise GateError(f"input escapes worktree: {resolved}") from exc
    raw = path.read_bytes()
    value = strict_load_bytes(raw)
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return value, {
        "path": str(path.relative_to(REPO)),
        "raw_sha256": sha256_bytes(raw),
        "canonical_sha256": sha256_bytes(canonical),
        "bytes": len(raw),
    }


class Checks:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, name: str, passed: bool, detail: Any) -> None:
        self.rows.append({"name": name, "pass": bool(passed), "detail": detail})

    @property
    def errors(self) -> list[str]:
        return [str(row["name"]) for row in self.rows if not row["pass"]]


def canonical_fraction(value: Any) -> str:
    if isinstance(value, dict) and "exact" in value:
        value = value["exact"]
    fraction = Fraction(str(value))
    return f"{fraction.numerator}/{fraction.denominator}"


def canonical_permutations(rows: Any, carrier_size: int | None = None) -> list[list[int]]:
    values = [tuple(int(item) for item in row) for row in rows]
    if len(values) != len(set(values)):
        raise GateError("duplicate permutation")
    if carrier_size is None:
        if not values:
            raise GateError("automorphism set must contain the identity")
        carrier_size = len(values[0])
    expected = list(range(carrier_size))
    if any(len(row) != carrier_size or sorted(row) != expected for row in values):
        raise GateError("malformed carrier permutation")
    return [list(row) for row in sorted(values)]


def canonical_partition(blocks: Any, carrier_size: int | None = None) -> list[list[int]]:
    normalized = [tuple(sorted(int(item) for item in block)) for block in blocks]
    if any(not block for block in normalized):
        raise GateError("partition contains an empty block")
    flat = [item for block in normalized for item in block]
    if len(flat) != len(set(flat)):
        raise GateError("partition repeats a state")
    if carrier_size is not None and sorted(flat) != list(range(carrier_size)):
        raise GateError("partition does not cover the carrier exactly")
    return [list(block) for block in sorted(normalized)]


def witness_states(value: Any) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("states")
    if not isinstance(value, list):
        raise GateError("distinction witness must contain a state pair")
    return sorted(int(item) for item in value)


def normalize_comparisons(rows: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in rows:
        key = f"{row['left']}|{row['right']}"
        if key in result:
            raise GateError(f"duplicate distinction comparison: {key}")
        result[key] = {
            "equal": bool(row["equal"]),
            "left_refines_right": bool(row["left_refines_right"]),
            "right_refines_left": bool(row["right_refines_left"]),
            "witness_states": witness_states(row.get("disagreement_witness")),
        }
    return dict(sorted(result.items()))


def normalize_julia_candidate(row: dict[str, Any]) -> dict[str, Any]:
    carrier_size = int(row["carrier_size"])
    kernel = row.get("exact_kernel_rows")
    payload = (
        [[canonical_fraction(value) for value in kernel_row] for kernel_row in kernel]
        if kernel is not None
        else row.get("canonical_adjacency")
    )
    stochastic = row.get("stochastic_neutrality_key")
    return {
        "id": row["id"],
        "carrier_size": carrier_size,
        "semantic_type": row["semantic_type"],
        "payload": payload,
        "named_constants": [int(value) for value in row.get("named_constants", [])],
        "automorphism_order": int(row["automorphism_order"]),
        "automorphism_permutations": canonical_permutations(row["automorphism_permutations"], carrier_size),
        "distinction_partitions": {
            key: canonical_partition(value, carrier_size)
            for key, value in sorted(row["distinction_partitions"].items())
        },
        "distinction_comparisons": normalize_comparisons(row["distinction_comparisons"]),
        "viability": dict(sorted(row["viability"].items())),
        "stochastic_neutrality": (
            [canonical_fraction(value) for value in stochastic] if stochastic is not None else None
        ),
    }


def normalize_jax_candidate(row: dict[str, Any]) -> dict[str, Any]:
    carrier_size = int(row["carrier_size"])
    identity = row["registry_identity"]
    payload = identity.get("exact_rational_kernel", identity.get("canonical_adjacency"))
    if isinstance(payload, list):
        payload = [[canonical_fraction(value) for value in kernel_row] for kernel_row in payload]
    viability = {
        key: (bool(value["pass"]) if value["applicable"] else None)
        for key, value in row["viability"].items()
    }
    stochastic = row.get("stochastic_neutrality")
    stochastic_key = None
    if stochastic is not None:
        stochastic_key = [
            canonical_fraction(stochastic["source_dependence_distance"]),
            canonical_fraction(stochastic["destination_bias_distance"]),
        ]
    return {
        "id": row["candidate_id"],
        "carrier_size": carrier_size,
        "semantic_type": row["semantic_type"],
        "payload": payload,
        "named_constants": [int(value) for value in identity.get("named_constants", [])],
        "automorphism_order": int(row["automorphism"]["order"]),
        "automorphism_permutations": canonical_permutations(row["automorphism"]["permutations"], carrier_size),
        "distinction_partitions": {
            key: canonical_partition(value, carrier_size)
            for key, value in sorted(row["distinction_partitions"].items())
        },
        "distinction_comparisons": normalize_comparisons(row["distinction_comparisons"]),
        "viability": dict(sorted(viability.items())),
        "stochastic_neutrality": stochastic_key,
    }


def normalized_candidates(julia: dict[str, Any], jax: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    julia_rows = [row for row in julia["candidates"] if int(row["carrier_size"]) <= 3]
    jax_rows = [row for n in ("1", "2", "3") for row in jax["registry_census"][n]]
    julia_map = {row["id"]: normalize_julia_candidate(row) for row in julia_rows}
    jax_map = {row["candidate_id"]: normalize_jax_candidate(row) for row in jax_rows}
    if len(julia_map) != len(julia_rows) or len(jax_map) != len(jax_rows):
        raise GateError("duplicate candidate ID")
    return julia_map, jax_map


def canonical_classes(classes: Any) -> list[list[str]]:
    normalized = [tuple(sorted(str(item) for item in row)) for row in classes]
    return [list(row) for row in sorted(normalized)]


def normalize_mss(julia: dict[str, Any], jax: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    julia_map: dict[str, Any] = {}
    for row in julia["mss_arms"]:
        n = int(row["carrier_size"])
        if n > 3:
            continue
        key = f"{n}|{row['arm_id']}"
        julia_map[key] = {
            "preorder": row["preorder"],
            "viability": row["viability"],
            "applicable_viable_count": int(row["applicable_viable_candidate_count"]),
            "quotient_class_count": len(row["viable_equivalence_classes"]),
            "frontier_classes": canonical_classes(row["frontier_classes"]),
        }
    jax_map: dict[str, Any] = {}
    for n in ("1", "2", "3"):
        for arm_id, row in jax["mss_frontiers"][n].items():
            key = f"{n}|{arm_id}"
            jax_map[key] = {
                "preorder": row["preorder"],
                "viability": row["viability"],
                "applicable_viable_count": int(row["applicable_viable_count"]),
                "quotient_class_count": int(row["quotient_class_count"]),
                "frontier_classes": canonical_classes(
                    [entry["members"] for entry in row["frontier_classes"]]
                ),
            }
    return julia_map, jax_map


def normalize_julia_mss_for_sizes(
    julia: dict[str, Any], carrier_sizes: set[int]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for row in julia["mss_arms"]:
        n = int(row["carrier_size"])
        if n not in carrier_sizes:
            continue
        key = f"{n}|{row['arm_id']}"
        if key in result:
            raise GateError(f"duplicate Julia MSS arm: {key}")
        result[key] = {
            "preorder": row["preorder"],
            "viability": row["viability"],
            "applicable_viable_count": int(row["applicable_viable_candidate_count"]),
            "quotient_class_count": len(row["viable_equivalence_classes"]),
            "frontier_classes": canonical_classes(row["frontier_classes"]),
        }
    return result


def matrix_from_mask(mask: int, n: int) -> list[list[bool]]:
    text = format(mask, f"0{n*n}b")
    return [[text[i * n + j] == "1" for j in range(n)] for i in range(n)]


def transformed_mask(matrix: list[list[bool]], permutation: tuple[int, ...]) -> int:
    bits = "".join(
        "1" if matrix[permutation[i]][permutation[j]] else "0"
        for i in range(len(matrix))
        for j in range(len(matrix))
    )
    return int(bits, 2)


def persistent_support(matrix: list[list[bool]]) -> bool:
    n = len(matrix)
    reach = [row[:] for row in matrix]
    for pivot in range(n):
        for left in range(n):
            for right in range(n):
                reach[left][right] = reach[left][right] or (
                    reach[left][pivot] and reach[pivot][right]
                )
    return all(reach[state][state] for state in range(n))


def oracle_relation_census(n: int) -> dict[str, Any]:
    perms = list(itertools.permutations(range(n)))
    groups: dict[int, list[int]] = {}
    labelled_viability = {name: 0 for name in ("V_registered", "V_serial", "V_persistent_support", "V_branching", "V_exploratory_support")}
    for mask in range(1 << (n * n)):
        matrix = matrix_from_mask(mask, n)
        canonical = min(transformed_mask(matrix, permutation) for permutation in perms)
        groups.setdefault(canonical, []).append(mask)
        serial = all(any(row) for row in matrix)
        persistent = persistent_support(matrix)
        branching = n > 1 and all(sum(row) >= 2 for row in matrix)
        values = {
            "V_registered": True,
            "V_serial": serial,
            "V_persistent_support": persistent,
            "V_branching": branching,
            "V_exploratory_support": persistent and branching,
        }
        for key, passed in values.items():
            labelled_viability[key] += int(passed)
    histogram: dict[str, int] = {}
    iso_viability = {name: 0 for name in labelled_viability}
    for canonical in sorted(groups):
        matrix = matrix_from_mask(canonical, n)
        aut_order = sum(transformed_mask(matrix, permutation) == canonical for permutation in perms)
        histogram[str(aut_order)] = histogram.get(str(aut_order), 0) + 1
        serial = all(any(row) for row in matrix)
        persistent = persistent_support(matrix)
        branching = n > 1 and all(sum(row) >= 2 for row in matrix)
        values = {
            "V_registered": True,
            "V_serial": serial,
            "V_persistent_support": persistent,
            "V_branching": branching,
            "V_exploratory_support": persistent and branching,
        }
        for key, passed in values.items():
            iso_viability[key] += int(passed)
    return {
        "labelled_count": 1 << (n * n),
        "canonical_masks": sorted(groups),
        "isomorphism_class_count": len(groups),
        "automorphism_order_histogram": dict(sorted(histogram.items(), key=lambda row: int(row[0]))),
        "labelled_viability": {key: value for key, value in labelled_viability.items() if value},
        "isomorphism_class_viability": {key: value for key, value in iso_viability.items() if value},
    }


def matrix_from_payload(payload: Any, n: int, semantic_type: str) -> list[list[bool]] | None:
    if semantic_type == "empty_signature":
        return None
    if semantic_type in {"static_relation", "transition_relation"}:
        if not isinstance(payload, str) or len(payload) != n * n or set(payload) - {"0", "1"}:
            raise GateError("malformed canonical adjacency")
        return [[payload[i * n + j] == "1" for j in range(n)] for i in range(n)]
    if semantic_type == "markov_kernel":
        if not isinstance(payload, list) or len(payload) != n or any(len(row) != n for row in payload):
            raise GateError("malformed exact kernel")
        fractions = [[Fraction(value) for value in row] for row in payload]
        if any(any(value < 0 for value in row) or sum(row) != 1 for row in fractions):
            raise GateError("kernel rows must be exact probability distributions")
        return [[value > 0 for value in row] for row in fractions]
    raise GateError(f"unknown semantic type: {semantic_type}")


def direct_automorphisms_for_payload(
    payload: Any,
    n: int,
    semantic_type: str,
    named_constants: list[int],
) -> list[list[int]]:
    if semantic_type == "empty_signature":
        weighted: Any = None
    elif semantic_type in {"static_relation", "transition_relation"}:
        weighted = matrix_from_payload(payload, n, semantic_type)
    else:
        weighted = [[Fraction(value) for value in row] for row in payload]
    result: list[list[int]] = []
    for permutation in itertools.permutations(range(n)):
        if any(permutation[value] != value for value in named_constants):
            continue
        if weighted is None or all(
            weighted[i][j] == weighted[permutation[i]][permutation[j]]
            for i in range(n)
            for j in range(n)
        ):
            result.append(list(permutation))
    return result


def orbits_from_permutations(n: int, permutations_rows: list[list[int]]) -> list[list[int]]:
    remaining = set(range(n))
    blocks: list[list[int]] = []
    while remaining:
        seed = min(remaining)
        block = {permutation[seed] for permutation in permutations_rows}
        blocks.append(sorted(block))
        remaining -= block
    return canonical_partition(blocks, n)


def local_probe_partition(matrix: list[list[bool]]) -> list[list[int]]:
    n = len(matrix)
    outdegrees = [sum(row) for row in matrix]
    indegrees = [sum(matrix[source][target] for source in range(n)) for target in range(n)]
    fingerprints: dict[tuple[Any, ...], list[int]] = {}
    for state in range(n):
        successors = [target for target in range(n) if matrix[state][target]]
        predecessors = [source for source in range(n) if matrix[source][state]]
        fingerprint = (
            matrix[state][state],
            indegrees[state],
            outdegrees[state],
            tuple(sorted(outdegrees[target] for target in successors)),
            tuple(sorted(indegrees[source] for source in predecessors)),
        )
        fingerprints.setdefault(fingerprint, []).append(state)
    return canonical_partition(list(fingerprints.values()), n)


def strong_bisimulation_partition(matrix: list[list[bool]]) -> list[list[int]]:
    n = len(matrix)
    relation = {(left, right) for left in range(n) for right in range(n)}
    changed = True
    while changed:
        changed = False
        next_relation: set[tuple[int, int]] = set()
        for left, right in relation:
            left_successors = [target for target in range(n) if matrix[left][target]]
            right_successors = [target for target in range(n) if matrix[right][target]]
            left_matches = all(
                any((left_target, right_target) in relation for right_target in right_successors)
                for left_target in left_successors
            )
            right_matches = all(
                any((left_target, right_target) in relation for left_target in left_successors)
                for right_target in right_successors
            )
            if left_matches and right_matches:
                next_relation.add((left, right))
            else:
                changed = True
        relation = next_relation
    blocks: list[list[int]] = []
    unseen = set(range(n))
    while unseen:
        seed = min(unseen)
        block = sorted(state for state in range(n) if (seed, state) in relation and (state, seed) in relation)
        if not block:
            block = [seed]
        blocks.append(block)
        unseen -= set(block)
    return canonical_partition(blocks, n)


def kernel_row_partition(payload: list[list[str]]) -> list[list[int]]:
    groups: dict[tuple[str, ...], list[int]] = {}
    for index, row in enumerate(payload):
        key = tuple(canonical_fraction(value) for value in row)
        groups.setdefault(key, []).append(index)
    return canonical_partition(list(groups.values()), len(payload))


def partition_refines(left: list[list[int]], right: list[list[int]]) -> bool:
    right_sets = [set(block) for block in right]
    return all(any(set(block) <= container for container in right_sets) for block in left)


def validate_distinction_comparisons(
    partitions: dict[str, list[list[int]]],
    comparisons: dict[str, Any],
) -> bool:
    expected_pairs = {
        f"{left}|{right}"
        for index, left in enumerate(sorted(partitions))
        for right in sorted(partitions)[index + 1 :]
    }
    if set(comparisons) != expected_pairs:
        return False
    for key, receipt in comparisons.items():
        left_name, right_name = key.split("|", 1)
        left = partitions[left_name]
        right = partitions[right_name]
        equal = left == right
        left_refines = partition_refines(left, right)
        right_refines = partition_refines(right, left)
        if (
            receipt["equal"] is not equal
            or receipt["left_refines_right"] is not left_refines
            or receipt["right_refines_left"] is not right_refines
        ):
            return False
        witness = receipt["witness_states"]
        if equal:
            if witness is not None:
                return False
            continue
        if not isinstance(witness, list) or len(witness) != 2 or witness[0] == witness[1]:
            return False
        first, second = witness
        left_same = any(first in block and second in block for block in left)
        right_same = any(first in block and second in block for block in right)
        if left_same == right_same:
            return False
    return True


def expected_kernel_payloads(n: int) -> dict[str, list[list[str]]]:
    uniform = [[canonical_fraction(Fraction(1, n)) for _ in range(n)] for _ in range(n)]
    lazy = (
        uniform
        if n == 1
        else [
            [
                canonical_fraction(Fraction(1, 2) if source == target else Fraction(1, 2 * (n - 1)))
                for target in range(n)
            ]
            for source in range(n)
        ]
    )
    biased_row = [canonical_fraction(Fraction(2 * (target + 1), n * (n + 1))) for target in range(n)]
    biased = [biased_row[:] for _ in range(n)]
    identity = [
        [canonical_fraction(Fraction(int(source == target), 1)) for target in range(n)]
        for source in range(n)
    ]
    presentations = {
        f"K0_{n}": uniform,
        f"Klazy_{n}": lazy,
        f"Kbiased_{n}": biased,
        f"Kidentity_{n}": identity,
    }
    result: dict[str, list[list[str]]] = {}
    for candidate_id in (f"K0_{n}", f"Klazy_{n}", f"Kbiased_{n}", f"Kidentity_{n}"):
        payload = presentations[candidate_id]
        if payload not in result.values():
            result[candidate_id] = payload
    return result


def expected_candidate_ids(oracle_census: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for n in (1, 2, 3):
        result.add(f"U_{n}")
        universal = (1 << (n * n)) - 1
        for mask in oracle_census[str(n)]["canonical_masks"]:
            bits = format(mask, f"0{n*n}b")
            result.add(f"J_{n}" if mask == universal else f"R_{n}_{bits}")
            result.add(f"C_{n}" if mask == universal else f"T_{n}_{bits}")
        result.update(expected_kernel_payloads(n))
    return result


def expected_partitions(candidate: dict[str, Any]) -> dict[str, list[list[int]]]:
    n = candidate["carrier_size"]
    semantic_type = candidate["semantic_type"]
    automorphisms_rows = direct_automorphisms_for_payload(
        candidate["payload"], n, semantic_type, candidate["named_constants"]
    )
    partitions = {"automorphism_orbits": orbits_from_permutations(n, automorphisms_rows)}
    matrix = matrix_from_payload(candidate["payload"], n, semantic_type)
    if matrix is not None:
        partitions["local_probe_equivalence"] = local_probe_partition(matrix)
    if semantic_type == "transition_relation":
        assert matrix is not None
        partitions["strong_bisimulation"] = strong_bisimulation_partition(matrix)
    if semantic_type == "markov_kernel":
        partitions["kernel_row_equivalence"] = kernel_row_partition(candidate["payload"])
    return dict(sorted(partitions.items()))


def expected_viability(candidate: dict[str, Any]) -> dict[str, bool | None]:
    n = candidate["carrier_size"]
    semantic_type = candidate["semantic_type"]
    matrix = matrix_from_payload(candidate["payload"], n, semantic_type)
    transition_applicable = semantic_type in {"transition_relation", "markov_kernel"}
    serial = transition_applicable and matrix is not None and all(any(row) for row in matrix)
    persistent = transition_applicable and matrix is not None and persistent_support(matrix)
    branching = transition_applicable and matrix is not None and n > 1 and all(sum(row) >= 2 for row in matrix)
    unbiased = False
    if semantic_type == "markov_kernel":
        uniform = canonical_fraction(Fraction(1, n))
        unbiased = all(all(canonical_fraction(value) == uniform for value in row) for row in candidate["payload"])
    return {
        "V_branching": branching if transition_applicable else None,
        "V_exploratory_support": (persistent and branching) if transition_applicable else None,
        "V_persistent_support": persistent if transition_applicable else None,
        "V_registered": True,
        "V_serial": serial if transition_applicable else None,
        "V_unbiased_stochastic": unbiased if semantic_type == "markov_kernel" else None,
    }


def expected_stochastic_key(candidate: dict[str, Any]) -> list[str] | None:
    if candidate["semantic_type"] != "markov_kernel":
        return None
    rows = [[Fraction(value) for value in row] for row in candidate["payload"]]
    n = len(rows)
    source = sum(abs(rows[x][y] - rows[0][y]) for x in range(1, n) for y in range(n))
    destination = sum(
        abs(sum(rows[x][y] for x in range(n)) / n - Fraction(1, n))
        for y in range(n)
    )
    return [canonical_fraction(source), canonical_fraction(destination)]


def candidate_semantic_errors(candidates: dict[str, Any], oracle_census: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_ids = expected_candidate_ids(oracle_census)
    if set(candidates) != expected_ids:
        errors.append("candidate_id_coverage")
    for candidate_id, candidate in sorted(candidates.items()):
        try:
            n = candidate["carrier_size"]
            if candidate_id == f"U_{n}":
                expected_payload = None
                expected_type = "empty_signature"
            elif candidate_id == f"J_{n}":
                expected_payload = "1" * (n * n)
                expected_type = "static_relation"
            elif candidate_id == f"C_{n}":
                expected_payload = "1" * (n * n)
                expected_type = "transition_relation"
            elif candidate_id.startswith(f"R_{n}_"):
                expected_payload = candidate_id.split("_", 2)[2]
                expected_type = "static_relation"
            elif candidate_id.startswith(f"T_{n}_"):
                expected_payload = candidate_id.split("_", 2)[2]
                expected_type = "transition_relation"
            else:
                expected_payload = expected_kernel_payloads(n).get(candidate_id)
                expected_type = "markov_kernel"
            if candidate["payload"] != expected_payload or candidate["semantic_type"] != expected_type:
                errors.append(f"identity:{candidate_id}")
                continue
            expected_aut = direct_automorphisms_for_payload(
                candidate["payload"], n, candidate["semantic_type"], candidate["named_constants"]
            )
            if candidate["automorphism_permutations"] != expected_aut or candidate["automorphism_order"] != len(expected_aut):
                errors.append(f"automorphism:{candidate_id}")
            partitions = expected_partitions(candidate)
            if candidate["distinction_partitions"] != partitions:
                errors.append(f"partitions:{candidate_id}")
            if not validate_distinction_comparisons(partitions, candidate["distinction_comparisons"]):
                errors.append(f"comparison:{candidate_id}")
            if candidate["viability"] != expected_viability(candidate):
                errors.append(f"viability:{candidate_id}")
            if candidate["stochastic_neutrality"] != expected_stochastic_key(candidate):
                errors.append(f"stochastic:{candidate_id}")
        except Exception as exc:
            errors.append(f"exception:{candidate_id}:{type(exc).__name__}")
    return errors


def support_set(candidate: dict[str, Any]) -> frozenset[tuple[int, int]]:
    matrix = matrix_from_payload(
        candidate["payload"], candidate["carrier_size"], candidate["semantic_type"]
    )
    if matrix is None:
        return frozenset()
    return frozenset(
        (source, target)
        for source in range(len(matrix))
        for target in range(len(matrix))
        if matrix[source][target]
    )


def signature_key(candidate: dict[str, Any]) -> tuple[int, int, int, int]:
    semantic_type = candidate["semantic_type"]
    return (
        int(semantic_type in {"static_relation", "transition_relation"}),
        int(semantic_type in {"transition_relation", "markov_kernel"}),
        int(semantic_type == "markov_kernel"),
        len(candidate["named_constants"]),
    )


def oracle_mss(
    candidates: dict[str, Any],
    spec: dict[str, Any],
    carrier_sizes: tuple[int, ...] = (1, 2, 3),
    include_equivalence_classes: bool = False,
) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for n in carrier_sizes:
        rows = [candidate for candidate in candidates.values() if candidate["carrier_size"] == n]
        for arm in spec["mss_arms"]:
            arm_id = arm["id"]
            preorder = arm["preorder"]
            viability = arm["viability"]
            applicable: list[dict[str, Any]] = []
            for candidate in rows:
                if preorder == "support_freedom" and candidate["semantic_type"] == "empty_signature":
                    continue
                if preorder == "stochastic_neutrality" and candidate["semantic_type"] != "markov_kernel":
                    continue
                if candidate["viability"].get(viability) is True:
                    applicable.append(candidate)

            def weak_or_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
                if preorder == "signature_commitment":
                    return all(a <= b for a, b in zip(signature_key(left), signature_key(right), strict=True))
                if preorder == "support_freedom":
                    return support_set(left) >= support_set(right)
                if preorder == "automorphism_freedom":
                    left_aut = {tuple(row) for row in left["automorphism_permutations"]}
                    right_aut = {tuple(row) for row in right["automorphism_permutations"]}
                    return left_aut >= right_aut
                if preorder == "stochastic_neutrality":
                    left_key = tuple(Fraction(value) for value in left["stochastic_neutrality"])
                    right_key = tuple(Fraction(value) for value in right["stochastic_neutrality"])
                    return all(a <= b for a, b in zip(left_key, right_key, strict=True))
                raise GateError(f"unknown preorder: {preorder}")

            classes: list[list[dict[str, Any]]] = []
            remaining = {candidate["id"]: candidate for candidate in applicable}
            while remaining:
                first_id = min(remaining)
                first = remaining[first_id]
                equivalent_ids = sorted(
                    candidate_id
                    for candidate_id, candidate in remaining.items()
                    if weak_or_equal(first, candidate) and weak_or_equal(candidate, first)
                )
                classes.append([remaining.pop(candidate_id) for candidate_id in equivalent_ids])
            frontier: list[list[str]] = []
            for candidate_class in classes:
                representative = candidate_class[0]
                has_strictly_weaker = any(
                    weak_or_equal(other, representative)
                    and not weak_or_equal(representative, other)
                    for other in applicable
                )
                if not has_strictly_weaker:
                    frontier.append(sorted(candidate["id"] for candidate in candidate_class))
            arm_result = {
                "preorder": preorder,
                "viability": viability,
                "applicable_viable_count": len(applicable),
                "quotient_class_count": len(classes),
                "frontier_classes": canonical_classes(frontier),
            }
            if include_equivalence_classes:
                arm_result["viable_equivalence_classes"] = canonical_classes(
                    [[candidate["id"] for candidate in candidate_class] for candidate_class in classes]
                )
            arms[f"{n}|{arm_id}"] = arm_result
    return arms


def expected_kernel_alias_groups(n: int) -> dict[str, list[str]]:
    names = [f"K0_{n}", f"Klazy_{n}", f"Kbiased_{n}", f"Kidentity_{n}"]
    if n == 1:
        return {names[0]: names}
    if n == 2:
        return {names[0]: names[:2], names[2]: [names[2]], names[3]: [names[3]]}
    return {name: [name] for name in names}


def julia_raw_mss_class_errors(
    julia: dict[str, Any],
    candidates: dict[str, Any],
    spec: dict[str, Any],
    carrier_sizes: tuple[int, ...],
) -> list[str]:
    expected = oracle_mss(
        candidates,
        spec,
        carrier_sizes,
        include_equivalence_classes=True,
    )
    rows = {
        f"{int(row['carrier_size'])}|{row['arm_id']}": row
        for row in julia["mss_arms"]
        if int(row["carrier_size"]) in carrier_sizes
    }
    errors: list[str] = []
    if set(rows) != set(expected):
        errors.append("arm_coverage")
    for key, oracle_row in sorted(expected.items()):
        row = rows.get(key)
        if row is None:
            continue
        reported = canonical_classes(row.get("viable_equivalence_classes", []))
        if reported != oracle_row["viable_equivalence_classes"]:
            errors.append(key)
    return errors


def raw_alias_errors(julia: dict[str, Any], jax: dict[str, Any]) -> list[str]:
    """Validate provenance aliases independently of normalized semantic equality."""

    errors: list[str] = []
    jax_rows = {
        row["candidate_id"]: row
        for n in (1, 2, 3)
        for row in jax["registry_census"][str(n)]
    }
    julia_rows = {
        row["id"]: row
        for row in julia["candidates"]
        if int(row["carrier_size"]) <= 3
    }
    for n in (1, 2, 3):
        root_aliases = {f"U_{n}": [f"U_{n}"], f"J_{n}": [f"J_{n}"], f"C_{n}": [f"C_{n}"]}
        kernel_aliases = expected_kernel_alias_groups(n)
        for candidate_id, row in jax_rows.items():
            if int(row["carrier_size"]) != n:
                continue
            expected = root_aliases.get(candidate_id, kernel_aliases.get(candidate_id, []))
            if sorted(row.get("provenance_aliases", [])) != sorted(expected):
                errors.append(f"jax_aliases:{candidate_id}")
            if row["semantic_type"] == "markov_kernel":
                if sorted(row.get("named_family_presentations", [])) != sorted(expected):
                    errors.append(f"jax_named_presentations:{candidate_id}")

        for candidate_id, row in julia_rows.items():
            if int(row["carrier_size"]) != n:
                continue
            if candidate_id in root_aliases:
                family = candidate_id.split("_", 1)[0]
                expected = [candidate_id, f"{family}_n@n={n}"]
            elif candidate_id in kernel_aliases:
                expected = [
                    alias
                    for concrete in kernel_aliases[candidate_id]
                    for alias in (concrete, f"{concrete.rsplit('_', 1)[0]}_n@n={n}")
                ]
            else:
                expected = [candidate_id]
            if sorted(row.get("aliases", [])) != sorted(expected):
                errors.append(f"julia_aliases:{candidate_id}")

        alias_summary = jax["candidate_counts"][str(n)]["alias_deduplication"]
        expected_collisions = {
            candidate_id: aliases
            for candidate_id, aliases in kernel_aliases.items()
            if len(aliases) > 1
        }
        if alias_summary.get("named_kernel_boundary_collisions") != expected_collisions:
            errors.append(f"jax_collision_summary:{n}")
        required_true = (
            "J_aliases_existing_universal_static",
            "C_aliases_existing_universal_transition",
            "K0_aliases_existing_named_kernel",
            "identity_count_matches_exact_dedup",
            "presentation_count_kept_separate_from_identity_count",
            "no_alias_double_count",
        )
        if any(alias_summary.get(key) is not True for key in required_true):
            errors.append(f"jax_alias_summary_boolean:{n}")
    return sorted(set(errors))


def raw_jax_orbit_errors(jax: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for n in (1, 2, 3):
        for row in jax["registry_census"][str(n)]:
            candidate_id = row["candidate_id"]
            try:
                permutations_rows = canonical_permutations(
                    row["automorphism"]["permutations"], n
                )
                expected = orbits_from_permutations(n, permutations_rows)
                reported = canonical_partition(row["automorphism"]["orbits"], n)
                distinction = canonical_partition(
                    row["distinction_partitions"]["automorphism_orbits"], n
                )
                if reported != expected or distinction != expected:
                    errors.append(candidate_id)
            except Exception as exc:
                errors.append(f"{candidate_id}:{type(exc).__name__}")
    return sorted(set(errors))


def jax_raw_representation_errors(jax: dict[str, Any]) -> list[str]:
    """Bind duplicate raw representations to the protected semantic payload."""

    errors: list[str] = []
    for n in (1, 2, 3):
        permutations_rows = list(itertools.permutations(range(n)))
        relation_groups: dict[int, list[int]] = {}
        for labelled_mask in range(1 << (n * n)):
            labelled_matrix = matrix_from_mask(labelled_mask, n)
            canonical_mask = min(
                transformed_mask(labelled_matrix, permutation)
                for permutation in permutations_rows
            )
            relation_groups.setdefault(canonical_mask, []).append(labelled_mask)

        for row in jax["registry_census"][str(n)]:
            candidate_id = row["candidate_id"]
            try:
                normalized = normalize_jax_candidate(row)
                semantic_type = normalized["semantic_type"]
                matrix = matrix_from_payload(normalized["payload"], n, semantic_type)
                if semantic_type in {"static_relation", "transition_relation"}:
                    assert matrix is not None
                    canonical_mask = int(normalized["payload"], 2)
                    support = [[int(value) for value in matrix_row] for matrix_row in matrix]
                    if row.get("canonical_mask") != canonical_mask:
                        errors.append(f"canonical_mask:{candidate_id}")
                    if row.get("canonical_bitstring") != normalized["payload"]:
                        errors.append(f"canonical_bitstring:{candidate_id}")
                    if row.get("support_matrix") != support:
                        errors.append(f"support_matrix:{candidate_id}")
                    members = relation_groups[canonical_mask]
                    if row.get("labelled_orbit_members") != members:
                        errors.append(f"labelled_orbit_members:{candidate_id}")
                    if row.get("labelled_orbit_size") != len(members):
                        errors.append(f"labelled_orbit_size:{candidate_id}")
                elif semantic_type == "markov_kernel":
                    fractions = [
                        [Fraction(value) for value in kernel_row]
                        for kernel_row in normalized["payload"]
                    ]
                    denominator = math.lcm(
                        *(value.denominator for kernel_row in fractions for value in kernel_row)
                    )
                    numerators = [
                        [value.numerator * (denominator // value.denominator) for value in kernel_row]
                        for kernel_row in fractions
                    ]
                    support = [
                        [int(value > 0) for value in kernel_row]
                        for kernel_row in fractions
                    ]
                    conditional = -sum(
                        float(value) * math.log2(float(value))
                        for value in fractions[0]
                        if value > 0
                    )
                    if row.get("common_denominator") != denominator:
                        errors.append(f"common_denominator:{candidate_id}")
                    if row.get("integer_numerators") != numerators:
                        errors.append(f"integer_numerators:{candidate_id}")
                    if row.get("support_matrix") != support:
                        errors.append(f"support_matrix:{candidate_id}")
                    if abs(float(row.get("conditional_entropy_from_state_0_bits")) - conditional) > FLOAT_TOLERANCE:
                        errors.append(f"conditional_entropy:{candidate_id}")
            except Exception as exc:
                errors.append(f"exception:{candidate_id}:{type(exc).__name__}")
    return sorted(set(errors))


def jax_summary_errors(jax: dict[str, Any], oracle_census: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_registry = {"1": 6, "2": 24, "3": 213}
    for n in ("1", "2", "3"):
        summary = jax["candidate_counts"][n]
        oracle = oracle_census[n]
        if len(jax["registry_census"][n]) != expected_registry[n]:
            errors.append(f"registry_length:{n}")
        if summary.get("total_registry_identities") != expected_registry[n]:
            errors.append(f"registry_summary:{n}")
        if summary.get("labelled_static_relations") != oracle["labelled_count"]:
            errors.append(f"static_labelled:{n}")
        if summary.get("labelled_transition_relations") != oracle["labelled_count"]:
            errors.append(f"transition_labelled:{n}")
        if summary.get("transition_viability_counts_labelled") != oracle["labelled_viability"]:
            errors.append(f"viability_labelled:{n}")
        if summary.get("transition_viability_counts_isomorphism_classes") != oracle["isomorphism_class_viability"]:
            errors.append(f"viability_isomorphism:{n}")
        if summary.get("relabel_canonical_invariant_exhaustive") is not True:
            errors.append(f"relabel_canonical:{n}")
        if summary.get("relabel_viability_and_partition_shape_invariant") is not True:
            errors.append(f"relabel_partition:{n}")
    return sorted(set(errors))


def external_gate_receipt_errors(jax: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    n = 3
    all_permutations = list(itertools.permutations(range(n)))
    baseline: dict[int, dict[str, Any]] = {}
    matrices = [matrix_from_mask(mask, n) for mask in range(1 << (n * n))]
    for mask, matrix in enumerate(matrices):
        baseline[mask] = {
            "adjacency": format(mask, "09b"),
            "automorphisms": [
                list(permutation)
                for permutation in all_permutations
                if transformed_mask(matrix, permutation) == mask
            ],
        }

    def reflexive(matrix: list[list[bool]]) -> bool:
        return all(matrix[index][index] for index in range(n))

    def symmetric(matrix: list[list[bool]]) -> bool:
        return all(matrix[left][right] == matrix[right][left] for left in range(n) for right in range(n))

    gates: list[tuple[str, Callable[[list[list[bool]]], bool], int]] = [
        ("none", lambda _matrix: True, 512),
        ("reflexive", reflexive, 64),
        ("reflexive_and_symmetric", lambda matrix: reflexive(matrix) and symmetric(matrix), 8),
        ("universal", lambda matrix: all(all(row) for row in matrix), 1),
    ]
    reported_rows = jax["external_constraint_controls"].get("gates", [])
    if len(reported_rows) != len(gates):
        return ["gate_count"]
    previous: set[int] | None = None
    for row, (name, predicate, expected_count) in zip(reported_rows, gates, strict=True):
        survivors = {mask for mask, matrix in enumerate(matrices) if predicate(matrix)}
        manifest = {mask: baseline[mask] for mask in sorted(survivors)}
        if row.get("gate") != name:
            errors.append(f"name:{name}")
        if row.get("survivor_masks") != sorted(survivors):
            errors.append(f"survivors:{name}")
        if row.get("model_count") != expected_count or row.get("expected_model_count") != expected_count:
            errors.append(f"count:{name}")
        if row.get("count_pass") is not True:
            errors.append(f"count_pass:{name}")
        if row.get("survivor_internal_manifest_sha256") != canonical_sha256(manifest):
            errors.append(f"manifest:{name}")
        if row.get("survivor_internal_byte_identity_against_baseline") is not True:
            errors.append(f"identity:{name}")
        if previous is not None and not survivors <= previous:
            errors.append(f"monotonicity:{name}")
        previous = survivors
    controls = jax["external_constraint_controls"]
    if controls.get("monotone_candidate_set_shrink") is not True:
        errors.append("summary_monotone")
    if controls.get("survivor_internal_structures_unchanged") is not True:
        errors.append("summary_identity")
    return sorted(set(errors))


def named_n4_expected() -> dict[str, tuple[str, Any, list[int]]]:
    identity = "".join("1" if source == target else "0" for source in range(4) for target in range(4))
    cycle = "".join("1" if target == (source + 1) % 4 else "0" for source in range(4) for target in range(4))
    terminal_edges = {(0, 1), (1, 2), (2, 3), (3, 3)}
    terminal = "".join("1" if (source, target) in terminal_edges else "0" for source in range(4) for target in range(4))
    cycle_matrix = matrix_from_payload(cycle, 4, "transition_relation")
    terminal_matrix = matrix_from_payload(terminal, 4, "transition_relation")
    assert cycle_matrix is not None and terminal_matrix is not None
    cycle = format(
        min(transformed_mask(cycle_matrix, permutation) for permutation in itertools.permutations(range(4))),
        "016b",
    )
    terminal = format(
        min(transformed_mask(terminal_matrix, permutation) for permutation in itertools.permutations(range(4))),
        "016b",
    )
    kernels = expected_kernel_payloads(4)
    return {
        "U_4": ("empty_signature", None, []),
        "R4_empty": ("static_relation", "0" * 16, []),
        "J_4": ("static_relation", "1" * 16, []),
        "C_4": ("transition_relation", "1" * 16, []),
        "T4_identity": ("transition_relation", identity, []),
        "T4_cycle": ("transition_relation", cycle, []),
        "T4_terminal": ("transition_relation", terminal, []),
        "J4_c0": ("static_relation", "1" * 16, [0]),
        "J4_c0_c1": ("static_relation", "1" * 16, [0, 1]),
        **{candidate_id: ("markov_kernel", payload, []) for candidate_id, payload in kernels.items()},
    }


def named_n4_julia_errors(julia: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    rows = [row for row in julia["candidates"] if int(row["carrier_size"]) == 4]
    raw_by_id = {row["id"]: row for row in rows}
    candidates = {row["id"]: normalize_julia_candidate(row) for row in rows}
    if len(candidates) != len(rows):
        errors.append("duplicate_candidate_id")
    expected = named_n4_expected()
    if set(candidates) != set(expected):
        errors.append("candidate_id_coverage")
    expected_aliases = {
        "U_4": ["U_4", "U_n@n=4"],
        "R4_empty": ["R4_empty", "empty relation"],
        "J_4": ["J_4", "J_n@n=4", "universal relation"],
        "C_4": ["C_4", "C_n@n=4"],
        "T4_identity": ["T4_identity", "identity loops"],
        "T4_cycle": ["T4_cycle", "directed four-cycle"],
        "T4_terminal": ["T4_terminal", "terminal path 0->1->2->3 with 3->3"],
        "J4_c0": ["J4_c0", "universal relation with named constant c0=0"],
        "J4_c0_c1": ["J4_c0_c1", "universal relation with named constants c0=0 and c1=1"],
        "K0_4": ["K0_4", "K0_n@n=4"],
        "Klazy_4": ["Klazy_4", "Klazy_n@n=4"],
        "Kbiased_4": ["Kbiased_4", "Kbiased_n@n=4"],
        "Kidentity_4": ["Kidentity_4", "Kidentity_n@n=4"],
    }
    for candidate_id, candidate in sorted(candidates.items()):
        try:
            semantic_type, payload, constants = expected[candidate_id]
            if (
                candidate["semantic_type"] != semantic_type
                or candidate["payload"] != payload
                or candidate["named_constants"] != constants
            ):
                errors.append(f"identity:{candidate_id}")
                continue
            expected_aut = direct_automorphisms_for_payload(payload, 4, semantic_type, constants)
            if candidate["automorphism_permutations"] != expected_aut:
                errors.append(f"automorphism:{candidate_id}")
            partitions = expected_partitions(candidate)
            if candidate["distinction_partitions"] != partitions:
                errors.append(f"partitions:{candidate_id}")
            if not validate_distinction_comparisons(partitions, candidate["distinction_comparisons"]):
                errors.append(f"comparison:{candidate_id}")
            if candidate["viability"] != expected_viability(candidate):
                errors.append(f"viability:{candidate_id}")
            if candidate["stochastic_neutrality"] != expected_stochastic_key(candidate):
                errors.append(f"stochastic:{candidate_id}")
            if sorted(raw_by_id[candidate_id].get("aliases", [])) != sorted(expected_aliases[candidate_id]):
                errors.append(f"aliases:{candidate_id}")
        except Exception as exc:
            errors.append(f"exception:{candidate_id}:{type(exc).__name__}")
    return sorted(set(errors)), candidates


def named_n4_jax_errors(jax: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "empty_relation": ("0" * 16, []),
        "universal_relation": ("1" * 16, []),
        "identity_loops": ("1000010000100001", []),
        "directed_four_cycle": ("0100001000011000", []),
        "terminal_path": ("0100001000010001", []),
        "universal_plus_c0": ("1" * 16, [0]),
        "universal_plus_c0_c1": ("1" * 16, [0, 1]),
    }
    boundary = jax.get("named_relation_controls_at_n4", {})
    rows = {row["id"]: row for row in boundary.get("controls", [])}
    if boundary.get("carrier_size") != 4 or set(rows) != set(expected):
        errors.append("coverage")
    for candidate_id, row in sorted(rows.items()):
        try:
            bitstring, constants = expected[candidate_id]
            if row.get("support_bitstring") != bitstring or row.get("named_constants") != constants:
                errors.append(f"identity:{candidate_id}")
                continue
            auts = direct_automorphisms_for_payload(bitstring, 4, "static_relation", constants)
            if canonical_permutations(row["automorphism_permutations"], 4) != auts:
                errors.append(f"automorphism:{candidate_id}")
            if int(row["automorphism_order"]) != len(auts):
                errors.append(f"order:{candidate_id}")
            if canonical_partition(row["automorphism_orbits"], 4) != orbits_from_permutations(4, auts):
                errors.append(f"orbits:{candidate_id}")
        except Exception as exc:
            errors.append(f"exception:{candidate_id}:{type(exc).__name__}")
    return sorted(set(errors))


def automorphisms(constants: tuple[int, ...]) -> list[list[int]]:
    return [
        list(permutation)
        for permutation in itertools.permutations(range(4))
        if all(permutation[value] == value for value in constants)
    ]


def append_oracle() -> dict[str, Any]:
    groups = {
        "A0": automorphisms(()),
        "A1": automorphisms(()),
        "A2": automorphisms((0,)),
        "A3": automorphisms((0, 1)),
        "B2": automorphisms((1,)),
    }
    return {
        "orders": [len(groups[name]) for name in ("A0", "A1", "A2", "A3")],
        "groups": groups,
        "replacement_witness": [2, 1, 0, 3],
    }


def external_gate_oracle() -> list[int]:
    matrices = [matrix_from_mask(mask, 3) for mask in range(512)]
    reflexive = [matrix for matrix in matrices if all(matrix[i][i] for i in range(3))]
    symmetric = [
        matrix
        for matrix in reflexive
        if all(matrix[i][j] == matrix[j][i] for i in range(3) for j in range(3))
    ]
    universal = [matrix for matrix in symmetric if all(all(row) for row in matrix)]
    return [len(matrices), len(reflexive), len(symmetric), len(universal)]


SMT_PLAN = [
    ("append_subgroup_A0_A1", "A1", "A0", "unsat", 0),
    ("append_subgroup_A1_A2", "A2", "A1", "unsat", 0),
    ("append_subgroup_A2_A3", "A3", "A2", "unsat", 0),
    ("append_strictness_A0_A1", "A0", "A1", "unsat", 0),
    ("append_strictness_A1_A2", "A1", "A2", "sat", 18),
    ("append_strictness_A2_A3", "A2", "A3", "sat", 4),
    ("replacement_B2_not_subset_A2", "B2", "A2", "sat", 4),
    ("control_mutated_replacement_c0_to_0", "B2_mutated_c0_0", "A2", "unsat", 0),
    ("control_mutated_A3_c1_to_0", "A2", "A3_mutated_c1_0", "unsat", 0),
]


SMT_CONSTANTS = {
    "A0": (),
    "A1": (),
    "A2": (0,),
    "A3": (0, 1),
    "B2": (1,),
    "B2_mutated_c0_0": (0,),
    "A3_mutated_c1_0": (0, 0),
}


def expected_smt_query_plan() -> list[dict[str, str]]:
    categories = {
        "append_subgroup_A0_A1": "required_append_subgroup",
        "append_subgroup_A1_A2": "required_append_subgroup",
        "append_subgroup_A2_A3": "required_append_subgroup",
        "append_strictness_A0_A1": "required_append_strictness",
        "append_strictness_A1_A2": "required_append_strictness",
        "append_strictness_A2_A3": "required_append_strictness",
        "replacement_B2_not_subset_A2": "required_replacement_nonmonotone",
        "control_mutated_replacement_c0_to_0": "mutated_constant_flip_control",
        "control_mutated_A3_c1_to_0": "mutated_constant_flip_control",
    }
    flips = {
        "control_mutated_replacement_c0_to_0": "replacement_B2_not_subset_A2",
        "control_mutated_A3_c1_to_0": "append_strictness_A2_A3",
    }
    result: list[dict[str, str]] = []
    for query_id, left, right, expected, _count in SMT_PLAN:
        row = {
            "id": query_id,
            "category": categories[query_id],
            "left": left,
            "right": right,
            "expected": expected,
        }
        if query_id in flips:
            row["flips"] = flips[query_id]
        result.append(row)
    return result


def expected_smt_structures() -> dict[str, Any]:
    universal = [[True for _ in range(4)] for _ in range(4)]
    return {
        "A0": {"relation": None, "constants": {}},
        "A1": {"relation": universal, "constants": {}},
        "A2": {"relation": universal, "constants": {"c0": 0}},
        "A3": {"relation": universal, "constants": {"c0": 0, "c1": 1}},
        "B2": {"relation": universal, "constants": {"c0": 1}},
        "B2_mutated_c0_0": {"relation": universal, "constants": {"c0": 0}},
        "A3_mutated_c1_0": {"relation": universal, "constants": {"c0": 0, "c1": 0}},
    }


def is_structure_automorphism(structure: str, permutation: tuple[int, ...]) -> bool:
    return sorted(permutation) == [0, 1, 2, 3] and all(
        permutation[value] == value for value in SMT_CONSTANTS[structure]
    )


def solver_oracle(left: str, right: str) -> list[list[int]]:
    return [
        list(permutation)
        for permutation in itertools.permutations(range(4))
        if is_structure_automorphism(left, permutation)
        and not is_structure_automorphism(right, permutation)
    ]


def validate_smt(smt: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    expected_plan = expected_smt_query_plan()
    if smt.get("query_plan_sha256") != canonical_sha256(expected_plan):
        errors.append("query_plan_sha256")
    if smt.get("structure_replay_sha256") != canonical_sha256(expected_smt_structures()):
        errors.append("structure_replay_sha256")
    expected_candidate_counts = {
        "carrier_size": 4,
        "all_carrier_permutations": 24,
        "core_structures": 5,
        "mutation_control_structures": 2,
        "queries": len(SMT_PLAN),
        "automorphism_orders": {
            structure_id: len(automorphisms(tuple(constants.values())))
            for structure_id, constants in {
                "A0": {},
                "A1": {},
                "A2": {"c0": 0},
                "A3": {"c0": 0, "c1": 1},
                "B2": {"c0": 1},
                "B2_mutated_c0_0": {"c0": 0},
                "A3_mutated_c1_0": {"c0": 0, "c1": 0},
            }.items()
        },
    }
    if smt.get("candidate_counts") != expected_candidate_counts:
        errors.append("candidate_counts")
    expected_spec_checks = {
        "schema_is_v1",
        "spec_is_frozen_amendment_1",
        "spec_hash_matches_frozen_amendment_1",
        "classification_is_scratch",
        "carrier_is_fixed_X4",
        "append_steps_match",
        "append_orders_match",
        "solver_obligations_present",
    }
    spec_checks = smt.get("spec_contract_checks", {})
    if set(spec_checks) != expected_spec_checks or not all(
        value is True for value in spec_checks.values()
    ):
        errors.append("spec_contract_checks")
    rows = smt.get("queries", [])
    if len(rows) != len(SMT_PLAN):
        errors.append("query_count")
        return errors, []
    if len({row.get("id") for row in rows}) != len(rows):
        errors.append("duplicate_query_id")
    by_id = {row.get("id"): row for row in rows}
    matrix: list[dict[str, Any]] = []
    expected_plan_by_id = {row["id"]: row for row in expected_plan}
    for query_id, left, right, expected, expected_count in SMT_PLAN:
        row = by_id.get(query_id)
        if row is None:
            errors.append(f"missing:{query_id}")
            continue
        oracle = solver_oracle(left, right)
        oracle_set = {tuple(value) for value in oracle}
        plan_row = expected_plan_by_id[query_id]
        if (
            row.get("left") != left
            or row.get("right") != right
            or row.get("expected") != expected
            or row.get("category") != plan_row["category"]
        ):
            errors.append(f"shape:{query_id}")
        reported_oracle = row.get("oracle", {})
        if reported_oracle.get("status") != expected or reported_oracle.get("witness_count") != expected_count:
            errors.append(f"oracle_status:{query_id}")
        if reported_oracle.get("witnesses") != oracle:
            errors.append(f"oracle_witnesses:{query_id}")
        if row.get("pass") is not True or not row.get("checks") or not all(
            value is True for value in row["checks"].values()
        ):
            errors.append(f"nested_query_checks:{query_id}")
        for solver_name in ("z3", "cvc5"):
            solver = row.get(solver_name, {})
            try:
                raw_witnesses = [item["permutation"] for item in solver.get("witnesses", [])]
                witnesses = (
                    canonical_permutations(raw_witnesses, 4)
                    if raw_witnesses
                    else []
                )
            except (GateError, KeyError, TypeError, ValueError):
                witnesses = []
                errors.append(f"witness_shape:{query_id}:{solver_name}")
            witness_set = {tuple(value) for value in witnesses}
            if solver.get("status") != expected:
                errors.append(f"status:{query_id}:{solver_name}")
            if solver.get("enumeration_terminal_status") != "unsat" or solver.get("enumeration_complete") is not True:
                errors.append(f"incomplete:{query_id}:{solver_name}")
            if int(solver.get("witness_count", -1)) != expected_count or witness_set != oracle_set:
                errors.append(f"witness_set:{query_id}:{solver_name}")
            for permutation in witness_set:
                if not (
                    is_structure_automorphism(left, permutation)
                    and not is_structure_automorphism(right, permutation)
                ):
                    errors.append(f"replay:{query_id}:{solver_name}")
            for item in solver.get("witnesses", []):
                permutation = tuple(int(value) for value in item.get("permutation", []))
                expected_replay = {
                    "permutation": sorted(permutation) == [0, 1, 2, 3],
                    "left_automorphism": is_structure_automorphism(left, permutation),
                    "right_automorphism": is_structure_automorphism(right, permutation),
                    "query_satisfied": (
                        is_structure_automorphism(left, permutation)
                        and not is_structure_automorphism(right, permutation)
                    ),
                }
                if item.get("replay") != expected_replay:
                    errors.append(f"nested_replay:{query_id}:{solver_name}")
        matrix.append(
            {
                "id": query_id,
                "left": left,
                "right": right,
                "expected": expected,
                "witness_count": expected_count,
                "oracle_witnesses": oracle,
            }
        )
    if sum(row[4] for row in SMT_PLAN) != 26:
        errors.append("internal_expected_total")
    controls = smt.get("controls", {})
    if not controls or not all(value is True for value in controls.values()):
        errors.append("smt_controls")
    independence = smt.get("solver_independence", {})
    if independence.get("shared_generated_formula_manifest") is not False or independence.get("shared_solver_models") is not False:
        errors.append("solver_independence")
    tool_receipts = smt.get("tool_receipts", {})
    expected_total = sum(row[4] for row in SMT_PLAN)
    for solver_name in ("z3", "cvc5"):
        receipt = tool_receipts.get(solver_name, {})
        if (
            receipt.get("all_terminal") is not True
            or receipt.get("query_count") != len(SMT_PLAN)
            or receipt.get("sat_permutations_extracted") != expected_total
        ):
            errors.append(f"tool_receipt:{solver_name}")
    python_receipt = tool_receipts.get("python_replay", {})
    if (
        python_receipt.get("all_replays_pass") is not True
        or python_receipt.get("z3_witnesses_replayed") != expected_total
        or python_receipt.get("cvc5_witnesses_replayed") != expected_total
        or python_receipt.get("oracle_permutations_per_query") != 24
    ):
        errors.append("tool_receipt:python_replay")
    return sorted(set(errors)), matrix


def common_lane_checks(
    lane: dict[str, Any],
    source: Path,
    result_path: Path,
    schema: str,
    spec: dict[str, Any],
    lane_name: str,
) -> dict[str, bool]:
    source_reported = lane.get("source_path")
    source_resolved = Path(str(source_reported))
    if not source_resolved.is_absolute():
        source_resolved = REPO / source_resolved
    command_text = json.dumps(lane.get("command", []))
    if lane_name == "julia":
        reads_peer = lane.get("runner_identity", {}).get("reads_peer_result")
        inputs_ok = lane.get("input_provenance", {}).get("peer_result_files_read") == []
        shared_ok = inputs_ok
    else:
        contract = lane.get("engine_contract", {})
        reads_peer = contract.get("reads_peer_result")
        inputs = contract.get("inputs_read")
        inputs_ok = inputs == [str(SPEC_PATH.relative_to(REPO))]
        shared_ok = contract.get("shared_generated_manifest_consumed") is False
    return {
        "schema": lane.get("schema_version") == schema,
        "all_pass": lane.get("all_pass") is True,
        "classification": lane.get("classification") == "scratch_diagnostic",
        "promotion_locked": lane.get("promotion_allowed") is False and lane.get("formal_admission_allowed") is False,
        "claim_ceiling": lane.get("claim_ceiling") == spec["claim_ceiling"],
        "blocked_consumers": lane.get("blocked_consumers") == spec["blocked_consumers"],
        "spec_hash": lane.get("spec_sha256") == EXPECTED_SPEC_SHA256,
        "source_path": source_resolved.resolve() == source.resolve(),
        "source_hash": lane.get("source_sha256") == sha256_file(source),
        "cwd": lane.get("cwd") == str(REPO),
        "command": source.name in command_text and (
            result_path.name in command_text
            or (
                lane_name == "julia"
                and lane.get("result_path") == str(result_path.relative_to(REPO))
            )
        ),
        "reads_peer_result": reads_peer is False,
        "inputs": inputs_ok,
        "no_shared_generated_manifest": shared_ok,
        "packages": isinstance(lane.get("packages_used"), list) and bool(lane["packages_used"]),
        "load_bearing": isinstance(lane.get("aligned_packages_load_bearing"), list) and bool(lane["aligned_packages_load_bearing"]),
        "runtime_identity": isinstance(lane.get("runner_identity"), dict) and bool(lane["runner_identity"]) and isinstance(lane.get("runtime"), dict) and bool(lane["runtime"]),
        "errors_clear": lane.get("errors") in (None, []),
    }


def engine_tool_receipt_errors(julia: dict[str, Any], jax: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if julia.get("packages_used") != ["Graphs", "JSON3", "SHA", "Pkg"]:
        errors.append("julia_packages_used")
    if julia.get("aligned_packages_load_bearing") != ["Graphs"]:
        errors.append("julia_aligned_load_bearing")
    julia_tools = {row.get("tool"): row for row in julia.get("tool_receipts", [])}
    if set(julia_tools) != {"Graphs", "JSON3", "SHA"}:
        errors.append("julia_tool_coverage")
    expected_julia = {
        "Graphs": {
            "qualified_api/function": "Graphs.SimpleDiGraph, Graphs.add_edge!, Graphs.strongly_connected_components",
            "gates": ["all_pass", "V_persistent_support", "V_exploratory_support", "MSS frontiers"],
        },
        "JSON3": {
            "qualified_api/function": "JSON3.read and JSON3.write",
            "gates": ["all_pass", "provenance", "result emission"],
        },
        "SHA": {
            "qualified_api/function": "SHA.sha256",
            "gates": ["all_pass", "provenance", "registry identity"],
        },
    }
    for tool_name, expected in expected_julia.items():
        row = julia_tools.get(tool_name, {})
        if row.get("load_bearing") is not True:
            errors.append(f"julia_load_bearing:{tool_name}")
        if row.get("qualified_api/function") != expected["qualified_api/function"]:
            errors.append(f"julia_api:{tool_name}")
        if row.get("gates") != expected["gates"]:
            errors.append(f"julia_gates:{tool_name}")
        for field in (
            "input_object",
            "output_object",
            "positive_case",
            "negative/erased_control",
            "boundary_case",
            "demotion_condition",
        ):
            if not row.get(field):
                errors.append(f"julia_field:{tool_name}:{field}")

    if jax.get("packages_used") != ["jax", "jax.numpy", "jraph"]:
        errors.append("jax_packages_used")
    if jax.get("aligned_packages_load_bearing") != ["jraph"]:
        errors.append("jax_aligned_load_bearing")
    jax_tools = {row.get("tool"): row for row in jax.get("tool_receipts", [])}
    if set(jax_tools) != {"jax", "jraph"}:
        errors.append("jax_tool_coverage")
    expected_jax = {
        "jax": {
            "qualified_api/function": "jax.jit(jax.vmap(transform_one))",
            "gates": ["all_pass", "isomorphism_quotient", "automorphism_sets", "MSS_frontiers"],
        },
        "jraph": {
            "qualified_api/function": "jraph.segment_sum",
            "gates": ["all_pass", "V_serial", "V_branching", "V_exploratory_support", "MSS_frontiers"],
        },
    }
    for tool_name, expected in expected_jax.items():
        row = jax_tools.get(tool_name, {})
        if row.get("load_bearing") is not True:
            errors.append(f"jax_load_bearing:{tool_name}")
        if row.get("qualified_api/function") != expected["qualified_api/function"]:
            errors.append(f"jax_api:{tool_name}")
        if row.get("gates") != expected["gates"]:
            errors.append(f"jax_gates:{tool_name}")
        for field in (
            "input_object",
            "output_object",
            "positive_case",
            "negative/erased_control",
            "boundary_case",
            "demotion_condition",
        ):
            if row.get(field) in (None, "", [], {}):
                errors.append(f"jax_field:{tool_name}:{field}")
    if julia.get("controls", {}).get("Graphs_SCC_cycle_controls", {}).get("pass") is not True:
        errors.append("julia_graphs_control")
    jax_checks = jax.get("controls", {}).get("checks", {})
    if jax_checks.get("jax_x64_enabled") is not True or jax_checks.get("jraph_edge_erasure_flips_viability") is not True:
        errors.append("jax_load_bearing_controls")
    return sorted(set(errors))


def lev_events_valid(events: list[dict[str, Any]]) -> bool:
    """Require a real started/completed/sealed Lev invocation, not shape-only JSON."""

    started = [row for row in events if row.get("type") == "exec.started"]
    completed = [row for row in events if row.get("type") == "exec.completed"]
    receipts = [row for row in events if row.get("type") == "exec.receipt"]
    if len(started) != 1 or len(completed) != 1 or len(receipts) != 1:
        return False
    exec_id = started[0].get("data", {}).get("execId")
    receipt = receipts[0].get("data", {}).get("receipt", {})
    return bool(
        exec_id
        and completed[0].get("data", {}).get("execId") == exec_id
        and completed[0].get("data", {}).get("exitCode") == 0
        and receipts[0].get("data", {}).get("execId") == exec_id
        and receipt.get("sessionId") == exec_id
        and receipt.get("sealedAt")
        and receipt.get("contentHash")
    )


def append_comparison(julia: dict[str, Any], jax: dict[str, Any], oracle: dict[str, Any]) -> dict[str, Any]:
    julia_chain = julia["fixed_carrier_internal_append_chain"]
    jax_chain = jax["fixed_carrier_internal_append_chain"]
    julia_orders = [int(row["aut_order"]) for row in julia_chain["steps"]]
    jax_orders = [int(row["automorphism_order"]) for row in jax_chain["steps"]]
    julia_groups = {
        row["id"]: canonical_permutations(row["aut_permutations"])
        for row in julia_chain["steps"]
    }
    jax_groups = {
        row["id"]: canonical_permutations(row["automorphism_permutations"])
        for row in jax_chain["steps"]
    }
    adjacent_julia = [
        (row["from"], row["to"], bool(row["next_subset_previous"]), bool(row["strict"]))
        for row in julia_chain["adjacent_checks"]
    ]
    adjacent_jax = [
        (row["from"], row["to"], bool(row["literal_subgroup"]), bool(row["strict"]))
        for row in jax_chain["adjacent_checks"]
    ]
    expected_adjacent = [
        ("A0", "A1", True, False),
        ("A1", "A2", True, True),
        ("A2", "A3", True, True),
    ]
    julia_nested_rows_ok = all(
        row.get("next_subset_previous") is True
        and row.get("strict") is row.get("expected_strict")
        and row.get("pass") is True
        and row.get("append_subgroup_query_direct_status") == "unsat"
        and row.get("append_strictness_query_direct_status")
        == ("sat" if row.get("expected_strict") else "unsat")
        for row in julia_chain["adjacent_checks"]
    )
    jax_nested_rows_ok = all(
        row.get("literal_subgroup") is True
        and row.get("strict") is row.get("expected_strict")
        and row.get("strictness_pass") is True
        for row in jax_chain["adjacent_checks"]
    )
    expected_removed = {
        ("A0", "A1"): None,
        ("A1", "A2"): list(
            min(
                set(map(tuple, oracle["groups"]["A1"]))
                - set(map(tuple, oracle["groups"]["A2"]))
            )
        ),
        ("A2", "A3"): list(
            min(
                set(map(tuple, oracle["groups"]["A2"]))
                - set(map(tuple, oracle["groups"]["A3"]))
            )
        ),
    }
    jax_removed_witnesses_ok = all(
        row.get("removed_witness") == expected_removed[(row["from"], row["to"])]
        for row in jax_chain["adjacent_checks"]
    )
    jax_step_orbits_ok = all(
        canonical_partition(row["automorphism_orbits"], 4)
        == orbits_from_permutations(4, oracle["groups"][row["id"]])
        for row in jax_chain["steps"]
    )
    julia_replacement = julia_chain["replacement_control"]
    jax_replacement = jax_chain["replacement_control"]
    return {
        "orders_equal_oracle": julia_orders == jax_orders == oracle["orders"],
        "groups_equal_oracle": julia_groups == jax_groups == {
            key: canonical_permutations(value)
            for key, value in oracle["groups"].items()
            if key != "B2"
        },
        "adjacent_equal": adjacent_julia == adjacent_jax,
        "julia_adjacent_matches_oracle": adjacent_julia == expected_adjacent,
        "jax_adjacent_matches_oracle": adjacent_jax == expected_adjacent,
        "julia_nested_receipt_green": julia_chain.get("all_pass") is True and julia_nested_rows_ok,
        "jax_nested_receipt_green": (
            jax_chain.get("all_pass") is True
            and jax_chain.get("all_append_subgroups") is True
            and jax_chain.get("all_strictness_expectations") is True
            and jax_nested_rows_ok
        ),
        "jax_removed_witnesses_replay": jax_removed_witnesses_ok,
        "jax_step_automorphism_orbits": jax_step_orbits_ok,
        "julia_replacement_receipt_green": (
            julia_replacement.get("pass") is True
            and julia_replacement.get("direct_status") == "sat"
            and julia_replacement.get("witness_replay_pass") is True
            and julia_replacement.get("B2_aut_order") == len(oracle["groups"]["B2"])
        ),
        "jax_replacement_receipt_green": (
            jax_replacement.get("direct_replay") is True
            and jax_replacement.get("automorphism_order") == len(oracle["groups"]["B2"])
            and canonical_permutations(jax_replacement.get("automorphism_permutations", []), 4)
            == canonical_permutations(oracle["groups"]["B2"], 4)
        ),
        "replacement_nonmonotone": (
            julia_chain["replacement_control"]["B2_subset_A2"] is False
            and jax_chain["replacement_control"]["Aut_B2_subset_Aut_A2"] is False
            and julia_chain["replacement_control"]["witness_permutation"] == oracle["replacement_witness"]
            and jax_chain["replacement_control"]["nonmonotone_witness"] == oracle["replacement_witness"]
        ),
    }


def entropy_comparison(julia: dict[str, Any], jax: dict[str, Any]) -> dict[str, bool]:
    julia_entropy = julia["entropy_capacity_readouts"]
    jax_entropy = jax["entropy_capacity_readouts"]
    fixed_ok = True
    for left, right in zip(julia_entropy["per_size"], jax_entropy["fixed_carrier"], strict=True):
        fixed_ok &= int(left["carrier_size"]) == int(right["n"])
        fixed_ok &= left["K0_fixed_n_state_entropy_change_exact"] == "0"
        fixed_ok &= left.get("fixed_n_pass") is True
        fixed_ok &= abs(float(left.get("K0_fixed_n_state_entropy_change_float"))) <= FLOAT_TOLERANCE
        fixed_ok &= abs(float(right["K0_fixed_n_state_entropy_change_bits"])) <= FLOAT_TOLERANCE
        fixed_ok &= right["K0_one_step_conditional_entropy"].get("formula") == "log2(n)"
        fixed_ok &= right["K0_path_entropy"].get("formula") == "H*log2(n)"
        fixed_ok &= right["C_support_path_capacity"].get("formula") == "H*log2(n)"
        fixed_ok &= abs(
            float(right["K0_uniform_stationary_input_entropy_bits"])
            - math.log2(int(right["n"]))
        ) <= FLOAT_TOLERANCE
        fixed_ok &= abs(
            float(right["K0_uniform_stationary_output_entropy_bits"])
            - math.log2(int(right["n"]))
        ) <= FLOAT_TOLERANCE
        fixed_ok &= abs(
            float(right["K0_uniform_stationary_output_entropy_bits"])
            - float(right["K0_uniform_stationary_input_entropy_bits"])
        ) <= FLOAT_TOLERANCE
        fixed_ok &= abs(float(left["K0_one_step_conditional_entropy"]) - float(right["K0_one_step_conditional_entropy"]["bits"])) <= FLOAT_TOLERANCE
        fixed_ok &= abs(float(left["K0_path_entropy_horizon_3"]) - float(right["K0_path_entropy"]["bits"])) <= FLOAT_TOLERANCE
        fixed_ok &= abs(float(left["C_support_path_capacity_horizon_3"]) - float(right["C_support_path_capacity"]["bits"])) <= FLOAT_TOLERANCE
    cross_ok = True
    for left, right in zip(julia_entropy["cross_size_explicit_inclusions"], jax_entropy["cross_size_with_explicit_inclusion"], strict=True):
        cross_ok &= int(left["from_n"]) == int(right["from_n"]) and int(left["to_n"]) == int(right["to_n"])
        cross_ok &= left.get("pass") is True
        cross_ok &= left.get("inclusion") == list(range(int(left["from_n"])))
        cross_ok &= left.get("uniform_inclusion_total_variation_expected") == left.get("uniform_inclusion_total_variation_exact")
        cross_ok &= canonical_fraction(left["uniform_inclusion_total_variation_exact"]) == canonical_fraction(right["uniform_inclusion_total_variation"])
        cross_ok &= abs(float(left["capacity_change"]) - float(right["total_capacity_change"]["bits"])) <= FLOAT_TOLERANCE
        cross_ok &= right.get("exact_retention") is False
        cross_ok &= right.get("inclusion") == f"X_{int(right['from_n'])}->X_{int(right['to_n'])}"
    compression_julia = [float(row["log2_model_set_change"]) for row in julia_entropy["external_model_set_compression"]]
    compression_jax = [float(row["bits"]) for row in jax_entropy["external_model_set_compression"]]
    horizon_metadata_ok = (
        jax_entropy.get("internal_path_horizon") == 3
        and all(row["K0_path_entropy"].get("H") == 3 for row in jax_entropy["fixed_carrier"])
        and all(row["C_support_path_capacity"].get("H") == 3 for row in jax_entropy["fixed_carrier"])
        and all(
            row.get("K0_one_step_conditional_entropy_formula")
            == f"log2({int(row['carrier_size'])})"
            for row in julia_entropy["per_size"]
        )
        and julia_entropy.get("all_pass") is True
    )
    return {
        "fixed_n_typed_readouts": fixed_ok,
        "cross_size_explicit_inclusions": cross_ok,
        "external_compression": compression_julia == compression_jax == [-3.0, -3.0, -3.0],
        "horizon_metadata": horizon_metadata_ok,
        "causal_status_readout_only": "readouts_only" in julia_entropy["causal_status"] and "readouts_only" in jax_entropy["causal_status"],
    }


def validate_payloads(
    spec: dict[str, Any],
    card: dict[str, Any],
    prereg: dict[str, Any],
    julia: dict[str, Any],
    jax: dict[str, Any],
    smt: dict[str, Any],
) -> tuple[Checks, dict[str, Any]]:
    checks = Checks()
    statement = card["primary_object_card"]["object_statement"]
    checks.add("spec_hash_exact", sha256_file(SPEC_PATH) == EXPECTED_SPEC_SHA256, sha256_file(SPEC_PATH))
    checks.add("spec_frozen", spec.get("spec_status") == "frozen_before_execution_amendment_1", spec.get("spec_status"))
    checks.add("spec_scratch", spec.get("classification") == "scratch_diagnostic" and spec.get("promotion_candidate") is False and spec.get("formal_admission_candidate") is False, spec.get("classification"))
    checks.add("no_search_or_ratchet_execution", spec["execution_bounds"]["search_steps_run"] == 0 and spec["execution_bounds"]["ratchet_epochs_run"] == 0, spec["execution_bounds"])
    checks.add("object_statement_hash", hashlib.sha256(statement.encode()).hexdigest() == card["primary_object_card"]["object_statement_sha256"], card["primary_object_card"]["object_statement_sha256"])
    checks.add("prereg_green", prereg.get("all_pass") is True and prereg.get("errors") == [], prereg.get("errors"))
    checks.add("prereg_spec_hash", prereg.get("spec_sha256") == EXPECTED_SPEC_SHA256, prereg.get("spec_sha256"))
    checks.add("prereg_card_hash", prereg.get("object_card_sha256") == sha256_file(CARD_PATH), prereg.get("object_card_sha256"))
    checks.add(
        "prereg_nested_checks_green",
        isinstance(prereg.get("checks"), list)
        and bool(prereg["checks"])
        and all(row.get("pass") is True for row in prereg["checks"]),
        prereg.get("checks"),
    )
    checks.add(
        "prereg_source_hash",
        prereg.get("source_sha256") == sha256_file(PREREG_SOURCE),
        prereg.get("source_sha256"),
    )

    julia_common = common_lane_checks(julia, JULIA_SOURCE, JULIA_RESULT, "finite_structure_hypothesis_tournament.julia_result.v1", spec, "julia")
    jax_common = common_lane_checks(jax, JAX_SOURCE, JAX_RESULT, "finite_structure_hypothesis_tournament.jax_result.v1", spec, "jax")
    for name, value in julia_common.items():
        checks.add(f"julia_{name}", value, value)
    for name, value in jax_common.items():
        checks.add(f"jax_{name}", value, value)

    julia_core = copy.deepcopy(julia)
    reported_julia_core_hash = julia_core.pop("result_core_sha256", None)
    computed_julia_core_hash = sha256_bytes(
        json.dumps(
            julia_core,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    )
    checks.add(
        "julia_closed_json_and_core_binding",
        julia.get("scientific_checks_before_closed_json") is True
        and julia.get("closed_json_validation", {}).get("passed") is True
        and julia.get("closed_json_validation", {}).get("required_fields")
        == spec["required_result_fields"]
        and reported_julia_core_hash == computed_julia_core_hash
        and julia.get("preregistration_sha256") == sha256_file(PREREG_PATH),
        {
            "reported_core_sha256": reported_julia_core_hash,
            "computed_core_sha256": computed_julia_core_hash,
            "reported_preregistration_sha256": julia.get("preregistration_sha256"),
        },
    )
    jax_core = copy.deepcopy(jax)
    reported_jax_core_hash = jax_core.pop("result_core_sha256", None)
    checks.add(
        "jax_result_core_binding",
        reported_jax_core_hash == canonical_sha256(jax_core),
        {
            "reported": reported_jax_core_hash,
            "computed": canonical_sha256(jax_core),
        },
    )
    smt_core = copy.deepcopy(smt)
    reported_smt_core_hash = smt_core.pop("result_core_sha256", None)
    checks.add(
        "smt_result_core_binding",
        reported_smt_core_hash == canonical_sha256(smt_core),
        {
            "reported": reported_smt_core_hash,
            "computed": canonical_sha256(smt_core),
        },
    )
    tool_receipt_errors = engine_tool_receipt_errors(julia, jax)
    checks.add(
        "engine_tool_receipts_load_bearing",
        tool_receipt_errors == [],
        tool_receipt_errors,
    )

    oracle_census = {str(n): oracle_relation_census(n) for n in (1, 2, 3)}
    julia_candidates, jax_candidates = normalized_candidates(julia, jax)
    julia_all_candidate_rows = julia["candidates"]
    julia_ids = [row["id"] for row in julia_all_candidate_rows]
    julia_by_size: dict[str, int] = {}
    julia_by_semantic: dict[str, int] = {}
    for row in julia_all_candidate_rows:
        size_key = str(int(row["carrier_size"]))
        semantic_key = str(row["semantic_type"])
        julia_by_size[size_key] = julia_by_size.get(size_key, 0) + 1
        julia_by_semantic[semantic_key] = julia_by_semantic.get(semantic_key, 0) + 1
    julia_count_summary = julia["candidate_counts"]
    checks.add(
        "julia_registry_count_summary",
        julia_count_summary.get("registry_identity_unique") is True
        and len(julia_ids) == len(set(julia_ids)) == 256
        and julia_count_summary.get("total_registry_candidates") == 256
        and julia_count_summary.get("unique_registry_identities") == 256
        and julia_count_summary.get("by_carrier_size") == julia_by_size
        and julia_count_summary.get("by_semantic_type") == julia_by_semantic,
        {
            "reported_total": julia_count_summary.get("total_registry_candidates"),
            "derived_by_size": julia_by_size,
            "derived_by_semantic_type": julia_by_semantic,
        },
    )
    candidate_ids_equal = set(julia_candidates) == set(jax_candidates)
    candidate_mismatches = [
        candidate_id
        for candidate_id in sorted(set(julia_candidates) | set(jax_candidates))
        if julia_candidates.get(candidate_id) != jax_candidates.get(candidate_id)
    ]
    checks.add("candidate_identity_sets_equal", candidate_ids_equal, {"julia": len(julia_candidates), "jax": len(jax_candidates)})
    checks.add("candidate_registry_exact_243", len(julia_candidates) == len(jax_candidates) == 243, {"julia": len(julia_candidates), "jax": len(jax_candidates)})
    checks.add("candidate_semantics_exactly_equal", candidate_mismatches == [], candidate_mismatches[:20])

    julia_semantic_errors = candidate_semantic_errors(julia_candidates, oracle_census)
    jax_semantic_errors = candidate_semantic_errors(jax_candidates, oracle_census)
    checks.add("julia_candidate_semantic_oracle", julia_semantic_errors == [], julia_semantic_errors[:20])
    checks.add("jax_candidate_semantic_oracle", jax_semantic_errors == [], jax_semantic_errors[:20])

    julia_mss, jax_mss = normalize_mss(julia, jax)
    mss_mismatches = [
        key
        for key in sorted(set(julia_mss) | set(jax_mss))
        if julia_mss.get(key) != jax_mss.get(key)
    ]
    checks.add("mss_all_fifteen_arms", len(julia_mss) == len(jax_mss) == 15, {"julia": len(julia_mss), "jax": len(jax_mss)})
    checks.add("mss_frontiers_exactly_equal", mss_mismatches == [], mss_mismatches)

    independent_mss = oracle_mss(julia_candidates, spec)
    julia_mss_oracle_mismatches = [
        key
        for key in sorted(set(julia_mss) | set(independent_mss))
        if julia_mss.get(key) != independent_mss.get(key)
    ]
    jax_mss_oracle_mismatches = [
        key
        for key in sorted(set(jax_mss) | set(independent_mss))
        if jax_mss.get(key) != independent_mss.get(key)
    ]
    checks.add("julia_mss_independent_oracle", julia_mss_oracle_mismatches == [], julia_mss_oracle_mismatches)
    checks.add("jax_mss_independent_oracle", jax_mss_oracle_mismatches == [], jax_mss_oracle_mismatches)
    julia_raw_mss_errors = julia_raw_mss_class_errors(
        julia, julia_candidates, spec, (1, 2, 3)
    )
    checks.add(
        "julia_raw_mss_equivalence_classes",
        julia_raw_mss_errors == [],
        julia_raw_mss_errors,
    )

    oracle_errors: list[str] = []
    expected_registry = {"1": 6, "2": 24, "3": 213}
    for n in ("1", "2", "3"):
        oracle = oracle_census[n]
        jax_count = jax["candidate_counts"][n]
        julia_count = julia["candidate_counts"]["relation_census"][n]
        if jax_count["relation_canonical_masks"] != oracle["canonical_masks"]:
            oracle_errors.append(f"jax_masks_{n}")
        if int(jax_count["relation_isomorphism_classes_each_semantic_type"]) != oracle["isomorphism_class_count"]:
            oracle_errors.append(f"jax_iso_{n}")
        if int(julia_count["static"]["isomorphism_class_count"]) != oracle["isomorphism_class_count"] or int(julia_count["transition"]["isomorphism_class_count"]) != oracle["isomorphism_class_count"]:
            oracle_errors.append(f"julia_iso_{n}")
        for semantic_name in ("static", "transition"):
            semantic_count = julia_count[semantic_name]
            if int(semantic_count.get("labelled_count", -1)) != oracle["labelled_count"]:
                oracle_errors.append(f"julia_labelled_{semantic_name}_{n}")
            if int(semantic_count.get("class_multiplicity_sum", -1)) != oracle["labelled_count"]:
                oracle_errors.append(f"julia_multiplicity_{semantic_name}_{n}")
            if semantic_count.get("orbit_stabilizer_pass") is not True:
                oracle_errors.append(f"julia_orbit_stabilizer_{semantic_name}_{n}")
        if jax_count["relation_automorphism_order_histogram_per_semantic_type"] != oracle["automorphism_order_histogram"]:
            oracle_errors.append(f"jax_aut_hist_{n}")
        if int(jax_count["total_registry_identities"]) != expected_registry[n] or int(julia["candidate_counts"]["by_carrier_size"][n]) != expected_registry[n]:
            oracle_errors.append(f"registry_{n}")
    checks.add("independent_python_relation_oracle", oracle_errors == [], oracle_errors)
    checks.add("named_kernel_collision_counts", [julia["candidate_counts"]["kernel_alias_collapse"][str(n)]["registry_identities"] for n in (1, 2, 3)] == [1, 3, 4] and [jax["candidate_counts"][str(n)]["named_kernel_registry_identities"] for n in (1, 2, 3)] == [1, 3, 4], [1, 3, 4])

    alias_errors = raw_alias_errors(julia, jax)
    raw_orbit_errors = raw_jax_orbit_errors(jax)
    raw_representation_errors = jax_raw_representation_errors(jax)
    summary_errors = jax_summary_errors(jax, oracle_census)
    checks.add("raw_alias_provenance", alias_errors == [], alias_errors[:20])
    checks.add("jax_raw_automorphism_orbits", raw_orbit_errors == [], raw_orbit_errors[:20])
    checks.add("jax_raw_duplicate_representations", raw_representation_errors == [], raw_representation_errors[:20])
    checks.add("jax_exhaustive_summary_oracle", summary_errors == [], summary_errors)

    n4_julia_errors, n4_julia_candidates = named_n4_julia_errors(julia)
    n4_julia_mss = normalize_julia_mss_for_sizes(julia, {4})
    n4_independent_mss = oracle_mss(n4_julia_candidates, spec, (4,))
    n4_mss_mismatches = [
        key
        for key in sorted(set(n4_julia_mss) | set(n4_independent_mss))
        if n4_julia_mss.get(key) != n4_independent_mss.get(key)
    ]
    n4_jax_errors = named_n4_jax_errors(jax)
    n4_julia_raw_mss_errors = julia_raw_mss_class_errors(
        julia, n4_julia_candidates, spec, (4,)
    )
    checks.add("julia_named_n4_semantic_oracle", n4_julia_errors == [], n4_julia_errors)
    checks.add("julia_named_n4_mss_oracle", n4_mss_mismatches == [], n4_mss_mismatches)
    checks.add("julia_named_n4_raw_mss_equivalence_classes", n4_julia_raw_mss_errors == [], n4_julia_raw_mss_errors)
    checks.add("jax_named_n4_boundary_oracle", n4_jax_errors == [], n4_jax_errors)
    checks.add(
        "n4_scope_is_named_boundary_not_full_cross_runtime",
        spec["execution_bounds"]["exhaustive_carrier_sizes"] == [1, 2, 3]
        and spec["execution_bounds"]["named_boundary_carrier_sizes"] == [4],
        spec["execution_bounds"],
    )

    append = append_comparison(julia, jax, append_oracle())
    for name, value in append.items():
        checks.add(f"append_{name}", value, value)
    checks.add(
        "jax_append_nested_all_pass",
        jax["fixed_carrier_internal_append_chain"].get("all_pass") is True,
        jax["fixed_carrier_internal_append_chain"].get("all_pass"),
    )
    gate_oracle = external_gate_oracle()
    julia_gate_counts = [int(row["model_count"]) for row in julia["external_constraint_controls"]["stages"]]
    jax_gate_counts = [int(row["model_count"]) for row in jax["external_constraint_controls"]["gates"]]
    checks.add("external_gate_counts", julia_gate_counts == jax_gate_counts == gate_oracle == [512, 64, 8, 1], {"julia": julia_gate_counts, "jax": jax_gate_counts})
    checks.add("external_gate_internal_immutability", julia["external_constraint_controls"]["all_pass"] is True and jax["external_constraint_controls"]["survivor_internal_structures_unchanged"] is True, True)
    external_receipt_errors = external_gate_receipt_errors(jax)
    checks.add("jax_external_gate_receipt_oracle", external_receipt_errors == [], external_receipt_errors)

    entropy = entropy_comparison(julia, jax)
    for name, value in entropy.items():
        checks.add(f"entropy_{name}", value, value)

    smt_errors, smt_matrix = validate_smt(smt)
    smt_common = common_lane_checks(smt, SMT_SOURCE, SMT_RESULT, "finite_structure_hypothesis_tournament.smt.v1", spec, "smt")
    # SMT has a distinct provenance shape; only reuse the universal checks.
    for name in ("schema", "all_pass", "classification", "claim_ceiling", "blocked_consumers", "spec_hash", "source_path", "source_hash", "cwd", "command", "errors_clear"):
        checks.add(f"smt_{name}", smt_common[name], smt_common[name])
    checks.add("smt_full_query_matrix", smt_errors == [], smt_errors)
    expected_smt_witnesses = sum(row[4] for row in SMT_PLAN)
    checks.add("smt_total_witnesses", smt["tool_receipts"]["z3"]["sat_permutations_extracted"] == expected_smt_witnesses and smt["tool_receipts"]["cvc5"]["sat_permutations_extracted"] == expected_smt_witnesses, smt["tool_receipts"])

    discrepancy_groups = {
        "cross_lane_candidates": candidate_mismatches,
        "cross_lane_mss": mss_mismatches,
        "engine_tool_receipts": tool_receipt_errors,
        "relation_census_oracle": oracle_errors,
        "julia_candidate_oracle": julia_semantic_errors,
        "jax_candidate_oracle": jax_semantic_errors,
        "julia_mss_oracle": julia_mss_oracle_mismatches,
        "jax_mss_oracle": jax_mss_oracle_mismatches,
        "julia_raw_mss_classes": julia_raw_mss_errors,
        "alias_provenance": alias_errors,
        "jax_raw_orbits": raw_orbit_errors,
        "jax_raw_representations": raw_representation_errors,
        "jax_summary_oracle": summary_errors,
        "julia_named_n4": n4_julia_errors,
        "julia_named_n4_mss": n4_mss_mismatches,
        "julia_named_n4_raw_mss_classes": n4_julia_raw_mss_errors,
        "jax_named_n4": n4_jax_errors,
        "jax_external_gate_receipt": external_receipt_errors,
        "smt": smt_errors,
        "append": [name for name, value in append.items() if not value],
        "entropy": [name for name, value in entropy.items() if not value],
    }
    mismatch_count = sum(len(values) for values in discrepancy_groups.values())
    comparison = {
        "mismatch_count": mismatch_count,
        "candidate_count": len(julia_candidates),
        "candidate_mismatches": candidate_mismatches,
        "mss_mismatches": mss_mismatches,
        "oracle_errors": oracle_errors,
        "engine_tool_receipt_errors": tool_receipt_errors,
        "julia_candidate_oracle_errors": julia_semantic_errors,
        "jax_candidate_oracle_errors": jax_semantic_errors,
        "julia_mss_oracle_mismatches": julia_mss_oracle_mismatches,
        "jax_mss_oracle_mismatches": jax_mss_oracle_mismatches,
        "julia_raw_mss_class_errors": julia_raw_mss_errors,
        "alias_errors": alias_errors,
        "jax_raw_orbit_errors": raw_orbit_errors,
        "jax_raw_representation_errors": raw_representation_errors,
        "jax_summary_errors": summary_errors,
        "julia_named_n4_errors": n4_julia_errors,
        "julia_named_n4_mss_mismatches": n4_mss_mismatches,
        "julia_named_n4_raw_mss_class_errors": n4_julia_raw_mss_errors,
        "jax_named_n4_errors": n4_jax_errors,
        "jax_external_gate_receipt_errors": external_receipt_errors,
        "smt_errors": smt_errors,
        "discrepancy_groups": discrepancy_groups,
        "component_discrepancy_counts": {
            "cross_lane": len(candidate_mismatches) + len(mss_mismatches),
            "engine_tool_receipts": len(tool_receipt_errors),
            "julia_oracle": len(julia_semantic_errors) + len(julia_mss_oracle_mismatches) + len(julia_raw_mss_errors) + len(n4_julia_errors) + len(n4_mss_mismatches) + len(n4_julia_raw_mss_errors),
            "jax_oracle": len(jax_semantic_errors) + len(jax_mss_oracle_mismatches) + len(raw_orbit_errors) + len(raw_representation_errors) + len(summary_errors) + len(n4_jax_errors) + len(external_receipt_errors),
            "shared_alias_provenance": len(alias_errors),
            "relation_census_oracle": len(oracle_errors),
            "smt_oracle": len(smt_errors),
            "append_oracle": sum(not value for value in append.values()),
            "entropy_oracle": sum(not value for value in entropy.values()),
        },
        "relation_oracle": oracle_census,
        "append": append,
        "entropy": entropy,
        "smt_query_matrix": smt_matrix,
    }
    return checks, comparison


def corruption_controls(
    spec: dict[str, Any],
    card: dict[str, Any],
    prereg: dict[str, Any],
    julia: dict[str, Any],
    jax: dict[str, Any],
    smt: dict[str, Any],
) -> dict[str, bool]:
    def rejected_raw(text: str) -> bool:
        try:
            strict_load_bytes(text.encode())
        except Exception:
            return True
        return False

    def validation_error_names(
        julia_value: dict[str, Any] = julia,
        jax_value: dict[str, Any] = jax,
        smt_value: dict[str, Any] = smt,
        prereg_value: dict[str, Any] = prereg,
    ) -> set[str]:
        try:
            mutated_checks, _ = validate_payloads(
                spec, card, prereg_value, julia_value, jax_value, smt_value
            )
            return set(mutated_checks.errors)
        except Exception as exc:
            return {f"gate_exception:{type(exc).__name__}"}

    def julia_candidate(value: dict[str, Any], candidate_id: str) -> dict[str, Any]:
        return next(row for row in value["candidates"] if row["id"] == candidate_id)

    def jax_candidate(value: dict[str, Any], n: int, candidate_id: str) -> dict[str, Any]:
        return next(
            row
            for row in value["registry_census"][str(n)]
            if row["candidate_id"] == candidate_id
        )

    mutated_candidate = copy.deepcopy(jax)
    mutated_candidate["registry_census"]["2"][0]["automorphism"]["order"] += 1
    candidate_errors = validation_error_names(jax_value=mutated_candidate)

    mutated_mss = copy.deepcopy(jax)
    mutated_mss["mss_frontiers"]["2"]["signature_registered"]["frontier_classes"][0]["members"] = ["C_2"]
    mss_errors = validation_error_names(jax_value=mutated_mss)

    coordinated_missing_julia = copy.deepcopy(julia)
    coordinated_missing_jax = copy.deepcopy(jax)
    coordinated_missing_julia["candidates"] = [
        row for row in coordinated_missing_julia["candidates"] if row["id"] != "R_3_000000001"
    ]
    coordinated_missing_jax["registry_census"]["3"] = [
        row
        for row in coordinated_missing_jax["registry_census"]["3"]
        if row["candidate_id"] != "R_3_000000001"
    ]
    coordinated_missing_errors = validation_error_names(
        julia_value=coordinated_missing_julia, jax_value=coordinated_missing_jax
    )

    coordinated_mss_julia = copy.deepcopy(julia)
    coordinated_mss_jax = copy.deepcopy(jax)
    next(
        row
        for row in coordinated_mss_julia["mss_arms"]
        if int(row["carrier_size"]) == 2 and row["arm_id"] == "signature_registered"
    )["frontier_classes"] = [["C_2"]]
    coordinated_mss_jax["mss_frontiers"]["2"]["signature_registered"]["frontier_classes"] = [
        {"members": ["C_2"]}
    ]
    coordinated_mss_errors = validation_error_names(
        julia_value=coordinated_mss_julia, jax_value=coordinated_mss_jax
    )

    coordinated_partition_julia = copy.deepcopy(julia)
    coordinated_partition_jax = copy.deepcopy(jax)
    julia_candidate(coordinated_partition_julia, "U_2")["distinction_partitions"]["automorphism_orbits"] = [[0], [1]]
    jax_candidate(coordinated_partition_jax, 2, "U_2")["distinction_partitions"]["automorphism_orbits"] = [[0], [1]]
    coordinated_partition_errors = validation_error_names(
        julia_value=coordinated_partition_julia, jax_value=coordinated_partition_jax
    )

    erased_aliases = copy.deepcopy(jax)
    erased_k0 = jax_candidate(erased_aliases, 1, "K0_1")
    erased_k0["provenance_aliases"] = []
    erased_k0["named_family_presentations"] = []
    erased_alias_errors = validation_error_names(jax_value=erased_aliases)

    corrupted_raw_orbit = copy.deepcopy(jax)
    jax_candidate(corrupted_raw_orbit, 3, "U_3")["automorphism"]["orbits"] = [[0], [1], [2]]
    corrupted_raw_orbit_errors = validation_error_names(jax_value=corrupted_raw_orbit)

    corrupted_summary = copy.deepcopy(jax)
    corrupted_summary["candidate_counts"]["3"]["transition_viability_counts_labelled"]["V_serial"] = 999
    corrupted_summary_errors = validation_error_names(jax_value=corrupted_summary)

    corrupted_entropy = copy.deepcopy(jax)
    corrupted_entropy["entropy_capacity_readouts"]["fixed_carrier"][2]["K0_fixed_n_state_entropy_change_bits"] = 123.0
    corrupted_entropy_errors = validation_error_names(jax_value=corrupted_entropy)

    corrupted_nested_append = copy.deepcopy(jax)
    corrupted_nested_append["fixed_carrier_internal_append_chain"]["all_pass"] = False
    corrupted_nested_append_errors = validation_error_names(jax_value=corrupted_nested_append)

    coordinated_append_julia = copy.deepcopy(julia)
    coordinated_append_jax = copy.deepcopy(jax)
    coordinated_append_julia["fixed_carrier_internal_append_chain"]["steps"][2]["aut_order"] = 24
    coordinated_append_jax["fixed_carrier_internal_append_chain"]["steps"][2]["automorphism_order"] = 24
    coordinated_append_errors = validation_error_names(
        julia_value=coordinated_append_julia, jax_value=coordinated_append_jax
    )

    corrupted_n4 = copy.deepcopy(jax)
    corrupted_n4["named_relation_controls_at_n4"]["controls"][3]["automorphism_order"] = 24
    corrupted_n4_errors = validation_error_names(jax_value=corrupted_n4)

    coordinated_external_julia = copy.deepcopy(julia)
    coordinated_external_jax = copy.deepcopy(jax)
    coordinated_external_julia["external_constraint_controls"]["stages"][1]["model_count"] = 999
    coordinated_external_jax["external_constraint_controls"]["gates"][1]["model_count"] = 999
    coordinated_external_errors = validation_error_names(
        julia_value=coordinated_external_julia, jax_value=coordinated_external_jax
    )

    coordinated_strict_julia = copy.deepcopy(julia)
    coordinated_strict_jax = copy.deepcopy(jax)
    coordinated_strict_julia["fixed_carrier_internal_append_chain"]["adjacent_checks"][1]["strict"] = False
    coordinated_strict_jax["fixed_carrier_internal_append_chain"]["adjacent_checks"][1]["strict"] = False
    coordinated_strict_errors = validation_error_names(
        julia_value=coordinated_strict_julia, jax_value=coordinated_strict_jax
    )

    julia_nested_red = copy.deepcopy(julia)
    julia_nested_red["fixed_carrier_internal_append_chain"]["all_pass"] = False
    julia_nested_red_errors = validation_error_names(julia_value=julia_nested_red)

    jax_subordinate_red = copy.deepcopy(jax)
    jax_subordinate_red["fixed_carrier_internal_append_chain"]["all_append_subgroups"] = False
    jax_subordinate_red_errors = validation_error_names(jax_value=jax_subordinate_red)

    corrupted_labelled_orbit = copy.deepcopy(jax)
    orbit_row = jax_candidate(corrupted_labelled_orbit, 3, "C_3")
    orbit_row["labelled_orbit_members"] = [511]
    orbit_row["labelled_orbit_size"] = 999
    corrupted_labelled_orbit_errors = validation_error_names(jax_value=corrupted_labelled_orbit)

    corrupted_support_matrix = copy.deepcopy(jax)
    jax_candidate(corrupted_support_matrix, 2, "C_2")["support_matrix"] = [[0, 0], [0, 0]]
    corrupted_support_matrix_errors = validation_error_names(jax_value=corrupted_support_matrix)

    corrupted_kernel_numerators = copy.deepcopy(jax)
    jax_candidate(corrupted_kernel_numerators, 3, "K0_3")["integer_numerators"][0][0] = 999
    corrupted_kernel_numerator_errors = validation_error_names(jax_value=corrupted_kernel_numerators)

    corrupted_julia_classes = copy.deepcopy(julia)
    next(
        row
        for row in corrupted_julia_classes["mss_arms"]
        if int(row["carrier_size"]) == 2 and row["arm_id"] == "signature_registered"
    )["viable_equivalence_classes"][0][0] = "BOGUS"
    corrupted_julia_class_errors = validation_error_names(julia_value=corrupted_julia_classes)

    corrupted_horizon = copy.deepcopy(jax)
    corrupted_horizon["entropy_capacity_readouts"]["fixed_carrier"][2]["K0_path_entropy"]["H"] = 999
    corrupted_horizon_errors = validation_error_names(jax_value=corrupted_horizon)

    corrupted_external_manifest = copy.deepcopy(jax)
    corrupted_external_manifest["external_constraint_controls"]["gates"][1]["survivor_internal_manifest_sha256"] = "0" * 64
    corrupted_external_manifest_errors = validation_error_names(jax_value=corrupted_external_manifest)

    corrupted_n4_alias = copy.deepcopy(julia)
    julia_candidate(corrupted_n4_alias, "K0_4")["aliases"] = []
    corrupted_n4_alias_errors = validation_error_names(julia_value=corrupted_n4_alias)

    corrupted_julia_census = copy.deepcopy(julia)
    corrupted_julia_census["candidate_counts"]["relation_census"]["3"]["static"]["labelled_count"] = 999
    corrupted_julia_census["candidate_counts"]["relation_census"]["3"]["static"]["class_multiplicity_sum"] = 999
    corrupted_julia_census["candidate_counts"]["relation_census"]["3"]["static"]["orbit_stabilizer_pass"] = False
    corrupted_julia_census_errors = validation_error_names(julia_value=corrupted_julia_census)

    corrupted_removed_witness = copy.deepcopy(jax)
    corrupted_removed_witness["fixed_carrier_internal_append_chain"]["adjacent_checks"][1]["removed_witness"] = [0, 1, 2, 3]
    corrupted_removed_witness_errors = validation_error_names(jax_value=corrupted_removed_witness)

    corrupted_julia_replacement = copy.deepcopy(julia)
    corrupted_julia_replacement["fixed_carrier_internal_append_chain"]["replacement_control"]["witness_replay_pass"] = False
    corrupted_julia_replacement["fixed_carrier_internal_append_chain"]["replacement_control"]["direct_status"] = "unsat"
    corrupted_julia_replacement_errors = validation_error_names(julia_value=corrupted_julia_replacement)

    corrupted_jax_replacement = copy.deepcopy(jax)
    corrupted_jax_replacement["fixed_carrier_internal_append_chain"]["replacement_control"]["direct_replay"] = False
    corrupted_jax_replacement_errors = validation_error_names(jax_value=corrupted_jax_replacement)

    corrupted_jax_append_orbits = copy.deepcopy(jax)
    corrupted_jax_append_orbits["fixed_carrier_internal_append_chain"]["steps"][2]["automorphism_orbits"] = [[0, 1, 2, 3]]
    corrupted_jax_append_orbit_errors = validation_error_names(jax_value=corrupted_jax_append_orbits)

    corrupted_julia_entropy_summary = copy.deepcopy(julia)
    corrupted_julia_entropy_summary["entropy_capacity_readouts"]["per_size"][2]["fixed_n_pass"] = False
    corrupted_julia_entropy_summary["entropy_capacity_readouts"]["per_size"][2]["K0_fixed_n_state_entropy_change_float"] = 123.0
    corrupted_julia_entropy_summary_errors = validation_error_names(julia_value=corrupted_julia_entropy_summary)

    corrupted_jax_entropy_formula = copy.deepcopy(jax)
    corrupted_jax_entropy_formula["entropy_capacity_readouts"]["fixed_carrier"][2]["K0_path_entropy"]["formula"] = "teleology"
    corrupted_jax_entropy_formula_errors = validation_error_names(jax_value=corrupted_jax_entropy_formula)

    corrupted_julia_tool_receipt = copy.deepcopy(julia)
    corrupted_julia_tool_receipt["tool_receipts"][0]["load_bearing"] = False
    corrupted_julia_tool_receipt_errors = validation_error_names(julia_value=corrupted_julia_tool_receipt)

    corrupted_jax_tool_receipt = copy.deepcopy(jax)
    corrupted_jax_tool_receipt["tool_receipts"][1]["load_bearing"] = False
    corrupted_jax_tool_receipt_errors = validation_error_names(jax_value=corrupted_jax_tool_receipt)

    corrupted_prereg_nested = copy.deepcopy(prereg)
    corrupted_prereg_nested["checks"][0]["pass"] = False
    corrupted_prereg_nested_errors = validation_error_names(prereg_value=corrupted_prereg_nested)

    corrupted_julia_scientific_close = copy.deepcopy(julia)
    corrupted_julia_scientific_close["scientific_checks_before_closed_json"] = False
    corrupted_julia_scientific_close_errors = validation_error_names(julia_value=corrupted_julia_scientific_close)

    corrupted_julia_closed_json = copy.deepcopy(julia)
    corrupted_julia_closed_json["closed_json_validation"]["passed"] = False
    corrupted_julia_closed_json_errors = validation_error_names(julia_value=corrupted_julia_closed_json)

    corrupted_julia_core_hash = copy.deepcopy(julia)
    corrupted_julia_core_hash["result_core_sha256"] = "0" * 64
    corrupted_julia_core_hash_errors = validation_error_names(julia_value=corrupted_julia_core_hash)

    corrupted_julia_prereg_hash = copy.deepcopy(julia)
    corrupted_julia_prereg_hash["preregistration_sha256"] = "0" * 64
    corrupted_julia_prereg_hash_errors = validation_error_names(julia_value=corrupted_julia_prereg_hash)

    corrupted_julia_registry_summary = copy.deepcopy(julia)
    corrupted_julia_registry_summary["candidate_counts"]["registry_identity_unique"] = False
    corrupted_julia_registry_summary_errors = validation_error_names(julia_value=corrupted_julia_registry_summary)

    corrupted_julia_cross_size = copy.deepcopy(julia)
    corrupted_julia_cross_size["entropy_capacity_readouts"]["cross_size_explicit_inclusions"][0]["pass"] = False
    corrupted_julia_cross_size_errors = validation_error_names(julia_value=corrupted_julia_cross_size)

    corrupted_jax_core_hash = copy.deepcopy(jax)
    corrupted_jax_core_hash["result_core_sha256"] = "0" * 64
    corrupted_jax_core_hash_errors = validation_error_names(jax_value=corrupted_jax_core_hash)

    mutated_smt = copy.deepcopy(smt)
    mutated_smt["queries"][4]["z3"]["status"] = "unknown"
    smt_errors, _ = validate_smt(mutated_smt)

    mutated_witness = copy.deepcopy(smt)
    mutated_witness["queries"][4]["z3"]["witnesses"][0]["permutation"] = [0, 0, 2, 3]
    witness_errors, _ = validate_smt(mutated_witness)

    mutated_smt_oracle = copy.deepcopy(smt)
    mutated_smt_oracle["queries"][4]["oracle"]["witnesses"] = []
    smt_oracle_errors, _ = validate_smt(mutated_smt_oracle)

    mutated_smt_hashes = copy.deepcopy(smt)
    mutated_smt_hashes["query_plan_sha256"] = "0" * 64
    mutated_smt_hashes["structure_replay_sha256"] = "0" * 64
    smt_hash_errors, _ = validate_smt(mutated_smt_hashes)

    mutated_smt_nested_replay = copy.deepcopy(smt)
    mutated_smt_nested_replay["queries"][4]["z3"]["witnesses"][0]["replay"]["query_satisfied"] = False
    smt_nested_replay_errors, _ = validate_smt(mutated_smt_nested_replay)

    mutated_smt_counts = copy.deepcopy(smt)
    mutated_smt_counts["candidate_counts"]["all_carrier_permutations"] = 999
    smt_count_errors, _ = validate_smt(mutated_smt_counts)

    mutated_smt_spec_checks = copy.deepcopy(smt)
    mutated_smt_spec_checks["spec_contract_checks"]["append_orders_match"] = False
    smt_spec_check_errors, _ = validate_smt(mutated_smt_spec_checks)

    mutated_smt_errors_field = copy.deepcopy(smt)
    mutated_smt_errors_field["errors"] = ["scientific failure"]
    mutated_smt_errors_field_names = validation_error_names(smt_value=mutated_smt_errors_field)

    mutated_smt_core_hash = copy.deepcopy(smt)
    mutated_smt_core_hash["result_core_sha256"] = "0" * 64
    mutated_smt_core_hash_names = validation_error_names(smt_value=mutated_smt_core_hash)

    mutated_lane_red = copy.deepcopy(jax)
    mutated_lane_red["all_pass"] = False
    lane_checks = common_lane_checks(mutated_lane_red, JAX_SOURCE, JAX_RESULT, "finite_structure_hypothesis_tournament.jax_result.v1", spec, "jax")

    mutated_blocked = copy.deepcopy(jax)
    mutated_blocked["blocked_consumers"] = mutated_blocked["blocked_consumers"][:-1]
    blocked_checks = common_lane_checks(mutated_blocked, JAX_SOURCE, JAX_RESULT, "finite_structure_hypothesis_tournament.jax_result.v1", spec, "jax")

    mutated_source = copy.deepcopy(jax)
    mutated_source["source_sha256"] = "0" * 64
    source_checks = common_lane_checks(mutated_source, JAX_SOURCE, JAX_RESULT, "finite_structure_hypothesis_tournament.jax_result.v1", spec, "jax")

    duplicate_candidate_rejected = False
    duplicated_registry = copy.deepcopy(jax)
    duplicated_registry["registry_census"]["1"].append(
        copy.deepcopy(duplicated_registry["registry_census"]["1"][0])
    )
    try:
        normalized_candidates(julia, duplicated_registry)
    except GateError:
        duplicate_candidate_rejected = True

    duplicate_top = '{"all_pass":true,"all_pass":false}'
    duplicate_nested = '{"lane":{"source_sha256":"a","source_sha256":"b"}}'
    nan_payload = '{"max_divergence":NaN}'
    infinity_payload = '{"entropy":Infinity}'
    return {
        "duplicate_top_level_key_rejected": rejected_raw(duplicate_top),
        "duplicate_nested_key_rejected": rejected_raw(duplicate_nested),
        "nan_rejected": rejected_raw(nan_payload),
        "infinity_rejected": rejected_raw(infinity_payload),
        "mutated_engine_metric_rejected": "candidate_semantics_exactly_equal" in candidate_errors and "jax_candidate_semantic_oracle" in candidate_errors,
        "mutated_mss_frontier_rejected": "mss_frontiers_exactly_equal" in mss_errors and "jax_mss_independent_oracle" in mss_errors,
        "coordinated_candidate_deletion_rejected": "candidate_registry_exact_243" in coordinated_missing_errors and "julia_candidate_semantic_oracle" in coordinated_missing_errors and "jax_candidate_semantic_oracle" in coordinated_missing_errors,
        "coordinated_wrong_mss_rejected": "julia_mss_independent_oracle" in coordinated_mss_errors and "jax_mss_independent_oracle" in coordinated_mss_errors,
        "coordinated_malformed_partition_rejected": "julia_candidate_semantic_oracle" in coordinated_partition_errors and "jax_candidate_semantic_oracle" in coordinated_partition_errors,
        "erased_alias_provenance_rejected": "raw_alias_provenance" in erased_alias_errors,
        "corrupted_raw_orbit_rejected": "jax_raw_automorphism_orbits" in corrupted_raw_orbit_errors,
        "corrupted_viability_summary_rejected": "jax_exhaustive_summary_oracle" in corrupted_summary_errors,
        "corrupted_fixed_n_entropy_rejected": "entropy_fixed_n_typed_readouts" in corrupted_entropy_errors,
        "red_nested_append_receipt_rejected": "jax_append_nested_all_pass" in corrupted_nested_append_errors,
        "coordinated_append_order_rejected": "append_orders_equal_oracle" in coordinated_append_errors,
        "corrupted_named_n4_boundary_rejected": "jax_named_n4_boundary_oracle" in corrupted_n4_errors,
        "coordinated_external_gate_count_rejected": "external_gate_counts" in coordinated_external_errors,
        "coordinated_append_strictness_rejected": "append_julia_adjacent_matches_oracle" in coordinated_strict_errors and "append_jax_adjacent_matches_oracle" in coordinated_strict_errors,
        "julia_nested_append_red_rejected": "append_julia_nested_receipt_green" in julia_nested_red_errors,
        "jax_subordinate_append_red_rejected": "append_jax_nested_receipt_green" in jax_subordinate_red_errors,
        "corrupted_labelled_orbit_members_rejected": "jax_raw_duplicate_representations" in corrupted_labelled_orbit_errors,
        "corrupted_support_matrix_rejected": "jax_raw_duplicate_representations" in corrupted_support_matrix_errors,
        "corrupted_kernel_numerators_rejected": "jax_raw_duplicate_representations" in corrupted_kernel_numerator_errors,
        "corrupted_julia_equivalence_classes_rejected": "julia_raw_mss_equivalence_classes" in corrupted_julia_class_errors,
        "corrupted_entropy_horizon_rejected": "entropy_horizon_metadata" in corrupted_horizon_errors,
        "corrupted_external_manifest_rejected": "jax_external_gate_receipt_oracle" in corrupted_external_manifest_errors,
        "corrupted_n4_aliases_rejected": "julia_named_n4_semantic_oracle" in corrupted_n4_alias_errors,
        "corrupted_julia_relation_census_rejected": "independent_python_relation_oracle" in corrupted_julia_census_errors,
        "corrupted_jax_removed_witness_rejected": "append_jax_removed_witnesses_replay" in corrupted_removed_witness_errors,
        "corrupted_julia_replacement_receipt_rejected": "append_julia_replacement_receipt_green" in corrupted_julia_replacement_errors,
        "corrupted_jax_replacement_receipt_rejected": "append_jax_replacement_receipt_green" in corrupted_jax_replacement_errors,
        "corrupted_jax_append_orbits_rejected": "append_jax_step_automorphism_orbits" in corrupted_jax_append_orbit_errors,
        "corrupted_julia_entropy_summary_rejected": "entropy_fixed_n_typed_readouts" in corrupted_julia_entropy_summary_errors,
        "corrupted_jax_entropy_formula_rejected": "entropy_fixed_n_typed_readouts" in corrupted_jax_entropy_formula_errors,
        "corrupted_julia_tool_receipt_rejected": "engine_tool_receipts_load_bearing" in corrupted_julia_tool_receipt_errors,
        "corrupted_jax_tool_receipt_rejected": "engine_tool_receipts_load_bearing" in corrupted_jax_tool_receipt_errors,
        "corrupted_prereg_nested_check_rejected": "prereg_nested_checks_green" in corrupted_prereg_nested_errors,
        "corrupted_julia_scientific_close_rejected": "julia_closed_json_and_core_binding" in corrupted_julia_scientific_close_errors,
        "corrupted_julia_closed_json_rejected": "julia_closed_json_and_core_binding" in corrupted_julia_closed_json_errors,
        "corrupted_julia_core_hash_rejected": "julia_closed_json_and_core_binding" in corrupted_julia_core_hash_errors,
        "corrupted_julia_prereg_hash_rejected": "julia_closed_json_and_core_binding" in corrupted_julia_prereg_hash_errors,
        "corrupted_julia_registry_summary_rejected": "julia_registry_count_summary" in corrupted_julia_registry_summary_errors,
        "corrupted_julia_cross_size_receipt_rejected": "entropy_cross_size_explicit_inclusions" in corrupted_julia_cross_size_errors,
        "corrupted_jax_core_hash_rejected": "jax_result_core_binding" in corrupted_jax_core_hash_errors,
        "mutated_source_hash_rejected": source_checks["source_hash"] is False,
        "double_counted_candidate_id_rejected": duplicate_candidate_rejected,
        "solver_unknown_rejected": bool(smt_errors),
        "bad_solver_witness_rejected": bool(witness_errors),
        "corrupted_smt_oracle_witnesses_rejected": any(error.startswith("oracle_witnesses:") for error in smt_oracle_errors),
        "corrupted_smt_binding_hashes_rejected": "query_plan_sha256" in smt_hash_errors and "structure_replay_sha256" in smt_hash_errors,
        "corrupted_smt_nested_replay_rejected": any(error.startswith("nested_replay:") for error in smt_nested_replay_errors),
        "corrupted_smt_candidate_counts_rejected": "candidate_counts" in smt_count_errors,
        "corrupted_smt_spec_contract_checks_rejected": "spec_contract_checks" in smt_spec_check_errors,
        "corrupted_smt_errors_field_rejected": "smt_errors_clear" in mutated_smt_errors_field_names,
        "corrupted_smt_core_hash_rejected": "smt_result_core_binding" in mutated_smt_core_hash_names,
        "red_lane_rejected": lane_checks["all_pass"] is False,
        "blocked_consumer_removal_rejected": blocked_checks["blocked_consumers"] is False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    fixed_inputs = [SPEC_PATH, CARD_PATH, PREREG_PATH, JULIA_SOURCE, JULIA_RESULT, JAX_SOURCE, JAX_RESULT, SMT_SOURCE, SMT_RESULT]
    before = {str(path): sha256_file(path) for path in fixed_inputs}
    spec, spec_meta = strict_load(SPEC_PATH)
    card, card_meta = strict_load(CARD_PATH)
    prereg, prereg_meta = strict_load(PREREG_PATH)
    julia, julia_meta = strict_load(JULIA_RESULT)
    jax, jax_meta = strict_load(JAX_RESULT)
    smt, smt_meta = strict_load(SMT_RESULT)

    checks, comparison = validate_payloads(spec, card, prereg, julia, jax, smt)
    controls = corruption_controls(spec, card, prereg, julia, jax, smt)
    for name, passed in controls.items():
        checks.add(f"corruption_{name}", passed, passed)

    scope_checks = {
        "zero_execution_lev_receipt_rejected_by_unit_guard": not lev_events_valid([]),
        "pytorch_omission_frozen_by_declared_mode": spec["engine_mode"]["pytorch"].startswith("not_scoped_by_mode"),
        "n4_is_named_boundary_not_full_cross_runtime": spec["execution_bounds"]["named_boundary_carrier_sizes"] == [4]
        and spec["execution_bounds"]["exhaustive_carrier_sizes"] == [1, 2, 3],
    }
    for name, passed in scope_checks.items():
        checks.add(f"scope_{name}", passed, passed)

    after = {str(path): sha256_file(path) for path in fixed_inputs}
    checks.add("inputs_unchanged_during_controller", before == after, {"before": before, "after": after})
    checks.add(
        "fixed_inputs_are_regular_worktree_files",
        all(not path.is_symlink() and path.resolve().is_relative_to(REPO.resolve()) for path in fixed_inputs),
        [str(path) for path in fixed_inputs],
    )
    all_pass = not checks.errors
    qualified_claim_ceiling = (
        spec["claim_ceiling"]
        + " In this controller, Julia/JAX agreement means exhaustive candidate and MSS parity only for n=1,2,3; n=4 is separately checked as a Julia named-candidate/MSS boundary and a JAX seven-relation automorphism boundary, with no full n=4 cross-runtime parity claim."
    )
    result = {
        "schema_version": "finite_structure_hypothesis_tournament.controller.v4",
        "all_pass": all_pass,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": qualified_claim_ceiling,
        "source_spec_claim_ceiling": spec["claim_ceiling"],
        "blocked_consumers": spec["blocked_consumers"],
        "command": [sys.executable, str(Path(__file__).resolve()), "--out", str(args.out.resolve())],
        "cwd": os.getcwd(),
        "runner_identity": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
            "executable": sys.executable,
            "role": "strict fail-closed comparison and replay controller",
        },
        "runtime": {"platform": platform.platform()},
        "source_path": str(Path(__file__).resolve().relative_to(REPO)),
        "source_sha256": sha256_file(Path(__file__).resolve()),
        "spec_path": str(SPEC_PATH.relative_to(REPO)),
        "spec_sha256": sha256_file(SPEC_PATH),
        "input_receipts": {
            "spec": spec_meta,
            "object_card": card_meta,
            "preregistration": prereg_meta,
            "julia": julia_meta,
            "jax": jax_meta,
            "smt": smt_meta,
        },
        "engine_roles": {
            "not_innately_independent": True,
            "julia": "semantic canon and exact finite-structure owner",
            "jax": "batched independent recomputation and workhorse",
            "smt": "bounded dual-solver witness crossover",
            "pytorch": spec["engine_mode"]["pytorch"],
        },
        "cross_runtime_comparison": {
            "metric": "controller_discrepancy_count",
            "units": "failed exact comparison or independent-oracle rows",
            "julia_authoritative": True,
            "comparison_domain": {
                "exhaustive_cross_runtime_carrier_sizes": [1, 2, 3],
                "named_boundary_carrier_sizes": [4],
                "n4_full_julia_jax_candidate_or_mss_parity_claimed": False,
            },
            **comparison,
        },
        "smt_crossover": {
            "receipt_path": str(SMT_RESULT.relative_to(REPO)),
            "receipt_sha256": smt_meta["raw_sha256"],
            "polarity": "exists p in Aut(left) but not Aut(right)",
            "query_matrix": comparison["smt_query_matrix"],
            "all_pass": not comparison["smt_errors"],
        },
        "checks": checks.rows,
        "controls": controls,
        "scope_checks": scope_checks,
        "errors": checks.errors,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "errors": checks.errors, "mismatch_count": comparison["mismatch_count"], "output": str(args.out.resolve())}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
