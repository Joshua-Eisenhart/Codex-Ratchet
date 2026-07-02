#!/usr/bin/env python3
"""Separate L7 Hopf-shell full spinor-network carrier-depth scout."""

from __future__ import annotations

from layer_full_spinor_network_individual_runner import run_layer

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "individual_full_spinor_network_layer_depth_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native complex Hopf-shell spinor payloads and QIT densities"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "actual MPS, PEPS2D, and PEPS3D carrier objects"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-tree witness for PEPS carrier contractions"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "finite contraction values for carrier signatures"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "Hopf-shell spinor anticommutation witness"},
    "sympy": {"used": True, "role": "load_bearing", "reason": "exact finite count and symbolic shape checks"},
    "z3": {"used": True, "role": "load_bearing", "reason": "positive-gap and downstream-lock gate"},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent Boolean gate for all-row pass"},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "finite K graph connectivity witness"},
    "XGI": {"used": True, "role": "load_bearing", "reason": "finite K hyperedge witness"},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "finite cell-complex witness"},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "finite simplex and filtration witness"},
    "PyG": {"used": True, "role": "load_bearing", "reason": "graph message-passing witness over K"},
    "geomstats": {"used": True, "role": "load_bearing", "reason": "S3 spinor-distance witness"},
    "e3nn": {"used": True, "role": "load_bearing", "reason": "O(3) equivariance witness over spinor-derived vectors"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "XGI": "load_bearing",
    "TopoNetX": "load_bearing",
    "GUDHI": "load_bearing",
    "PyG": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
}


if __name__ == "__main__":
    raise SystemExit(
        run_layer(
            layer="L7",
            sim_id="l7_hopf_shell_full_spinor_network_layer_probe",
            tier="L7 individual full Hopf-shell spinor-network carrier-depth layer",
            purpose="Run L7 as its own full-spec Hopf shell/projection spinor-network layer sim over bounded layer-native scale rows.",
            scientific_question="Does L7 preserve Hopf shell/fiber projection structure through torch spinors, PyG, MPS, PEPS2D, PEPS3D, and QIT entropy-family readouts?",
            finite_map="L7_full : finite Hopf shell/fiber projection over K -> shell carrier signatures, entropy-family cuts, controls, and tool deltas",
            domain="finite K=(V,E,F,C), Hopf shell/fiber projection states, bounded L7 native scale rows, MPS, PEPS2D bond-4, PEPS3D bond-4, and controls",
            codomain="L7 Hopf-shell carrier signatures, QIT readouts, shell/fiber controls, ablation deltas, and locked downstream consumers",
            geometry_layer="L7 Hopf shell/fibration/projection geometry",
            claim_ceiling="Formal scout only: individual L7 carrier-depth receipt; no stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.",
            source_alignment_category="l7_individual_full_spinor_network_layer_depth",
            tool_manifest=TOOL_MANIFEST,
            tool_integration_depth=TOOL_INTEGRATION_DEPTH,
        )
    )
