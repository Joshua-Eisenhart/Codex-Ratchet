#!/usr/bin/env python3
"""Independent fail-closed validator for the v1 frozen benchmark surfaces."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "spec.json"
RECEIPT_PATH = ROOT / "preregistration_receipt.json"
OBJECT_CARD_PATH = ROOT / "wizard_v4_3_object_card.json"
RESULT_PATH = ROOT / "results" / "finite_probe_behavioral_object_engine_v1_preregistration_validation.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact_sha(value: Any) -> str:
    payload = json.dumps(value, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


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


def rule_orbit(rule: int) -> tuple[int, ...]:
    seen = {rule}
    pending = [rule]
    while pending:
        current = pending.pop()
        for candidate in (
            reflect_rule(current),
            conjugate_rule(current),
            reflect_rule(conjugate_rule(current)),
        ):
            if candidate not in seen:
                seen.add(candidate)
                pending.append(candidate)
    return tuple(sorted(seen))


def ordered_orbits(tag: str) -> list[tuple[int, ...]]:
    unique = {rule_orbit(rule) for rule in range(256)}
    return sorted(
        unique,
        key=lambda orbit: hashlib.sha256(
            (tag + "|orbit|" + ",".join(map(str, orbit))).encode()
        ).hexdigest(),
    )


def eca_step(state: int, rule: int, ring_size: int = 6) -> int:
    out = 0
    for site in range(ring_size):
        left = (state >> ((site - 1) % ring_size)) & 1
        center = (state >> site) & 1
        right = (state >> ((site + 1) % ring_size)) & 1
        neighborhood = (left << 2) | (center << 1) | right
        out |= ((rule >> neighborhood) & 1) << site
    return out


def probes(state: int, ring_size: int = 6) -> tuple[int, int]:
    walls = sum(
        ((state >> site) & 1) != ((state >> ((site + 1) % ring_size)) & 1)
        for site in range(ring_size)
    )
    return state.bit_count(), walls


def canonical_labels(signatures: list[Any]) -> list[int]:
    ids: dict[Any, int] = {}
    labels: list[int] = []
    for signature in signatures:
        if signature not in ids:
            ids[signature] = len(ids)
        labels.append(ids[signature])
    return labels


def stable_partition(rule_a: int, rule_b: int) -> tuple[list[int], int]:
    transitions_a = [eca_step(state, rule_a) for state in range(64)]
    transitions_b = [eca_step(state, rule_b) for state in range(64)]
    labels = canonical_labels([probes(state) for state in range(64)])
    for depth in range(64):
        signatures = [
            (labels[state], labels[transitions_a[state]], labels[transitions_b[state]])
            for state in range(64)
        ]
        refined = canonical_labels(signatures)
        if refined == labels:
            return labels, depth
        labels = refined
    raise AssertionError("partition did not stabilize within finite bound")


def behavioral_hash(pair: list[int]) -> str:
    labels, _ = stable_partition(pair[0], pair[1])
    return compact_sha(labels)


def validate_fixture_membership(spec: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    split = spec["rule_symmetry_split"]
    tag = split["tag"]
    orbits = ordered_orbits(tag)
    if len(orbits) != split["expected_orbit_count"]:
        errors.append("rule symmetry orbit count mismatch")

    blocks = split["orbit_blocks"]
    orbit_index = {rule: index for index, orbit in enumerate(orbits) for rule in orbit}
    all_selected_rules: dict[str, set[int]] = {}
    split_names = ("train", "validation", "test_primary", "test_structural_holdout")
    for name in split_names:
        pool = "test" if name.startswith("test_") else name
        start, end = blocks[pool]
        used: set[int] = set()
        for pair in spec["fixtures"][name]:
            if len(pair) != 2 or pair[0] >= pair[1]:
                errors.append(f"{name}: noncanonical pair {pair}")
                continue
            a, b = pair
            if a in used or b in used:
                errors.append(f"{name}: repeated selected rule in {pair}")
            used.update(pair)
            if not (start <= orbit_index[a] <= end and start <= orbit_index[b] <= end):
                errors.append(f"{name}: rule outside frozen orbit block {pair}")
            if orbit_index[a] == orbit_index[b]:
                errors.append(f"{name}: pair members share a symmetry orbit {pair}")
        all_selected_rules[name] = used

    train_orbits = {orbit_index[r] for r in all_selected_rules["train"]}
    validation_orbits = {orbit_index[r] for r in all_selected_rules["validation"]}
    test_orbits = {
        orbit_index[r]
        for name in ("test_primary", "test_structural_holdout")
        for r in all_selected_rules[name]
    }
    if train_orbits & validation_orbits or train_orbits & test_orbits or validation_orbits & test_orbits:
        errors.append("symmetry orbit leaked across train/validation/test")

    expected_counts = {"train": 64, "validation": 16, "test_primary": 14, "test_structural_holdout": 2}
    for name, expected in expected_counts.items():
        if len(spec["fixtures"][name]) != expected:
            errors.append(f"{name}: expected {expected} fixtures")

    heldout_hashes = set(
        spec["behavioral_partition_hash"]["structural_holdout_hashes_excluded_from_train_and_validation"]
    )
    observed_hashes = {
        name: [behavioral_hash(pair) for pair in spec["fixtures"][name]]
        for name in split_names
    }
    if set(observed_hashes["test_structural_holdout"]) != heldout_hashes:
        errors.append("structural-holdout fixtures do not match frozen partition hashes")
    if heldout_hashes & set(observed_hashes["train"]):
        errors.append("structural-holdout partition leaked into train")
    if heldout_hashes & set(observed_hashes["validation"]):
        errors.append("structural-holdout partition leaked into validation")

    details = {
        "orbit_count": len(orbits),
        "orbit_size_histogram": {
            str(size): sum(len(orbit) == size for orbit in orbits)
            for size in sorted({len(orbit) for orbit in orbits})
        },
        "fixture_counts": {name: len(spec["fixtures"][name]) for name in split_names},
        "partition_hashes_by_split": {
            name: sorted(set(values)) for name, values in observed_hashes.items()
        },
        "structural_holdout_hashes": sorted(heldout_hashes),
    }
    return errors, details


def leakage_sentinel_rejected(spec: dict[str, Any]) -> bool:
    mutated = copy.deepcopy(spec)
    first_train_rule = mutated["fixtures"]["train"][0][0]
    equivalent = next(
        rule for rule in rule_orbit(first_train_rule) if rule != first_train_rule
    )
    mutated["fixtures"]["test_primary"][0][0] = equivalent
    errors, _ = validate_fixture_membership(mutated)
    return any("outside frozen orbit block" in error or "leaked" in error for error in errors)


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    receipt = json.loads(RECEIPT_PATH.read_text())
    object_card = json.loads(OBJECT_CARD_PATH.read_text())
    errors: list[str] = []

    if sha256_file(SPEC_PATH) != receipt["spec_sha256"]:
        errors.append("spec hash differs from preregistration")
    if sha256_file(OBJECT_CARD_PATH) != receipt["object_card_sha256"]:
        errors.append("object-card hash differs from preregistration")
    if receipt["builder_sources_present_when_frozen"] is not False:
        errors.append("preregistration does not state builder sources were absent")
    if object_card["primary_object_card"]["object_statement_sha256"] != hashlib.sha256(
        object_card["primary_object_card"]["object_statement"].encode()
    ).hexdigest():
        errors.append("object statement hash mismatch")

    fixture_errors, details = validate_fixture_membership(spec)
    errors.extend(fixture_errors)
    sentinel_pass = leakage_sentinel_rejected(spec)
    if not sentinel_pass:
        errors.append("in-memory symmetry leakage sentinel was not rejected")

    result = {
        "schema": "codex_ratchet.finite_probe_behavioral_object_engine_v1.preregistration_validation.v1",
        "sim_id": spec["sim_id"],
        "classification": "controller_preflight",
        "checks": {
            "spec_hash_matches": sha256_file(SPEC_PATH) == receipt["spec_sha256"],
            "object_card_hash_matches": sha256_file(OBJECT_CARD_PATH) == receipt["object_card_sha256"],
            "object_statement_hash_matches": object_card["primary_object_card"]["object_statement_sha256"]
            == hashlib.sha256(object_card["primary_object_card"]["object_statement"].encode()).hexdigest(),
            "fixture_membership_and_partition_exclusions_pass": not fixture_errors,
            "leakage_sentinel_rejected": sentinel_pass,
        },
        "details": details,
        "errors": errors,
        "all_pass": not errors,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "frozen object, split, and structural-holdout preflight only; no model, perception, T9, QIT, or stage claim",
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "errors": errors, "result_path": str(RESULT_PATH)}))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
