---
id: "A2_3::ENGINE_PATTERN_PASS::GATEWAY_MESSAGE_ROUTING::a864ee2c5947d320"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# GATEWAY_MESSAGE_ROUTING
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::GATEWAY_MESSAGE_ROUTING::a864ee2c5947d320`

## Description
BootpackBGateway routes inbound messages to 4 handlers: COMMAND (REQUEST DUMP_LEDGER etc.), EXPORT (→ kernel.evaluate_export_block), SNAPSHOT (→ validate + admit), SIM_EVIDENCE (→ kernel.ingest_sim_evidence_pack). Unrecognized messages are hard-rejected as MULTI_ARTIFACT_OR_PROSE.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[sim_dispatcher.py]] → **ENGINE_PATTERN_PASS**
