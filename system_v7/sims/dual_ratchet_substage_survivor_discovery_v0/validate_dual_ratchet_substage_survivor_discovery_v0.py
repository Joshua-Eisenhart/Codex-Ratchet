#!/usr/bin/env python3
"""Validate the bounded Julia/JAX operator-quotient scout receipts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SPEC_PATH = HERE / "spec.json"
JAX_SOURCE = HERE / "dual_ratchet_substage_survivor_discovery_v0_jax.py"
JULIA_SOURCE = HERE / "dual_ratchet_substage_survivor_discovery_v0_julia.jl"
JAX_RESULT = HERE / "results" / "dual_ratchet_substage_survivor_discovery_v0_jax_results.json"
JULIA_RESULT = HERE / "results" / "dual_ratchet_substage_survivor_discovery_v0_julia_results.json"
AGREEMENT_RESULT = HERE / "results" / "dual_ratchet_substage_survivor_discovery_v0_agreement.json"
EXPECTED_VERDICT = "conditional_pauli_registry_four_class_operator_quotient_only"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def contains_key(value: Any, forbidden: str) -> bool:
    if isinstance(value, dict):
        return forbidden in value or any(contains_key(item, forbidden) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, forbidden) for item in value)
    return False


def comparable_main_checks(result: dict[str, Any]) -> dict[str, bool]:
    return {
        key: bool(value)
        for key, value in result["main_checks"].items()
        if key not in {"strict_carrier_project", "strict_load_path"}
    }


def main() -> int:
    jax = load(JAX_RESULT)
    julia = load(JULIA_RESULT)
    checks = {
        "both_local_packet_gates_pass": jax["all_pass"] is True and julia["all_pass"] is True,
        "verdicts_match_conditional_ceiling": jax["scientific_verdict"] == julia["scientific_verdict"] == EXPECTED_VERDICT,
        "main_partitions_agree": jax["main_pauli_registry"]["reference_partition"] == julia["main_pauli_registry"]["reference_partition"],
        "generic_partitions_agree": jax["generic_axis_challenge"]["reference_partition"] == julia["generic_axis_challenge"]["reference_partition"],
        "main_checks_agree": comparable_main_checks(jax) == comparable_main_checks(julia),
        "falsifier_checks_agree": jax["falsifier_checks"] == julia["falsifier_checks"],
        "main_class_count_is_four": jax["main_pauli_registry"]["reference_class_count"] == julia["main_pauli_registry"]["reference_class_count"] == 4,
        "generic_control_blocks_universal_four": jax["generic_axis_challenge"]["reference_class_count"] == julia["generic_axis_challenge"]["reference_class_count"] == 8,
        "foundational_four_remains_false": jax["foundational_four_substage_emergence_earned"] is False and julia["foundational_four_substage_emergence_earned"] is False,
        "history_dependent_dual_ratchet_remains_false": jax["history_dependent_dual_ratchet_tested"] is False and julia["history_dependent_dual_ratchet_tested"] is False,
        "per_stage_substages_remain_false": jax["per_stage_four_substages_earned"] is False and julia["per_stage_four_substages_earned"] is False,
        "compact_receipts_omit_raw_fingerprints": not contains_key(jax, "fingerprint") and not contains_key(julia, "fingerprint"),
        "jax_source_hash_matches": jax["source_hashes"][str(JAX_SOURCE.relative_to(REPO))] == digest(JAX_SOURCE),
        "jax_spec_hash_matches": jax["source_hashes"][str(SPEC_PATH.relative_to(REPO))] == digest(SPEC_PATH),
        "julia_source_hash_matches": julia["source_sha256"] == digest(JULIA_SOURCE),
        "julia_spec_hash_matches": julia["spec_sha256"] == digest(SPEC_PATH),
    }
    all_pass = all(checks.values())
    receipt = {
        "schema": "codex_ratchet.dual_ratchet_substage_survivor_discovery_v0.agreement.v1",
        "sim_id": "dual_ratchet_substage_survivor_discovery_v0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "claim_ceiling": "Conditional four-operator-class quotient inside the finite Pauli registry only; not per-stage substages or a history-dependent dual ratchet.",
        "checks": checks,
        "all_pass": all_pass,
        "source_hashes": {
            str(SPEC_PATH.relative_to(REPO)): digest(SPEC_PATH),
            str(JAX_SOURCE.relative_to(REPO)): digest(JAX_SOURCE),
            str(JULIA_SOURCE.relative_to(REPO)): digest(JULIA_SOURCE),
            str(JAX_RESULT.relative_to(REPO)): digest(JAX_RESULT),
            str(JULIA_RESULT.relative_to(REPO)): digest(JULIA_RESULT),
        },
        "measured": {
            "main_class_count": jax["main_pauli_registry"]["reference_class_count"],
            "generic_class_count": jax["generic_axis_challenge"]["reference_class_count"],
            "main_survivor_count": jax["main_pauli_registry"]["reference_intersection_survivor_count"],
            "generic_survivor_count": jax["generic_axis_challenge"]["reference_intersection_survivor_count"],
            "scientific_verdict": jax["scientific_verdict"],
        },
        "blocked_consumers": [
            "per-stage four-substage execution",
            "history-dependent dual ratchet",
            "Type-1/Type-2 engine admission",
            "Axis0, perception, object, MMM, ontology, or Lev mesh authority",
        ],
    }
    AGREEMENT_RESULT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result_path": str(AGREEMENT_RESULT), "all_pass": all_pass, "checks": checks}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
