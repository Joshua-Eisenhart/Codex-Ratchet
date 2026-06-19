#!/usr/bin/env python3
"""Authoritative EXACT leg -- exact integer set arithmetic over the finite
configuration space {0,1}^N. No floats in the survivor-set logic (the only
float is the mean, immediately rounded to an integer threshold).

Computation style UNIQUE to this leg: explicit enumeration of the full
configuration set and exact set operations (symmetric-difference counts).

It derives, independently of any other leg:
  * running_mean_threshold under the RUNNING survivor set -> noncommute count > 0
    (order-dependence from a natural survivor-set-reactive rule; the full-fleet audit
     rejected the stronger 'emergence' label -- this is order-dependent filtering)
  * the SAME family under the FIXED-reference isolator -> noncommute count 0
    (isolates the order-sensitivity to the running-set dependence)
  * three confluence controls (consistency / competitive / minority) -> 0
    (shows noncommutation is NOT a universal property of natural rules)
  * robustness of the running-X count across N in {5,6,7}

Ceiling: scratch_diagnostic, promotion_allowed=False. This exhibits the
noncommutation PRIMITIVE only; it is NOT a full ratchet and NOT a local-only rule.
"""

import itertools
import json
import os
import hashlib
from datetime import datetime, timezone

SIM_ID = "survivor_set_running_mean_threshold_noncommutation_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
OFFSETS = [-2, -1, 1, 2]


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def windows_for(n):
    """Deduplicated cell-sets from nonempty offset-subsets, mod n."""
    seen = []
    for k in range(1, len(OFFSETS) + 1):
        for t in itertools.combinations(OFFSETS, k):
            comp = tuple(sorted(set(o % n for o in t)))
            if comp not in seen:
                seen.append(comp)
    return seen


def count1(x, comp):
    return sum(x[i] for i in comp)


# ---- rule family: running-mean threshold (candidate engine) ----
# CONVENTION-FREE: the threshold is the REAL-valued mean (no rounding). "survive iff
# your 1-count is at or above the running average 1-count." An earlier round()-based
# version was convention-fragile (floor->0); the real-valued mean removes that artifact
# (>= gives 62/105, > gives 64/105, both robust across N). floor(mean) is kept below as
# an explicit state-dependent-BUT-confluent control.
def mean_count(comp, X):
    if not X:
        return 0.0
    return sum(count1(y, comp) for y in X) / len(X)


def step_density_running(comp, X):
    m = mean_count(comp, X)
    return [x for x in X if count1(x, comp) >= m]


def step_density_fixed(comp, X, REF):
    m = mean_count(comp, REF)  # mean read from FIXED reference, not running X
    return [x for x in X if count1(x, comp) >= m]


def step_density_floor_running(comp, X):
    # state-dependent threshold floor(mean): a NON-CONSTANT function of the running set
    # that is nonetheless CONFLUENT -- shows state-dependence is necessary but NOT sufficient.
    import math
    thr = math.floor(mean_count(comp, X))
    return [x for x in X if count1(x, comp) >= thr]


# ---- confluence controls ----
def _cond_value(c, x, comp, X, anti=False):
    w = [(c + o) % len(x) for o in comp]
    ones = zeros = 0
    for y in X:
        if all(y[j] == x[j] for j in w):
            if y[c] == 1:
                ones += 1
            else:
                zeros += 1
    if ones == zeros:
        return None
    maj = 1 if ones > zeros else 0
    return (1 - maj) if anti else maj


def step_consistency(comp, X):
    out = []
    for x in X:
        ok = True
        for c in range(len(x)):
            m = _cond_value(c, x, comp, X, anti=False)
            if m is not None and x[c] != m:
                ok = False
                break
        if ok:
            out.append(x)
    return out


def step_minority(comp, X):
    out = []
    for x in X:
        ok = True
        for c in range(len(x)):
            m = _cond_value(c, x, comp, X, anti=True)
            if m is not None and x[c] != m:
                ok = False
                break
        if ok:
            out.append(x)
    return out


def step_competitive(comp, X):
    n = len(X[0]) if X else 0
    outside = None
    out = []
    compset = set(comp)
    for x in X:
        outc = [i for i in range(n) if i not in compset]
        dominated = False
        for y in X:
            if y is x:
                continue
            if all(y[i] == x[i] for i in outc) and count1(y, comp) > count1(x, comp):
                dominated = True
                break
        if not dominated:
            out.append(x)
    return out


def noncommute_count(step, windows, ALL):
    """count of unordered window pairs whose two application orders differ."""
    nc = 0
    examples = []
    for a, b in ((a, b) for a in windows for b in windows if a < b):
        AB = step(b, step(a, ALL))
        BA = step(a, step(b, ALL))
        d = len(set(AB) ^ set(BA))
        if d > 0:
            nc += 1
            if len(examples) < 2 and len(AB) > 0 and len(BA) > 0:
                examples.append({"a": list(a), "b": list(b), "len_AB": len(AB),
                                 "len_BA": len(BA), "symdiff": d})
    return nc, examples


def fixed_ref_count(windows, ALL):
    nc = 0
    for a, b in ((a, b) for a in windows for b in windows if a < b):
        A2 = step_density_fixed(b, step_density_fixed(a, ALL, ALL), ALL)
        B2 = step_density_fixed(a, step_density_fixed(b, ALL, ALL), ALL)
        if set(A2) ^ set(B2):
            nc += 1
    return nc


