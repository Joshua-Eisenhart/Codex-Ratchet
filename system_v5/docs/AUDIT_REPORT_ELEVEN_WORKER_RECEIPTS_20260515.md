# AUDIT REPORT — 11 Worker Receipts (2026-05-15)

Audit layer: opus-fresh-context (code-reviewer agent), no author-thread bias.
Receipt set: 11 worker outputs collected in one dispatch window during operational engine landing.
Result-classification: 3 CLEAN, 4 NOTE, 2 FINDING-P3, 2 FINDING-P2, 0 FINDING-P1.

Closure judgment: receipts inform next wave with patches. Two receipts (#6 trainable, #9 late-stage Popper) had source-spec drift; one (#7 bipartite) needed initial-state caveat surfaced into result JSON; one (#10 Track A) needed α-sweep validation. None killed the receipt set. All four findings patched in this session (see PATCH RESOLUTION below).

## Per-receipt findings

### Receipt 1 — `sim_paired_chiral_operational_lindblad_composer_with_terrain_readout_integration_probe.py` (`a90a8b11d156fde53`)
**NOTE.** 21/21 passes against six required source-alignment categories. Tool manifest non-empty reason fields all match invocations. z3 UNSAT witness on stage count survives. Minor: graveyard predicate `"scrambled_topology_assignment_breaks_state_evolution"` reports `patterns_differ: false` (canonical=`WINwin`, scrambled=`WINwin`) but the predicate still passes via `frobenius_diff: 0.32` — the graveyard is named "breaks state evolution" but the readout *pattern* did not differ, only the underlying density. Receipt should rename or document this in result JSON.

### Receipt 2 — `sim_fe_asymmetry_pauli_generator_algebra_z3_derivation_probe.py` (`a7fe7d919001e2518`)
**CLEAN.** z3 SAT/UNSAT verdicts are non-cosmetic. Canonical assignment SAT, `all_same_generator AND exactly_one_sigma_y` UNSAT, swapped-Fe-to-σ_z UNSAT. Sympy commutator cross-check confirms σ_y has unique negative coupling class. Zhuangzi-closed verdict is earned by algebra, not by spec table.

### Receipt 3 — `sim_fresh_cycle_hysteresis_independence_falsifier_probe.py` (`a9bb82ec127a1e3d9`)
**NOTE.** Verdict `ATTRACTOR_CONVERGENCE` honestly contradicts the prior hysteresis claim (`mean_additivity_ratio_k20=0.1035 < 0.5`). Good faith Popper work. Minor concern: `per_seed_cumulative_slopes` and `per_seed_fresh_slopes` are *identical to floating-point precision* — for a deterministic CPTP channel they must be; the z3 confound check is structurally a tautology in this case.

### Receipt 4 — 3-inactive-layers refactor (`ac2469ee77667b417`)
**CLEAN (file-existence).** `claude_integrated_manifold_modules/active_layer_constraint_enforcers.py` exists at 39379 bytes; v3 sim runs 35/35.

### Receipt 5 — `CROSS_THREAD_AUDIT_CODEX_VS_CLAUDE_SIM_ESTATE_20260515.md` (`aaa2b0b6b37b8df8a`)
**CLEAN (file-existence).** 31769 bytes. Doc content not deep-audited per scope.

### Receipt 6 — `sim_qit_engines_perform_classification_task_with_trainable_readout_probe.py` (`a1031e4fe5a238f63`)
**FINDING-P2 — source-spec drift.** Sim defines local `TYPE_ONE_TOPOLOGIES` at line 126 using field names `major/minor` while canonical spec uses `outer/inner`. Schema divergence means canonical-module updates will not propagate. 96.05% accuracy is real but cite as "topology-canonical-equivalent at audit time" not "canonical-sourced." **PATCHED 2026-05-15:** sim now imports from `canonical_qit_engine_specs`; numerics identical to full float precision.

### Receipt 7 — `sim_paired_engine_bipartite_logarithmic_negativity_coupling_probe.py` (`a48f0b281ae92a4cb`)
**FINDING-P3 — caveat in code, not in JSON.** Initial state `|+⟩⟨+|⊗|+⟩⟨+|` documented in function docstring (line 436) but result JSON does not surface this in `claim_ceiling`. Downstream readers see peak E_N=0.41 without rationale. **PATCHED 2026-05-15:** `claim_ceiling` upgraded to dict with `initial_state_choice`, `out_of_scope`, `surviving_alternatives_summary`; canonical caveat now appears in JSON.

### Receipt 8 — `sim_non_abelian_schedule_order_commutator_probe.py` (`a7369443b1398fe65`)
**NOTE.** Source-spec compliant (imports canonical specs). 92.6% non-commuting fraction is genuine (vs identity baseline 1.7e-15). z3 UNSAT on anti-commuting -> C=I holds inside the encoded fixture. One Zhuangzi-open admitted honestly: pure outer-only and inner-only commutators are O(1e-16); only interleaved schedules expose non-commutativity. Documented, not hidden.

### Receipt 9 — `sim_engine_late_stage_feature_only_classification_falsifier_probe.py` (`aa1f08c75ff22740a`)
**FINDING-P2 — source-spec drift + uncomfortable verdict.** Same drift as receipt 6: local `TYPE_ONE_TOPOLOGIES` at line 137. Verdict `front_loaded` is honest — early-only (0.96) matches full (0.96), late-only collapses to 0.64. Cross-receipt note: this falsifies receipt 6's "engines preserve information for classification" reading. **PATCHED 2026-05-15:** sim now imports from canonical specs; verdict and numerics unchanged.

### Receipt 10 — Track A MPS fix (`a7bd468d431557872`)
**FINDING-P3 — α=0.31 origin weakly grounded.** Patch claim "mirrors Track B's YY weight" is grounded (Track B uses 0.31 as YY base coefficient), but sign-flip changes operational eigenstructure. α=0.31 is "designed-to-pass parameter, not derived." **PATCHED 2026-05-15:** v3 sim now runs α-sweep predicate over {0.05, 0.15, 0.31, 0.50, 0.75}; signed information curve monotone increasing (0.305 → 0.536), all > noise floor 0.05, sign consistent. α=0.31 now sits on a validated curve.

### Receipt 11 — `sim_engine_trajectory_persistent_homology_readout_feature_probe.py` (`a187b3d09e7ba5960`)
**CLEAN with caveat.** Predicate `persistence_ge_raw_no_harm` defined as `>=`, not strict `>`. Persistence 0.81 vs raw 0.80 passes the predicate honestly. Result publishes `headline.delta_persistence_minus_raw: 0.01` for the reader to judge. The 0.01 advantage is one fold of variance away from zero (std ~0.04). Receipt does not over-claim; promoting persistence as primary readout is NOT supported by the data.

## Cross-receipt findings

**Cross-receipt collapse risk — receipt 9 falsifies receipt 6's headline.** Receipt 6 reports 96.05% engine accuracy and concludes engines preserve input geometry. Receipt 9 then runs the Popper falsifier and finds 64% late-only with `verdict: front_loaded`. Together they are coherent (receipt 9 explicitly addresses receipt 6's Popper open) but citing receipt 6 in isolation would be unearned agreement. Treat the pair as one Popper-closed package.

