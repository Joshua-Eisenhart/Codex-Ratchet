---
id: "SKILL::structured-fuzzer"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# structured-fuzzer
**Node ID:** `SKILL::structured-fuzzer`

## Description
Structured Fuzzer

## Properties
- **skill_type**: verification
- **source_type**: python_module
- **source_path**: system_v4/skills/structured_fuzzer.py
- **status**: active
- **applicable_layers**: ["SIM_EVIDENCED"]
- **applicable_trust_zones**: ["SIM_EVIDENCED"]
- **applicable_graphs**: []
- **inputs**: ["runtime_state"]
- **outputs**: ["fuzz_result", "witness"]
- **adapters**: {"shell": "system_v4/skills/structured_fuzzer.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[coupled_structural_evidence_ladders]]
