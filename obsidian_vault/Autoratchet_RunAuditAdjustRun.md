---
id: "A2_3::ENGINE_PATTERN_PASS::Autoratchet_RunAuditAdjustRun::9c5ea2d81584cb78"
type: "EXTRACTED_CONCEPT"
layer: "A2_HIGH_INTAKE"
authority: "SOURCE_CLAIM"
---

# Autoratchet_RunAuditAdjustRun
**Node ID:** `A2_3::ENGINE_PATTERN_PASS::Autoratchet_RunAuditAdjustRun::9c5ea2d81584cb78`

## Description
autoratchet.py line 8: 'This is an execution discipline harness: run → audit → adjust → run.' The autoratchet wraps the bidirectional A0↔B↔SIM loop in an OUTER loop: (1) generate A1 strategy packet, (2) run one step of a1_a0_b_sim_runner (which itself runs both directions), (3) check metrics (canonical_terms, survivors, kills), (4) repeat. Debate strategy controls which graveyard mode to use.

## Properties
- **source_line_range**: 
- **extraction_mode**: ENGINE_PATTERN_PASS

## Inward Relations
- [[a1_a0_b_sim_runner.py]] → **ENGINE_PATTERN_PASS**
