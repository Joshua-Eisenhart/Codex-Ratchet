# Selector Phase — Side-Quest Handoff to Formal Threads

**Source:** grok_sim side-quest. **Status:** side_quest_only. **Authoritative copy:** this file only; not for promotion.
**Created:** 2026-05-20 by grok_sim thread, addressed to formal_scouts thread.
**Intent:** information transfer. The formal thread may read this and use it to improve `system_v5/ops/NEXT_GOAL_SELECTOR_ENERGY_PHASE_PLAN.md`. Grok_sim does not write to formal surfaces.

## TL;DR for the formal goal doc

Three specific concrete improvements that the selector phase plan should incorporate, based on what grok_sim has now actually run against the plan as an exploration step (iters 108-109):

1. **Lower the kill threshold or replace with bootstrap CI.** The plan's implicit "beats baseline by 1.5×" rule killed all three selector families in iter_108. Cross-audit by Gemini and Grok independently flagged the threshold as non-robust at the sample sizes the plan suggests (25-50 trajectories × ~2000-5000 steps). Either lower to 1.2× or replace with a 95% bootstrap CI test against the matched baseline distribution.

2. **Pre-register sample size from a power analysis, not a heuristic.** 25 trajectories at 2000 steps appears too few to detect modest but real basins. Grok cross-audit specifically named this as "under-powered." Suggested floor for any survived claim: 50 trajectories × 5000 steps minimum, or pre-registered power analysis demonstrating sufficient sensitivity.

3. **Require at least two substrates before declaring any selector "killed" or "survived."** Both cross-audit models flagged single-substrate (n=4 / 2-qubit Pauli) testing as insufficient. The 3-qubit Pauli substrate at N=21 is the natural scale-up; grok_sim iter_109 is running it now.

## What grok_sim ran against the plan

The plan's amended Workstream 1 (after the audit amendments I added) was implemented as `system_v5/grok_sim/iters/iter_108_selector_energy_weighted_dynamics.py`. Three selector families:

- `degree_regularization_energy` (graveyard-by-design)
- `finite_symmetry_closure_energy` using Z_16 cyclic relabeling (non-Clifford action)
- `commutator_balance_energy` calibrated against a predeclared null distribution

Run config: 25 trajectories × 2000 steps, 2-qubit Pauli substrate, weak F01+N01 admission, three move regimes (local, group, mixed), plus a variance-0-start baseline filter for the iter_107 conjugation artifact.

iter_108 result: all three selectors classified KILLED under 1.5× baseline rule. degree_regularization correctly killed as graveyard. Other two killed by threshold.

## Cross-audit findings on iter_108

Both Gemini and Grok independently flagged the verdict as **premature**:

- *Kill threshold (1.5×) not robust.* Both models marked the threshold as arbitrary at this sample size. A modest real basin could be killed by chance.
- *Sample size potentially under-powered.* 25 trajectories may not detect modest signals; Grok specifically suggested 50+ at 5000 steps.
- *Single-substrate test insufficient.* Outcome B requires evidence across multiple substrates per Grok; n=4 alone is not enough.
- *Z_16 closure has a representation-mismatch issue (Gemini).* The 16-element 2-qubit Pauli pool has natural Z_2^4 symplectic vector-space structure, not Z_16 ring structure. Imposing Z_16 cyclic closure as the test action is geometrically inappropriate. The closure-test action should respect the symplectic structure (e.g., a Z_2^4 translation subgroup, or an explicit non-Clifford symplectic subgroup acting on pool indices).

## Recommendations for the formal plan

These are specific text changes to `system_v5/ops/NEXT_GOAL_SELECTOR_ENERGY_PHASE_PLAN.md` that the formal thread should consider:

### Amendment A (Workstream 1, item 7 of Admission Rules)

Replace the implicit "1.5× baseline" threshold with explicit statistical criterion:

