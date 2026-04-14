#!/usr/bin/env python3
"""Canonical: Kochen-Specker contextuality via Cabello's 18-ray / 9-context set.

Classical macrorealism / non-contextual hidden variable (NCHV) assignment:
each ray v gets a {0,1} value f(v), each orthogonal 4-tuple (context) must
sum to exactly 1. For the Cabello 18-ray set, this system is UNSAT.

load_bearing: z3 -- the UNSAT certificate on the boolean constraint system
IS the contextuality proof. Without z3 we have no structural impossibility
result; numpy can only attempt enumeration.

Gap: classical NCHV admissible assignments = 0; quantum (projectors) = 1.
UNSAT itself is the gap (structural exclusion of classical realism).

Positive: full 18-ray system returns UNSAT.
Negative: drop one context -> SAT (assignment exists); confirms tightness.
Boundary: single context in isolation -> SAT trivially.
"""
import json
import os

import numpy as np

classification = "canonical"
divergence_log = None

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not required for boolean UNSAT proof"},
    "pyg":       {"tried": False, "used": False, "reason": "not a graph ML task"},
    "z3":        {"tried": False, "used": False, "reason": "placeholder -- filled below"},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 suffices; cvc5 optional cross-check"},
    "sympy":     {"tried": False, "used": False, "reason": "booleans, not symbolic algebra"},
    "clifford":  {"tried": False, "used": False, "reason": "projector algebra already encoded as 18 rays"},
    "geomstats": {"tried": False, "used": False, "reason": "not a manifold task"},
    "e3nn":      {"tried": False, "used": False, "reason": "not a representation task"},
    "rustworkx": {"tried": False, "used": False, "reason": "orthogonality graph small; direct encoding clearer"},
    "xgi":       {"tried": False, "used": False, "reason": "9 contexts small; direct encoding"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None,
    "z3": "load_bearing",
    "cvc5": None, "sympy": None, "clifford": None, "geomstats": None,
    "e3nn": None, "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "boolean SAT/UNSAT on NCHV assignment system; UNSAT = KS contextuality proof"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    z3 = None


# 18 rays in R^4 (unnormalized), verified orthogonal in 9 contexts with each
# ray appearing in exactly 2 contexts (Cabello-Estebaranz-Garcia-Alcaine 1996
# parity structure; specific representatives recovered algorithmically).
RAYS = [
    (0, 0, 0, 1),     # 0
    (0, 0, 1, 0),     # 1
    (0, 0, 1, 1),     # 2
    (0, 1,-1, 0),     # 3
    (0, 1, 0,-1),     # 4
    (0, 1, 0, 1),     # 5
    (0, 1, 1, 0),     # 6
    (1,-1,-1, 1),     # 7
    (1,-1, 0, 0),     # 8
    (1,-1, 1,-1),     # 9
    (1,-1, 1, 1),     # 10
    (1, 0,-1, 0),     # 11
    (1, 0, 0,-1),     # 12
    (1, 0, 0, 0),     # 13
    (1, 1,-1, 1),     # 14
    (1, 1, 0, 0),     # 15
    (1, 1, 1,-1),     # 16
    (1, 1, 1, 1),     # 17
]

CONTEXTS = [
    (0, 1, 8, 15),
    (0, 3, 6, 13),
    (1, 4, 5, 13),
    (2, 7, 9, 15),
    (2, 8, 14, 16),
    (3, 7, 12, 17),
    (4, 9, 11, 17),
    (5, 10, 11, 16),
    (6, 10, 12, 14),
]


def _verify_orthogonality():
    """Sanity: every declared context is pairwise orthogonal (within num tol)."""
    rays = np.array(RAYS, dtype=float)
    bad = []
    for c in CONTEXTS:
        for i in range(4):
            for j in range(i + 1, 4):
                dot = float(np.dot(rays[c[i]], rays[c[j]]))
                if abs(dot) > 1e-12:
                    bad.append((c, c[i], c[j], dot))
    return bad


def _solve_nchv(contexts):
    """Return 'sat'/'unsat' for NCHV over given contexts."""
    if z3 is None:
        return "z3_missing"
    s = z3.Solver()
    xs = [z3.Bool(f"v{i}") for i in range(len(RAYS))]
    for c in contexts:
        # exactly one of the four rays in a context is assigned 1
        bs = [xs[i] for i in c]
        s.add(z3.PbEq([(b, 1) for b in bs], 1))
    r = s.check()
    if r == z3.sat:
        return "sat"
    if r == z3.unsat:
        return "unsat"
    return "unknown"


def run_positive_tests():
    r = {}
    # Pre-check: contexts are legitimately orthogonal.
    ortho_bad = _verify_orthogonality()
    r["contexts_orthogonal"] = {
        "bad_pairs": len(ortho_bad),
        "pass": len(ortho_bad) == 0,
    }
    # Full KS system must be UNSAT.
    status = _solve_nchv(CONTEXTS)
    r["full_system_unsat"] = {
        "z3_status": status,
        "pass": status == "unsat",
    }
    # Classical admissible assignments = 0 (UNSAT); quantum projectors exist = 1.
    r["gap"] = {
        "classical_nchv_assignments": 0 if status == "unsat" else 1,
        "quantum_projector_assignments": 1,
        "gap": 1,
        "pass": status == "unsat",
    }
    return r


def run_negative_tests():
    r = {}
    # Drop one context -> system should become SAT.
    reduced = CONTEXTS[:-1]
    status = _solve_nchv(reduced)
    r["drop_last_context_sat"] = {
        "z3_status": status,
        "pass": status == "sat",
    }
    # Drop a different context (index 0) -> also SAT.
    reduced2 = CONTEXTS[1:]
    status2 = _solve_nchv(reduced2)
    r["drop_first_context_sat"] = {
        "z3_status": status2,
        "pass": status2 == "sat",
    }
    return r


def run_boundary_tests():
    r = {}
    # Single context alone is trivially SAT.
    status = _solve_nchv(CONTEXTS[:1])
    r["single_context_sat"] = {
        "z3_status": status,
        "pass": status == "sat",
    }
    # Two contexts sharing rays still SAT.
    status2 = _solve_nchv(CONTEXTS[:2])
    r["two_contexts_sat"] = {
        "z3_status": status2,
        "pass": status2 == "sat",
    }
    return r


def _all_pass(section):
    return all(v.get("pass", False) for v in section.values())


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = _all_pass(pos) and _all_pass(neg) and _all_pass(bnd)

    results = {
        "name": "kochen_specker_18ray_canonical",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "load_bearing_tool": "z3",
            "gap_classical": 0,
            "gap_quantum": 1,
            "gap_value": 1,
            "gap_kind": "structural_unsat",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "kochen_specker_18ray_canonical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out_path}")
    raise SystemExit(0 if all_pass else 1)
