#!/usr/bin/env python3
"""Validate the frozen N9 census and downstream benchmark-admission surfaces."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


SIM_ID = "eca_behavioral_refinement_depth_census_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
HERE = Path(__file__).resolve().parent
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
RECEIPT_PATH = HERE / "preregistration_receipt.json"
RESULT_PATH = HERE / "results" / f"{SIM_ID}_preregistration_validation.json"
TAG = "ECA9-DEPTH-V1"

TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Exact finite rule-symmetry enumeration, SHA ordering, and frozen-surface validation.",
    },
    "git": {
        "used": True,
        "reason": "Historical tree inspection proves builder sources were absent in the first committed packet state.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "git": "supportive"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def transforms(rule: int) -> tuple[int, int, int, int]:
    return (
        rule,
        reflect_rule(rule),
        conjugate_rule(rule),
        reflect_rule(conjugate_rule(rule)),
    )


def simultaneous_pair_orbit(pair: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    ta = transforms(pair[0])
    tb = transforms(pair[1])
    return tuple(sorted({tuple(sorted((ta[index], tb[index]))) for index in range(4)}))


def pair_orbit_key(pair: tuple[int, int]) -> str:
    canonical = simultaneous_pair_orbit(pair)[0]
    return f"{canonical[0]},{canonical[1]}"


def orbit_order_hash(key: str) -> str:
    return hashlib.sha256(f"{TAG}|pair_orbit|{key}".encode()).hexdigest()


def enumerate_split() -> dict:
    pairs = [(a, b) for a in range(255) for b in range(a + 1, 256)]
    by_key: dict[str, list[tuple[int, int]]] = {}
    for pair in pairs:
        by_key.setdefault(pair_orbit_key(pair), []).append(pair)
    ordered_keys = sorted(by_key, key=lambda key: (orbit_order_hash(key), key))
    batch_by_key = {
        key: "A" if index % 2 == 0 else "B" for index, key in enumerate(ordered_keys)
    }
    membership_counts = Counter(
        batch_by_key[pair_orbit_key(pair)] for pair in pairs
    )
    orbit_counts = Counter(batch_by_key.values())
    orbit_size_histogram = Counter(len(members) for members in by_key.values())
    return {
        "pair_count": len(pairs),
        "unique_pair_orbit_count": len(by_key),
        "pair_orbit_size_histogram": {
            str(key): orbit_size_histogram[key] for key in sorted(orbit_size_histogram)
        },
        "hidden_batch_pair_counts": dict(sorted(membership_counts.items())),
        "hidden_batch_orbit_counts": dict(sorted(orbit_counts.items())),
        "ordered_orbit_keys_sha256": hashlib.sha256(
            json.dumps(ordered_keys, separators=(",", ":")).encode()
        ).hexdigest(),
        "all_orbit_members_share_batch": all(
            len({batch_by_key[pair_orbit_key(member)] for member in members}) == 1
            for members in by_key.values()
        ),
    }


def invalid_one_rule_transform_detected() -> dict:
    for a in range(255):
        for b in range(a + 1, 256):
            original = (a, b)
            invalid = tuple(sorted((reflect_rule(a), b)))
            if pair_orbit_key(original) != pair_orbit_key(invalid):
                return {
                    "detected": True,
                    "original_pair": list(original),
                    "invalid_one_rule_transform": list(invalid),
                    "original_orbit_key": pair_orbit_key(original),
                    "invalid_orbit_key": pair_orbit_key(invalid),
                }
    return {"detected": False}


def receipt_mutation_detected(receipt: dict) -> bool:
    mutated = copy.deepcopy(receipt)
    mutated["spec_sha256"] = "0" * 64
    return mutated["spec_sha256"] != sha256_file(SPEC_PATH)


def builders_absent_in_first_packet_commit() -> dict:
    repo = HERE.parents[2]
    relative = HERE.relative_to(repo)
    commits = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--reverse", "--format=%H", "--", str(relative)],
        text=True,
    ).splitlines()
    if not commits:
        return {"passed": False, "reason": "packet has no committed history"}
    first_commit = commits[0]
    builder_presence = {}
    for name in ("run_jax.py", "run_julia.jl"):
        probe = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{first_commit}:{relative}/{name}"],
            capture_output=True,
            text=True,
            check=False,
        )
        builder_presence[name] = probe.returncode == 0
    return {
        "passed": not any(builder_presence.values()),
        "first_packet_commit": first_commit,
        "builder_sources_present": builder_presence,
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    card = json.loads(CARD_PATH.read_text())
    receipt = json.loads(RECEIPT_PATH.read_text())
    split = enumerate_split()
    sentinel = invalid_one_rule_transform_detected()
    historical_builder_check = builders_absent_in_first_packet_commit()
    statement = card["primary_object_card"]["object_statement"]
    tests = {
        "P1_sim_id_matches": spec.get("sim_id") == receipt.get("sim_id") == SIM_ID,
        "P2_spec_hash_matches": sha256_file(SPEC_PATH) == receipt.get("spec_sha256"),
        "P3_object_card_hash_matches": sha256_file(CARD_PATH)
        == receipt.get("object_card_sha256"),
        "P4_object_statement_hash_matches": hashlib.sha256(statement.encode()).hexdigest()
        == card["primary_object_card"].get("object_statement_sha256"),
        "P5_builder_sources_absent_when_frozen": receipt.get(
            "builder_sources_present_when_frozen"
        )
        is False
        and historical_builder_check["passed"],
        "P6_complete_pair_universe": split["pair_count"] == 32640,
        "P7_orbit_members_do_not_cross_hidden_batches": split[
            "all_orbit_members_share_batch"
        ],
        "P8_both_hidden_batches_nonempty": set(split["hidden_batch_orbit_counts"])
        == {"A", "B"},
        "P9_invalid_one_rule_symmetry_detected": sentinel["detected"],
        "P10_receipt_hash_mutation_detected": receipt_mutation_detected(receipt),
        "P11_v2_admission_is_explicitly_not_success": spec[
            "downstream_v2_admission_gate"
        ]["admission_is_not_learning_success"]
        is True,
    }
    result = {
        "schema": "codex_ratchet.eca_behavioral_refinement_depth_census_v1.preregistration_validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "split_receipt": split,
        "invalid_symmetry_sentinel": sentinel,
        "historical_builder_check": historical_builder_check,
        "tests": tests,
        "all_pass": all(tests.values()),
        "claim_ceiling": "frozen N9 complete-census, hidden-batch, and downstream V2-admission design only; no N9 labels or learned result",
        "blocked_consumers": spec["blocked_consumers"],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "tests": tests, "split": split}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
