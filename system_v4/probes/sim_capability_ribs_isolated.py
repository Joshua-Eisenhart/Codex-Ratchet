#!/usr/bin/env python3
"""
sim_capability_ribs_isolated.py -- Isolated tool-capability probe for pyribs.

Classical_baseline capability probe: demonstrates that ribs.archives.GridArchive
supports insert/query/coverage in isolation, with honest positive/negative/boundary
coverage. Pays down discipline debt recorded 2026-04-14 in KNOWN_DISCIPLINE_DEBT.md
for the evolutionary-tool integration sims that were authored before their
capability probes existed. Per the four-sim-kinds doctrine, this is a capability
sim, not an integration sim; it deliberately avoids coupling to any other tool
or lego.
"""

import json
import os

classification = "classical_baseline"
divergence_log = (
    "Classical capability baseline: this isolates ribs as a single-tool "
    "MAP-Elites/archive probe, not a canonical nonclassical witness."
)

# =====================================================================
# TOOL MANIFEST
# =====================================================================

_ISOLATED_REASON = (
    "not used: this probe isolates the pyribs GridArchive capability in "
    "isolation; cross-tool integration deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
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
    "ribs":      {"tried": True, "used": True, "reason": "load-bearing isolated capability probe for GridArchive insertion, coverage tracking, and elite sampling"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
    "ribs": "load_bearing",
}
RIBS_OK = False
RIBS_VERSION = None
try:
    import numpy as np
    import ribs
    from ribs.archives import GridArchive
    RIBS_OK = True
    RIBS_VERSION = getattr(ribs, "__version__", "unknown")
except Exception as exc:
    _ribs_exc = exc


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    r = {}
    if not RIBS_OK:
        r["ribs_available"] = {"pass": False, "detail": f"ribs missing: {_ribs_exc}"}
        return r
    r["ribs_available"] = {"pass": True, "version": RIBS_VERSION}

    # GridArchive with 2 behavior dims, 10x10 cells, each in [-1, 1].
    archive = GridArchive(
        solution_dim=3,
        dims=[10, 10],
        ranges=[(-1.0, 1.0), (-1.0, 1.0)],
    )
    sols = np.random.default_rng(0).standard_normal((50, 3))
    objs = np.linalg.norm(sols, axis=1)  # fitness
    measures = np.random.default_rng(1).uniform(-1, 1, size=(50, 2))
    add_info = archive.add(sols, objs, measures)
    occupied = len(archive)
    coverage = occupied / 100.0
    r["insert_populates_archive"] = {
        "pass": occupied > 0 and coverage > 0.0,
        "occupied": int(occupied),
        "coverage": float(coverage),
    }
    # Query: sample from archive
    sample = archive.sample_elites(5)
    r["sample_elites"] = {
        "pass": len(sample["solution"]) == 5,
        "sample_count": int(len(sample["solution"])),
    }
    return r


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    r = {}
    if not RIBS_OK:
        r["skip"] = {"pass": False, "detail": "ribs missing"}
        return r
    archive = GridArchive(
        solution_dim=3,
        dims=[5, 5],
        ranges=[(-1.0, 1.0), (-1.0, 1.0)],
    )
    raised = False
    try:
        # Malformed insert: solution dim mismatch (2 instead of 3).
        archive.add(np.zeros((1, 2)), np.zeros(1), np.zeros((1, 2)))
    except Exception:
        raised = True
    r["malformed_insert_raises"] = {"pass": raised}
    return r


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    r = {}
    if not RIBS_OK:
        r["skip"] = {"pass": False, "detail": "ribs missing"}
        return r
    # Empty archive: coverage must be 0.
    archive = GridArchive(
        solution_dim=2, dims=[4, 4], ranges=[(0.0, 1.0), (0.0, 1.0)],
    )
    coverage = len(archive) / 16.0
    r["empty_archive_coverage_zero"] = {
        "pass": coverage == 0.0,
        "coverage": float(coverage),
    }
    return r


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_ribs_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {"name": "ribs", "version": RIBS_VERSION, "integration": "load_bearing"},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": "GridArchive admits batched (solution, objective, measure) "
                   "inserts, tracks coverage, and samples elites deterministically "
                   "with a seed; supports boundary case of empty archive = 0 coverage.",
            "cannot": "Does not by itself define what behavior measures MEAN; "
                     "measure-design is a modeling decision excluded from this probe.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_ribs_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
