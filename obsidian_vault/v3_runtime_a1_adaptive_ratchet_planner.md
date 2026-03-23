---
id: "A2_3::SOURCE_MAP_PASS::v3_runtime_a1_adaptive_ratchet_planner::495c95ec28f1e173"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# v3_runtime_a1_adaptive_ratchet_planner
**Node ID:** `A2_3::SOURCE_MAP_PASS::v3_runtime_a1_adaptive_ratchet_planner::495c95ec28f1e173`

## Description
a1_adaptive_ratchet_planner.py (125794B): #!/usr/bin/env python3 """ Deterministic A1-side planner that generates packet-mode A1_STRATEGY_v1 capsules to advance a bottom-up term ladder (no FORMULA / no equals) toward QIT primitives.  This does NOT use an LLM. It is an executable reference fo

## Properties
- **source_line_range**: 
- **extraction_mode**: SOURCE_MAP_PASS

## Outward Relations
- **DEPENDS_ON** → [[a1_strategy_v1]]
- **DEPENDS_ON** → [[reference]]
- **DEPENDS_ON** → [[planner]]
- **DEPENDS_ON** → [[packet]]

## Inward Relations
- [[test_run_a1_autoratchet_cycle_audit.py]] → **SOURCE_MAP_PASS**
- [[a1_adaptive_ratchet_planner_py]] → **EXCLUDES**
- [[test_a1_adaptive_ratchet_planner_py]] → **EXCLUDES**
