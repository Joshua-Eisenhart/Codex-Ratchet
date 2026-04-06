#!/usr/bin/env python3
"""
BC1 Fence Investigation — What Actually Alternates?
====================================================
z3 caught that "expansion alternates at every step" is WRONG for the
actual LOOP_STAGE_ORDER traversal.  This probe finds the TRUE invariants.

Reads engine_core.py structures, prints full tables, checks every
candidate alternation rule, then encodes each as a z3 constraint
to confirm SAT/UNSAT against the real terrain data.

Output: a2_state/sim_results/bc1_fence_investigation_results.json
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR
from z3 import (
    Solver, Bool, Int, IntVal, BoolVal, sat, unsat,
    And, Or, Not, Distinct, If,
)

# ═══════════════════════════════════════════════════════════════════
# 1. FULL STAGE TABLE
# ═══════════════════════════════════════════════════════════════════

def build_stage_table(engine_type):
    """Build full property table for every stage in traversal order."""
    order = LOOP_STAGE_ORDER[engine_type]
    rows = []
    for pos, tidx in enumerate(order):
        t = TERRAINS[tidx]
        key = (engine_type, t["loop"], t["topo"])
        op_name, polarity = STAGE_OPERATOR_LUT[key]
        loop_label = "outer" if pos < 4 else "inner"
        rows.append({
            "position": pos,
            "terrain_idx": tidx,
            "name": t["name"],
            "topo": t["topo"],
            "loop": t["loop"],
            "expansion": t["expansion"],
            "open": t["open"],
            "operator": op_name,
            "polarity_up": polarity,
            "engine_loop": loop_label,
        })
    return rows


def print_table(rows, engine_type):
    """Pretty-print the stage table."""
    hdr = (f"{'Pos':>3}  {'Idx':>3}  {'Name':<6}  {'Topo':<4}  {'Loop':<6}  "
           f"{'Exp':>3}  {'Open':>4}  {'Op':<4}  {'Pol':>3}  {'ELoop':<6}")
    print(f"\n=== Engine Type {engine_type} Stage Order ===")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        exp_s = "T" if r["expansion"] else "F"
        opn_s = "T" if r["open"] else "F"
        pol_s = "+" if r["polarity_up"] else "-"
        print(f"{r['position']:>3}  {r['terrain_idx']:>3}  {r['name']:<6}  "
              f"{r['topo']:<4}  {r['loop']:<6}  {exp_s:>3}  {opn_s:>4}  "
              f"{r['operator']:<4}  {pol_s:>3}  {r['engine_loop']:<6}")


# ═══════════════════════════════════════════════════════════════════
# 2. CHECK ADJACENT-PAIR PATTERNS
# ═══════════════════════════════════════════════════════════════════

def check_alternation(rows, field, scope="global"):
    """Check if `field` alternates between adjacent steps.
    scope='global' checks all 8 steps.
    scope='within_loop' checks within each 4-step loop separately.
    """
    violations = []
    if scope == "global":
        pairs = [(i, i + 1) for i in range(len(rows) - 1)]
    elif scope == "within_loop":
        pairs = [(i, i + 1) for i in range(3)] + [(i, i + 1) for i in range(4, 7)]
    elif scope == "wrap_within_loop":
        # also wrap: step 3->0 and step 7->4
        pairs = ([(i, i + 1) for i in range(3)] + [(3, 0)]
                 + [(i, i + 1) for i in range(4, 7)] + [(7, 4)])
    else:
        pairs = []

    for a, b in pairs:
        if rows[a][field] == rows[b][field]:
            violations.append({
                "pos_a": a, "pos_b": b,
                "val_a": rows[a][field], "val_b": rows[b][field],
                "name_a": rows[a]["name"], "name_b": rows[b]["name"],
            })
    return violations


def check_no_consecutive_repeat(rows, field, scope="global"):
    """Check that `field` never repeats consecutively."""
    return check_alternation(rows, field, scope)  # same logic for booleans


def check_topo_coverage(rows):
    """Check each 4-step loop visits {Se, Si, Ne, Ni} exactly once."""
    for loop_start, loop_name in [(0, "outer"), (4, "inner")]:
        topos = [rows[i]["topo"] for i in range(loop_start, loop_start + 4)]
        if set(topos) != {"Se", "Si", "Ne", "Ni"}:
            return False, f"{loop_name}: {topos}"
        if len(topos) != len(set(topos)):
            return False, f"{loop_name} has duplicates: {topos}"
    return True, "each loop has {Se,Si,Ne,Ni} exactly once"


def check_topo_dual_coverage(rows):
    """Check each topo appears exactly twice total (once fiber, once base)."""
    from collections import Counter
    topo_loop = [(r["topo"], r["loop"]) for r in rows]
    c = Counter(topo_loop)
    for topo in ["Se", "Si", "Ne", "Ni"]:
        for loop in ["fiber", "base"]:
            if c[(topo, loop)] != 1:
                return False, f"({topo},{loop}) count={c[(topo, loop)]}"
    return True, "each (topo,loop) pair appears exactly once"


# ═══════════════════════════════════════════════════════════════════
# 3. z3 INVARIANT TESTS
# ═══════════════════════════════════════════════════════════════════

def z3_test_alternation_global(field_name, engine_type):
    """Encode: field alternates at every global step. Check SAT against real data."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    vals = [Bool(f'{field_name}_{i}') for i in range(8)]
    # Pin to actual values
    for i, tidx in enumerate(order):
        actual = TERRAINS[tidx][field_name]
        s.add(vals[i] == BoolVal(actual))
    # Constraint: alternation at every adjacent pair
    for i in range(7):
        s.add(vals[i] != vals[i + 1])
    return str(s.check())


