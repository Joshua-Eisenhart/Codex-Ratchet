# Dynamic Manifold Upgrade Design - 2026-06-12

Bottom line: the minimal honest upgrade is not another Axis-0 formula sweep. It is a dynamic state layer on `M(C)`: states evolve, entropy is computed from those states at each time, shells are recomputed from the live field/boundary object, `j/k` fuzz is emitted as admissible-future multiplicity, and Axis-0 becomes `perturb -> watch -> classify spread-vs-damp` over a trajectory window.

Claim ceiling: design receipt only. No sims run. No proofs. No admission, canonical, bridge, physics, or Axis-0 closure claim.

Owner correction carried as binding: the old anchor did not build Axis-0. Its `phi=(2x-5y+7z+3xy-z^2+4r2+11shell)/97` is a synthetic static coordinate polynomial, not an entropy field computed from a state; shells were static labels; no `j/k` future multiplicity existed; and allostasis/homeostasis require response over time.

Minimal reuse answer:

- Reuse the 33-cell Family A carrier, generator adjacency, and engine stroke machinery for v0.
- Reuse `basin_dof_perturb_and_read_v0` as protocol shape only: perturb, evolve/read, classify `RETURN/BOUNDARY/SCRAMBLING`. Do not reuse its old `phi` readout as the entropy answer.
- Reuse `manifold_entropy_ledger_v0` and entropy-type doctrine as type guards.
- Reuse spinor-network surface and QCA/ring-checkerboard packets as successor substrate candidates, not as v0 prerequisites.
- Reuse the cover v2/v2.1 CW carrier as cellular shell/complex machinery, not as the disowned `b6=-b0*b3` law.

Owner-choice points are marked explicitly below.

## (1) THE STATE OBJECT

What evolves must be a state object, not a scalar label.

### Candidate A - Family A per-cell density states `rho_c(t)`

Object:

- Carrier: committed Family A 33-cell Bloch-grid object.
- State at cell `c`: `rho_c = (I + r_c . sigma) / 2`, where `r_c` is the cell's Bloch vector.
- Trajectory: `rho_{c_t}` under committed generator edges or engine stroke schedules.

Pros:

- Minimal v0. The carrier, cells, generator labels, transition graph, and engine stroke machinery already exist.
- It gives a real answer to "what entropy gradient is being used?": local von Neumann entropy `S_vN(rho_c(t))` and directed differences `Delta_e S = S(rho_dst(t+1)) - S(rho_src(t))`.
- It can reuse `engines_run_with_axes_v0`, `basin_rc_transition_graph_v0`, `basin_generating_set_sweep_v0`, and the existing identity/shuffle/over-boundary control idioms.
- It is enough to test whether the old static `phi` sign predicts any dynamic spread/damp row.

Cons:

- It is chart-relative and coarse. The 33-cell grid is a quotient view, not the final surface.
- A single-cell density entropy is weaker than the owner-side shell/cut pipeline `M(C) -> Xi -> rho_AB -> entropy scalar field`.
- It may not express correlation persistence unless v0 also tracks ensembles, neighborhoods, or edge/cut states.

Determination:

- PICK for v0: this is the smallest honest dynamic carrier that can be built without inventing new substrate doctrine.
- Do not pick it as final `M(C)` doctrine. It is the first dynamic chart packet.

### Candidate B - Spinor-network surface state

Object:

- Carrier: finite spinor network surface, especially the n4 surface estate: 4 nodes, 5 edges, 2 faces, `C^16`, density quotient rows, terrain flux/current rows, and the v3 surface chart-recovery packet.
- State: joint network state `rho_N(t)` or pure vector `|Psi(t)>` with reduced states `rho_i(t)`, `rho_AB(t)`, or shell-cut states.
- Trajectory: channel/retrieval/QNN/Hopfield-style update on the network.

Pros:

- Best doctrinal fit for "upgrade the whole manifold": the owner doctrine says charts are views of a finite spinor network surface.
- Supports real correlation entropy: conditional vN, mutual information, coherent information, and channel readouts can be computed from the actual network state rather than a chart scalar.
- The v3 surface result has partial pre-registered chart-cell identity evidence, so it is no longer just a wish.

Cons:

