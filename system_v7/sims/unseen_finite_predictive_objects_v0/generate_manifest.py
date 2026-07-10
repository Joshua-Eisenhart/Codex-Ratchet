#!/usr/bin/env python3
"""Generate the prospective exact object registry before learner source exists."""

from __future__ import annotations

import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
OUTPUT_PATH = HERE / "object_manifest.json"
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "Exact Fraction arithmetic, finite permutation canonicalization, SHA-256 registry generation, and JSON receipt I/O."}
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def candidate(counter: int) -> tuple[tuple[int, int, int], ...]:
    digest = hashlib.sha256(f"ufpo-v0|candidate|{counter}".encode()).digest()
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


def state_signature(machine: tuple[tuple[int, int, int], ...], state: int) -> tuple[Fraction, ...]:
    return tuple(
        word_probability(machine, state, word)
        for length in range(1, 9)
        for word in itertools.product((0, 1), repeat=length)
    )


def predictive_signature(machine: tuple[tuple[int, int, int], ...]) -> tuple[Fraction, ...]:
    return tuple(
        sum((word_probability(machine, state, word) for state in range(4)), Fraction(0)) / 4
        for length in range(1, 9)
        for word in itertools.product((0, 1), repeat=length)
    )


def signature_hash(signature: tuple[Fraction, ...]) -> str:
    encoded = [[value.numerator, value.denominator] for value in signature]
    return sha256_bytes(canonical_json(encoded))


def short_horizon_distance(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> Fraction:
    return sum(abs(left[index] - right[index]) for index in range(6))


def long_horizon_distance(left: tuple[Fraction, ...], right: tuple[Fraction, ...]) -> Fraction:
    return sum(abs(left[index] - right[index]) for index in range(6, len(left)))


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    start, stop = spec["object_family"]["candidate_counter_interval"]
    objects: dict[str, dict[str, Any]] = {}
    rejected = {"not_strongly_connected": 0, "not_minimal": 0, "machine_duplicate": 0, "signature_duplicate": 0}
    signature_seen: set[str] = set()
    for counter in range(start, stop + 1):
        machine = canonical_machine(candidate(counter))
        machine_hash = sha256_bytes(canonical_json(machine))
        if machine_hash in objects:
            rejected["machine_duplicate"] += 1
            continue
        if not strongly_connected(machine):
            rejected["not_strongly_connected"] += 1
            continue
        state_signatures = [state_signature(machine, state) for state in range(4)]
        if len(set(state_signatures)) != 4:
            rejected["not_minimal"] += 1
            continue
        signature = predictive_signature(machine)
        sig_hash = signature_hash(signature)
        if sig_hash in signature_seen:
            rejected["signature_duplicate"] += 1
            continue
        signature_seen.add(sig_hash)
        objects[machine_hash] = {
            "counter": counter,
            "machine": [list(row) for row in machine],
            "machine_sha256": machine_hash,
            "predictive_signature_sha256": sig_hash,
            "state_signature_sha256": [signature_hash(value) for value in state_signatures],
        }
    ordered = [objects[key] for key in sorted(objects)]
    required = sum(spec["frozen_splits"][key] for key in ("train_objects", "validation_objects", "test_objects"))
    if len(ordered) < required:
        raise RuntimeError(f"only {len(ordered)} accepted objects; need {required}")
    selected = ordered[:required]
    train_stop = spec["frozen_splits"]["train_objects"]
    validation_stop = train_stop + spec["frozen_splits"]["validation_objects"]
    split_rows = {
        "train": selected[:train_stop],
        "validation": selected[train_stop:validation_stop],
        "test": selected[validation_stop:],
    }
    signatures = {
        row["machine_sha256"]: predictive_signature(tuple(tuple(value) for value in row["machine"]))
        for row in split_rows["test"]
    }
    remaining = [row["machine_sha256"] for row in split_rows["test"]]
    hard_pairs: list[list[str]] = []
    while remaining:
        left = remaining.pop(0)
        right = min(
            remaining,
            key=lambda candidate_hash: (
                short_horizon_distance(signatures[left], signatures[candidate_hash]),
                -long_horizon_distance(signatures[left], signatures[candidate_hash]),
                candidate_hash,
            ),
        )
        remaining.remove(right)
        hard_pairs.append([left, right])
    manifest = {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v0.object_manifest.v1",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "spec_sha256": sha256_bytes(SPEC_PATH.read_bytes()),
        "candidate_interval": [start, stop],
        "accepted_candidate_count": len(ordered),
        "rejected_counts": rejected,
        "selection": "first 192 after canonical machine hash sort",
        "splits": split_rows,
        "hard_negative_test_pairs": hard_pairs,
        "test_outcome_status": "machine registry and exact pair declarations frozen; no learned test metric exists",
        "model_input_excludes_manifest_identity_fields": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False
    }
    OUTPUT_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "accepted_candidate_count": len(ordered),
        "selected_count": required,
        "split_counts": {key: len(value) for key, value in split_rows.items()},
        "manifest_sha256": sha256_bytes(OUTPUT_PATH.read_bytes()),
        "output": str(OUTPUT_PATH),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