def z3_test_alternation_within_loop(field_name, engine_type):
    """Encode: field alternates within each 4-step loop (not across loops)."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    vals = [Bool(f'{field_name}_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = TERRAINS[tidx][field_name]
        s.add(vals[i] == BoolVal(actual))
    # Within-loop alternation only
    for loop_start in [0, 4]:
        for k in range(3):
            a = loop_start + k
            b = loop_start + k + 1
            s.add(vals[a] != vals[b])
    return str(s.check())


def z3_test_alternation_within_loop_wrap(field_name, engine_type):
    """Encode: field alternates within each 4-step loop INCLUDING wrap (step 3->0, 7->4)."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    vals = [Bool(f'{field_name}_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = TERRAINS[tidx][field_name]
        s.add(vals[i] == BoolVal(actual))
    for loop_start in [0, 4]:
        for k in range(4):
            a = loop_start + k
            b = loop_start + ((k + 1) % 4)
            s.add(vals[a] != vals[b])
    return str(s.check())


def z3_test_topo_no_repeat(engine_type):
    """Encode: topo never repeats consecutively (globally)."""
    order = LOOP_STAGE_ORDER[engine_type]
    topo_map = {"Se": 0, "Si": 1, "Ne": 2, "Ni": 3}
    s = Solver()
    vals = [Int(f'topo_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = topo_map[TERRAINS[tidx]["topo"]]
        s.add(vals[i] == IntVal(actual))
    for i in range(7):
        s.add(vals[i] != vals[i + 1])
    return str(s.check())


def z3_test_topo_no_repeat_within_loop(engine_type):
    """Encode: topo never repeats consecutively within each loop."""
    order = LOOP_STAGE_ORDER[engine_type]
    topo_map = {"Se": 0, "Si": 1, "Ne": 2, "Ni": 3}
    s = Solver()
    vals = [Int(f'topo_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = topo_map[TERRAINS[tidx]["topo"]]
        s.add(vals[i] == IntVal(actual))
    for loop_start in [0, 4]:
        for k in range(3):
            a = loop_start + k
            b = loop_start + k + 1
            s.add(vals[a] != vals[b])
    return str(s.check())


def z3_test_topo_coverage_per_loop(engine_type):
    """Encode: each 4-step loop visits all 4 topologies exactly once."""
    order = LOOP_STAGE_ORDER[engine_type]
    topo_map = {"Se": 0, "Si": 1, "Ne": 2, "Ni": 3}
    s = Solver()
    vals = [Int(f'topo_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = topo_map[TERRAINS[tidx]["topo"]]
        s.add(vals[i] == IntVal(actual))
    for loop_start in [0, 4]:
        loop_vals = [vals[loop_start + k] for k in range(4)]
        s.add(Distinct(*loop_vals))
    return str(s.check())


def z3_test_loop_field_constant(engine_type):
    """Encode: 'loop' (fiber/base) is constant within each engine loop."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    vals = [Bool(f'is_fiber_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        actual = TERRAINS[tidx]["loop"] == "fiber"
        s.add(vals[i] == BoolVal(actual))
    # Within each engine loop (positions 0-3 and 4-7), loop type is constant
    for loop_start in [0, 4]:
        for k in range(3):
            a = loop_start + k
            b = loop_start + k + 1
            s.add(vals[a] == vals[b])
    return str(s.check())


def z3_test_expansion_open_xor(engine_type):
    """Encode: expansion XOR open is constant (i.e. expansion == NOT open, or expansion == open)."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    exp_vals = [Bool(f'exp_{i}') for i in range(8)]
    open_vals = [Bool(f'open_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        s.add(exp_vals[i] == BoolVal(TERRAINS[tidx]["expansion"]))
        s.add(open_vals[i] == BoolVal(TERRAINS[tidx]["open"]))
    # Test: is expansion == open at every step? (i.e. they always agree)
    for i in range(8):
        s.add(exp_vals[i] == open_vals[i])
    r1 = str(s.check())

    # Test: is expansion == NOT open at every step?
    s2 = Solver()
    exp_vals2 = [Bool(f'exp2_{i}') for i in range(8)]
    open_vals2 = [Bool(f'open2_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        s2.add(exp_vals2[i] == BoolVal(TERRAINS[tidx]["expansion"]))
        s2.add(open_vals2[i] == BoolVal(TERRAINS[tidx]["open"]))
    for i in range(8):
        s2.add(exp_vals2[i] != open_vals2[i])
    r2 = str(s2.check())

    return {"exp_eq_open": r1, "exp_eq_not_open": r2}


def z3_test_polarity_alternation_within_loop(engine_type):
    """Encode: polarity alternates within each loop."""
    order = LOOP_STAGE_ORDER[engine_type]
    s = Solver()
    vals = [Bool(f'pol_{i}') for i in range(8)]
    for i, tidx in enumerate(order):
        t = TERRAINS[tidx]
        key = (engine_type, t["loop"], t["topo"])
        _, pol = STAGE_OPERATOR_LUT[key]
        s.add(vals[i] == BoolVal(pol))
    for loop_start in [0, 4]:
        for k in range(3):
            a = loop_start + k
            b = loop_start + k + 1
            s.add(vals[a] != vals[b])
    return str(s.check())


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    results = {
        "name": "bc1_fence_investigation",
        "description": "Investigates which alternation fences actually hold for LOOP_STAGE_ORDER traversals",
        "stage_order_type1": [],
        "stage_order_type2": [],
        "alternation_checks": {},
        "z3_invariant_tests": {},
        "true_invariants": [],
        "false_invariants": [],
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
    }

    # ── 1. Build and display tables ──────────────────────────────
    for et in [1, 2]:
        rows = build_stage_table(et)
        print_table(rows, et)
        key = f"stage_order_type{et}"
        # Sanitize for JSON (bools are fine, but be explicit)
        results[key] = [
            {k: (bool(v) if isinstance(v, (bool, int)) and k in ("expansion", "open", "polarity_up") else v)
             for k, v in r.items()}
            for r in rows
        ]

    # ── 2. Check all alternation patterns ────────────────────────
    print("\n=== Alternation Checks ===")
    all_checks = {}

    for et in [1, 2]:
        rows = build_stage_table(et)
        et_key = f"type{et}"
        checks = {}

        # Expansion checks
        for scope in ["global", "within_loop", "wrap_within_loop"]:
            v = check_alternation(rows, "expansion", scope)
            label = f"expansion_{scope}"
            holds = len(v) == 0
            checks[label] = {"violations": len(v), "holds": holds, "details": v}
            print(f"  Type {et} | {label}: violations={len(v)}, holds={holds}")

        # Open checks
        for scope in ["global", "within_loop", "wrap_within_loop"]:
            v = check_alternation(rows, "open", scope)
            label = f"open_{scope}"
            holds = len(v) == 0
            checks[label] = {"violations": len(v), "holds": holds, "details": v}
            print(f"  Type {et} | {label}: violations={len(v)}, holds={holds}")

        # Topo no-repeat
        v = check_no_consecutive_repeat(rows, "topo", "global")
        checks["topo_no_repeat_global"] = {"violations": len(v), "holds": len(v) == 0, "details": v}
        print(f"  Type {et} | topo_no_repeat_global: violations={len(v)}, holds={len(v)==0}")

        v = check_no_consecutive_repeat(rows, "topo", "within_loop")
        checks["topo_no_repeat_within_loop"] = {"violations": len(v), "holds": len(v) == 0, "details": v}
        print(f"  Type {et} | topo_no_repeat_within_loop: violations={len(v)}, holds={len(v)==0}")

        # Topo coverage
        ok, detail = check_topo_coverage(rows)
        checks["topo_coverage_per_loop"] = {"holds": ok, "detail": detail}
        print(f"  Type {et} | topo_coverage_per_loop: holds={ok}")

        # Topo dual coverage
        ok, detail = check_topo_dual_coverage(rows)
        checks["topo_dual_coverage"] = {"holds": ok, "detail": detail}
        print(f"  Type {et} | topo_dual_coverage: holds={ok}")

        # Polarity alternation
        v = check_alternation(rows, "polarity_up", "within_loop")
        checks["polarity_alternates_within_loop"] = {"violations": len(v), "holds": len(v) == 0, "details": v}
        print(f"  Type {et} | polarity_alternates_within_loop: violations={len(v)}, holds={len(v)==0}")

        # Loop field constant within engine loop
        loop_violations = []
        for loop_start, loop_name in [(0, "outer"), (4, "inner")]:
            loop_vals = [rows[i]["loop"] for i in range(loop_start, loop_start + 4)]
            if len(set(loop_vals)) != 1:
                loop_violations.append({"loop": loop_name, "vals": loop_vals})
        checks["loop_constant_within_engine_loop"] = {
            "violations": len(loop_violations), "holds": len(loop_violations) == 0,
            "details": loop_violations,
        }
        print(f"  Type {et} | loop_constant_within_engine_loop: holds={len(loop_violations)==0}")

        all_checks[et_key] = checks

    results["alternation_checks"] = all_checks

    # ── 3. z3 invariant tests ────────────────────────────────────
    print("\n=== z3 Invariant Tests ===")
    z3_results = {}

    for et in [1, 2]:
        et_key = f"type{et}"
        z3_et = {}

        # Expansion alternation
        r = z3_test_alternation_global("expansion", et)
        z3_et["expansion_alternates_global"] = r
        print(f"  Type {et} | expansion_alternates_global: {r}")

        r = z3_test_alternation_within_loop("expansion", et)
        z3_et["expansion_alternates_within_loop"] = r
        print(f"  Type {et} | expansion_alternates_within_loop: {r}")

        r = z3_test_alternation_within_loop_wrap("expansion", et)
        z3_et["expansion_alternates_within_loop_wrap"] = r
        print(f"  Type {et} | expansion_alternates_within_loop_wrap: {r}")

        # Open alternation
        r = z3_test_alternation_global("open", et)
        z3_et["open_alternates_global"] = r
        print(f"  Type {et} | open_alternates_global: {r}")

        r = z3_test_alternation_within_loop("open", et)
        z3_et["open_alternates_within_loop"] = r
        print(f"  Type {et} | open_alternates_within_loop: {r}")

        r = z3_test_alternation_within_loop_wrap("open", et)
        z3_et["open_alternates_within_loop_wrap"] = r
        print(f"  Type {et} | open_alternates_within_loop_wrap: {r}")

        # Topo
        r = z3_test_topo_no_repeat(et)
        z3_et["topo_no_repeat_global"] = r
        print(f"  Type {et} | topo_no_repeat_global: {r}")

        r = z3_test_topo_no_repeat_within_loop(et)
        z3_et["topo_no_repeat_within_loop"] = r
        print(f"  Type {et} | topo_no_repeat_within_loop: {r}")

        r = z3_test_topo_coverage_per_loop(et)
        z3_et["topo_coverage_per_loop"] = r
        print(f"  Type {et} | topo_coverage_per_loop: {r}")

        # Loop constant
        r = z3_test_loop_field_constant(et)
        z3_et["loop_constant_within_engine_loop"] = r
        print(f"  Type {et} | loop_constant_within_engine_loop: {r}")

        # Expansion/open relationship
        r = z3_test_expansion_open_xor(et)
        z3_et["expansion_open_relationship"] = r
        print(f"  Type {et} | expansion_open_relationship: {r}")

        # Polarity alternation
        r = z3_test_polarity_alternation_within_loop(et)
        z3_et["polarity_alternates_within_loop"] = r
        print(f"  Type {et} | polarity_alternates_within_loop: {r}")

        z3_results[et_key] = z3_et

    results["z3_invariant_tests"] = z3_results

    # ── 4. Classify true vs false invariants ─────────────────────
    print("\n=== CLASSIFICATION ===")

    # An invariant is TRUE if it holds (SAT) for BOTH types
    # An invariant is FALSE if it fails (UNSAT) for ANY type
    candidate_invariants = [
        ("expansion_alternates_global", "z3"),
        ("expansion_alternates_within_loop", "z3"),
        ("expansion_alternates_within_loop_wrap", "z3"),
        ("open_alternates_global", "z3"),
        ("open_alternates_within_loop", "z3"),
        ("open_alternates_within_loop_wrap", "z3"),
        ("topo_no_repeat_global", "z3"),
        ("topo_no_repeat_within_loop", "z3"),
        ("topo_coverage_per_loop", "z3"),
        ("loop_constant_within_engine_loop", "z3"),
        ("polarity_alternates_within_loop", "z3"),
    ]

    true_inv = []
    false_inv = []

    for inv_name, source in candidate_invariants:
        t1 = z3_results["type1"].get(inv_name, "missing")
        t2 = z3_results["type2"].get(inv_name, "missing")
        if t1 == "sat" and t2 == "sat":
            true_inv.append(inv_name)
            print(f"  TRUE:  {inv_name}")
        else:
            false_inv.append({"name": inv_name, "type1": t1, "type2": t2})
            print(f"  FALSE: {inv_name} (type1={t1}, type2={t2})")

    # Special: expansion_open_relationship
    for et_key in ["type1", "type2"]:
        rel = z3_results[et_key].get("expansion_open_relationship", {})
        if isinstance(rel, dict):
            for sub_key, sub_val in rel.items():
                label = f"expansion_open_{sub_key}_{et_key}"
                if sub_val == "sat":
                    print(f"  TRUE:  {label}")
                else:
                    print(f"  FALSE: {label}")

    results["true_invariants"] = true_inv
    results["false_invariants"] = false_inv

    # ── 5. Summary ───────────────────────────────────────────────
    print("\n=== SUMMARY ===")
    print(f"  True invariants  ({len(true_inv)}): {true_inv}")
    print(f"  False invariants ({len(false_inv)}): {[f['name'] for f in false_inv]}")

    if "expansion_alternates_global" in [f["name"] for f in false_inv]:
        print("\n  ** CONFIRMED: 'expansion alternates globally' is FALSE **")
        print("     The BC1 fence as originally stated ('expansion alternates') is wrong.")
        # Identify what IS true
        if "open_alternates_within_loop" in true_inv:
            print("     ACTUAL FENCE: 'open alternates within each loop' is the true constraint.")
        if "expansion_alternates_within_loop" in true_inv:
            print("     ALSO TRUE: 'expansion alternates within each loop'.")

    # ── Write output ─────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    out_path = os.path.join(out_dir, "bc1_fence_investigation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Written to: {out_path}")


if __name__ == "__main__":
    main()
