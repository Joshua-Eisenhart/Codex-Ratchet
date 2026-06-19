# Old Sims Complete Consume Receipt - 2026-06-12

```yaml
receipt_kind: old_sims_complete_consume
lane: "DEEP-READ LANE - rest of old-sims estate beyond prior axis/queue/basin/Hopfield passes"
repo: "/Users/joshuaeisenhart/Codex-Ratchet"
write_scope: "exactly this file"
git_action: "none"
classification: "mining_receipt"
promotion_allowed: false
formal_admission_allowed: false
claim_ceiling: "complete old-estate consume table plus proposed packet feedstock only"
```

## Fences

```text
This receipt does not promote any old sim, formal scout, Julia carrier result, bridge row, axis row,
basin row, Hopfield row, QIT row, physics row, or registry row.
It treats old code/results as mined feedstock, dormant candidates, graveyard negatives, superseded
material, or weird fragments.
It does not claim layer completion, canonical manifold admission, bridge admission, Axis0/Xi/Phi0
closure, physics, FEP, gravity, holography, ER=EPR, consciousness, or final M(C).
It writes no queue file, no registry file, no source file, no result JSON, and no git state.
```

## Direct Inventory And Read Evidence

```yaml
roots_read:
  - system_v4/probes/
  - system_v5/ops/formal_scouts/
  - system_v5/julia_carrier/
direct_read_pass:
  command_shape: "Python pathlib rglob over all files; read_bytes for every file; JSON parse for *.json; header/claim-term scan for non-JSON"
  files_opened: 8145
  read_errors: 0
  by_root:
    system_v4/probes: 6626
    system_v5/ops/formal_scouts: 990
    system_v5/julia_carrier: 529
  json_files: 883
  json_parsed_ok: 882
  json_parse_errors:
    - path: system_v5/julia_carrier/scratch_jax_snapshot_20260604/gs_su3_calabiyau_jax_results.json
      error: "Expecting value: line 9 column 25"
  dominant_file_types:
    py: 5028
    json: 883
    jl: 192
    md: 19
    pyc: 124
    lane_snapshots: 1881
  parsed_json_classifications:
    scratch_diagnostic: 369
    classical_baseline: 207
    canonical: 98
    tool_lego_fit_probe: 58
    formal_scout: 23
  parsed_json_promotion_allowed_false: 588
```

## Prior Coverage Diff

| Prior surface | Covered before this pass | Excluded from new packet proposals here | Residual handled here |
|---|---|---|---|
| `system_v6/receipts/old_sims_axis_variants_20260612.md` | Axis-bearing old sims and cross-axis variants, including Axis0-6 adapter sketches. | Axis anchors, axis contenders, axis readout rows, and axis registry amendments. | Only axis-adjacent negatives that became newly testable today are listed as controls. |
| `77fb7ca52` / `system_v6/receipts/old_estate_mine_20260611.md` | Broad mine of all three roots: 6626 v4 files, 990 formal-scout files, 529 Julia-carrier files, 68 negative/graveyard items, ranked unconsumed queues. | The 14-item/20-item future queue is not re-presented as new work unless today's results changed relevance. | This receipt classifies the rest as active feedstock, dormant, graveyard, superseded, or weird. |
| Basin/Hopfield/surface passes | Attractor-basin doctrine, basin/Hopfield estate, spinor-network surface estate, and quantum-Hopfield gap. | Basin/Hopfield rows are not relitigated. | Only basin/Hopfield-adjacent old fragments are marked superseded or dormant. |
| Today's committed v6 results | `axis0_contender_heavy_v0`, `axis_triple_consistency_b6_v0`, `ring_checkerboard_qca_v2`, axis registries, axis0 amendment. | No old result is upgraded because of these. | They reopen or sharpen negative-control tests against old bridge/axis/QCA claims. |

## Complete Consume Table For Residual Old-Sim Objects

