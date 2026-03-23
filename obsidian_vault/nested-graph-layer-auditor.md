---
id: "SKILL::nested-graph-layer-auditor"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# nested-graph-layer-auditor
**Node ID:** `SKILL::nested-graph-layer-auditor`

## Description
Audit each queued nested-graph layer against build program, boot surfaces, and owner surfaces.

## Properties
- **skill_type**: audit
- **source_type**: repo_skill
- **source_path**: system_v4/skill_specs/nested-graph-layer-auditor/SKILL.md
- **status**: active
- **applicable_layers**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_trust_zones**: ["INDEX", "A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL", "A1_JARGONED", "A1_STRIPPED", "A1_CARTRIDGE"]
- **applicable_graphs**: ["concept", "dependency", "rosetta"]
- **inputs**: ["nested_graph_build_program", "build_queue_status_packet"]
- **outputs**: ["nested_graph_layer_audit_report", "nested_graph_layer_audit_note"]
- **adapters**: {"codex": "system_v4/skill_specs/nested-graph-layer-auditor/SKILL.md", "gemini": "system_v4/skill_specs/nested-graph-layer-auditor/SKILL.md", "shell": "system_v4/skills/nested_graph_layer_auditor.py"}
- **related_skills**: ["graph-capability-auditor", "ratchet-a2-a1", "thread-run-monitor"]

## Outward Relations
- **RELATED_TO** → [[graph-capability-auditor]]
- **RELATED_TO** → [[ratchet-a2-a1]]
- **RELATED_TO** → [[thread-run-monitor]]
- **SKILL_OPERATES_ON** → [[graph_as_control_substrate]]

## Inward Relations
- [[a1-cartridge-graph-builder]] → **RELATED_TO**
- [[a1-entropy-bridge-helper-lift-pack]] → **RELATED_TO**
- [[a1-entropy-diversity-alias-lift-pack]] → **RELATED_TO**
- [[a1-entropy-structure-decomposition-control]] → **RELATED_TO**
- [[a1-first-entropy-structure-campaign]] → **RELATED_TO**
- [[a1-jargoned-graph-builder]] → **RELATED_TO**
- [[a1-jargoned-scope-aligner]] → **RELATED_TO**
- [[a1-stripped-exact-term-aligner]] → **RELATED_TO**
- [[a1-stripped-graph-builder]] → **RELATED_TO**
- [[a1-stripped-term-plan-aligner]] → **RELATED_TO**
- [[a2-colder-witness-execution-consolidation]] → **RELATED_TO**
- [[a2-entropy-bridge-helper-decomposition-control]] → **RELATED_TO**
- [[a2-high-intake-graph-builder]] → **RELATED_TO**
- [[a2-low-control-graph-builder]] → **RELATED_TO**
- [[a2-mid-refinement-graph-builder]] → **RELATED_TO**
- [[a2-refinement-for-a1-stripped-landing]] → **RELATED_TO**
- [[a2-stage1-operatorized-entropy-head-refinement]] → **RELATED_TO**
- [[a2-substrate-base-queue-pivot-audit]] → **RELATED_TO**
- [[graph-capability-auditor]] → **RELATED_TO**
- [[identity-registry-builder]] → **RELATED_TO**
- [[identity-registry-overlap-quarantine]] → **RELATED_TO**
