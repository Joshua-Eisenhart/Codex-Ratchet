#!/usr/bin/env python3
"""Validate frozen manifests and object boundaries for the identifiability scout."""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from pathlib import Path


SIM_ID = "eca_observation_object_identifiability_v0"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TAG = "ECA-OBS-ID-V0"
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
RECEIPT_PATH = HERE / "preregistration_receipt.json"
RESULT_PATH = HERE / "results" / f"{SIM_ID}_preregistration_validation.json"

TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Exact finite manifest construction, SHA ordering, source hashing, and JSON validation.",
    },
    "git": {
        "used": True,
        "reason": "Historical packet-tree inspection after builders exist; current absence before first commit.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "git": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def compact_json(value: object, *, sort_keys: bool = False) -> str:
    return json.dumps(value, sort_keys=sort_keys, separators=(",", ":"))


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
    return sum(
        (1 - ((rule >> (7 - neighborhood)) & 1)) << neighborhood
        for neighborhood in range(8)
    )


def rule_orbit(rule: int) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                rule,
                reflect_rule(rule),
                conjugate_rule(rule),
                reflect_rule(conjugate_rule(rule)),
            }
        )
    )


def ordered_rule_orbits() -> list[tuple[int, ...]]:
    orbits = set(rule_orbit(rule) for rule in range(256))
    return sorted(
        orbits,
        key=lambda orbit: (
            digest_text(f"{TAG}|rule_orbit|" + ",".join(map(str, orbit))),
            orbit,
        ),
    )


