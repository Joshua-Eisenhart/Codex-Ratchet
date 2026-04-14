#!/usr/bin/env python3
"""
sim_L11_placement_admissibility.py

L11 (Placement law: terrain / operator / loop assignment) shell-local sim.

Claim tested (shell-local, not coupling):
  A placement assignment P: Operator -> (Terrain, Loop) is admissible iff
    (a) each operator is placed on exactly one terrain stratum
        (inner torus / Clifford torus / outer torus),
    (b) each operator is placed on exactly one loop class
        (fiber-loop or base-loop),
    (c) a Type-1 operator (density-stationary) is placed on a stationary
        loop (fiber) and a Type-2 operator (density-traversing) is placed
        on a traversing loop (base),
    (d) chirality-sensitive operators land on a chirality-carrying stratum
        (Clifford torus), not on the degenerate inner/outer poles.

Structural admissibility is proven via z3 (load_bearing): we SAT-check a
positive model and UNSAT-check each negative (rule violation). Classical
numeric cross-check is decorative.

Classification: classical_baseline (shell-local placement law; no torch
tensors required for the admissibility claim).
"""

import json
import os
import numpy as np

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

# --- tool availability probes ---
try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    HAVE_Z3 = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    HAVE_Z3 = False

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    import rustworkx as rx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    HAVE_RX = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"
    HAVE_RX = False


# =====================================================================
# PLACEMENT DOMAIN (shell-local)
# =====================================================================
# Terrain strata on the Hopf carrier (L5/L6):
#   0 = inner torus (degenerate, no chirality)
#   1 = Clifford torus (chirality carrier)
#   2 = outer torus (degenerate, no chirality)
# Loop classes (L9):
#   0 = fiber (density-stationary)
#   1 = base (density-traversing)
# Operator types (L10):
#   1 = Type-1 stationary
#   2 = Type-2 traversing
# Chirality-sensitive flag (L7/L8):
#   True  => Weyl-resolved operator (needs Clifford torus)
#   False => density-only operator

OPS = [
    # (name, type, chiral_sensitive)
    ("O_fib_stat",     1, False),
    ("O_base_trav",    2, False),
    ("O_weyl_stat",    1, True),
    ("O_weyl_trav",    2, True),
]


def z3_admissible(placements):
    """placements: list of (op_idx, terrain, loop) tuples to test as a model.

    Returns (is_sat, reason). Encodes L11 admissibility rules as constraints
    and asks z3 whether the given assignment satisfies them.
    """
    if not HAVE_Z3:
        return None, "z3 unavailable"

    s = z3.Solver()
    terrain_vars = [z3.Int(f"t_{i}") for i in range(len(OPS))]
    loop_vars    = [z3.Int(f"l_{i}") for i in range(len(OPS))]

    for i, (_, typ, chir) in enumerate(OPS):
        t, l = terrain_vars[i], loop_vars[i]
        # (a) exactly one terrain in {0,1,2}
        s.add(z3.Or(t == 0, t == 1, t == 2))
        # (b) exactly one loop in {0,1}
        s.add(z3.Or(l == 0, l == 1))
        # (c) type <-> loop: Type-1 -> fiber(0), Type-2 -> base(1)
        if typ == 1:
            s.add(l == 0)
        else:
            s.add(l == 1)
        # (d) chirality-sensitive operators live on Clifford torus (1)
        if chir:
            s.add(t == 1)

    # pin the candidate placement
    for (i, t_val, l_val) in placements:
        s.add(terrain_vars[i] == t_val)
        s.add(loop_vars[i] == l_val)

    result = s.check()
    return result == z3.sat, str(result)


def classical_admissible(placements):
    """Pure-python check mirroring the z3 constraints (cross-check)."""
    placed = {i: (t, l) for (i, t, l) in placements}
    for i, (_, typ, chir) in enumerate(OPS):
        if i not in placed:
            continue
        t, l = placed[i]
        if t not in (0, 1, 2):
            return False, f"op {i} terrain {t} not in {{0,1,2}}"
        if l not in (0, 1):
            return False, f"op {i} loop {l} not in {{0,1}}"
        if typ == 1 and l != 0:
            return False, f"op {i} Type-1 but loop={l} (not fiber)"
        if typ == 2 and l != 1:
            return False, f"op {i} Type-2 but loop={l} (not base)"
        if chir and t != 1:
            return False, f"op {i} chiral-sensitive but terrain={t} (not Clifford)"
    return True, "ok"


