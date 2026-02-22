# A-Thread Bootpack Projection (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Project the enforceable A-thread operational rules into v3 spec surface so A1/A0 behavior remains aligned with Thread A boot discipline.

## Authority Source
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACK_THREAD_A_v2.60.md`

## Projected Rule Set (Enforceable Core; Summarized)
These rules are originally framed for a chat UI (atomic copy/paste boxes). In automation, the same discipline applies as:
- one artifact per file/message
- no prose mixed into kernel-facing artifacts
- explicit provenance pinning when gates are active

### Tone + Epistemics
- `A-001 NO_SMOOTHING`: no motivational tone; use `UNKNOWN` when missing.
- `A-002 NO_IMPLICIT_MEMORY`: do not claim “already established” without a pasted artifact (snapshot/report).
- `A-003 NO_CHOICE_POLICY`: do not push mode selection to user; default to full structured output.

### Atomicity / Artifact Discipline
- `A-006 ATOMIC COPY/PASTE BOXES`: one atomic action per box (automation analog: one atomic artifact per file).
- `A-015 ARTIFACT_DRAFT_PROSE_BAN`: artifact sections may contain only artifacts (no prose).

### Sentence-Term + Glyph Discipline (anti-smuggling)
- `A-017 SENTENCE_TERM_POLICY`: underscore compounds must be treated as component-wise; never assume admissibility.
- `A-018 FORMULA_SYMBOL_POLICY`: '=' is forbidden unless `equals_sign` is canonically allowed (per B).
- `A-019 GLYPH_POLICY`: operator glyphs in formula are ratcheted terms; do not assume notation.

### Provenance Header Gate Injection
- `A-110 RULESET_SHA256_HEADER_INJECTION`: include `RULESET_SHA256: <hex64>` only when pinned (do not invent).
- `A-116 MEGABOOT_SHA256_HEADER_INJECTION`: include `MEGABOOT_SHA256: <hex64>` only when pinned (do not invent).
- `A-117 COMBINED_GATE_HEADER_INJECTION`: include both when both are pinned.

### Tracks (TEACH guide; informs A1/A2 planning)
- `A-020 FOUNDATIONAL_BUILD_NOTE`: maintain parallel tracks (e.g., topology-first vs pragmatic QIT-first) without claiming correctness; convergence is by replay + comparison.

## v3 Mapping Targets
- A1 planning/repair behavior:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- A0 compile/header behavior:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/04_A0_COMPILER_SPEC.md`
- B grammar and symbol gating:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/03_B_KERNEL_SPEC.md`
- Conformance gates:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`

## Projection Notes
- Thread-A route/box macros are operational scaffolding, not canon authority.
- Canon authority remains in B.
- This projection does not alter B acceptance semantics.
