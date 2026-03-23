#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_a1_queue_candidate_registry import validate as validate_registry


def _require_abs_existing(path_str: str, key: str) -> str:
    path = Path(path_str)
    if not path.is_absolute():
        raise SystemExit(f"non_absolute_{key}")
    if not path.exists():
        raise SystemExit(f"missing_path_{key}:{path}")
    return str(path)


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Create one machine-readable A1 queue candidate registry.")
    parser.add_argument("--family-slice-json", action="append", default=[])
    parser.add_argument("--selected-family-slice-json", default="")
    parser.add_argument("--out-json", required=True)
    args = parser.parse_args(argv)

    out_json = Path(args.out_json)
    if not out_json.is_absolute():
        raise SystemExit("non_absolute_out_json")

    candidates = _dedupe_preserve_order(
        [_require_abs_existing(path, f"family_slice_json[{index}]") for index, path in enumerate(args.family_slice_json, start=1)]
    )
    selected = ""
    if args.selected_family_slice_json:
        selected = _require_abs_existing(args.selected_family_slice_json, "selected_family_slice_json")

    packet = {
        "schema": "A1_QUEUE_CANDIDATE_REGISTRY_v1",
        "candidate_family_slice_jsons": candidates,
        "selected_family_slice_json": selected,
    }
    validation = validate_registry(packet)
    if not validation["valid"]:
        raise SystemExit(f"candidate_registry_invalid:{validation['errors'][0]}")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
