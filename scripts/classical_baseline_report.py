#!/usr/bin/env python3
"""Classical baseline aggregator.

Crawls system_v4/probes/a2_state/sim_results/*_classical*_results.json and
emits a markdown boundary-failure matrix.

Columns: lego | runs | all_pass | divergence_log summary | innate_failure

innate_failure = True iff any negative test whose name matches
    *misses* / *breaks* / *not_preserved*  passed (pass=True).

Output: markdown to stdout.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

RESULTS_GLOB = (
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/"
    "system_v4/probes/a2_state/sim_results/*_classical*_results.json"
)

INNATE_PAT = re.compile(r"(misses|breaks|not_preserved)", re.IGNORECASE)


SECTION_KEYS = ("positive", "negative", "boundary", "comparison", "tests")


def _truthy_pass(v):
    """Extract a pass flag from heterogeneous value shapes."""
    if isinstance(v, bool):
        return v
    if isinstance(v, dict):
        for k in ("pass", "passed", "ok"):
            if isinstance(v.get(k), bool):
                return v[k]
        st = v.get("status")
        if isinstance(st, str) and st.lower() in ("pass", "passed", "ok"):
            return True
        if isinstance(st, str) and st.lower() in ("fail", "failed", "error"):
            return False
    return None


def _collect_tests(obj, parent_key=None):
    """Yield (name, pass_flag) pairs from nested dict/list.

    Handles these shapes:
      - {"positive": {"testname": bool}}
      - {"positive": {"testname": {"pass": bool, ...}}}
      - {"tests": [{"name": "...", "passed": bool}, ...]}
      - {"name": "...", "pass": bool}
    """
    if isinstance(obj, dict):
        # Named test object at this level
        name = obj.get("name") or obj.get("test") or obj.get("label")
        passed = _truthy_pass(obj)
        if name is not None and isinstance(passed, bool):
            yield str(name), passed
        # Section-dict pattern: iterate entries treating keys as names
        for k, v in obj.items():
            if k in ("name", "test", "label", "pass", "passed", "ok", "status"):
                continue
            if k in SECTION_KEYS and isinstance(v, dict):
                for tk, tv in v.items():
                    tp = _truthy_pass(tv)
                    if isinstance(tp, bool):
                        yield str(tk), tp
                    if isinstance(tv, (dict, list)):
                        yield from _collect_tests(tv, parent_key=tk)
            elif k in SECTION_KEYS and isinstance(v, list):
                yield from _collect_tests(v, parent_key=k)
            else:
                # Fall through — also try key-as-name / value-as-pass
                tp = _truthy_pass(v)
                if isinstance(tp, bool) and parent_key is None:
                    # Only at root if key itself resembles a test name
                    pass
                if isinstance(v, (dict, list)):
                    yield from _collect_tests(v, parent_key=k)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, dict):
                tp = _truthy_pass(v)
                nm = v.get("name") or v.get("test") or v.get("label") or parent_key
                if nm is not None and isinstance(tp, bool):
                    yield str(nm), tp
            yield from _collect_tests(v, parent_key=parent_key)


def _divergence_summary(data):
    dl = data.get("divergence_log")
    if dl is None:
        for key in ("divergence", "divergences", "boundary_divergence"):
            if key in data:
                dl = data[key]
                break
    if dl is None:
        return "-"
    s = json.dumps(dl, default=str) if not isinstance(dl, str) else dl
    s = s.replace("\n", " ").strip()
    return (s[:80] + "...") if len(s) > 80 else s


def _all_pass(data):
    for key in ("all_pass", "overall_pass"):
        if key in data and isinstance(data[key], bool):
            return data[key]
    summ = data.get("summary") or {}
    if isinstance(summ, dict) and isinstance(summ.get("all_pass"), bool):
        return summ["all_pass"]
    return None


def _runs(data):
    for key in ("total_count", "runs", "num_tests", "n_runs"):
        v = data.get(key)
        if isinstance(v, int):
            return v
    tests = list(_collect_tests(data))
    return len(tests) if tests else 0


def main():
    paths = sorted(glob.glob(RESULTS_GLOB))
    rows = []
    innate_count = 0
    for p in paths:
        try:
            data = json.load(open(p))
        except Exception as e:
            rows.append((Path(p).stem, 0, f"READ_ERR:{e}", "-", False))
            continue
        lego = Path(p).stem.replace("_classical_results", "").replace("_results", "")
        runs = _runs(data)
        ap = _all_pass(data)
        div = _divergence_summary(data)
        innate = False
        # Signal 1: explicit innately_missing field populated
        im = data.get("innately_missing")
        if isinstance(im, str) and im.strip() and im.strip().lower() not in ("none", "null", "-"):
            innate = True
        elif isinstance(im, (list, dict)) and im:
            innate = True
        # Signal 2: any negative-style test whose name matches the pattern and passed
        if not innate:
            for name, passed in _collect_tests(data):
                if INNATE_PAT.search(name) and passed:
                    innate = True
                    break
        if innate:
            innate_count += 1
        rows.append((lego, runs, ap, div, innate))

    print("# Classical Baseline Boundary-Failure Matrix\n")
    print(f"Total sims crawled: {len(rows)}  |  innate_failure=True: {innate_count}\n")
    print("| lego | runs | all_pass | divergence_log | innate_failure |")
    print("|---|---|---|---|---|")
    for lego, runs, ap, div, innate in rows:
        ap_s = "-" if ap is None else str(ap)
        print(f"| {lego} | {runs} | {ap_s} | {div} | {innate} |")

    print(f"\n**TOTAL**: {len(rows)} sims, {innate_count} with innate_failure=True")


if __name__ == "__main__":
    main()
