---
id: "SKILL::run-real-ratchet"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# run-real-ratchet
**Node ID:** `SKILL::run-real-ratchet`

## Description
Full autonomous ratchet loop

## Properties
- **skill_type**: runner
- **source_type**: runner
- **source_path**: system_v4/skills/run_real_ratchet.py
- **status**: active
- **applicable_layers**: ["A1_STRIPPED", "A1_CARTRIDGE", "B_ADJUDICATED", "SIM_EVIDENCED"]
- **applicable_trust_zones**: ["A1_STRIPPED", "A1_CARTRIDGE", "B_ADJUDICATED", "SIM_EVIDENCED"]
- **applicable_graphs**: ["dependency", "runtime"]
- **inputs**: []
- **outputs**: []
- **adapters**: {"shell": "system_v4/skills/run_real_ratchet.py"}
- **related_skills**: []

## Outward Relations
- **RELATED_TO** → [[ratchet-verify]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]
- **SKILL_OPERATES_ON** → [[DETERMINISTIC_KERNEL_PIPELINE]]
- **SKILL_OPERATES_ON** → [[eight_phase_gate_pipeline]]
- **SKILL_OPERATES_ON** → [[p0_through_p7_build_phases]]

## Inward Relations
- [[automation-controller]] → **RELATED_TO**
- [[ratchet-prompt-stack]] → **RELATED_TO**
- [[thread-dispatch-controller]] → **RELATED_TO**
- [[thread-run-monitor]] → **RELATED_TO**
- [[ratchet-overseer]] → **RELATED_TO**
