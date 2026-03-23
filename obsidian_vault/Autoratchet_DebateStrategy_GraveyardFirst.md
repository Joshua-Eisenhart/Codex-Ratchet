---
id: "A2_3::ENGINE_PATTERN_PASS::Autoratchet_DebateStrategy_GraveyardFirst::55265965f45a378b"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# Autoratchet_DebateStrategy_GraveyardFirst
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::Autoratchet_DebateStrategy_GraveyardFirst::55265965f45a378b`

## Description
autoratchet.py: debate_strategy='graveyard_first_then_recovery'. For early steps (seq <= graveyard_fill_steps), debate_mode='graveyard_first' — fill the graveyard before attempting rescue. After fill steps, switches to 'graveyard_recovery' — rescue from graveyard. This sequences the bidirectional loop: first build failure evidence (backward-heavy), then build rescue attempts (forward-heavy).

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[V3_RealLoop_Autoratchet]]

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
