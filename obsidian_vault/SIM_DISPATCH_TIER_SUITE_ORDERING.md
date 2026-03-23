---
id: "A2_3::ENGINE_PATTERN_PASS::SIM_DISPATCH_TIER_SUITE_ORDERING::8844a4dbe7314908"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# SIM_DISPATCH_TIER_SUITE_ORDERING
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::SIM_DISPATCH_TIER_SUITE_ORDERING::8844a4dbe7314908`

## Description
SimDispatcher plans SIM campaigns using a multi-key sort: (blocked, stage_rank, tier_rank, suite_rank, sim_id). 8 suite kinds ordered: micro_suite → mid_suite → segment_suite → engine_suite → mega_suite → failure_isolation → graveyard_rescue → replay_from_tape. Engine/mega suites are blocked until all lower-tier stages complete.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[sim_dispatcher.py]] → **ENGINE_PATTERN_PASS**
- [[A0_Compile_Bucket_Order]] → **RELATED_TO**
- [[SEQUENCE_MONOTONICITY_WITH_PARK]] → **RELATED_TO**
