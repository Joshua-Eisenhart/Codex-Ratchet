# Axis-6 Contender-Probe Registry - 2026-06-12

Purpose: register the alternative Axis-6 precedence readout-probe space before
any readout is citable as THE Axis-6 readout.

Scope: registry receipt only. No sims were run. No result JSON was rewritten.
This file defines finite candidate representatives, alias-class detection,
expected teeth rows, closeness grades, and cost classes for a later contender
sweep packet.

Evidence ceiling: `scratch_diagnostic` planning/registry receipt.
`promotion_allowed: false`
`formal_admission_allowed: false`

## Source Hash Ledger

- Doctrine anchor: `owner_doctrine_axes_as_existence_probes_20260612.md`, commit
  `fcf1b3858`, which requires a contender registry per axis before "the readout"
  language.
- Registry-format template: `axis0_contender_probe_registry_20260612.md`, commit
  `31dfd11b6`.
- Boundary audit standard: `axis0_contender_heavy_v0/audit_verdict.md`, commit
  `c27d3dd39`; the distinction-boundary predicate must be computable and able
  to admit true contenders.
- Axis-6 anchor packet: `discrete_axis6_precedence_v0`, commit `b6fafc67f`.
- Axis-4/Axis-6 never-merge sources:
  `axis_work_order_20260612.md`,
  `terrain_operator_precedence_64_matrix/audit_verdict.md`,
  `axis_independence_discriminators_036/audit_verdict.md`, and
  `geo_s6_stacked_flows_hopf_v0/audit_verdict.md`.
- Scaffold source: `working_math_scaffold_20260609.md`, which records Axis-6
  as operator-first versus terrain-first precedence and Axis-4 as a distinct
  composition/order class.

## Axis-6 Distinction Boundary

Contenders must read the same distinction: precedence between applying an
operator and applying a terrain map on the same carrier row. A probe that
primarily reads Axis-4 deductive/inductive loop-order composition, Axis-3
placement, Axis-0 response, or generic trajectory distance without recovering
operator-first versus terrain-first precedence is not an Axis-6 contender; it is
a different-axis or geometry probe.

Pinned distinction:

- operator-first: `Phi_T(O(rho_cell))`;
- terrain-first: `O(Phi_T(rho_cell))`;
- anchor sign: `b6 = sign(||Phi_T(O(rho_cell)) - O(Phi_T(rho_cell))||_1 *
  Delta_z)`;
- anchor labels: `operator_first_precedence`,
  `terrain_first_precedence`, and `neutral_commuting_or_zero_projection`.

## Positive Boundary Predicate

A candidate reads the Axis-6 distinction only if all of the following are
computed on a finite pinned representative:

1. `same_carrier_precedence_pair`: every row uses the same carrier cell before
   and after both orders, with pinned operator `O`, terrain `Phi_T`, step size
   or flow parameter, and neutral tolerance.
2. `order_swap_changes_or_demotes`: swapping the declared order difference from
   operator-first minus terrain-first to the reverse flips all nonzero signs or
   demotes the row by a predeclared neutral rule.
3. `commuting_control_reaches_neutral`: a pinned commuting operator/terrain
   pair reaches the all-neutral or declared-zero outcome under the same
   functional.
4. `label_permutation_fails`: label-only reproduction fails on the same carrier.
5. `not_axis4_loop_order`: varying Axis-4 loop order with Axis-6 precedence
   held does not change the Axis-6 vector, and varying Axis-6 precedence with
   Axis-4 held changes the Axis-6 observable.
6. `not_axis0_or_axis3_recoverable`: Axis-0 response and Axis-3 placement keys
   do not deterministically recover the candidate vector under the declared
   shared rows or projection.
7. `not_constant_or_single_sign_vector`: the candidate is not all one sign
   except where the candidate is a named neutral/commuting control.

This predicate is intentionally positive: the anchor passes it, and a genuine
commutator-sign, L/R-action spectral order, win/lose, or trajectory-difference
contender can pass if it computes the same operator/terrain precedence split
under pinned adapters. The predicate must not kill a candidate merely because
it reports a different scalar of the same precedence pair.

## Axis-4 Never-Merge Boundary

Axis-4 and Axis-6 both use order language, but they are not the same degree of
freedom.

- Axis-6 varies `Phi_T(O(rho))` versus `O(Phi_T(rho))`: terrain/operator
  precedence on a cell.
- Axis-4 varies `Phi_D=U o E o U o E` versus `Phi_I=E o U o E o U`:
  deductive/inductive loop-order composition on a shared carrier.

The distinction-boundary row is mandatory in every Axis-6 contender sweep:

1. Hold Axis-4 loop-order class fixed and vary Axis-6 precedence; the Axis-6
   observable must move.
2. Hold Axis-6 precedence fixed and vary Axis-4 loop-order class; the Axis-6
   observable must hold or be explicitly classified as an Axis-4/Axis-6 coupling
   candidate rather than a pure Axis-6 readout.
3. Any candidate whose only evidence is `Phi_D/Phi_I` trajectory difference is
   `wrong_distinction` for Axis-6 unless it also computes the operator/terrain
   precedence pair and passes the positive boundary.

Existing estate anchors for this boundary:

- `terrain_operator_precedence_64_matrix` F8 reports separate fields for
  `axis6_precedence_sign`, `axis6_signed_delta_fro`,
  `axis4_inner_density_delta_fro`, `axis4_outer_density_delta_fro`, and
  `axis4_loop_class`.
- `axis_independence_discriminators_036` v2 reports Axis-4 order gap
  `0.14204848183630314`, Axis-4 class movement from `deductive_D` to
  `inductive_I`, Axis-4 hold under Axis-6 precedence variation, and Axis-6
  movement from `+0.11527418229160312` to `-0.11527418229160312`.
- `geo_s6_stacked_flows_hopf_v0` reports `g_DI` as the S6 `Phi_D/Phi_I`
  metric and keeps Matrix64 `Delta_T,O` only as overlay relation evidence.

## Registry Contract

Every future sweep packet generated from this registry must predeclare:

1. `alternative_space_bound`: the finite candidate ids below, with no extra
   candidates added after results are inspected.
2. `carrier_pin`: the committed Family A 33-cell carrier or a declared
   same-carrier adapter, including ordered `cell_id=0..32`.
3. `operator_terrain_pin`: operator, terrain, step/flow, source paths, hashes,
   and exact matrix/function rows.
4. `candidate_vector`: a 33-entry vector over the same cell ids, with raw values
   and signs in `{-1,0,+1}` where `+1=operator_first_precedence`,
   `-1=terrain_first_precedence`, and `0=neutral_commuting_or_zero_projection`
   after the candidate's declared orientation convention.
5. `canonical_alias_form`: computed before any teeth row. Exact aliases do not
   inflate the tested count.
6. `representative_selection_rule`: one representative per exact alias class;
   aliases are reported but not tested as independent contenders.
7. `classification_rule`: each candidate becomes exactly one of `alias`,
   `co_survivor`, `excluded`, `wrong_distinction`, or `open`.
8. `positive_boundary_result`: the computed predicate above, including at least
   one candidate or control that proves the predicate can admit.
9. `axis4_never_merge_result`: the boundary row above, not prose.
10. `expected_teeth_row`: the first computed comparison expected to separate
    the candidate from `A6.CP.0_committed_trace_norm_weighted_z_precedence`.
11. `cost_guard`: heavy-local rows run only after the light-symbolic alias pass
    and only on non-alias representatives.
12. `adapter_pin`: the G7 rule is binding. Every adapter realization must be
    pinned by rule, source path, convention tuple, and hash or finite row list
    before evaluation.

## Shared Alias Detection

For each candidate `R`, compute over the pinned 33 cells:

- `raw_value[c]`: exact rational, algebraic, integer, floating-with-tolerance,
  or interval-tagged scalar.
- `sign_value[c] in {-1,0,+1}` after the candidate's declared orientation.
- `zero_set`, `positive_set`, and `negative_set`.
- `rank_partition`: cells partitioned by exact raw value order after reducing
  candidate-specific gauge, spectral, action-side, or norm conventions.
- `precedence_control_signature`: result under order reversal, commuting pair,
  identity/constant-field pair, label permutation, and neutral tolerance.
- `axis_boundary_signature`: recovery/nonrecovery rows against Axis-0 response,
  Axis-3 placement, and Axis-4 loop-order keys.
- `source_convention_tuple`: provenance path, formula id, norm/sign convention,
  operator/terrain pins, flow step, neutral tolerance, and adapter rule.

Two readouts are the same Axis-6 probe iff all of the following hold:

1. Same carrier and same cell ordering.
2. Same `zero_set`.
3. `positive_set` and `negative_set` are identical after either no sign flip or
   a documented global order-convention flip. A sign flip is allowed only when
   the provenance explicitly says which side is operator-first versus
   terrain-first.
4. `rank_partition` is identical up to a strictly monotone reparameterization of
   the raw scalar and up to candidate-declared norm/action convention.
5. `precedence_control_signature` is identical.
6. `axis_boundary_signature` is identical, including the Axis-4 never-merge row.

