# Current Authoritative Stack Index

**Date:** 2026-03-29  
**Purpose:** Compact post-cleanup authority index so controller, Codex, Claude Code, and Antigravity reference the same owner surfaces.  
**Discipline:** No theory expansion. No re-ranking. No new doctrine.

Navigation shortcut:

- If you need one-click entry for live docs, use [DOCS_QUICK_NAVIGATION.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/DOCS_QUICK_NAVIGATION.md).
- Inventory command: `./system_v4/tools/doc_inventory.sh --all` (active vs superseded classification by packet status).

## 1. Authority Surfaces

These are the current owner surfaces for the live stack.

### 1.1 Controller authority

- `THREAD_CONSOLIDATION_CONTROLLER.md`
  - controller thread is the authority for Ax0 integration, bounded worker routing, stop rules, and final integration of compact sync surfaces
  - Ax0 doctrine ranking is not delegated back to side threads
- `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md`
  - controller-grade Ax0 integration summary for `earned`, `live but open`, `killed or demoted`, and `still unvalidated`
  - summary surface only; does not replace the narrower owner packets below

### 1.2 Ax0 owner stack

- `CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`
  - authority for build order separation: constraints -> manifold -> geometry -> allowed math -> `Ax0`
- `AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`
  - authority for bridge-layer contract, bridge families, executable evidence, killed bridge options, and bridge-side gaps
- `AXIS0_CUT_TAXONOMY.md`
  - authority for cut legitimacy, current cut-family status, killed or demoted cut families, and cut-side admission tests
- `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`
  - compact operator handoff card for the current kernel -> bridge -> cut read; compressed surface only, not a replacement for owner packets

### 1.3 Thread B authority

- `THREAD_B_STACK_AUDIT.md`
  - authority for current Thread B staging status, surviving surfaces, resolved cleanup items, and bounded next steps
  - Thread B remains staging-only and does not own canon, permit, or bridge/cut closure

## 2. Support Surfaces

These remain live as secondary support under the authority surfaces above.

### 2.1 Ax0 support surfaces

- `AXIS0_TYPED_SHELL_CUT_CONTRACT.md`
  - minimum doctrine-facing cut target for a strict shell bridge
- `AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md`
  - minimum executable cut target for `Xi_hist`
- `AXIS0_TYPED_CUT_SYNC_CARD.md`
  - non-equivalence lock between typed shell and typed history targets
- `AXIS0_XI_HIST_EMISSION_PACKET.md`
  - emission-side support for the live `Xi_hist` bridge family
- `AXIS0_XI_HIST_STRICT_OPTIONS.md`
  - strict history replacement packet; support, not top-level authority
- `AXIS0_XI_SHELL_STRICT_OPTIONS.md`
  - strict shell replacement packet; support, not top-level authority
- `AXIS0_XI_REF_STRICT_OPTIONS.md`
  - point-reference support packet and cut-role tightening surface
- `AXIS0_BRIDGE_RELATION_PACKET.md`
  - support surface for bridge-family relation locks
- `AXIS0_BRIDGE_CLOSEOUT_CARD.md`
  - support closeout card for compact bridge-state synchronization
- `AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md`
  - shell algebra option-space support surface
- `AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md`
  - shell-local microscopic option-space support surface

### 2.2 Thread B support surfaces

- `THREAD_B_TERM_ADMISSION_MAP.md`
  - staging owner packet for term-state admission
- `THREAD_B_LEXEME_ADMISSION_CANDIDATES.md`
  - staging lexeme-admission support surface
- `THREAD_B_LEXEME_REGISTRY_COLLISION_CHECK.md`
  - collision audit for current lexeme tiers; preserve the hard fence on `coherent_information_relation`
- `THREAD_B_STAGING_VALIDATION_PACKET.md`
  - completed worker-lane validation packet: validated / blocked / not allowed yet
- `THREAD_B_LANE_HANDOFF_PACKET.md`
  - completed worker-lane closeout/context packet; useful audit history, but not current routing authority
- `THREAD_B_ENTROPY_EXPORT_VALIDATION.md`
  - current entropy export validation surface
- `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`
  - current preferred entropy review surface for the safe VN + MI split
- `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md`
  - background entropy audit lineage; not the preferred active entropy surface
