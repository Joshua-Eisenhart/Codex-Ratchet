---
id: "A2_3::SOURCE_MAP_PASS::campaign_tape_v1_format::cbe6cca730f2c986"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "NONCANON"
---

# campaign_tape_v1_format
**Node ID:** `A2_3::SOURCE_MAP_PASS::campaign_tape_v1_format::cbe6cca730f2c986`

## Description
CAMPAIGN_TAPE v1: mandatory append-only JSONL recording (EXPORT_BLOCK + THREAD_B_REPORT) pairs in canonical order. Required keys: seq (monotonic), export_id, export_block_sha256, export_block_relpath, thread_b_report_sha256, thread_b_report_relpath. Shardable with deterministic suffixes.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Inward Relations
- [[16_ZIP_SAVE_AND_TAPES_SPEC.md]] → **SOURCE_MAP_PASS**
- [[campaign_tape_append_only]] → **RELATED_TO**
- [[campaign_tape_000_jsonl]] → **STRUCTURALLY_RELATED**
- [[campaign_tape_append_only]] → **STRUCTURALLY_RELATED**
- [[Campaign_Tape_Mandatory]] → **STRUCTURALLY_RELATED**
- [[CAMPAIGN_TAPE_APPEND_ONLY]] → **STRUCTURALLY_RELATED**
