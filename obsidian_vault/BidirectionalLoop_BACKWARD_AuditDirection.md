---
id: "A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_BACKWARD_AuditDirection::6546471a79b589b4"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# BidirectionalLoop_BACKWARD_AuditDirection
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::BidirectionalLoop_BACKWARD_AuditDirection::6546471a79b589b4`

## Description
a1_a0_b_sim_runner.py: BACKWARD direction in the A0↔B↔SIM loop. ZIP packets with direction='BACKWARD': SIM_TO_A0_SIM_RESULT_ZIP (SIM evidence → A0), then kernel.ingest_sim_evidence_pack() feeds evidence BACK into B Kernel — this is where KILL signals execute. B_TO_A0_STATE_UPDATE_ZIP (B state snapshot → A0). A0_TO_A1_SAVE_ZIP emits when inbox is empty (A0 sends state back to A1 for next strategy). This direction AUDITS and KILLS — it enforces.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