- Not minimal for v0. The surface estate still has open coverage: partial A33 recovery, a missed entangled `-z` cell, no doctrine closure, no global quantum-Hopfield theorem.
- A strict retrieval/channel dynamic layer still needs to be built for the selected network state if used as the primary dynamic substrate.
- Higher implementation blast radius.

Determination:

- OWNER-CHOICE POINT: if the owner requires Axis-0 to be built only on the surface rather than a chart, this becomes the primary substrate.
- Engineering recommendation: do not block v0 on this. Build v0 on the 33-cell dynamic chart, then lift the same measurement contract to the surface.

### Candidate C - Ring-checkerboard / QCA field

Object:

- Carrier: ring-checkerboard finite support with brickwork/Margolus local updates; QCA v3 open-chain local-unitary fixture for L/R flux index.
- State: finite field configuration or quantum local state over the chain.
- Trajectory: local rule applied phase-wise.

Pros:

- Cleanest locality/update form: finite support plus local homogeneous rule.
- QCA v3 earned a bounded open-chain fixture where L/R disciplines carry opposite extracted indices.
- Natural home for `j/k` future multiplicity if the admissible local-rule family is explicitly enumerated.

Cons:

- QCA v3 is open-chain fixture evidence, not finite-ring/global QCA admission.
- It does not by itself give the whole manifold state, and it does not yet include the required Axis-0 entropy/shell/fuzz protocol.
- A deterministic local unitary has trivial one-step multiplicity unless the admissible perturbation/rule family is part of the state row.

Determination:

- OWNER-CHOICE POINT: use as final substrate only if the owner wants the manifold realized primarily as local-update CA/QCA.
- Reuse for later locality and local-rule rows. Not required for minimal v0.

## (2) THE DYNAMICS

The committed generator family should become actual time evolution:

```text
state row:
  carrier_id
  state_id
  t
  cell_or_node
  rho_or_state_vector
  generator_or_channel_applied
  source_state_id
  target_state_id
```

Minimal v0 dynamics:

- Start with Family A cells as density states `rho_c`.
- Use committed generator edges from the 33-cell transition graph.
- Use one schedule first, not a broad queue:
  - either one engine stroke schedule from `engines_run_with_axes_v0`;
  - or one basin DoF from `basin_dof_perturb_and_read_v0`;
  - or one declared generator such as `D_z` or `R_x`.
- Persist the trajectory window `t=0..T`, with `T` small and pinned.

Perturbation family, the pokes:

- zero perturbation: calibration, should damp/return;
- one-cell neighbor perturbation: smallest local shake on the carrier;
- generator-DoF perturbation: change active generator set or DoF row;
- order perturbation: shuffle/permute one schedule, the N01-style control;
- over-boundary perturbation: push outside `Adm_C`, should classify boundary;
- probe-erased entropy control: constant entropy or erased state-dependence, should degrade the readout.

Reuse:

- `engines_run_with_axes_v0` already maps all 33 starting cells through four-stroke Carnot/Szilard trajectories and has identity and shuffled-order controls.
- `basin_dof_perturb_and_read_v0` already has the `RETURN/BOUNDARY/SCRAMBLING` vocabulary and controls, but it is formula-relative to old `phi`.
- `basin_rc_transition_graph_v0` supplies the transition graph semantics, SCCs, terminal classes, may/must basin language, and absent-exit proof pattern.

Design correction:

- Do not call a one-step static lookup a response. Response means compare the perturbed trajectory to an unperturbed/control trajectory over a window.

## (3) THE ENTROPY FIELD

The real answer to "what entropy gradient is being used?" in v0:

```text
S_t(c) = S_vN(rho_c(t)) = -Tr(rho_c(t) log rho_c(t))
Delta_S_t(c -> c') = S_{t+1}(c') - S_t(c)
```

This replaces static `phi` for Axis-0 measurement purposes.

For richer states, keep typed alternatives live:

- local vN entropy: valid once a density quotient exists;
- conditional vN `S(A|B)`: valid once a bipartition/shell-cut state exists;
- mutual information: unsigned correlation diagnostic once `rho_AB` exists;
- coherent information `I_c(A>B) = S(rho_B) - S(rho_AB)`: signed cut/channel candidate once the cut/channel exists;
- counting entropy: valid for finite support/future multiplicity rows;
- differential/chart entropy: valid only with an explicit chart/measure convention;
- record/syndrome conservation accounts: valid only after the record object exists.

