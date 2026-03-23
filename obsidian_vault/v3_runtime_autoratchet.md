---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_autoratchet::a7d6c52811e524df"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_autoratchet
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_autoratchet::a7d6c52811e524df`

## Description
autoratchet.py (22309B): #!/usr/bin/env python3 """ Autonomous local loop (no external LLM) for packet-mode runs:   - generates 1 A1_TO_A0_STRATEGY_ZIP using the deterministic planner   - runs 1 step of a1_a0_b_sim_runner.py in packet mode   - repeats for N steps  This is an

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[external]]
- **DEPENDS_ON** → [[planner]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
