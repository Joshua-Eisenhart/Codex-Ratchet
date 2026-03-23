---
name: a2-a1-memory-admission-guard
description: Audit or gate candidate writes into active A2 and A1 memory surfaces for the Codex Ratchet system. Use when an update note, summary, index, proposal surface, thread packet, or derived helper surface may enter active A2/A1 memory and must be checked for surface class, provenance, write permission, and semantic hygiene.
---

# A2/A1 Memory Admission Guard

Use this skill when a surface may be appended, refreshed, or promoted into active A2 or A1 memory.

## Core rules

- This is an upper-memory guard, not a lower-loop truth gate.
- Derived surfaces do not become source corpus just because they are useful.
- Proposal surfaces do not become earned state by wording.
- If admission checks fail, reject from active memory or demote to `RUNTIME_ONLY` or `ARCHIVE_ONLY`.
- Keep one active owner surface per concern whenever possible.

## Owner docs

- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

## Surface classes

- `SOURCE_CORPUS`
- `DERIVED_A2`
- `PROPOSAL_A1`
- `PACKAGED_A0`
- `EVIDENCE_SIM`
- `EARNED_STATE`
- `RUNTIME_ONLY`
- `ARCHIVE_ONLY`

## Admission checks

1. Schema or shape validity
2. Explicit surface class
3. Layer write permission validity
4. Source refs or explicit runtime provenance
5. Append-only or provenance-safe write path
6. Semantic hygiene:
   - no fake canon labels
   - no truth-sounding A1 proposal naming
   - no source/derived class confusion
   - no derived helper surface outranking active owner docs

## Write permissions

- `A2` may write: `DERIVED_A2`
- `A1` may write: `PROPOSAL_A1`
- `A0` may write: `PACKAGED_A0`
- `SIM` may write: `EVIDENCE_SIM`
- `B` may write: `EARNED_STATE`

Use these as hard constraints for active-memory admission.

## Workflow

1. Identify the candidate surface and intended destination.
2. Classify the candidate surface.
3. Check whether the writing layer is allowed to write that class.
4. Check provenance:
   - source refs
   - runtime provenance
   - thread/sink lineage when relevant
5. Check whether the target is the active owner surface or a duplicate/stale competing surface.
6. Check semantic hygiene.
7. Decide exactly one:
   - admit
   - reject
   - demote to `RUNTIME_ONLY`
   - demote to `ARCHIVE_ONLY`
8. If admitted, record the class and provenance clearly in the update path.

## Guardrails

- Do not let summaries or indexes outrank source refs.
- Do not let A2/A1 self-summary recursion become active memory.
- Do not admit malformed closeout packets, helper indices, or overlay notes as owner surfaces.
- Do not silently rewrite class identity because a file sounds authoritative.
- If two active surfaces compete for the same concern, flag surface-creep risk explicitly.