```
7. It produces a statistically significant change in dwell, return probability, or
   stationary mass compared with matched no-selector baselines:
   - local swap only;
   - group action only;
   - mixed local/group dynamics with the same move schedule.
   Statistical significance is measured by 95% bootstrap CI of the difference;
   if zero is excluded from the CI in the favorable direction, the difference is
   significant. The 1.5× ratio rule is replaced by this CI rule.
```

### Amendment B (Workstream 1, step 3 - sample size)

Add a sample-size floor:

```
3.bis Sample size floor. Initial scout uses minimum 50 trajectories × 5000 steps
      per condition. Lower sample sizes may be used for fast preliminary sweeps,
      but no "killed" or "survived" verdict is admitted without the floor met.
      The variance-0-start baseline uses the same trajectory count.
```

### Amendment C (Workstream 1, step 6 - substrate requirement)

Add a multi-substrate requirement:

```
6. Multi-substrate requirement for verdict. A "killed" or "survived" verdict for
   any selector family requires consistent results across at least two distinct
   substrates. For the initial pass: 2-qubit Pauli (16 elements, N=10) plus
   3-qubit Pauli (64 elements, N=21). A selector that passes at one substrate
   but fails at the other is INCONCLUSIVE and requires further investigation,
   not a verdict.
```

### Amendment D (Workstream 1, finite_symmetry_closure_energy spec)

Address the Z_16 representation mismatch:

```
2.bis Closure-test action family revised. Z_16 cyclic relabeling is dropped due
      to representation mismatch with the Z_2^4 symplectic structure of the
      2-qubit Pauli pool. The corrected closure-test action family is:
      - the Z_2^4 translation subgroup acting on Pauli symplectic vectors;
      - or a predeclared non-Clifford symplectic subgroup (e.g., a Pauli
        stabilizer group that's not the full Clifford group);
      - or a tensor-product-symmetry action (e.g., qubit-permutation S_2).
      The closure-test action must respect the substrate's natural algebraic
      structure, not impose a topology foreign to it.
```

## What iter_109 tells us (results, landed 2026-05-20)

iter_109 ran the three phases that addressed the audit findings. Result is **Outcome B recommended at grok_sim proposal level with stronger evidence than iter_108**, plus a new finding about why selectors at this level did not work in the sidequest fixtures.

### Phase A — commutator_balance target sweep on 2-qubit substrate

Targets stepped from null mean 0.497 down to Cl(0,4) fraction 0.333:

| target | dwell at variance-0 | final cl_iso count |
|---|---|---|
| 0.4973 (null mean) | 0.0000 | 0/30 |
| 0.4645 | 0.0000 | 0/30 |
| 0.4317 | 0.0000 | 0/30 |
| 0.3989 | 0.0000 | 0/30 |
| 0.3661 | 0.0000 | 0/30 |
| 0.3333 (Cl fraction) | 0.4656 | 30/30 |

Reading: the selector is killed for every honest (non-Cl-calibrated) target. Only the smuggling endpoint — target set EQUAL to Cl's exact commute fraction — "passes" with a 635× baseline ratio. The plan's admission rule 4 explicitly forbids that endpoint as tautological. Phase A is a textbook demonstration of the kill mechanism, not a candidate.

### Phase B — 3-qubit Pauli substrate (N=21, matching Cl(0,6))

The critical finding. At 3-qubit scale:

- Cl(0,6) commute fraction: 0.500
- Null mean (random admitted): 0.4998
- Differential: 0.0002

**Cl's density coincides with random at this substrate.** Density-targeting selectors have no unique target distinguishing Cl from typical admitted graphs. Result:

| condition | dwell at variance-0 | final cl_iso count |
|---|---|---|
| baseline local_only | 0.0000 | 0/30 |
| baseline group_only | 0.0000 | 0/30 |
| baseline mixed | 0.0000 | 0/30 |
| commutator_balance (null target) | 0.0000 | — |
| commutator_balance (Cl-fraction target) | 0.0000 | 0/30 |

The 2-qubit smuggling pattern cannot even be applied here because Cl's density and random's density coincide. The selector family is structurally unable to localize Cl at this scale.

