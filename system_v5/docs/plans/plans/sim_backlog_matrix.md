# Sim Backlog Matrix

Status: PRIMARY LIVE QUEUE SURFACE

Goal: make the current engine-construction queue explicit across the primary lanes without widening scope or collapsing truth labels. The sims in this queue are build/validation instruments for lego completion and engine assembly readiness, not the end goal.

Authority surfaces used:
- `new docs/07_model_math_geometry_sim_plan.md`
- `new docs/08_aligned_sim_backlog_and_build_order.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `new docs/TOOLING_STATUS.md`

## Queue policy
- Build actual engines through controlled lego construction; do not treat sim count or sim novelty as progress by itself.
- Geometry-before-axis.
- One primary lane plus one maintenance lane per batch by default.
- Pairwise/coexistence only after local legos are real.
- Flux stays derived and gated behind lower differential/chirality work.
- Each queued batch should advance one of: lego completion, lego validation, assembly prerequisite clarity, or engine-readiness gating.

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
| B1 | `constraint_probe_admissibility` | needs deeper lego work; blocked_on_lego | clean direct admission probe and proof pressure row | z3, cvc5 |
| B2 | `carrier_admission_density_matrix` | partial; ready_now | truth-audit and rerun strongest carrier anchor | pytorch, sympy |
| B2a | `g_structure_tower` | passes local rerun; classical_baseline anchor with a separate bounded canonical follow-on | keep `sim_g_structure_tower.py` as the bounded support-manifold admissibility baseline anchor; keep `sim_gstructure_compatibility_coupling.py` as the local canonical follow-on for the S³→S² Hopf-coupling claim under the tower; the baseline-vs-canonical comparison surface is now explicit on the wiki `g-structure-tower` page, so the next bounded move is a fuller tool-native tower-wide counterpart before widening into broader support claims | z3, sympy |

### Phase B2 — same-carrier geometry packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B3 | `geometry_crosschecks_same_carrier` | covered; ready_now | keep as main geometry packet anchor | geomstats, clifford, pytorch |
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
| B11 | `graph_cell_complex_geometry` | covered; ready_now | deepen shallow-tool usage on same-carrier geometry | pyg, toponetx, xgi |
| B12 | `state_class_binding_geometry` | canonical by process | keep `sim_toponetx_state_class_binding.py` as the direct local TopoNetX binding anchor; deepen separate graph/topology successors rather than re-auditing this packet again | toponetx |
| B13 | `cell_complex_geometry` | canonical by process | keep `sim_cell_complex_geometry.py` as the direct local TopoNetX anchor; deepen separate graph/topology successors rather than re-downgrading this packet | toponetx, gudhi |
| B14 | `persistence_geometry` | canonical by process | keep `sim_persistence_geometry.py` as the direct local persistence anchor; deepen separate graph/topology successors rather than re-auditing this bounded topology packet | gudhi |

### Phase B4 — operator/chirality/differential packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B15 | `operator_family_admission` | needs deeper lego work; blocked_on_lego | keep `sim_local_operator_action.py` as the clean primitive local-action anchor and deepen channel/commutator/Clifford successors next | clifford, sympy, z3 |
| B16 | `channel_cptp_map` family | canonical by process | keep `sim_pure_lego_channels_choi_lindblad.py` as the direct bounded local channel-admission anchor; advance separate channel-capacity / taxonomy / measurement successors next rather than re-auditing this packet again | z3, pytorch |
| B17 | `composition_order_noncommutation` | canonical by process | keep `sim_torch_channel_composition.py` as the direct local order-sensitivity anchor; deepen separate channel/commutator/Clifford successors next rather than re-auditing this packet again | z3, sympy, pytorch |
| B18 | `flux_candidate_family` | derived/open only | defer until transport + chirality + delta surfaces are real | differential/chirality packet first |

### Phase B5 — bipartite/correlation local packet

| Priority | Lego / packet | Current state from docs | Next bounded move | Preferred tool pressure |
|---|---|---|---|---|
| B19 | `bipartite_structure_local` | covered; ready_now | maintain as local witness layer below bridge | gudhi, pyg |
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
| C5 | `16_lego_build_catalog.md` | keep grouped controller ledger current | patch when new docs/results materially change states |
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

| Priority | Tool-capability family | Objective | Current state | Next bounded move |
|---|---|---|---|---|
| D1 | proof/symbolic capability | make impossibility, cross-check, derivation, and synthesis roles explicit | partial but active | bounded z3 / cvc5 / sympy packets with baseline-vs-canonical comparison notes |
| D2 | graph-native capability | learn DAG, pairwise-graph, and hypergraph-native claim paths | partial but active | bounded rustworkx / PyG / XGI packets on one local object family |
| D3 | topology capability | learn cell-complex and persistence claim paths | partial but active | bounded TopoNetX / GUDHI packets with explicit local witness scope |
| D4 | geometry/equivariance capability | learn rotor/spinor, metric/geodesic, and equivariance claim paths | partial but active | bounded clifford / geomstats / e3nn packets on one same-carrier geometry family |
| D5 | baseline-vs-canonical comparison surface | keep the difference between numpy baselines and tool-native counterparts explicit | now strategically necessary | write or update explicit comparison notes whenever a pair exists |

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

## Explicit non-queue items
Do not promote by default:
- axis work
- broad bridge closure claims
- entropy-first summaries
- unbounded maintenance autonomy
