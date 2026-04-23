#!/usr/bin/env python3
"""
z3 Fence-Removal Exhaustive Negative Battery
=============================================
For EVERY fence in the system (15 total), remove it and prove that a
violation state becomes satisfiable. This tests every fence is load-bearing.

Also tests pair-wise fence removal to find jointly-necessary pairs.

Output: a2_state/sim_results/z3_fence_exhaustive_negatives_results.json
"""

import sys
import os
import json
import itertools
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from z3 import (
    Solver, Bool, Int, IntVal, BoolVal, sat, unsat,
    And, Or, Not, Distinct, If, Implies, Real, RealVal,
)
from engine_core import TERRAINS, STAGE_OPERATOR_LUT, LOOP_STAGE_ORDER, LOOP_GRAMMAR


# =====================================================================
# SIM CONTRACT METADATA
# =====================================================================

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- no autograd layer; pure SMT fence-removal battery"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph message-passing layer here"},
    "z3":        {"tried": True,  "used": True,  "reason": "load_bearing: SAT/UNSAT verdicts for every fence-removal and pairwise-removal test in the exhaustive battery"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 alone covers the SAT/UNSAT battery"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- fence encodings use z3 primitives directly"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer here"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry layer here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant network layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph needed for fence battery"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology here"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}


# ═════════════════════════════════════════════════════════════════════
# UTILITY
# ═════════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert z3/numpy types to JSON-safe Python types."""
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if hasattr(obj, 'sexpr'):
        s = str(obj)
        if s == 'True':
            return True
        if s == 'False':
            return False
        return s
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float, str)):
        return obj
    if obj is None:
        return obj
    return str(obj)


# ═════════════════════════════════════════════════════════════════════
# TERRAIN DATA EXTRACTION
# ═════════════════════════════════════════════════════════════════════

TOPO_MAP = {"Se": 0, "Si": 1, "Ne": 2, "Ni": 3}
LOOP_MAP = {"fiber": 0, "base": 1}
OP_MAP   = {"Ti": 0, "Fe": 1, "Te": 2, "Fi": 3}
N_TERRAINS = len(TERRAINS)  # 8
N_OPS = 4
N_STEPS = 8  # per engine type


def get_terrain_data():
    """Extract all terrain properties as plain lists indexed by terrain index."""
    names      = [t["name"] for t in TERRAINS]
    topos      = [TOPO_MAP[t["topo"]] for t in TERRAINS]
    loops      = [LOOP_MAP[t["loop"]] for t in TERRAINS]
    expansions = [t["expansion"] for t in TERRAINS]
    opens      = [t["open"] for t in TERRAINS]
    return names, topos, loops, expansions, opens


def get_operator_assignment(engine_type):
    """For each terrain index, get (op_index, polarity) for given engine type."""
    ops = []
    pols = []
    for tidx in range(N_TERRAINS):
        t = TERRAINS[tidx]
        key = (engine_type, t["loop"], t["topo"])
        op_name, pol = STAGE_OPERATOR_LUT[key]
        ops.append(OP_MAP[op_name])
        pols.append(pol)
    return ops, pols


def get_stage_order(engine_type):
    return LOOP_STAGE_ORDER[engine_type]


# ═════════════════════════════════════════════════════════════════════
# VARIABLE FACTORY
# ═════════════════════════════════════════════════════════════════════
# Global counter ensures unique z3 variable names across solver instances.
_var_counter = [0]

