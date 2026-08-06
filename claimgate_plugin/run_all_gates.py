#!/usr/bin/env python3
"""Run the recorded ClaimGate gate suites through one aggregate entry point."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent

SUITES = (
    {
        "suite": "claimgate_plugin/run_bypass_regression.py",
        "expected": 0,
        "semantics": "12/12 blocked",
        "side_effects": (
            "appends claimgate_plugin/results/gate_ledger.jsonl; rewrites "
            "claimgate_plugin/results/gate_ledger.head.json; writes "
            "claimgate_plugin/results/bypass_regression_v1.json"
        ),
    },
    {
        "suite": "claimgate_plugin/run_typed_grammar_regression.py",
        "expected": 0,
        "semantics": "8/8",
        "side_effects": (
            "appends claimgate_plugin/results/gate_ledger.jsonl; rewrites "
            "claimgate_plugin/results/gate_ledger.head.json; writes "
            "claimgate_plugin/results/typed_grammar_regression_v1.json"
        ),
    },
    {
        "suite": "claimgate_plugin/run_bypass2_regression.py",
        "expected": 0,
        "semantics": "exit 0 = matched recorded; 6 bypass2 holes remain OPEN",
        "side_effects": (
            "appends claimgate_plugin/results/gate_ledger.jsonl; rewrites "
            "claimgate_plugin/results/gate_ledger.head.json; writes "
            "claimgate_plugin/fixtures/bypass2/bypass2_regression_v1.json"
        ),
    },
    {
        "suite": "claimgate_plugin/run_slop_regression.py",
        "expected": 0,
        "semantics": "recorded slop fixtures matched",
        "side_effects": "writes claimgate_plugin/results/slop_regression_v1.json",
    },
    {
        "suite": "claimgate_plugin/run_standing_regression.py",
        "expected": 0,
        "semantics": "recorded standing fixtures matched",
        "side_effects": "none",
    },
    {
        "suite": "claimgate_plugin/formal/chain_bmc_z3.py",
        "expected": 0,
        "semantics": "recorded Z3 chain properties matched",
        "side_effects": "writes claimgate_plugin/formal/results/chain_bmc_v0.json",
    },
    {
        "suite": "claimgate_plugin/formal/chain_bmc_cvc5.py",
        "expected": 0,
        "semantics": "recorded cvc5 chain properties matched",
        "side_effects": "writes claimgate_plugin/formal/results/chain_bmc_cvc5_v0.json",
    },
    {
        "suite": "claimgate_plugin/run_numpy_containment_regression.py",
        "expected": 1,
        "semantics": "RED-as-expected: 7 unmet clauses",
        "side_effects": (
            "appends claimgate_plugin/results/gate_ledger.jsonl; rewrites "
            "claimgate_plugin/results/gate_ledger.head.json; writes "
            "claimgate_plugin/results/numpy_containment_regression_v1.json"
        ),
    },
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreter used for every suite (default: this interpreter)",
    )
    parser.add_argument("--json", type=Path, help="write the aggregate report as JSON")
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the recorded expectation table without running suites",
    )
    return parser.parse_args(argv)


def display_expected(row: dict[str, Any]) -> str:
    expected = str(row["expected"])
    if row["expected"] == 1:
        return f"{expected} (RED)"
    return expected


def print_table(rows: list[dict[str, Any]]) -> None:
    headers = ("suite", "expected", "actual", "verdict", "side-effects", "seconds")
    rendered = []
    for row in rows:
        rendered.append(
            (
                row["suite"],
                display_expected(row),
                "-" if row.get("actual") is None else str(row["actual"]),
                row.get("verdict", "NOT RUN"),
                row["side_effects"],
                "-" if row.get("seconds") is None else f"{row['seconds']:.3f}",
            )
        )
    widths = [
        max(len(headers[index]), *(len(values[index]) for values in rendered))
        for index in range(len(headers))
    ]
    print(" | ".join(headers[index].ljust(widths[index]) for index in range(len(headers))))
    print("-|-".join("-" * width for width in widths))
    for row, values in zip(rows, rendered):
        print(" | ".join(values[index].ljust(widths[index]) for index in range(len(values))))
        semantics = row["semantics"]
        if semantics:
            print(f"  semantics: {semantics}")


def listed_rows() -> list[dict[str, Any]]:
    return [
        {
            **suite,
            "actual": None,
            "verdict": "NOT RUN",
            "seconds": None,
        }
        for suite in SUITES
    ]


def run_suites(python: str) -> list[dict[str, Any]]:
    rows = []
    for suite in SUITES:
        started = time.monotonic()
        proc = subprocess.run(
            [python, suite["suite"]],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        duration = time.monotonic() - started
        verdict = "MATCH" if proc.returncode == suite["expected"] else "DEVIATION"
        row = {
            **suite,
            "actual": proc.returncode,
            "verdict": verdict,
            "seconds": duration,
        }
        rows.append(row)
        if verdict == "MATCH":
            if suite["expected"] == 1:
                print(f"{suite['suite']}: MATCH — RED-as-expected (exit 1)")
            else:
                print(f"{suite['suite']}: MATCH (exit {proc.returncode})")
            if suite["suite"] == "claimgate_plugin/run_bypass2_regression.py":
                print(suite["semantics"])
        else:
            print(
                f"{suite['suite']}: DEVIATION "
                f"(expected {suite['expected']}, actual {proc.returncode})"
            )
            if suite["expected"] == 1 and proc.returncode == 0:
                print(
                    "EXPECTATION STALE: expected-red suite turned green; "
                    "the expectation must be updated in this file."
                )
            print(f"--- {suite['suite']} stdout ---")
            print(proc.stdout, end="" if proc.stdout.endswith("\n") or not proc.stdout else "\n")
            print(f"--- {suite['suite']} stderr ---")
            print(proc.stderr, end="" if proc.stderr.endswith("\n") or not proc.stderr else "\n")
    return rows


def report_payload(rows: list[dict[str, Any]], ran: bool) -> dict[str, Any]:
    deviations = [row["suite"] for row in rows if row["verdict"] == "DEVIATION"]
    return {
        "repo_root": str(REPO_ROOT),
        "ran": ran,
        "table": rows,
        "n_match": sum(row["verdict"] == "MATCH" for row in rows),
        "n_deviation": len(deviations),
        "deviating_suites": deviations,
    }


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    rows = listed_rows() if args.list else run_suites(args.python)
    print()
    print_table(rows)
    payload = report_payload(rows, ran=not args.list)
    print(f"\nn_match={payload['n_match']}")
    print(f"n_deviation={payload['n_deviation']}")
    print(f"deviating_suites={payload['deviating_suites']}")
    if args.json is not None:
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0 if args.list or payload["n_deviation"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
