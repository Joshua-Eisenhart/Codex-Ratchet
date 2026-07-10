#!/usr/bin/env python3
"""Fail-closed validation of the frozen UFPO v1 preregistration surfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.json"
MANIFEST = HERE / "object_manifest.json"
GENERATOR = HERE / "generate_manifest.py"
README = HERE / "README.md"
DESIGN = HERE / "PREREGISTRATION_DESIGN.md"
CARD = HERE / "wizard_v4_3_object_card.json"
ENGINE_SOURCES = {name: HERE / path for name, path in {
    "julia": "run_julia.jl", "jax": "run_jax.py", "pytorch": "run_pytorch.py",
    "recompute_metrics": "recompute_metrics.py", "controller": "validate_results.py",
}.items()}
DEFAULT_OUTPUT = HERE / "results" / "preregistration_validation.json"
SIM_ID = "unseen_finite_predictive_objects_v1"
GREEN = "BOUNDED_SUPERVISED_MULTI_VIEW_PREDICTIVE_RETRIEVAL_ON_UNSEEN_FOUR_STATE_OBJECTS_UNDER_FROZEN_LOSSY_VIEWS"
RED = "UNSEEN_PREDICTIVE_OBJECT_LEARNING_NOT_ESTABLISHED"


class ValidationError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant, object_pairs_hook=reject_duplicates)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain one JSON object")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate() -> dict[str, Any]:
    spec, manifest, card = load(SPEC), load(MANIFEST), load(CARD)
    require(spec.get("schema") == f"codex_ratchet.{SIM_ID}.spec.v1", "spec schema drift")
    require(manifest.get("schema") == f"codex_ratchet.{SIM_ID}.object_manifest.v1", "manifest schema drift")
    require(spec.get("sim_id") == manifest.get("sim_id") == SIM_ID, "sim identity drift")
    require(manifest.get("spec_sha256") == sha(SPEC), "manifest/spec hash mismatch")
    require(spec.get("classification") == manifest.get("classification") == "scratch_diagnostic", "classification drift")
    require(spec.get("promotion_allowed") is False and manifest.get("promotion_allowed") is False, "promotion lock removed")
    require(spec.get("formal_admission_allowed") is False and manifest.get("formal_admission_allowed") is False, "admission lock removed")
    require(manifest.get("learner_source_sealed") is False, "manifest improperly claims learner sealing")
    require(spec.get("learner_source_status") == "not_sealed_by_manifest_generation", "learner-source status drift")
    require(spec.get("accepted_green_ceiling") == GREEN and spec.get("accepted_red_ceiling") == RED, "claim ceiling drift")
    require(spec.get("engine_contract", {}).get("mode") == "all_three_full_sims", "all-three engine contract removed")
    require(spec["engine_contract"].get("semantic_owner") == "Julia independent exact finite predictive-equivalence verification and arbitration", "Julia semantic ownership drift")
    require(spec["engine_contract"].get("jacrev") == "supportive only; never a semantic arbiter or primary gate", "supportive jacrev ceiling drift")
    require(spec["view_process"].get("model_seeds") == [2701, 2702, 2703], "model seed plan drift")
    require(spec["view_process"].get("seed_domain") == "ufpo-v1|view|split|machine-hash|view-index|trajectory-index|channel", "view seed domain drift")
    require(spec["learner"].get("checkpoint_policy") == "score epoch 16 only; no early stopping or test-aware selection", "checkpoint policy drift")
    require(manifest.get("candidate_interval") == [0, 8191] and manifest.get("accepted_candidate_count") == 2367, "candidate census drift")
    require(manifest.get("split_counts") == {"train": 128, "validation": 32, "test": 32}, "declared split counts drift")
    require({name: len(manifest["splits"][name]) for name in ("train", "validation", "test")} == {"train": 128, "validation": 32, "test": 32}, "actual split counts drift")
    rows = [row for split in ("train", "validation", "test") for row in manifest["splits"][split]]
    machine_hashes = [row["machine_sha256"] for row in rows]
    signature_hashes = [row["predictive_signature_sha256"] for row in rows]
    require(len(set(machine_hashes)) == len(set(signature_hashes)) == len(rows) == 192, "split identity overlap")
    pairs = manifest.get("test_pairing", {}).get("pairs", [])
    members = [pair[key] for pair in pairs for key in ("left_machine_sha256", "right_machine_sha256")]
    require(len(pairs) == 16 and len(members) == len(set(members)) == 32, "test pairing is not a 32-object partition")
    require(set(members) == {row["machine_sha256"] for row in manifest["splits"]["test"]}, "test pairing membership drift")
    require(card.get("schema_version") == "wizard_v4_3_primary_object_card_v1", "object-card schema drift")
    require(card.get("evidence_spine", {}).get("claim_ceiling") == "object-preservation and preregistration/controller validation only; no proof, admission, QIT, Axis0, physics, life, or consciousness claim", "object-card claim ceiling drift")
    source_hashes = {name: sha(path) for name, path in ENGINE_SOURCES.items()}
    return {
        "schema": f"codex_ratchet.{SIM_ID}.preregistration_validation.v1", "sim_id": SIM_ID,
        "classification": "scratch_diagnostic", "all_pass": True, "spec_sha256": sha(SPEC),
        "object_manifest_sha256": sha(MANIFEST), "manifest_generator_sha256": sha(GENERATOR),
        "readme_sha256": sha(README), "preregistration_design_sha256": sha(DESIGN),
        "wizard_v4_3_object_card_sha256": sha(CARD), "expected_source_sha256": source_hashes,
        "engine_mode": "all_three_full_sims", "accepted_green_ceiling": GREEN,
        "accepted_red_ceiling": RED, "promotion_allowed": False, "formal_admission_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = validate()
    except (ValidationError, KeyError, TypeError, OSError) as exc:
        result = {"schema": f"codex_ratchet.{SIM_ID}.preregistration_validation.v1", "sim_id": SIM_ID,
                  "classification": "scratch_diagnostic", "all_pass": False, "error": str(exc),
                  "accepted_claim_label": RED, "promotion_allowed": False, "formal_admission_allowed": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