Minimal v0 should use local `S_vN(rho_c)` because it is state-derived and available on the 33-cell chart. It should also emit a typed-row warning:

```text
axis0_entropy_field_v0:
  entropy_type: local_von_neumann
  state_source: rho_c from Bloch cell
  not_yet: conditional_vN, coherent_information, shell_cut_entropy
```

Owner-choice point:

- OWNER-CHOICE POINT: final Axis-0 may require `Phi0(rho_AB)` rather than local `S_vN(rho_c)`. v0 should not decide that doctrine point; it should create the first honest state-derived entropy-gradient row and leave `Xi/rho_AB` as a later rung.

## (4) DYNAMIC SHELLS

A dynamic shell is a recomputed region/boundary at time `t`, not a static label copied from the carrier.

Live alternatives:

1. Entropy-level shell:
   - Shell is a level set or band of `S_t(c)`.
   - Boundary is where `Delta_S` changes sign or crosses a threshold.
   - Minimal on Family A.

2. Correlation-boundary shell:
   - Shell is a cut/correlation boundary in `rho_AB(t)` or network reduced states.
   - Boundary is where conditional entropy, mutual information, or coherent information changes class.
   - Better for spinor-network surface.

3. Basin-boundary shell:
   - Shell is the terminal/SCC/basin boundary under the active generator/DoF dynamics.
   - Boundary is `RETURN`, `BOUNDARY`, or `SCRAMBLING` against terminal/reconvergence checks.
   - Reuses existing basin machinery.

Determinable v0 choice:

- Use entropy-level shell plus basin-boundary readout on the Family A dynamic chart.
- Emit the correlation-boundary shell as `blocked_until_rho_AB_or_surface_cut`.

Computable row:

```text
dynamic_shell_row:
  t
  shell_rule_id
  member_cells
  boundary_edges
  entered_cells
  exited_cells
  persistence_fraction
  entropy_band_or_boundary_value
```

Owner-choice point:

- OWNER-CHOICE POINT: whether the doctrinal shell is ultimately entropy-level, correlation-boundary, basin-boundary, or a registered family. v0 should preserve all three as alternatives and make one computable.

## (5) J/K FUZZ

`j/k` fuzz should be a row of admissible-future multiplicity per current state.

Minimal finite definition:

```text
k(c,t) = number of candidate one-step continuations from state c at time t
j(c,t) = number of those continuations that remain admissible under the active constraints
fuzz(c,t) = structure of the surviving futures, not just the ratio
```

For the Family A v0:

- `k` can be the outgoing generator-edge count or the count of candidate perturbation+generator continuations.
- `j` is the count that remains in `Adm_C`, satisfies the active shell/entropy constraint, and has a typed entropy row available.
- If distinct continuations collapse to the same target state, record both raw continuation count and quotient target count.

Suggested row:

```text
jk_fuzz_row:
  t
  state_id
  candidate_continuations_k
  admissible_continuations_j
  admissible_target_count
  entropy_signature_classes
  shell_target_classes
  killed_continuations
  fuzz_class: none | low | split | broad | degenerate
```

Controls:

- deterministic identity schedule should give low or no fuzz;
- over-boundary perturbation should kill continuations;
- erased constraints should inflate or degenerate multiplicity;
- shuffled order should move the future structure if order matters.

Owner-choice point:

- OWNER-CHOICE POINT: the final `j/k` convention may count generator choices, perturbation choices, local-rule choices, or quotient-distinct futures. v0 should emit all three counts where available: raw continuations, admissible continuations, and quotient-distinct targets.

## (6) AXIS-0 PROPER

Axis-0 proper is the response classifier:

```text
perturb -> watch trajectory -> classify spread-vs-damp per region
```

Minimum protocol:

1. Pick an initial state or region `R0`.
2. Run an unperturbed/control trajectory.
3. Apply one pinned perturbation.
4. Run the perturbed trajectory over the same window.
5. Compute state-derived entropy field `S_t`, shell rows, and `j/k` rows at each time.
6. Compare spread/damp:
   - entropy spread: variance/range/edge-gradient expansion of `S_t`;
   - shell spread: boundary growth or region fragmentation;
   - future spread: `j/k` multiplicity expansion;
   - damp: reconvergence of those rows to the control/baseline region.
