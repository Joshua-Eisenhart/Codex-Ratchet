"""Lean v9 command line. The previous wide CLI is `constraintbox-legacy`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core_tools import doctor, exercise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="constraintbox")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "exercise"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", dest="as_json")
    control_plane = commands.add_parser(
        "control-plane",
        help="run a bounded typed CB Light candidate-evaluation consumer",
    )
    control_plane.add_argument(
        "--request",
        type=Path,
        required=True,
        help="strict JSON control request",
    )
    control_plane.add_argument(
        "--db",
        type=Path,
        help=(
            "CB Light SQLite state database containing the selection triple; "
            "defaults to CB_LIGHT_STATE_DB or the contained Light state path"
        ),
    )
    control_plane.add_argument("--output", type=Path)
    cb_light = commands.add_parser(
        "cb-light",
        help="run the contained CB Light deterministic gate front door",
    )
    cb_light.add_argument(
        "gate_args",
        nargs=argparse.REMAINDER,
        help="arguments passed unchanged to cb-light-gate",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    # The gate owns its own option grammar (including a top-level ``--db``).
    # Dispatch before argparse sees those options, otherwise the outer parser
    # can reject them before the contained gate gets a chance to enforce them.
    if raw_args and raw_args[0] == "cb-light":
        from hookkernel.cb_light_gate import main as cb_light_main

        raise SystemExit(cb_light_main(raw_args[1:]))
    args = build_parser().parse_args(raw_args)
    if args.command == "control-plane":
        from .control_plane import run_candidate_evaluation_file
        from hookkernel.cb_light_state import default_db_path

        body = run_candidate_evaluation_file(
            args.request,
            db_path=args.db or default_db_path(),
        )
        rendered = json.dumps(body, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        if body["disposition"] != "CANDIDATE_EVALUATED_LOCAL":
            raise SystemExit(2)
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
