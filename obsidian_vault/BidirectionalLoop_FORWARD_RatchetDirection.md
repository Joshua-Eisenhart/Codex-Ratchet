---
id: "A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_FORWARD_RatchetDirection::c4ff60f69e6a8eef"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BidirectionalLoop_FORWARD_RatchetDirection
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_FORWARD_RatchetDirection::c4ff60f69e6a8eef`

## Description
a1_a0_b_sim_runner.py: FORWARD direction in the A0↔B↔SIM loop. ZIP packets with direction='FORWARD': A1_TO_A0_STRATEGY_ZIP (A1 proposes strategy → A0), A0_TO_B_EXPORT_BATCH_ZIP (A0 compiles → B). B evaluates: ACCEPT (new survivor), PARK (retained for replay), REJECT (graveyard). Then SIM runs campaign tasks to test survivors. This direction BUILDS and VALIDATES — it ratchets.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
