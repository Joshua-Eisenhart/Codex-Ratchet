# Carnot/Szilard/Basin stroke correspondence map

created_at: 2026-06-12
lane: mapping-mining
write_scope: this file only
ceiling: mapping_receipt
promotion_allowed: false
formal_admission_allowed: false
claim_status: computed correspondence candidates from committed rows; no basin-cycle packet built here

## Authority and scope

Read-first doctrine:

- `system_v6/receipts/owner_doctrine_carnot_szilard_connection_20260612.md`
  - commit: `24d03db89`
  - expectation used: expectation 3, the stroke-to-stroke structure map must be computed from committed rows, not asserted.

This receipt grounds the map for the next build card. It does not promote the Carnot/Szilard/basin connection. The next packet still has to compute the per-cycle typed ledger and basin-Landauer floor on the committed RETURN rows.

## Source inventory

Committed rows read:

- Carnot/Szilard ledger v1:
  - commit: `d79d71a0d`
  - result: `system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_envelope_results.json`
  - source: `system_v6/sims/carnot_szilard_landauer_ledger_v1/carnot_szilard_landauer_ledger_v1_common.py`
- Carnot/Szilard fence v0:
  - commit: `e10273983`
  - result: `system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- Basin DoF perturb/read v0:
  - commit: `f41d4c311`
  - result: `system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json`
  - source: `system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_common.py`
- Typed entropy machinery:
  - `system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json`
  - commit seen in log: `a54224476`
  - `system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json`
  - commit: `bd7a54080`
- Two-loop / order forms:
  - `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json`
  - commit seen in log: `9dad43b2b`
  - `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`
  - commit seen in log: `7dc512454`, with later tooling remediations
  - `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json`
  - commit: `fe06d49bd`
  - nested-ratchet support receipt: `system_v6/receipts/nested_ratchet_support/nr_fresh_audit_verdict.md`

## Carnot column: committed ledger rows

Primary reversible Carnot row:

- JSON path: `carnot_szilard_landauer_ledger_v1_envelope_results.json#.cycle_ledger_tables.reversible_carnot_cycle`
- `classification`: `classical_baseline`
- `expected`: `sat`
- `derived.q_hot_total.string`: `2/1`
- `derived.q_cold_total.string`: `-1/1`
- `derived.work_out_total.string`: `1/1`
- `derived.energy_residual.string`: `0/1`
- `derived.entropy_production.string`: `0/1`
- `derived.eta.string`: `1/2`
- `derived.eta_c.string`: `1/2`
- `derived.eta_relation`: `equal_to_eta_C`
- `z3.status`: `sat`
- `cvc5.status`: `sat`
- `z3.constraints`: `first_law_q_hot_plus_q_cold_minus_work_eq_0=true`, `entropy_production_nonnegative=true`, `no_asserted_eta_bound=true`

The four committed stroke rows are:

| Carnot stroke field | q_hot | q_cold | work_out | committed JSON field |
|---|---:|---:|---:|---|
| `hot_isothermal_expansion` | `2/1` | `0/1` | `3/2` | `.cycle_ledger_tables.reversible_carnot_cycle.strokes[0]` |
| `adiabatic_expansion` | `0/1` | `0/1` | `1/2` | `.cycle_ledger_tables.reversible_carnot_cycle.strokes[1]` |
| `cold_isothermal_compression` | `0/1` | `-1/1` | `-1/1` | `.cycle_ledger_tables.reversible_carnot_cycle.strokes[2]` |
| `adiabatic_compression` | `0/1` | `0/1` | `0/1` | `.cycle_ledger_tables.reversible_carnot_cycle.strokes[3]` |

Boundary/fence rows in ledger v1:

- `sub_carnot_irreversible_cycle`: `.cycle_ledger_tables.sub_carnot_irreversible_cycle`
  - `expected`: `sat`
  - `derived.eta.string`: `1/4`
  - `derived.entropy_production.string`: `1/2`
  - `derived.q_hot_total.string`: `2/1`
  - `derived.q_cold_total.string`: `-3/2`
  - `derived.work_out_total.string`: `1/2`
- `trivial_zero_work_cycle`: `.cycle_ledger_tables.trivial_zero_work_cycle`
  - `expected`: `sat`
  - heat/work totals `0/1`
  - `derived.entropy_production.string`: `0/1`
  - `derived.eta.string`: `0/1`
