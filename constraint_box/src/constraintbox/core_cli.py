"""Lean v9 command line. The previous wide CLI is `constraintbox-legacy`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core_tools import doctor, exercise
from .gate import GateError, GATE_EXIT_CODES, run_gate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="constraintbox")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "exercise"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", dest="as_json")
    gate = commands.add_parser("gate", help="run the ClaimGate receipt entrypoint")
    gate.add_argument("receipt", type=Path, nargs="?")
    gate.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "gate":
        if args.receipt is None:
            build_parser().error("the following arguments are required: receipt")
        try:
            body = run_gate(args.receipt)
            exit_code = GATE_EXIT_CODES[body["disposition"]]
        except GateError as exc:
            body = {"error": str(exc)}
            exit_code = 2
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if exit_code:
            raise SystemExit(exit_code)
        return

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
