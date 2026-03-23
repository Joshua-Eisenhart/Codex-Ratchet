#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from a2_to_a1_family_slice_models import load_family_slice


def build_result(family_slice_json: Path) -> dict:
    family_slice = load_family_slice(family_slice_json)
    return {
        "schema": "A2_TO_A1_FAMILY_SLICE_PYDANTIC_AUDIT_v1",
        "valid": True,
        "family_slice_json": str(family_slice_json),
        "family_id": family_slice.family_id,
        "run_mode": family_slice.run_mode,
        "graph_summary": family_slice.graph_summary(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate one A2_TO_A1_FAMILY_SLICE_v1 using the local Pydantic model.")
    parser.add_argument("--family-slice-json", required=True)
    args = parser.parse_args(argv)

    family_slice_json = Path(args.family_slice_json)
    if not family_slice_json.is_absolute():
        raise SystemExit("non_absolute_family_slice_json")

    result = build_result(family_slice_json)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
