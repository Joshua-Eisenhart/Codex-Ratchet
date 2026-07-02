#!/usr/bin/env python3
"""Separate L6 entropy-cut full spinor-network carrier-depth scout."""

from __future__ import annotations

from layer_full_spinor_network_individual_runner import run_layer

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "individual_full_spinor_network_layer_depth_probe"
TOOL_MANIFEST = {
    "torch": {"used": True, "role": "load_bearing", "reason": "torch-native complex spinor payloads, QIT densities, and carrier readouts"},
    "quimb": {"used": True, "role": "load_bearing", "reason": "actual MPS, PEPS2D, and PEPS3D carrier objects"},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-tree witness for PEPS carrier contractions"},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "finite contraction values for carrier signatures"},
    "clifford": {"used": True, "role": "load_bearing", "reason": "cut/action anticommutation witness"},
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
            layer="L6",
            sim_id="l6_entropy_cut_full_spinor_network_layer_probe",
            tier="L6 individual full entropy-cut spinor-network carrier-depth layer",
            purpose="Run L6 as its own full-spec QIT cut/readout spinor-network layer sim over bounded layer-native scale rows.",
            scientific_question="Does L6 preserve entropy-cut/communication structure as a derived readout of torch spinors, PyG, MPS, PEPS2D, and PEPS3D rather than replacing the carrier with scalar entropy?",
            finite_map="L6_full : finite entropy-cut/communication action over K -> communication carrier signatures, QIT entropy-family cuts, controls, and tool deltas",
            domain="finite K=(V,E,F,C), QIT cut/readout communication actions, bounded L6 native scale rows, MPS, PEPS2D bond-4, PEPS3D bond-4, and controls",
            codomain="L6 entropy-cut carrier signatures, QIT readouts, scalar-entropy rejection controls, ablation deltas, and locked downstream consumers",
            geometry_layer="L6 entropy-cut/communication geometry",
            claim_ceiling="Formal scout only: individual L6 carrier-depth receipt; no stacking, flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission.",
            source_alignment_category="l6_individual_full_spinor_network_layer_depth",
            tool_manifest=TOOL_MANIFEST,
            tool_integration_depth=TOOL_INTEGRATION_DEPTH,
        )
    )
