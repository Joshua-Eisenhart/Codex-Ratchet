#!/usr/bin/env python3
"""Generate the exact prospective ufpo-v1 registry before learner sealing."""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable

import networkx as nx


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
V0_MANIFEST_PATH = HERE.parent / "unseen_finite_predictive_objects_v0" / "object_manifest.json"
OUTPUT_PATH = HERE / "object_manifest.json"
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Exact Fraction arithmetic, finite permutation canonicalization, SHA-256 registry generation, and JSON receipt I/O.",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "Exact minimum-weight perfect matching over the 32 frozen test objects.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "networkx": "load_bearing"}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def candidate(counter: int) -> tuple[tuple[int, int, int], ...]:
    digest = hashlib.sha256(f"ufpo-v1|candidate|{counter}".encode()).digest()
    return tuple(
        (digest[state] % 4, digest[4 + state] % 4, 2 + digest[8 + state] % 5)
        for state in range(4)
    )


def relabel(machine: tuple[tuple[int, int, int], ...], order: tuple[int, ...]) -> tuple[tuple[int, int, int], ...]:
    inverse = {old: new for new, old in enumerate(order)}
    return tuple(
        (inverse[machine[old][0]], inverse[machine[old][1]], machine[old][2])
        for old in order
    )


def canonical_machine(machine: tuple[tuple[int, int, int], ...]) -> tuple[tuple[int, int, int], ...]:
    return min(relabel(machine, order) for order in itertools.permutations(range(4)))


def strongly_connected(machine: tuple[tuple[int, int, int], ...]) -> bool:
    for source in range(4):
        seen = {source}
        pending = [source]
        while pending:
            state = pending.pop()
            for target in machine[state][:2]:
                if target not in seen:
                    seen.add(target)
                    pending.append(target)
        if len(seen) != 4:
            return False
    return True


def word_probability(machine: tuple[tuple[int, int, int], ...], start: int, word: Iterable[int]) -> Fraction:
    probability = Fraction(1)
    state = start
    for symbol in word:
        numerator = machine[state][2]
        probability *= Fraction(numerator if symbol else 8 - numerator, 8)
        state = machine[state][symbol]
    return probability


def state_signature(machine: tuple[tuple[int, int, int], ...], state: int, max_length: int) -> tuple[Fraction, ...]:
    frontier = [(state, Fraction(1))]
    values: list[Fraction] = []
    for _length in range(1, max_length + 1):
        next_frontier: list[tuple[int, Fraction]] = []
        for current_state, prefix_probability in frontier:
            zero_probability = prefix_probability * Fraction(8 - machine[current_state][2], 8)
            one_probability = prefix_probability * Fraction(machine[current_state][2], 8)
            values.extend((zero_probability, one_probability))
            next_frontier.extend(((machine[current_state][0], zero_probability), (machine[current_state][1], one_probability)))
        frontier = next_frontier
    return tuple(values)


def predictive_signature(machine: tuple[tuple[int, int, int], ...], max_length: int) -> tuple[Fraction, ...]:
    frontiers = [[(state, Fraction(1))] for state in range(4)]
    values: list[Fraction] = []
    for _length in range(1, max_length + 1):
        next_frontiers: list[list[tuple[int, Fraction]]] = [[] for _ in range(4)]
        for position in range(len(frontiers[0])):
            for start in range(4):
                current_state, prefix_probability = frontiers[start][position]
                zero_probability = prefix_probability * Fraction(8 - machine[current_state][2], 8)
                one_probability = prefix_probability * Fraction(machine[current_state][2], 8)
                next_frontiers[start].extend(((machine[current_state][0], zero_probability), (machine[current_state][1], one_probability)))
            values.append(sum((next_frontiers[start][-2][1] for start in range(4)), Fraction(0)) / 4)
            values.append(sum((next_frontiers[start][-1][1] for start in range(4)), Fraction(0)) / 4)
        frontiers = next_frontiers
    return tuple(values)