def make_vars(engine_type):
    """Create z3 variables for an 8-step engine traversal."""
    _var_counter[0] += 1
    p = f"v{_var_counter[0]}"
    et = engine_type
    v = {
        # Per-step variables (indexed by step position in traversal)
        "open":      [Bool(f'{p}_open_{et}_{i}') for i in range(N_STEPS)],
        "topo":      [Int(f'{p}_topo_{et}_{i}') for i in range(N_STEPS)],
        "loop":      [Int(f'{p}_loop_{et}_{i}') for i in range(N_STEPS)],
        "expansion": [Bool(f'{p}_exp_{et}_{i}') for i in range(N_STEPS)],
        # Per-terrain variables (indexed by terrain index 0-7)
        "op":        [Int(f'{p}_op_{et}_{i}') for i in range(N_TERRAINS)],
        "t_exp":     [Bool(f'{p}_texp_{et}_{i}') for i in range(N_TERRAINS)],
        # Structural counts
        "n_terrains": Int(f'{p}_nterr_{et}'),
        "n_ops":      Int(f'{p}_nops_{et}'),
        # Weyl chirality Bloch vectors
        "weyl_Lx":   Real(f'{p}_wLx_{et}'),
        "weyl_Ly":   Real(f'{p}_wLy_{et}'),
        "weyl_Lz":   Real(f'{p}_wLz_{et}'),
        "weyl_Rx":   Real(f'{p}_wRx_{et}'),
        "weyl_Ry":   Real(f'{p}_wRy_{et}'),
        "weyl_Rz":   Real(f'{p}_wRz_{et}'),
        # Unique prefix for auxiliary vars (counts etc)
        "_prefix": p,
    }
    return v


def domain_constraints(v):
    """Basic domain bounds for free variables."""
    c = []
    for i in range(N_STEPS):
        c.extend([v["topo"][i] >= 0, v["topo"][i] <= 3])
        c.extend([v["loop"][i] >= 0, v["loop"][i] <= 1])
    for tidx in range(N_TERRAINS):
        c.extend([v["op"][tidx] >= 0, v["op"][tidx] <= 3])
    for comp in ["weyl_Lx", "weyl_Ly", "weyl_Lz", "weyl_Rx", "weyl_Ry", "weyl_Rz"]:
        c.extend([v[comp] >= -1, v[comp] <= 1])
    c.extend([v["n_terrains"] >= 1, v["n_terrains"] <= 100])
    c.extend([v["n_ops"] >= 1, v["n_ops"] <= 100])
    return c


def pin_to_real_data(v, engine_type):
    """Pin z3 variables to the actual engine data. Returns constraints."""
    constraints = []
    order = get_stage_order(engine_type)
    _, topos, loops, expansions, opens = get_terrain_data()
    ops, pols = get_operator_assignment(engine_type)

    for i, tidx in enumerate(order):
        constraints.append(v["open"][i] == BoolVal(opens[tidx]))
        constraints.append(v["topo"][i] == IntVal(topos[tidx]))
        constraints.append(v["loop"][i] == IntVal(loops[tidx]))
        constraints.append(v["expansion"][i] == BoolVal(expansions[tidx]))

    for tidx in range(N_TERRAINS):
        constraints.append(v["op"][tidx] == IntVal(ops[tidx]))
        constraints.append(v["t_exp"][tidx] == BoolVal(expansions[tidx]))

    constraints.append(v["n_terrains"] == IntVal(N_TERRAINS))
    constraints.append(v["n_ops"] == IntVal(N_OPS))

    return constraints


# ═════════════════════════════════════════════════════════════════════
# FENCE DEFINITIONS (15 fences)
# ═════════════════════════════════════════════════════════════════════

def fence_1_open_alternates(v, _et):
    """Fence 1: open/closed alternates at every step within each loop."""
    c = []
    for loop_start in [0, 4]:
        for k in range(3):
            c.append(v["open"][loop_start + k] != v["open"][loop_start + k + 1])
    return c


def fence_2_no_topo_repeat(v, _et):
    """Fence 2: topology never repeats consecutively within each loop."""
    c = []
    for loop_start in [0, 4]:
        for k in range(3):
            c.append(v["topo"][loop_start + k] != v["topo"][loop_start + k + 1])
    return c


