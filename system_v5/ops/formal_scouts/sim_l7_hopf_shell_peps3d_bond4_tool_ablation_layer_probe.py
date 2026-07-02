#!/usr/bin/env python3
"""Individual L7 Hopf-shell PEPS3D bond-4 scout."""

from __future__ import annotations

from layer_l4_l5_l7_individual_runner import run_individual_layer

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native Hopf spinors, shell projections, local QIT readouts, and PEPS3D bond-4 arrays"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "actual qtn.PEPS3D object construction for each L7 row"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-tree witness for PEPS3D carrier"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "bounded contraction-value witness for PEPS3D tensors"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "anticommutation witness for noncommuting shell-loop basis separation"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count witness for shells and phase grid"},
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
            layer="L7",
            sim_id="l7_hopf_shell_peps3d_bond4_tool_ablation_layer_probe",
            tier="L7 individual Hopf-shell layer",
            purpose="Run L7 as its own Hopf-shell PEPS3D bond-4 layer sim with tool ablations.",
            scientific_question="Does the finite L7 Hopf-shell layer preserve shell, phase-grid, and fiber/base loop structure on an actual bond-4 PEPS3D carrier while flattened-shell and proxy controls collapse?",
            finite_map="L7_HK_bond4 : (K, Hopf shells, phase grid, fiber/base loops, Hopf spinors) -> shell projections, connection signatures, QIT cuts, controls, and tool deltas",
            domain="finite K=(V,E,F,C), 5 eta shells, 64 phase-grid points, fiber/base loops, 8/16/32/64 sites, PEPS3D bond_dim=4",
            codomain="finite L7 Hopf shell projection signatures, PEPS3D bond-4 readouts, QIT cuts, controls, and blocked consumers",
            geometry_layer="L7 Hopf shell/fibration projection geometry",
            claim_ceiling="Individual L7 layer-depth scout only; no stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.",
            source_alignment_category="l7_individual_peps3d_bond4_tool_ablation",
            tool_manifest=TOOL_MANIFEST,
            tool_integration_depth=TOOL_INTEGRATION_DEPTH,
        )
    )
