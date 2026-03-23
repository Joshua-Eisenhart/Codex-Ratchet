---
id: "A2_3::SOURCE_MAP_PASS::zip_dropins_layer1_ingest_and_normalization_rep::6a834d2ca391cf2b"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# zip_dropins_layer1_ingest_and_normalization_rep
**Node ID:** `A2_3::SOURCE_MAP_PASS::zip_dropins_layer1_ingest_and_normalization_rep::6a834d2ca391cf2b`

## Description
LAYER1_INGEST_AND_NORMALIZATION_REPORT.out.md (578B): # LAYER-1 INGEST AND NORMALIZATION REPORT (Layer 1.5)  status: COMPLETE|PARTIAL  discovered_runs:   - run_slug: <FILL>     source_path_in_bundle: <FILL>     detected_output_tree: YES|NO     detected_alt_model_lane_packet: YES|NO     detected_rosetta_

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 4 sources, 4 batches, 8 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **DEPENDS_ON** → [[output]]
- **DEPENDS_ON** → [[packet]]
- **DEPENDS_ON** → [[layer1_ingest_and_normalization_report.out]]

## Inward Relations
- [[README__L1_5__WHAT_THIS_JOB_IS__v1.md]] → **SOURCE_MAP_PASS**
- [[ZIP_JOB_MANIFEST_v1.json]] → **OVERLAPS**
- [[ZIP_JOB_ROOT_AND_PAYLOAD_DISCOVERY_RULES__v1.md]] → **OVERLAPS**
- [[00_TASK__PORTABLE_OUTPUT_FILE_FENCE_AND_FAIL_CLOSED.task.md]] → **OVERLAPS**
- [[layer1_ingest_and_normalization_report.out]] → **STRUCTURALLY_RELATED**
- [[01_task__ingest_and_normalize_layer1_outputs.task]] → **STRUCTURALLY_RELATED**
