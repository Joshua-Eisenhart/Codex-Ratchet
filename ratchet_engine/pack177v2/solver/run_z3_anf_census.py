#!/usr/bin/env python3
"""Z3 enumeration of all exact ANF coefficient models for each source."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from z3 import Bool, BoolVal, Not, Or, Solver, Xor, is_true, sat


ROOT = Path(__file__).resolve().parents[1]


def load_tables(path: Path) -> dict[str, list[tuple[int, int, int, int]]]:
    tables: dict[str, list[tuple[int, int, int, int]]] = defaultdict(list)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "handle\th0\th1\tp\to":
        raise ValueError("unexpected normalized table header")
    for line in lines[1:]:
        handle, h0, h1, probe, outcome = line.split("\t")
        tables[handle].append((int(h0), int(h1), int(probe), int(outcome)))
    return dict(tables)


def enumerate_models(rows: list[tuple[int, int, int, int]]) -> list[int]:
    coefficients = [Bool(f"c{index}") for index in range(8)]
    solver = Solver()
    for h0, h1, probe, outcome in rows:
        values = (1, h0, h1, probe, h0*h1, h0*probe, h1*probe, h0*h1*probe)
        active = [coefficients[index] for index, value in enumerate(values) if value == 1]
        expression = Xor(*active) if len(active) > 1 else active[0] if active else BoolVal(False)
        solver.add(expression if outcome == 1 else Not(expression))
    masks: list[int] = []
    while solver.check() == sat:
        model = solver.model()
        bits = [is_true(model.eval(item, model_completion=True)) for item in coefficients]
        mask = sum((1 << index) for index, value in enumerate(bits) if value)
        masks.append(mask)
        solver.add(Or(*[item != BoolVal(value) for item, value in zip(coefficients, bits, strict=True)]))
    return sorted(masks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "receipts" / "normalized_source_tables.tsv")
    parser.add_argument("--expected", type=Path, default=ROOT / "receipts" / "r6_full_recompute.json")
    parser.add_argument("--output", type=Path, default=ROOT / "solver" / "results" / "z3_anf_census.json")
    args = parser.parse_args()
    tables = load_tables(args.input)
    expected_receipt = json.loads(args.expected.read_text(encoding="utf-8"))
    expected = {
        row["handle"]: row["full_recompute"]["anf_exact_survivor_masks"]
        for row in expected_receipt["sources"]
    }
    observed = {handle: enumerate_models(tables[handle]) for handle in sorted(tables)}
    passed = observed == expected
    receipt = {
        "schema_version": "ratchet.z3-anf-census/0.1",
        "source_count": len(observed),
        "observed_models": observed,
        "matches_exact_enumeration": passed,
        "all_pass": passed,
        "status": "PASS" if passed else "HOLD_Z3_DISAGREEMENT",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