| Residual object / sim family | Main old source(s) | What it computes | Verdict / ceiling | Current relevance class | Packet proposal only if active |
|---|---|---|---|---|---|
| Carnot/Szilard/Landauer fence family | `system_v4/probes/*carnot*`, `*szilard*`, `bridge_landauer_erasure_bit_distinguishability_results.json`, graveyard receipts | Classical heat/work ledgers, super-Carnot exclusions, Landauer erasure floors, measurement-feedback variants. | Classical calibration only; source rows remain open where graveyards say so. | superseded-by-committed-work | No new packet; current committed `carnot_szilard_landauer_ledger_v1` and `carnot_szilard_basin_cycle_v0` are the active surfaces. |
| Engine-lab open-row audit and graveyard trio | `sim_engine_lab_*`, `carnot_asymmetric_direction_graveyard_results.json`, `szilard_open_failure_graveyard_results.json`, `engine_lab_sidecar_graveyard_results.json` | Open-row repair priorities, topology/readout sidecars, killed/survived local variants. | Controller audit only; no source-row closure. | dormant candidate | No packet unless engine-lab queue movement resumes. |
| Stage-matrix negative batteries | `deep_graveyard_battery.py`, `extended_graveyard_battery.py`, `thermodynamic_graveyard_battery.py`, `neg_scrambled_sequence_sim.py` | Designed-fail controls for order, dissipation, chirality, CPTP, decoherence, commutativity. | Graveyard/control library; not mechanism evidence. | feedstock for active vein | Use as control-set feedstock for any new sequence/order/axis packet. |
| Szilard PyTorch measurement-feedback cycle | `sim_szilard_torch_measure_feedback_erasure_landauer_cycle.py` | Density update, mutual information, feedback/erasure accounting, z3 forbidden-region check. | Source intent / bridge-control row; no promotion. | superseded-by-committed-work | No immediate packet; committed ledger/fence rows are stronger. |
| Hopf base-section phase recovery | `sim_hopf_base_section_phase_recovery.py` family | Base/fiber section reconstruction and wrong-phase negative controls. | Earned later as `hopf_base_section_phase_recovery_v0`; scratch. | superseded-by-committed-work | None. |
| Clifford Spin(3) double-cover micro | `sim_clifford_spinor_double_cover_micro.py` and related Clifford rotor probes | `R` and `-R` same vector action, non-unit rotor exclusions. | Earned later as `clifford_spin3_double_cover_micro_v0`; tool-function micro only. | superseded-by-committed-work | None. |
| TopoNetX/GUDHI Hodge-Betti cross-check | `sim_toponetx_gudhi_hodge_betti_cross.py`, topology parity probes | Torus/disk/sphere Betti/Hodge parity and topology mislabel controls. | Candidate fixture; old same-stem result not found. | feedstock for active vein | `topology_parity_micro_v0` only if a current topology packet needs an independent Betti/Hodge guard. |
| G-tower GL-to-O metric reduction | `sim_gtower_gl_to_o_reduction.py` | Excludes GL candidates that do not preserve fixed metric under `A^T g A = g`. | Classical G-structure exclusion fixture. | dormant candidate | No packet unless G-structure reduction reopens. |
| SMT/cvc5 law fixtures | `sim_cvc5_*constraint.py`, monad/effect/operad law probes | SAT/UNSAT law fixtures and violated-law negatives. | Law fixtures only, not ratchet mechanism evidence. | feedstock for active vein | Use one fixture at a time as SMT negative control for exact future law packets. |
| QIT density/channel baselines | `sim_*density*`, `sim_*channel*`, `tool_capability_qutip.py`, `tool_capability_torch.py` | CPTP, Choi, trace, entropy, trace-distance, Werner/Bell/CHSH/channel controls. | Baseline hygiene; no nonclassical witness. | feedstock for active vein | Consume as hygiene controls in any current QIT/channel packet. |
| Hopf/Weyl/Clifford transport family | numerous `sim_*hopf*`, `sim_*weyl*`, `sim_*clifford*` | Carrier/readout transport, holonomy, chirality, convention-sensitive projections. | Must be decomposed; old rows are convention-pressure only. | dormant candidate | No packet until a row has one carrier, one observable, one kill condition. |
| Large integration / mega-stack probes | `sim_integration_*mega_stack.py`, multi-shell coupling programs | Broad tool couplings and multi-layer vocabulary. | Too wide; source intent or decorative risk until micro receipts exist. | weird-fragment | No packet. Decompose before use. |
| `spinor_twistor_entanglement_information_network_root_gate` | `system_v5/ops/formal_scouts/sim_spinor_twistor_entanglement_information_network_root_gate_probe.py` | Finite spinor/twistor incidence, entanglement entropy, SU2 transport, tensor graveyards, capacity gates. | Source-only; result JSON absent. | dormant candidate | No immediate packet; v6 finite-incidence packets already cover the safer route. |
| `spinor_twistor_network_clifford_tensor_boundary_next_wave` | formal scout source | Clifford rotor transport, entropy-only equality control, tensor boundary, capacity check. | Source-only; no ER=EPR/holography/twistor promotion. | dormant candidate | None. |
| `spinor_twistor_flux_basin_binding` | formal scout source | Tests global flux binding versus per-stage flux flipping for finite spinor/twistor basins. | Source-only; no result JSON. | feedstock for active vein | Possible future packet only after shared-carrier flux/basin gate is explicit. |
| `spinor_twistor_xi_cut_phi0_bridge_candidate` | formal scout source | Xi -> rho_AB -> coherent-information Phi0 bridge with product/history/phase controls. | Source-only; expected naive raw incidence-phase bridge may fail. | feedstock for active vein | Only as a negative bridge boundary, not an admission packet. |
| `geometric_flux_derives_basin_binding` | formal-scout README row | Hopf/Weyl geometry deriving global flux sign and testing basin binding. | README-declared result absent. | dormant candidate | None. |
| `source_aligned_qit_engine_runtime` / attractor basin | formal-scout README row | Source-aligned runtime and attractor-basin scout rows. | Declared result JSON absent; README frozen/stale. | dormant candidate | None. |
| `qit_fep_axis0_path_integral_spinor` | formal-scout README row | Spinor density states and Kraus-history path sums for finite path-FEP. | Declared result absent; FEP/Axis0 promotion blocked. | feedstock for active vein | Proposed only as a fenced predictive/FEP readout control after Axis0 amendment rows are selected. |
| `axis0_entropy_family_qit_fep_admission_bakeoff` | formal-scout README row | Comparative entropy/readout family bakeoff with controls. | Declared result absent; no family admission. | superseded-by-committed-work | Today's `axis0_contender_heavy_v0` supersedes the broad bakeoff shape in its registry scope. |
| `source_aligned_stack_completion_gap_classifier` | formal-scout README row | Completion/gap classifier, including premature-completion unsat. | Declared result absent. | feedstock for active vein | Useful only as a validator/gate hardening idea; no sim packet. |
| `two_root_constraint_flux_coherent_recovery_*` | formal-scout README rows | Flux-coherent recovery Phi0 candidate and stress rows. | Declared results absent; final Xi/Phi0 blocked. | feedstock for active vein | Only as negative/contrast rows for flux-coherent bridge tests. |
| `process_signature_family_local_*` | formal-scout README rows | Vector-bundle and family-local process signatures with scalarization controls. | Declared results absent; no scalar Phi0/tensor admission. | dormant candidate | None. |
| `engine_v6_l0_purification_bridge_witness` | formal-scout source | Purification bridge exclusion label. | Source-only in current results; bridge boundary only. | graveyard negative | Keep as bridge-exclusion control. |
| Full sedenion zero-divisor / 84-pair graph | `system_v5/julia_carrier/*sedenion*`, canon artifact receipts | Sedenion zero-divisor witnesses and convention-sensitive product spellings. | Graveyard/control; witness spelling convention-dependent. | dormant candidate | No packet unless a convention-pinned full graph classifier is requested. |
| Octonion associator as 3-cell/cocycle | `canon_algebra_artifact_v1`, octonion carrier rows | Concrete associator witness, e.g. `e1,e2,e4 -> -2e5`. | Algebra-local scratch diagnostic. | feedstock for active vein | Use as a 3-cell bracketing-erasure control only. |
| Malcev / Akivis tangent probe | Julia carrier artifact plus nonassoc map | Finite commutator/associator data for tangent identities. | Ready but unimplemented; tangent identity only. | dormant candidate | None until nonassoc tangent lane opens. |
| Split-octonion / split-`G2(2)` discriminator | Julia carrier nonassoc rows | Compact-vs-split multiplication/signature alternative. | Separate split convention needed. | dormant candidate | None. |
| Nucleus and associator-ideal harness | Julia carrier artifact | Locates bracketing defects instead of binary associativity pass/fail. | Finite table analysis only. | dormant candidate | None. |
| Associahedron/free-magma bracketing harness | Julia carrier artifact | Arity-4/5 bracketing grammar generator idea. | Harness object, not independent claim. | dormant candidate | None. |
| Same-carrier `M(C)` bracketing field | Julia carrier + current M(C) receipts | Whether associator changes admissibility object or only readout. | Future integration only; no old promotion. | dormant candidate | None. |
| Quaternion-as-control consumer gate | Julia carrier quaternion controls | Noncommutative but associative kill-control. | Control row only. | feedstock for active vein | Use to kill root-only nonassoc overclaims. |
| `discrete_axis0_field` / `axis0_field_candidate` | old registries and axis docs | Graph scalar `phi0: V -> R`, directed gradients, local scalar readout. | Axis candidate only. | superseded-by-committed-work | Today's Axis0 heavy result narrows active path to committed anchor alias class; keep as historical candidate/control. |
| `Xi_shell` | old registry / AXES ladder | Shell-aggregated bridge candidate. | Bridge candidate only; not Phi0 closure. | dormant candidate | None unless Xi bridge lane explicitly reopens. |
| `Xi_hist` | old registry / AXES ladder | History-window bridge candidate with erased-history control. | Bridge candidate only. | dormant candidate | None. |
| `torus_seat_entropy` | old registry | Geometry-seat entropy over a torus family. | No global entropy-field claim. | dormant candidate | None. |
| `path_entropy`, `branch_weight`, `history_window_entropy`, `transport_weighted_entropy` | old registry | Entropy over paths, branches, history windows, and transport-weighted structure. | Must compute weights/windows, not label-assign. | feedstock for active vein | Use only one functional at a time as an entropy-row candidate/control. |
| `operator_ordered_entropy` | old registry and `sim_operator_ordered_entropy.py` | Entropy response under noncommuting operator/terrain order. | Order fixture; no axis admission. | feedstock for active vein | Good control for sequence/order claims after current cross-axis negative. |
| `shell_indexed_tensor_network`, `shell_fuzz_jk` | old registry | Shell-indexed tensor support and j/k support-window perturbations. | Support-window only. | dormant candidate | None. |
| `chiral_overlap` | migration registry row | L/R Weyl handedness overlap under fixed carrier. | No physics/SM promotion. | feedstock for active vein | Useful only as a local chirality control. |
| `z_measurement`, `measurement_instrument`, `purify(rho)`, `unitary_rotation()` | migration registry rows | Standalone measurement, instrument, purification, rotation-as-channel functions. | Micro QIT hygiene objects only. | feedstock for active vein | Build only when needed by a current packet's missing primitive. |
| `relative_entropy_coherence`, `wigner_negativity`, `quantum_discord`, `mutual_information_measure`, `coherent_information_measure`, `logarithmic_negativity`, `channel_capacity`, `blackwell_style_comparison` | old registry / migration rows | Local information/functionals over fixed state/channel families. | Local measurements only; no bridge or Axis0 promotion. | dormant candidate | None until a current packet selects exactly one. |
| `operator_semigroup_closure` over `{Ti,Te,Fi,Fe}` | operator docs / terrain map | Bounded word-depth closure/invertibility test. | Likely kills finite-group overclaim unless parameters/quotients are fixed. | feedstock for active vein | Useful negative for operator-family closure claims. |
| 68 C4 divergence-log proposal rows | `system_v5/ops/c4_divergence_log_proposals.json` | Dry-run list of old classical/bridge files missing divergence logs; 58 bridge, 10 classical, 40 with emitted-classification conflicts. | Review index only; not a graveyard result set. | graveyard negative | Use as a negative-control index before citing any listed old bridge/classical row. |

