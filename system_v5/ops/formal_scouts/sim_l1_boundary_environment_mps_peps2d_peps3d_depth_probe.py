#!/usr/bin/env python3
"""L1 boundary environment depth entrypoint."""

from __future__ import annotations

from formal_layer_depth_common import run_depth

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "manifold_layer_depth_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native boundary spinors, densities, and QIT cuts"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "MPS/PEPS2D/PEPS3D carrier views"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "finite contraction-tree witnesses"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "noncommuting generator sanity checks"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count checks"},
    "z3": {"used": True, "role": "load_bearing", "reason": "gap and downstream-lock gates"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent finite admission gate"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


if __name__ == "__main__":
    raise SystemExit(run_depth("l1_boundary_environment_mps_peps2d_peps3d_depth_probe"))
