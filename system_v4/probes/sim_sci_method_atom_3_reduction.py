#!/usr/bin/env python3
"""
sim_sci_method_atom_3_reduction.py

Atom 3/7: REDUCTION -- the inquiry quotients the carrier by ~.

Claim: Scientific claims are made about equivalence classes, not raw carriers.
A valid reduction is a surjection q: C -> C/~ whose fibers are exactly the
~-classes. Reduction preserves cardinality as sum of fiber sizes and loses
no admissible candidate.

Positive: partition {0,1,2,3} by parity -> two classes, sizes 2+2=4.
Negative: a non-partition (overlapping "classes") breaks surjectivity-uniqueness.
Boundary: identity reduction q(x)=x gives |C/~|=|C| and zero compression.
"""

import json
import os

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

SIM_BASENAME = os.path.splitext(os.path.basename(__file__))[0]
RUN_BOUNDARY_FIELDS = {
    "claim_ceiling": "recursive science-method atom micro only; no promotion beyond bounded falsifiability/admissibility fixture",
    "next_lego_target": SIM_BASENAME,
    "promotion_condition": "requires later independent admission, executed receipt review, and stage-appropriate lego gate before any higher claim",
    "blocked_until": "exact runner result receipt validates under strict executable run boundary",
    "demotion_condition": "demote if used as theory proof beyond this bounded science-method fixture or if execution result omits positive, negative, or boundary checks",
    "out_of_scope": [
        "no theory promotion",
        "no manifold admission",
        "no scientific coupling claim",
        "no bridge or axis claim",
    ],
}

# --- backfill empty TOOL_MANIFEST reasons (cleanup) ---
def _backfill_reasons(tm):
    for _k,_v in tm.items():
        if not _v.get('reason'):
            if _v.get('used'):
                _v['reason'] = 'used without explicit reason string'
            elif _v.get('tried'):
                _v['reason'] = 'imported but not exercised in this sim'
            else:
                _v['reason'] = 'not used in this sim scope'
    return tm


try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def reduce_by(carrier, key_fn):
    classes = {}
    for c in carrier:
        classes.setdefault(key_fn(c), []).append(c)
    return classes


def is_partition(classes, carrier):
    seen = []
    for cls in classes.values():
        seen.extend(cls)
    return sorted(seen) == sorted(carrier) and len(seen) == len(set(seen))


def _z3_fiber_sum(classes, total):
    s = z3.Solver()
    # Sum of fiber sizes equals |C|
    sizes = [len(v) for v in classes.values()]
    Sigma = z3.Int("Sigma")
    s.add(Sigma == sum(sizes))
    s.add(Sigma == total)
    return s.check() == z3.sat


def run_positive_tests():
    C = [0, 1, 2, 3]
    classes = reduce_by(C, lambda x: x % 2)
    part = is_partition(classes, C)
    zok = _z3_fiber_sum(classes, len(C))
    r = {"classes": {str(k): v for k, v in classes.items()},
         "is_partition": part, "z3_fiber_sum_ok": zok,
         "n_classes": len(classes)}
    r["pass"] = part and zok and len(classes) == 2
    return {"parity_on_quad": r, "all_pass": r["pass"]}


def run_negative_tests():
    C = [0, 1, 2]
    # Overlapping "classes" violate partition
    classes = {"A": [0, 1], "B": [1, 2]}
    part = is_partition(classes, C)
    r = {"part": part, "pass": not part}
    return {"overlapping_classes": r, "all_pass": r["pass"]}


def run_boundary_tests():
    C = [5, 6, 7]
    classes = reduce_by(C, lambda x: x)  # identity
    part = is_partition(classes, C)
    zok = _z3_fiber_sum(classes, len(C))
    r = {"n_classes": len(classes), "is_partition": part, "z3_ok": zok,
         "pass": part and zok and len(classes) == len(C)}
    # sympy cross-check: Rational(|C|,|C/~|) == 1
    r["sympy_compression_one"] = sp.Rational(len(C), len(classes)) == 1
    r["pass"] = r["pass"] and r["sympy_compression_one"]
    return {"identity_reduction": r, "all_pass": r["pass"]}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing check that fiber sizes sum to |C|"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "rational compression ratio for identity reduction"
    TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"

    results = {
        "name": SIM_BASENAME,
        "classification": "canonical",
        "tool_manifest": _backfill_reasons(TOOL_MANIFEST),
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "overall_pass": pos["all_pass"] and neg["all_pass"] and bnd["all_pass"],
        **RUN_BOUNDARY_FIELDS,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{SIM_BASENAME}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
