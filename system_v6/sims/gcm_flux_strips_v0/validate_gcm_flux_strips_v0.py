#!/usr/bin/env python3
"""Validate the complete GCM geometric flux strip packet."""

from __future__ import annotations

import json
from pathlib import Path

from gcm_flux_strips_v0 import RESULT_PATH, VALIDATOR_RESULT_PATH, load_json, validate_payload, write_json


def validate(write: bool = True) -> dict:
    payload = load_json(RESULT_PATH)
    errors = validate_payload(payload)
    result = {"ok": not errors, "errors": errors, "result_path": str(RESULT_PATH)}
    if write:
        write_json(VALIDATOR_RESULT_PATH, result)
    return result


def main() -> None:
    result = validate(write=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()

