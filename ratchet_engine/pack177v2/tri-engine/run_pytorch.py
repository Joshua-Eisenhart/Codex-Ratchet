#!/usr/bin/env python3
"""PyTorch execution of the frozen 256-map ANF census.  No NumPy."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import torch


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


def census(rows: list[tuple[int, int, int, int]]) -> list[int]:
    x = torch.tensor([[h0, h1, probe] for h0, h1, probe, _ in rows], dtype=torch.int64)
    outcome = torch.tensor([value for _, _, _, value in rows], dtype=torch.int64)
    monomials = torch.stack(
        (
            torch.ones((x.shape[0],), dtype=torch.int64),
            x[:, 0],
            x[:, 1],
            x[:, 2],
            x[:, 0] * x[:, 1],
            x[:, 0] * x[:, 2],
            x[:, 1] * x[:, 2],
            x[:, 0] * x[:, 1] * x[:, 2],
        ),
        dim=1,
    )
    selector = torch.tensor(
        [[(mask >> index) & 1 for index in range(8)] for mask in range(256)],
        dtype=torch.int64,
    )
    predicted = torch.remainder(selector @ monomials.T, 2)
    exact = torch.all(predicted == outcome.unsqueeze(0), dim=1)
    flags = [bool(value) for value in exact.tolist()]
    return [mask for mask, keep in enumerate(flags) if keep]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "receipts" / "normalized_source_tables.tsv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "tri-engine" / "results" / "pytorch_anf_census.tsv",
    )
    args = parser.parse_args()
    tables = load_tables(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["handle\texact_anf_masks"]
    for handle in sorted(tables):
        masks = census(tables[handle])
        lines.append(handle + "\t" + ",".join(str(mask) for mask in masks))
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS PyTorch ANF census {len(tables)} anonymous sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
