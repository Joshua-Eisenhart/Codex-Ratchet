#!/usr/bin/env python3
"""Individual L5 operator-substage PEPS3D bond-4 scout."""

from __future__ import annotations

from layer_l4_l5_l7_individual_runner import run_individual_layer

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native spinors, substage cell actions, local QIT readouts, and PEPS3D bond-4 arrays"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "actual qtn.PEPS3D object construction for each L5 row"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-tree witness for PEPS3D carrier"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "bounded contraction-value witness for PEPS3D tensors"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "anticommutation witness for noncommuting operator basis separation"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count witness for 64 substage cells"},
    "z3": {"used": True, "role": "load_bearing", "reason": "finite sweep and downstream-lock gate"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent nonpromotion gate"},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "PEPS3D K graph connectivity witness"},
    "XGI": {"used": True, "role": "load_bearing", "reason": "PEPS3D hyperedge/cell witness"},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "finite cell-complex witness"},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "finite filtration/simplex witness"},
    "PyG": {"used": True, "role": "load_bearing", "reason": "graph data aggregate witness for K anchors"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


if __name__ == "__main__":
    raise SystemExit(
        run_individual_layer(
            layer="L5",
            sim_id="l5_operator_substage_peps3d_bond4_tool_ablation_layer_probe",
            tier="L5 individual operator-substage layer",
            purpose="Run L5 as its own operator-substage PEPS3D bond-4 layer sim with tool ablations.",
            scientific_question="Does the finite L5 operator-substage layer preserve 64 local cell/channel actions on an actual bond-4 PEPS3D carrier while 16-row and proxy controls are rejected?",
            finite_map="L5_CK_bond4 : (K, sheets, loops, terrains, operator slots, spinor-derived densities) -> 64 cell signatures, projections, QIT cuts, controls, and tool deltas",
            domain="finite K=(V,E,F,C), 64 operator-substage cells c=(sheet,loop,terrain,operator_slot), 8/16/32/64 sites, PEPS3D bond_dim=4",
            codomain="finite L5 64-cell tensor/channel signatures, placement projections, PEPS3D bond-4 readouts, QIT cuts, controls, and blocked consumers",
            geometry_layer="L5 operator-substage cell geometry",
            claim_ceiling="Individual L5 layer-depth scout only; no stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.",
            source_alignment_category="l5_individual_peps3d_bond4_tool_ablation",
            tool_manifest=TOOL_MANIFEST,
            tool_integration_depth=TOOL_INTEGRATION_DEPTH,
        )
    )
