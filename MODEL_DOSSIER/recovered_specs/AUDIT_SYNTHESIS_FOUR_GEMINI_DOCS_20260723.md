# Audit synthesis — the 2026-07-23 Gemini doc set
Auditors: codex1-luna (contracts vs repo), codex1-terra (governance vs stack), NVIDIA deepseek-v4-pro
(GPU doc vs hard-reject ledger), Grok 4.5 (orientation math+consistency), Claude (PDF classification,
synthesis). Full reports: AUDIT_orientation_doc_by_grok.md, AUDIT_gpu_doc_by_nvidia_deepseek.md
(codex verdicts recovered from session rollouts — their sandbox blocked Desktop writes).

## Verdicts by document

| Doc | Verdict | Blockers | Fix to usable |
|---|---|---|---|
| RATCHET_SYSTEM_MODEL_ORIENTATION (5515 ln) | Math SOUND (6/6 spot-checks verified w/ derivations: Hopf A, holonomy 2pi(m+n cos2eta), F=dA, 3 bipartitions, Schmidt licensing, DeltaE caution). Checksum 1-20 consistent; loop words never swapped. | 1: section 18 "verbatim invariant kernel" TRUNCATED mid-token — the exact block a fresh thread must preserve | Restore section 18 + one line pinning Axis-0 ROLE=locked vs cofield FORMULAS=candidate. Then safe to hand to a fresh Gemini. |
| GEMINI_GPU_GREAT_PROBLEMS (2494 ln) | CLEAN — zero blockers/majors. A genuine CORRECTION document: systematically rejects every hard-rejected claim (GPU-2^n, annealing-P!=NP, RH-circularity, NS/YM overclaims), realistic cuQuantum/annealer limits, T1-T5 tier ceilings enforced per campaign. | 0 | Usable NOW as the research-program manual, provided each campaign's special_seam.lift_obligation is completed pre-execution and no T4/T5 without independent mathematical review. |
| GEMINI_AGENT_OPERATING_CONTRACTS (2065 ln) | Future-state design presented adjacent to status. | 5: phantom companion doc; no negative-regression receipt; relies on DEAD `orchestration claimgate-steering`; abstract seal API != real ClaimGate commands; build order not receipt-backed | Repair the 5, re-ground on LEV_ATTACH_MAP (live seams: lev eval run absolute-path, lev exec --verifier). Until then: design fuel only. |
| GEMINI_EXECUTION_GOVERNANCE (1704 ln) | Proposal-heavy but honestly aimed: correctly targets the 3 REAL hostile gaps (dup-key/NaN/renamed-metric). Fixes NOT live; ClaimGate remains 7 HOLD/3 GAP; cloud = PRE-T0 on M1 16GB. | 0 hard, status-inflation risk | Usable as spec fuel with statuses downgraded to PROPOSED. |

## PDFs
- geminin chat 2 (65p): already fully audited by GEMINI_THREAD_GROUNDED_RECOVERY_AUDIT_20260723.md
  (hard-reject ledger + salvage table) — that audit checks out against repo receipts; treat as governing.
- gemini thread 2 v1 (53p): SECOND corrected-era thread. Late outputs = PROPOSED code written under the
  corrected discipline: (1) ClaimGateIntakeSupervisor — dup-key rejection via object_pairs_hook,
  recursive NaN/Inf guard, pydantic schema, version guard, digest receipts — DIRECTLY fixes 2 of the 3
  live hostile gaps (renamed_metric NOT addressed); (2) BoundedIsingCheckerboard4x4 — JAX comparator
  with consistent DeltaE convention + EXHAUSTIVE 16-site delta-vs-full-recompute harness (atol 1e-12),
  terminal-state-only. Both PROPOSED, never executed.

## Cross-cutting pattern (same as every prior round)
The set is honest about ceilings in its own vocabulary, yet the two ops docs still describe future-state
architecture in present-adjacent voice, and the dead steering seam keeps reappearing. The math/science
docs (orientation, GPU) are the strong pair; the ops docs need re-grounding on the live seam map.

## Recommended actions (in order)
1. Restore orientation doc section 18 (truncated kernel) + the Axis-0 role/formula status line — then it
   is the canonical fresh-thread boot doc.
2. Implement ClaimGateIntakeSupervisor (from thread-2-v1) as the dup-key + NaN gate fix, acceptance =
   hostile corpus flips those 2 GAPs to HOLD, zero drift on the 7 HOLDs. Add a renamed_metric fix
   (edit-distance floor-key guard) to close the third. Codex card, no Claude.
3. Adopt GPU doc as the great-problems program manual under its own tier rules.
4. Send contracts+governance docs back for the 5-blocker repair + status downgrades before any agent
   operates from them.
