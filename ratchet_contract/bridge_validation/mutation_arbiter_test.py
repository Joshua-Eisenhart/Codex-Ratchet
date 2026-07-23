#!/usr/bin/env python3
"""Mutation test proving the rival bridge agreement check can detect faults.

All mutations are applied only to source text compiled into distinctly named
in-memory modules.  The checked bridge files are never modified on disk.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import sys
import traceback
from pathlib import Path
from typing import Optional, Sequence

THIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_PATH = RESULTS_DIR / "mutation_arbiter_test.json"

_RATCHET_CONTRACT_DIR = THIS_DIR.parent
_FUEL_SIMS_DIR = _RATCHET_CONTRACT_DIR / "fuel_sims"
for _path in (THIS_DIR, _RATCHET_CONTRACT_DIR, _FUEL_SIMS_DIR):
    _path_string = str(_path)
    if _path_string not in sys.path:
        sys.path.insert(0, _path_string)

from bridge_interface import (  # noqa: E402
    Action,
    CandidateBridgeInterface,
    HistoryPointT,
    Outcome,
    Root,
    replay,
)
from run_rival_agreement import _build_cases  # noqa: E402


def _outcome_trace(
    candidate: CandidateBridgeInterface,
    point: HistoryPointT,
    word: tuple[Action, ...],
) -> tuple[Outcome, ...]:
    """Replay one continuation and retain every emitted outcome."""
    root: Root
    prefix: tuple[Action, ...]
    root, prefix = point
    state = replay(candidate, root, tuple(prefix))
    outcomes: list[Outcome] = []
    for action in word:
        state, outcome = candidate.step_C(state, action, None)
        outcomes.append(outcome)
    return tuple(outcomes)


def arbiter_indistinguishable(
    candidate: CandidateBridgeInterface,
    x: HistoryPointT,
    y: HistoryPointT,
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> bool:
    """Exhaustively decide the predictive quotient by full trace equality."""
    alphabet = tuple(candidate.action_alphabet() if action_alphabet is None else action_alphabet)
    if not alphabet:
        raise ValueError("action_alphabet is empty -- nothing to enumerate words with")
    for length in range(horizon + 1):
        for word in itertools.product(alphabet, repeat=length):
            if _outcome_trace(candidate, x, word) != _outcome_trace(candidate, y, word):
                return False
    return True


def arbiter_partition(
    candidate: CandidateBridgeInterface,
    X: Sequence[HistoryPointT],
    *,
    horizon: int,
    action_alphabet: Optional[Sequence[Action]] = None,
) -> tuple[int, ...]:
    """Pairwise arbiter partition, normalized by first appearance."""
    if not X:
        return ()
    alphabet = tuple(candidate.action_alphabet() if action_alphabet is None else action_alphabet)
    if not alphabet:
        raise ValueError("action_alphabet is empty -- nothing to enumerate words with")

    parent = list(range(len(X)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def join(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left in range(len(X)):
        for right in range(left + 1, len(X)):
            if arbiter_indistinguishable(candidate, X[left], X[right], horizon=horizon, action_alphabet=alphabet):
                join(left, right)

    label_for_root: dict[int, int] = {}
    labels: list[int] = []
    for index in range(len(X)):
        root = find(index)
        if root not in label_for_root:
            label_for_root[root] = len(label_for_root)
        labels.append(label_for_root[root])
    return tuple(labels)


def load_faulted_module(real_path: Path, module_name: str, patches: list[tuple[str, str]]):
    """Compile exactly patched source under a new sys.modules key only."""
    source = real_path.read_text(encoding="utf-8")
    applied = []
    for old, new in patches:
        count = source.count(old)
        if count != 1:
            raise RuntimeError(
                f"patch target not found exactly once in {real_path} "
                f"(found {count}): {old!r}"
            )
        source = source.replace(old, new, 1)
        applied.append({"old": old, "new": new})
    spec = importlib.util.spec_from_loader(module_name, loader=None, origin=str(real_path))
    if spec is None:
        raise RuntimeError(f"could not construct module spec for {real_path}")
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(real_path)
    sys.modules[module_name] = module
    exec(compile(source, f"{real_path} <faulted:{module_name}>", "exec"), module.__dict__)
    return module, applied


FAULTS = (
    {
        "bridge_faulted": "bridge_word_bfs",
        "fault": "depth_off_by_one",
        "path": THIS_DIR / "bridge_word_bfs.py",
        "module_name": "bridge_word_bfs__fault_depth_off_by_one",
        "patches": [("    for _depth in range(1, horizon + 1):", "    for _depth in range(1, horizon):")],
    },
    {
        "bridge_faulted": "bridge_word_bfs",
        "fault": "prefix_comparison_skipped",
        "path": THIS_DIR / "bridge_word_bfs.py",
        "module_name": "bridge_word_bfs__fault_prefix_comparison_skipped",
        "patches": [(
            "                if ox != oy:\n                    return new_word",
            "                if _depth == horizon and ox != oy:\n                    return new_word",
        )],
    },
    {
        "bridge_faulted": "bridge_action_predictive",
        "fault": "memo_poisoned",
        "path": THIS_DIR / "bridge_action_predictive.py",
        "module_name": "bridge_action_predictive__fault_memo_poisoned",
        "patches": [(
            "    state = replay(candidate, root, prefix, memo=memo)\n    _next_state, outcome = candidate.step_C(state, action, None)\n    return outcome",
            "    _poison_key = (\"POISONED\", root)\n    if _poison_key in memo:\n        state = memo[_poison_key]\n    else:\n        state = replay(candidate, root, prefix, memo=memo)\n        memo[_poison_key] = state\n    _next_state, outcome = candidate.step_C(state, action, None)\n    return outcome",
        )],
    },
    {
        "bridge_faulted": "bridge_action_predictive",
        "fault": "base_case_wrong",
        "path": THIS_DIR / "bridge_action_predictive.py",
        "module_name": "bridge_action_predictive__fault_base_case_wrong",
        "patches": [(
            "    if depth == 0:\n        sig_cache[key] = _BASE_SIGNATURE\n        return _BASE_SIGNATURE",
            "    if depth == 0:\n        sig = (\"LEAF\", prefix)\n        sig_cache[key] = sig\n        return sig",
        )],
    },
)


def _first_conflicting_pair(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, int]:
    for i in range(len(left)):
        for j in range(i + 1, len(left)):
            if (left[i] == left[j]) != (right[i] == right[j]):
                return i, j
    raise RuntimeError("different partitions had no pairwise conflict")


def run_mutation_arbiter_test() -> dict:
    import bridge_action_predictive
    import bridge_word_bfs

    cases = _build_cases()
    results = []
    for fault_spec in FAULTS:
        faulted_module, _applied = load_faulted_module(
            fault_spec["path"], fault_spec["module_name"], fault_spec["patches"]
        )
        faulted_word_bfs = fault_spec["bridge_faulted"] == "bridge_word_bfs"
        disagreements = []
        first_disagreement = None
        for case in cases:
            candidate, X = case["candidate"], case["X"]
            horizon, alphabet = case["horizon"], case["alphabet"]
            if faulted_word_bfs:
                pi_faulted = faulted_module.induce_word_bfs_partition(
                    candidate, X, horizon=horizon, action_alphabet=alphabet
                )
                pi_unfaulted = bridge_action_predictive.induce_action_predictive_partition(
                    candidate, X, horizon=horizon, action_alphabet=alphabet
                )
            else:
                pi_faulted = faulted_module.induce_action_predictive_partition(
                    candidate, X, horizon=horizon, action_alphabet=alphabet
                )
                pi_unfaulted = bridge_word_bfs.induce_word_bfs_partition(
                    candidate, X, horizon=horizon, action_alphabet=alphabet
                )
            if pi_faulted != pi_unfaulted:
                disagreements.append(case["case"])
                if first_disagreement is None:
                    first_disagreement = (case, pi_faulted, pi_unfaulted)

        arbiter_check = None
        if first_disagreement is not None:
            case, pi_faulted, pi_unfaulted = first_disagreement
            i, j = _first_conflicting_pair(pi_faulted, pi_unfaulted)
            verdict = arbiter_indistinguishable(
                case["candidate"], case["X"][i], case["X"][j],
                horizon=case["horizon"], action_alphabet=case["alphabet"],
            )
            faulted_says_same = pi_faulted[i] == pi_faulted[j]
            unfaulted_says_same = pi_unfaulted[i] == pi_unfaulted[j]
            arbiter_check = {
                "case": case["case"],
                "pair_indices": [i, j],
                "faulted_bridge_says_indistinguishable": faulted_says_same,
                "unfaulted_bridge_says_indistinguishable": unfaulted_says_same,
                "arbiter_verdict_indistinguishable": verdict,
                "arbiter_sided_with_unfaulted": verdict == unfaulted_says_same and verdict != faulted_says_same,
            }
        results.append({
            "bridge_faulted": fault_spec["bridge_faulted"],
            "fault": fault_spec["fault"],
            "disagreement_found": bool(disagreements),
            "disagreeing_cases": disagreements,
            "coverage_finding": not disagreements,
            "arbiter_check": arbiter_check,
        })

    sided_count = sum(
        row["arbiter_check"] is not None and row["arbiter_check"]["arbiter_sided_with_unfaulted"]
        for row in results
    )
    disagreement_count = sum(row["disagreement_found"] for row in results)
    coverage_findings = [row["fault"] for row in results if row["coverage_finding"]]
    return {
        "purpose": "Mutation-test the rival predictive-quotient bridges and independently arbitrate their first conflicting pair.",
        "scope": "practice/fuel development only -- promotion_allowed=false, formal_admission_allowed=false (matches bridge_validation/README.md's ceiling)",
        "cases_checked_per_fault": len(cases),
        "faults": results,
        "summary": {
            "total_faults": len(results),
            "faults_with_disagreement": disagreement_count,
            "faults_arbiter_sided_with_unfaulted": sided_count,
            "coverage_findings": coverage_findings,
            "cross_check_earned": disagreement_count == len(results) and sided_count == len(results),
            "ratio": f"{sided_count}/{len(results)}",
        },
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_mutation_arbiter_test()
    except Exception:
        RESULTS_PATH.write_text(
            json.dumps({"error": "mutation_arbiter_test raised", "traceback": traceback.format_exc()}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"exit_code": 1, "error": "mutation_arbiter_test raised -- see results/mutation_arbiter_test.json"}))
        return 1

    RESULTS_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases_checked": result["cases_checked_per_fault"],
        "faults": [
            {"fault": row["fault"], "disagreement_found": row["disagreement_found"]}
            for row in result["faults"]
        ],
        "cross_check_ratio": result["summary"]["ratio"],
        "results_path": str(RESULTS_PATH),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
