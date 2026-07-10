#!/usr/bin/env python3
"""Validate the frozen two-phase relation-directed design preregistration."""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from pathlib import Path


SIM_ID = "eca_relation_directed_observation_design_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TAG = "ECA-OBS-DESIGN-V1"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
V0 = HERE.parent / "eca_observation_object_identifiability_v0"
SPEC_PATH = HERE / "spec.json"
CARD_PATH = HERE / "wizard_v4_3_object_card.json"
RECEIPT_PATH = HERE / "preregistration_receipt.json"
RESULT_PATH = HERE / "results" / f"{SIM_ID}_preregistration_validation.json"
SEARCH_SOURCES = ("search_jax.py", "search_julia.jl", "select_designs.py")
CONFIRM_SOURCES = ("confirm_jax.py", "confirm_julia.jl", "validate_confirmation.py")
TOOL_MANIFEST = {
    "python_stdlib": {
        "used": True,
        "reason": "Exact manifest reconstruction, candidate enumeration, source hashing, and historical git checks.",
    },
    "git": {
        "used": True,
        "reason": "Proves search and confirmation sources were absent from the first packet commit after later phases exist.",
    },
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive", "git": "supportive"}

sys.path.insert(0, str(V0))
from validate_preregistration import build_manifests, compact_json  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def fixture_representatives(manifests: dict, block: str) -> list[tuple[int, int]]:
    return [min(tuple(map(tuple, orbit))) for orbit in manifests["pair_orbits"][block]]


def design_fixtures(manifests: dict) -> list[tuple[int, int]]:
    train = fixture_representatives(manifests, "train")
    return sorted(
        train,
        key=lambda pair: (
            digest_text(f"{TAG}|design_fixture|{pair[0]},{pair[1]}"),
            pair,
        ),
    )[:128]


def source_absence_at_first_commit(names: tuple[str, ...]) -> dict:
    if not any((HERE / name).exists() for name in names):
        return {"passed": True, "mode": "current_absence", "presence": {name: False for name in names}}
    relative = HERE.relative_to(REPO)
    commits = subprocess.check_output(
        ["git", "-C", str(REPO), "log", "--reverse", "--format=%H", "--", str(relative)],
        text=True,
    ).splitlines()
    if not commits:
        return {"passed": False, "mode": "no_packet_commit", "presence": {}}
    first = commits[0]
    presence = {}
    for name in names:
        check = subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{first}:{relative}/{name}"],
            capture_output=True,
            check=False,
        )
        presence[name] = check.returncode == 0
    return {
        "passed": not any(presence.values()),
        "mode": "historical_first_packet_commit",
        "first_packet_commit": first,
        "presence": presence,
    }


def main() -> int:
    spec = json.loads(SPEC_PATH.read_text())
    card = json.loads(CARD_PATH.read_text())
    receipt = json.loads(RECEIPT_PATH.read_text())
    manifests = build_manifests()
    selected = design_fixtures(manifests)
    candidate_counts = {
        str(size): len(list(itertools.combinations(range(16), size)))
        for size in (2, 3, 4)
    }
    candidate_counts["total"] = sum(candidate_counts.values())
    search_history = source_absence_at_first_commit(SEARCH_SOURCES)
    confirm_history = source_absence_at_first_commit(CONFIRM_SOURCES)
    parent_spec = REPO / spec["parent"]["spec_path"]
    parent_result = REPO / spec["parent"]["result_path"]
    tests = {
        "P1_identity_and_receipt": spec["sim_id"] == receipt["sim_id"] == SIM_ID,
        "P2_spec_hash": sha256_file(SPEC_PATH) == receipt["spec_sha256"],
        "P3_object_card_hash": sha256_file(CARD_PATH) == receipt["object_card_sha256"],
        "P4_object_statement_hash": digest_text(card["primary_object_card"]["object_statement"])
        == card["primary_object_card"]["object_statement_sha256"],
        "P5_parent_hashes": sha256_file(parent_spec) == spec["parent"]["spec_sha256"]
        and sha256_file(parent_result) == spec["parent"]["result_sha256"],
        "P6_inherited_manifests": manifests["hashes"]["rule_orbits"]
        == spec["rule_family_split"]["rule_orbit_manifest_sha256"]
        and manifests["hashes"]["pair_orbits"]
        == spec["rule_family_split"]["same_block_pair_orbit_manifest_sha256"]
        and manifests["hashes"]["assignments"]
        == spec["candidate_pool"]["assignment_manifest_sha256"]
        and manifests["hashes"]["queries"]
        == spec["inherited_carrier"]["query_manifest_sha256"],
        "P7_design_fixture_manifest": len(selected) == spec["rule_family_split"]["design_fixture_count"]
        and digest_text(compact_json(selected))
        == spec["rule_family_split"]["design_fixture_manifest_sha256"],
        "P8_confirmation_counts": len(fixture_representatives(manifests, "validation")) == 325
        and len(fixture_representatives(manifests, "test")) == 531,
        "P9_candidate_universe": candidate_counts == spec["candidate_pool"]["candidate_counts"],
        "P10_shortlist_shape": spec["two_stage_search"]["shortlist_per_size"] == 32
        and 32 * len(spec["candidate_pool"]["subset_sizes"]) == 96,
        "P11_search_sources_absent_at_freeze": receipt["search_sources_present_when_frozen"] is False
        and search_history["passed"],
        "P12_confirmation_sources_absent_at_freeze": receipt["confirmation_sources_present_when_frozen"] is False
        and confirm_history["passed"],
        "P13_no_posthoc_size_selection": spec["candidate_pool"]["all_sizes_remain_claim_bearing"] is True
        and spec["candidate_pool"]["posthoc_size_deletion_forbidden"] is True,
        "P14_test_is_not_blind": "historically consumed" in spec["rule_family_split"]["secondary_confirmation"]
        and spec["confirmation_policy"]["test_status"] == "reused confirmation only; never blind",
        "P15_pytorch_and_learning_blocked": "excluded" in spec["engine_contract"]["pytorch"]
        and any("neural training" in item for item in spec["blocked_consumers"]),
    }
    result = {
        "schema": "codex_ratchet.eca_relation_directed_observation_design_v1.preregistration_validation.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "manifest_receipt": {
            "inherited_hashes": manifests["hashes"],
            "design_fixture_count": len(selected),
            "design_fixture_manifest_sha256": digest_text(compact_json(selected)),
            "design_fixture_examples": [list(pair) for pair in selected[:8]],
            "candidate_counts": candidate_counts,
        },
        "historical_source_checks": {
            "search": search_history,
            "confirmation": confirm_history,
        },
        "tests": tests,
        "all_pass": all(tests.values()),
        "claim_ceiling": "frozen target-aware two-phase search design only; no search result, measurement candidate, learner, or perception claim",
        "blocked_consumers": spec["blocked_consumers"],
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "tests": tests, "manifest_receipt": result["manifest_receipt"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
