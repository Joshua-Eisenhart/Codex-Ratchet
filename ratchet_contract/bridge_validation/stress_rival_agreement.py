#!/usr/bin/env python3
"""Adversarial pure-Python stress cases for the two bridge implementations.

This is a practice/fuel check only; it does not admit a carrier or ratchet
the axioms.  The toy machines live here so this campaign is independent of
the existing controls.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_PATH = RESULTS_DIR / "stress_rival_agreement.json"
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from bridge_interface import CandidateBridgeInterface, Outcome, history_point, hp_json  # noqa: E402
from bridge_action_predictive import (  # noqa: E402
    induce_action_predictive_partition,
    separating_witness,
)
from bridge_word_bfs import induce_word_bfs_partition  # noqa: E402


class OrderSensitiveCandidate(CandidateBridgeInterface):
    """First action is always an ack; the second action reveals order/state."""

    name = "stress_order_sensitive"

    def action_alphabet(self):
        return ("a", "b")

    def action_category(self, action):
        return "ordered_compose"

    def initial_state(self, root):
        return (str(root), ())

    def step_C(self, state, action, nest_context=None):
        root, seen = state
        if action not in self.action_alphabet():
            raise ValueError(action)
        if not seen:
            return (root, (action,)), Outcome.deterministic("ack")
        # The observable distinction is deliberately absent at depth one.
        order = seen[0] + action
        token = {"ab": "left", "ba": "right"}.get(order, "steady")
        return (root, seen + (action,)), Outcome.deterministic(token)


class HorizonBoundaryCandidate(CandidateBridgeInterface):
    name = "stress_horizon_boundary"

    def __init__(self, trigger_depth):
        self.trigger_depth = trigger_depth

    def action_alphabet(self):
        return ("probe", "other")

    def action_category(self, action):
        return "perturb"

    def initial_state(self, root):
        return (str(root), 0)

    def step_C(self, state, action, nest_context=None):
        root, depth = state
        if action not in self.action_alphabet():
            raise ValueError(action)
        token = "same"
        if depth + 1 == self.trigger_depth and action == "probe":
            token = "L" if root == "left" else "R"
        return (root, depth + 1), Outcome.deterministic(token)


class PrefixTrapCandidate(CandidateBridgeInterface):
    name = "stress_prefix_trap"

    def __init__(self, target):
        self.target = tuple(target)

    def action_alphabet(self):
        return ("a", "b")

    def action_category(self, action):
        return "ordered_compose"

    def initial_state(self, root):
        return (str(root), ())

    def step_C(self, state, action, nest_context=None):
        root, prefix = state
        next_prefix = prefix + (action,)
        # Every proper prefix, and every off-target word, is identical.
        if next_prefix == self.target:
            token = "L" if root == "left" else "R"
        else:
            token = "same"
        return (root, next_prefix), Outcome.deterministic(token)


class RelabeledCandidate(PrefixTrapCandidate):
    name = "stress_prefix_trap_relabeled"

    def step_C(self, state, action, nest_context=None):
        next_state, outcome = super().step_C(state, action, nest_context)
        mapping = {"same": "alpha", "L": "beta", "R": "gamma"}
        return next_state, Outcome.deterministic(mapping[outcome.tokens()[0]])


def _normalise(labels):
    seen = {}
    out = []
    for label in labels:
        if label not in seen:
            seen[label] = len(seen)
        out.append(seen[label])
    return tuple(out)


def _arbiter_partition(candidate, X, horizon, alphabet):
    # separating_witness is the arbiter because it exhaustively enumerates
    # every word up to horizon directly against the definition, independently
    # of both bridges' internal induction machinery.
    parent = list(range(len(X)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(len(X)):
        for j in range(i + 1, len(X)):
            if separating_witness(candidate, X[i], X[j], horizon=horizon, action_alphabet=alphabet) is None:
                union(i, j)
    return _normalise(find(i) for i in range(len(X)))


def _build_cases():
    cases = []
    order = OrderSensitiveCandidate()
    X_order = (history_point("left"), history_point("right"))
    cases += [
        {"case": "order_sensitive_ab_ba", "candidate": order, "X": X_order, "horizon": 2, "alphabet": None},
        {"case": "order_sensitive_ba_ab", "candidate": order, "X": X_order, "horizon": 3, "alphabet": ("b", "a")},
    ]
    for depth in (2, 3):
        cand = HorizonBoundaryCandidate(depth)
        X = (history_point("left"), history_point("right"))
        cases.append({"case": f"horizon_boundary_H{depth}", "candidate": cand, "X": X, "horizon": depth, "alphabet": None})
        cases.append({"case": f"horizon_boundary_H{depth}_minus_1", "candidate": cand, "X": X, "horizon": depth - 1, "alphabet": None})
    for target in (("a", "b"), ("a", "b", "a")):
        cand = PrefixTrapCandidate(target)
        cases.append({"case": f"prefix_trap_{len(target)}", "candidate": cand,
                      "X": (history_point("left"), history_point("right")), "horizon": len(target), "alphabet": None})
    relabel_target = ("a", "b")
    cases += [
        {"case": "permutation_original", "candidate": PrefixTrapCandidate(relabel_target),
         "X": (history_point("left"), history_point("right")), "horizon": 2, "alphabet": None},
        {"case": "permutation_relabeled", "candidate": RelabeledCandidate(relabel_target),
         "X": (history_point("left"), history_point("right")), "horizon": 2, "alphabet": None},
    ]
    return cases


def run_stress_rival_agreement():
    rows, divergences = [], []
    for spec in _build_cases():
        candidate, X, horizon = spec["candidate"], spec["X"], spec["horizon"]
        alphabet = tuple(spec["alphabet"] or candidate.action_alphabet())
        pi_ap = induce_action_predictive_partition(candidate, X, horizon=horizon, action_alphabet=alphabet)
        pi_bfs = induce_word_bfs_partition(candidate, X, horizon=horizon, action_alphabet=alphabet)
        agree = pi_ap == pi_bfs
        row = {"case": spec["case"], "candidate": candidate.name, "X": [hp_json(x) for x in X],
               "horizon": horizon, "action_alphabet": [repr(a) for a in alphabet],
               "pi_action_predictive": list(pi_ap), "pi_word_bfs": list(pi_bfs), "agree": agree}
        if not agree:
            truth = _arbiter_partition(candidate, X, horizon, alphabet)
            deviates = []
            if pi_ap != truth: deviates.append("pi_action_predictive")
            if pi_bfs != truth: deviates.append("pi_word_bfs")
            row.update({"arbiter_true_partition": list(truth), "which_bridge_deviates": deviates})
            divergences.append(dict(row))
        rows.append(row)
    return {
        "purpose": "adversarial stress cross-check of the two independent bridge partitions with order, exact-horizon, prefix-trap, and bijective token-relabel cases",
        "scope": "practice/fuel development only -- promotion_allowed=false, formal_admission_allowed=false; does NOT ratchet the axioms, does NOT admit any real carrier",
        "cases_checked": len(rows), "cases": rows, "all_agree": not divergences, "divergences": divergences,
    }


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_stress_rival_agreement()
        RESULTS_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except Exception:
        RESULTS_PATH.write_text(json.dumps({"error": "stress_rival_agreement raised", "traceback": traceback.format_exc()}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"exit_code": 1, "error": "stress_rival_agreement raised -- see results/stress_rival_agreement.json"}))
        return 1
    print(json.dumps({"cases_checked": result["cases_checked"], "all_agree": result["all_agree"],
                      "divergences_count": len(result["divergences"]), "results_path": str(RESULTS_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
