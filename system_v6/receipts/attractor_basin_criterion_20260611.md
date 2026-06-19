# Attractor-Basin Criterion - 2026-06-11

Status: owner-doctrine criterion plus pilot registration.
Ceiling: design receipt / build card support, not an admitted basin theorem.
Pollution rule: cite committed corpus distillates and result surfaces only.

## Source Lock

This receipt turns the owner doctrine into a computable criterion:

- Constraints should form an attractor basin.
- The QIT engine runs in an attractor and is itself an attractor-like object.
- The eight engine stages are degrees of freedom on that object.
- After ratcheting to saturation, decompose the saturated object into sub-basins and subsub-basins. "Not fully independent" means an attractor lattice / Morse decomposition with connecting-orbit witnesses, not prose independence.

Committed surfaces used:

- `geo_s5_terrain_flows_v0` at current packet commit `6aa75cc96`: exact affine S5 terrain generators, fixed points, basin limits, and nonlimit orbit receipts. Result: `system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_jax_results.json`.
- `ratchet_s6_terrain_sweep_v0` at commit `826e716d1`: conditioned `T_pi/6` terrain sweep, zero fixed-point survivors, no pure-shell compatible terrain, exact order-gap rows. Result: `system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json`.
- `ratchet_deep_chain_v0` at commit `7909b1b1b`: scoped saturation for the available committed constraint set, final denominator 16, per-step entropy ledger, and mortality exhibit. Result: `system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json`.
- `manifold_entropy_ledger_v0` at commit `a54224476`: exact entropy rows, chain-rule check, lens quotient sign caveat, terrain restriction delta.
- `old_estate_mine_20260611.md` at commit `77fb7ca52`: old basin/formal-scout estate consumed as mine material only; basin rows are finite witness/control material, not current admission.
- `engine_stage_word_cost_discriminator_v0` at commit `123b8e7d8`: bounded-chi loop-local 8-stage word evidence at computed sizes; cost discriminator only.

## 1. Criterion

For a ratcheted admissible object `A` under engine dynamics `F`, call `A` an attractor-basin object only if all four rows below are receipt-backed.

### 1.1 Invariance

Criterion: `F(A) subset A`, or for continuous time, the vector field is tangent/inward on the boundary of `A`.

Computable route:

- For committed affine terrain flows `r' = M r + b`, compute exactly from the exported symbolic `M,b`.
- For a finite object, compute image containment directly on representatives.
- For a shell or manifold chart, compute the normal component and tangent defect.

S5 terrain-flow status:

- `Se_Funnel_L`, `Se_Cannon_R`, `Ni_Pit_L`, and `Ni_Source_R` preserve the Bloch ball and have fixed-point basin rows under the committed affine flow.
- `Ne_Vortex_L` and `Ne_Spiral_R` preserve norm but are rotations with non-attracting orbit classes.
- `Si_Hill_L` and `Si_Citadel_R` have attracting slices, not a unique whole-ball fixed point.
- The conditioned `T_pi/6` shell is not invariant for the worked rows below; the sweep classifies this as shell-breaking, not as a hidden attractor.

### 1.2 Attraction

Criterion: there is a computed neighborhood `U` of `A` such that orbits from `U` enter or converge to `A`.

Computable route:

- For affine maps/flows, use fixed-point solve plus eigenstructure of `M`.
- If all eigenvalues transverse to `A` have negative real part, attraction is exact for the linearized affine row; for a full-rank dissipative affine flow with invariant Bloch ball, the basin can be the whole ball.
- If eigenvalues are purely imaginary or have zero real transverse modes, classify as invariant-but-not-attracting unless another receipt supplies contraction.
- For nonlinear/composite cases, use interval boxes and Attractors.jl/DynamicalSystems.jl as an outer approximation, then prove the finite graph statement with can-fail controls.

### 1.3 Lyapunov-Type Object

Evaluate both candidate families:

1. Ratchet narrowing measure: finite representative count, chart volume, denominator, or interval-box volume after each constraint step.
2. Entropy-ledger deltas: exact entropy drops and typed entropy rows, especially `a54224476`.

