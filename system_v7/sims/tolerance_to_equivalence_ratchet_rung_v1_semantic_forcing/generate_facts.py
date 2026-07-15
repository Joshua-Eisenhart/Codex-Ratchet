#!/usr/bin/env python3
"""Deterministic fact-only instance generator; it never calls the oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random


def generate(seed: int, n: int) -> dict[str, object]:
    if n < 4 or n > 8:
        raise ValueError("n must be in the preregistered range 4..8")
    rng = random.Random(seed)
    # Generate T and E0 before demand. T is a disjoint union of independently
    # sampled local chains; E0 is the universal current presentation.
    cut = rng.randrange(1, n)
    tolerance_edges = [
        [index, index + 1]
        for start, stop in ((0, cut), (cut, n))
        for index in range(start, stop - 1)
    ]
    all_pairs = [(left, right) for left in range(n - 1) for right in range(left + 1, n)]
    demand_size = rng.randrange(0, min(len(all_pairs), n) + 1)
    demand_pairs = rng.sample(all_pairs, demand_size)
    demand = [
        {"pair": list(edge), "weight": rng.randrange(1, 6)}
        for edge in sorted(demand_pairs)
    ]
    return {
        "schema": "codex_ratchet.tolerance_to_equivalence_v1.instance.v1",
        "instance_id": f"seed-{seed}-n-{n}",
        "seed": seed,
        "n": n,
        "tolerance_edges": tolerance_edges,
        "current_labels": [0] * n,
        "demand": demand,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    payload = generate(args.seed, args.n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"instance_id": payload["instance_id"], "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
