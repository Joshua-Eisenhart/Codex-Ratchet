#!/usr/bin/env python3
"""L2 Weyl/chirality depth entrypoint."""

from __future__ import annotations

from formal_layer_depth_common import run_depth

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "manifold_layer_depth_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native Weyl spinor carriers, spinor-derived densities, chirality controls, and QIT cuts"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "MPS/PEPS2D/PEPS3D carrier views over the L2 spinor payload"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "finite contraction-tree witnesses"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "noncommuting generator sanity checks"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count and commutator checks"},
    "z3": {"used": True, "role": "load_bearing", "reason": "gap and downstream-lock gates"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent finite admission gate"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


if __name__ == "__main__":
    raise SystemExit(run_depth("l2_weyl_spinor_chirality_mps_peps2d_peps3d_depth_probe"))
