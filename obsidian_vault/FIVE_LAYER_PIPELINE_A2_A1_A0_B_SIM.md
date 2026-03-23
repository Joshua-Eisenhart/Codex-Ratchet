---
id: "A2_3::ENGINE_PATTERN_PASS::FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM::3e0a023caed08006"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::FIVE_LAYER_PIPELINE_A2_A1_A0_B_SIM::3e0a023caed08006`

## Description
The runtime implements a 5-layer deterministic pipeline connected by file-based ZIP capsules: A2 (graph controller) → A1 (strategy generator) → A0 (compiler) → B (enforcement kernel) → SIM (evidence engine). No in-process RPC, no shared memory — all inter-layer communication is artifact-based.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[control_plane_bundle_architecture]]
- **RELATED_TO** → [[end_to_end_loop]]
- **RELATED_TO** → [[layer_entropy_hierarchy]]
- **RELATED_TO** → [[V4_Pipeline_Components_Exist]]
- **RELATED_TO** → [[ZIP_PROTOCOL_V2_EIGHT_TYPE_SYSTEM]]
- **RELATED_TO** → [[JP_DETERMINISM_FIRST_RULE]]
- **RELATED_TO** → [[b_kernel_7_stage_pipeline]]
- **RELATED_TO** → [[b_kernel_10_stage_pipeline]]
- **RELATED_TO** → [[b_kernel_deterministic_stage_order]]
- **STRUCTURALLY_RELATED** → [[five_layer_boundary_law]]

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
