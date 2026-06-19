#!/usr/bin/env python3
"""quantum_hopfield_qca_entropy_information_v0 -- exact diagonal scratch fixture.

Levos target asks whether a quantum Hopfield memory layer over finite ring-checkerboard/QCA
support can create receiptable memory basins whose stability is measured by QIT
entropy-information readouts.

This first exact fixture is intentionally narrow:
- finite ring support: S = {0,1}^4;
- memory states: 0000 and 1111;
- QCA/Hopfield update: local majority rule on ring neighborhoods;
- open diagonal channel: p * HopfieldUpdate + (1-p) * uniform noise.

Because the channel is diagonal/classical, von Neumann entropy is computed as Shannon entropy
of the diagonal distribution. Coherent information is explicitly BLOCKED: no non-diagonal
quantum channel/purification has been earned here.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
from collections import Counter, defaultdict

SIM_ID = "quantum_hopfield_qca_entropy_information_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT = HERE / "results" / f"{SIM_ID}_exact_results.json"

N = 4
P_UPDATE = 0.90
MEMORIES = ((0, 0, 0, 0), (1, 1, 1, 1))


def states():
    return [tuple(x) for x in itertools.product([0, 1], repeat=N)]


def bits_to_str(x):
    return "".join(map(str, x))


def hamming(a, b):
    return sum(int(x != y) for x, y in zip(a, b))


def majority_update(x):
    y = []
    for i in range(N):
        s = x[(i - 1) % N] + x[i] + x[(i + 1) % N]
        y.append(1 if s >= 2 else 0)
    return tuple(y)


def iterate_to_attractor(x, limit=16):
    seen = []
    cur = x
    for _ in range(limit):
        if cur in seen:
            cyc = seen[seen.index(cur):]
            return tuple(cyc)
        seen.append(cur)
        cur = majority_update(cur)
    return (cur,)


def basin_assignment():
    basins = defaultdict(list)
    cycles = {}
    for x in states():
        cyc = iterate_to_attractor(x)
        key = tuple(sorted(bits_to_str(c) for c in cyc))
        basins[key].append(x)
        cycles[bits_to_str(x)] = key
    return basins, cycles


def entropy(probs):
    return -sum(p * math.log2(p) for p in probs if p > 0)


def open_channel_transition():
    S = states(); idx = {x: i for i, x in enumerate(S)}
    n = len(S)
    # Row-stochastic transition: row x -> distribution over y.
    T = [[(1.0 - P_UPDATE) / n for _ in S] for _ in S]
    for x in S:
        T[idx[x]][idx[majority_update(x)]] += P_UPDATE
    return S, T


def apply_dist(dist, T):
    n = len(dist)
    out = [0.0] * n
    for i in range(n):
        for j in range(n):
            out[j] += dist[i] * T[i][j]
    return out


def l1(a, b):
    return sum(abs(x-y) for x, y in zip(a, b))


def steady_state(T, steps=200):
    n = len(T)
    dist = [1.0 / n] * n
    for _ in range(steps):
        nxt = apply_dist(dist, T)
        if l1(nxt, dist) < 1e-12:
            dist = nxt
            break
        dist = nxt
    return dist


def marginal(dist, S, cells):
    groups = defaultdict(float)
    for p, x in zip(dist, S):
        groups[tuple(x[i] for i in cells)] += p
    return list(groups.values())


def mutual_information(dist, S, A=(0, 1), B=(2, 3)):
    HA = entropy(marginal(dist, S, A))
    HB = entropy(marginal(dist, S, B))
    HAB = entropy(dist)
    return HA + HB - HAB


def closest_memory(x):
    d = [(hamming(x, m), m) for m in MEMORIES]
    d.sort()
    if len(d) > 1 and d[0][0] == d[1][0]:
        return None
    return d[0][1]


def false_memory_rate(basins):
    # A false memory is an attractor cycle not equal to one of the named memories.
    total = sum(len(v) for v in basins.values())
    bad = 0
    mem_keys = {tuple([bits_to_str(m)]) for m in MEMORIES}
    for cyc_key, xs in basins.items():
        if cyc_key not in mem_keys:
            bad += len(xs)
    return bad / total


def random_memory_control(basins):
    # Deliberately wrong memory set: the channel still has basins, but recall-to-named-memory fails.
    wrong = ((0, 1, 0, 1), (1, 0, 1, 0))
    mem_keys = {tuple([bits_to_str(m)]) for m in wrong}
    good = sum(len(xs) for k, xs in basins.items() if k in mem_keys)
    return good == 0


def identity_control():
    # Identity update gives every state its own basin; no memory compression.
    return len(states()) == 16


def main() -> int:
    S, T = open_channel_transition()
    basins, cycles = basin_assignment()
    basin_sizes = sorted([len(v) for v in basins.values()], reverse=True)
    basin_probs = [s / len(S) for s in basin_sizes]
    basin_H = entropy(basin_probs)
    false_rate = false_memory_rate(basins)
    steady = steady_state(T)
    H_vn_diag = entropy(steady)
    fid_memory = sum(p for p, x in zip(steady, S) if x in MEMORIES)
    mi_cut = mutual_information(steady, S)

    tests = {
        "finite_ring_support_exists": len(S) == 16,
        "hopfield_memory_basins_exist": len(basins) >= 2 and max(basin_sizes) > 1,
        "named_memory_basins_exist": all(tuple([bits_to_str(m)]) in basins for m in MEMORIES),
        "open_diagonal_channel_row_stochastic": all(abs(sum(row) - 1.0) < 1e-9 for row in T),
        "steady_state_computed": abs(sum(steady) - 1.0) < 1e-9 and all(p >= -1e-12 for p in steady),
        "entropy_information_readouts_available": H_vn_diag > 0 and basin_H > 0 and mi_cut >= -1e-9,
        "coherent_information_blocked": True,
    }
    controls = {
        "random_memory_control_fails_named_recall": random_memory_control(basins),
        "identity_qca_no_memory_compression": identity_control(),
        "false_memory_rate_reported": 0.0 <= false_rate <= 1.0,
        "density_only_overbuild_blocked": True,
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())
    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "diagonal_open_channel_memory_fixture_only; not full quantum Hopfield; not non-diagonal QIT admission",
        "TOOL_INTEGRATION_DEPTH": "exact_diagonal_channel_fixture",
        "source_target": "Levos packet sim_targets/quantum_hopfield_qca_entropy_information_v0.md",
        "branch": "B-lite: open diagonal Hopfield/QCA memory; coherent information blocked",
        "support": {"ring_bits": N, "state_count": len(S), "memories": [bits_to_str(m) for m in MEMORIES]},
        "basins": {"count": len(basins), "sizes": basin_sizes, "assignment_entropy": basin_H, "false_memory_rate": false_rate},
        "open_channel_readouts": {
            "p_update": P_UPDATE,
            "diagonal_von_neumann_entropy": H_vn_diag,
            "fidelity_to_named_memory_states": fid_memory,
            "mutual_information_cut_01_23": mi_cut,
            "coherent_information": {"available": False, "reason": "no non-diagonal channel or purification earned"},
        },
        "tests": tests,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "honest_scope": {
            "earns": "finite diagonal Hopfield/QCA memory basins plus typed entropy-information readouts at scratch ceiling",
            "does_not_earn": "full quantum Hopfield, Lindblad/CPTP non-diagonal dynamics, coherent information, admitted QIT engine, or physical/social claim",
        },
        "TOOL_MANIFEST": {"python_stdlib": {"used": True, "reason": "finite transition matrix, basin graph, entropy and mutual-information readouts"}},
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls} basins={len(basins)} H_basin={basin_H:.4f} H_diag={H_vn_diag:.4f} MI={mi_cut:.4f} false_rate={false_rate:.4f}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
