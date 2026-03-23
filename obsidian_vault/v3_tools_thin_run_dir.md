---
id: "A2_3::SOURCE_MAP_PASS::v3_tools_thin_run_dir::1fe020d88090f02e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_tools_thin_run_dir
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_tools_thin_run_dir::1fe020d88090f02e`

## Description
thin_run_dir.py (10454B): #!/usr/bin/env python3 """ Thin a run directory without destroying authoritative replay lineage.  Design: - Dry-run by default. - Only operates inside system_v3/runs/<RUN_ID>/ (or system_v3/runs/_CURRENT_STATE). - Targets duplicate plaintext/helper s

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[current]]

## Inward Relations
- [[stage_browser_observed_thread_packet.py]] → **SOURCE_MAP_PASS**
