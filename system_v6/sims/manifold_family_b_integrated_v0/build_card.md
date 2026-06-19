# BUILD CARD — manifold_family_b_integrated_v0 (the second integrated run: the Hopf-torus object)

You are codex1 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside system_v6/sims/manifold_family_b_integrated_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## What this is
The Family B counterpart of the just-committed manifold_super_sim_v0 (commit 42542f120 — READ its build_card.md, its audit_verdict.md, and system_v6/receipts/program_plan_factory_20260611.md first). The plan receipt requires Family B to be integrated AS ITS OWN OBJECT, never folded into Family A as citations. Same integration mechanism, same anti-cherry-picking core: rebuild everything from pinned sources; parent RESULT rows may be consumed only as pinned-source tables or anchors, never as imported computation.

## LEARN FROM THE v0 AUDIT (avoid re-earning caveats G1-G5):
- hash-lock the CONSUMED result JSONs from the start; audit-verdict hashes under separate citation-context keys (the G1 lesson, already fixed pattern in manifold_super_sim_v0_common.py source_locks/audit_verdict_locks — reuse it)
- preserve every parent caveat label in every reduced/derived row (the G2 lesson)
- the trajectory artifact: single state_object_id + persisted sha-verified per-step rows WITH the unified-run step-dependent vs carried classification (the G3 lesson — do it properly this time, manifold_unified_run_v0 is the mechanism source)
- every layer's decorative detector = an actual input perturbation changing that layer's OWN row signature (the G5 lesson)
- declare the backend mode HONESTLY (the G4 lesson): if JAX/PyTorch share a Python common builder for the full object, say so in the envelope mode/notes rather than claiming full independence; Julia must independently recompute at least the orbit/cardinality counts (Graphs.jl/Z3.jl).

## The shared object (Family B)
The Hopf-torus chart carrier: the deep-chain chart (denominator 16) with its Z4 lens (alpha += pi/2, orbit order 4) and second Z2 (composite order 8), plus the MCT 384-row carrier (2 sheets x 3 eta x 8 phi x 8 chi). Pinned sources: ratchet_deep_chain_v0 + compression_flow_radiated_record_v0 (consume their pinned chart/predicate definitions by hash; REBUILD the orbit tables, exclusion flow, and ledgers yourself).

## The layers (each w/ a perturbation row proving it non-decorative)
B1 RATCHET CHAIN: recompute the seven-step exact chain (conditioning -> Z4 lens -> phase window -> Z2 -> Se restriction -> ...) — volume/denominator/entropy ledger symbolically exact; the ratchet ORDER semantics tested (a permuted constraint order must change the chain where order matters, N01).
B2 COMPRESSION / RADIATED RECORD: rebuild the 384-row three-step exclusion flow w/ exact cardinality conservation (384 = 288 + 96) and the append-only hash-chain record; reconstruction checks per the parent's pattern.
B3 CONSERVATION ACCOUNTS: the Z4 quotient loss/record rows recomputed on THIS object, co-citing z4_syndrome_record_v0's state-plus-record convention (record side CONSTRUCTED — syndrome tables, never record := loss).
B4 TYPED LEDGER: every entropy row typed per manifold_entropy_ledger_v0 (the chart-uniform differential convention + counting rows; the signed-lens-delta label caveat carried: loss_magnitude=+log4 / signed_entropy_change=-log4); the typed consistency matrix across B1-B3.

## WELD ANCHORS (recompute + match exactly; can-fail):
- deep-chain: denominator 16; volume pi^2/4; entropy deltas -ln4, -ln2, -ln2; Z4xZ2 composite order 8
- compression flow: 384 = 288 + 96 cardinality conservation; the hash-chain heads from the parent envelope
- conservation: loss ln4 = record ln4, defect 0.0 (computed both sides)
- every SMT row: negated identity UNSAT + erased/perturbed SAT flip on computed values

## KILL CONTROLS: stale-import (perturb a pinned chart/predicate entry -> dependent anchors mismatch; restore + rerun clean); order-shuffled (N01) on the chain; erased-record (defect ln4 computed); quotient-erased; similarity-only/root-off where partition language appears (THE GUARD).

## Fences: NO Family A rows (the weld of A+B is v2 scope); NO two-engine rows; NO axis/bridge/physics claims; chart-relative discipline on any class language; classification scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false.

## Engineering contract
Three engines (Julia reference w/ package_observables; JAX; PyTorch honest-scope per TOOL_INTENT_MATRIX), envelope ONLY via scripts/build_three_engine_envelope.py, validate --require-pytorch --strict-source-backed --require-tool-intent (or the honest subset w/ the omission stated), packet validator + a small pytest suite incl. regression checks for the v0-audit lessons above, positive+negative+boundary sections. End by listing every validator/test command + status and confirming parent_hash_pins name consumed result JSONs only.

## Round 1 hardening note — 2026-06-12

Scope: four mechanical caveats from `audit_verdict.md` weld-must-add items 3-6 only.

- B1 now derives its live reduced chain rows from a local pin block built from the pinned `ratchet_deep_chain_v0` parent ledger at `/ratchet_sequence/per_step_ledger/rows`; the stale-import control mutates `B1.pinned_ratchet_row_ledger.derived_pin_rows[1].factor` directly and requires dependent anchor mismatch.
- B2 raw record emission now projects parent support/probe rows into B-scoped witness rows before artifact emission; emitted B2 artifacts must contain no `axis0_*` fields.
- B3 record rows now carry the `z4_syndrome_record_v0` co-citation and `finite_counting_state_plus_record` convention label row-locally.
- The trajectory artifact now separates stable content SHA from file-byte SHA and stamps every step row with `trajectory_step_id`, `row_step_lineage_id`, and `row_step_class_why`.

Claim ceiling unchanged: scratch diagnostic only; no formal admission, Family A/B weld, axis, bridge, physics, or independent full-object three-engine claim.