Decision: the right Lyapunov-type object for this program is the ratchet narrowing measure, with entropy-ledger deltas as a typed readout when the measure convention is explicit.

Reason:

- A Lyapunov function must decrease along the dynamics or along ratchet steps toward the candidate basin. The narrowing measure is tied directly to exclusion, survivor sets, denominators, and interval boxes.
- Entropy deltas are valuable readouts but are typed. `a54224476` explicitly keeps differential entropy, vN entropy, and counting entropy separate, and names the lens sign caveat. Entropy is a ledger of constraint structure, not the primitive basin object.
- In `ratchet_deep_chain_v0`, steps 2, 3, and 4 decrease chart entropy by `-log(4)`, `-log(2)`, and `-log(2)` while the final terrain/order rows have entropy delta `0` because they do not add an absolutely continuous measure cut. The narrowing object still records the finite/order exclusion.

Pilot rule:

- Report both `V_narrow` and `Delta H`.
- Treat `V_narrow` as the Lyapunov-type candidate.
- Treat `Delta H` as corroborating telemetry only when its type table and sign convention are pinned.

### 1.4 Failure Semantics

Failure of attraction is information, not cleanup.

Use these labels:

- `attracting`: invariant and attracting from a computed neighborhood.
- `invariant_not_attracting`: invariant but no contraction into the set.
- `repelling`: invariant with transverse expansion or local orbits leaving under forward time.
- `shell_breaking`: the candidate shell/set is not invariant.
- `neither`: not invariant and not specifically repelling as the candidate object.
- `empty_conditioned_survivor`: the constrained candidate has no fixed-point/survivor witness under the committed row.

Re-read of the committed terrain-sweep zero-survivors result:

- The `ratchet_s6_terrain_sweep_v0` result does not say "the conditioned shell is an attractor with zero survivors." It says all 8 committed S5 terrain rows have zero fixed-point survivors on `T_pi/6`, no pure-shell-compatible terrain, and no terrain ranking.
- Therefore the conditioned shell is not "invariant-but-not-attracting" for the worked rows. It is `shell_breaking` / `neither` as an attractor candidate, with `empty_conditioned_survivor`.

## Worked Example: Two Committed Terrain Rows

Object: conditioned shell `T_pi/6` with

```text
r(theta) = (sqrt(3)/2 cos(theta), sqrt(3)/2 sin(theta), 1/2).
```

### Ne_Spiral_R

Committed affine row:

```text
M = [[0, 2*sqrt(3)/3, -2*sqrt(3)/3],
     [-2*sqrt(3)/3, 0, 2*sqrt(3)/3],
     [2*sqrt(3)/3, -2*sqrt(3)/3, 0]]
b = [0, 0, 0]
charpoly = lambda * (lambda**2 + 4)
eigenvalues = 0, +/- 2i
kernel = span((1,1,1))
```

Whole-ball classification: `invariant_not_attracting`. It is a pure rotation/orbit class, not a basin.

Conditioned-shell read:

```text
z_dot on T_pi/6 = sqrt(2)*cos(theta + pi/4)
d||r||^2/dt on T_pi/6 = 0
shell_average_z_dot = 0
```

The pure sphere is invariant, but the fixed `z=1/2` shell is not. The fixed axis hits `z=1/2` at radius squared `3/4`, not `1`, so there is no conditioned-shell fixed survivor.

Conditioned-shell classification: `shell_breaking`, `neither`, `empty_conditioned_survivor`.

### Ni_Source_R

Committed affine row:

```text
M = [[-1/4, 2*sqrt(3)/15, -2*sqrt(3)/15],
     [-2*sqrt(3)/15, -1/4, 2*sqrt(3)/15],
     [2*sqrt(3)/15, -2*sqrt(3)/15, -1/2]]
b = [0, 0, 1/2]
charpoly = lambda**3 + lambda**2 + (189/400)*lambda + 203/2400
eigenvalues ~= -0.341645905918435,
               -0.3291770470407825 +/- 0.3731199415923834 i
r_star = (-8*(-8 + 5*sqrt(3))/203,
          8*(8 + 5*sqrt(3))/203,
          139/203)
||r_star||^2 = 37113/41209 < 1
```

