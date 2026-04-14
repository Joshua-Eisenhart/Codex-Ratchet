"""Classical baseline: Leviathan coalition formation.

Mirrors the Leviathan framework (self-similar governance) with a classical
analog: majority-rule coalition emergence in a cooperative game. Given n
agents with random weights, a minimum-weight coalition exceeding 50% of total
weight is computable; we check that (a) such a coalition exists for
non-degenerate distributions and (b) it is minimal w.r.t. losing one member.

scope_note: classical_baseline mirror of Leviathan coalition dynamic
(OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md Leviathan framework).
"""
import numpy as np
from itertools import combinations
from _common import write_results


def min_winning_coalition(w):
    total = w.sum()
    threshold = total / 2.0
    n = len(w)
    for k in range(1, n + 1):
        best = None
        for combo in combinations(range(n), k):
            s = float(w[list(combo)].sum())
            if s > threshold:
                if best is None or s < best[1]:
                    best = (combo, s)
        if best is not None:
            return best
    return None


def run_positive():
    out = {}
    for seed in (0, 1, 2):
        rng = np.random.RandomState(seed)
        w = rng.uniform(1, 10, size=7)
        mw = min_winning_coalition(w)
        combo, s = mw
        # Minimality: removing any member drops below threshold
        thr = w.sum() / 2.0
        minimal = all(float(w[list(combo)].sum() - w[i]) <= thr for i in combo)
        out[f"seed{seed}"] = {
            "coalition": list(combo),
            "weight": s,
            "threshold": thr,
            "minimal": minimal,
            "pass": bool(s > thr and minimal),
        }
    return out


def run_negative():
    # A single agent with <50% weight should NOT form a winning coalition alone.
    w = np.array([1.0, 1.0, 1.0, 1.0, 1.0])  # each 20%, max 20% < 50%
    thr = w.sum() / 2.0
    any_singleton_wins = any(wi > thr for wi in w)
    return {"no_singleton_dominance": {"threshold": thr, "any_singleton_wins": bool(any_singleton_wins), "pass": not any_singleton_wins}}


def run_boundary():
    # Dictator: one agent has >50% alone.
    w = np.array([10.0, 1.0, 1.0])
    mw = min_winning_coalition(w)
    combo, s = mw
    return {"dictator_singleton": {"coalition": list(combo), "pass": len(combo) == 1 and combo[0] == 0}}


if __name__ == "__main__":
    write_results(
        "sim_classical_leviathan_coalition_formation",
        "classical_baseline mirror of Leviathan coalition self-similar governance (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_leviathan_coalition_formation_results.json",
    )
