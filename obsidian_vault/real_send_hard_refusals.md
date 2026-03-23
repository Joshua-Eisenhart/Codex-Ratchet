---
id: "A2_3::SOURCE_MAP_PASS::real_send_hard_refusals::8d312cdb9ca55683"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# real_send_hard_refusals
**Node ID:** `A2_3::SOURCE_MAP_PASS::real_send_hard_refusals::8d312cdb9ca55683`

## Description
Must refuse to run real-send if target is not READY, missing verification text, missing prior validate-only proof, or targeting Controller/Pro threads.

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **RELATED_TO** → [[sender_packet_hard_rules]]
- **RELATED_TO** → [[verification_lock]]

## Inward Relations
- [[60_BROWSER_REAL_SEND_MODE__v1.md]] → **SOURCE_MAP_PASS**
- [[browser_helper_refusals]] → **RELATED_TO**