Whole-ball classification: `attracting`. The fixed point is displaced and interior; the committed result says the whole Bloch ball converges to `r_star` because the pinned spectrum has negative real part. `Ni_Pit_L` is the sign-mirror displaced case.

Conditioned-shell read:

```text
z_dot on T_pi/6 = sqrt(2)*cos(theta + pi/4)/5 + 1/4
d||r||^2/dt on T_pi/6 = -1/8
shell_average_z_dot = 1/4
```

The shell is not invariant; the attractor lies inside the ball and off the pure conditioned shell.

Conditioned-shell classification: `shell_breaking`, `neither`, `empty_conditioned_survivor`.

## 2. Sub-Basin Program

Post-saturation target: `ratchet_deep_chain_v0`, because it already records:

- a scoped saturated object for available committed constraints;
- final effective denominator `16`;
- a finite representative object with `Z4 x Z2` coordinate model;
- per-step narrowing and entropy rows;
- a mortality exhibit for a raw window that is not quotient-well-defined;
- terrain/order rows that bind but do not add measure cuts.

Method:

1. Define the saturated carrier `S` from the final representative set and chart/interval surface.
2. Define the dynamics `F_C` as the admissible stage/terrain/operator update restricted to the saturated carrier.
3. Compute attracting blocks `B_i` and exits `E_i` as finite pairs `(B_i, E_i)`:
   - `F_C(B_i \\ E_i) subset B_i`;
   - exits witness the boundary where the block fails to retain orbits;
   - candidate attractor `A_i = Inv(B_i \\ E_i)`.
4. Build the finite lattice:
   - vertices are block-pair attractors or outer interval-box attractors;
   - order is reachability / inclusion of basins;
   - meet/join are computed by intersection/union followed by invariant-core recomputation, not by names.
5. Compute Morse decomposition:
   - strongly connected components of the interval-box graph give Morse sets;
   - directed edges between SCCs are connecting-orbit witnesses;
   - nonzero edges are the computable "not fully independent" structure.
6. Validate each sub-basin row with controls:
   - erased stage order;
   - shuffled representative labels;
   - wrong entropy type/sign;
   - collapsed `Z4 x Z2` rival;
   - interval refinement stability;
   - empty survivor / no-attraction controls.

Implementation route:

- Exact affine rows first for S5 terrain flows.
- Interval-box outer approximations for nonlinear/composite rows.
- Attractors.jl/DynamicalSystems.jl for numerical basin candidates.
- Finite graph + SMT/cvc5 checks for the block-pair and order claims.
- The old `Basin(F_C,A,R)`, Lyapunov-rank, and interval-box-graph language is authorized as a design target from the mined estate, but the literal strings were not found as committed load-bearing surfaces during this pass. Under `77fb7ca52`, old basin rows are mine material only until a fresh v6 packet instantiates them.

## 3. Testable QIT-Engine Reading

Claim to make testable:

```text
The engine runs in an attractor, and the engine itself is an attractor-like finite/dynamical object. The eight stages are degrees of freedom on that object.
```

Current consistency evidence:

- `123b8e7d8` shows the loop-local 8-stage engine word has bounded MPS cost at computed sizes: max chi `[4,8,4]` at `n=8/12/16` across the double traversal, with all-to-all and Haar controls. This is consistency evidence for a structured stage-word object, not an attractor proof.
- `engine_readout_strategy_fidelity_v0` consumes `123b8e7d8` and records readout strategies as coordinate/readout surfaces over the same loop-local replay. This supports "readout strategies as coordinates" for a pilot, not admission.

Decisive test:

```text
Compute the omega-limit set of the stage-word dynamics. Decide whether it is a proper attractor, and whether the eight stages act as degrees of freedom on it rather than as independent engines.
```

Pilot row:

- State: committed stage-word trajectory/replay from `123b8e7d8`.
- Dynamics: stage-word shift/update plus readout strategy maps.
- Candidate attractor: omega-limit set of the loop-local stage-word dynamics.
- Coordinates: readout strategies and stage positions.
- Required outputs: invariant set, attracting neighborhood, Lyapunov/narrowing candidate, stage DoF action table, controls against random word/all-to-all/Haar and stage-order erasure.