def fence_3_topo_coverage(v, _et):
    """Fence 3: each loop visits {Se,Si,Ne,Ni} exactly once."""
    c = []
    for loop_start in [0, 4]:
        loop_topos = [v["topo"][loop_start + k] for k in range(4)]
        c.append(Distinct(*loop_topos))
    return c


def fence_4_loop_constant(v, _et):
    """Fence 4: fiber/base is constant within each engine loop."""
    c = []
    for loop_start in [0, 4]:
        for k in range(3):
            c.append(v["loop"][loop_start + k] == v["loop"][loop_start + k + 1])
    return c


def fence_5_expansion_balanced(v, _et):
    """Fence 5: expansion is balanced -- exactly 2 True and 2 False per loop."""
    c = []
    p = v["_prefix"]
    for loop_idx, loop_start in enumerate([0, 4]):
        count_true = Int(f'{p}_f5_ct_{loop_idx}')
        c.append(count_true == sum([If(v["expansion"][loop_start + k], 1, 0)
                                    for k in range(4)]))
        c.append(count_true == 2)
    return c


def fence_6_one_op_per_terrain(v, _et):
    """Fence 6: each terrain operator is in range [0,3]."""
    c = []
    for tidx in range(N_TERRAINS):
        c.extend([v["op"][tidx] >= 0, v["op"][tidx] <= 3])
    return c


def fence_7_op_appears_twice(v, _et):
    """Fence 7: each operator appears exactly twice across 8 terrains."""
    c = []
    p = v["_prefix"]
    for op_val in range(N_OPS):
        count = Int(f'{p}_f7_c_{op_val}')
        c.append(count == sum([If(v["op"][tidx] == IntVal(op_val), 1, 0)
                               for tidx in range(N_TERRAINS)]))
        c.append(count == 2)
    return c


def fence_8_f_kernel_expansion(v, _et):
    """Fence 8: F-kernel operator-expansion coupling.
    Fe (1) only on expansion=False terrains.
    Fi (3) only on expansion=True terrains."""
    c = []
    for tidx in range(N_TERRAINS):
        # Fe(1) => expansion=False
        c.append(Implies(v["op"][tidx] == 1, v["t_exp"][tidx] == BoolVal(False)))
        # Fi(3) => expansion=True
        c.append(Implies(v["op"][tidx] == 3, v["t_exp"][tidx] == BoolVal(True)))
    return c


def fence_9_t_kernel_expansion(v, _et):
    """Fence 9: T-kernel operator-expansion coupling.
    Ti (0) only on expansion=True terrains.
    Te (2) only on expansion=False terrains."""
    c = []
    for tidx in range(N_TERRAINS):
        # Ti(0) => expansion=True
        c.append(Implies(v["op"][tidx] == 0, v["t_exp"][tidx] == BoolVal(True)))
        # Te(2) => expansion=False
        c.append(Implies(v["op"][tidx] == 2, v["t_exp"][tidx] == BoolVal(False)))
    return c


def fence_10_type_determines_ops(v, engine_type):
    """Fence 10: operator assignment is fully determined by engine type."""
    c = []
    ops, _ = get_operator_assignment(engine_type)
    for tidx in range(N_TERRAINS):
        c.append(v["op"][tidx] == IntVal(ops[tidx]))
    return c


def fence_11_eight_terrains(v, _et):
    """Fence 11: exactly 8 terrains total."""
    return [v["n_terrains"] == 8]


def fence_12_four_operators(v, _et):
    """Fence 12: exactly 4 operators."""
    return [v["n_ops"] == 4]


def fence_13_stage_cycle(v, _et):
    """Fence 13: stage order wraps -- last topo differs from first, per loop."""
    c = []
    for loop_start in [0, 4]:
        c.append(v["topo"][loop_start + 3] != v["topo"][loop_start])
    return c


def fence_14_no_self_loops(v, _et):
    """Fence 14: no consecutive identical topos across ALL 8 steps (including cross-loop)."""
    c = []
    for i in range(N_STEPS - 1):
        c.append(v["topo"][i] != v["topo"][i + 1])
    return c