## Newly Testable Or Newly Relevant Negatives From Today's Committed Results

| Negative/control | Old source/index | Today's committed result that makes it newly testable/relevant | Current use |
|---|---|---|---|
| Axis0 family bakeoff rows that try to admit non-anchor readouts. | `axis0_entropy_family_qit_fep_admission_bakeoff`, `sim_torch_axis0_*`, `sim_phi0_*`, C4 rows. | `axis0_contender_heavy_v0` says registry-scoped Axis0 is the anchor alias class and no co-survivor minted. | Newly relevant as exclusion controls; any old Axis0/FEP/Phi0 row must first state whether it is anchor-alias, excluded, or outside that registry. |
| Cross-axis formula `b6=-b0*b3` as universal law. | old axis/rosetta/axis6 bridge rows. | `axis_triple_consistency_b6_v0` passes blind anchors but fails widened Hopf sample at chance; strongest reading is realization-unfaithful. | Newly testable as shared-carrier requirement: old axis-composition claims must rerun all signs on one carrier. |
| Flux-engine relabeling. | QCA/ring/checkerboard/flux old rows and `sim_symplectic_berry_flux_axis0.py`. | `ring_checkerboard_qca_v2` earns extraction fixture but rejects L/R engine rows because they are calibration shifts under flux labels. | Newly relevant kill pattern: old flux rows must prove distinct engine unitaries, not labels on calibration operators. |
| Operator-order entropy / loop-order claims. | `sim_operator_ordered_entropy.py`, `sim_loop_order_family.py`, stage-matrix batteries. | Cross-axis negative plus QCA relabeling both show order/content separation failures are active. | Use scrambled/swapped/order-erased controls before citing old sequence positives. |
| Bridge/classical rows with emitted `canonical` literals. | 40 conflict rows in `c4_divergence_log_proposals.json`. | Today's receipts maintain scratch/fenced status for new axis/physics/holodeck claims. | Newly relevant as review blockers: old `canonical` literals cannot be used without reclassification. |
| FEP/gravity/holodeck render rows as substrate claims. | `sim_fep_derivative_bridge.py`, `sim_tetra_holodeck_fep_science_method_axis0.py`, physics/holodeck receipts. | Today's doctrine receipts put FEP/gravity/holodeck in candidate/readout/render layers, not carrier admission. | Use as boundary negatives against substrate promotion. |
| Below-Landauer and super-Carnot violators. | Carnot/Szilard graveyards and C4 Szilard rows. | Committed Carnot/Szilard ledger and basin-cycle work now provide exact current comparisons. | Still relevant, but superseded by committed ledgers for live packet checks. |
| Sedenion witness spelling as invariant. | Julia carrier sedenion rows. | Current nonassoc receipts keep convention sensitivity explicit. | Keep killed unless a packet pins doubling rule and basis/order. |

