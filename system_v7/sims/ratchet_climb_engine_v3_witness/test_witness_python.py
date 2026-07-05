from __future__ import annotations

import importlib
import itertools
import random
import subprocess
from pathlib import Path


def partitions(items):
    if not items:
        yield []
        return
    head, *tail = items
    for rest in partitions(tail):
        yield [[head], *[cell[:] for cell in rest]]
        for index in range(len(rest)):
            copy = [cell[:] for cell in rest]
            copy[index] = [head, *copy[index]]
            yield copy


def normalized(q):
    return sorted([sorted(cell) for cell in q], key=lambda cell: (cell[0], len(cell), cell))


def all_partitions(n):
    return [normalized(q) for q in partitions(list(range(n)))]


def random_facts(n, seed):
    rng = random.Random(seed)
    one = [rng.randint(-3, 3) for _ in range(n)]
    two = [[rng.randint(-2, 2) for _ in range(n)] for _ in range(n)]
    return [{"values": one}, {"values": two}]


def constant_on_cells(q, n):
    one = [0] * n
    two = [[0] * n for _ in range(n)]
    for ci, cell in enumerate(q):
        for x in cell:
            one[x] = ci
            for y in range(n):
                two[x][y] = ci * 10
                two[y][x] = ci * 10
    return [{"values": one}, {"values": two}]


def brute(q, facts, tolerance=0.0):
    n = max(max(cell) for cell in q) + 1 if q else 0

    def profile(x):
        out = []
        for fact in facts:
            values = fact["values"] if isinstance(fact, dict) else fact
            if isinstance(values[0], list):
                out.extend(values[x])
                out.extend(row[x] for row in values)
            else:
                out.append(values[x])
        return out

    pairs = []
    for ci, cell in enumerate(q):
        for i, x in enumerate(cell):
            for y in cell[i + 1 :]:
                px, py = profile(x), profile(y)
                delta = max((abs(a - b) for a, b in zip(px, py)), default=0.0)
                if delta > tolerance:
                    pairs.append({"cell": ci, "pair": [x, y], "delta": float(delta)})
    return {"conflates": bool(pairs), "witness_pairs": pairs}


def pair_key(result):
    return [(hit["cell"], hit["pair"][0], hit["pair"][1]) for hit in result["witness_pairs"]]


def check_engine(name):
    module = importlib.import_module(name)
    positive = module.separation_witness([[0, 1], [2]], [{"values": [7, 8, 7]}])
    assert positive["conflates"]
    assert pair_key(positive) == [(0, 0, 1)]

    negative_q = [[0, 2], [1, 3]]
    negative = module.separation_witness(negative_q, constant_on_cells(negative_q, 4))
    assert not negative["conflates"]

    boundary_q = [[0, 1]]
    boundary_facts = [{"values": [1.0, 1.125]}]
    assert not module.separation_witness(boundary_q, boundary_facts, tolerance=0.125)["conflates"]
    assert module.separation_witness(boundary_q, boundary_facts, tolerance=0.124999)["conflates"]

    checked = {4: 0, 5: 0}
    for n in (4, 5):
        for qi, q in enumerate(all_partitions(n)):
            for seed in range(8):
                facts = random_facts(n, 1000 * n + 17 * qi + seed)
                expected = brute(q, facts)
                actual = module.separation_witness(q, facts)
                assert actual["conflates"] == expected["conflates"]
                assert pair_key(actual) == pair_key(expected)
                checked[n] += 1
    return checked


def main():
    np_counts = check_engine("separation_witness_numpy")
    jax_counts = check_engine("separation_witness_jax")
    assert np_counts == jax_counts
    here = Path(__file__).resolve().parent
    julia = subprocess.run(
        ["julia", str(here / "test_witness_julia.jl")],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "n4=120 n5=416" in julia.stdout
    print("python engines: n4=120 n5=416")
    print(julia.stdout.strip())


if __name__ == "__main__":
    main()