def fence_15_weyl_chirality(v, _et):
    """Fence 15: Weyl chirality -- L/R Bloch vectors anti-aligned (dot < 0)."""
    dot = (v["weyl_Lx"] * v["weyl_Rx"] +
           v["weyl_Ly"] * v["weyl_Ry"] +
           v["weyl_Lz"] * v["weyl_Rz"])
    return [dot < 0]


# ═════════════════════════════════════════════════════════════════════
# FENCE REGISTRY
# ═════════════════════════════════════════════════════════════════════

FENCE_REGISTRY = {
    1:  ("open_alternates",        "open/closed alternates at every step within each loop",
         fence_1_open_alternates),
    2:  ("no_topo_repeat",         "topology never repeats consecutively within each loop",
         fence_2_no_topo_repeat),
    3:  ("topo_coverage",          "each loop visits {Se,Si,Ne,Ni} exactly once",
         fence_3_topo_coverage),
    4:  ("loop_constant",          "fiber/base is constant within each engine loop",
         fence_4_loop_constant),
    5:  ("expansion_balanced",     "expansion exactly 2 True and 2 False per loop",
         fence_5_expansion_balanced),
    6:  ("one_op_per_terrain",     "each terrain operator in range [0,3]",
         fence_6_one_op_per_terrain),
    7:  ("op_appears_twice",       "each operator appears exactly twice per engine type",
         fence_7_op_appears_twice),
    8:  ("f_kernel_expansion",     "Fe on expansion=False, Fi on expansion=True terrains",
         fence_8_f_kernel_expansion),
    9:  ("t_kernel_expansion",     "Ti on expansion=True, Te on expansion=False terrains",
         fence_9_t_kernel_expansion),
    10: ("type_determines_ops",    "operator assignment fully determined by engine type",
         fence_10_type_determines_ops),
    11: ("eight_terrains",         "exactly 8 terrains total",
         fence_11_eight_terrains),
    12: ("four_operators",         "exactly 4 operators",
         fence_12_four_operators),
    13: ("stage_cycle",            "stage order wraps (last != first per loop)",
         fence_13_stage_cycle),
    14: ("no_self_loops",          "no consecutive identical topos across all 8 steps",
         fence_14_no_self_loops),
    15: ("weyl_chirality",         "Weyl chirality: L/R anti-aligned (dot < 0)",
         fence_15_weyl_chirality),
}


def get_all_fence_constraints(v, engine_type, exclude=None):
    """Get constraints for all fences, optionally excluding some."""
    if exclude is None:
        exclude = set()
    c = []
    for fid, (_, _, fn) in FENCE_REGISTRY.items():
        if fid in exclude:
            continue
        c.extend(fn(v, engine_type))
    return c


# ═════════════════════════════════════════════════════════════════════
# VIOLATION CONSTRUCTORS
# ═════════════════════════════════════════════════════════════════════

def violation_1(v, _et):
    """Two consecutive open=True within first loop."""
    return [v["open"][0] == BoolVal(True), v["open"][1] == BoolVal(True)]


def violation_2(v, _et):
    """Two consecutive same topology within first loop."""
    return [v["topo"][0] == v["topo"][1]]


def violation_3(v, _et):
    """First loop visits Se twice, skips Ni."""
    return [
        v["topo"][0] == IntVal(TOPO_MAP["Se"]),
        v["topo"][1] == IntVal(TOPO_MAP["Se"]),
        v["topo"][2] == IntVal(TOPO_MAP["Ne"]),
        v["topo"][3] == IntVal(TOPO_MAP["Si"]),
    ]


def violation_4(v, _et):
    """Mixed fiber/base within first engine loop."""
    return [v["loop"][0] == IntVal(0), v["loop"][1] == IntVal(1)]


