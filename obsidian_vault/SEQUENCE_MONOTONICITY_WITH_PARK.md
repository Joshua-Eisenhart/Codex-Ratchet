---
id: "A2_3::ENGINE_PATTERN_PASS::SEQUENCE_MONOTONICITY_WITH_PARK::03bc3f654708a46e"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# SEQUENCE_MONOTONICITY_WITH_PARK
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::SEQUENCE_MONOTONICITY_WITH_PARK::03bc3f654708a46e`

## Description
ZIP packets carry monotonically increasing sequence numbers per (run_id, source_layer) pair. Out-of-order packets are PARKED (not rejected) for later replay. Regression (sequence <= last_accepted) is hard-rejected.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Outward Relations
- **RELATED_TO** → [[zip_job_deterministic_carrier]]
- **RELATED_TO** → [[SIM_DISPATCH_TIER_SUITE_ORDERING]]

## Inward Relations
- [[zip_protocol_v2_validator.py]] → **ENGINE_PATTERN_PASS**
- [[A0_Compile_Bucket_Order]] → **RELATED_TO**
- [[BACKWARD_BEFORE_FORWARD_PARKING]] → **RELATED_TO**
