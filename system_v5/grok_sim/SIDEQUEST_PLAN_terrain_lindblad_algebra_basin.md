# Side-Quest Plan: Terrain Lindblad Composition Algebra Basin (grok_sim)

**Created:** 2026-05-20
**Scope:** grok_sim side-quest only. `claim_ceiling: side_quest_only` on every output.
**Boundary:** READ-ONLY access to `system_v5/ops/formal_scouts/canonical_qit_engine_specs.py` for reference; no writes to formal_scouts/, no formal_scout admission, no canonization. The formal W3 scout (`sim_constraint_manifold_terrain_lindblad_composition_bridge_probe.py`) is locked behind W1 tooling repair per `NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md`. This side-quest does NOT replace, unblock, or substitute for that scout.

## Why this exists

After the master-doc audit, the right read is:
- F01+N01 alone are too weak to force a unique algebra (Grok+Gemini convergence)
- The owner's master atlas records a candidate selection mechanism: 8 terrain (Lindblad, Hamiltonian) pairs + nested substage→stage→loop→engine→schedule composition
- iter_113/114 used ground-state-of-Hamiltonian as observable, which is state-level not algebra-level — wrong test
- The right test is: under the recorded terrain Lindblad system, what algebra of observables / fixed states / generated channels is selected?

This side-quest provides bounded grok_sim evidence on that question, without taking authority away from the formal W3.

## Method

1. **Reconstruct (L, H) pairs inline.** Read canonical_qit_engine_specs.py as text reference; reproduce inline so no formal_scouts import. Per-perception L matrices: Se=σ_z, Ne=σ_+, Ni=-iσ_y, Si=σ_-. Type-2 mirrors Type-1 by L_R = σ_x L σ_x. Hamiltonians: H_0 = 0.77σ_z + 0.13σ_x, H_3 = 0.61σ_y + 0.21σ_x, H_S = 0.83σ_z, with Type-2 sign-flipped.

2. **Proper Lindblad CPTP via Liouvillian exponential.** `dρ/dt = -i[H,ρ] + LρL† - ½{L†L, ρ}`. Build the Liouvillian super-operator on vec(ρ) ∈ ℂ^4. Time evolution: `Φ_T(t) = expm(L_super · t)`. NOT Euler updates. Verify trace preservation and complete positivity (Choi matrix ≥ 0).

3. **Nested composition.**
   - Substage Φ_T: one terrain Lindblad step (fixed dt)
   - Stage: 4 substages composed = Φ_stage = Φ_T4 ∘ Φ_T3 ∘ Φ_T2 ∘ Φ_T1
   - Loop: 4 stages composed = Φ_loop = Φ_stage,4 ∘ ... ∘ Φ_stage,1
   - Engine: 2 loops (inner + outer) = Φ_engine = Φ_outer ∘ Φ_inner
   - Schedule: N engines composed = Φ_schedule = Φ_engine,N ∘ ... ∘ Φ_engine,1
   - Use the canonical Type-1 / Type-2 schedules: [(Se,outer), (Ne,outer), (Ni,outer), (Si,outer), (Se,inner), (Si,inner), (Ni,inner), (Ne,inner)]

4. **Algebra-level tests at each composition level.**
   - Fixed state ρ*: solve Φ(ρ*) = ρ* via eigenvector with eigenvalue 1
   - Fixed observable algebra: dual super-operator Φ†; find observables O with Φ†(O) = O
   - Generated channel algebra: rank of the span of {Φ_T : T ∈ terrains} in the 16-dim super-operator space
   - Spectral structure of each Φ: eigenvalues, gap to 1, decay rates

5. **Comparison against candidate algebras** (the three live readings).
   - **Cl(3,0)** anticommutation: σ_iσ_j + σ_jσ_i = 2δ_ij. Test whether the fixed-observable basis satisfies this.
   - **Heisenberg-Weyl**: clock-shift commutation [X, Z] = (something nontrivial). Test against discrete Weyl group structure.
   - **SU(2)/Pauli group**: [σ_i, σ_j] = 2iε_ijk σ_k. Test against su(2) Lie algebra closure.
   - **Quantum semigroup**: arbitrary CPTP composition algebra. Test whether the generated set is the full CPTP cone or a proper sub-semigroup.

6. **Anti-smuggling controls.**
   - **Static identity**: terrains replaced by Φ_T = identity. Tests whether composition alone selects structure.
   - **Commutative collapse**: only Se (σ_z) terrains. Tests whether noncommutation between L choices is load-bearing.
   - **Random Pauli L**: replace canonical L with random 2×2 unitaries. Tests whether the specific (L, H) choices matter.
   - **Order-erased**: random permutation of schedule. Tests whether ordering matters.

7. **Verdict per reading** (preserve plural; don't collapse).
   - Cl-class: dim of fixed-observable algebra = 4 (Pauli basis) AND anticommutation holds
   - Heisenberg-Weyl: dim ≤ 4 AND clock-shift relations
   - SU(2)-class: dim ≤ 4 AND Lie bracket closure
   - Quantum semigroup: dim of generated channel algebra > 4 (CPTP-class)
   - Plural: multiple readings consistent
   - Killed: fixed-observable algebra trivial or no nontrivial fixed state

## Hard holds

- `claim_ceiling: side_quest_only` on every output JSON
- no canonization claim
- no replacement of formal W3
- no contradiction of master atlas (Ξ, ρ_AB, Φ_0 stay open)
- result feeds formal W2 ingest as side-quest evidence ONLY when W2 unlocks
- if the result kills the candidate selection mechanism for ALL three readings, report as exclusion evidence; if multiple readings remain, hold as plural

## Iter sequence

- **iter_115**: terrain Lindblad composition + algebra basin (this plan)
- **iter_116 (conditional)**: alternative-dynamics side-quests (Heisenberg-Weyl, U_q(sl_2), fuzzy sphere) for comparison
- **iter_117 (conditional)**: schedule-order and terrain-law ablations

Stop at iter_115 and report. Subsequent iters spawn only if iter_115 surfaces a specific open question worth bounded follow-up.

## What this is NOT

- NOT a formal_scout
- NOT a canonization receipt
- NOT a substitute for W3
- NOT proof that Cl(p,q) is the basin
- NOT proof that the recorded selection mechanism succeeds
- NOT proof that grok_sim's Cl-basin chain (iter 97-114) was right or wrong about the deeper question
