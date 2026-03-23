---
id: "A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_SingleStep_BothDirections::c5edaebc4cac163f"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BidirectionalLoop_SingleStep_BothDirections
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_SingleStep_BothDirections::c5edaebc4cac163f`

## Description
a1_a0_b_sim_runner.py run_loop(): EVERY single step runs BOTH directions in sequence. Forward: A1 strategy → A0 compile → B evaluate → SIM execute tasks. Backward: SIM evidence → B ingest_sim_evidence_pack → B state snapshot → persist state. The loop is not 'sometimes forward sometimes backward' — both directions fire every step, making it a true bidirectional communication cycle.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
