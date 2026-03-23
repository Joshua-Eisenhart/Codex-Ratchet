---
id: "A2_3::ENGINE_PATTERN_PASS::V3_RealLoop_Autoratchet::fb09a1628eabd116"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# V3_RealLoop_Autoratchet
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::V3_RealLoop_Autoratchet::fb09a1628eabd116`

## Description
V3 run_real_loop.py: autoratchet with debate_strategy='graveyard_first_then_recovery'. Steps: init_run_surface → autoratchet → sync_events → materialize_export → replay_reports → materialize_sim_evidence → materialize_graveyard_records → materialize_tapes → phase_gate_pipeline → sprawl_guard. State objects: survivor_order, graveyard, park_set, term_registry, evidence_pending, sim_results.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[kernel.py]] → **ENGINE_PATTERN_PASS**
- [[Autoratchet_DebateStrategy_GraveyardFirst]] → **RELATED_TO**