- `candidate_super_carnot_cycle`: `.cycle_ledger_tables.candidate_super_carnot_cycle`
  - `expected`: `unsat`
  - `derived.eta.string`: `3/4`
  - `derived.eta_c.string`: `1/2`
  - `derived.entropy_production.string`: `-1/2`
  - `z3.status`: `unsat`
  - `cvc5.status`: `unsat`
- broken-fence witness: `.controls.broken_fence_drop_entropy_constraint_super_carnot`
  - dropping `entropy_production_nonnegative` flips the same super-Carnot ledger to `sat`
  - persisted model includes `q_hot=2`, `q_cold=-1/2`, `work_out=3/2`, `entropy_production=-1/2`, `eta=3/4`

Important boundary: the ledger JSON stores per-stroke heat/work entries. Entropy is row-level as `derived.entropy_production`, computed from stroke totals, not a per-stroke entropy column.

## Szilard column: committed measure-feedback-erase rows

Primary paid Szilard row:

- JSON path: `carnot_szilard_landauer_ledger_v1_envelope_results.json#.szilard_landauer_ledger_tables.szilard_paid_measure_feedback_erase`
- `classification`: `classical_baseline`
- `expected`: `sat`
- `derived.work_out`: `k*T*ln(2)`
- `derived.required_erasure`: `k*T*ln(2)`
- `derived.net_after_paid_erasure_ln2_coeff.string`: `0/1`
- `z3.status`: `sat`
- `cvc5.status`: `sat`
- `z3.derived.paid_ln2_coeff.string`: `1/1`
- `z3.derived.required_ln2_coeff.string`: `1/1`

The committed Szilard ledger rows are:

| Szilard phase field | nats_recorded_ln2_coeff | work_out_ln2_coeff | erasure_paid_ln2_coeff | committed JSON field |
|---|---:|---:|---:|---|
| `measure_record_one_bit` | `1/1` | `0/1` | `0/1` | `.szilard_landauer_ledger_tables.szilard_paid_measure_feedback_erase.ledger[0]` |
| `feedback_isothermal_expansion` | `0/1` | `1/1` | `0/1` | `.szilard_landauer_ledger_tables.szilard_paid_measure_feedback_erase.ledger[1]` |
| `erase_record` | `-1/1` | `0/1` | `1/1` | `.szilard_landauer_ledger_tables.szilard_paid_measure_feedback_erase.ledger[2]` |

Committed Landauer exclusions:

- `.szilard_landauer_ledger_tables.szilard_unpaid_erasure_variant`
  - `expected`: `unsat`
  - `derived.paid_erasure_ln2_coeff.string`: `0/1`
  - `derived.required_erasure_ln2_coeff.string`: `1/1`
  - `z3.status`: `unsat`
  - `cvc5.status`: `unsat`
- `.szilard_landauer_ledger_tables.below_landauer_half_paid`
  - `expected`: `unsat`
  - `derived.paid_erasure_ln2_coeff.string`: `1/2`
  - `derived.required_erasure_ln2_coeff.string`: `1/1`
  - `z3.status`: `unsat`
  - `cvc5.status`: `unsat`

Typed entropy convention in ledger v1:

- JSON path: `.typed_entropy`
- `conversion`: `1 bit * ln(2) = ln(2) nats`
- `units_policy`: bit counts are converted to nats before ledger rows are compared
- `landauer_one_bit_cost`: `k*T*ln(2)`

## Basin column: committed RETURN rows and phase mechanics

Primary result path:

- `system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json`
- `classification`: `scratch_diagnostic`
- `claim_ceiling`: `basin_dof_readout_rows_only`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`
- `result_summary.classification_counts`: `{"RETURN": 3, "BOUNDARY": 6}`

The RETURN rows are:

| RETURN DoF | dof_family | generators | phase/return fields | sample merge candidate | full graph candidate |
|---|---|---|---|---:|---:|
| `G0` | `generator_family` | `Se_Funnel_L`, `Ni_Pit_L`, `Ni_Source_R`, `Ne_Spiral_R`, `D_z`, `R_x` | `.dof_classification_table[]` where `dof_id=="G0"`: `returned_to_prior_terminal_class=true`, `terminal_class_cells=[[16]]`, `terminal_class_count=1`, `state_count=33`, `scrambling_found=false` | 9 distinct sampled `perturbed_cell` values return to `16` | 33 if the single-terminal 33-state graph is accepted as the merge carrier |
| `G2` | `generator_family` | `Ne_Spiral_R`, `Ne_Vortex_L`, `Ni_Pit_L`, `Ni_Source_R`, `Se_Cannon_R`, `Se_Funnel_L`, `Si_Citadel_R`, `Si_Hill_L`, `D_x`, `D_z`, `R_x`, `R_z` | same fields, `dof_id=="G2"` | 9 distinct sampled `perturbed_cell` values return to `16` | 33 candidate |
| `stage_shift_Rx_to_Rz` | `stage_operator_direction` | `Se_Funnel_L`, `Ni_Pit_L`, `Ni_Source_R`, `Ne_Spiral_R`, `D_z`, `R_z` | same fields, `dof_id=="stage_shift_Rx_to_Rz"` | 9 distinct sampled `perturbed_cell` values return to `16` | 33 candidate |

Computed sample merge details:

- `G0` sample unique perturbed cells: `[0,2,3,5,15,16,17,30,31]`; sample terminal cells: `[16]`
- `G2` sample unique perturbed cells: `[0,3,7,11,15,16,17,21,31]`; sample terminal cells: `[16]`
- `stage_shift_Rx_to_Rz` sample unique perturbed cells: `[0,2,3,5,15,16,17,30,31]`; sample terminal cells: `[16]`

Landauer-floor `m` boundary:

- The conservative sampled value available directly from committed `trajectory_rows` is `m_sample=9` for each RETURN row above.
- The cheap full-graph candidate is `m_full_candidate=33`, because each RETURN row has `state_count=33`, `terminal_class_count=1`, and `terminal_class_cells=[[16]]`.
- The next packet must recompute/emit the chosen `m` from the committed transition graph, not silently choose between sampled and full-carrier readings.

Phase mechanics in source:

- Perturb phase: `basin_dof_perturb_and_read_v0_common.py#perturb_cell(seed, size, graph, generator_names)`
  - applies `size` generator steps, preferring the corresponding `generator_names[step % len(generator_names)]`.
- Relax/read phase: `basin_dof_perturb_and_read_v0_common.py#shortest_terminal_path(start, graph)`
  - follows shortest path to a terminal class in the finite graph.
- Cycle sample row builder: `trajectory_rows(...)`
  - stores `seed_cell`, `perturbation_size`, `perturbed_cell`, `trajectory`, `trajectory_length`, `terminal_cell`, `terminal_class_id`, and `axis0_reconverged_for_sample`.
- RETURN predicate: `classify_dof(...)`
  - `returned = len(terms) == 1 and terms[0] == prior_terminal_cells`
  - `classification="RETURN"` only when `returned` and all sampled axis0 readouts reconverge.

Honest basin caveat:

- The committed audit caveat remains binding: `scrambling_found=false` is partly vacuous because readout is sampled at terminal cell `16`. Do not cite this as discovered absence of scrambling.
- The Axis-0 readout is formula-relative to the committed `discrete_axis0_field_v0` candidate (`axis0_readout_rebuild.commit_hint=5d330b427`).

## Typed-entropy machinery available for the basin packet

`manifold_entropy_ledger_v0` supplies typed entropy conventions, not a basin-cycle ledger yet:

- result: `system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json`
- `ledger.log_base`: `e`
- `entropy_type_table` includes:
  - `differential` / measure layer / Riemannian or induced area measure
  - `mixed differential plus discrete Shannon` / conditioning bands/unions
  - `von_Neumann` / carrier layer
  - `lattice/counting` / terrain row restrictions
- `ledger.conditioning_deltas.lens_quotient.drop_exact`: `log(4)`
- `ledger.conditioning_deltas.terrain_restriction.drop_exact`: `log(5/2)`
- `allowed_claims`: exact entropy rows under pinned conventions, conditioning deltas, carrier vN anchors, counting entropy for committed terrain row restriction
- `blocked_claims`: formal admission, canonical manifold entropy theorem, physics or bridge claim, recomputed carrier ladder entropy values

