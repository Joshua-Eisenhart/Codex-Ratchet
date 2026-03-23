---
id: "A2_3::SOURCE_MAP_PASS::campaign_tape_000_jsonl::54869748f0be3564"
type: "KERNEL_CONCEPT"
layer: "A2_2_CANDIDATE"
authority: "CROSS_VALIDATED"
---

# campaign_tape_000_jsonl
**Node ID:** `A2_3::SOURCE_MAP_PASS::campaign_tape_000_jsonl::54869748f0be3564`

## Description
Unprocessed File Type (campaign_tape.000.jsonl): {"export_block_relpath":"zip_packets/000002_A0_TO_B_EXPORT_BATCH_ZIP.zip","export_block_sha256":"eca921f8109fc43bbbf53d7727ea0b49dd361ab5afea006e1a9e07f1fa8e5687","export_id":"A0_1D5B2416623ED3D6","seq":2,"thread_b_report_relpath":"b_reports/b_report

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS
- **promoted_by**: CROSS_VALIDATION_PASS_001
- **promoted_reason**: CROSS_VAL: 4 sources, 4 batches, 9 edges
- **promoted_from**: A2_3_INTAKE

## Outward Relations
- **STRUCTURALLY_RELATED** → [[campaign_tape_append_only]]
- **STRUCTURALLY_RELATED** → [[campaign_tape_v1_format]]
- **STRUCTURALLY_RELATED** → [[export_tape_000_jsonl]]
- **DEPENDS_ON** → [[export_block]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[campaign_tape.000.jsonl]] → **SOURCE_MAP_PASS**
- [[campaign_tape.000.jsonl]] → **OVERLAPS**
- [[campaign_tape.000.jsonl]] → **OVERLAPS**
- [[campaign_tape.000.jsonl]] → **OVERLAPS**
- [[campaign_tape_append_only]] → **STRUCTURALLY_RELATED**
- [[Campaign_Tape_Mandatory]] → **STRUCTURALLY_RELATED**
- [[CAMPAIGN_TAPE_APPEND_ONLY]] → **STRUCTURALLY_RELATED**
