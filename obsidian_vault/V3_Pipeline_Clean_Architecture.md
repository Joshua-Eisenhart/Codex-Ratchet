---
id: "A2_3::ENGINE_PATTERN_PASS::V3_Pipeline_Clean_Architecture::70ca1effb66b106a"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# V3_Pipeline_Clean_Architecture
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::V3_Pipeline_Clean_Architecture::70ca1effb66b106a`

## Description
V3 pipeline.py: 38 lines. A0BSimPipeline = BootpackBKernel + BootpackBGateway + A0SimDispatcher + SimEngine. handle_message() → gateway. ingest_export_block() → kernel. run_sim_cycle(): dispatcher.build_campaign_plan(state) → tasks → sim_engine.run_task → kernel.ingest_sim_evidence_pack. Clean separation of concerns.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[kernel.py]] → **ENGINE_PATTERN_PASS**