## 4. Pilot Registration

Pilot name: `basin_criterion_pilot_v0`.

Phase: sim-wizard Phase 1 / build-card only.

Scope:

- Run the criterion exactly on committed S5 affine terrain flows.
- Re-read the conditioned `T_pi/6` shell and one ratchet chain step.
- Produce invariance, attraction, Lyapunov-type, and failure classification per selected terrain.
- Include one displaced Ni fixed-point terrain (`Ni_Source_R`; `Ni_Pit_L` is the sign mirror).
- Ask the first sub-basin question honestly: do any committed affine terrains admit multiple attractors on the Bloch ball?

Expected answer:

- Affine dissipative rows generically have unique attracting fixed points or attracting slices, not multiple isolated attractors on the ball.
- Pure Ne rows have invariant orbit classes, not attracting basins.
- The real sub-basin frontier is nonlinear/composite/stage-word dynamics after saturation, especially the `ratchet_deep_chain_v0` carrier and the QIT stage-word omega-limit test.

Fresh scratch command used for this receipt:

```bash
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba \
  /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# exact SymPy recomputation of Ne_Spiral_R and Ni_Source_R panel rows
PY
```

No canonical result JSON was written by this command.

## Route Truth

Native Codex child subagents ran read-only sidecar checks:

- provenance/evidence miner: completed; reported that committed evidence supports the criterion but not literal pre-existing `Basin(F_C,A,R)` / `KMV` / `Lyapunov-rank` load-bearing claims;
- affine math cross-check: completed; independently classified `Ne_Spiral_R` and `Ni_Source_R` as above.

Gemini TUI cross-check was requested, but no callable Gemini TUI tool was available in this Codex runtime. No OMX route was used.

No `git add` or `git commit` was run.

## BINDING-SPEC RECONCILIATION - 2026-06-11

Status: appended reconciliation against the binding Hermes basin/manifold spec and basin-packet contract.

This section does not delete or demote the Conley/lattice material above. The two framings are complementary: the finite Morse graph over strongly connected components is the Markov/communicating-class object. The earlier Conley block-pair and lattice rows remain the right topology-facing implementation route; the binding spec adds the required finite `M(C)` vocabulary, claim ladder, and card contract.

Existing receipt sections kept:

> "Compute attracting blocks `B_i` and exits `E_i` as finite pairs `(B_i, E_i)`"

> "Build the finite lattice"

> "Compute Morse decomposition"

> "strongly connected components of the interval-box graph give Morse sets"

> "directed edges between SCCs are connecting-orbit witnesses"

These are retained as the Conley/lattice view of the same finite transition structure. In the binding vocabulary, SCCs/closed classes/communicating classes form the hierarchy; directed edges are leakage, boundary, escape, or transition witnesses.

### M(C)-Native Formulation

For a constraint family `C`:

- `S`: finite or bounded state/probe space.
- `Adm_C`: explicit admissibility predicate on `S`.
- `M(C) = {x: Adm_C(x)}`: admitted carrier/survivor set under `C`.
- `R_C`: allowed update semigroup generated by admitted updates, probes, terrain/stage maps, ratchet steps, or ordered channel words under `C`.
- Trapping set: `A subset M(C)` is trapping when `R_C(A) subset A`.
- Basin of a trapping/terminal candidate: `B(A) = {x: omega_{R_C}(x) subset A}`.
- For a finite generated `R_C` with multiple allowed generator choices, use the
  standard nondeterministic-transition-system fork explicitly:
  `can_reach_terminal` is existential/may reachability to a terminal class,
  while `sure_basin_omega_containment` is universal/must containment where all
  generator choices have omega-limit inside `A`.
- Unqualified basin-map citations are forbidden when may and must semantics
  differ; name `can_reach_terminal` or `sure_basin_omega_containment`.
- Ratcheting: tighten `C`, recompute `M(C)`, rebuild the `R_C` transition graph/semigroup, and classify each basin's fate as `survives`, `shrinks`, `SPLITS`, `metastable`, or `collapses`.

This replaces any loose "cluster converges" reading. A candidate basin is a finite admitted transition object with an update rule, trapping evidence, omega-limit/closed-class evidence, and boundary/escape tests.