def signature_hash(signature: tuple[Fraction, ...]) -> str:
    encoded = [[value.numerator, value.denominator] for value in signature]
    return sha256_bytes(canonical_json(encoded))


def fraction_pair(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def full_horizon_l1(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> Fraction:
    return sum((abs(a - b) for a, b in zip(left, right)), Fraction(0))


def manifest_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for split in ("train", "validation", "test") for row in manifest["splits"][split]]


def exact_matching(test_rows: list[dict[str, Any]], signatures: dict[str, tuple[Fraction, ...]]) -> list[dict[str, Any]]:
    graph = nx.Graph()
    hashes = sorted(row["machine_sha256"] for row in test_rows)
    graph.add_nodes_from(hashes)
    for left_index, left in enumerate(hashes):
        for right in hashes[left_index + 1 :]:
            graph.add_edge(left, right, weight=full_horizon_l1(signatures[left], signatures[right]))
    matching = nx.algorithms.matching.min_weight_matching(graph, weight="weight")
    if len(matching) != len(hashes) // 2:
        raise RuntimeError(f"matching has {len(matching)} pairs; expected {len(hashes) // 2}")
    pairs = []
    for left, right in matching:
        left, right = sorted((left, right))
        distance = graph[left][right]["weight"]
        pairs.append({
            "left_machine_sha256": left,
            "right_machine_sha256": right,
            "full_lengths_1_to_12_l1_distance": fraction_pair(distance),
        })
    return sorted(pairs, key=lambda pair: (pair["left_machine_sha256"], pair["right_machine_sha256"]))


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    v0_manifest = json.loads(V0_MANIFEST_PATH.read_text(encoding="utf-8"))
    v0_rows = manifest_rows(v0_manifest)
    excluded_machine_hashes = {row["machine_sha256"] for row in v0_rows}
    excluded_target_hashes = {
        row.get("predictive_signature_sha256", row.get("target_signature_sha256"))
        for row in v0_rows
    }
    if None in excluded_target_hashes:
        raise RuntimeError("v0 manifest row is missing its length1-to-8 predictive signature hash")

    start, stop = spec["object_family"]["candidate_counter_interval"]
    objects: dict[str, dict[str, Any]] = {}
    rejected = {
        "not_strongly_connected": 0,
        "not_minimal": 0,
        "machine_duplicate": 0,
        "signature_duplicate": 0,
        "excluded_v0_machine_hash": 0,
        "excluded_v0_predictive_signature_hash": 0,
    }
    signature_seen: set[str] = set()
    for counter in range(start, stop + 1):
        machine = canonical_machine(candidate(counter))
        machine_hash = sha256_bytes(canonical_json(machine))
        if machine_hash in excluded_machine_hashes:
            rejected["excluded_v0_machine_hash"] += 1
            continue
        if machine_hash in objects:
            rejected["machine_duplicate"] += 1
            continue
        if not strongly_connected(machine):
            rejected["not_strongly_connected"] += 1
            continue
        state_signatures = [state_signature(machine, state, 8) for state in range(4)]
        if len(set(state_signatures)) != 4:
            rejected["not_minimal"] += 1
            continue
        target_signature = predictive_signature(machine, 8)
        target_hash = signature_hash(target_signature)
        if target_hash in excluded_target_hashes:
            rejected["excluded_v0_predictive_signature_hash"] += 1
            continue
        if target_hash in signature_seen:
            rejected["signature_duplicate"] += 1
            continue
        signature_seen.add(target_hash)
        objects[machine_hash] = {
            "counter": counter,
            "machine": [list(row) for row in machine],
            "machine_sha256": machine_hash,
            "predictive_signature_sha256": target_hash,
            "target_signature_sha256": target_hash,
            "state_signature_sha256": [signature_hash(value) for value in state_signatures],
        }

    ordered = [objects[key] for key in sorted(objects)]
    required = sum(spec["frozen_splits"][key] for key in ("train_objects", "validation_objects", "test_objects"))
    if len(ordered) < required:
        raise RuntimeError(f"only {len(ordered)} eligible objects; need {required}")
    selected = ordered[:required]
    train_stop = spec["frozen_splits"]["train_objects"]
    validation_stop = train_stop + spec["frozen_splits"]["validation_objects"]
    split_rows = {
        "train": selected[:train_stop],
        "validation": selected[train_stop:validation_stop],
        "test": selected[validation_stop:],
    }

    target_signatures: dict[str, tuple[Fraction, ...]] = {}
    challenge_signatures: dict[str, tuple[Fraction, ...]] = {}
    for row in selected:
        machine = tuple(tuple(value) for value in row["machine"])
        target = predictive_signature(machine, 8)
        challenge = predictive_signature(machine, 12)
        row["predictive_signature_sha256"] = signature_hash(target)
        row["target_signature_sha256"] = row["predictive_signature_sha256"]
        row["challenge_signature_sha256"] = signature_hash(challenge)
        row["target_signature_coordinate_count"] = len(target)
        row["challenge_signature_coordinate_count"] = len(challenge)
        target_signatures[row["machine_sha256"]] = target
        challenge_signatures[row["machine_sha256"]] = challenge

    pairs = exact_matching(split_rows["test"], challenge_signatures)
    selected_machine_hashes = {row["machine_sha256"] for row in selected}
    selected_target_hashes = {row["predictive_signature_sha256"] for row in selected}
    if selected_machine_hashes & excluded_machine_hashes:
        raise RuntimeError("selected machine hash intersects v0 exclusion set")
    if selected_target_hashes & excluded_target_hashes:
        raise RuntimeError("selected length1-to-8 signature hash intersects v0 exclusion set")

    manifest = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v1.object_manifest.v1",
        "sim_id": spec["sim_id"],
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "spec_sha256": sha256_bytes(SPEC_PATH.read_bytes()),
        "v0_manifest_sha256": sha256_bytes(V0_MANIFEST_PATH.read_bytes()),
        "candidate_namespace": spec["object_family"]["candidate_namespace"],
        "candidate_interval": [start, stop],
        "accepted_candidate_count": len(objects),
        "eligible_candidate_count": len(ordered),
        "rejected_counts": rejected,
        "excluded_v0_machine_hash_count": len(excluded_machine_hashes),
        "excluded_v0_predictive_signature_hash_count": len(excluded_target_hashes),
        "selection": spec["frozen_splits"]["selection"],
        "split_counts": {key: len(value) for key, value in split_rows.items()},
        "signature_contract": {
            "target_lengths": [1, 8],
            "challenge_lengths": [1, 12],
            "target_coordinate_count": len(next(iter(target_signatures.values()))),
            "challenge_coordinate_count": len(next(iter(challenge_signatures.values()))),
            "exact_rational_encoding": "each Fraction is hashed from [numerator, denominator] pairs in canonical JSON order",
        },
        "splits": split_rows,
        "test_pairing": {
            "name": "full-observation-horizon-matched",
            "algorithm": "networkx.algorithms.matching.min_weight_matching",
            "objective": "minimum-weight perfect matching",
            "weight": "exact Python Fraction L1 distance over all predictive-signature coordinates at lengths 1 through 12",
            "pairs": pairs,
        },
        "test_outcome_status": "machine registry, exact target signatures, challenge signatures, and full-observation-horizon-matched pair distances frozen; learner source is not sealed and no learned test metric exists",
        "learner_source_sealed": False,
        "model_input_excludes_manifest_identity_fields": True,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "accepted_candidate_count": len(objects),
        "eligible_candidate_count": len(ordered),
        "selected_count": required,
        "split_counts": manifest["split_counts"],
        "pair_count": len(pairs),
        "spec_sha256": manifest["spec_sha256"],
        "manifest_sha256": sha256_bytes(OUTPUT_PATH.read_bytes()),
        "output": str(OUTPUT_PATH),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
