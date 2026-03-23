---
skill_id: a1-jargoned-scope-aligner
name: a1-jargoned-scope-aligner
description: Align the queued A1_JARGONED family scope with live packet-backed Rosetta fuel, minting only defensible anchored terms and preserving blocked scope residue explicitly.
skill_type: correction
source_type: repo_skill
applicable_layers: [A1_JARGONED]
applicable_graphs: [rosetta]
inputs: [rosetta_v2, a1_queue_candidate_registry, a2_to_a1_family_slice, system_graph_a2_refinery]
outputs: [rosetta_v2, a1_jargoned_handoff, a1_jargoned_scope_alignment_audit]
related_skills: [a1-jargoned-graph-builder, a1-rosetta-stripper, identity-registry-builder, nested-graph-layer-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A1 boundary correction lane"
adapters:
  codex: system_v4/skill_specs/a1-jargoned-scope-aligner/SKILL.md
  gemini: system_v4/skill_specs/a1-jargoned-scope-aligner/SKILL.md
  shell: system_v4/skills/a1_jargoned_scope_aligner.py
---

# A1 Jargoned Scope Aligner

Use this skill when `A1_JARGONED` is blocked because the queued family slice
does not match live packet-backed Rosetta fuel.

## Purpose

- align the A1-jargoned handoff to the queue-selected family slice
- mint only Rosetta packets with live A2 anchors
- preserve blocked scope terms explicitly instead of inventing them

## Execute Now

1. Load:
   - `system_v4/a1_state/rosetta_v2.json`
   - `system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
   - `system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json`
   - `system_v4/a2_state/graphs/system_graph_a2_refinery.json`
2. Mint only those DUAL_STACKED_ENGINE terms that have exact live A2 anchors.
3. Rewrite the A1-jargoned handoff to the aligned family slice.
4. Emit:
   - updated `rosetta_v2.json`
   - updated A1-jargoned handoff
   - `A1_JARGONED_SCOPE_ALIGNMENT_AUDIT__2026_03_20__v1.md`

## Quality Gates

- Do not mint `left_weyl_spinor_engine` or `right_weyl_spinor_engine` without exact live packet-backed anchors.
- Do not claim executable landing for minted terms.
- Keep blocked terms explicit in the audit and handoff metadata.