**Cross-receipt assumption check — J=0 in receipt 7 vs paired-engine independence in receipt 1.** Receipt 7 at J=0 reports peak E_N=0 (no coupling). Receipt 1 reports paired-engine independence with `max_divergence: 1.10` evolving paired engines under independent runs. Both consistent.

**Source-spec drift pattern — only sims #6 and #9 redefined topology dicts locally.** Sims #1, #3, #8, #11 import from `canonical_qit_engine_specs`. Sims #6 and #9 did not. Latent bug, not present incorrect claim. Patched.

## Patch resolution summary (2026-05-15)

| Finding | Receipt | Status | Patch artifact |
|---|---|---|---|
| FINDING-P2 source drift | #6 trainable | RESOLVED | sim now imports canonical specs; bit-identical numerics |
| FINDING-P2 source drift | #9 late-stage | RESOLVED | sim now imports canonical specs; verdict unchanged |
| FINDING-P3 initial-state caveat | #7 bipartite | RESOLVED | result JSON `claim_ceiling` extended with `initial_state_choice` |
| FINDING-P3 α=0.31 origin | #10 Track A | RESOLVED | α-sweep predicate added; 5-point curve confirms stability |
| NOTE graveyard pattern claim | #1 integration | OPEN | result JSON predicate name not yet adjusted |
| NOTE z3 tautology | #3 hysteresis | OPEN | structural; the channel IS deterministic |

## Closure judgment after patching

Receipts inform the next dispatch wave without caveats. Two notes remain open as structural observations, not as findings that would block downstream work. The receipt set's overall posture is `passes local rerun`; none are `canonical by process`.

Audit-chain fixed-point status: this is round 1. A round-2 audit on the post-patch state would close the fixed point if it returns zero findings. That has not yet been run.
