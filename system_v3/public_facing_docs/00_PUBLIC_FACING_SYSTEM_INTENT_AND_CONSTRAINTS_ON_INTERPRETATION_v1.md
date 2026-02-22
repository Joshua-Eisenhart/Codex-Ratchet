# Public-Facing System Intent and Constraints on Interpretation (v1)
Status: PUBLIC / NONCANON (explanatory only)
Date: 2026-02-20

This document exists to prevent common misreadings when encountering the project for the first time.

## What This System Is
This project is a specification-driven, staged constraint engine that incrementally builds a **canonical constraint surface**.

It is designed to start with only two root constraints:
- `F01_FINITUDE` (finite encodability / finite computation as a hard reality constraint)
- `N01_NONCOMMUTATION` (order matters; no commutative reordering as a default)

The system then:
- proposes candidate structures (high entropy)
- compiles them into strict artifacts (entropy compression boundary)
- admits/rejects/parks them deterministically (kernel)
- demands executable evidence (sims) plus explicit failed alternatives (graveyard)

The intended long-term behavior is attractor-basin formation: as constraints tighten, fewer structures survive; those survivors define an “allowed manifold” of structure.

## What This System Is NOT
- Not a “workflow OS” where a kernel schedules tasks and maintains a world-model.
- Not a probabilistic planner; confidence/probability are not kernel primitives.
- Not a conventional proof assistant (Lean/Coq/Isabelle). Admission is not “axiom → theorem.”
- Not “physics simulation first.” Sims are mathematical/evidence harnesses for constraint-surviving structures.
- Not “classical math with new labels.” Classical defaults are treated as suspect until explicitly earned.

## Canon vs Noncanon (Authority Boundary)
- Canonical authority lives in the **constraint kernel output** (admissions + evidence links + deterministic snapshots).
- High-entropy text, analogies, jargon, and cross-domain mapping are allowed only *above* the boundary and must not leak into kernel artifacts.

## Non-Negotiables (Project-Level)
- Root constraints `F01_FINITUDE` and `N01_NONCOMMUTATION` are not “tunable policies.”
- Every meaningful survivor must be backed by:
  - positive sim evidence
  - negative sim evidence
  - explicit failed alternatives in a graveyard

## Typical Failure Modes (Do Not Do These)
- Treating the system as “just semantics / word games” and ignoring sim evidence + graveyard.
- Smuggling classical primitives as if they were harmless defaults (identity, equality, metrics, time, probability).
- Collapsing roles (e.g., letting the kernel invent candidates, or letting high-entropy notes become canon).
- Using jargon labels inside canon instead of keeping them as overlays (Rosetta dictionaries).

## Where to Start (Repo Pointers)
- User’s intent and scope (authoritative): `system_v3/a2_state/INTENT_SUMMARY.md`
- Interpretive overlay (explicitly non-authoritative): `system_v3/a2_state/MODEL_CONTEXT.md`
- Implementation-facing specs (noncanon drafts): `system_v3/specs/`

