#!/usr/bin/env python3
"""Adversarial regression checks for the campaign envelope validator."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from validate_hardened_campaign_v2 import validate


HERE = Path(__file__).resolve().parent
ENVELOPE = HERE / "results" / "hardened_campaign_v2_envelope.json"


def main() -> int:
    original = json.loads(ENVELOPE.read_text(encoding="utf-8"))

    def h_lane(raw: dict) -> dict:
        return next(lane for lane in raw["lanes"] if lane["id"] == "H")

    def k_lane(raw: dict) -> dict:
        return next(lane for lane in raw["lanes"] if lane["id"] == "K")

    mutations = {
        "forged_campaign_all_pass": lambda raw: raw.update(all_pass=True),
        "forged_promotion_eligibility": lambda raw: raw.update(promotion_eligible=True),
        "forged_h_green": lambda raw: h_lane(raw).update(receipt_all_pass=True),
        "forged_k_result_hash": lambda raw: k_lane(raw).update(result_sha256="0" * 64),
        "erased_runner_completion": lambda raw: raw.update(runner_all_completed=False),
        "forged_runtime_doctor": lambda raw: raw["runtime_doctor"].update(all_gates_pass=False),
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
