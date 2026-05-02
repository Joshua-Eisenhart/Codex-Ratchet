#!/usr/bin/env python3
"""Validate result JSONs as controller-admissible receipts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from receipt_schema import make_report, repo_root, validate_result_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Result JSON files to validate.")
    parser.add_argument(
        "--strict-scope",
        action="store_true",
        help="Require demotion_condition and out_of_scope fields as hard gates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    records = [
        validate_result_path(Path(path), root=root, strict_scope=args.strict_scope)
        for path in args.files
    ]
    report = make_report(records)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