## Weird Fragments

| Fragment class | Paths / count | Honest classification |
|---|---:|---|
| Lane snapshot files | 1881 files with `.laneA_w*` / `.laneB_w*` suffixes | Generated split/snapshot artifacts, not independent sims. Counted in read pass; not packet feedstock by themselves. |
| Python bytecode | 124 `__pycache__/*.pyc` files | Runtime residue; not source evidence. |
| macOS metadata | `system_v4/probes/.DS_Store`, `system_v5/ops/formal_scouts/.DS_Store` | Weird fragment; no claim content. |
| Visualization/support files | `nested_hopf_viz.html`, `attractor_basin_viz.html`, `evidence_graph.mermaid`, heartbeat logs/plist | Support/runtime artifacts, not sim receipts. |
| Duplicate-space filenames | `sim_zorns_lemma_constraint_canonical 2.py`, `sim_quantum_capacity_classical 2.py`, `sim_lattice_distributive_constraint_canonical 2.py`, `sim_p_adic_comparison_crystalline_constraint_canonical 2.py` | Likely duplicate/copy artifacts; do not cite without comparing against canonical same-family file. |
| Malformed JSON | `system_v5/julia_carrier/scratch_jax_snapshot_20260604/gs_su3_calabiyau_jax_results.json` | Parsed-failed fragment; cannot be used as result evidence. |