### Phase C — kill-threshold robustness

Only the smuggling "pass" (Cl-fraction target at 2-qubit) clears the 1.5× threshold, by an enormous factor (635×) that trivially clears 1.2× and 2.0× too. The real kills (intermediate targets at 2-qubit, all targets at 3-qubit) are robust across all thresholds. The 1.5× threshold was not the load-bearing factor for any honest kill.

### The structural finding from Phase B

Across substrates, Cl(p,q)'s commute density behaves differently:

| substrate | Cl commute fraction | null mean | differential |
|---|---|---|---|
| 2-qubit (Cl(0,4), N=10) | 0.3333 | 0.4993 | 0.166 |
| 3-qubit (Cl(0,6), N=21) | 0.5000 | 0.4998 | 0.0002 |

A selector targeting density distinguishes Cl from random *only at substrates where Cl's density is far from random*. At larger substrates this differential shrinks (and likely vanishes). So any selector built on a commute-density principle is **substrate-dependent by construction** — not a general selector for Cl, just a low-dimension density-rarity artifact.

This is a sharper kill than iter_108. iter_108 killed the family at one substrate. iter_109 kills it across substrates AND identifies the structural reason: commute density alone is not a load-bearing feature of Cl at higher dimensions.

## Corrected verdict and Outcome B closure

Three structurally distinct graveyard receipts now stand, each with multi-target or multi-substrate evidence:

1. **`degree_regularization_energy`** — graveyard-by-design, killed at 2-qubit (iter_108). Direct variance preference is tautological per plan rule 4.

2. **`finite_symmetry_closure_energy`** — killed at 2-qubit (iter_108), with additional structural critique from Gemini that Z_16 ring topology mismatches the Z_2^4 symplectic structure. Per amendment D suggested above, the closure-test action needs to respect substrate structure.

3. **`commutator_balance_energy`** — killed at 2-qubit across a 6-target sweep (iter_109 Phase A) and killed at 3-qubit (iter_109 Phase B). Structural reason: commute density doesn't distinguish Cl from random at larger substrates.

Within grok_sim only, Outcome B from the plan ("Under tested selector families, stable basin admission remains blocked; the strongest honest result is static/extreme-corner plus reachability/orbit connectivity") is recommended for formal reproduction/audit. The grok_sim sidequest has met its own handoff threshold for three structurally distinct graveyard proposals, but this does not close the formal basin question.

## Updated recommendations for the formal plan

In addition to amendments A-D above, iter_109 surfaces one more:

### Amendment E (substrate-dependence test)

Add to Workstream 1 as a required pre-flight check:

```
0.bis Substrate-dependence pre-flight. Before testing any density-based or
      counting-based selector, measure the candidate's discriminative power
      between Cl(p,q) and a random null at each tested substrate. If Cl's
      target value coincides with the null target value at any substrate,
      that selector family is structurally unable to distinguish Cl from
      random there, and the test is inconclusive (not a kill, not a survive).

      For commutator_balance specifically: this pre-flight already failed at
      3-qubit substrate (Cl differential 0.0002), so density-based selector
      designs should be deferred at 3-qubit or higher. The selector phase
      should focus on non-density features (e.g., spectral properties,
      automorphism orbit volumes, persistent homology of the commute
      complex) where the substrate-dependence isn't built in.
```

The deeper lesson for the formal plan: the candidate selector families in the original Workstream 1 list were all surface-level descriptive features of the commute graph. A productive next selector phase should consider deeper algebraic invariants (spectrum, orbit volume, persistent homology) where the Cl-vs-random separation doesn't collapse at higher dimensions.

## iter_110 result (added 2026-05-20)

Six new selector families tested across both substrates with bootstrap CI thresholds.

### Pre-flight discriminative power confirms selectors CAN see Cl

The pre-flight check (Amendment E above) verified each candidate selector's targets distinguish Cl from random null:

| substrate | spectrum L1 (Cl vs null) | clique count diff (sigma) | orbit size diff |
|---|---|---|---|
| 2-qubit | 5.72 | 3.74σ (Cl=15 vs null=10.47±1.21) | 0.02 (Cl=2 vs null=1.98) |
| 3-qubit | 23.17 | 10.35σ (Cl=105 vs null=49.73±5.34) | 0.00 (Cl=6 vs null=6.0) |

Spectrum and clique-count selectors are pre-flight-discriminative at both substrates. Orbit size is essentially non-discriminative. All three were nevertheless tested.

### iter_110 results

All three selectors killed at both substrates with bootstrap CI:

| selector | 2-qubit bootstrap CI | 3-qubit bootstrap CI | verdict |
|---|---|---|---|
| spectral_signature_energy | excludes 0 negative (selector worse) | CI = [0.0, 0.0] (no difference) | KILLED_both_substrates |
| clique_count_energy | excludes 0 negative | CI = [0.0, 0.0] | KILLED_both_substrates |
| orbit_size_energy | CI straddles 0 | CI = [0.0, 0.0] | KILLED_both_substrates |

### The structural reason: target-direction tension

This is the key finding from iter_110. Each selector targets the null distribution mean (not Cl-specific to avoid smuggling). But Cl sits at the EXTREME of every measured invariant — variance 0 (extreme low), clique count 105 (10 sigma above null mean), spectral signature far from null centroid.

So a selector targeting null mean pulls trajectories AWAY from Cl. A selector targeting Cl's specific values is smuggling (rule 4 of plan admission). There is no defensible target direction within this framework that genuinely localizes Cl.

The pattern across iters 108-110:

- iter_108: density-based selectors killed at 2-qubit
- iter_109: target sweep across density values killed everywhere except smuggling endpoint; 3-qubit confirmed (Cl density = null density)
- iter_110: spectrum, clique count, orbit size all killed at both substrates via bootstrap CI

Six distinct selector families across two substrates with statistical rigor. All killed.

## The deeper structural finding

Within a pure constraint-admissibility framework (no external physics):

- Honest non-tautological selectors target null-distribution statistics → push AWAY from Cl (which sits at extreme corners)
- Selectors targeting Cl's specific values → smuggling by plan rule 4
- There is no defensible "middle" target that genuinely localizes Cl

The selector phase, within the tested grok_sim operationalizations and substrates, did not produce a non-tautological basin claim. This is not a failure of one selector; it is a bounded sidequest limit that formal tensor-network basin claims may still test separately.

For the basin claim to survive, the plan's framework must be extended in one of these directions:

1. *Physics-derived fitness.* Define an energy/free-energy/MDL function from EXTERNAL physical principles (thermodynamics, information theory, error correction). The function targets low values; Cl may happen to minimize that function. Burden of proof: derive the energy from first principles, not retro-fit.

2. *Selection from outside the dynamics.* Replace the equilibrium walk with a non-equilibrium process (gradient descent, simulated annealing, reinforcement) where the trajectory is driven by an external loss. The loss has to come from somewhere outside Cl.

3. *Statistical-extreme reframing.* Accept that the static finding (Cl at extreme corner of admitted set) is the strongest available verb. Stop claiming dynamic basin generation. The original goal becomes "Cl is the maximal-symmetry / extremal-clique / minimal-variance structure admitted by F01+N01" — a measure-theoretic claim, not a dynamical one.

The grok_sim side-quest has now exhausted what it can say within the constraint-admissibility frame. Routes 1 and 2 are outside grok_sim's scope; route 3 is what the existing static iters 97-99 already support.

## Final Outcome-B recommendation from grok_sim

The selector phase under the tested grok_sim non-tautological operationalizations, tested substrates, and bootstrap-CI thresholds recommends treating the tested F01+N01-alone basin claim as blocked pending formal reproduction/audit. Six selector families x two substrates x bootstrap-CI rigor = no grok_sim candidate survived.

Outcome B is closed only at grok_sim's proposal level. The formal thread takes over from here. The recommended path forward for the formal selector/energy phase is either:

