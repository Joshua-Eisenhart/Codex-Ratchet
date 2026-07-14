#!/usr/bin/env python3
"""Adversarial regression checks for the campaign envelope validator."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from validate_hardened_campaign_v2 import validate


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
ENVELOPE = HERE / "results" / "hardened_campaign_v2_envelope.json"


def main() -> int:
    original = json.loads(ENVELOPE.read_text(encoding="utf-8"))

    def h_lane(raw: dict) -> dict:
        return next(lane for lane in raw["lanes"] if lane["id"] == "H")

    def k_lane(raw: dict) -> dict:
        return next(lane for lane in raw["lanes"] if lane["id"] == "K")

    def forge_partial_promotion(raw: dict) -> None:
        raw["claim_ceiling"] = "capability_fit_all_pass authorizes partial promotion"
        raw["blocked_consumers"] = []
        raw["partial_promotion_eligible"] = True

    def replay_timestamps(raw: dict) -> None:
        stamp = "2000-01-01T00:00:00+00:00"
        raw["created_at"] = stamp
        raw["runner_identity"]["runner_started_at"] = stamp
        raw["runner_identity"]["runner_finished_at"] = stamp
        for lane in raw["lanes"]:
            lane["started_at"] = stamp
            lane["finished_at"] = stamp

    def substitute_k_result(raw: dict) -> None:
        target = REPO_ROOT / "AGENTS.md"
        k_lane(raw)["result_path"] = str(target)
        k_lane(raw)["result_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()

    def substitute_sources(raw: dict) -> None:
        target = REPO_ROOT / "AGENTS.md"
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        raw["runtime_doctor"]["source_path"] = str(target)
        raw["runtime_doctor"]["source_sha256"] = digest
        for lane in raw["lanes"]:
            lane["producer_source_path"] = str(target)
            lane["producer_source_sha256"] = digest

    mutations = {
        "forged_campaign_all_pass": lambda raw: raw.update(all_pass=True),
        "forged_promotion_eligibility": lambda raw: raw.update(promotion_eligible=True),
        "forged_h_green": lambda raw: h_lane(raw).update(receipt_all_pass=True),
        "forged_k_result_hash": lambda raw: k_lane(raw).update(result_sha256="0" * 64),
        "erased_runner_completion": lambda raw: raw.update(runner_all_completed=False),
        "forged_runtime_doctor": lambda raw: raw["runtime_doctor"].update(all_gates_pass=False),
        "erased_top_level_provenance": lambda raw: raw.pop("created_at"),
        "forged_partial_promotion_alias": forge_partial_promotion,
        "replayed_envelope_timestamps": replay_timestamps,
        "self_consistent_result_substitution": substitute_k_result,
        "self_consistent_source_substitution": substitute_sources,
        "provider_evidence_alias": lambda raw: raw.update(provider_opinion_ingested_as_evidence=True),
        "erased_blocked_consumers": lambda raw: raw.update(blocked_consumers=[]),
    }
    receipts = {}
    for name, mutate in mutations.items():
        candidate = copy.deepcopy(original)
        mutate(candidate)
        errors = validate(candidate)
        receipts[name] = {"rejected": bool(errors), "errors": errors}
    all_pass = all(row["rejected"] for row in receipts.values())
    print(json.dumps({"all_pass": all_pass, "controls": receipts}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
