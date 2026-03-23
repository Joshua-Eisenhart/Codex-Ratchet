#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCHEMA = "A1_QUEUE_CANDIDATE_REGISTRY_v1"


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"missing_input:{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid_json:{path}:{exc.lineno}:{exc.colno}") from exc


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_abs_existing(value: object, key: str, errors: list[str]) -> None:
    if not _is_nonempty_text(value):
        errors.append(f"missing_{key}")
        return
    path = Path(str(value).strip())
    if not path.is_absolute():
        errors.append(f"non_absolute_{key}")
        return
    if not path.exists():
        errors.append(f"missing_path_{key}:{path}")


def validate(packet: dict) -> dict:
    errors: list[str] = []

    if packet.get("schema") != SCHEMA:
        errors.append("invalid_schema")

    candidates = packet.get("candidate_family_slice_jsons")
    if not isinstance(candidates, list):
        errors.append("invalid_candidate_family_slice_jsons")
        candidates = []
    else:
        seen: set[str] = set()
        for index, item in enumerate(candidates, start=1):
            _require_abs_existing(item, f"candidate_family_slice_jsons[{index}]", errors)
            if _is_nonempty_text(item):
                normalized = str(item).strip()
                if normalized in seen:
                    errors.append("duplicate_candidate_family_slice_json")
                seen.add(normalized)

    selected = packet.get("selected_family_slice_json", "")
    if selected not in ("", None):
        _require_abs_existing(selected, "selected_family_slice_json", errors)
        if isinstance(candidates, list) and str(selected).strip() not in {str(item).strip() for item in candidates if _is_nonempty_text(item)}:
            errors.append("selected_family_slice_not_in_candidates")

    return {
        "schema": "A1_QUEUE_CANDIDATE_REGISTRY_VALIDATION_RESULT_v1",
        "valid": not errors,
        "errors": errors,
        "packet_schema": packet.get("schema", ""),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate one A1 queue candidate registry.")
    parser.add_argument("--registry-json", required=True)
    args = parser.parse_args(argv)

    result = validate(_load_json(Path(args.registry_json)))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
