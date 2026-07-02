#!/usr/bin/env python3
"""Individual L8 groupoid/gluing PEPS3D bond-4 scout."""

from __future__ import annotations

from layer_bond4_individual_runner import run_layer

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native spinor/density carrier and PEPS3D bond-4 arrays"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "actual PEPS3D object construction"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-tree witness"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "bounded contraction value witness"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "spinor/geometric anticommutation witness"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count witness"},
    "z3": {"used": True, "role": "load_bearing", "reason": "positive-gap and downstream-lock gate"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent Boolean nonpromotion gate"},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "K graph connectivity witness"},
    "XGI": {"used": True, "role": "load_bearing", "reason": "K hyperedge witness"},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "cell-complex witness"},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "filtration/simplex witness"},
    "PyG": {"used": True, "role": "load_bearing", "reason": "graph data aggregate witness"},
    "geomstats": {"used": True, "role": "load_bearing", "reason": "S3 spinor-distance witness"},
    "e3nn": {"used": True, "role": "load_bearing", "reason": "O(3) norm-equivariance witness"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing", "quimb": "load_bearing", "cotengra": "load_bearing", "opt_einsum": "load_bearing",
    "clifford": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing",
    "rustworkx": "load_bearing", "XGI": "load_bearing", "TopoNetX": "load_bearing", "GUDHI": "load_bearing",
    "PyG": "load_bearing", "geomstats": "load_bearing", "e3nn": "load_bearing",
}


if __name__ == "__main__":
    raise SystemExit(
        run_layer(
            layer="L8",
            sim_id="l8_groupoid_gluing_peps3d_bond4_tool_ablation_layer_probe",
            tier="L8 individual groupoid/gluing dynamic layer",
            purpose="Run L8 as its own groupoid/gluing PEPS3D bond-4 layer sim with tool ablations.",
            scientific_question="Does the finite groupoid/gluing dynamic layer preserve object/arrow/gluing structure on a bond-4 PEPS3D carrier with label-only controls rejected?",
            finite_map="L8_GK_bond4 : (K, finite objects/arrows/gluing dynamics) -> groupoid signatures, QIT cuts, controls, and tool deltas",
            domain="finite K=(V,E,F,C), finite groupoid objects/arrows/dynamics, 8/16/32/64 sites, PEPS3D bond_dim=4",
            codomain="finite L8 groupoid/gluing signatures, PEPS3D bond-4 readouts, QIT cuts, controls, and blocked consumers",
            geometry_layer="L8 groupoid/gluing/equivariant dynamic geometry",
            claim_ceiling="Individual L8 layer-depth scout only; no stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.",
            source_alignment_category="l8_individual_peps3d_bond4_tool_ablation",
            tool_manifest=TOOL_MANIFEST,
            tool_integration_depth=TOOL_INTEGRATION_DEPTH,
        )
    )
