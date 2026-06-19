#!/usr/bin/env python3
"""Qubit-ladder depth gate for sim result packets.

CEILING (read this first): this gate recomputes NO math. It checks LADDER
DEPTH vs the VALIDITY CLAIM only: does the result carry per-rung evidence
across a ladder of Hilbert-space depths to a declared useful depth plus one
step beyond, IF and only if it claims validity?

An honest scratch_diagnostic / promotion_allowed=false sim that makes no
validity claim is permitted to be 1q-only. Pure-math naming only: new keys are
ladder/depth/check terms, not owner jargon.

This gate is a mechanical admission gate. It grants no status above the
depth-vs-claim check it performs, and it does not run git.

Usage:
    python3 scripts/validate_qubit_ladder_depth.py <result.json | sim_dir>
    python3 scripts/validate_qubit_ladder_depth.py --selftest

Output: JSON {"ok": bool, "sim": str, "ladder_depths_present": [int],
"useful_depth": int|null, "one_beyond_present": bool,
"claims_validity": bool, "violations": [{"kind": str, "detail": str}]}.
Exit code: 0 if clean, 1 if any violation, 2 on usage/read error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

NON_VALIDITY_CLASSIFICATIONS = frozenset(
    {"scratch_diagnostic", "tool_lego_fit_probe", "classical_baseline"}
)

LADDER_KEY_RE = re.compile(r"(ladder|rungs|qubit_rungs|by_qubit|by_depth|depths)", re.IGNORECASE)
USEFUL_DEPTH_KEY_RE = re.compile(r"(ladder_useful_depth|useful_depth)", re.IGNORECASE)
ONE_BEYOND_KEY_RE = re.compile(r"(ladder_one_beyond|one_beyond)", re.IGNORECASE)
QUBIT_COUNT_KEYS = frozenset({"qubits", "n_qubits", "depth", "q"})


class UsageError(Exception):
    """Input is missing, unreadable, or not a JSON result surface."""


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _truthy_claim_value(value: object) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return bool(value)


def _parse_depth_token(value: object) -> int | None:
    if _is_number(value) and int(value) == value and int(value) > 0:
        return int(value)
    if not isinstance(value, str):
        return None
    s = value.strip().lower()
    patterns = (
        r"^(\d+)$",
        r"^(\d+)\s*q$",
        r"^q\s*(\d+)$",
        r"^(?:depth|qubits?|n_qubits)[_\-\s:]*(\d+)$",
    )
    for pat in patterns:
        m = re.match(pat, s)
        if m:
            n = int(m.group(1))
            return n if n > 0 else None
    return None


def _has_numeric_observable(node: object) -> bool:
    """True when a rung carries a numeric computed observable.

    The qubit-count fields themselves do not count as observables; numbers
    elsewhere in the rung do.
    """
    if _is_number(node):
        return True
    if isinstance(node, list):
        return any(_has_numeric_observable(item) for item in node)
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key) in QUBIT_COUNT_KEYS:
                continue
            if _has_numeric_observable(value):
                return True
    return False


def _depth_from_rung(node: object) -> int | None:
    if not isinstance(node, dict):
        return None
    for key in QUBIT_COUNT_KEYS:
        if key in node:
            depth = _parse_depth_token(node[key])
            if depth is not None:
                return depth
    return None


def _collect_depths_from_ladder_container(node: object, depths: set[int]) -> None:
    if isinstance(node, dict):
        direct_depth = _depth_from_rung(node)
        if direct_depth is not None and _has_numeric_observable(node):
            depths.add(direct_depth)

        for key, value in node.items():
            keyed_depth = _parse_depth_token(key)
            if keyed_depth is not None and _has_numeric_observable(value):
                depths.add(keyed_depth)
            if isinstance(value, (dict, list)):
                _collect_depths_from_ladder_container(value, depths)
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, dict):
                item_depth = _depth_from_rung(item)
                if item_depth is not None and _has_numeric_observable(item):
                    depths.add(item_depth)
            if isinstance(item, (dict, list)):
                _collect_depths_from_ladder_container(item, depths)


def _walk_for_ladder_depths(node: object, depths: set[int]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if LADDER_KEY_RE.search(str(key)):
                _collect_depths_from_ladder_container(value, depths)
            _walk_for_ladder_depths(value, depths)
    elif isinstance(node, list):
        for item in node:
            _walk_for_ladder_depths(item, depths)


def _walk_for_useful_depths(node: object, useful_depths: list[int]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if USEFUL_DEPTH_KEY_RE.search(str(key)):
                depth = _parse_depth_token(value)
                if depth is not None:
                    useful_depths.append(depth)
            _walk_for_useful_depths(value, useful_depths)
    elif isinstance(node, list):
        for item in node:
            _walk_for_useful_depths(item, useful_depths)


def _walk_for_one_beyond_candidates(node: object, candidates: list[object]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if ONE_BEYOND_KEY_RE.search(str(key)):
                candidates.append(value)
            _walk_for_one_beyond_candidates(value, candidates)
    elif isinstance(node, list):
        for item in node:
            _walk_for_one_beyond_candidates(item, candidates)


def _candidate_names_or_carries_depth(node: object, target_depth: int) -> bool:
    depth = _parse_depth_token(node)
    if depth == target_depth:
        return True

    if isinstance(node, dict):
        direct_depth = _depth_from_rung(node)
        if direct_depth == target_depth and _has_numeric_observable(node):
            return True
        for key, value in node.items():
            keyed_depth = _parse_depth_token(key)
            if keyed_depth == target_depth and _has_numeric_observable(value):
                return True
            if _candidate_names_or_carries_depth(value, target_depth):
                return True
    elif isinstance(node, list):
        return any(_candidate_names_or_carries_depth(item, target_depth) for item in node)
    elif isinstance(node, str):
        return _parse_depth_token(node) == target_depth
    return False


def _claims_validity_in_node(node: object) -> bool:
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            if key_str == "classification" and isinstance(value, str):
                label = value.strip()
                if label and label not in NON_VALIDITY_CLASSIFICATIONS:
                    return True
            elif key_str in {"promotion_allowed", "formal_admission_allowed"} and value is True:
                return True
            elif key_str == "validity_claim" and _truthy_claim_value(value):
                return True
            elif key_str == "valid" and value is True:
                return True
            if _claims_validity_in_node(value):
                return True
    elif isinstance(node, list):
        return any(_claims_validity_in_node(item) for item in node)
    return False


def collect_result_files(target: Path) -> list[Path]:
    if target.is_file():
        if target.suffix.lower() != ".json":
            return []
        return [target]
    if target.is_dir():
        results_dir = target / "results"
        search_root = results_dir if results_dir.is_dir() else target
        return sorted(search_root.glob("*.json"))
    return []


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"unreadable JSON: {path}: {exc}") from exc


def _empty_report(sim: str, detail: str) -> dict:
    return {
        "ok": False,
        "sim": sim,
        "ladder_depths_present": [],
        "useful_depth": None,
        "one_beyond_present": False,
        "claims_validity": False,
        "violations": [{"kind": "usage_error", "detail": detail}],
    }


def run(target: Path) -> dict:
    files = collect_result_files(target)
    if not files:
        raise UsageError(f"no result JSON found: {target}")

    claims_validity = False
    ladder_depths: set[int] = set()
    useful_depths: list[int] = []
    one_beyond_candidates: list[object] = []

    for path in files:
        data = _load_json(path)
        claims_validity = claims_validity or _claims_validity_in_node(data)
        _walk_for_ladder_depths(data, ladder_depths)
        _walk_for_useful_depths(data, useful_depths)
        _walk_for_one_beyond_candidates(data, one_beyond_candidates)

    useful_depth = max(useful_depths) if useful_depths else None
    one_beyond_present = False
    if useful_depth is not None:
        one_beyond_depth = useful_depth + 1
        one_beyond_present = one_beyond_depth in ladder_depths or any(
            _candidate_names_or_carries_depth(candidate, one_beyond_depth)
            for candidate in one_beyond_candidates
        )

    sorted_depths = sorted(ladder_depths)
    violations: list[dict] = []
    if claims_validity:
        if not sorted_depths or sorted_depths == [1]:
            violations.append(
                {
                    "kind": "ladder_too_shallow",
                    "detail": (
                        "claims validity but carries only 1q evidence "
                        f"(ladder_depths_present={sorted_depths})"
                    ),
                }
            )
        if useful_depth is None:
            violations.append(
                {
                    "kind": "missing_useful_depth",
                    "detail": "claims validity but no ladder_useful_depth declared",
                }
            )
        elif useful_depth not in ladder_depths:
            violations.append(
                {
                    "kind": "useful_depth_no_evidence",
                    "detail": f"declared useful_depth={useful_depth} but no rung evidence at depth {useful_depth}",
                }
            )
        if useful_depth is not None and not one_beyond_present:
            violations.append(
                {
                    "kind": "missing_one_beyond",
                    "detail": f"useful_depth={useful_depth} but no depth-({useful_depth + 1}) one-beyond rung",
                }
            )

    return {
        "ok": len(violations) == 0,
        "sim": target.name,
        "ladder_depths_present": sorted_depths,
        "useful_depth": useful_depth,
        "one_beyond_present": one_beyond_present,
        "claims_validity": claims_validity,
        "violations": violations,
    }


def _write_result(tmp: Path, name: str, payload: dict) -> Path:
    sim_dir = tmp / name
    results_dir = sim_dir / "results"
    results_dir.mkdir(parents=True)
    (results_dir / f"{name}_results.json").write_text(json.dumps(payload), encoding="utf-8")
    return sim_dir


def _violation_kinds(report: dict) -> set[str]:
    return {str(v.get("kind")) for v in report.get("violations", [])}


def _selftest() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        scratch_1q = _write_result(
            tmp,
            "scratch_1q_only",
            {
                "classification": "scratch_diagnostic",
                "promotion_allowed": False,
                "probe_expectations_full": {"s0": [0.0, 0.0, 0.0]},
            },
        )
        report = run(scratch_1q)
        if not report["ok"] or report["claims_validity"]:
            failures.append("scratch 1q-only should pass without claiming validity")

        shallow_valid = _write_result(
            tmp,
            "shallow_valid",
            {
                "classification": "canonical",
                "qubit_rungs": {"1": {"observable": [0.0, 1.0]}},
            },
        )
        report = run(shallow_valid)
        if report["ok"] or "ladder_too_shallow" not in _violation_kinds(report):
            failures.append("1q-only validity claim should fail ladder_too_shallow")

        no_beyond = _write_result(
            tmp,
            "no_beyond",
            {
                "validity_claim": "candidate",
                "ladder_rungs": {
                    "1q": {"observable": [1.0]},
                    "2q": {"observable": [2.0]},
                    "3q": {"observable": [3.0]},
                },
                "ladder_useful_depth": 3,
            },
        )
        report = run(no_beyond)
        if report["ok"] or "missing_one_beyond" not in _violation_kinds(report):
            failures.append("useful depth without one-beyond should fail missing_one_beyond")

        full_ladder = _write_result(
            tmp,
            "full_ladder",
            {
                "classification": "valid",
                "rungs": [
                    {"qubits": 1, "observable": [1.0]},
                    {"qubits": 2, "observable": [2.0]},
                    {"qubits": 3, "observable": [3.0]},
                    {"qubits": 4, "observable": [4.0]},
                ],
                "ladder_useful_depth": 3,
                "ladder_one_beyond": 4,
            },
        )
        report = run(full_ladder)
        if not report["ok"] or report["ladder_depths_present"] != [1, 2, 3, 4]:
            failures.append("full ladder 1..4 useful 3 beyond 4 should pass")

        no_ladder = _write_result(tmp, "no_ladder", {"valid": True})
        report = run(no_ladder)
        if report["ok"] or "ladder_too_shallow" not in _violation_kinds(report):
            failures.append("valid:true without ladder should fail ladder_too_shallow")

        missing_useful = _write_result(
            tmp,
            "missing_useful",
            {
                "promotion_allowed": True,
                "by_qubit": {
                    "1": {"observable": [1.0]},
                    "2": {"observable": [2.0]},
                    "3": {"observable": [3.0]},
                },
            },
        )
        report = run(missing_useful)
        if report["ok"] or "missing_useful_depth" not in _violation_kinds(report):
            failures.append("validity claim without useful_depth should fail missing_useful_depth")

        useful_no_evidence = _write_result(
            tmp,
            "useful_no_evidence",
            {
                "classification": "canonical",
                "depths": {"q1": {"observable": [1.0]}, "q2": {"observable": [2.0]}},
                "useful_depth": 3,
            },
        )
        report = run(useful_no_evidence)
        if report["ok"] or "useful_depth_no_evidence" not in _violation_kinds(report):
            failures.append("declared useful depth with no rung evidence should fail")

        formal_full = _write_result(
            tmp,
            "formal_full",
            {
                "formal_admission_allowed": True,
                "by_depth": {
                    "1": {"observable": [1.0]},
                    "2": {"observable": [2.0]},
                    "3": {"observable": [3.0]},
                    "4": {"observable": [4.0]},
                    "5": {"observable": [5.0]},
                },
                "ladder_useful_depth": 4,
                "one_beyond": {"depth": 5, "sanity_observable": 5.0},
            },
        )
        report = run(formal_full)
        if not report["ok"] or not report["one_beyond_present"]:
            failures.append("formal admission full ladder 1..5 useful 4 beyond 5 should pass")

        scratch_with_ladder = _write_result(
            tmp,
            "scratch_with_ladder",
            {
                "classification": "scratch_diagnostic",
                "rungs": [
                    {"n_qubits": 1, "observable": [1.0]},
                    {"n_qubits": 2, "observable": [2.0]},
                    {"n_qubits": 3, "observable": [3.0]},
                    {"n_qubits": 4, "observable": [4.0]},
                ],
                "useful_depth": 3,
                "one_beyond": 4,
            },
        )
        report = run(scratch_with_ladder)
        if not report["ok"] or report["claims_validity"]:
            failures.append("scratch_diagnostic with full ladder should still pass as non-validity")

        tool_probe = _write_result(
            tmp,
            "tool_probe_1q",
            {
                "classification": "tool_lego_fit_probe",
                "by_qubit": {"1": {"observable": [1.0]}},
            },
        )
        report = run(tool_probe)
        if not report["ok"] or report["claims_validity"]:
            failures.append("tool_lego_fit_probe 1q-only should pass as non-validity")

        real_shape_anchor = _write_result(
            tmp,
            "distinguishability_quotient_floor_v0",
            {
                "classification": "scratch_diagnostic",
                "promotion_allowed": False,
                "formal_admission_allowed": False,
                "finite_set_size": 4,
                "state_labels": ["s0", "s1", "s2", "s3"],
                "probe_expectations_full": {
                    "s0": [0.0, 0.0, 0.0],
                    "s1": [0.5, 0.0, 0.3],
                    "s2": [0.5, 0.0, -0.3],
                    "s3": [0.0, 0.6, 0.0],
                },
            },
        )
        report = run(real_shape_anchor)
        if not report["ok"] or report["claims_validity"] or report["ladder_depths_present"]:
            failures.append("real-shape scratch anchor should pass as permitted scratch")

    if failures:
        print("SELFTEST FAILED")
        for failure in failures:
            print("  -", failure)
        return 1
    print("SELFTEST PASSED")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Qubit-ladder depth gate: enforce ladder depth only when a result claims validity."
    )
    p.add_argument("target", nargs="?", help="result-JSON path OR a sim dir (scans results/*.json).")
    p.add_argument("--selftest", action="store_true", help="run the built-in self-test and exit.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if not args.target:
        print(json.dumps(_empty_report("<none>", "provide a result JSON or sim dir"), indent=2))
        return 2
    target = Path(args.target)
    if not target.exists():
        print(json.dumps(_empty_report(str(target), f"not found: {target}"), indent=2))
        return 2
    try:
        report = run(target)
    except UsageError as exc:
        print(json.dumps(_empty_report(target.name, str(exc)), indent=2))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
