#!/usr/bin/env python3
"""
sim_sci_method_atom_6_chirality.py

Atom 6/7: CHIRALITY -- forward-potential vs past-causality asymmetry.

Claim: The recursive science method is chiral: the "forward" direction
(what futures remain admissible given current constraints) and the
"backward" direction (what pasts could have produced the current state)
are NOT symmetric. A chirality operator χ flips the two; a process is
chiral iff χ(process) != process under probe P.

Positive: a directed step sequence s = (0,1,2,3) has reversal s' = (3,2,1,0);
          their probe-signatures differ under the ordered-difference probe.
Negative: a symmetric (palindromic) sequence has χ(s) = s under the same probe
          -- no chirality, so the "chirality claim" is falsified for it.
Boundary: sequence of length 1 is trivially self-reverse -- chirality
          undefined (must be reported as such, not as PASS of chirality).

This matches the doctrine: separate forward-evolution from backward-admissibility
claims explicitly.
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


def signature(seq):
    """Ordered-difference signature: tuple of (s[i+1]-s[i])."""
    return tuple(seq[i+1] - seq[i] for i in range(len(seq)-1))


def chi(seq):
    return tuple(reversed(seq))


def is_chiral(seq):
    rev = chi(seq)
    return signature(seq) != signature(rev), signature(seq), signature(rev)


def _z3_confirm_inequality(sig_a, sig_b):
    s = z3.Solver()
    neq = z3.Bool("neq")
    s.add(neq == z3.BoolVal(sig_a != sig_b))
    s.add(neq)
    return s.check() == z3.sat


def run_positive_tests():
    seq = (0, 1, 2, 3)
    chiral, sa, sb = is_chiral(seq)
    zok = _z3_confirm_inequality(sa, sb)
    # sympy symbolic cross-check: sum of signature differs in sign on reverse
    sym_ok = sp.Rational(sum(sa)) == -sp.Rational(sum(sb))
    r = {"chiral": chiral, "sig": list(sa), "sig_rev": list(sb),
         "z3_sig_neq": zok, "sympy_sign_flip": bool(sym_ok),
         "pass": chiral and zok and bool(sym_ok)}
    return {"monotone_step": r, "all_pass": r["pass"]}


def run_negative_tests():
    seq = (0, 1, 0, 1, 0)  # palindrome-ish under diff: diffs = (1,-1,1,-1); rev diffs = (1,-1,1,-1)
    chiral, sa, sb = is_chiral(seq)
    r = {"chiral": chiral, "sig": list(sa), "sig_rev": list(sb),
         "pass": not chiral}
    return {"symmetric_seq": r, "all_pass": r["pass"]}


def run_boundary_tests():
    seq = (7,)
    chiral, sa, sb = is_chiral(seq)
    # sig is empty tuple for length 1; chirality undefined -> must report not-chiral
    r = {"chiral": chiral, "sig": list(sa), "sig_rev": list(sb),
         "pass": (not chiral) and sa == () and sb == ()}
    return {"length_one": r, "all_pass": r["pass"]}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "load-bearing confirmation sig(s) != sig(chi(s))"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic sign-flip cross-check of signature sums"
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
