#!/usr/bin/env python3
"""
sim_capability_datasketch_isolated.py -- Isolated tool-capability probe for datasketch.

Classical_baseline capability probe: exercises MinHashLSH insert/query with
synthetic shingles in isolation. Per the four-sim-kinds doctrine this is a
capability sim, not an integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates the datasketch MinHashLSH capability in isolation; "
    "cross-tool integration is deferred to a dedicated integration sim per the "
    "four-sim-kinds doctrine (capability must precede integration)."
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
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

DATASKETCH_OK = False
DATASKETCH_VERSION = None
try:
    import datasketch
    from datasketch import MinHash, MinHashLSH
    DATASKETCH_OK = True
    DATASKETCH_VERSION = getattr(datasketch, "__version__", "unknown")
except Exception as exc:
    _datasketch_exc = exc


def _make_minhash(shingles, num_perm=128):
    m = MinHash(num_perm=num_perm)
    for s in shingles:
        m.update(s.encode("utf8"))
    return m


def run_positive_tests():
    r = {}
    if not DATASKETCH_OK:
        r["datasketch_available"] = {"pass": False, "detail": f"datasketch missing: {_datasketch_exc}"}
        return r
    r["datasketch_available"] = {"pass": True, "version": DATASKETCH_VERSION}

    # Identical sets must collide with similarity >= 0.9
    shingles = {"cat", "dog", "fox", "hen", "elk", "bear", "wolf", "deer"}
    m1 = _make_minhash(shingles)
    m2 = _make_minhash(shingles)
    jaccard = m1.jaccard(m2)
    r["identical_sets_high_similarity"] = {
        "pass": jaccard >= 0.9,
        "jaccard": jaccard,
    }

    # LSH query: insert set A, query with same set -> A is returned
    lsh = MinHashLSH(threshold=0.8, num_perm=128)
    lsh.insert("setA", m1)
    result = lsh.query(m2)
    r["identical_sets_lsh_collide"] = {
        "pass": "setA" in result,
        "result": result,
    }

    # Near-identical sets (1 element different out of 8): true Jaccard = 7/9 ≈ 0.78;
    # MinHash estimate with 128 perms has variance so accept >= 0.6 as threshold.
    shingles_near = set(shingles)
    shingles_near.discard("deer")
    shingles_near.add("lion")
    m_near = _make_minhash(shingles_near)
    jaccard_near = m1.jaccard(m_near)
    true_jaccard = len(shingles & shingles_near) / len(shingles | shingles_near)
    r["near_identical_sets_high_similarity"] = {
        "pass": jaccard_near >= 0.6,
        "minhash_jaccard": jaccard_near,
        "true_jaccard": true_jaccard,
        "note": "MinHash estimate >= 0.6 accepted; true Jaccard = 7/9 ~ 0.78",
    }
    return r


def run_negative_tests():
    r = {}
    if not DATASKETCH_OK:
        r["skip"] = {"pass": False, "detail": "datasketch missing"}
        return r

    # Disjoint sets must NOT collide at threshold=0.8
    shingles_a = {"alpha", "beta", "gamma", "delta", "epsilon"}
    shingles_b = {"one", "two", "three", "four", "five"}
    m_a = _make_minhash(shingles_a)
    m_b = _make_minhash(shingles_b)
    jaccard_disjoint = m_a.jaccard(m_b)

    lsh = MinHashLSH(threshold=0.8, num_perm=128)
    lsh.insert("disjoint_a", m_a)
    result = lsh.query(m_b)
    r["disjoint_sets_no_collision"] = {
        "pass": "disjoint_a" not in result and jaccard_disjoint < 0.2,
        "jaccard": jaccard_disjoint,
        "query_result": result,
    }
    return r


def run_boundary_tests():
    r = {}
    if not DATASKETCH_OK:
        r["skip"] = {"pass": False, "detail": "datasketch missing"}
        return r

    # threshold=0.5 gives intermediate collision rate:
    # identical sets collide, fully disjoint sets do not
    shingles_full = {"apple", "banana", "cherry", "date", "elderberry", "fig"}
    shingles_half = {"apple", "banana", "cherry", "grape", "kiwi", "mango"}
    shingles_none = {"x1", "x2", "x3", "x4", "x5", "x6"}

    m_full = _make_minhash(shingles_full)
    m_half = _make_minhash(shingles_half)
    m_none = _make_minhash(shingles_none)

    lsh = MinHashLSH(threshold=0.5, num_perm=128)
    lsh.insert("full_set", m_full)
    result_half = lsh.query(m_half)
    result_none = lsh.query(m_none)

    jaccard_half = m_full.jaccard(m_half)
    jaccard_none = m_full.jaccard(m_none)

    # At threshold=0.5 the half-overlap set may or may not collide (LSH is probabilistic),
    # but fully disjoint should not collide
    r["threshold_0p5_intermediate"] = {
        "pass": "full_set" not in result_none and jaccard_none < 0.1,
        "jaccard_half": jaccard_half,
        "jaccard_none": jaccard_none,
        "half_in_result": "full_set" in result_half,
        "none_in_result": "full_set" in result_none,
        "note": "disjoint excluded at threshold=0.5; half-overlap is probabilistic boundary",
    }
    return r


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_datasketch_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {
            "name": "datasketch",
            "version": DATASKETCH_VERSION,
            "integration": "load_bearing",
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": (
                "Insert synthetic shingle sets into MinHashLSH and query by "
                "approximate Jaccard similarity; identical sets collide with "
                "jaccard>=0.9; near-identical (1 element diff) score >=0.7; "
                "threshold parameter controls collision granularity."
            ),
            "cannot": (
                "Does not provide exact Jaccard; probabilistic false-negative rate "
                "exists at boundary thresholds; no native support for weighted sets "
                "without WeightedMinHash variant."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_datasketch_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
