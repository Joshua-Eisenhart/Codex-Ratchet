---
id: "A2_3::ENGINE_PATTERN_PASS::BIDIRECTIONAL_LOOP_EVERY_STEP::4eae4ceebd4472a5"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BIDIRECTIONAL_LOOP_EVERY_STEP
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BIDIRECTIONAL_LOOP_EVERY_STEP::4eae4ceebd4472a5`

## Description
The main loop in a1_a0_b_sim_runner fires BOTH forward (A1→A0→B strategy evaluation) and backward (SIM execution → evidence ingestion → state snapshot) in EVERY iteration. There is no separate audit pass — auditing is integral to every ratchet step.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[end_to_end_loop]]

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
