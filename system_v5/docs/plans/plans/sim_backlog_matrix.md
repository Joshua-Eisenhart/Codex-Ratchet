# Sim Backlog Matrix

Status: ADMISSION POOL (not an ordered pipeline)

---

## What this file is

This file is an **admission pool** of candidate sims. Reading top to bottom carries no admission force. The rows are unordered with respect to execution; any ordering in the text is historical bookkeeping.

A sim runs iff its stage gate is admitted from session-visible evidence. Position in this file does not admit a sim. Running row N does not admit row N+1.

## What this file is NOT

- This file is not a queue in the FIFO sense.
- "Next" has no meaning in this file.
- A sim completing does not release its successor; successors have no defined relationship to predecessors here.
- Adjacency in text is not adjacency in execution.

## Admission form

For any candidate sim considered for execution:

```
Candidate sim: <path>
Stage gate required: <step N from 06_coupling_program_order.md>
Gate criterion: <exact admission criterion for step N>
Gate evidence from this session: <result file path OR "no evidence cited">
Admission decision: admitted | excluded
```

If the gate evidence is "no evidence cited", the sim is excluded from execution regardless of where it sits in this file.

## Skip-ahead refusal

**The primary failure this file's structure refuses is skip-ahead:** treating a sim's presence in the pool as authorization to run it, or treating a completed sim as authorization for its textual neighbor.

Skip-ahead in pool operations surfaces as:
- "The previous sim ran, so the next one is admitted" — collapsed; adjacency is not admission
- "Most of the pool has run, so the remaining sims are close to admission" — collapsed; aggregate pool state is not per-gate admission
- "Broad higher-stage promotion is reasonable since local exploration is strong" — collapsed; narrative substitution for gate obedience

Intercept shape (per `28_bounded_work.md`): cite the stage gate and the session-visible result file. If the citation fails, the sim is excluded. Do not smooth a gate failure with pool position.

## Bounded-work reference

Every sim execution is wrapped in a bounded-work block from `~/wiki/harness/28_bounded_work.md`. The pool entries below are candidates; the work unit is declared separately at execution time with explicit Scope, Out-of-scope, and Bound exit condition.

---

Goal: make the current engine-construction queue explicit across the primary lanes without widening scope or collapsing truth labels. The sims in this queue are build/validation instruments for lego completion and engine assembly readiness, not the end goal.