7. Classify:
   - `RETURN`: state/basin and entropy/shell/future rows reconverge;
   - `BOUNDARY`: escape, terminal-class change, or shell boundary crossing persists;
   - `SCRAMBLING`: spatial/basin return occurs but entropy/shell/future readouts do not reconverge.

Allostatic/homeostatic readout:

- allostatic: perturbation increases spread/diversity/multiplicity over the window without immediate reconvergence;
- homeostatic: perturbation damps deviation and reconverges toward the baseline/control readout;
- neutral: no nontrivial movement;
- degraded: entropy/shell/future readout was erased or not load-bearing.

Relation to the old static anchor:

- Old `discrete_axis0_field_v0` can survive only as a static proxy/equilibrium-shadow candidate.
- Add a bridge row:

```text
static_phi_bridge_row:
  old_phi_sign_at_c
  dynamic_response_class_under_perturbation
  predicts_dynamic_response: true | false
  falsifier: old_phi_sign fails to predict spread/damp better than control/null
```

Either outcome is useful:

- If it predicts some dynamic response, the old field becomes an equilibrium-shadow proxy with bounded scope.
- If it fails, the old field remains formula taxonomy only and is not part of Axis-0 measurement.

The old static anchor must not be cited as Axis-0 proper unless this bridge row survives.

## (7) THE BUILD LADDER

### v0 - Minimal Dynamic Axis-0 Chart Packet

Goal:

- Smallest honest dynamic carrier + one perturbation + state-derived entropy field + spread-vs-damp readout.

Reuse:

- Family A 33-cell carrier from `manifold_super_sim_v0` / `basin_rc_transition_graph_v0`.
- Generator edges and transition lookup from existing basin/engine packets.
- Engine stroke / identity / shuffled-order controls from `engines_run_with_axes_v0`.
- Type discipline from `manifold_entropy_ledger_v0` and entropy-type doctrine.

Must build:

- `rho_c(t)` density rows for the trajectory.
- `S_vN(rho_c(t))` field.
- `Delta_S` directed gradients over active edges.
- dynamic entropy-shell rows.
- `j/k` future multiplicity rows.
- perturb-control comparison.
- `RETURN/BOUNDARY/SCRAMBLING` plus allostatic/homeostatic spread-vs-damp class.

Witness gates:

- density validity: trace 1, PSD, Hermitian;
- entropy source gate: every entropy value computed from `rho`, not from `phi` or labels;
- dynamic gate: `T>1` trajectory rows exist;
- perturb gate: zero perturb, one nonzero perturb, and one order/over-boundary control;
- shell gate: shell membership recomputed at each `t`;
- `j/k` gate: raw/admissible/quotient future counts emitted;
- readout gate: spread-vs-damp classification changes under at least one real perturbation or honestly reports no movement;
- old-phi bridge row emitted with either pass or fail.

### v1 - DoF Perturb-And-Read Replacement

Goal:

- Rebuild the existing DoF perturb table with state-derived entropy/shell/fuzz rows instead of old `phi`.

Reuse:

- `basin_dof_perturb_and_read_v0` row vocabulary and controls.
- `basin_generating_set_sweep_v0` generator-family rows.

Witness gates:

- at least one real `RETURN`;
- at least one real `BOUNDARY`;
- `SCRAMBLING` must be reachable by predicate design, or the packet must say it is unreachable and why;
- formula-relativity to old `phi` removed or isolated to bridge comparison.

### v2 - Typed Entropy / Shell-Cut Lift

Goal:

- Add the first `Xi/rho_AB` or shell-cut state row where possible.

Reuse:

- `manifold_entropy_ledger_v0`.
- entropy-type doctrine and v1/v2 co-ratchet lessons.
- Family B typed ledger and record/accounting rows.

Witness gates:

- local vN, conditional vN, MI, or coherent information type is enabled only when its state/cut/channel exists;
- premature evaluation yields named `MissingStructure`;
- no cross-type entropy sum without explicit convention.

### v3 - Spinor-Network Surface Lift

Goal:

- Run the same dynamic Axis-0 protocol on a finite spinor-network state object.

Reuse:

- `spinor_network_surface_v3` pre-registered chart-cell recovery discipline.
- `stage_lifted_spinor_shell_n4_v0`.
- `terrain_spinor_flux_nest_n4_v0`.
- Family C integrated feedstock.

Witness gates:

