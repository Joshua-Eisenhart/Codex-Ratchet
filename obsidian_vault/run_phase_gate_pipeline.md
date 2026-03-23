---
id: "A2_3::SOURCE_MAP_PASS::run_phase_gate_pipeline::aacc4179b3d78a4f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# run_phase_gate_pipeline
**Node ID:** `A2_3::SOURCE_MAP_PASS::run_phase_gate_pipeline::aacc4179b3d78a4f`

## Description
Evaluates phase gate conditions (P0_SPEC_LOCK to P7_RELEASE_CANDIDATE) from run reports artifacts, updates phase_transition_report.json and release_checklist_v1.json. Optional --require-phase fails if a required phase is not PASS.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **STRUCTURALLY_RELATED** → [[v3_tools_run_phase_gate_pipeline]]
- **STRUCTURALLY_RELATED** → [[run_phase_gate_pipeline_py]]

## Inward Relations
- [[22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md]] → **SOURCE_MAP_PASS**
- [[mass_extraction_runner_skill]] → **RELATED_TO**
- [[eight_phase_gate_pipeline]] → **STRUCTURALLY_RELATED**
- [[eight_phase_gate_pipeline]] → **STRUCTURALLY_RELATED**
