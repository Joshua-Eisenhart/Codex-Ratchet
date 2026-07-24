#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — exact settlement versus factor-graph VE.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: bounded classical factor-graph calibration — exact-vs-VE
agreement on small instances only; no 4^16 extrapolation licensed.

This is Experiment-B mini from the recovery audit: it asks whether a compact,
atemporal pairwise-factor representation settles the same finite Ising object
as direct enumeration, and records the elimination cost rather than treating
agreement as free.  The literal 4x4 grid has sixteen sites, so the grid row is
only defined at n=16; chain and tree rows cover n=8,12,16.

Exit 0 records completed checks (including a failed scientific check); exit 1
is reserved for infrastructure/API failure.
"""
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pgmpy
from pgmpy.factors.discrete import DiscreteFactor
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteMarkovNetwork

HERE = Path(__file__).resolve().parent
SIZES = (8, 12, 16)
TOL = 1e-10


def topology_edges(kind, n):
    if kind == "chain":
        return [(i, i + 1) for i in range(n - 1)]
    if kind == "tree":
        # Heap-indexed binary tree: non-path, still acyclic, deterministic.
        return [((i - 1) // 2, i) for i in range(1, n)]
    if kind == "grid_4x4":
        if n != 16:
            raise ValueError("literal 4x4 grid is defined only for n=16")
        return [(r * 4 + c, (r + 1) * 4 + c) for r in range(3) for c in range(4)] + [
            (r * 4 + c, r * 4 + c + 1) for r in range(4) for c in range(3)
        ]
    raise ValueError(kind)


def parameters(n, edges, seed):
    # Seeded random fields/couplings give reproducible random Ising instances.
    # Nonzero fields break spin-flip symmetry; strong positive couplings make a
    # deliberately reversed edge observable in the negative control.
    rng = np.random.default_rng(seed)
    fields = rng.uniform(-1.30, 1.30, size=n).tolist()
    couplings = {edge: float(rng.uniform(0.95, 1.35)) for edge in edges}
    return fields, couplings


def exact_settlement(n, edges, fields, couplings):
    weights = []
    states = []
    for bits in itertools.product((0, 1), repeat=n):
        spin = tuple(2 * bit - 1 for bit in bits)
        log_weight = sum(h * s for h, s in zip(fields, spin))
        log_weight += sum(couplings[e] * spin[e[0]] * spin[e[1]] for e in edges)
        states.append(bits)
        weights.append(math.exp(log_weight))
    z = math.fsum(weights)
    marginals = [math.fsum(w for b, w in zip(states, weights) if b[i]) / z for i in range(n)]
    return z, marginals


def min_fill_order(nodes, edges, keep):
    """Deterministic graph-only MinFill order used by pgmpy VE and proxy."""
    neighbors = {v: set() for v in nodes}
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    remaining = set(nodes) - {keep}
    order = []
    while remaining:
        def score(v):
            ns = neighbors[v] & remaining
            fill = sum(b not in neighbors[a] for a, b in itertools.combinations(sorted(ns), 2))
            return (fill, len(ns), v)
        v = min(remaining, key=score)
        ns = neighbors[v] & remaining
        for a, b in itertools.combinations(ns, 2):
            neighbors[a].add(b)
            neighbors[b].add(a)
        remaining.remove(v)
        order.append(v)
    return order


def peak_factor_scope(n, edges, keep):
    """Max variable scope formed by the same elimination graph/order."""
    neighbors = {v: set() for v in range(n)}
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    peak = 1  # unary factors are present
    for v in min_fill_order(range(n), edges, keep):
        scope = (neighbors[v] & set(range(n))) | {v}
        peak = max(peak, len(scope))
        ns = neighbors[v] & set(range(n))
        for a, b in itertools.combinations(ns, 2):
            neighbors[a].add(b)
            neighbors[b].add(a)
        for a in ns:
            neighbors[a].discard(v)
        neighbors[v].clear()
    return peak


def make_model(n, edges, fields, couplings):
    model = DiscreteMarkovNetwork()
    model.add_nodes_from(range(n))
    model.add_edges_from(edges)
    factors = [DiscreteFactor([i], [2], [math.exp(-h), math.exp(h)]) for i, h in enumerate(fields)]
    for edge in edges:
        j = couplings[edge]
        # state 0 -> spin -1, state 1 -> spin +1; row-major values.
        factors.append(DiscreteFactor(list(edge), [2, 2], [math.exp(j), math.exp(-j), math.exp(-j), math.exp(j)]))
    model.add_factors(*factors)
    return model


def ve_marginals(n, edges, fields, couplings):
    model = make_model(n, edges, fields, couplings)
    ve = VariableElimination(model)
    values, peak = [], 1
    started = time.perf_counter()
    for keep in range(n):
        order = min_fill_order(range(n), edges, keep)
        peak = max(peak, peak_factor_scope(n, edges, keep))
        factor = ve.query([keep], elimination_order=order, show_progress=False)
        vals = np.asarray(factor.values, dtype=float)
        values.append(float(vals[1] / vals.sum()))
    return values, time.perf_counter() - started, peak


def run_case(kind, n):
    edges = topology_edges(kind, n)
    topology_seed = {"chain": 11, "tree": 23, "grid_4x4": 37}[kind]
    seed = 10_000 * n + topology_seed
    fields, couplings = parameters(n, edges, seed)
    t0 = time.perf_counter()
    z, exact = exact_settlement(n, edges, fields, couplings)
    exact_seconds = time.perf_counter() - t0
    ve_vals, ve_seconds, peak = ve_marginals(n, edges, fields, couplings)
    max_div = max(abs(a - b) for a, b in zip(exact, ve_vals))

    # Negative control: reverse one deliberately strong edge. The comparison is
    # still against the original exact object, so agreement cannot be vacuous.
    wrong = dict(couplings)
    # Fixed first edge makes the intentionally wrong model reproducible rather
    # than selecting a favorable result after observing the marginals.
    flipped_edge = edges[0]
    wrong[flipped_edge] *= -1.0
    wrong_vals, wrong_seconds, _ = ve_marginals(n, edges, fields, wrong)
    wrong_div = max(abs(a - b) for a, b in zip(exact, wrong_vals))
    return {
        "topology": kind, "n_variables": n, "random_seed": seed, "n_pairwise_factors": len(edges),
        "partition_function_exact": z, "exact_enumeration_seconds": exact_seconds,
        "ve_all_single_site_marginals_seconds": ve_seconds,
        "ve_wrong_factor_seconds": wrong_seconds,
        "peak_factor_scope_variables": peak, "peak_factor_table_entries_proxy": 2 ** peak,
        "exact_vs_ve_max_abs_divergence": max_div, "exact_vs_ve_match_1e-10": max_div <= TOL,
        "wrong_factor_flipped_edge": list(flipped_edge),
        "wrong_factor_vs_original_exact_max_abs_divergence": wrong_div,
        "wrong_factor_diverges_gt_0_1": wrong_div > 0.1,
    }


def main():
    started = time.perf_counter()
    rows = [run_case(kind, n) for kind in ("chain", "tree") for n in SIZES]
    rows.append(run_case("grid_4x4", 16))
    by_key = {(r["topology"], r["n_variables"]): r for r in rows}
    chain_16 = by_key[("chain", 16)]
    grid_16 = by_key[("grid_4x4", 16)]
    timing_control = grid_16["ve_all_single_site_marginals_seconds"] >= chain_16["ve_all_single_site_marginals_seconds"]
    all_match = all(row["exact_vs_ve_match_1e-10"] for row in rows)
    wrong_control = all(row["wrong_factor_diverges_gt_0_1"] for row in rows)
    all_pass = all_match and wrong_control and timing_control
    receipt = {
        "classification": "unofficial_stress_probe", "promotion_allowed": False,
        "claim_ceiling": "bounded classical factor-graph calibration — exact-vs-VE agreement on small instances only; no 4^16 extrapolation licensed",
        "pgmpy_version": getattr(pgmpy, "__version__", "unknown"),
        "model_api": "pgmpy.models.DiscreteMarkovNetwork (available in installed pgmpy)",
        "method": {"exact": "2^n brute-force Ising enumeration", "ve": "pgmpy VariableElimination with deterministic graph-only MinFill orders; output normalized explicitly", "peak_treewidth_proxy": "maximum factor variable scope during the corresponding elimination, reported also as binary table entries"},
        "scope_deviation": "A literal 4x4 grid has n=16 only; n=8 and n=12 rows are chain/tree only. The grid-vs-chain timing control is therefore at n=16.",
        "cases": rows,
        "negative_controls": {"grid_16_ve_seconds": grid_16["ve_all_single_site_marginals_seconds"], "chain_16_ve_seconds": chain_16["ve_all_single_site_marginals_seconds"], "grid_slower_or_equal_than_chain_at_n16": timing_control, "all_wrong_factors_diverge_gt_0_1": wrong_control},
        "agreement": {"tolerance": TOL, "all_exact_vs_ve_match": all_match},
        "all_pass": all_pass, "seconds": time.perf_counter() - started,
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    path = out / "factor_graph_settlement_probe.json"
    with path.open("w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps({"agreement": receipt["agreement"], "negative_controls": receipt["negative_controls"], "all_pass": all_pass}, indent=1))
    print(f"[*] factor-graph settlement probe COMPLETED — checks {'ALL HOLD' if all_pass else 'FAIL (recorded)'}; receipt: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