- network state valid;
- reduced states/cuts computed from the actual network state;
- retrieval/channel dynamics are CPTP or explicitly dissipative/post-selected;
- chart recoverability is measured, not assumed;
- dynamic entropy/shell/fuzz rows are not copied from chart v0.

### v4 - Ring-Checkerboard / QCA Locality Lift

Goal:

- Test whether local brickwork/QCA dynamics changes the dynamic Axis-0 readout relative to the global chart dynamics.

Reuse:

- `ring_checkerboard_qca_v3` realized-unitary and crossing-rank machinery.
- classical ring-checkerboard SCC/transient-topology floor.

Witness gates:

- local rule generates the trajectory, not metadata;
- finite-ring caveat remains explicit;
- local reduced states or field configurations produce entropy rows;
- `j/k` counts local-rule admissible futures, not labels.

### v5 - Cross-Substrate Comparison / Static-Shadow Adjudication

Goal:

- Compare Family A chart v0/v1, spinor-network surface v3, and QCA/locality v4 on the same perturbation vocabulary.

Witness gates:

- state object IDs separate;
- comparison rows declare quotient maps;
- old static anchor predicts or fails under a pre-registered bridge metric;
- no substrate is silently declared final because it was easier to run.

## (8) WHAT DIES

Dies or is re-scoped:

- "Axis-0 has been built" dies. Axis-0 remains unbuilt until dynamic state-derived response rows exist.
- `discrete_axis0_field_v0` as Axis-0 measurement dies. It carries only as a static proxy/formula-taxonomy packet on the 33-cell carrier.
- The contender closure "anchor alias class only = Axis-0" dies as Axis-0. It carries as static formula-family adjudication under that carrier.
- Any claim that CP.11/FEP or CP.14/marginal entropy "lost Axis-0" dies. They read different distinctions; their own-object status is untouched.
- `b6=-b0*b3` as owner doctrine dies. The cover v1/v2/v2.1 machinery carries; the law row is moot by provenance and at-chance by computation.
- Static shell labels as shell bookkeeping die for Axis-0. They carry only as initial chart metadata or controls.
- One-step polarity stability as allostasis/homeostasis dies. It carries as a static proxy sanity check only.
- Engine-axis signature rows as dynamic Axis-0 die. They carry as finite dynamics machinery and baseline trajectories.
- `basin_dof_perturb_and_read_v0` as probe-invariant dynamic Axis-0 dies because it is old-`phi` relative. It carries as perturb/read/classify protocol shape.

Carries:

- Family A 33-cell carrier and generator graph.
- Family B Hopf-torus typed ledger/feedstock.
- Family C spinor-network terrain-ladder feedstock.
- A+B weld as typed-accounting/chart-to-chart bookkeeping, not surface geometry.
- CW cellular cover carrier and chain-complex/witness-gate pattern.
- Spinor-network surface doctrine and v3 partial pre-registered family-cell identity evidence.
- Ring-checkerboard/QCA locality fixture at scratch open-chain ceiling.
- Entropy-type doctrine: types become admissible only after the enabling state/cut/channel/record exists.

## Source Surfaces Read

- `system_v6/receipts/owner_correction_axis0_not_built_20260612.md` at `0313d47bc`.
- `system_v6/receipts/axis0_deep_vein_20260612.md`.
- `system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md`.
- `system_v6/receipts/owner_doctrine_entropy_type_ratchet_20260611.md`.
- `system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md`.
- `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`.
- Family A/B/C integrated packet build/audit surfaces.
- A+B weld build/audit surfaces.
- 33-cell carrier/basin packet build/audit surfaces.
- cover v2/v2.1 build/audit surfaces.
- spinor-network surface estate/doctrine/v3 surfaces.
- QCA ring-checkerboard doctrine/v3 surfaces.
- `engines_run_with_axes_v0` build/common surfaces.
- entropy ledger, entropy-type, and typed co-ratchet surfaces.
- old static Axis-0 anchor and contender family surfaces.

## Final Design Status

This design answers the design question only:

```text
minimal honest upgrade = dynamic state object + state-derived entropy field + dynamic shells + j/k future multiplicity + perturb/watch/classify response protocol
first build target = Family A 33-cell dynamic chart v0
final substrate = OWNER-CHOICE across chart, spinor-network surface, and QCA/local-update readings
claim ceiling = design receipt only
```