`z4_syndrome_record_v0` supplies the state-plus-record accounting convention:

- result: `system_v6/sims/z4_syndrome_record_v0/results/z4_syndrome_record_v0_envelope_results.json`
- `typed_entropy_discipline.log_base`: `e`
- `typed_entropy_discipline.all_rows_label`: `finite_counting_entropy_nats`
- `typed_entropy_discipline.product_bookkeeping_convention`: state quotient loss and retained finite syndrome record are compared within the same finite representative table
- `typed_entropy_discipline.cross_type_sum`: `false`
- `.regimes.positive`: full record, `state_loss_without_record_nats=1.3862943611198906`, `record_retained_nats=1.3862943611198906`, `computed_defect_nats=0.0`
- `.regimes.negative_erased_record`: erased record, `state_loss_without_record_nats=1.3862943611198906`, `record_retained_nats=0.0`, `computed_defect_nats=1.3862943611198906`
- `.regimes.negative_partial_record`: partial one-bit record, `computed_defect_nats=0.6931471805599453`
- `.reconstruction.with_quotient_and_syndrome.*.bit_exact_roundtrip=true`
- `.reconstruction.quotient_alone.*.computed_ambiguity=4`, `unique_reconstruction_possible=false`

Implication for the build card:

- A basin cycle ledger can use finite counting entropy in nats for merge floors and record retention, but the state-plus-record object must be constructed for the basin RETURN carrier. The Z4 packet is a convention and example, not a substitute for the basin record.

## Two loop forms and correspondence rows

Dual-stack probe:

- result: `system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json`
- `headline.headline_loop`: `section_15_literal_inductive_loop`
- `headline.literal_loop_g_DI_trace_norm`: `1.267611676635775`
- `headline.Type1_vs_Type2_trace_norm`: `1.4761370271087597`
- `headline.ax6_order_gap_U_E_trace_norm`: `0.049559683493157806`
- `smt_verdicts.z3/cvc5/julia_z3`: `unsat`
- `smt_verdicts.commuting_control_z3/cvc5/julia_z3`: `sat`
- `controls.commuting_control.commuting_control_delta_trace_norm`: `0.0`
- `szilard_ledger_summary.information_gained_nats`: `0.8329910613993748`
- `szilard_ledger_summary.landauer_reset_cost`: `0.10150905441283588`
- `szilard_ledger_summary.landauer_margin_W_minus_reset_cost`: `0.04493755499389039`
- `claim_ceiling`: finite-map dual-stack Carnot/Szilard Hopf-Weyl witness probe only; no engine, M(C), Axis0, bridge, or admission claim

S6 explicit D/I realization:

- result: `system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`
- `loop_order_gap.Phi_D`: `U @ E @ U @ E on Bloch vectors`
- `loop_order_gap.Phi_I`: `E @ U @ E @ U on Bloch vectors`
- `loop_order_gap.U.source`: `S5 Ne_Vortex_L exported A,b`
- `loop_order_gap.E.source`: `S5 Si_Hill_L exported A,b`
- `loop_order_gap.shared_carrier`: `density/Bloch carrier because E=Si_Hill_L is nonunitary dephasing`
- `loop_order_gap.max_g_DI_trace_norm`: `0.36341316691657366`
- `loop_order_gap.controls.commuting_erased_control.pass`: `true`
- `loop_order_gap.controls.commuting_erased_control.max_g`: `5.238750013840908E-17`
- `loop_order_gap.controls.carrier_mismatch_control.expected_failure_observed`: `true`
- `pin_spec` includes `Phi_D=U_E_U_E|Phi_I=E_U_E_U|U=Ne_Vortex_L_flow_t1|E=Si_Hill_L_flow_t1|carrier=density_bloch`

Ring floor:

- result: `system_v6/sims/ring_checkerboard_automaton_v0/results/ring_checkerboard_automaton_v0_envelope_results.json`
- `phase_test.alternating_order.discipline`: `alternating`
- `phase_test.alternating_order.order_name`: `deductive`
- `phase_test.alternating_signature.period_histogram`: `{"2":576}`
- `phase_test.alternating_signature.scc_count`: `464`
- `phase_test.alternating_signature.terminal_class_count`: `112`
- `phase_test.paired_order.discipline`: `paired`
- `phase_test.paired_order.order_name`: `inductive`
- `phase_test.paired_signature.period_histogram`: `{"4":576}`
- `phase_test.paired_signature.scc_count`: `240`
- `phase_test.paired_signature.terminal_class_count`: `112`
- `phase_test.terminal_structure_distinguishable`: `true`
- `phase_test.orbit_structure_distinguishable`: `true`
- `nesting_comparison.terminal_structure_changed`: `true`
- `disallowed_claims`: QCA index, quantum state/QCA, Axis0 closure, canonical support, manifold admission, 64-state engine placement, physics/cosmology/consciousness/world-engine claims

Nested-ratchet support:

- receipt: `system_v6/receipts/nested_ratchet_support/nr_fresh_audit_verdict.md`
- contributes continuity anchors for typed information and order sensitivity, not a direct Carnot/Szilard stroke map
- recomputed rung values: `S(A|B)` carrier row goes `0`, `-0.36207321415030524`, `-0.67863240236859246` in natural logs; separable control flips positive
- order sensitivity: adjacent carrier channel gaps positive; commuting-control gaps near zero

## Legality anchors

Fence v0 (`e10273983`):