def violation_5(v, _et):
    """Expansion has 3 True in first loop (not balanced)."""
    p = v["_prefix"]
    ct = Int(f'{p}_v5_ct')
    return [
        ct == sum([If(v["expansion"][k], 1, 0) for k in range(4)]),
        ct == 3,
    ]


def violation_6(v, _et):
    """Terrain 0 has operator value 5 (outside range)."""
    return [v["op"][0] == IntVal(5)]


def violation_7(v, _et):
    """Ti(0) appears 3 times."""
    p = v["_prefix"]
    ct = Int(f'{p}_v7_ct')
    return [
        ct == sum([If(v["op"][tidx] == IntVal(0), 1, 0) for tidx in range(N_TERRAINS)]),
        ct == 3,
    ]


def violation_8(v, _et):
    """Fe(1) on an expansion=True terrain (violates Fe->exp=False)."""
    return [v["op"][0] == IntVal(1), v["t_exp"][0] == BoolVal(True)]


def violation_9(v, _et):
    """Ti(0) on an expansion=False terrain (violates Ti->exp=True)."""
    return [v["op"][0] == IntVal(0), v["t_exp"][0] == BoolVal(False)]


def violation_10(v, engine_type):
    """Operator assignment from the OTHER engine type."""
    other_type = 2 if engine_type == 1 else 1
    other_ops, _ = get_operator_assignment(other_type)
    return [v["op"][tidx] == IntVal(other_ops[tidx]) for tidx in range(N_TERRAINS)]


def violation_11(v, _et):
    """Terrain count = 6."""
    return [v["n_terrains"] == IntVal(6)]


def violation_12(v, _et):
    """Operator count = 5."""
    return [v["n_ops"] == IntVal(5)]


def violation_13(v, _et):
    """Last topo equals first in outer loop (breaks cycle)."""
    return [v["topo"][3] == v["topo"][0]]


def violation_14(v, _et):
    """Consecutive identical topos at cross-loop boundary (step 3 = step 4)."""
    return [v["topo"][3] == v["topo"][4]]


def violation_15(v, _et):
    """L and R Bloch vectors aligned (dot > 0)."""
    dot = (v["weyl_Lx"] * v["weyl_Rx"] +
           v["weyl_Ly"] * v["weyl_Ry"] +
           v["weyl_Lz"] * v["weyl_Rz"])
    return [dot > 0]


VIOLATION_REGISTRY = {
    1:  ("two consecutive open=True",                  violation_1),
    2:  ("two consecutive same topology",              violation_2),
    3:  ("loop visits Se twice, skips Ni",             violation_3),
    4:  ("mixed fiber/base in one engine loop",        violation_4),
    5:  ("expansion 3 True in one loop (unbalanced)",  violation_5),
    6:  ("operator value 5 (outside 0-3)",             violation_6),
    7:  ("Ti appears 3 times (not exactly 2)",         violation_7),
    8:  ("Fe on expansion=True terrain",               violation_8),
    9:  ("Ti on expansion=False terrain",              violation_9),
    10: ("ops from wrong engine type",                 violation_10),
    11: ("terrain count = 6",                          violation_11),
    12: ("operator count = 5",                         violation_12),
    13: ("last topo = first in outer loop",            violation_13),
    14: ("step 3 topo = step 4 topo",                  violation_14),
    15: ("L/R Bloch vectors aligned (dot > 0)",        violation_15),
}


# ═════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═════════════════════════════════════════════════════════════════════

