#!/usr/bin/env python3
"""Load and compose Constraint Box MMM packs."""

import argparse
import json
import sys
from pathlib import Path


PACKS_DIR = Path(__file__).resolve().parent / "packs"
SEPARATOR = "\n\n---\n\n"


def discover_packs():
    """Return the available pack names in stable order."""
    return sorted(path.stem for path in PACKS_DIR.glob("*.md") if path.is_file())


def load_pack(name):
    """Return one named pack or raise KeyError for an unknown name."""
    path = PACKS_DIR / f"{name}.md"
    if name not in discover_packs():
        raise KeyError(name)
    return path.read_text(encoding="utf-8")


def compose_packs(names):
    """Return pack bodies in the requested order, preserving repetitions."""
    return SEPARATOR.join(load_pack(name) for name in names)


def build_parser():
    parser = argparse.ArgumentParser(description="Load Constraint Box MMM packs.")
    parser.add_argument("packs", nargs="+", help="pack names without .md")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    available = discover_packs()
    for name in args.packs:
        if name not in available:
            print(
                f"unknown pack: {name}; available packs: {', '.join(available)}",
                file=sys.stderr,
            )
            return 2

    texts = [load_pack(name) for name in args.packs]
    if args.as_json:
        json.dump({"packs": args.packs, "texts": texts}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(SEPARATOR.join(texts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