- result: `system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- `.classical_fence.computed.eta_C.string`: `1/2`
- `.classical_fence.computed.landauer_min_erasure_cost.exact`: `ln(2)`
- `.classical_fence.computed.typed_entropy_conversion.conversion`: `1 bit * ln(2) = ln(2) nats`
- admitted rows:
  - `.classical_fence.admitted_rows.carnot_equality_boundary.status`: `sat`
  - `.classical_fence.admitted_rows.sub_carnot_eta_1_4.status`: `sat`
  - `.classical_fence.admitted_rows.paid_erasure_one_bit.status`: `sat`
- excluded rows:
  - `.classical_fence.excluded_rows.super_carnot_eta_3_4.status`: `unsat`
  - `.classical_fence.excluded_rows.single_bath_positive_work.status`: `unsat`
  - `.classical_fence.excluded_rows.below_landauer_half_paid.status`: `unsat`
  - `.classical_fence.excluded_rows.unpaid_erasure_surplus.status`: `unsat`
- `.controls.shuffled_ledger_order.*`: normal order `measure,feedback,erase` is `sat`; shuffled `feedback,measure,erase` is `unsat`
- `purpose_boundary`: classical fence/exclusion evidence only; no physics admission, bridge claim, or nonclassical promotion

Ledger v1 (`d79d71a0d`):

- binds the same legality with ledger-derived rows:
  - super-Carnot `eta=3/4` is `unsat` because `entropy_production=-1/2`
  - unpaid and half-paid erasure variants are `unsat` against `paid_erasure_cost_gte_required_landauer_cost`
  - broken entropy fence flips super-Carnot to `sat`, preserving the witness that the fence is load-bearing
  - `.controls.n01_order.*`: `measure,feedback,erase` is `sat`; `feedback,measure,erase` is `unsat`

How these bind basin-cycle quantities:

- Any basin cycle that claims work-like extraction from relaxation must ledger a typed dissipation/record account at least as strong as the Landauer excluded rows: unpaid merge erasure and half-paid merge erasure are illegal by analogy only after `m` and record-retention are computed on the basin carrier.
- Any basin cycle that claims a reversible/boundary case must close the ledger under a state-plus-record convention, analogous to `entropy_production=0/1` and paid `net_after_paid_erasure_ln2_coeff=0/1`.
- Any basin cycle that shuffles readout/order/reset phases must pass an N01-style order control; the committed fence says measurement/readout before feedback/reset is load-bearing.

## Computed structure map

This is the current map for the next build. "Basin carrier field" names the committed field available now; it does not mean the basin packet has already computed the cycle ledger.

| Shared mechanic | Carnot row | Szilard row | Basin cycle phase | Basin carrier field now | Boundary |
|---|---|---|---|---|---|
| Open/contact with reservoir or distinguishable branch | `hot_isothermal_expansion`: `q_hot=2/1`, `work_out=3/2` | `measure_record_one_bit`: records `1/1` ln2 bit-equivalent | perturb/readout creates a distinguishable perturbed state | `trajectory_rows[].perturbation_size`, `perturbed_cell`; RETURN rows list sampled perturbed cells | Basin has no heat bath variable yet; this is typed-state perturbation, not thermodynamic heat. |
| Work-producing expansion / feedback | Carnot hot stroke contributes positive work; total row has `work_out_total=1/1` | `feedback_isothermal_expansion`: `work_out_ln2_coeff=1/1` | relax toward terminal class after perturbation | `shortest_terminal_path(perturbed, graph)` and `trajectory_rows[].trajectory` | Basin relax is not yet a work extractor; next packet must define the ledger quantity. |
| Isolated stroke / no heat contact | `adiabatic_expansion`: `q_hot=0/1`, `q_cold=0/1`, `work_out=1/2`; `adiabatic_compression`: all heat zero | no direct Szilard phase; order legality instead appears in N01 measurement-before-feedback | internal graph travel with no new record, if the future ledger defines it | current basin result has graph trajectory only; no explicit isolated/bath-gated basin field | Honest gap: no basin counterpart to adiabatic isolation is committed. |
| Cold rejection / cost payment | `cold_isothermal_compression`: `q_cold=-1/1`, `work_out=-1/1` | `erase_record`: `nats_recorded_ln2_coeff=-1/1`, `erasure_paid_ln2_coeff=1/1` | reset/record erasure for merged perturb states | available convention: Z4 `.regimes.negative_erased_record` and `.regimes.positive`; basin RETURN rows do not yet construct a record object | Must be built in `carnot_szilard_basin_cycle_v0`; do not reuse Z4 record as basin record. |
| Closed cycle ledger | reversible row has `energy_residual=0/1`, `entropy_production=0/1`, `eta=eta_C=1/2` | paid row has net after erasure `0/1` | perturb -> relax -> return on `G0`, `G2`, `stage_shift_Rx_to_Rz` | `returned_to_prior_terminal_class=true`, `terminal_class_cells=[[16]]`, `axis0_readout_reconverged=true` | Spatial/readout return is not ledger closure. Next packet must compute conservation account. |
| Illegal free lunch | `candidate_super_carnot_cycle`: `eta=3/4`, `entropy_production=-1/2`, `unsat` | unpaid/half-paid erasure rows `unsat` | basin cycle beating `ln(m)` floor | candidate `m_sample=9`; `m_full_candidate=33`; no floor row committed yet | This is exactly the next falsifier; no claim until floor arithmetic is committed. |
| Order legality | Carnot has isothermal/adiabatic stroke gating | N01: `measure,feedback,erase` sat; shuffled unsat | perturb/readout/reset order and D/I loop order | basin controls include `controls.shuffled_order_N01.classification=BOUNDARY`; S6 D/I and ring alternating/paired rows give order surfaces | Axis-1 bath-gating legality is doctrine/work-order context, not yet a basin-cycle field. |
| Two loop forms | doctrine maps D to `U E U E` / Carnot-like alternation | doctrine maps I to `E U E U` / Szilard-like block | ring alternating vs paired; S6 `Phi_D` vs `Phi_I` | S6 `.loop_order_gap.Phi_D/Phi_I`; ring `.phase_test.alternating_signature` and `.paired_signature` | Dual-stack probe remains scratch/finite-map; ring floor is classical support, not QCA/engine placement. |

## Honest boundaries

Mechanics not yet earned on the basin side:

1. Heat/work variables on the basin carrier. Current basin rows have graph perturbation, relaxation, terminal return, and Axis-0 readout fields; they do not have `q_hot`, `q_cold`, or `work_out`.
2. A basin record object. Z4 proves a state-plus-record convention on its own packet-local carrier; the basin packet must construct its own record/erasure rows.
3. A committed basin-Landauer floor. This receipt computes candidate `m` values from committed rows but does not test `dissipation >= ln(m)`.
4. A basin analogue of adiabatic isolation/bath-gating. Current fields do not name bath contact or no-contact strokes.
5. A closed basin ledger. `returned_to_prior_terminal_class=true` is spatial/readout return only; conservation closure must be computed.
6. Physics, bridge, M(C), Axis0 admission, engine placement, QCA/index, or manifold admission. Every cited packet keeps `promotion_allowed=false` or explicit disallowed-claim fences.

## Draft build-card skeleton: `carnot_szilard_basin_cycle_v0`

Packet objective:

- Build one bounded scratch packet that computes the per-cycle typed ledger on the committed basin RETURN rows and emits the structure-map table as output, not prose.

Inputs:

- RETURN rows from `basin_dof_perturb_and_read_v0`:
  - `G0`
  - `G2`
  - `stage_shift_Rx_to_Rz`
- Entropy conventions:
  - `manifold_entropy_ledger_v0` for typed entropy table and natural-log counting discipline.
  - `z4_syndrome_record_v0` for state-plus-record conservation convention, co-cited as convention only.
- Classical legality anchors:
  - `carnot_szilard_landauer_fence_v0`
  - `carnot_szilard_landauer_ledger_v1`
- Loop/order anchors:
  - `geo_s6_stacked_flows_hopf_v0.loop_order_gap`
  - `ring_checkerboard_automaton_v0.phase_test`
  - `dual_stack_carnot_szilard_hopf_weyl_probe` as scratch continuity, with its ceiling preserved.

Required outputs:

1. `basin_cycle_rows`
   - one row per RETURN DoF
   - fields: `dof_id`, `seed_set`, `perturbation_sizes`, `perturbed_state_count_m`, `m_source` (`sample` or `full_graph`), `terminal_class_cells`, `record_retained_nats`, `state_loss_nats`, `dissipation_or_reset_cost_nats`, `ledger_defect_nats`, `closed_under_state_plus_record`
2. `basin_landauer_floor`
   - computes `floor_nats = ln(m)` for each row
   - compares reset/dissipation account against `floor_nats`
   - status: `pass`, `fail_beats_floor`, or `inconclusive_unledgered_record`
3. `ledger_closure_account`
   - separate code paths for state loss and record retained, mirroring Z4 discipline
   - explicit `cross_type_sum=false` unless a product convention is constructed
4. `structure_map_table`
   - columns: Carnot stroke, Szilard phase, basin phase, committed source field, computed ledger field, boundary
   - must include honest gaps from this receipt
5. `legality_anchor_report`
   - cites the exact fence rows that would be violated by unpaid/half-paid basin erasure or super-Carnot-style negative entropy production

Controls:

- `record_erased_cycle`: erase the basin record; must show the floor defect or fail the connection.
- `over_recorded_cycle`: retain excess record; must charge reset/record cost instead of hiding it.
- `commuting_control_D_I`: use a commuting or order-erased D/I control; S6-style gap must collapse near zero.
- `shuffled_order_N01`: shuffle readout/feedback/reset order; must fail or become `BOUNDARY`.
- `classical_baseline_rows_labeled`: all Carnot/Szilard legality rows remain `classical_baseline`, never nonclassical evidence.

Fences:

- `classification`: `scratch_diagnostic`
- `promotion_allowed`: `false`
- `formal_admission_allowed`: `false`
- no physics admission
- no bridge claim
- no Axis0 admission
- no M(C) admission
- no QCA/index claim
- no engine placement claim
- no manifold admission

Stop/kill conditions:

- If any RETURN row beats `ln(m)` without an explicit retained-record charge, the connection is killed for that row or the record model is incomplete.
- If ledger closure requires summing unlike entropy types without a constructed product convention, classify as `inconclusive_type_mismatch`.
- If the packet cannot decide `m_sample` versus `m_full_graph`, emit both and mark the floor test blocked on `m_scope`.
- If the commuting/order-erased control does not collapse, do not cite D/I order as load-bearing.
- If a basin record object is not constructed, do not claim Landauer closure.

## Commands / checks used for this mapping receipt

Fresh commands included:

- `git show --name-status --oneline --stat --find-renames d79d71a0d`
- `git show --name-status --oneline --stat --find-renames f41d4c311`
- `git show --name-status --oneline --stat --find-renames e10273983`
- `git show --name-status --oneline --stat --find-renames bd7a54080`
- `git show --name-status --oneline --stat --find-renames fe06d49bd`
- `jq` reads over the result paths listed above
- `rg` for `Phi_D`, `Phi_I`, `UEUE`, `EUEU`, `dual_stack`, `ring`, `alternating`, and `paired`
- direct source reads of `basin_dof_perturb_and_read_v0_common.py` phase functions

No validators were rerun for this receipt. This is committed-row mapping archaeology plus cheap candidate `m` computation from committed result JSON fields.
