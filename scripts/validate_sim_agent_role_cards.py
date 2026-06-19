#!/usr/bin/env python3
"""Validate sim agent role-card YAML blocks."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


REQUIRED_FIELDS = {
    "role_id",
    "goal",
    "scope",
    "out_of_scope",
    "read_first",
    "acceptance",
    "deliverable",
    "receipt_fields",
    "closeout_check",
}


def _cards(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    cards: list[dict[str, Any]] = []
    for match in re.finditer(r"```yaml\n(.*?)\n```", text, re.DOTALL):
        loaded = yaml.safe_load(match.group(1))
        if isinstance(loaded, dict) and "role_id" in loaded:
            cards.append(loaded)
    return cards


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    cards = _cards(path)
    if not cards:
        return ["no role cards found"]
    seen: set[str] = set()
    for card in cards:
        role_id = str(card.get("role_id", ""))
        if role_id in seen:
            errors.append(f"duplicate role_id: {role_id}")
        seen.add(role_id)
        missing = sorted(REQUIRED_FIELDS - set(card))
        if missing:
            errors.append(f"{role_id or '<missing role_id>'} missing fields: {', '.join(missing)}")
        for list_key in ("read_first", "acceptance", "receipt_fields"):
            if not isinstance(card.get(list_key), list) or not card.get(list_key):
                errors.append(f"{role_id}.{list_key} must be a non-empty list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    errors = validate(args.path)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "path": str(args.path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
