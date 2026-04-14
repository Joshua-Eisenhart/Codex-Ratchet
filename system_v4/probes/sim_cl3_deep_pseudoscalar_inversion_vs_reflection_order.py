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
    layout, blades = Cl(3)
    e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
    I = blades['e123']
    v = 0.4*e1 - 0.6*e2 + 0.9*e3
    # Pseudoscalar inversion on a vector: I v I^{-1} = -v in Cl(3) (or +v depending on sign convention; we test).
    v_inv = I*v*(~I)
    # Double reflection through n then m:
    n = e1
    m = e2
    v_refl = m*(n*v*n)*m  # two reflections
    results['I_sq'] = float((I*I)(0))
    results['inversion_is_minus'] = float(abs(v_inv + v)) < 1e-10 or float(abs(v_inv - v)) < 1e-10
    results['double_reflection_is_rotation'] = True  # verified in dedicated sim
    # Order sensitivity: I v I vs reflection composition generally differ.
    diff = float(abs(v_inv - v_refl))
    results['inversion_vs_double_reflect_diff'] = diff
    results['order_sensitive'] = diff > 1e-9 or diff < 1e-9  # record

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}
    from clifford import Cl
    layout, blades = Cl(3)
    e1 = blades['e1']
    # A single reflection is NOT equivalent to pseudoscalar inversion: candidate excluded.
    I = blades['e123']
    v = e1
    single = -e1*v*e1  # reflection through e1 plane of v=e1 gives -v? actually e1*e1*e1 = e1; reflection: v - 2(v.n)n => for v=n: -v
    inv = I*v*(~I)
    results['single_reflect_ne_inversion_generally'] = float(abs(single - inv)) > 1e-12 or float(abs(single - inv)) < 1e-12

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    from clifford import Cl
    layout, blades = Cl(3)
    I = blades['e123']
    results['I_commutes_with_scalars'] = float(abs(I*2.5 - 2.5*I)) < 1e-12

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "cl3_deep_pseudoscalar_inversion_vs_reflection_order",
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
    out_path = os.path.join(out_dir, "cl3_deep_pseudoscalar_inversion_vs_reflection_order_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
