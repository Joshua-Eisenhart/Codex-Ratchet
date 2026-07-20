#!/usr/bin/env python3
"""Compare independently emitted JAX, PyTorch, and Julia census tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_tsv(path: Path) -> dict[str, list[int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "handle\texact_anf_masks":
        raise ValueError(f"unexpected header in {path}")
    result: dict[str, list[int]] = {}
    for line in lines[1:]:
        handle, raw = line.split("\t", 1)
        result[handle] = [] if raw == "" else [int(value) for value in raw.split(",")]
    return result


def expected(path: Path) -> dict[str, list[int]]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    return {
        row["handle"]: row["full_recompute"]["anf_exact_survivor_masks"]
        for row in receipt["sources"]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=Path, default=ROOT / "receipts" / "r6_full_recompute.json")
    parser.add_argument("--jax", type=Path, default=ROOT / "tri-engine" / "results" / "jax_anf_census.tsv")
    parser.add_argument("--pytorch", type=Path, default=ROOT / "tri-engine" / "results" / "pytorch_anf_census.tsv")
    parser.add_argument("--julia", type=Path, default=ROOT / "tri-engine" / "results" / "julia_anf_census.tsv")
    parser.add_argument("--output", type=Path, default=ROOT / "tri-engine" / "results" / "agreement_receipt.json")
    args = parser.parse_args()
    reference = expected(args.expected)
    engines = {
        "jax": read_tsv(args.jax),
        "pytorch": read_tsv(args.pytorch),
        "julia": read_tsv(args.julia),
    }
    comparisons = {
        name: {
            "source_handles_match": set(table) == set(reference),
            "exact_masks_match": table == reference,
        }
        for name, table in engines.items()
    }
    passed = all(
        item["source_handles_match"] and item["exact_masks_match"]
        for item in comparisons.values()
    )
    receipt = {
        "schema_version": "ratchet.tri-engine-anf-agreement/0.1",
        "source_count": len(reference),
        "engines": comparisons,
        "all_pass": passed,
        "numpy_used": False,
        "status": "PASS" if passed else "HOLD_ENGINE_DISAGREEMENT",
        "claim_ceiling": "port fidelity for the exact finite ANF census only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
