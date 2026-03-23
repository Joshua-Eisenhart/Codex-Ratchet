---
id: "A2_3::ENGINE_PATTERN_PASS::SimSuiteModes_ThreeKinds::015d8cf878c9cbf0"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# SimSuiteModes_ThreeKinds
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::SimSuiteModes_ThreeKinds::015d8cf878c9cbf0`

## Description
a1_a0_b_sim_runner.py lines 816-818: three suite modes tracked in each step: failure_isolation (test specific failure boundaries), graveyard_rescue (attempt to recover graveyard items), replay_from_tape (replay deterministic tape segments). These are what the backward direction routes — each produces different evidence types that feed back into B for different kinds of audit.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