def test_single_fence(fence_id, engine_type):
    """
    For fence_id:
      Test A: all fences + real data => SAT (consistency)
      Test B: all fences EXCEPT fence_id + violation => SAT? (violation reachable without fence)
      Test C: all fences INCLUDING fence_id + violation => UNSAT? (fence blocks violation)

    load_bearing = (B is SAT) and (C is UNSAT)
    """
    viol_desc, viol_fn = VIOLATION_REGISTRY[fence_id]

    # --- Test A: full system consistency ---
    va = make_vars(engine_type)
    sa = Solver()
    sa.add(pin_to_real_data(va, engine_type))
    sa.add(get_all_fence_constraints(va, engine_type))
    test_a = str(sa.check())

    # --- Test B: remove fence, add violation, free variables ---
    vb = make_vars(engine_type)
    sb = Solver()
    sb.add(domain_constraints(vb))
    sb.add(get_all_fence_constraints(vb, engine_type, exclude={fence_id}))
    sb.add(viol_fn(vb, engine_type))
    test_b_result = sb.check()
    test_b = str(test_b_result)
    violation_reachable = (test_b_result == sat)

    # --- Test C: all fences + violation, free variables ---
    vc = make_vars(engine_type)
    sc = Solver()
    sc.add(domain_constraints(vc))
    sc.add(get_all_fence_constraints(vc, engine_type))
    sc.add(viol_fn(vc, engine_type))
    test_c_result = sc.check()
    test_c = str(test_c_result)
    violation_blocked = (test_c_result == unsat)

    load_bearing = violation_reachable and violation_blocked

    return {
        "full_system_sat": test_a,
        "without_fence_violation_reachable": violation_reachable,
        "with_fence_violation_blocked": test_c,
        "load_bearing": load_bearing,
    }


def test_pair_removal(fid_a, fid_b, engine_type):
    """Remove fences A and B. Add both violations. Check SAT."""
    _, viol_a = VIOLATION_REGISTRY[fid_a]
    _, viol_b = VIOLATION_REGISTRY[fid_b]

    v = make_vars(engine_type)
    s = Solver()
    s.add(domain_constraints(v))
    s.add(get_all_fence_constraints(v, engine_type, exclude={fid_a, fid_b}))
    s.add(viol_a(v, engine_type))
    s.add(viol_b(v, engine_type))

    result = s.check()
    return result == sat