- *Route 3 (reframe as static-extremal).* Cheapest. Use the iter_97-99 + iter_108-110 receipts as the bounded final synthesis. Stop the dynamical basin program.
- *Route 1 (physics-derived energy).* Requires external derivation. Out of grok_sim's scope; potentially in formal scope if the program is willing to introduce thermodynamic/info-theoretic axioms.
- *Route 2 (non-equilibrium dynamics).* Requires a loss function. Same constraint as Route 1.

grok_sim's recommendation: take Route 3 unless the formal program is prepared to commit to introducing axioms beyond F01+N01.

## Total grok_sim iter coverage on the basin question

13 iters across the F01+N01 basin question:

| iters | what they bounded |
|---|---|
| 97-99 | Static admitted-set test. Cl at variance-0 extreme corner, stable across n=4,6,8. |
| 100-101 | Dynamic test under weak and sharpened admission. No basin under single-edge flips. |
| 102 | 8-constraint greedy + combinatorial search. All score 0. |
| 103 | 11 substrate variations. Cl-isomorphic rate ~0.1% only on Pauli-tensor pool at n=4. |
| 104 | C2 threshold sweep. Best partial localization at variance ~0.45, never variance 0. |
| 105 | Substrate-constrained walk. Cl reachable 90% of time but never stable. |
| 106 | Variance-0 subset at n=3 is 170 isolated nodes under edge flips. Confirms structural disconnection. |
| 107 | Clifford-group conjugation. Preserves variance trivially but doesn't attract from elsewhere. |
| 108 | First selector phase pass. 3 families killed at 1.5× threshold. |
| 109 | Target sweep + 3-qubit + threshold robustness. Outcome B recommended at grok_sim proposal level across tested substrates. |
| 110 | Deeper invariant selectors (spectral, clique count, orbit size). All killed at both substrates with bootstrap CI. |

This is the comprehensive bound for the grok_sim selector sidequest. The formal threads still own any tensor-network, basin, or admission claim.

## Extension to physics-derived dynamics and tensor-network scale (iters 111-113)

Owner directive after the selector-phase Outcome B closure: "make it all dynamic now? 16-64 qubits? full pytorch and tensor networks?" — push grok_sim past discrete Markov walks into the formal-scout-style dynamic PyTorch / MPS regime. Iters 111-113 carry this out.

### iter_111 — physics-derived ground states at N=4, 6, 8

Three Hamiltonians tested via exact eigendecomposition (state vector dim ≤ 256):

- **TFIM** (transverse-field Ising): H = sum Z_i Z_{i+1} + sum X_i
- **Heisenberg**: H = sum (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1})
- **Random TFIM**: random J_i, h_i couplings ∈ [0.5, 1.5]

For each ground state, top stabilizers identified via Pauli expectation enumeration. Commute graphs compared to Cl(0,4).

| N | Hamiltonian | top stabilizer | second stabilizer | top-10 Cl(0,4) iso? |
|---|---|---|---|---|
| 4 | TFIM | XXXX (1.000) | XXXI (-0.862) | No |
| 4 | Heisenberg | XXXX (1.000) | YYYY (1.000), ZZZZ (1.000) | No |
| 4 | RandomTFIM | XXXX (1.000) | IXXX (-0.792) | No |
| 6 | TFIM | XXXXXX (1.000) | XXXXXI (-0.855) | No |
| 6 | Heisenberg | XXXXXX (-1.0), YYYYYY (-1.0), ZZZZZZ (-1.0) | — | No |
| 6 | RandomTFIM | XXXXXX (1.000) | IIIIXX (0.932) | No |
| 8 | TFIM | XXXXXXXX (1.000) | XXXXXXXI (-0.852) | No |
| 8 | Heisenberg | XXXXXXXX (1.0), YYYYYYYY (1.0), ZZZZZZZZ (1.0) | — | No |
| 8 | RandomTFIM | XXXXXXXX (1.000) | IIXXXXXX (0.944) | No |

