---
id: "A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_WhatEachDirectionDoes::e5fd62bae9a1f24c"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BidirectionalLoop_WhatEachDirectionDoes
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_WhatEachDirectionDoes::e5fd62bae9a1f24c`

## Description
FORWARD direction does ratcheting: builds new candidates, compiles them, evaluates structure, runs simulations. BACKWARD direction does auditing: sim evidence kills bad survivors, state updates propagate, graveyard fills, coverage reports check promotion readiness. Forward ADDS to the system. Backward REMOVES from the system. Both are needed — adding without removing creates noise, removing without adding creates stall.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
