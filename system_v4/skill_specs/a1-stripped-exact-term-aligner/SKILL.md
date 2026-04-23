---
skill_id: a1-stripped-exact-term-aligner
name: a1-stripped-exact-term-aligner
description: Resolve exact stripped-term admissibility for a bounded A1 alias term, write an explicit correction audit, and re-materialize the stripped owner graph from the corrected doctrine.
skill_type: correction
source_type: repo_skill
applicable_layers: [A1_STRIPPED]
applicable_graphs: [dependency]
inputs: [a1_stripped_graph_v1, a1_cartridge_graph_v1, a1_live_family_hint_coverage, a1_entropy_diversity_alias_lift_pack, a1_cartridge_reviews]
outputs: [a1_stripped_exact_term_alignment_audit, a1_stripped_graph_v1]
related_skills: [a1-stripped-graph-builder, a1-cartridge-graph-builder, nested-graph-layer-auditor, graph-capability-auditor]
capabilities:
  can_write_repo: true
  can_only_propose: false
tool_dependencies: []
provenance: "repo-grounded A1 exact-term correction lane"
adapters:
  codex: system_v4/skill_specs/a1-stripped-exact-term-aligner/SKILL.md
  gemini: system_v4/skill_specs/a1-stripped-exact-term-aligner/SKILL.md
  shell: system_v4/skills/a1_stripped_exact_term_aligner.py
---

# A1 Stripped Exact Term Aligner

Use this skill when a bounded A1 stripped alias term may have been promoted
above the exact status supported by current repo-held doctrine.

## Purpose

- audit one exact stripped term against the live A1 family doctrine
- preserve the exact-term contradiction explicitly instead of silently smoothing it
- re-materialize the stripped owner graph from the corrected exact-term read

## Execute Now

1. Load:
   - `system_v4/a1_state/a1_stripped_graph_v1.json`
   - `system_v4/a1_state/a1_cartridge_graph_v1.json`
   - `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
   - `system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md`
   - `system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md`
   - `system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
2. Decide the exact status of `pairwise_correlation_spread_functional`.
3. If the term is still witness-side, do not keep it in the stripped owner graph.
4. Emit:
   - updated `a1_stripped_graph_v1.json`
   - `A1_STRIPPED_EXACT_TERM_ALIGNMENT__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.md`

## Quality Gates

- Do not upgrade the exact term because of family-level passenger status on a different term.
- Do not keep a witness-only exact term in the stripped owner graph if the stripped-layer contract excludes it.
- Do not claim a replacement stripped landing already exists unless a current repo-held doctrine surface says so.
