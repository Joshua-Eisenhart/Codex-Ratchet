#!/usr/bin/env python3
"""Validate the compact Wizard loop RUN_RECEIPT profile."""

import argparse
import json
import sys
from pathlib import Path


REQUIRED_KEYS = {
    "receipt_id",
    "loop_number",
    "what_ran",
    "claims_checked",
    "open_items",
    "stop_signals_fired",
    "metrics_delta",
    "honest_status_summary",
}

ALLOWED_CEILINGS = {
    "exists",
    "runs",
    "passes_local",
    "canonical",
    "scratch_diagnostic",
    "GENUINE-WITH-CAVEATS",
}


def validate(receipt: dict) -> list[str]:
    errors = []
    missing = sorted(REQUIRED_KEYS - set(receipt))
    if missing:
        errors.append(f"missing required keys: {', '.join(missing)}")

    what_ran = receipt.get("what_ran")
    if not isinstance(what_ran, list):
        errors.append("what_ran must be a list")
    elif receipt.get("loop_number", 0) and not what_ran:
        errors.append("what_ran must be non-empty when loop_number claims work")

    claims = receipt.get("claims_checked")
    if not isinstance(claims, list):
        errors.append("claims_checked must be a list")
        claims = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claims_checked[{index}] must be an object")
            continue
        if not claim.get("claim"):
            errors.append(f"claims_checked[{index}].claim is required")
        if claim.get("result") not in {"confirmed", "refuted", "partial", "not_checked"}:
            errors.append(f"claims_checked[{index}].result is invalid")
        if claim.get("ceiling") not in ALLOWED_CEILINGS:
            errors.append(f"claims_checked[{index}].ceiling is invalid")

    open_items = receipt.get("open_items")
    if not isinstance(open_items, list):
        errors.append("open_items must be a list")

    stop_signals = receipt.get("stop_signals_fired")
    if not isinstance(stop_signals, list):
        errors.append("stop_signals_fired must be a list")
    elif any(not isinstance(signal, str) or not signal for signal in stop_signals):
        errors.append("stop_signals_fired entries must be non-empty strings")

    metrics_delta = receipt.get("metrics_delta")
    if not isinstance(metrics_delta, dict):
        errors.append("metrics_delta must be an object")

    summary = receipt.get("honest_status_summary")
    if not isinstance(summary, str) or not summary.strip():
        errors.append("honest_status_summary must be non-empty")

    council_outputs = receipt.get("council_outputs", [])
    if council_outputs:
        if not isinstance(council_outputs, list):
            errors.append("council_outputs must be a list when present")
        else:
            decorative = 0
            for index, output in enumerate(council_outputs):
                if not isinstance(output, dict):
                    errors.append(f"council_outputs[{index}] must be an object")
                    continue
                if output.get("decorative") is True:
                    decorative += 1
                if output.get("decorative") is not True and not output.get("changed_field"):
                    errors.append(
                        f"council_outputs[{index}] must affect a changed_field or be marked decorative"
                    )
            if decorative * 2 >= len(council_outputs):
                errors.append("decorative-majority council outputs are not allowed")

    refuted_or_unchecked = {
        claim.get("claim")
        for claim in claims
        if isinstance(claim, dict) and claim.get("result") in {"refuted", "not_checked"}
    }
    open_text = " ".join(
        json.dumps(item, sort_keys=True) for item in open_items if isinstance(open_items, list)
    )
    missing_open = sorted(claim for claim in refuted_or_unchecked if claim and claim not in open_text)
    if missing_open:
        errors.append(
            "refuted/not_checked claims must appear in open_items: "
            + ", ".join(missing_open)
        )

    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt")
    ap.add_argument("--json-indent", type=int, default=2)
    args = ap.parse_args()

    receipt_path = Path(args.receipt)
    try:
        receipt = json.loads(receipt_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        result = {"ok": False, "receipt": str(receipt_path), "errors": [str(exc)]}
        json.dump(result, sys.stdout, indent=args.json_indent)
        print()
        return 1

    errors = validate(receipt)
    result = {"ok": not errors, "receipt": str(receipt_path), "errors": errors}
    json.dump(result, sys.stdout, indent=args.json_indent)
    print()
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
