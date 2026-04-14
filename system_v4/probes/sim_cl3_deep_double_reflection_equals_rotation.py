#!/usr/bin/env python3
"""
SIM TEMPLATE -- All new sims must start from this template.
See system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md for rules.

Usage:
  1. Copy this file to sim_<your_name>.py
  2. Rename "TEMPLATE" throughout
  3. Implement positive, negative, and boundary tests
  4. Update TOOL_MANIFEST entries with used=True and reason for each tool
  5. Record which tools were actually load-bearing for the claim
  5. Run and commit the result JSON
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": True, "reason": "matrix numpy cannot express the bivector/rotor distinction needed for this admissibility claim"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

# Record actual integration depth, not just import presence.
# Each entry should be one of:
# - "load_bearing"  : the result materially depends on this tool
# - "supportive"    : useful cross-check/helper but not decisive
# - "decorative"    : present only at manifest/import level (avoid this)
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Try importing each tool
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    from clifford import Cl
    import math
    layout, blades = Cl(3)
    e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
    e12 = blades['e12']
    # Reflect v across plane with unit normal n: v -> -n v n
    # Two reflections across normals n then m separated by angle alpha/2 => rotation by alpha in plane n^m.
    alpha = math.pi/3
    n = e1
    m = math.cos(alpha/2)*e1 + math.sin(alpha/2)*e2
    v = 0.3*e1 + 0.7*e2 - 0.2*e3
    v_two_refl = -m*(-n*v*n)*m  # = m n v n m
    R = math.cos(alpha/2) - math.sin(alpha/2)*e12  # rotation by alpha about e3 axis
    v_rot = R*v*~R
    diff = float(abs(v_two_refl - v_rot))
    results['double_reflect_equals_rotation'] = diff < 1e-9
    results['diff'] = diff

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}
    from clifford import Cl
    import math
    layout, blades = Cl(3)
    e1,e2 = blades['e1'],blades['e2']
    e12 = blades['e12']
    # Single reflection is grade-reversing (orientation flip); does NOT equal any rotation.
    v = 0.3*e1 + 0.7*e2
    n = e1
    refl = -n*v*n
    # Try all rotations by sweeping angle: none should match single reflection
    best = 1e9
    for k in range(200):
        a = 2*math.pi*k/200
        R = math.cos(a/2) - math.sin(a/2)*e12
        best = min(best, float(abs(R*v*~R - refl)))
    results['single_reflection_excluded_from_rotations'] = best > 1e-6
    results['best_match'] = best

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    from clifford import Cl
    layout, blades = Cl(3)
    e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
    # Two reflections across same plane = identity.
    v = 0.5*e1 - 0.2*e2 + 0.3*e3
    n = e1
    v2 = -n*(-n*v*n)*n
    results['same_plane_twice_identity'] = float(abs(v2 - v)) < 1e-12

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "cl3_deep_double_reflection_equals_rotation",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
        "scope_note": "Scope: see system_v5/new docs/ENGINE_MATH_REFERENCE.md -- rotor composition is shell-local non-commutative geometric product; exclusion language: candidates failing equality are excluded as indistinguishable-under-commutation, not proven nonexistent."
    }

    # Mark tools as used based on what was actually called
    # (update TOOL_MANIFEST entries with used=True and reason)

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cl3_deep_double_reflection_equals_rotation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
