#!/usr/bin/env python3
"""
sim_capability_hypothesis_isolated.py -- Isolated tool-capability probe for hypothesis.

Classical_baseline capability probe: exercises hypothesis property-based testing
in isolation. Verifies reverse(reverse(xs))==xs for 100 cases and confirms that
hypothesis FINDS a counterexample when the invariant is intentionally broken.
Per the four-sim-kinds doctrine this is a capability sim, not an integration sim.
"""

import json
import os

classification = "classical_baseline"
divergence_log = (
    "Classical capability baseline: this isolates hypothesis as a single-tool "
    "property-testing probe, not a canonical nonclassical witness."
)

_ISOLATED_REASON = (
    "not used: this probe isolates the hypothesis property-based testing capability "
    "in isolation; cross-tool integration is deferred to a dedicated integration sim "
    "per the four-sim-kinds doctrine (capability must precede integration)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "hypothesis": {"tried": True, "used": True, "reason": "load-bearing isolated capability probe for property-based test generation and shrinking"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["hypothesis"] = "load_bearing"

HYPOTHESIS_OK = False
HYPOTHESIS_VERSION = None
try:
    import hypothesis
    from hypothesis import given, settings, HealthCheck
    from hypothesis import strategies as st
    HYPOTHESIS_OK = True
    HYPOTHESIS_VERSION = getattr(hypothesis, "__version__", "unknown")
except Exception as exc:
    _hypothesis_exc = exc


def run_positive_tests():
    r = {}
    if not HYPOTHESIS_OK:
        r["hypothesis_available"] = {"pass": False, "detail": f"hypothesis missing: {_hypothesis_exc}"}
        return r
    r["hypothesis_available"] = {"pass": True, "version": HYPOTHESIS_VERSION}

    # Property: reverse(reverse(xs)) == xs for lists of integers
    failures = []

    @given(st.lists(st.integers(min_value=-100, max_value=100), max_size=20))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def _check_double_reverse(xs):
        if list(reversed(list(reversed(xs)))) != xs:
            failures.append(xs)

    try:
        _check_double_reverse()
        r["double_reverse_holds_100_cases"] = {
            "pass": len(failures) == 0,
            "failures_found": len(failures),
        }
    except Exception as exc:
        r["double_reverse_holds_100_cases"] = {"pass": False, "detail": str(exc)}

    # Property: double reverse also works for empty list (explicit check)
    r["empty_list_double_reverse"] = {
        "pass": list(reversed(list(reversed([])))) == [],
    }
    return r


def run_negative_tests():
    r = {}
    if not HYPOTHESIS_OK:
        r["skip"] = {"pass": False, "detail": "hypothesis missing"}
        return r

    # Broken invariant: "xs is a palindrome" is NOT true for all random lists.
    # Hypothesis should find a counterexample quickly.
    found_counterexample = False
    counterexample_detail = None

    @given(st.lists(st.integers(min_value=0, max_value=9), min_size=1, max_size=10))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def _check_palindrome_broken(xs):
        nonlocal found_counterexample, counterexample_detail
        # This invariant is FALSE for most lists
        assert xs == list(reversed(xs)), f"Not a palindrome: {xs}"

    try:
        _check_palindrome_broken()
        # If no exception, the invariant accidentally held (shouldn't happen for random lists)
        r["hypothesis_finds_counterexample_for_broken_invariant"] = {
            "pass": False,
            "note": "No counterexample found — unexpected for palindrome check on random lists",
        }
    except Exception as exc:
        # hypothesis.errors.Unsatisfied or AssertionError -> counterexample found
        exc_str = str(exc)
        found_counterexample = True
        counterexample_detail = exc_str[:200]
        r["hypothesis_finds_counterexample_for_broken_invariant"] = {
            "pass": True,
            "counterexample_found": True,
            "exc_type": type(exc).__name__,
            "detail": counterexample_detail,
        }
    return r


def run_boundary_tests():
    r = {}
    if not HYPOTHESIS_OK:
        r["skip"] = {"pass": False, "detail": "hypothesis missing"}
        return r

    # Boundary: empty list must satisfy double-reverse property
    xs = []
    result = list(reversed(list(reversed(xs))))
    r["empty_list_boundary"] = {
        "pass": result == [],
        "result": result,
    }

    # Boundary: single-element list
    xs_single = [42]
    result_single = list(reversed(list(reversed(xs_single))))
    r["single_element_boundary"] = {
        "pass": result_single == [42],
        "result": result_single,
    }

    # Boundary: hypothesis with max_examples=1 still runs without crashing
    ran_ok = False
    try:
        @given(st.lists(st.integers(), max_size=5))
        @settings(max_examples=1, suppress_health_check=[HealthCheck.too_slow])
        def _one_example(xs):
            assert list(reversed(list(reversed(xs)))) == xs

        _one_example()
        ran_ok = True
    except Exception as exc:
        ran_ok = False

    r["max_examples_1_runs_ok"] = {"pass": ran_ok}
    return r


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_hypothesis_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {
            "name": "hypothesis",
            "version": HYPOTHESIS_VERSION,
            "integration": "load_bearing",
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": (
                "Verify reverse(reverse(xs))==xs holds across 100 generated integer "
                "list cases; actively find counterexamples when an invariant is broken "
                "(palindrome check on random lists fails fast); handles empty and "
                "single-element boundary inputs without crash."
            ),
            "cannot": (
                "Does not provide formal proofs; shrinking is heuristic and may not "
                "find minimal counterexample in all cases; database persistence between "
                "runs requires hypothesis database configuration."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_hypothesis_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
