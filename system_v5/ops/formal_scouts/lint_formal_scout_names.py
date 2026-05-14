#!/usr/bin/env python3
"""Lint formal-scout executable names for target-system labels."""

from __future__ import annotations

import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parent
BANNED_TOKENS = {
    "axis",
    "engine",
    "gstack",
    "rosetta",
    "type1",
    "type2",
    "iching",
}


def tokenize(path: pathlib.Path) -> set[str]:
    return {token for token in path.stem.lower().replace("-", "_").split("_") if token}


def lint_path(path: pathlib.Path) -> dict[str, object]:
    tokens = tokenize(path)
    hits = sorted(tokens & BANNED_TOKENS)
    return {
        "path": str(path),
        "pass": not hits,
        "banned_tokens": hits,
    }


def main() -> int:
    paths = [pathlib.Path(arg) for arg in sys.argv[1:]] or sorted(ROOT.glob("sim_*.py"))
    rows = [lint_path(path) for path in paths]
    all_pass = all(bool(row["pass"]) for row in rows)
    print(json.dumps({"all_pass": all_pass, "banned_tokens": sorted(BANNED_TOKENS), "results": rows}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
