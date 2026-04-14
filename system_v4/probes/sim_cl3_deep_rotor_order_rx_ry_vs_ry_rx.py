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
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    e12, e23, e13 = blades['e12'], blades['e23'], blades['e13']
    theta = math.pi/3
    phi = math.pi/4
    Rx = math.cos(theta/2) - math.sin(theta/2)*e23  # rotor about x
    Ry = math.cos(phi/2) - math.sin(phi/2)*e13
    AB = Rx * Ry
    BA = Ry * Rx
    diff = (AB - BA)
    diff_norm = float(abs(diff))
    v = e1 + 0.3*e2 + 0.7*e3
    v_ab = AB * v * ~AB
    v_ba = BA * v * ~BA
    sep = float(abs(v_ab - v_ba))
    results['rotor_products_differ'] = diff_norm > 1e-9
    results['vector_images_differ'] = sep > 1e-9
    results['diff_norm'] = diff_norm
    results['image_sep'] = sep

    return results


# =====================================================================
# NEGATIVE TESTS (mandatory)
# =====================================================================

def run_negative_tests():
    results = {}
    from clifford import Cl
    import math
    layout, blades = Cl(3)
    e23 = blades['e23']
    # Coaxial rotors commute; candidate 'non-commutative' claim excluded for collinear axes.
    R1 = math.cos(0.3) - math.sin(0.3)*e23
    R2 = math.cos(0.7) - math.sin(0.7)*e23
    diff = float(abs(R1*R2 - R2*R1))
    results['coaxial_commute'] = diff < 1e-12

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    from clifford import Cl
    import math
    layout, blades = Cl(3)
    e23, e13 = blades['e23'], blades['e13']
    # tiny angle: BCH first-order => commutator scales as theta*phi
    t = 1e-6
    Rx = math.cos(t/2) - math.sin(t/2)*e23
    Ry = math.cos(t/2) - math.sin(t/2)*e13
    diff = float(abs(Rx*Ry - Ry*Rx))
    results['small_angle_nonzero'] = 0 < diff < 1e-6
    results['small_angle_diff'] = diff

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "cl3_deep_rotor_order_rx_ry_vs_ry_rx",
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
    out_path = os.path.join(out_dir, "cl3_deep_rotor_order_rx_ry_vs_ry_rx_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
