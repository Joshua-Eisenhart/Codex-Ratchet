---
id: "SKILL::run-a1-eval-slice"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# run-a1-eval-slice
**Node ID:** `SKILL::run-a1-eval-slice`

## Description
A1 evaluation harness

## Properties
- **skill_type**: verification
- **source_type**: runner
- **source_path**: system_v4/skills/run_a1_eval_slice.py
- **status**: active
- **applicable_layers**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_trust_zones**: ["A1_JARGONED", "A1_STRIPPED"]
- **applicable_graphs**: ["concept"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/run_a1_eval_slice.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
