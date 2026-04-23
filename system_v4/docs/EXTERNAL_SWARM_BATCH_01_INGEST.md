# External Swarm Batch 01 Ingest

**Date:** 2026-03-29  
**Purpose:** Controller-side ingest summary for the first large external-thread return batch in `system_v4/thread_returns/`.
**Live queue companion:** [RETURN_QUEUE_STATUS_CARD.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/RETURN_QUEUE_STATUS_CARD.md)

---

## 1. Accepted

These returns are accepted directly as useful controller support.

| Return | Classification | Why |
|---|---|---|
| `RETURN__GEMINI_HIGH__AX0_OWNER_STACK_AUDIT__2026_03_29__v1.md` | `accepted` | correctly identified the Ax0 owner/support mismatch between the authority index and the doctrine state card |
| `RETURN__SONNET__AUTHORITY_INDEX_CROSSCHECK__2026_03_29__v1.md` | `accepted` | correctly identified omission and classification gaps in the authority index |
| `RETURN__GEMINI_LOW__THREAD_B_REGISTRY_CHECK__2026_03_29__v1.md` | `accepted_with_fence` | Tier 1-3 registry-facing acceptance is useful; Tier 4 must keep hard fences verbatim |
| `RETURN__SONNET__THREAD_B_OVERREACH_HUNT__2026_03_29__v1.md` | `accepted` | correctly identified wording overreach in `THREAD_B_STACK_AUDIT.md` |
| `RETURN__OPUS__AX1_AX4_CHAIN_ATTACK__2026_03_29__v1.md` | `accepted_with_fence` | good REVIEW_ONLY attack surface; useful gaps for later fixup without changing doctrine |
| `RETURN__GEMINI_FLASH__DOC_INVENTORY_CLUSTER__2026_03_29__v1.md` | `accepted` | useful fast classification inventory |
| `RETURN__GEMINI_FLASH__CITATION_MAP_INVENTORY__2026_03_29__v1.md` | `accepted` | useful citation-cluster inventory for later cleanup |

---

## 2. Partial

These returns remain live in `system_v4/thread_returns` as bounded support or pressure, but should not be accepted wholesale.

| Return | Classification | Why |
|---|---|---|
| `RETURN__GEMINI_LOW__DUPLICATE_FAMILY_AUDIT__2026_03_29__v1.md` | `partial` | good duplicate-family classifications, but some runbook keep/supersede calls remain controller-open |
| `RETURN__SONNET__DUPLICATE_FAMILY_COLLAPSE_PLAN__2026_03_29__v1.md` | `partial` | good collapse plan, but some keep/supersede calls conflict with current controller choices |
| `RETURN__GEMINI_FLASH__NAMING_DRIFT_CLUSTER_AUDIT__2026_03_29__v1.md` | `partial` | useful naming drift inventory; treat as an inventory, not policy |
| `RETURN__GEMINI_FLASH__THREAD_B_NAMING_DRIFT__2026_03_29__v1.md` | `partial` | useful family-drift inventory, but one capitalization finding is already fixed on disk |
| `RETURN__GEMINI_HIGH__RIVAL_STACK_AUDIT__2026_03_29__v1.md` | `partial` | good dissent pressure, but keep as adversarial audit only |
| `RETURN__GEMINI_HIGH__OWNER_PACKET_GAP_HUNT__2026_03_29__v1.md` | `partial` | useful gap/fence pressure, but several asks are now superseded by the current authority index or reach beyond current controller need |
| `RETURN__GEMINI_LOW__DOC_CLEANUP_AUDIT__2026_03_29__v1.md` | `partial` | useful cleanup pressure, but it still pushes broader archive/delete actions than the current controller stack has not ratified wholesale |
| `RETURN__OPUS__SIM_TO_DOCTRINE_MISMATCH_AUDIT__2026_03_29__v1.md` | `partial` | useful caution about overreading sims, but some downgrade recommendations overreach current controller locks |

---

## 3. Archive Only

These returns should be retained as audit history but not used as live controller guidance.

| Return | Classification | Why |
|---|---|---|
| `RETURN__GPT_OSS__DISSENT_AUDIT__2026_03_29__v1.md` | `archive_only` | dissent redundancy lane only; no controller change adopted from it in this ingest pass |
| `RETURN__GEMINI_HIGH__ALTERNATE_AXIS_MAPPING_AUDIT__2026_03_29__v1.md` | `archive_only` | exploratory mapping-pressure audit; useful as background pressure, not active controller guidance |
| `RETURN__GEMINI_HIGH__DOC_CLEANUP_AUDIT__2026_03_29__v1.md` | `archive_only` | broader cleanup pressure that conflicts with settled controller choices on branch-map routing and archive scope; retain only as background history |
| `RETURN__OPUS__ANTI_SMOOTHING_STRESS_TEST__2026_03_29__v1.md` | `archive_only` | useful adversarial language audit, but the current authority stack already carries the accepted anti-smoothing fences directly |

---

## 4. Immediate Ingested Actions

These changes were accepted into the live controller stack from this batch:

1. align the Ax0 state card with the authority index by separating owner surfaces from support surfaces
2. add `AXIS0_CURRENT_DOCTRINE_STATE_CARD.md` to the authority index as a controller-grade summary surface
3. add `runtime GA0` proxy demotion to the authority index kill/demote list
4. tone down the overreach wording in `THREAD_B_STACK_AUDIT.md`
5. mark older Thread B export runbooks and the smaller Ax1 review-only card as superseded where the controller decision is now clear
6. resolve the branch-map duplicate in favor of `AXIS_MATH_BRANCH_MAP.md` for current routing use
7. tighten the Ax1/Ax4 review-only chain so Ax1 explicitly stays bridge/cut-independent, generator-gated, and branch-selector-only
8. remove the ghost `engine_composition_rule` dependency from the formal Ax4 derivation and fence local `U` / `E` ordering shorthand to block branch-name drift
9. demote older Thread B lane closeout and entropy-math-term-only packets to context/superseded status so they stop reading like active routing surfaces
10. separate the remaining live return queue into accepted-live support versus live-partial support and remove archive-only rows from the partial section
11. add `RETURN_QUEUE_STATUS_CARD.md` as the compact controller surface for the remaining live return queue
12. move background-only partial returns into `archive_only` status and out of `system_v4/thread_returns`
13. record that the partial queue intentionally retained state remains in force until its pressure is absorbed into owner/controller surfaces or explicitly downgraded

---

## 5. Still Open After Ingest

- final cleanup policy for stale Thread B runbooks and archive-only surfaces
- any promotion or permit path for Thread B export shapes
- any further Ax1/Ax4 changes beyond the current REVIEW_ONLY fence hardening
- partial queue intentionally retained until duplicate-family cleanup pressure and sim-to-doctrine caution are either absorbed into current owner/controller surfaces or explicitly downgraded to archive-only history
