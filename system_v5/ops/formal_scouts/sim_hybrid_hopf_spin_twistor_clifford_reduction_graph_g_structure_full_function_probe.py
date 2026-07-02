#!/usr/bin/env python3
"""Individual hybrid Hopf/Spin/Twistor/Clifford G-structure scout."""

from __future__ import annotations

from g_structure_individual_runner import run_candidate

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_g_structure_candidate_full_function_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native spinor carrier and QIT readouts"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "MPS, PEPS2D, and PEPS3D carrier views"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "finite contraction-tree witness"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "Clifford sanity checks for spinor geometry"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite invariant checks"},
    "z3": {"used": True, "role": "load_bearing", "reason": "individual candidate gap proof gate"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent row-pass proof gate"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


if __name__ == "__main__":
    raise SystemExit(run_candidate("Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph"))