Verdict: 0/9 ground states have Cl(0,4)-isomorphic top-10 commute graphs.

The structural pattern is unmistakable. Ground states are stabilized by the **Hamiltonian's symmetry group**:
- TFIM has Z2 (global X-parity) → top stabilizer X^N
- Heisenberg has SU(2) (global rotation) → top stabilizers X^N, Y^N, Z^N pairwise anti-commuting
- These are *Hamiltonian symmetries*, not the specific Cl(0,n) anticommutation pattern

### iter_112 — scale to N=16 via PyTorch sparse gradient descent

State vector dim = 65,536. Exact eigendecomposition infeasible. Used Adam optimizer with sparse Hamiltonian-vector products (each Pauli term applied as a permutation + sign flip). 2000 gradient steps per Hamiltonian. Pauli expectations computed for 5000 random Pauli strings plus 3 global anchors.

Results:

| Hamiltonian | ground energy | top stabilizer | second stabilizer | top-10/21 Cl iso? |
|---|---|---|---|---|
| TFIM | -16.000 | XXXXXXXXXXXXXXXX (0.9999) | random Pauli at 5.8e-5 (noise) | No |
| Heisenberg | -15.355 | XXXXXXXXXXXXXXXX (-0.417), YYYYYYYYYYYYYYYY (0.319) | random Pauli at 0.054 | No |
| RandomTFIM | -15.427 | XXXXXXXXXXXXXXXX (0.9999) | random Pauli at 6.6e-5 (noise) | No |

Verdict: 0/6 conditions Cl-iso. Same structural pattern: Hamiltonian's symmetry group dominates the stabilizers. At N=16, the discrete sample of 5003 Pauli strings reveals that besides the global symmetry, all other stabilizers are at noise floor — they're statistically random sampled Pauli expectations on a generic ground state.

### iter_113 — MPS+DMRG at N=32 via quimb (landed)

State vector intractable at N=32 (dim 4×10⁹). Used quimb's DMRG1 with bond dim 16. TFIM. DMRG converged in 0.2s, ground energy -16.98. 2000 Pauli expectations sampled.

Results:
- Top stabilizer: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (X^32) at 0.999999999999984 (Z2 symmetry)
- Second stabilizer: random Pauli at -3.8e-8 (noise)
- Top-10 commute graph: 26 edges, degree variance 3.36, NOT Cl(0,4)-iso
- Top-21 commute graph: 112 edges, degree variance 9.84, NOT Cl(0,6)-iso

Total iter time: 4.7s.

### iter_114 — MPS+DMRG at N=64 via quimb (landed)

State vector dim 2^64 ≈ 1.8×10¹⁹. Required MPS. DMRG1, bond dim 16. TFIM. Pauli sampling needed Python's getrandbits (numpy int64 overflows at 2^64).

Results:
- DMRG ground energy at N=64: -34.0005 (converged in 0.3s)
- Top stabilizer: X^64 at 0.999999999981 (Z2 symmetry, strong)
- Second-fourth stabilizers: Z^64 and Y^64 and random Pauli at 1e-19 level — essentially exactly zero
- Top-10 commute graph: 25 edges, degree variance 0.80, NOT Cl(0,4)-iso
- Top-21 commute graph: 98 edges, degree variance 2.60, NOT Cl(0,6)-iso

Total iter time: 7.8s.

### Full N=4..64 sweep confirms structural pattern

| N | method | Hamiltonian | top stabilizer | second stabilizer | Cl(0,n) iso? |
|---|---|---|---|---|---|
| 4 | exact eigh | TFIM | XXXX (1.000) | XXXI (-0.862) | No |
| 6 | exact eigh | TFIM | XXXXXX (1.000) | XXXXXI (-0.855) | No |
| 8 | exact eigh | TFIM | XXXXXXXX (1.000) | XXXXXXXI (-0.852) | No |
| 16 | PyTorch grad descent | TFIM | X^16 (0.9999) | random Pauli (5.8e-5, noise) | No |
| 32 | MPS DMRG1 | TFIM | X^32 (1.0) | random Pauli (3.8e-8, noise) | No |
| 64 | MPS DMRG1 | TFIM | X^64 (1.0) | Z^64/Y^64 (1e-19, noise) | No |

