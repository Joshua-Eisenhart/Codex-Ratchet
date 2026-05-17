#!/usr/bin/env python3
"""Validate provider premortem receipts.

This intentionally stays separate from validate_provider_receipts.py because
premortem receipts are proposal-only failure analyses, not provider proposals.
"""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


EXPECTED_SCHEMA = "PROVIDER_PREMORTEM_RECEIPT_v1"
EXPECTED_CLASSIFICATION = "proposal_only_premortem"


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate(path: pathlib.Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return {"path": str(path), "pass": False, "errors": [f"could not read json: {exc}"]}

    if data.get("schema") != EXPECTED_SCHEMA:
        errors.append("wrong schema")
    if data.get("classification") != EXPECTED_CLASSIFICATION:
        errors.append("wrong classification")
    if data.get("status") != "completed":
        errors.append("status is not completed")
    if data.get("promotion_allowed") is not False:
        errors.append("promotion_allowed must be false")
    if data.get("evidence_allowed") is not False:
        errors.append("evidence_allowed must be false")
    if not nonempty(data.get("provider")):
        errors.append("missing provider")
    if not nonempty(data.get("model")):
        errors.append("missing model")
    if not nonempty(data.get("prompt_hash")):
        errors.append("missing prompt_hash")
    if not nonempty(data.get("claim_ceiling")):
        errors.append("missing claim_ceiling")
    premortem_text = data.get("premortem_text")
    if not nonempty(premortem_text):
        errors.append("missing premortem_text")
    else:
        required_markers = [
            "most_likely_failure",
            "most_dangerous_failure",
            "hidden_assumption",
            "early_warning_signs",
        ]
        for marker in required_markers:
            if marker not in premortem_text:
                errors.append(f"premortem_text missing {marker}")
    grounding = data.get("repo_grounding")
    targets = grounding.get("targets") if isinstance(grounding, dict) else None
    if not isinstance(targets, list) or not targets:
        errors.append("missing repo_grounding targets")

    return {"path": str(path), "pass": not errors, "errors": errors}


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_provider_premortem_receipts.py RECEIPT [...]", file=sys.stderr)
        return 2
    results = [validate(pathlib.Path(arg)) for arg in argv]
    payload = {"all_pass": all(row["pass"] for row in results), "results": results}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