### Vocabulary Ladder And Earn-The-Term Discipline

Use the weakest earned term that the receipt supports:

1. `terminal/closed communicating class`: earned when the finite `R_C` graph has a closed class with no outgoing allowed transition.
2. `chain-recurrent class`: earned when recurrence survives the chosen chain/epsilon relation, including Conley-style SCC/Morse evidence.
3. `nested basin`: earned when a basin decomposes into receipt-backed subbasins/subsubbasins under tightening/refinement.
4. `metastable set`: earned when residence/stability is real but escape/leakage exists on the tested horizon or perturbation family.
5. `almost-invariant set`: earned when most allowed transitions stay inside but boundary leakage is measured.
6. `communicating class`: earned when states mutually reach one another but closure/trapping is not yet shown.

Use `separatrix` or `basin boundary` only when the receipt names the boundary test separating retained states from escape/failure states. The Morse graph is the graph of this hierarchy: vertices are communicating/chain-recurrent/terminal classes as earned; edges are leakage, transition, or connecting-orbit witnesses.

Safe CR wording:

> "Attractor-basin criterion: constraints should form or reveal a finite dynamical basin, not merely a similar-looking cluster."

> "Similarity, clustering, repeated motifs, or provider/model agreement is not convergence."

For this receipt, the safe current claim is: the basin criterion is now a finite `M(C)`/`R_C` build contract with Conley/lattice implementation support. It is still not an admitted basin theorem until the basin-packet card below is filled by a scratch-diagnostic result and passes the audit contract.

### Basin-Packet Contract: The 9 Card Requirements

Every basin-packet card must include these 9 requirements:

1. finite `S`;
2. `Adm_C`;
3. `R_C` explicit;
4. trapping test;
5. Lyapunov/monotone-exclusion observable;
6. escape tests;
7. basin partition (terminal vs metastable vs leaky);
8. the engine-DoF perturbation test;
9. the negative controls (similarity-only cluster, shuffled order, root-off, F01-only, N01-only, quotient-erased, commutative-collapse).

Notes for this receipt:

- Requirements 1-4 map the Conley/lattice rows onto finite state, predicate, semigroup, and trapping tests.
- Requirement 5 uses the existing `V_narrow` discipline first, with typed entropy rows as telemetry only; the observable direction convention must be explicit, such as exclusion non-decreasing or reachable-set size non-increasing.
- Requirement 6 is the existing failure-semantics lane plus explicit Markov/finite transition escape checks.
- Requirement 7 must classify terminal/closed, metastable/almost-invariant, and leaky communicating classes instead of calling every SCC a basin; if the transition relation is generated/nondeterministic, split basin-map rows into `can_reach_terminal` may semantics and `sure_basin_omega_containment` must semantics.
- Requirement 8 decides whether the eight engine stages are genuine degrees of freedom on/inside/over the basin: perturbing a stage must measurably change basin membership, escape, stability, or subbasin transitions.
- Requirement 9 is mandatory negative-control coverage. Missing any listed negative control demotes the packet to candidate, diagnostic-only, or blocked.

### Key Guard

Clustering/model agreement is NEVER a basin. State space + update rule + trapping + boundary/escape evidence are required.

Both audit families now enforce this guard: the repo-side basin/manifold contract and the Hermes-patched `nonclassical-sim-contract-audit`. A row can be useful if it shows repeated motifs, cross-model agreement, or visual clustering, but it cannot promote basin language until the finite `S`, `Adm_C`, explicit `R_C`, trapping test, basin partition, and escape/boundary evidence exist.

### Pilot Delta

`/tmp/basin_pilot_card.md` must carry this contract explicitly before the pilot is executable:

- add a `Binding Basin-Packet Contract` section with the 9 requirements;
- add the clustering/model-agreement guard;
- add the vocabulary ladder and earn-the-term rule;
- require output fields for `S`, `Adm_C`, `R_C`, trapping, `V_narrow` or monotone-exclusion observable, escape tests, basin partition, engine-DoF perturbation, and the negative-control suite;
- keep the old affine/Conley panel as the first worked source slice, but do not let it alone satisfy the full basin packet.
