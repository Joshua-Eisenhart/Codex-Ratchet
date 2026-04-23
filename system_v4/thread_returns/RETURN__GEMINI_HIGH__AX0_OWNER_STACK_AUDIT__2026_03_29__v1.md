# RETURN: Ax0 Owner Stack Audit

**Date:** 2026-03-29
**Agent:** Antigravity (Gemini High)
**Status:** SUCCESS / UNBLOCKED (No doctrine changed, no items smoothed)

## 1. Audit Summary
The Ax0 owner stack successfully holds the core logical guardrails: raw `L|R` is demoted, old shell-strata is killed, and the ranking of candidates (history vs shell vs point-reference) is strictly synchronized across all 4 reviewed documents. 

However, there is a significant authority contradiction regarding what constitutes the "Owner Stack", and several overlaps that create a maintenance hazard for open items.

## 2. Authority Contradiction: Index vs State Card
There is a direct authority collision between the master index and the state card regarding the membership of the Ax0 owner stack.
- **The Index (`CURRENT_AUTHORITATIVE_STACK_INDEX.md`)** defines the Ax0 owner stack precisely as 4 files:
  - `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`
  - `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`
  - `AXIS0_CUT_TAXONOMY.md`
  - `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`
  It explicitly classifies `AXIS0_TYPED_SHELL_CUT_CONTRACT.md`, `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md`, `AXIS0_XI_HIST_EMISSION_PACKET.md`, `AXIS0_TYPED_CUT_SYNC_CARD.md`, and `AXIS0_BRIDGE_CLOSEOUT_CARD.md` as "2.1 Ax0 support surfaces".
- **The State Card (`AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`)** contradicts this in Section 6 ("Owner Stack"):
  - It completely omits `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`.
  - It elevates all 5 of those "support surfaces" back into the list of top-level Owner Stack files.
- **Verdict**: Authority leakage. Support surfaces are slipping back into owner-level listings, and an official owner surface was dropped from the state card.

## 3. Stale Overlap & Maintenance Risks
Multiple files are currently maintaining redundant lists of open items and cross-referencing out-of-scope support files, which guarantees stale overlap if any single branch advances:
- **Redundant Open Item Registries**: The exact same unresolved dependencies (e.g., "exact shell algebra", "doctrine-level cut `A|B`", "exact `Xi_hist` construction") are listed as tables/lists in:
  - `CURRENT_AUTHORITATIVE_STACK_INDEX.md` (Section 4.1)
  - `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md` (Section 2)
  - `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md` (Section 10)
  - `AXIS0_CUT_TAXONOMY.md` (Section 10)
  If any one of these open items (like the shell algebra) is closed out, it must be manually updated in 4 separate documents to avoid drift.
- **Cross-Domain Reference Bleed**: 
  - `AXIS0_CUT_TAXONOMY.md` rightfully acknowledges it does not own strict bridge constructions, yet Section 6.3 maintains explicit links to `AXIS0_XI_SHELL_STRICT_OPTIONS.md` and `AXIS0_XI_HIST_STRICT_OPTIONS.md`.
  - `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md` rightfully defers the cut taxonomy, yet maintains internal links to `AXIS0_TYPED_SHELL_CUT_CONTRACT.md` and `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md`.
  This cross-linking makes the support tree highly entangled and dilutes the boundaries of authority.

## 4. Solid Doctrine (No Action Needed)
The anti-smoothing constraints are holding perfectly against regressions. The core logic of the stack is sound:
- Raw local `L|R` is consistently classified as control-only across all specs.
- Old shell-strata logic is dead and successfully blocked from being implicitly rebranded as doctrine.
- The separation between the strongest live bridge (`Xi_hist`) and the strongest doctrine-facing cut (shell/interior-boundary) is respected globally without premature unification.
