#!/usr/bin/env python3
"""Fail-closed prospective seal validation for UFPO v0."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec.json"
README = HERE / "README.md"
GENERATOR = HERE / "generate_manifest.py"
MANIFEST = HERE / "object_manifest.json"
CARD = HERE / "wizard_v4_3_object_card.json"
PREREG = HERE / "preregistration_receipt.json"
CORRECTION = HERE / "PREREGISTRATION_CORRECTION.md"
DEFAULT_OUTPUT = HERE / "results" / "preregistration_validation.json"
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "Strict JSON, SHA-256, split, identity, and prospective seal validation."}
}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


class ValidationError(RuntimeError):
    pass


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant: {token}")


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain one object")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate() -> dict[str, Any]:
    spec = load(SPEC)
    manifest = load(MANIFEST)
    prereg = load(PREREG)
    card = load(CARD)
    require(prereg["status"] == "frozen_correction_before_engine_result_acceptance", "preregistration status drift")
    require(prereg["spec_sha256"] == sha(SPEC), "spec hash mismatch")
    require(prereg["readme_sha256"] == sha(README), "README hash mismatch")
    require(prereg["manifest_generator_sha256"] == sha(GENERATOR), "manifest generator hash mismatch")
    require(prereg["object_manifest_sha256"] == sha(MANIFEST), "manifest hash mismatch")
    require(prereg["wizard_v4_3_object_card_sha256"] == sha(CARD), "object card hash mismatch")
    require(prereg["correction_sha256"] == sha(CORRECTION), "correction hash mismatch")
    require(prereg["original_frozen_spec_sha256"] == "b8660e4b05066a6dbb733e443989bbde50a74caa3145892d0baf0a740b89536f", "original spec hash drift")
    require(manifest["spec_sha256"] == prereg["original_frozen_spec_sha256"], "manifest/original-spec binding mismatch")
    require(spec["engine_contract"]["original_frozen_spec_sha256"] == prereg["original_frozen_spec_sha256"], "corrected spec lost original binding")
    require("any Julia disagreement" in spec["engine_contract"]["julia_disagreement_policy"], "Julia disagreement does not block packet")
    require(manifest["accepted_candidate_count"] == 1254, "accepted candidate count drift")
    require(manifest["selection"] == "first 192 after canonical machine hash sort", "selection rule drift")
    require({key: len(value) for key, value in manifest["splits"].items()} == {"train": 128, "validation": 32, "test": 32}, "split counts drift")
    require(len(manifest["hard_negative_test_pairs"]) == 16, "short-horizon-matched pair count drift")
    all_rows = [row for split in ("train", "validation", "test") for row in manifest["splits"][split]]
    hashes = [row["machine_sha256"] for row in all_rows]
    signatures = [row["predictive_signature_sha256"] for row in all_rows]
    require(len(hashes) == len(set(hashes)) == 192, "machine identity overlap")
    require(len(signatures) == len(set(signatures)) == 192, "predictive signature overlap")
    require(all(len(row["machine"]) == 4 for row in all_rows), "malformed machine")
    test_hashes = {row["machine_sha256"] for row in manifest["splits"]["test"]}
    pair_members = [item for pair in manifest["hard_negative_test_pairs"] for item in pair]
    require(len(pair_members) == len(set(pair_members)) == 32, "short-horizon-matched pairing is not a partition")
    require(set(pair_members) == test_hashes, "short-horizon-matched pair membership differs from test split")
    require(manifest["test_outcome_status"].endswith("no learned test metric exists"), "test seal text drift")
    require(card["schema_version"] == "wizard_v4_3_primary_object_card_v1", "object card schema drift")
    require(spec["frozen_splits"]["model_seeds"] == [1701, 1702, 1703], "model seeds drift")
    require(spec["learner"]["checkpoint_policy"].startswith("score epoch 32 only"), "checkpoint policy drift")
    require(spec["promotion_allowed"] is False and spec["formal_admission_allowed"] is False, "promotion lock removed")
    return {
        "schema": "codex_ratchet.unseen_finite_predictive_objects_v0.preregistration_validation.v2",
        "sim_id": spec["sim_id"],
        "classification": "scratch_diagnostic",
        "all_pass": True,
        "spec_sha256": sha(SPEC),
        "manifest_sha256": sha(MANIFEST),
        "preregistration_sha256": sha(PREREG),
        "object_card_sha256": sha(CARD),
        "split_counts": {key: len(value) for key, value in manifest["splits"].items()},
        "test_objects_sealed": 32,
        "short_horizon_matched_pairs_sealed": 16,
        "julia_semantic_arbitration_required": True,
        "manifest_immutable_under_correction": True,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = validate()
    except ValidationError as exc:
        result = {
            "schema": "codex_ratchet.unseen_finite_predictive_objects_v0.preregistration_validation.v2",
            "sim_id": "unseen_finite_predictive_objects_v0",
            "classification": "scratch_diagnostic",
            "all_pass": False,
            "error": str(exc),
            "promotion_allowed": False,
            "formal_admission_allowed": False,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