Authority surfaces used:
- `docs/07_model_math_geometry_sim_plan.md`
- `docs/08_aligned_sim_backlog_and_build_order.md`
- `docs/16_lego_build_catalog.md`
- `docs/17_actual_lego_registry.md`
- `docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `docs/TOOLING_STATUS.md`
- `docs/plans/plans/2026-04-18-tool-stage-plan.md`

## Queue policy
- Build actual engines through controlled lego construction; do not treat sim count or sim novelty as progress by itself.
- Geometry-before-axis.
- One primary lane plus one maintenance lane per batch by default.
- Tool sims stay active.
- Tool-integration sims stay active.
- Lego rows stay active, one bounded row at a time, across `17_actual_lego_registry.md`.
- Bounded pairwise/coexistence exploration may run off the strongest already-simed local parents.
- Do not treat exploratory coupling as permission for broad higher-stage promotion.
- Flux stays derived and gated behind lower differential/chirality work.
- Each queued batch should advance one of: lego completion, lego validation, assembly prerequisite clarity, or engine-readiness gating.

Interpretation rule:
- successor language inside this file is bookkeeping, not automatic permission
- bounded exploratory successors may be used when the parent locals are already strong and the claim stays narrow
- broad higher-stage promotion still requires stronger parent coverage and explicit review

## Fresh bounded exploratory coupling executions (2026-04-18)

- `sim_gstructure_compatibility_coupling.py`
  - reran cleanly
  - keep as the strongest current bounded coupling exploration off `g_structure_tower` + Hopf locals
- `sim_operator_geometry_compatibility.py`
  - reran cleanly as `supporting`
  - repo-local cache env fix restored real `clifford` execution; keep as bounded operator/geometry exploration only
- `sim_constraint_shells_binding_crosscheck.py`
  - reran cleanly as `supporting`
  - keep as bounded shell-binding exploration, not broader promotion
- `sim_xgi_indirect_pathway.py`
  - reran cleanly
  - keep as bounded graph/hypergraph exploration only
- `sim_compound_operator_geometry.py`
  - reran cleanly as `supporting`
  - repo-local cache env fix restored real `clifford` execution; remains exploration-only

Rule:
- these reruns prove the exploratory loop is real now
- they do not authorize broad pairwise/coexistence/bridge/axis/engine promotion

## Fresh local / tool-bearing reruns (2026-04-18)

- direct local winners reran cleanly as `canonical`:
  - `sim_graph_shell_geometry.py`
  - `sim_reduced_state_object.py`
  - `sim_negativity_measure.py`
  - `sim_concurrence_measure.py`
  - `sim_local_operator_action.py`
  - `sim_persistence_geometry.py`
- direct tool-bearing locals reran cleanly as `canonical`:
  - `sim_e3nn_hopf_spinor_equivariance.py`
  - `sim_toponetx_state_class_binding.py`
  - `sim_lego_constraint_admissibility_fence_z3.py`
  - `sim_torch_channel_taxonomy.py`
- additional bounded local/tool-base legos reran cleanly as `canonical`:
  - `sim_lego_adiabatic_theorem.py`
  - `sim_lego_entropy_family_crosscheck.py`
  - `sim_lego_povm_measurement.py`
  - `sim_lego_stinespring_complementary.py`
  - `sim_lego_entanglement_distillation.py`
  - `sim_pure_lego_geodesic_exponential_map.py`
  - `sim_lego_coherent_info_advanced.py`
  - `sim_lego_toric_code.py`
  - `sim_lego_pauli_algebra.py`
  - `sim_lego_unitary_generators.py`
  - `sim_lego_dirac_gamma.py`
  - `sim_lego_gksl_kossakowski.py`
  - `sim_lego_clifford_commutator_algebra.py`
  - `sim_lego_fiber_bundles.py`
  - `sim_lego_spectral_triple_carrier.py`
  - `sim_lego_spectral_triple_heat_kernel.py`
  - `sim_lego_assoc_bundle_load_bearing.py`
  - `sim_lego_lindblad_dissipator.py`
  - `sim_lego_lindblad_spectral.py`
  - `sim_pure_lego_levi_civita_connection.py`
  - `sim_pure_geometry_hopf_tori.py`
  - `sim_pure_lego_hopf_tori_base.py`
  - `sim_foundation_hopf_torus_geomstats_clifford.py`
  - `sim_pure_lego_berry_phase_u1_abelian.py`
  - `sim_pure_lego_wilczek_zee_holonomy.py`
  - `sim_pure_lego_adiabatic_berry_dynamics.py`
  - `sim_lego_su2_representations.py`
  - `sim_lego_uhlmann_phase.py`
- bounded local/foundation follow-ons reran cleanly:
  - `sim_integration_gudhi_gtower_filtration.py` as `classical_baseline`
  - `sim_foundation_shell_graph_topology.py` as `foundation_lego`
  - `sim_pure_lego_state_discrimination.py` as `classical_baseline`
  - `sim_pure_lego_no_go_theorems.py` as `classical_baseline`
  - `sim_probe_object.py` as `canonical`
  - `sim_probe_identity_preservation.py` as `canonical`
  - `sim_distinguishability_relation.py` as `canonical`
  - `sim_carrier_probe_support.py` as `canonical`
  - `sim_helstrom_guess_bound.py` as `canonical`
  - `sim_positivity_constraint.py` as `canonical`
- `sim_partial_trace_audit.py` produced a useful estate-wide correctness audit, but its named live-bug claims now need direct per-file confirmation before using it to invalidate owner surfaces

Rule:
- these reruns strengthen the local and tool-stage substrate
- they do not by themselves authorize broad higher-stage promotion

## Lane A — Classical engine lane

Purpose in the overall build: construct and validate the classical/QIT baseline legos that will later support actual engine building. These sims are not the product; they are controlled construction steps toward engine behavior that can be assembled honestly.

| Priority | Batch | Objective | Current state | Next bounded move | Notes |
|---|---|---|---|---|---|
| A1 | classical-baseline-audit | Re-audit Carnot/Szilard baseline files against current process rules | exists; mixed process depth | build truth audit rows for core Carnot/Szilard result files | keep baseline lane separate from geometry proof |
| A2 | carnot-forward-reverse-packet | Explicit forward + reverse Carnot loops with staged mechanics | partial estate exists: `qit_carnot_two_bath_cycle_results.json`, `qit_carnot_finite_time_companion_results.json`, `qit_carnot_hold_policy_companion_results.json` | identify best current forward/reverse anchors and rerun one bounded packet | must stay classical/QIT-first; do not promote above `exists`/`runs` without fresh rerun + process re-audit |
| A3 | szilard-forward-reverse-packet | Explicit forward + reverse Szilard/Landauer loops with substep mechanics | partial estate exists: `qit_szilard_landauer_cycle_results.json`, `qit_szilard_record_companion_results.json`, `qit_szilard_substep_companion_results.json`, `qit_szilard_bidirectional_protocol_results.json` | identify best current forward/reverse anchors and rerun one bounded packet | include wrong-order/reset negatives; do not promote above current truth-audit labels without fresh rerun + process re-audit |
| A4 | engine-bridge-readiness | Extract which engine mechanics transfer cleanly to QIT engine lane | blocked on geometry/chirality packet quality | defer until geometry spine packets are cleaner | topology/admissibility differences must stay explicit |

## Lane B — Geometry-manifold lane (the spine)

Purpose in the overall build: construct the geometry/chirality/operator legos that the eventual engines depend on. This lane is the main build spine because engine assembly should happen only after these lower geometric parts are explicit, validated, and stackable.

### Phase B1 — root/carrier admission

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B1 | `constraint_probe_admissibility` | needs deeper lego work; lego_stage_incomplete | clean direct admission probe and proof pressure row | z3, cvc5 |
| B2 | `carrier_admission_density_matrix` | partial; lego_stage_only | truth-audit and rerun strongest carrier anchor | pytorch, sympy |
| B2a | `g_structure_tower` | passes local rerun; classical_baseline anchor with a separate bounded canonical follow-on | keep `sim_g_structure_tower.py` as the bounded support-manifold admissibility baseline anchor; keep `sim_gstructure_compatibility_coupling.py` as the local canonical follow-on for the S³→S² Hopf-coupling claim under the tower; the baseline-vs-canonical comparison surface is now explicit on the wiki `g-structure-tower` page, so the next bounded move is a fuller tool-native tower-wide counterpart before widening into broader support claims | z3, sympy |

### Phase B2 — same-carrier geometry packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B3 | `geometry_crosschecks_same_carrier` | covered; lego_stage_only | keep as main geometry packet anchor | geomstats, clifford, pytorch |
| B4 | `hopf_map_s3_to_s2` | canonical by process | keep `sim_density_hopf_geometry.py` as the explicit local Hopf-map anchor; advance fiber-equivalence next rather than re-hiding projection evidence under generic Hopf geometry | pytorch, sympy |
| B5 | `hopf_fiber_equivalence` | canonical by process | keep `sim_hopf_fiber_equivalence.py` as the direct fiber-equivalence anchor; advance `nested_torus_geometry` next rather than reworking this packet again | pytorch, sympy, z3 |
| B6 | `hopf_connection_form` / `holonomy_geometry` / `transport_geometry` | canonical by process | keep `sim_torch_hopf_connection.py` as the bounded connection/holonomy/transport anchor; advance `hopf_fiber_equivalence` next instead of reworking this packet again | pytorch, e3nn |
| B7 | `nested_torus_geometry` | canonical by process | keep `sim_pure_geometry_hopf_tori.py` as the direct nested-torus anchor; advance same-carrier geometry schema/process hardening or separate graph/topology successors next rather than re-auditing this packet again | clifford, toponetx |
| B7c | `fiber_loop_law` | canonical by process (2026-04-12) | keep `sim_fiber_loop_law.py` as the direct fiber-loop law anchor; pytorch is load_bearing for density outer-product cross-check; sympy is load_bearing for symbolic phase-cancellation proof (e^{iα}ψ outer-product returns same rho); z3 was tried with explicit non-empty reason (not load_bearing — continuous symbolic claim proven by sympy); z3 empty-reason process defect found and resolved on 2026-04-12 4h-run; fresh rerun at 2026-04-12T14:06:36 confirms 8/8 all_pass with complete manifest; advance pairwise coupling tests after base_loop_law and berry_holonomy have companions | pytorch, sympy |
| B7a | `base_loop_law` | canonical by process (2026-04-12) | keep `sim_base_loop_law.py` as the direct base-loop anchor; pytorch is load_bearing for density tensor computation; sympy is load_bearing for symbolic closure proof (upgraded from supportive on 2026-04-12 4h-run — sympy simplification is a direct gate on the symbolic_closure_proof test); advance pairwise coupling with fiber_loop_law next | pytorch, sympy |
| B7b | `berry_holonomy` | canonical by process (2026-04-12) | keep `sim_pure_lego_berry_curvature_stokes.py` as the direct abelian Berry holonomy anchor (Stokes theorem on CP1); pytorch load_bearing, sympy load_bearing (upgraded from supportive on 2026-04-12 4h-run — sympy F=dA derivation with diff_check==0 is a direct gate on P5_sympy_stokes); advance to non-abelian holonomy (Wilczek-Zee) or pairwise coupling next | pytorch, sympy |
| B8 | `weyl_chirality_pair` | canonical by process | keep `sim_weyl_spinor_hopf.py` as the direct bounded chirality-pair anchor; advance the Pauli/local-operator successor packet next rather than re-auditing this packet again | clifford, sympy |
| B9 | `chiral_density_bookkeeping` | canonical by process | keep `sim_chiral_density_bookkeeping.py` as the direct bookkeeping anchor and advance the explicit Pauli/local-operator successor packet next rather than re-auditing rho_L / rho_R bookkeeping | pytorch, sympy, z3 |
| B10 | `pauli_generator_basis` + `left_right_asymmetry` | canonical by process | keep `sim_lego_pauli_algebra.py` as the direct Pauli-basis anchor and `sim_weyl_spinor_hopf.py` as the direct asymmetry anchor; advance `composition_order_noncommutation` next rather than re-auditing these local basis/asymmetry rows | clifford, sympy, z3 |

### Phase B3 — graph/topology geometry packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B11 | `graph_cell_complex_geometry` | covered; lego_stage_only | deepen shallow-tool usage on same-carrier geometry | pyg, toponetx, xgi |
| B12 | `state_class_binding_geometry` | canonical by process | keep `sim_toponetx_state_class_binding.py` as the direct local TopoNetX binding anchor; deepen separate graph/topology successors rather than re-auditing this packet again | toponetx |
| B13 | `cell_complex_geometry` | canonical by process | keep `sim_cell_complex_geometry.py` as the direct local TopoNetX anchor; deepen separate graph/topology successors rather than re-downgrading this packet | toponetx, gudhi |
| B14 | `persistence_geometry` | canonical by process | keep `sim_persistence_geometry.py` as the direct local persistence anchor; deepen separate graph/topology successors rather than re-auditing this bounded topology packet | gudhi |

### Phase B4 — operator/chirality/differential packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B15 | `operator_family_admission` | needs deeper lego work; lego_stage_incomplete | keep `sim_local_operator_action.py` as the clean primitive local-action anchor and deepen channel/commutator/Clifford successors next | clifford, sympy, z3 |
| B16 | `channel_cptp_map` family | canonical by process | keep `sim_pure_lego_channels_choi_lindblad.py` as the direct bounded local channel-admission anchor; advance separate channel-capacity / taxonomy / measurement successors next rather than re-auditing this packet again | z3, pytorch |
| B17 | `composition_order_noncommutation` | canonical by process | keep `sim_torch_channel_composition.py` as the direct local order-sensitivity anchor; deepen separate channel/commutator/Clifford successors next rather than re-auditing this packet again | z3, sympy, pytorch |
| B18 | `flux_candidate_family` | derived/open only | defer until transport + chirality + delta surfaces are real | differential/chirality packet first |

### Phase B5 — bipartite/correlation local packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B19 | `bipartite_structure_local` | covered; lego_stage_only | maintain as local witness layer below bridge | gudhi, pyg |
| B20 | `partial_trace_operator` / `reduced_state_object` | partial | separate these more explicitly in audits/docs | pytorch, sympy |
| B21 | `joint_density_matrix` / `correlation_tensor_object` | not_normalized_yet | create direct rows in maintenance surfaces | pytorch |

### Phase B6 — late/local entropy and bridge gates

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B22 | `entropy_family_crosschecks` | needs deeper lego work; blocked_on_lego | keep late and local; do not promote early | sympy, pytorch |
| B23 | `joint_cut_state_rho_ab` | covered | treat as late support object, not early target | bounded bridge discipline |
| B24 | `bridge_family_xi_*` | partial / not_normalized_yet | keep blocked behind lower packet quality | no early promotion |

## Lane C — Maintenance / control lane

Purpose in the overall build: keep the construction process honest, reproducible, and organized so lego completion and eventual engine assembly are governed by real prerequisites instead of ad hoc sim-running.

| Priority | Surface | Objective | Next bounded move |
|---|---|---|---|
| C1 | `sim_truth_audit.md` | explicit truth labels for key current files | build first audit table |
| C2 | `tool_integration_maintenance_matrix.md` | show which tools are deep vs shallow by lane | build matrix from tooling docs + legos |
| C3 | `controller_maintenance_checklist.md` | keep runs healthy and aligned | create pre/during/post run checklist |
| C4 | `on-demand-telegram-runner.md` | keep launch/heartbeat/closeout behavior aligned with controller ownership | link progress/health reporting to truth/maintenance closure |
| C5 | `16_lego_build_catalog.md` | keep grouped controller ledger current | patch when docs/results materially change states |
| C6 | `17_actual_lego_registry.md` | keep exhaustive lego registry current | patch when distinct math objects/results need explicit rows |
| C7 | wiki concept pages | keep current-docs-aligned summaries in sync | patch touched concept pages after material changes, but not as part of controller-only closure unless concept framing changed |

## Lane D — Tool-capability foundation / counterpart lane

Purpose in the overall build: explicitly learn what each nonclassical tool can and cannot do here under bounded conditions, then turn that learned capability into careful tool-native counterparts for later scientific sims. This lane is foundational, not side work.

Interpretation rule:
- the tool families named here are illustrative seed classes, not an exhaustive whitelist of all valid packets
- if a nearby bounded packet better teaches the same tool capability while staying in-lane, the controller may choose it

Required per-family shape whenever possible:
1. classical baseline / numpy reference
2. canonical tool-native counterpart
3. explicit comparison note describing what the tool adds

Coverage-lego rule:
- tool-stage work should prefer real bounded legos that exercise many tools honestly
- do not force one mega-sim that integrates everything
- do use a small set of real local legos as the coverage surface for the tool estate

| Priority | Tool-capability family | Objective | Current state | Next bounded move |
|---|---|---|---|---|
| D1 | proof/symbolic capability | make impossibility, cross-check, derivation, and synthesis roles explicit | partial but active | bounded z3 / cvc5 / sympy packets with baseline-vs-canonical comparison notes |
| D2 | graph-native capability | learn DAG, pairwise-graph, and hypergraph-native claim paths | partial but active | bounded rustworkx / PyG / XGI packets on one local object family |
| D3 | topology capability | learn cell-complex and persistence claim paths | partial but active | bounded TopoNetX / GUDHI packets with explicit local witness scope |
| D4 | geometry/equivariance capability | learn rotor/spinor, metric/geodesic, and equivariance claim paths | partial but active | bounded clifford / geomstats / e3nn packets on one same-carrier geometry family |
| D5 | baseline-vs-canonical comparison surface | keep the difference between numpy baselines and tool-native counterparts explicit | now strategically necessary | write or update explicit comparison notes whenever a pair exists |

### Immediate tool-stage batch (2026-04-18)

- capability:
  - `sim_rustworkx_capability.py`
  - `sim_geomstats_capability.py`
  - `sim_xgi_capability.py`
  - `sim_e3nn_capability.py`
- bounded integrations now verified 2026-04-18:
  - `sim_integration_networkx_rustworkx_crosscheck.py`
  - `sim_integration_geomstats_constraint_manifold.py`
  - `sim_integration_toponetx_gtower_chain_complex.py` as executed baseline/reference only; do not reuse it as the default next Tier A candidate because it already leans into tower-order semantics

Rule:
- keep this batch in Lane D
- do not reinterpret it as lego coupling progress

### Fresh follow-on tool-stage runs (2026-04-18)

- canonical proof/search/tool integrations:
  - `sim_integration_hypothesis_z3_property_guard.py`
  - `sim_integration_optuna_sympy_invariant_search.py`
  - `sim_integration_datasketch_pyg_lsh_graph.py`
  - `sim_integration_ribs_z3_constraint_archive.py`

Rule:
- keep these as tool-stage proof/search/graph packets
- do not reinterpret them as lego completion or as permission to widen into coupling work

### Coverage-lego tool-stage batch

- Hopf / same-carrier coverage:
  - `sim_toponetx_hopf_crosscheck.py`
  - `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`
  - `sim_foundation_hopf_torus_geomstats_clifford.py`
- G-tower local proof coverage:
  - `sim_gtower_reduction_obstruction_z3.py`

Rule:
- these are still tool-stage because the point is tool coverage on real bounded legos
- do not reinterpret them as permission to move to coupling

Fresh verified executions (2026-04-18):
- `sim_gtower_reduction_obstruction_z3.py`
- `sim_toponetx_hopf_crosscheck.py`
- `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`
- `sim_foundation_hopf_torus_geomstats_clifford.py`

## Recommended first execution batches

Interpret these as construction packets, not as a list of sims to run for their own sake.

### Batch 1
- B2 carrier-admission audit/rerun surface
- B3 same-carrier geometry anchor audit/rerun
- C1 truth audit
- C2 tool-integration maintenance matrix
- C3/C4 controller + Telegram linkage pass

### Batch 2
- B8/B9 Weyl + chiral bookkeeping packet audit/rerun
- B10 Pauli/left-right packet audit/rerun
- C5/C6 lego-ledger maintenance
- C7 wiki sync only if the bounded batch changed concept framing, not just controller state

### Batch 3
- B11/B13 graph/cell-complex geometry deepen pass
- B15 operator-family-admission cleanup
- C3/C4 controller maintenance closeout polish if run behavior changed

### Audit-driven batches (2026-04-18)

### Batch 4
- C1 canonical-conformance repair pass
- target the `63` canonical-labeled probes that fail the current packet rules
- output: survivor / demotion / process-repair split, not a blanket relabel
- use `system_v5/docs/plans/plans/2026-04-18-canonical-conformance-repair-queue.md` as the staged queue for demotion-first vs repair-first handling

### Batch 4b
- bounded exploratory coupling reruns off strong local parents
- current safe order:
  - `sim_gstructure_compatibility_coupling.py`
  - `sim_operator_geometry_compatibility.py`
  - `sim_constraint_shells_binding_crosscheck.py`
  - `sim_xgi_indirect_pathway.py`
  - `sim_compound_operator_geometry.py`
- output:
  - honest rerun state plus any runtime/process blockers
  - no broad promotion from these packets alone

### Batch 5
- B8/B11/B12/B19/B20 local winner normalization pass
- reflect the strongest direct local anchors that are currently under-represented in the ledgers:
  - direct Weyl local owner
  - graph/topology local owners
  - reduced-state / negativity local owners
- keep truth labels conservative unless fresh reruns justify stronger labels

### Batch 6
- pairwise / coexistence / bridge honesty pass
- audit higher-stage owner packets for prerequisite drift, substrate drift, and owner inflation
- keep only the sanctioned bounded successor packets as current parents for higher-stage work

### Batch 7
- Tier D rebuild pass
- replace toy boundary encodings with real lower-layer boundary packets
- require explicit anti-tautology pressure and real lower-layer object dependence

### Batch 8
- narrow classical/QIT re-audit pass
- one bounded Carnot family and one bounded Szilard family only
- goal: clean truth/status surface for the real baseline lane, not broad engine promotion

## Explicit non-queue items
Do not promote by default:
- axis work
- broad bridge closure claims
- entropy-first summaries
- unbounded maintenance autonomy
