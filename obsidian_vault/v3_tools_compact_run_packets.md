---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_compact_run_packets::0ccb31bc415a0030"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_compact_run_packets
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_compact_run_packets::0ccb31bc415a0030`

## Description
compact_run_packets.py (9575B): #!/usr/bin/env python3 """ Conservative packet-journal compaction pilot for one run.  Design: - Dry-run by default. - Only targets packet classes that have already been audited as checkpoint-like:   - B_TO_A0_STATE_UPDATE_ZIP   - A0_TO_A1_SAVE_ZIP - 

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[compaction]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[build_full_plus_save_zip.py]] → **SOURCE_MAP_PASS**
- [[compact_run_packets_py]] → **EXCLUDES**