def simultaneous_pair_orbit(pair: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    a, b = pair
    ta = (a, reflect_rule(a), conjugate_rule(a), reflect_rule(conjugate_rule(a)))
    tb = (b, reflect_rule(b), conjugate_rule(b), reflect_rule(conjugate_rule(b)))
    return tuple(sorted({tuple(sorted((ta[index], tb[index]))) for index in range(4)}))


def build_manifests() -> dict:
    orbits = ordered_rule_orbits()
    blocks = {"train": orbits[:52], "validation": orbits[52:70], "test": orbits[70:88]}
    rule_block = {
        rule: block
        for block, block_orbits in blocks.items()
        for orbit in block_orbits
        for rule in orbit
    }
    pair_orbits: dict[str, list[list[list[int]]]] = {}
    counts = {}
    for block, block_orbits in blocks.items():
        raw_pairs = [
            (a, b)
            for a in range(255)
            for b in range(a + 1, 256)
            if rule_block[a] == rule_block[b] == block
        ]
        unique_pair_orbits = sorted(set(simultaneous_pair_orbit(pair) for pair in raw_pairs))
        pair_orbits[block] = [[list(pair) for pair in orbit] for orbit in unique_pair_orbits]
        counts[block] = {
            "rule_orbits": len(block_orbits),
            "rules": len({rule for orbit in block_orbits for rule in orbit}),
            "raw_pairs": len(raw_pairs),
            "simultaneous_pair_orbits": len(unique_pair_orbits),
        }
    words = sorted(
        ("".join(bits) for bits in itertools.product("AB", repeat=4)),
        key=lambda word: (digest_text(f"{TAG}|word|{word}"), word),
    )
    states = sorted(
        range(512),
        key=lambda state: (digest_text(f"{TAG}|initial_state|{state}"), state),
    )[:16]
    assignments = [[word, state] for word, state in zip(words, states)]

    def probe(state: int) -> tuple[int, int]:
        bits = [(state >> site) & 1 for site in range(9)]
        return sum(bits), sum(bits[index] != bits[(index + 1) % 9] for index in range(9))

    queries = [
        [a, b]
        for a in range(511)
        for b in range(a + 1, 512)
        if probe(a) == probe(b)
    ]
    return {
        "orbits": orbits,
        "pair_orbits": pair_orbits,
        "counts": counts,
        "assignments": assignments,
        "queries": queries,
        "hashes": {
            "rule_orbits": digest_text(compact_json(orbits)),
            "pair_orbits": digest_text(compact_json(pair_orbits, sort_keys=True)),
            "assignments": digest_text(compact_json(assignments)),
            "queries": digest_text(compact_json(queries)),
        },
    }


def builders_absent_at_freeze() -> dict:
    builders = ("run_jax.py", "run_julia.jl")
    if not any((HERE / name).exists() for name in builders):
        return {"passed": True, "mode": "current_prebuild_absence"}
    repo = HERE.parents[2]
    relative = HERE.relative_to(repo)
    commits = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--reverse", "--format=%H", "--", str(relative)],
        text=True,
    ).splitlines()
    if not commits:
        return {"passed": False, "mode": "no_committed_packet_history"}
    first = commits[0]
    presence = {}
    for name in builders:
        probe = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{first}:{relative}/{name}"],
            capture_output=True,
            check=False,
        )
        presence[name] = probe.returncode == 0
    return {
        "passed": not any(presence.values()),
        "mode": "historical_first_packet_commit",
        "first_packet_commit": first,
        "builder_sources_present": presence,
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    card = json.loads(CARD_PATH.read_text())
    receipt = json.loads(RECEIPT_PATH.read_text())
    manifests = build_manifests()
    historical = builders_absent_at_freeze()
    expected = spec["rule_family_split"]["expected_counts"]
    statement = card["primary_object_card"]["object_statement"]
    tests = {
        "P1_sim_id_matches": spec["sim_id"] == receipt["sim_id"] == SIM_ID,
        "P2_spec_hash_matches": sha256_file(SPEC_PATH) == receipt["spec_sha256"],
        "P3_object_card_hash_matches": sha256_file(CARD_PATH) == receipt["object_card_sha256"],
        "P4_object_statement_hash_matches": digest_text(statement)
        == card["primary_object_card"]["object_statement_sha256"],
        "P5_builders_absent_at_freeze": receipt["builder_sources_present_when_frozen"] is False
        and historical["passed"],
        "P6_rule_orbit_count": len(manifests["orbits"]) == expected["rule_orbits"] == 88,
        "P7_block_counts_match": all(manifests["counts"][key] == expected[key] for key in ("train", "validation", "test")),
        "P8_rule_orbit_manifest_matches": manifests["hashes"]["rule_orbits"]
        == spec["rule_family_split"]["rule_orbit_manifest_sha256"],
        "P9_pair_orbit_manifest_matches": manifests["hashes"]["pair_orbits"]
        == spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"],
        "P10_word_state_manifest_matches": manifests["assignments"]
        == spec["observation_packet"]["ordered_word_state_assignments"]
        and manifests["hashes"]["assignments"]
        == spec["observation_packet"]["word_state_assignment_sha256"],
        "P11_query_manifest_matches": len(manifests["queries"])
        == spec["query_universe"]["query_count_per_fixture"]
        and manifests["hashes"]["queries"]
        == spec["query_universe"]["query_manifest_sha256"],
        "P12_all_budgets_frozen": spec["observation_packet"]["cumulative_trajectory_budgets"]
        == [1, 2, 4, 8, 16]
        and spec["regime_classification"]["posthoc_budget_deletion_forbidden"] is True,
        "P13_learning_boundary_explicit": "new preregistration"
        in spec["regime_classification"]["future_learning_boundary"],
    }
    result = {
        "schema": "codex_ratchet.eca_observation_object_identifiability_v0.preregistration_validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "manifest_receipt": {
            "counts": manifests["counts"],
            "hashes": manifests["hashes"],
            "test_fixture_count": len(manifests["pair_orbits"]["test"]),
            "query_count": len(manifests["queries"]),
            "word_state_assignments": manifests["assignments"],
        },
        "historical_builder_check": historical,
        "tests": tests,
        "all_pass": all(tests.values()),
        "claim_ceiling": "frozen observation-identifiability design only; no exact scout result, learner, or perception claim",
        "blocked_consumers": spec["blocked_consumers"],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "tests": tests, "manifest_receipt": result["manifest_receipt"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
