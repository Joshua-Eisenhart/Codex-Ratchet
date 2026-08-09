"""Lean v9 command line. The previous wide CLI is `constraintbox-legacy`."""

from __future__ import annotations

import argparse
import json

from .core_tools import doctor, exercise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="constraintbox")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "exercise"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    body = doctor() if args.command == "doctor" else exercise()
    if args.as_json:
        print(json.dumps(body, indent=2, sort_keys=True))
    else:
        if args.command == "doctor":
            print("ConstraintBox core tools")
            for row in body["rows"]:
                state = "visible" if row["import_visible"] else "missing"
                print(f"- {row['id']}: {state} ({row['version'] or 'no distribution version'})")
        else:
            print(f"ConstraintBox exercised {len(body['observations'])} core tools")
            print(f"observation_sha256={body['observation_sha256']}")


if __name__ == "__main__":
    main()