# =====================================================================
# POSITIVE TESTS
# =====================================================================
def run_positive_tests():
    results = {}

    # Canonical admitted placement:
    #   O_fib_stat  -> (inner, fiber)
    #   O_base_trav -> (outer, base)
    #   O_weyl_stat -> (Clifford, fiber)
    #   O_weyl_trav -> (Clifford, base)
    canonical = [(0, 0, 0), (1, 2, 1), (2, 1, 0), (3, 1, 1)]
    z3_ok, z3_msg = z3_admissible(canonical)
    cl_ok, cl_msg = classical_admissible(canonical)
    results["canonical_placement"] = {
        "z3_sat": z3_ok, "z3_msg": z3_msg,
        "classical_ok": cl_ok, "classical_msg": cl_msg,
        "passed": bool(z3_ok) and cl_ok,
    }

    # Alternative admitted placement (non-chiral ops relocated to Clifford):
    alt = [(0, 1, 0), (1, 1, 1), (2, 1, 0), (3, 1, 1)]
    z3_ok2, _ = z3_admissible(alt)
    cl_ok2, _ = classical_admissible(alt)
    results["alt_all_clifford"] = {
        "z3_sat": z3_ok2, "classical_ok": cl_ok2,
        "passed": bool(z3_ok2) and cl_ok2,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================
def run_negative_tests():
    results = {}

    # N1: Type-1 placed on base (loop/type mismatch) -> must be UNSAT
    bad_type_loop = [(0, 0, 1)]  # O_fib_stat on base
    z3_ok, z3_msg = z3_admissible(bad_type_loop)
    cl_ok, cl_msg = classical_admissible(bad_type_loop)
    results["neg_type1_on_base"] = {
        "z3_sat": z3_ok, "z3_msg": z3_msg,
        "classical_ok": cl_ok, "classical_msg": cl_msg,
        "passed": (z3_ok is False) and (cl_ok is False),
    }

    # N2: Chiral op placed on inner torus -> must be UNSAT
    bad_chir = [(2, 0, 0)]  # O_weyl_stat on inner
    z3_ok, z3_msg = z3_admissible(bad_chir)
    cl_ok, _ = classical_admissible(bad_chir)
    results["neg_chiral_on_inner"] = {
        "z3_sat": z3_ok, "z3_msg": z3_msg,
        "classical_ok": cl_ok,
        "passed": (z3_ok is False) and (cl_ok is False),
    }

    # N3: Type-2 placed on fiber -> must be UNSAT
    bad_t2 = [(1, 2, 0)]
    z3_ok, _ = z3_admissible(bad_t2)
    cl_ok, _ = classical_admissible(bad_t2)
    results["neg_type2_on_fiber"] = {
        "z3_sat": z3_ok, "classical_ok": cl_ok,
        "passed": (z3_ok is False) and (cl_ok is False),
    }

    # N4: Chiral op placed on outer torus -> must be UNSAT
    bad_chir2 = [(3, 2, 1)]
    z3_ok, _ = z3_admissible(bad_chir2)
    cl_ok, _ = classical_admissible(bad_chir2)
    results["neg_chiral_on_outer"] = {
        "z3_sat": z3_ok, "classical_ok": cl_ok,
        "passed": (z3_ok is False) and (cl_ok is False),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================
def run_boundary_tests():
    results = {}

    # B1: non-chiral op on Clifford torus is allowed (chirality-agnostic
    # operator may live anywhere terrain-legal).
    boundary = [(0, 1, 0)]  # O_fib_stat on Clifford, fiber
    z3_ok, _ = z3_admissible(boundary)
    cl_ok, _ = classical_admissible(boundary)
    results["bnd_nonchiral_on_clifford"] = {
        "z3_sat": z3_ok, "classical_ok": cl_ok,
        "passed": bool(z3_ok) and cl_ok,
    }

    # B2: out-of-range terrain index (3) -> must be UNSAT
    bad_terrain = [(0, 3, 0)]
    z3_ok, _ = z3_admissible(bad_terrain)
    cl_ok, _ = classical_admissible(bad_terrain)
    results["bnd_terrain_out_of_range"] = {
        "z3_sat": z3_ok, "classical_ok": cl_ok,
        "passed": (z3_ok is False) and (cl_ok is False),
    }

    # B3: empty placement (no ops pinned) -> z3 should still find a model
    # (the rules are satisfiable in the abstract).
    z3_ok, _ = z3_admissible([])
    results["bnd_empty_placement_satisfiable"] = {
        "z3_sat": z3_ok,
        "passed": bool(z3_ok),
    }

    # B4: rustworkx structural cross-check -- placement graph has 4 ops,
    # 3 terrain strata, 2 loop classes; admissibility relation must match
    # the z3 model count for a small exhaustive sweep.
    count_admitted = 0
    for t0 in range(3):
        for t1 in range(3):
            for t2 in range(3):
                for t3 in range(3):
                    for l0 in range(2):
                        for l1 in range(2):
                            for l2 in range(2):
                                for l3 in range(2):
                                    cand = [(0, t0, l0), (1, t1, l1),
                                            (2, t2, l2), (3, t3, l3)]
                                    ok, _ = classical_admissible(cand)
                                    if ok:
                                        count_admitted += 1
    # Expected: type/loop forced (1 choice each), chiral ops forced to t=1,
    # non-chiral ops free over 3 terrains -> 3 * 3 = 9 admitted models.
    expected = 9
    results["bnd_enumeration_count"] = {
        "admitted": count_admitted,
        "expected": expected,
        "passed": count_admitted == expected,
    }

    if HAVE_RX:
        g = rx.PyGraph()
        g.add_nodes_from([f"op_{i}" for i in range(len(OPS))])
        g.add_nodes_from(["inner", "clifford", "outer"])
        # link each op to its *admissible* terrain set (just for structural
        # record; rustworkx used supportively)
        for i, (_, _, chir) in enumerate(OPS):
            if chir:
                g.add_edge(i, len(OPS) + 1, "clifford_only")
            else:
                for k in range(3):
                    g.add_edge(i, len(OPS) + k, f"terrain_{k}")
        results["bnd_rx_graph_edges"] = {
            "num_edges": g.num_edges(),
            "passed": g.num_edges() == (2 * 3 + 2 * 1),  # 2 nonchir*3 + 2 chir*1
        }

    return results


# =====================================================================
# MAIN
# =====================================================================
if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    # Mark tools actually used
    if HAVE_Z3:
        TOOL_MANIFEST["z3"]["used"] = True
        TOOL_MANIFEST["z3"]["reason"] = (
            "SAT/UNSAT checks for L11 placement admissibility rules "
            "(type<->loop, chirality<->Clifford, terrain range)"
        )
        TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"

    # numpy used for trivial bookkeeping only
    TOOL_MANIFEST["sympy"]["reason"] = (
        TOOL_MANIFEST["sympy"]["reason"]
        or "not needed: admissibility is discrete, handled by z3"
    )
    if HAVE_RX:
        TOOL_MANIFEST["rustworkx"]["used"] = True
        TOOL_MANIFEST["rustworkx"]["reason"] = (
            "structural record of op<->terrain admissibility edges; "
            "supportive cross-check of edge count"
        )
        TOOL_INTEGRATION_DEPTH["rustworkx"] = "supportive"

    # Reasons for untried tools
    for k, v in TOOL_MANIFEST.items():
        if not v["tried"] and not v["reason"]:
            v["reason"] = "not relevant to shell-local discrete placement law"

    all_sections = {**pos, **neg, **bnd}
    all_passed = all(v.get("passed", False) for v in all_sections.values())

    results = {
        "name": "sim_L11_placement_admissibility",
        "layer": "L11_placement_law",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "classical_baseline",
        "all_passed": all_passed,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_L11_placement_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL_PASSED={all_passed}")
    if not all_passed:
        for k, v in all_sections.items():
            if not v.get("passed", False):
                print(f"  FAIL: {k} -> {v}")
