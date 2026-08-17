#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SKILLS = Path(os.environ.get("CB_SKILLS_ROOT", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(SKILLS / "cb-wave-author" / "scripts"))
import validate_wave as validator
sys.path.insert(0, str(SKILLS / "cb-capability-binder"))
from scripts.bind import bind_wave
sys.path.insert(0, str(SKILLS / "cb-management-plane" / "scripts"))
from plane import digest_obj, now


REQUIRED_NEGATIVES = (
    "positive",
    "reason_specific_negative",
    "boundary",
    "replay",
    "severance",
    "cancellation",
    "receipt_tamper",
)

CONTRACT_FIELDS = (
    "object_card",
    "target_digest",
    "context_epoch_digest",
    "parent",
    "progress_measure",
    "claim_ceiling",
    "downstream_consumer",
)


def admit(wave: dict, negatives: dict | None = None, contract: dict | None = None) -> dict:
    errors = validator.validate(wave)
    binding = bind_wave(wave)
    missing_neg = [key for key in REQUIRED_NEGATIVES if not (negatives or {}).get(key)]
    if errors:
        return {"schema": "constraintbox.wave-recipe.v1", "status": "REFUSE", "reason": "REFUSE_SHAPE", "errors": errors, "activated": False, "promotion_allowed": False}
    if binding.get("status") != "BOUND":
        return {"schema": "constraintbox.wave-recipe.v1", "status": "HOLD", "reason": "HOLD_UNBOUND_TOOLS", "binding": binding, "activated": False, "promotion_allowed": False}
    if missing_neg:
        return {"schema": "constraintbox.wave-recipe.v1", "status": "HOLD", "reason": "HOLD_NEGATIVE_MATRIX", "missing": missing_neg, "activated": False, "promotion_allowed": False}
    if contract is not None:
        missing_contract = [key for key in CONTRACT_FIELDS if not contract.get(key)]
        if missing_contract:
            return {"schema": "constraintbox.wave-recipe.v1", "status": "HOLD", "reason": "HOLD_CONTRACT", "missing": missing_contract, "activated": False, "promotion_allowed": False}
        if contract.get("promotion_allowed") is not False:
            return {"schema": "constraintbox.wave-recipe.v1", "status": "REFUSE", "reason": "REFUSE_PROMOTION", "activated": False, "promotion_allowed": False}
    recipe = {
        "schema": "constraintbox.wave-recipe.v1",
        "status": "FROZEN",
        "wave_id": wave.get("wave_id"),
        "topology_digest": digest_obj(wave.get("children")),
        "wave_digest": digest_obj(wave),
        "binding": binding,
        "activated": False,
        "frozen_at": now(),
        "promotion_allowed": False,
    }
    return recipe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", type=Path, required=True)
    parser.add_argument("--negatives", type=Path, default=None)
    parser.add_argument("--contract", type=Path, default=None)
    args = parser.parse_args()
    negatives = json.loads(args.negatives.read_text(encoding="utf-8")) if args.negatives else {}
    contract = json.loads(args.contract.read_text(encoding="utf-8")) if args.contract else None
    receipt = admit(json.loads(args.wave.read_text(encoding="utf-8")), negatives, contract)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt.get("status") == "FROZEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