## Final Gaps And Completion Claim

```yaml
old_estate_completion_claim:
  inventory_level: "complete for the requested roots as of this read pass"
  files_opened: 8145
  read_errors: 0
  receipt_coverage_after_this_file:
    system_v4/probes: "covered by old_estate_mine plus this residual consume and weird-fragment table"
    system_v5/ops/formal_scouts: "covered by old_estate_mine plus this source-only/supersession consume"
    system_v5/julia_carrier: "covered by old_estate_mine plus this algebra/control consume"
  no_uncovered_old_estate_files_known_after_this_receipt: true
absence_claim_rule:
  - "Absence here means no uncovered file/path/object was found by the direct filesystem read pass and prior-receipt diff."
  - "It does not mean no useful future packet can be built from old material."
  - "It does not cover files added after this receipt or paths outside the three requested roots."
  - "Any later packet must still reread its exact source files and current committed result before citing them."
remaining_gaps:
  - "No strict quantum-Hopfield carrier was found; prior surface receipt already owns that gap."
  - "No broad Axis0/FEP/Phi0 old row may bypass today's Axis0-heavy adjudication."
  - "No old bridge/classical row in the 68 C4 index should be cited until its classification conflict and divergence-log gap are reviewed."
  - "Malformed JSON and duplicate-space filenames remain unusable without repair/compare work."
```