- `THREAD_B_AXIS_MATH_EXPORT_BLOCK_REVIEW.md`
  - current axis export review surface
- `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md`
  - review-only Ax1 antecedent shape for derived-axis export lineage
- `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md`
  - review-only Ax4 derived-axis shape; depends on the Ax1 antecedent review block
- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md`
  - current plural candidate staging packet
- `THREAD_B_SIGNED_AX0_DEFERRED_PACKET.md`
  - deferred signed `Ax0` reserve packet; keep fenced below current export readiness and permit decisions
- `THREAD_B_CONSTRAINT_RATCHET_CARD.md`
  - B-thread-facing root-first constraint card
- `RETURN_QUEUE_STATUS_CARD.md`
  - compact controller card for what still remains live in `system_v4/thread_returns`
- `AXIS_MATH_BRANCH_MAP.md`
  - routing-only support surface; must not outrank newer owner maps
- `DOC_SUPERSEDE_CLEANUP_CARD.md`
  - cleanup support card for supersede and scratch handling in the Thread B export cluster

## 3. Superseded Surfaces

These should not be referenced as active owner doctrine or active pipeline authority.

### 3.1 Thread B superseded

- `THREAD_B_ENTROPY_EXPORT_CANDIDATES.md`
  - superseded by `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` and `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`
- `THREAD_B_ENTROPY_EXPORT_PACKET.md`
  - superseded by `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` and `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`
- `THREAD_B_ENTROPY_MATH_TERM_PACKET.md`
  - superseded by `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`
- `THREAD_B_ENTROPY_MATH_TERM_RUNBOOK.md`
  - stale runbook; superseded by the audit/admission/review path
- `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md`
  - stale runbook below the current validation/review stack
- `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md`
  - stale generic runbook replaced by narrower owner-specific review surfaces
- `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md`
  - stale runbook once validation owner packet exists
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_PACKET.md`
  - intermediate staging surface now outranked by the split export plus validation/review stack
- `THREAD_B_ENTROPY_MATH_TERM_ONLY_RUNBOOK.md`
  - stale runbook for the intermediate math-term-only packet

### 3.2 Scratch / retracted

- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md`
  - singular scratch/retracted artifact; do not treat as active
- `AXIS_MATH_BRANCHES_MAP.md`
  - superseded for current routing use by `AXIS_MATH_BRANCH_MAP.md`; retain only as an older broader extraction surface

### 3.3 Killed or demoted within live owner packets

- raw local `L|R` as sufficient bridge doctrine
  - killed as sufficient; control only
- uncoupled pure-product `L|R` as final doctrine cut
  - demoted to control only
- old shell-strata pointwise implementation / old shell-strata pointwise cut
  - killed as strict shell solution / strict pointwise shell solution
- single-spinor, single reduced density, and raw `eta`-only cut stand-ins
  - killed as legitimate final cut objects
- runtime `GA0` as doctrine object
  - demoted to proxy only

## 4. Still-Open Items

These remain open after cleanup and should stay marked open rather than silently closed.

### 4.1 Ax0 open items

- final canon `Xi` is open
- final doctrine-level cut `A|B` is open
- exact shell algebra for `A_r|B_r` is open
- exact microscopic meaning of `I_r|B_r` is open
- typed shell cut contract exists, but exact shell algebra is still open
- typed history-window cut contract exists, but exact family is still open
- final doctrinal role of the point-reference cut family is open and secondary

### 4.2 Thread B open items

- actual Thread B export readiness is still open
- coherent-information permit work is still blocked by bridge/cut dependence
- deferred signed `Ax0` packet promotion is still open
- full lexeme registry registration is still open after the collision-audit pass
- axis export promotion is still open

### 4.3 Duplicate / cleanup-open items

- `THREAD_B_AXIS_MATH_EXPORT_CANDIDATE.md` vs `THREAD_B_AXIS_MATH_EXPORT_CANDIDATES.md`
  - singular/plural duplicate family remains only partially resolved
- overlapping Thread B export runbook layer
  - `THREAD_B_ENTROPY_EXPORT_RUNBOOK.md`, `THREAD_B_ENTROPY_EXPORT_VALIDATION_RUNBOOK.md`, and `THREAD_B_EXPORT_BLOCK_REVIEW_RUNBOOK.md` remain as stale overlap below the current owner stack