# ═════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("z3 FENCE-REMOVAL EXHAUSTIVE NEGATIVE BATTERY")
    print("=" * 70)

    results = {
        "name": "z3_fence_exhaustive_negatives",
        "total_fences": 15,
        "single_removal_tests": {},
        "pair_removal_tests": {},
        "summary": {
            "load_bearing_fences": [],
            "redundant_fences": [],
            "jointly_necessary_pairs": [],
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
    }

    # ── PHASE 1: Full system consistency ────────────────────────────
    print("\n[Phase 1] Full system consistency check...")
    for et in [1, 2]:
        v = make_vars(et)
        s = Solver()
        s.add(pin_to_real_data(v, et))
        s.add(get_all_fence_constraints(v, et))
        r = s.check()
        print(f"  Engine Type {et}: all 15 fences + real data = {r}")
        if r != sat:
            # Diagnose which fence breaks it
            print("  DIAGNOSING: testing each fence individually against real data...")
            for fid in sorted(FENCE_REGISTRY.keys()):
                vd = make_vars(et)
                sd = Solver()
                sd.add(pin_to_real_data(vd, et))
                sd.add(FENCE_REGISTRY[fid][2](vd, et))
                rd = sd.check()
                tag = "OK" if rd == sat else "** CONFLICT **"
                print(f"    Fence {fid:2d} ({FENCE_REGISTRY[fid][0]}): {rd} {tag}")
            raise SystemExit(f"Full system UNSAT for engine type {et}")

    # ── PHASE 2: Single fence removal ──────────────────────────────
    print("\n[Phase 2] Single fence removal tests...")

    load_bearing = []
    redundant = []

    for fid in sorted(FENCE_REGISTRY.keys()):
        fname, fdesc, _ = FENCE_REGISTRY[fid]
        viol_desc, _ = VIOLATION_REGISTRY[fid]
        print(f"\n  Fence {fid:2d} ({fname}): {fdesc}")

        r1 = test_single_fence(fid, engine_type=1)
        r2 = test_single_fence(fid, engine_type=2)

        combined_lb = r1["load_bearing"] or r2["load_bearing"]

        entry = {
            "description": fdesc,
            "violation_description": viol_desc,
            "type1": {
                "full_system_sat": r1["full_system_sat"],
                "without_fence_violation_reachable": r1["without_fence_violation_reachable"],
                "with_fence_violation_blocked": r1["with_fence_violation_blocked"],
                "load_bearing": r1["load_bearing"],
            },
            "type2": {
                "full_system_sat": r2["full_system_sat"],
                "without_fence_violation_reachable": r2["without_fence_violation_reachable"],
                "with_fence_violation_blocked": r2["with_fence_violation_blocked"],
                "load_bearing": r2["load_bearing"],
            },
            "load_bearing": combined_lb,
        }

        key = f"fence_{fid}_{fname}"
        results["single_removal_tests"][key] = entry

        status = "LOAD-BEARING" if combined_lb else "REDUNDANT"
        print(f"    T1: reach={r1['without_fence_violation_reachable']}, "
              f"blocked={r1['with_fence_violation_blocked']}, lb={r1['load_bearing']}")
        print(f"    T2: reach={r2['without_fence_violation_reachable']}, "
              f"blocked={r2['with_fence_violation_blocked']}, lb={r2['load_bearing']}")
        print(f"    --> {status}")

        if combined_lb:
            load_bearing.append(key)
        else:
            redundant.append(key)

    results["summary"]["load_bearing_fences"] = load_bearing
    results["summary"]["redundant_fences"] = redundant

    # ── PHASE 3: Pair removal ──────────────────────────────────────
    print("\n[Phase 3] Pair fence removal tests...")

    jointly_necessary = []
    pair_count = 0

    for fid_a, fid_b in itertools.combinations(sorted(FENCE_REGISTRY.keys()), 2):
        combined_reachable = test_pair_removal(fid_a, fid_b, engine_type=1)

        single_a_key = f"fence_{fid_a}_{FENCE_REGISTRY[fid_a][0]}"
        single_b_key = f"fence_{fid_b}_{FENCE_REGISTRY[fid_b][0]}"
        single_a_reach = results["single_removal_tests"].get(
            single_a_key, {}).get("type1", {}).get("without_fence_violation_reachable", False)
        single_b_reach = results["single_removal_tests"].get(
            single_b_key, {}).get("type1", {}).get("without_fence_violation_reachable", False)

        # Jointly necessary = combined works but neither single did
        extra = combined_reachable and not single_a_reach and not single_b_reach

        pair_key = f"fence_{fid_a}_AND_{fid_b}"
        results["pair_removal_tests"][pair_key] = {
            "combined_violation_reachable": combined_reachable,
            "extra_violations_vs_single": extra,
            "fence_a": FENCE_REGISTRY[fid_a][0],
            "fence_b": FENCE_REGISTRY[fid_b][0],
        }

        if extra:
            jointly_necessary.append(pair_key)

        pair_count += 1
        if pair_count % 20 == 0:
            print(f"    ... tested {pair_count} pairs")

    print(f"  Total pairs tested: {pair_count}")
    results["summary"]["jointly_necessary_pairs"] = jointly_necessary

    # ── PHASE 4: Summary ───────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total fences:           {results['total_fences']}")
    print(f"  Load-bearing:           {len(load_bearing)}")
    for f in load_bearing:
        print(f"    + {f}")
    print(f"  Redundant/tautological: {len(redundant)}")
    for f in redundant:
        print(f"    - {f}")
    print(f"  Jointly necessary pairs: {len(jointly_necessary)}")
    for p in jointly_necessary:
        print(f"    * {p}")

    # ── Write output ───────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "z3_fence_exhaustive_negatives_results.json")

    with open(out_path, "w") as f:
        json.dump(sanitize(results), f, indent=2, default=str)
    print(f"\n  Written to: {out_path}")


if __name__ == "__main__":
    main()