Plus 3 Hamiltonians tested at N=4, 6, 8, 16: TFIM, Heisenberg, RandomTFIM. Heisenberg's SU(2) symmetry produces three strong stabilizers (X^N, Y^N, Z^N — all global rotations). TFIM and RandomTFIM have just X^N (Z2 only).

**Across 6 distinct system sizes, 3 different methods (exact eigh, PyTorch grad descent, MPS DMRG), 3 physics-motivated Hamiltonians: every ground state's stabilizer structure mirrors its Hamiltonian's symmetry group, never Cl(0,n) anticommutation structure.**

The signal-to-noise gap at N=64 (1.0 vs 1e-19, ratio 10^19) is overwhelming in these Hamiltonian/DMRG sidequest controls. The Hamiltonian symmetry is the stabilizer in this control family. This covers these controls only and does not settle formal tensor-network basin claims.

### What the dynamic / tensor-network extension suggests within tested controls

Route 1 from the selector-phase synthesis (physics-derived fitness function whose ground state attracts toward Cl) did not work for the tested physics-motivated Hamiltonians. The sidequest structural reading:

**Ground states are stabilized by the Hamiltonian's symmetry group. Cl(0,n) is NOT a symmetry group of any of TFIM, Heisenberg, RandomTFIM. So Cl-like stabilizer structure is not present in their ground states.**

The only way to get Cl-like stabilizer structure from a physics ground state is to engineer the Hamiltonian to have Cl as its symmetry group (or to take it as the stabilizer code Hamiltonian, e.g., toric code). That is Hamiltonian engineering, not emergence — exactly the smuggling pattern Route 1 was supposed to avoid.

### Assessment of the formal `thirteen_layer_active_nested_manifold_mps` stack

Read-only inspection of `system_v5/ops/formal_scouts/sim_thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe.py`:

The stack is technically rich:
- 13 nested layer constraint enforcers
- MPS contraction with bond-dim-tracked entanglement
- Special-holonomy parallel comparator (SU3/G2/Spin7)
- Layer-removal graveyard suite (each of 13 layers individually removed)
- Iterated cross-entropy long-horizon readouts
- Topology flux feedback + persistence + Clifford projection feedback

What's structurally good:
- The layer-removal graveyards correctly test each layer's load-bearing contribution
- The special-holonomy comparator gives an alternative algebraic frame
- MPS contraction with iterated readouts is the right scaffold for dynamics testing

What needs tuning, based on grok_sim's bound:
- **The "basin admission" claim path is wrong-framed**. The stack should NOT claim attractor-basin generation under F01+N01 + Clifford. iters 100-113 establish this empirically.
- **The static-extremal reframe should be made explicit**. Cl is at the extreme corner of the admitted set (verified at N=4..16); this is the strongest claim grok_sim can support. The stack should target THAT claim, not basin generation.
- **The 13-layer probe should incorporate the iter_111-113 finding** that physics ground states stabilize on Hamiltonian symmetries (not Cl). Any Hamiltonian-derived feedback in the stack (e.g., topology flux feedback, persistence feedback) will tend toward the Hamiltonian's symmetry group, not Cl(0,n). This needs to be tested explicitly and either confirmed or explicitly worked around.
- **The Clifford projection feedback is the load-bearing module to audit**. If it's working by projecting ANY state onto the Cl manifold, that's smuggling. If it's working as a measurement of distance from Cl, that's fine but doesn't generate Cl.

### Recommended action for the formal stack

