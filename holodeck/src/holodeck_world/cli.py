from __future__ import annotations

import argparse
import json

from .doctor import report


def main() -> None:
    parser = argparse.ArgumentParser(prog="holodeck")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor = commands.add_parser("doctor")
    doctor.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    body = report()
    if args.as_json:
        print(json.dumps(body, indent=2, sort_keys=True))
    else:
        visible = sum(row["live_import_visible"] for row in body["tool_rows"])
        print(f"Holodeck tool visibility: {visible}/{len(body['tool_rows'])}")
        print(f"QIT bridge: {body['qit_bridge_state']}")


if __name__ == "__main__":
    main()
