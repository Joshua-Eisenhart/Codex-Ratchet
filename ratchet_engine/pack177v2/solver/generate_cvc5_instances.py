#!/usr/bin/env python3
"""Generate one finite SMT-LIB ANF satisfiability instance per source."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_tables(path: Path) -> dict[str, list[tuple[int, int, int, int]]]:
    tables: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    for ordinal, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if ordinal == 0:
            if line != "handle\th0\th1\tp\to":
                raise ValueError("unexpected normalized table header")
            continue
        handle, h0, h1, probe, outcome = line.split("\t")
        tables[handle].append((int(h0), int(h1), int(probe), int(outcome)))
    return dict(tables)


def xor_expression(active: list[str]) -> str:
    if not active:
        return "false"
    if len(active) == 1:
        return active[0]
    current = f"(xor {active[0]} {active[1]})"
    for token in active[2:]:
        current = f"(xor {current} {token})"
    return current


def instance(rows: list[tuple[int, int, int, int]]) -> str:
    lines = ["(set-logic QF_UF)"]
    lines.extend(f"(declare-const c{index} Bool)" for index in range(8))
    for h0, h1, probe, outcome in rows:
        values = (1, h0, h1, probe, h0*h1, h0*probe, h1*probe, h0*h1*probe)
        expression = xor_expression([f"c{index}" for index, value in enumerate(values) if value])
        lines.append(f"(assert {expression})" if outcome else f"(assert (not {expression}))")
    lines.append("(check-sat)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "receipts" / "normalized_source_tables.tsv")
    parser.add_argument("--expected", type=Path, default=ROOT / "receipts" / "r6_full_recompute.json")
    parser.add_argument("--output-directory", type=Path, default=ROOT / "solver" / "cvc5_instances")
    parser.add_argument("--manifest", type=Path, default=ROOT / "solver" / "cvc5_manifest.json")
    args = parser.parse_args()
    tables = load_tables(args.input)
    expected_receipt = json.loads(args.expected.read_text(encoding="utf-8"))
    expected = {
        row["handle"]: bool(row["full_recompute"]["anf_exact_survivor_masks"])
        for row in expected_receipt["sources"]
    }
    args.output_directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for handle in sorted(tables):
        path = args.output_directory / f"{handle}.smt2"
        path.write_text(instance(tables[handle]), encoding="utf-8")
        rows.append(
            {
                "handle": handle,
                "path": str(path.relative_to(ROOT)),
                "expected": "sat" if expected[handle] else "unsat",
            }
        )
    args.manifest.write_text(
        json.dumps(
            {
                "schema_version": "ratchet.cvc5-anf-manifest/0.1",
                "instances": rows,
                "execution_status": "UNRUN_UNTIL_CVC5_RUNTIME_AVAILABLE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"generated {len(rows)} cvc5 instances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