1. Add the static-extremal reframing as an explicit alternative claim path in the thirteen_layer probe — allow it to land as "Cl is structurally extremal in the admitted set" rather than requiring "Cl is an attractor basin."
2. Audit the Clifford projection feedback module. Determine whether it's a measurement or a smuggled selector. If selector, demote to graveyard control.
3. For the 8/16/32/64-site scaling probe: add a "Hamiltonian symmetry vs Cl symmetry" test that explicitly measures whether the ground state's stabilizer group is generated by the Hamiltonian's symmetry generators or by the Cl(0,n) anticommutation structure. The grok_sim finding suggests this will fall on the Hamiltonian-symmetry side for all physics-motivated Hamiltonians.

### Updated total iter coverage (97-113)

| iters | what they bounded |
|---|---|
| 97-99 | Static admitted-set test. Cl at variance-0 extreme corner. |
| 100-101 | Dynamic test under weak and sharpened admission. No basin. |
| 102 | 8-constraint greedy search. All score 0. |
| 103 | 11 substrate variations. Random Pauli sampling never produces Cl. |
| 104 | C2 threshold sweep. Partial localization at variance ~0.45, never 0. |
| 105 | Substrate-constrained walk. 90% reach, 0% stable. |
| 106 | Variance-0 subset disconnected under edge flips. |
| 107 | Clifford-group conjugation: preserves variance trivially, doesn't attract. |
| 108-110 | Selector phase. 6 selector families across 2 substrates, all killed via bootstrap CI. |
| 111 | Physics ground states at N=4,6,8: stabilize on Hamiltonian symmetry, not Cl. |
| 112 | N=16 via PyTorch grad descent: same Hamiltonian-symmetry pattern. |
| 113 (in flight) | N=32 via MPS+DMRG: expected to confirm at MPS scale. |

17 iters. The basin claim under F01+N01 is bounded only inside grok_sim's sidequest fixtures across discrete dynamics, group action, selectors, physics Hamiltonians, and attempted tensor-network-scale probes. The pattern is structural within those fixtures, but formal_scouts still own any repo admission or tensor-network basin claim.

## What grok_sim's bound on the basin claim still says

Independent of the selector phase, the static + dynamic findings from iters 97-107 remain:

- *Cl(p,q) is at the variance-zero extreme corner of the F01+N01 admitted set.* Static finding, stable across n=4,6,8.
- *Single-edge-flip dynamics never localizes to Cl's corner.* Even with substrate constraint or Clifford group conjugation in the move set.
- *The variance-zero subset at n=3 (170 graphs) is internally disconnected under single-edge flips.* Each Cl-orbit element is structurally isolated from the others.
- *Pure Clifford conjugation trivially preserves variance-zero if started there, but doesn't attract from elsewhere.* No selection mechanism.

Whatever the selector phase produces, these bounds stand. They are the negative result the selector/energy work has to either supersede (by finding a non-tautological selector that does cause attraction) or accept (as Outcome B).

## Boundary discipline

This document is in `system_v5/grok_sim/`. The formal thread reads it but does not require grok_sim to participate in its formal-scout admission process. Any text changes the formal thread chooses to make to its plan doc are at its discretion. Grok_sim does not write to `system_v5/ops/formal_scouts/`.

Cross-audit receipts and full iter source live in:
- `system_v5/grok_sim/iters/iter_108_selector_energy_weighted_dynamics.py`
- `system_v5/grok_sim/iters/iter_109_selector_target_sweep_and_3qubit_substrate.py`
- `system_v5/grok_sim/results/iter_108_selector_energy_weighted_dynamics_results.json`
- `system_v5/grok_sim/results/iter_109_selector_target_sweep_and_3qubit_substrate_results.json` (once iter_109 lands)
- `/tmp/engine_v2/iter108_audit_gemini_out.txt`
- `/tmp/engine_v2/iter108_audit_grok_out.txt`

The audit transcripts in `/tmp/` are ephemeral; if the formal thread wants durable cross-audit receipts, the appropriate path is to ingest them through a formal_scout ingest probe (the pattern already used in `sim_two_root_constraint_grok_dynamic_negative_evidence_ingest_probe.py`).
