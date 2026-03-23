---
id: "A2_3::SOURCE_MAP_PASS::build_phase_matrix_p0_p7::63b97f45815143c2"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# build_phase_matrix_p0_p7
**Node ID:** `A2_3::SOURCE_MAP_PASS::build_phase_matrix_p0_p7::63b97f45815143c2`

## Description
Eight ordered implementation phases: P0_SPEC_LOCK (spec lint), P1_ARTIFACT_GRAMMAR (parser/emitter validation), P2_B_CONFORMANCE (fixture suite green), P3_A0_COMPILER (deterministic EXPORT_BLOCK), P4_A1_TO_B_SMOKE (50-cycle deterministic replay), P5_SIM_EVIDENCE_LOOP (evidence ingest pass), P6_LONG_RUN_DISCIPLINE (sharding enforcement), P7_RELEASE_CANDIDATE (dual replay hash equality). No phase skipping.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[p0_through_p7_build_phases]]

## Inward Relations
- [[21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md]] → **SOURCE_MAP_PASS**
