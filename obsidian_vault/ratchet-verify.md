---
id: "SKILL::ratchet-verify"
type: "SKILL"
layer: "SKILL_REGISTRY"
authority: "SOURCE_CLAIM"
---

# ratchet-verify
**Node ID:** `SKILL::ratchet-verify`

## Description
Quality gate verification for graph concepts

## Properties
- **skill_type**: verification
- **source_type**: repo_skill
- **source_path**: system_v4/skills/ratchet-verify/SKILL.md
- **status**: active
- **applicable_layers**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_trust_zones**: ["A2_HIGH_INTAKE", "A2_MID_REFINEMENT", "A2_LOW_CONTROL"]
- **applicable_graphs**: ["concept", "contradiction", "dependency"]
- **inputs**: ["concept_id or batch"]
- **outputs**: ["Verification report", "PROMOTED edges"]
- **adapters**: {"codex": "system_v4/skills/ratchet-verify/SKILL.md", "gemini": "system_v4/skills/ratchet-verify/SKILL.md"}
- **related_skills**: ["ratchet-reduce", "ratchet-reflect", "ratchet-reweave"]

## Outward Relations
- **SKILL_FOLLOWS** → [[ratchet-reduce]]
- **SKILL_FOLLOWS** → [[ratchet-reflect]]
- **SKILL_FOLLOWS** → [[ratchet-reweave]]
- **RELATED_TO** → [[ratchet-reduce]]
- **RELATED_TO** → [[ratchet-reflect]]
- **RELATED_TO** → [[ratchet-reweave]]
- **SKILL_OPERATES_ON** → [[unitary_thread_b_ratchet]]

## Inward Relations
- [[ratchet-reduce]] → **SKILL_FOLLOWS**
- [[ratchet-reflect]] → **SKILL_FOLLOWS**
- [[ratchet-reweave]] → **SKILL_FOLLOWS**
- [[a0-compiler]] → **RELATED_TO**
- [[a1-brain]] → **RELATED_TO**
- [[a1-cartridge-assembler]] → **RELATED_TO**
- [[a1-distiller]] → **RELATED_TO**
- [[a1-from-a2-distillation]] → **RELATED_TO**
- [[a1-rosetta-mapper]] → **RELATED_TO**
- [[a1-rosetta-stripper]] → **RELATED_TO**
- [[a1-routing-state]] → **RELATED_TO**
- [[a2-a1-memory-admission-guard]] → **RELATED_TO**
- [[a2-brain-refresh]] → **RELATED_TO**
- [[a2-graph-refinery]] → **RELATED_TO**
- [[a2-thermodynamic-purge]] → **RELATED_TO**
- [[b-adjudicator]] → **RELATED_TO**
- [[b-kernel]] → **RELATED_TO**
- [[external-research-return-ingest]] → **RELATED_TO**
- [[generate-doc-queue]] → **RELATED_TO**
- [[graveyard-router]] → **RELATED_TO**
- [[pro-return-instant-audit]] → **RELATED_TO**
- [[ratchet-a2-a1]] → **RELATED_TO**
- [[ratchet-integrator]] → **RELATED_TO**
- [[rosetta-v2]] → **RELATED_TO**
- [[run-a1-eval-slice]] → **RELATED_TO**
- [[run-real-ratchet]] → **RELATED_TO**
- [[runtime-graph-bridge]] → **RELATED_TO**
- [[safe-run-maintenance]] → **RELATED_TO**
- [[sim-engine]] → **RELATED_TO**
- [[sim-holodeck-engine]] → **RELATED_TO**
- [[thread-closeout-auditor]] → **RELATED_TO**
- [[v4-graph-builder]] → **RELATED_TO**
- [[v4-tape-writer]] → **RELATED_TO**
- [[graveyard-lawyer]] → **RELATED_TO**
- [[ratchet-overseer]] → **RELATED_TO**
- [[ratchet-reduce]] → **RELATED_TO**
- [[ratchet-reflect]] → **RELATED_TO**
- [[ratchet-reweave]] → **RELATED_TO**
- [[runtime-state-kernel]] → **RELATED_TO**
- [[z3-constraint-checker]] → **RELATED_TO**
- [[z3-cegis-refiner]] → **RELATED_TO**
- [[property-pressure-tester]] → **RELATED_TO**
- [[differential-tester]] → **RELATED_TO**
- [[structured-fuzzer]] → **RELATED_TO**
- [[model-checker]] → **RELATED_TO**
- [[fep-regulation-operator]] → **RELATED_TO**
- [[frontier-search-operator]] → **RELATED_TO**
