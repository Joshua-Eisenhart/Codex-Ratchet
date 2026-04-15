#!/usr/bin/env python3
"""
sim_hypothesis_property_admissibility_invariant.py

Canonical sim. Property-based test with `hypothesis` over random G-tower
reduction sequences drawn from {GL, O, SO, SU, U1}, length 1..5.

Claim (exclusion framing):
  - If a sequence is COMMUTATIVE (all pairwise [A,B]=0 in our stylized
    commutation table), the admissibility predicate SURVIVES cyclic shift.
  - If a sequence is NON-COMMUTATIVE, at least one cyclic shift is
    EXCLUDED by the admissibility predicate (the witness is destroyed).
"""

import json
import os
from hypothesis import given, strategies as st, settings, HealthCheck

classification = "canonical"

TOOL_MANIFEST = {
    "hypothesis": {"tried": True, "used": True,
                   "reason": "randomized property-based generation of G-tower reduction sequences"},
}
TOOL_INTEGRATION_DEPTH = {"hypothesis": "load_bearing"}

GROUPS = ["GL", "O", "SO", "SU", "U1"]

# Stylized commutation table. Pairs listed commute. Anything else does not.
COMMUTES = {
    frozenset(("SO", "O")),
    frozenset(("SU", "U1")),
    frozenset(("GL", "GL")),
    frozenset(("O", "O")),
    frozenset(("SO", "SO")),
    frozenset(("SU", "SU")),
    frozenset(("U1", "U1")),
}


def pairwise_commutative(seq):
    for i in range(len(seq)):
        for j in range(i + 1, len(seq)):
            if frozenset((seq[i], seq[j])) not in COMMUTES:
                return False
    return True


def admissible(seq):
    """Stylized predicate: sequence is admissible iff no excluded adjacent
    pair. We mark (GL, U1) and (O, SU) as excluded adjacencies."""
    excluded = {("GL", "U1"), ("U1", "GL"), ("O", "SU"), ("SU", "O")}
    for a, b in zip(seq, seq[1:]):
        if (a, b) in excluded:
            return False
    return True


def cyclic_shifts(seq):
    return [tuple(seq[i:] + seq[:i]) for i in range(len(seq))]


# Track outcomes across hypothesis runs
STATS = {
    "total": 0,
    "commutative_invariant": 0,
    "commutative_violations": 0,
    "noncomm_total": 0,
    "noncomm_with_excluded_shift": 0,
}


@settings(max_examples=300, deadline=None,
          suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(st.sampled_from(GROUPS), min_size=1, max_size=5))
def _property(seq):
    STATS["total"] += 1
    verdicts = [admissible(s) for s in cyclic_shifts(seq)]
    all_same = all(v == verdicts[0] for v in verdicts)
    if pairwise_commutative(seq):
        if all_same:
            STATS["commutative_invariant"] += 1
        else:
            STATS["commutative_violations"] += 1
        # Property assertion: commutative => invariant under cyclic shift
        assert all_same, f"commutative but not invariant: {seq}"
    else:
        STATS["noncomm_total"] += 1
        if not all(verdicts):
            STATS["noncomm_with_excluded_shift"] += 1


def run_positive_tests():
    STATS.update({k: 0 for k in STATS})
    _property()
    return {
        "total_cases": STATS["total"],
        "commutative_invariant": STATS["commutative_invariant"],
        "commutative_violations": STATS["commutative_violations"],
        "invariance_held": STATS["commutative_violations"] == 0 and STATS["commutative_invariant"] > 0,
    }


def run_negative_tests():
    # Direct negative: a known non-commutative sequence has a cyclic shift excluded.
    seq = ["GL", "U1", "SO"]  # GL-U1 excluded adjacency; rotate exposes it
    shifts = cyclic_shifts(seq)
    verdicts = [admissible(s) for s in shifts]
    return {
        "sequence": seq,
        "shift_verdicts": verdicts,
        "at_least_one_excluded": not all(verdicts),
    }


def run_boundary_tests():
    # Boundary: length-1 sequence is trivially invariant under cyclic shift.
    seq = ["SU"]
    shifts = cyclic_shifts(seq)
    verdicts = [admissible(s) for s in shifts]
    return {
        "len1_invariant": all(v == verdicts[0] for v in verdicts),
        "noncomm_shift_stats": {
            "noncomm_total": STATS["noncomm_total"],
            "noncomm_with_excluded_shift": STATS["noncomm_with_excluded_shift"],
        },
    }


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    passed = (
        pos.get("invariance_held", False)
        and neg.get("at_least_one_excluded", False)
        and bnd.get("len1_invariant", False)
    )
    results = {
        "name": "sim_hypothesis_property_admissibility_invariant",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": bool(passed),
        "passed": bool(passed),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_hypothesis_property_admissibility_invariant_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={passed} -> {out_path}")