def run_for_n(n):
    ALL = [tuple(p) for p in itertools.product([0, 1], repeat=n)]
    windows = windows_for(n)
    npairs = len(windows) * (len(windows) - 1) // 2
    dens_run, dens_ex = noncommute_count(step_density_running, windows, ALL)
    dens_fix = fixed_ref_count(windows, ALL)
    dens_floor, _ = noncommute_count(step_density_floor_running, windows, ALL)
    cons, _ = noncommute_count(step_consistency, windows, ALL)
    comp, _ = noncommute_count(step_competitive, windows, ALL)
    mino, _ = noncommute_count(step_minority, windows, ALL)
    return {
        "N": n,
        "config_count": len(ALL),
        "window_count": len(windows),
        "pair_count": npairs,
        "running_mean_threshold_running_X_noncommute": dens_run,
        "running_mean_threshold_fixed_reference_noncommute": dens_fix,
        "floor_mean_threshold_running_X_noncommute": dens_floor,
        "ensemble_consistency_noncommute": cons,
        "competitive_exclusion_noncommute": comp,
        "minority_frustration_noncommute": mino,
        "examples": dens_ex,
    }


def main():
    per_n = {n: run_for_n(n) for n in (5, 6, 7)}

    # the load-bearing facts
    order_dependence = all(per_n[n]["running_mean_threshold_running_X_noncommute"] > 0 for n in per_n)
    isolator_holds = all(per_n[n]["running_mean_threshold_fixed_reference_noncommute"] == 0 for n in per_n)
    # state-dependence is NECESSARY (fixed-ref->0) but NOT SUFFICIENT: floor(mean) and the three
    # control families are all state-dependent yet confluent. This refutes "any state-dependent
    # threshold trivially noncommutes."
    necessary_not_sufficient = all(
        per_n[n]["floor_mean_threshold_running_X_noncommute"] == 0
        and per_n[n]["ensemble_consistency_noncommute"] == 0
        and per_n[n]["competitive_exclusion_noncommute"] == 0
        and per_n[n]["minority_frustration_noncommute"] == 0
        for n in per_n
    )
    controls_confluent = necessary_not_sufficient

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "exact",
        "computation_style": "explicit_enumeration_exact_set_operations",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_exact_results.json",
        "per_N": per_n,
        "claims": {
            "running_X_admits_order_dependence": order_dependence,
            "isolator_fixed_reference_commutes": isolator_holds,
            "state_dependence_necessary_not_sufficient": necessary_not_sufficient,
            "rule": "convention-free: survive iff count1(x,comp) >= real-valued mean over the running survivor set (no rounding)",
            "interpretation": (
                "Under a natural state-reactive cut ('survive iff your 1-count is at or above the running average'), "
                "survivor-set descent ADMITS ORDER-DEPENDENT terminal sets (restriction-noncommutation) for a GENERIC "
                "fraction of window pairs (62/105 at this alphabet; the strict '>' variant gives 64/105). "
                "The fixed-reference control commutes (0), so dependence on the RUNNING survivor set is NECESSARY -- "
                "BUT note this control is partly a set-intersection tautology (static predicates commute), so it confirms "
                "necessity rather than supplying independent causal evidence. State-dependence is NOT SUFFICIENT: floor(mean) "
                "-- also a state-dependent threshold -- is confluent (0), as are the three closure/dominance control families. "
                "So the noncommutation is a real property of THIS non-monotone-aggregate cut, which REFUTES the objection "
                "that any state-reactive threshold trivially noncommutes."
            ),
            "emergence_label": "REJECTED as overclaim by the full-fleet audit (6/7 returning verdicts; held divergence: gemini-3.1-pro alone called it justified). This is order-dependent survivor-set filtering under a natural state-reactive cut, NOT strong emergence.",
            "fragility_note": "an earlier round()-based threshold was convention-fragile (floor->0, ceil->62, banker's-round->44, half-up->32); the real-valued mean removes that rounding artifact.",
            "robustness_caveat": "the count is identical at N in {5,6,7} because it is fixed by the window-SIZE structure (offset alphabet), so N is a WEAK robustness axis. The meaningful robustness is convention-freeness (no rounding) and both inequality variants (>= 62, > 64).",
        },
        "honest_scope": {
            "earns": "a narrow, fleet-survived fact: a natural state-reactive cut ADMITS generic restriction-noncommutation, convention-free, with the necessary-not-sufficient sharpening (state-dependence alone does not force it)",
            "does_not_earn": "the 'emergence' label (fleet-rejected); a full ratchet (strict-decrease/termination/distinct-terminal-sets); a local-only rule (threshold reads a GLOBAL aggregate -- the mean over the whole survivor set); a causal 'engine'; no GNVW/bridge/manifold/axis claim",
        },
        "packages_used": ["python-stdlib"],
        "TOOL_MANIFEST": {
            "itertools": {"tried": True, "used": True, "reason": "exact enumeration of the finite configuration space and window alphabet"},
        },
        "TOOL_INTEGRATION_DEPTH": {"itertools": "supportive"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_exact_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"exact leg wrote {out}")
    for n in (5, 6, 7):
        r = per_n[n]
        print(f"  N={n}: density(>=mean) running-X {r['running_mean_threshold_running_X_noncommute']}/{r['pair_count']} "
              f"| fixed-ref {r['running_mean_threshold_fixed_reference_noncommute']} "
              f"| floor(mean) {r['floor_mean_threshold_running_X_noncommute']} "
              f"| consistency {r['ensemble_consistency_noncommute']} competitive {r['competitive_exclusion_noncommute']} minority {r['minority_frustration_noncommute']}")
    print(f"  order_dependence={order_dependence} isolator_holds={isolator_holds} necessary_not_sufficient={necessary_not_sufficient}")


if __name__ == "__main__":
    main()
