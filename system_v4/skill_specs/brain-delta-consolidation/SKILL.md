---
name: brain-delta-consolidation
description: Consolidate many bounded upper-loop outputs into a small number of append-safe A2 and A1 deltas for the Codex Ratchet system. Use when refreshed A2 notes, A1 cross-audits, external-research audits, closeout packets, or family summaries exist and need to be merged without contradiction smoothing or owner-surface drift.
---

# Brain Delta Consolidation

Use this skill when multiple bounded outputs exist and the system needs a small, traceable delta set instead of more raw packets.

## Core rules

- Consolidate without contradiction smoothing.
- Keep explicit source anchors.
- Separate A2 updates from A1 impacts.
- Preserve unresolved tensions instead of forcing closure.
- Do not let helper summaries or staging packets become active owner surfaces by accident.

## Primary source surfaces

- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
- `system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`

## Common consolidation inputs

- refreshed A2 update notes
- A1 cross-audits
- A1 exec summaries
- integration batch notes
- external-research audit results
- thread closeout packets
- bounded family summaries

## Workflow

1. Gather only the bounded outputs relevant to one consolidation scope.
2. Classify each input:
   - A2 update candidate
   - A1 impact candidate
   - unresolved tension
   - hold/revisit item
   - staging/helper artifact only
3. Check source anchors and active-owner targets.
4. Merge repeated findings only when they are truly the same claim.
5. Preserve contradictions and time-ordered tensions explicitly.
6. Emit a small delta set:
   - `A2_UPDATE_DELTA`
   - `A1_IMPACT_DELTA`
   - `UNRESOLVED_TENSIONS`
   - `HOLD_OR_REVISIT`
7. Route admitted deltas through `a2-a1-memory-admission-guard` before active-memory writes.

## Output discipline

- keep deltas bounded
- prefer append-safe updates over broad rewrites
- name competing interpretations explicitly
- preserve role placement:
  - head
  - passenger
  - witness-only
  - residue
  when relevant

## Guardrails

- Do not turn one elegant summary into a replacement for family-specific source work.
- Do not merge A2 understanding and A1 proposal content into one undifferentiated note.
- Do not collapse broad survival and narrow executable landing into the same claim.
- Do not consolidate staging packets directly into active owner surfaces without anchor checks.
- If the scope is still too broad, split it before consolidating.
