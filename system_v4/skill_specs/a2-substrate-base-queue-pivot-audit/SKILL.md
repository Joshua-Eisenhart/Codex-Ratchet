---
skill_id: a2-substrate-base-queue-pivot-audit
name: a2-substrate-base-queue-pivot-audit
description: Audit whether the dormant substrate-base family slice should replace the current entropy-selected A1 queue candidate, and update the live current A1 queue surfaces only if the existing queue selector admits it.
skill_type: correction
source_type: repo_skill
applicable_layers: [A2_LOW_CONTROL]
applicable_graphs: [concept, dependency]
inputs: [current_a1_queue_packet, current_a1_candidate_registry, substrate_base_family_slice, substrate_family_campaign, queue_status_surface_spec]
outputs: [substrate_base_queue_pivot_audit, current_a1_candidate_registry, current_a1_queue_packet, current_a1_queue_note]
related_skills: [graph-capability-auditor, nested-graph-layer-auditor, a1-jargoned-graph-builder]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A2 control lane for substrate-base queue pivot admission"
adapters:
  codex: system_v4/skill_specs/a2-substrate-base-queue-pivot-audit/SKILL.md
  gemini: system_v4/skill_specs/a2-substrate-base-queue-pivot-audit/SKILL.md
  shell: system_v4/skills/a2_substrate_base_queue_pivot_audit.py
---

# A2 Substrate Base Queue Pivot Audit

Use this skill when the direct entropy executable branch is honestly paused and
the question becomes whether the dormant substrate-base family slice should be
admitted into the live A1 queue.

## Purpose

- let A2 own the queue-routing correction rather than making A1 improvise
- prove the pivot with the existing queue selector instead of handwaving it
- update the live current queue surfaces only if the selector really emits a ready packet

## Execute Now

1. Load:
   - `system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
   - `system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`
   - `system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json`
   - `system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
   - `system_v3/a1_state/A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md`
   - `system_v3/a1_state/A1_ROSETTA_BATCH__PROBE_OPERATOR__v1.md`
   - `system_v3/a1_state/A1_CARTRIDGE_REVIEW__PROBE_OPERATOR__v1.md`
   - `system_v3/run_anchor_surface/RUN_ANCHOR__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md`
   - `system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
   - `system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md`
2. Prove the pivot via the existing queue selector in a temp staging area first.
3. Copy the new current registry and queue surfaces into the live current paths only if:
   - the selector emits `READY_FROM_NEW_A2_HANDOFF`
   - the selected family slice is the substrate-base owner slice
   - the ready packet exists on disk
4. Emit:
   - `system_v4/a2_state/audit_logs/A2_SUBSTRATE_BASE_QUEUE_PIVOT_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Fail closed if the handoff packet is missing or structurally invalid.
- Fail closed if the doctrine-backed substrate evidence is incomplete.
- Do not mutate the live current queue surfaces until the temp selector proof succeeds.
- Do not treat this as an entropy-branch unpause.