Equal aggregate counts alone are not alias. Equal commutator norm, trajectory
gap, win/lose total, or L/R spectral total alone is not alias. Matching only
Axis-4 loop-order or Axis-3 placement metadata is evidence for
`wrong_distinction` unless the Axis-6 vector still cross-cuts those rows.

## Registered Candidate Space

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
|---|---|---|---|---|
| `A6.CP.0_committed_trace_norm_weighted_z_precedence` | Control. The `discrete_axis6_precedence_v0` 33-cell Family A carrier with pinned operator `S4:D_z` and pinned terrain `S5:Ne_Spiral_R` at `h=1/2`; raw value is `||Phi_T(O(rho_cell))-O(Phi_T(rho_cell))||_1 * Delta_z`; sign is operator-first, terrain-first, or neutral. | control | none; anchor | light-symbolic |
| `A6.CP.1_commutator_sign_readout` | Same carrier, operator, terrain, and step as CP.0; raw value is a direct signed commutator functional for the pinned pair, such as signed selected component of `[Phi_T,O](rho_cell)` or signed norm difference under a predeclared orientation. | nearest algebraic neighbor | Commutator teeth: same commuting control must be all-neutral, order reversal must flip nonzero signs, and label permutation must fail. Alias if sign vector and controls match CP.0. | light-symbolic |
| `A6.CP.2_lr_action_spectral_order` | Same carrier rows, but read precedence through left action `L_A(rho)=A rho` versus right action `R_A(rho)=rho A` spectral order, using the owner apple source naming. | close owner-source alternative; Axis-4 confusion risk | L/R teeth: prove left/right action order is the operator/terrain precedence side, not Axis-4 loop order; compare spectral rank partition and sign vector against CP.0. | heavy-local |
| `A6.CP.3_win_lose_pattern_discriminator` | Same carrier rows, with raw value from the committed scaffold win/lose precedence pattern. Representative must return a per-cell carrier table before comparison. | medium symbolic/scaffold neighbor | Win/lose teeth: compute a per-cell table, not aggregate grammar. Kill if it is label-only or if commuting/order-reversal controls do not fire. | heavy-local |
| `A6.CP.4_axis4_style_trajectory_difference_sign` | Estate alternative inspired by Axis-4 trajectory-difference signs: compute a trajectory or norm gap sign over the same cells while holding Axis-4 loop-order class fixed and varying only operator/terrain precedence. | far but important boundary row | Never-merge teeth: if the sign is driven by `Phi_D/Phi_I`, classify as `wrong_distinction`; if it varies with Axis-6 precedence while Axis-4 is held, keep open or co-survivor. | heavy-local |
| `A6.CP.5_unweighted_precedence_component_sign` | Same CP.0 pair and carrier, but raw value is the signed selected component difference, e.g. `Delta_z` or another predeclared Bloch component, without trace-norm weighting. | nearest scalar ablation | Component teeth: cells where trace-norm weighting changes sign/rank separate from CP.0; neutral-set equality alone is not alias. | light-symbolic |

## Per-Candidate Provenance Pins

### `A6.CP.0_committed_trace_norm_weighted_z_precedence`

Provenance:

- `discrete_axis6_precedence_v0` commit message pins the first Axis-6 candidate
  as `D_z + Ne_Spiral_R at h=1/2`, with the G7 rule's first fully compliant
  packet.
- `build_card.md` predeclares `Phi_T(O(rho_cell))` versus
  `O(Phi_T(rho_cell))`, pinned operator hash
  `0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566`,
  pinned terrain hash
  `ced1d4a8395b66077defbfa44dade651cac9c02ef7ea95cca9918a4019b0634a`,
  and sign functional `sign(trace_norm_weight * z_component_difference)`.
- `audit_verdict.md` reports counts `14` operator-first, `14` terrain-first,
  `5` neutral, `28` nonneutral.

Alias note: this is the control representative. Other candidates can alias it
only by the shared alias rule above; matching 14/14/5 counts is not enough.

### `A6.CP.1_commutator_sign_readout`

Provenance:

- `discrete_axis6_precedence_v0` stored contender row:
  `commutator_sign_readout`, `staged_not_run`, readout "sign of a direct
  commutator functional for the pinned operator/terrain pair".
- The packet requires this row to beat neutral/commuting and label-permutation
  controls on the same carrier.

Why it reads the same distinction: it computes the algebraic failure of
operator/terrain order to commute on the same cell.

Alias detection: candidate key includes commutator functional and selected sign
component. Alias only if the 33-cell sign vector, rank partition, and precedence
controls match CP.0.

### `A6.CP.2_lr_action_spectral_order`

Provenance:

- `discrete_axis6_precedence_v0` stored contender row:
  `lr_action_spectral_order`, `staged_not_run`, readout "LEFT action
  L_A(rho)=A rho versus RIGHT action R_A(rho)=rho A spectral order".
- `axis_work_order_20260612.md` records Axis-6 as `Phi_T(O(rho))` versus
  `O(Phi_T(rho))`, equivalently left action versus right action in owner apple
  source language.

Why it reads the same distinction: it is the owner-source action-side version
of precedence.

Alias detection: action-side convention, spectral ordering rule, and operator
pin are part of the canonical tuple. If the row collapses into Axis-4 loop
order, classify as `wrong_distinction`.

### `A6.CP.3_win_lose_pattern_discriminator`

Provenance:

- `discrete_axis6_precedence_v0` stored contender row:
  `win_lose_pattern_discriminator`, `staged_not_run`, readout "win/lose
  precedence pattern from the committed scaffold".
- `symbolic_layer_iching_taijitu_20260609.md` and screenshot-math receipts keep
  win/lose casing as readout grammar only, not axis admission.

Why it reads the same distinction: win/lose can contend only if it becomes a
per-cell operator/terrain precedence table, not if it stays symbolic grammar.

Alias detection: grammar labels are not canonical values. Alias requires the
same 33-cell vector, rank partition, and controls as CP.0.

### `A6.CP.4_axis4_style_trajectory_difference_sign`

Provenance:

- `axis_work_order_20260612.md` says Axis-4 composition order and Axis-6
  precedence must never be merged.
- `terrain_operator_precedence_64_matrix` F8 stores separate Axis-4 and Axis-6
  fields and reports Axis4 inner/outer movement separately from Axis6 selected
  output gap.
- `axis_independence_discriminators_036` v2 reports a closed Axis-4/Axis-6
  boundary where Axis-4 loop order moves under loop-order variation, holds
  under Axis-6 variation, and Axis-6 moves under precedence variation.
- `geo_s6_stacked_flows_hopf_v0` reports `g_DI` as Axis-4-style
  `Phi_D/Phi_I` loop-order gap and keeps Matrix64 `Delta_T,O` as overlay only.

Why it reads the same distinction: only a trajectory-difference sign that is
computed with Axis-4 held and operator/terrain precedence varied can contend
for Axis-6. A pure `Phi_D/Phi_I` sign is Axis-4, not Axis-6.

Alias detection: Axis-4 loop-order class and Axis-6 precedence convention are
part of the canonical tuple. The never-merge row must run before any alias or
co-survivor classification.

### `A6.CP.5_unweighted_precedence_component_sign`

Provenance:

- CP.0 already computes the weighted z-component difference and neutral rule.
- The build card exposes `Delta_z` as the direction component multiplied by
  trace-norm weight.

Why it reads the same distinction: it is the scalar ablation of the committed
operator/terrain precedence functional.

Alias detection: alias only if the unweighted component sign vector, zero set,
rank partition, and controls match CP.0. Equal nonneutral count is not enough.

## Expected Sweep Phases

Phase 1: light-symbolic alias pass.

- Compute CP.0, CP.1, and CP.5 directly from the existing 33-cell carrier and
  pinned operator/terrain pair where source-backed rows exist.
- For CP.2-CP.4, verify whether a source-backed 33-cell adapter already exists.
  If not, mark `open_adapter_required` and do not run heavy batteries.
- Emit raw candidate count, alias-class count, non-alias representative count,
  wrong-distinction count, positive-boundary pass count, and Axis-4
  never-merge pass count.

Phase 2: heavy-local representative pass.

- Run only candidates whose adapter exists and whose light-symbolic canonical
  form did not alias CP.0 or fail the same-distinction gate.
- Required teeth against CP.0:
  - exact Hamming disagreement cells by `cell_id`;
  - neutral-set disagreement cells;
  - per-generator or per-row stability deltas where the carrier supplies
    dynamics;
  - Axis0, Axis3, and Axis4 nonrecoverability rows;
  - no-structure controls: commuting pair, identity/constant-field pair, order
    reversal, label permutation, neutral tolerance flip, and component erasure;
  - source-specific controls: commutator functional flip, L/R action swap,
    win/lose grammar erasure, trajectory gap with Axis-4 held, and Axis-4
    loop-order variation with Axis-6 held.

## Stop Rule

Stop after the registry in this receipt. The sweep packet is a separate later
build.

No row from this registry authorizes:

- Axis-6 admission;
- "THE Axis-6 readout" language;
- bridge, physics, or manifold promotion;
- broad queue launch;
- treating co-survivors as merged;
- using an unpinned adapter realization;
- using Axis-4 loop-order evidence as Axis-6 precedence evidence.

`promotion_allowed: false`
