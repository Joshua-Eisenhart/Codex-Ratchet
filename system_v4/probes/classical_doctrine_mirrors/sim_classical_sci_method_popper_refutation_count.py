"""Classical baseline: Popperian refutation count (science method).

Mirrors the science-method framework: hypotheses are admissible only until
refuted. Given a dataset and a family of threshold hypotheses H_t: "all x > t",
we count how many are refuted by at least one counterexample. Survivor count
should decrease monotonically as threshold widens.

scope_note: classical_baseline mirror of scientific-method framework
(OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md, Popper/empiricism doctrine).
"""
import numpy as np
from _common import write_results


def refuted(data, t):
    return bool(np.any(data <= t))


def survivor_thresholds(data, ts):
    return [t for t in ts if not refuted(data, t)]


def run_positive():
    rng = np.random.RandomState(0)
    data = rng.uniform(5, 10, size=200)
    ts = np.linspace(0, 10, 11)
    refuted_count = sum(int(refuted(data, t)) for t in ts)
    survivors = survivor_thresholds(data, ts)
    # Every t >= min(data) is refuted; every t < min(data) survives.
    mn = float(data.min())
    expected_refuted = int(np.sum(ts >= mn))
    return {
        "refuted_count": {"count": refuted_count, "expected": expected_refuted, "pass": refuted_count == expected_refuted},
        "survivors_monotone": {"pass": bool(all(survivors[i] <= survivors[i + 1] for i in range(len(survivors) - 1)))},
    }


def run_negative():
    # A hypothesis refuted by the data must NOT be in survivors.
    data = np.array([1.0, 2.0, 3.0])
    ts = [0.5, 2.5]
    surv = survivor_thresholds(data, ts)
    return {"refuted_excluded": {"survivors": surv, "pass": 2.5 not in surv}}


def run_boundary():
    # Empty dataset: no refutations possible (vacuous survival).
    data = np.array([])
    t = 5.0
    return {"empty_data_vacuous": {"refuted": refuted(data, t), "pass": not refuted(data, t)}}


if __name__ == "__main__":
    write_results(
        "sim_classical_sci_method_popper_refutation_count",
        "classical_baseline mirror of Popperian refutation (OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md science-method framework)",
        run_positive(), run_negative(), run_boundary(),
        "sim_classical_sci_method_popper_refutation_count_results.json",
    )
