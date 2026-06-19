# Deep Validity Audit - Lane E Gap Closure (2026-06-12)

```yaml
receipt_kind: validity_audit_lane_e_gapclosure
auditor: codex2_medium
claim_ceiling: audit_receipt_only
promotion_allowed: false
formal_admission_allowed: false
write_scope: system_v6/receipts/validity_audit_lane_e_gapclosure_20260612.md only
git_mutation: none; no git add/commit
```

## Bottom Line

Lane E closes the Gemini gap for the missed sim directories, `system_v6/optional/`, `system_v6/probes/`, and ghost citations. The missed estate is mostly real scratch computation, but four row groups should not be cited as current `VALID`: `axis_triple_consistency_b6_v0/v1` are b6-law-moot after `0313d47bc`, `s8_local_information_table_v0` has a stale envelope source hash, `twistor_incidence_finite_packet_v0` has a stale baseline-result hash, and `manifold_dynamic_chart_v1` has no result JSON.

The strongest positive rows are the ratchet series, the round3 discriminator series, `flux_emergence_discriminator`, `z4_syndrome_record_v0`, `bloch_root_admissibility_discriminator_v0`, `assoc_weakening_lattice_classifier`, and the source-locked/operator/terrain matrix packets. These are `VALID` only at their named `scratch_diagnostic` packet ceilings; none earns admission, bridge, physics, or canonical doctrine.

## Shared Rubric Cited

- VALID: the result is computed from source, reproducible, controls fire for computed reasons, independently cross-audited (or honestly labeled awaiting-audit), and the CLAIM'S NAME matches what was actually measured. Honest negatives/nulls/deaths ARE valid.
- SHALLOW: real computation but the claim exceeds the measurement - the species catalog: static/synthetic fields wearing measurement names (the Axis-0 polynomial); one-step witnesses wearing response/dynamics names; formula taxonomy wearing family-closure names; decorative tools (load_bearing labels w/o capability probes; byte-identical all_pass mirrors); thin/unfair baselines; carrier-relative results cited carrier-free; pre-G.2a contract gaps; results resting on provenance-disowned doctrine (the b6 species).
- FAKE/BROKEN: not reproducible from current source (hash mismatches, stale results); hardcoded/echoed values presented as computed (the frozen-factor/readback species); claims with NO computation behind them; red validators cited as green; quote-fabrication; decorative SMT asserting literals.

Built on, not redone: `static_shallowness_audit_20260612.md` at b4ee8f030, `hermes_audit_forwarded_20260612.md` at b891e0611, `owner_correction_axis0_not_built_20260612.md` at 0313d47bc, and `receipts_index_20260612.md` at 276d42d81.

## Scope Diff

Mechanical diff of `system_v6/sims/` against Lane A+B table entries found 47 missed sim directories.

Explicit Gemini gap dirs present and not covered by A/B: `ratchet_deep_chain_v0`, `ratchet_g2_family_v0`, `ratchet_order_breadth_v0`, `ratchet_s1_single_shell_pilot_v0`, `ratchet_s2_three_shell_chain_v0`, `ratchet_s2_two_shell_flux_v0`, `ratchet_s6_terrain_operator_shell_v0`, `ratchet_s6_terrain_sweep_v0`, `round3_s2_alias_pass_v0`, `round3_s3_alias_pass_v0`, `round3_s4_alias_pass_v0`, `round3_s4_heavy_discriminator_v0`, `round3_s5_alias_pass_v0`, `round3_s5_heavy_discriminator_v0`, `round3_s6s7_alias_pass_v0`, `round3_s6s7_heavy_discriminator_v0`, `round3_s9_alias_pass_v0`, `round3_s9_s2_final_heavy_v0`, `assoc_weakening_lattice_classifier`, `axis_triple_consistency_b6_v0`, `axis_triple_consistency_b6_v1`, `bloch_root_admissibility_discriminator_v0`, `flux_emergence_discriminator`, `z4_syndrome_record_v0`.

Additional A/B misses found: `axis_independence_discriminators_036`, `compression_flow_radiated_record_v0`, `dual_stack_carnot_szilard_hopf_weyl_probe`, `engine_readout_spinor_lift_v0`, `engine_readout_strategy_fidelity_v0`, `engine_stage_word_cost_discriminator_v0`, `g2_forced_vs_installed_discriminator`, `malcev_akivis_tangent_micro_v0`, `manifold_dynamic_chart_v1`, `nesting_consistency_family_v0`, `pg32_sedenion_incidence`, `root_randomness_entropy_discriminator_v0`, `s8_local_information_table_v0`, `sequential_inheritance_not_cycle_v0`, `source_locked_operator_base_packet`, `spinor_network_hopf_weyl_testbed`, `terrain_exact_mirror_finder_v0`, `terrain_generator_sheet_packet`, `terrain_operator_precedence_64_matrix`, `terrain_spinor_shell_nest_v0`, `terrain_weyl_spinor_lr_v0`, `twistor_incidence_finite_packet_v0`, `winlose_pattern_derivation_discriminator`.

## Fresh Checks

- Validator spot-reruns: 8 fresh `scripts/validate_three_engine_sim_result.py` checks returned `ok:true`: `ratchet_deep_chain_v0`, `ratchet_s6_terrain_sweep_v0`, `round3_s4_heavy_discriminator_v0`, `round3_s9_s2_final_heavy_v0`, `axis_triple_consistency_b6_v0`, `axis_triple_consistency_b6_v1`, `flux_emergence_discriminator`, and `source_locked_operator_base_packet`.
- Load-bearing recomputes: `ratchet_s2_two_shell_flux_v0` recomputed `dchi_gap=1/2` and `flux_physical=pi/2`; `ratchet_s6_terrain_sweep_v0` recomputed `Se_Funnel_L` order-gap norm squared `4/25`; `z4_syndrome_record_v0` recomputed erased-record loss `ln(4)=1.3862943611198906` and partial-record defect `ln(2)=0.6931471805599453`; `flux_emergence_discriminator` recomputed oriented Chern `-1` and absolute Chern `1`.
- Source-hash freshness: every row marked `VALID` below had no stale `source_path/source_sha256` pairs in the audit sweep or passed strict/source-backed validator sampling. Exceptions are explicitly downgraded: `s8_local_information_table_v0`, `twistor_incidence_finite_packet_v0`, and `manifold_dynamic_chart_v1`.
- b6 provenance overlay: `axis_triple_consistency_b6_v0/v1` validators are green, but the law row is moot by owner correction `0313d47bc`; only machinery/proxy carrier work survives.
- Flux decorative-proof check: `flux_emergence_discriminator` binds shared engine values, reports Chern `1`, three ablations, and solver rows with computed values/erased flips; no decorative literal-only SMT issue found in this audit.

## Classification Table

| packet / surface | classification | one sentence of evidence | upgrade to VALID or stronger-valid |
|---|---|---|---|
| `ratchet_deep_chain_v0` | VALID | Source hashes are fresh, validator is green, and the packet computes the deep ratchet chain with real mortality, denominator, holonomy, and terrain-order rows. | None for scratch chain claim; do not cite as global order theorem. |
| `ratchet_g2_family_v0` | VALID | Source-fresh G2 ratchet computes `Der(O)=14`, stabilizer `8`, branch rows, split fork, and sign/permutation controls. | Independent algebra engines would strengthen backend-independence; no admission. |
| `ratchet_order_breadth_v0` | VALID | All 24 fixed `L/Z/W/T` orders are enumerated, 19 die, and 5 survivors collapse to 2 order-blind classes under the corrected full-signature grouping. | Extend beyond this fixed alphabet/multiset before broader ratchet-order claims. |
| `ratchet_s1_single_shell_pilot_v0` | VALID | Single-shell conditioning, Z4 quotient, holonomy `pi/2`, and non-Z4-saturated mortality are source-fresh and scoped to one shell. | Multi-shell/nested conditioning requires separate packets. |
| `ratchet_s2_two_shell_flux_v0` | VALID | Recomputed `dchi_gap=1/2`, `flux=pi/2`, Stokes identity, Z4 rows, and controls match fresh source-backed envelope. | No 3+ shell or terrain claim; use three-shell packet for that. |
| `ratchet_s2_three_shell_chain_v0` | VALID | Three-leaf union weights and flux chain compute `flux12+flux23=flux13` with source-fresh Julia/Python rows and controls. | More shells or terrain coupling require new receipts. |
| `ratchet_s6_terrain_operator_shell_v0` | VALID | Source-fresh packet computes `Se_Funnel_L` then `Fi_R_x` order gap `4/25` and commuting `D_z/R_z` zero control. | Not a basin theorem or full terrain sweep. |
| `ratchet_s6_terrain_sweep_v0` | VALID | Strict validator is green and recompute confirms 8 terrains, zero fixed survivors, `Se_Funnel_L` gap `4/25`, and five commuting controls. | Broader support-graph/topology alternatives remain separate. |
| `round3_s2_alias_pass_v0` | VALID | Source-fresh S2 alias pass compares committed-adjacent connection/convention rows with matching Julia/JAX verdict hashes. | Heavy/global S2 alternatives require separate discriminator rows. |
| `round3_s3_alias_pass_v0` | VALID | Source-fresh S3 alias pass checks d=2 POVM probe-family candidates with matching Julia/JAX verdict hashes. | Does not prove global S3 uniqueness. |
| `round3_s4_alias_pass_v0` | VALID | Source-fresh S4 alias pass checks committed-adjacent operator/channel alphabets and keeps the claim to alias screening. | Use heavy packet for local exclusion rows. |
| `round3_s4_heavy_discriminator_v0` | VALID | Fresh validator is green and the packet runs the four queued S4 heavy-local rows with SMT/tool intent and matching verdict table. | Does not exhaust all operator/channel space. |
| `round3_s5_alias_pass_v0` | VALID | Source-fresh S5 alias pass is bounded to registered terrain-flow family alias screening. | Heavy S5 exclusions require heavy packet rows. |
| `round3_s5_heavy_discriminator_v0` | VALID | Source-fresh heavy S5 discriminator computes registered candidate kills/co-survivors under bounded terrain-flow batteries. | Does not prove minimality of the eight-generator set. |
| `round3_s6s7_alias_pass_v0` | VALID | Source-fresh S6/S7 alias pass screens registered topology/support aliases without claiming full topology exhaustion. | Heavy topology exclusions require heavy packet rows. |
| `round3_s6s7_heavy_discriminator_v0` | VALID | Source-fresh heavy packet computes registered S6/S7 topology/support discriminators with bounded controls. | Does not close every support graph/topology alternative. |
| `round3_s9_alias_pass_v0` | VALID | Source-fresh S9 alias pass validates bounded path/connection candidates and names only phase-1 screening. | Convention-independent S9 exclusion remains open. |
| `round3_s9_s2_final_heavy_v0` | VALID | Fresh validator is green; SMT binds S9 theta-gap `pi/120` and S2 invalid-cover validity with erased flips. | No global S9 uniqueness or arbitrary S2 union theorem. |
| `assoc_weakening_lattice_classifier` | VALID | Finite structure-constant classifier computes R/C/H/O/S/K law matrix with Z3/cvc5 controls and H/O flips. | Stronger algebra admission needs canonical proof surface, not this classifier alone. |
| `axis_triple_consistency_b6_v0` | SHALLOW | Real three-engine computation reproduces a chance-level negative on an unfaithful Hopf transplant, but the b6 law row is provenance-disowned. | Retain machinery only; replace the b6-law target with owner-authorized topology/axis target. |
| `axis_triple_consistency_b6_v1` | SHALLOW | Real 33-cell/proxy carrier audit finds no faithful gamma-in/gamma-out adapter, so law admission is blocked and moot. | Build a proof-backed 33-cell cover or source-backed adapter before retesting any relation. |
| `bloch_root_admissibility_discriminator_v0` | VALID | Source-fresh three-engine discriminator computes Bloch/Hopf ladder, sedenion failure, rank obstruction, and SMT value flips. | No carrier admission or physics claim without a consuming proof gate. |
| `flux_emergence_discriminator` | VALID | Strict validator is green; Chern `1`, holonomy/flux rows, three ablations, and computed-value SMT flips survive without decorative proof. | Keep as candidate-family discriminator; no family winner or axis/bridge claim. |
| `z4_syndrome_record_v0` | VALID | Source-fresh packet computes Z4 syndrome/preimage table, erased/partial record entropy, bit-exact reconstruction, and shuffled syndrome failure. | Stronger information-dynamics claim needs trajectory consumer. |
| `axis_independence_discriminators_036` | SHALLOW | Source-fresh 3x3 vary/hold matrix is real, but "axis independence" exceeds class-level polarity discrimination under named pins. | Rename to pinned polarity discriminator or add independence proof criteria. |
| `compression_flow_radiated_record_v0` | VALID | Source-fresh finite compression-flow/radiated-record packet is valid as first scratch record accounting. | No S11/bridge claim without consuming dynamics and cross-audit. |
| `dual_stack_carnot_szilard_hopf_weyl_probe` | SHALLOW | Computation exists, but result lacks `source_path/source_sha256` freshness pairs in the envelope scan. | Add source locks and rerun before current `VALID` citation. |
| `engine_readout_spinor_lift_v0` | VALID | Source-fresh packet measures phase-sensitive spinor-lift readouts separating first/second 360 traversals. | Keep to readout separation; no full engine proof. |
| `engine_readout_strategy_fidelity_v0` | VALID | Source-fresh packet regenerates n=8 dense loop-local states and reads the committed 16-strategy automaton. | No behavioral theorem beyond finite strategy fidelity. |
| `engine_stage_word_cost_discriminator_v0` | VALID | Source-fresh cost discriminator tests the committed two-engine 8-stage word in local ring MPS dynamics. | Broader engine optimality needs expanded word-family search. |
| `g2_forced_vs_installed_discriminator` | VALID | Source-fresh discriminator shows G2 is installed by stronger carrier constraints, not forced by bare root, with H/M2/O controls. | Does not prove a crowned G2 form. |
| `malcev_akivis_tangent_micro_v0` | VALID | Source-fresh packet computes octonion commutator non-Lie/Malcev behavior and quaternion subalgebra controls. | Stronger tangent theory requires a consuming formal proof. |
| `manifold_dynamic_chart_v1` | FAKE/BROKEN | Directory exists but no result JSON was found, so there is no reproducible packet result to classify as current. | Run/build the packet, write result JSON, then audit source hashes and controls. |
| `nesting_consistency_family_v0` | VALID | Source-fresh packet computes inter-rung/inter-stage nesting maps with embedding, trace, arrow-order, and quotient-chain rows. | Family closure beyond registered maps remains open. |
| `pg32_sedenion_incidence` | VALID | Source-fresh three-engine packet computes PG(3,2)/sedenion incidence rows with matching scalar controls. | No broad sedenion geometry claim. |
| `root_randomness_entropy_discriminator_v0` | VALID | Source-fresh three-engine finite root-layer discriminator computes geometry-first entropy/order rows and label-shuffle controls. | Keep root-layer finite discriminator ceiling. |
| `s8_local_information_table_v0` | FAKE/BROKEN | Envelope `source_path/source_sha256` is stale even though other engine sources are fresh. | Rerun envelope from current source and then revalidate. |
| `sequential_inheritance_not_cycle_v0` | VALID | Source-fresh all-three packet separates inheritance from cycle/random nulls with terminal-structure match count `24`. | Still a finite toy; stronger inheritance doctrine needs broader carriers. |
| `source_locked_operator_base_packet` | VALID | Strict validator is green and source-fresh packet computes operator commutators, CPTP certificates, and noncommuting/commuting SMT controls. | None for base operator packet; consumers must cite exact rows. |
| `spinor_network_hopf_weyl_testbed` | VALID | Source-fresh all-three testbed computes Hopf/Weyl network rows, sign-erasure controls, SO(3) negatives, and SMT commutation checks. | No full spinor-network doctrine without surface consumers. |
| `terrain_exact_mirror_finder_v0` | VALID | Source-fresh packet finds no exact all-four O(3) mirror and preserves scoped family-local mirror facts with controls. | Does not imply terrain minimality/ranking. |
| `terrain_generator_sheet_packet` | SHALLOW | Source-fresh all-three terrain sheet is real, but it still carries `axis0_response`/static-proxy signs. | Patch Axis-0 response labels or add actual response-over-time measurement. |
| `terrain_operator_precedence_64_matrix` | VALID | Source-fresh all-three matrix computes 64 behavior rows, precedence degeneracy ladder, and label/erasure controls. | Keep as finite precedence matrix, not axis theorem. |
| `terrain_spinor_shell_nest_v0` | VALID | Source-fresh three-level terrain/spinor/shell nest consumes parent rows and computes shell leakage/readout controls. | No full many-qubit network theorem. |
| `terrain_weyl_spinor_lr_v0` | VALID | Source-fresh packet kills exact sigma-y mirror while preserving signed/time chirality diagnostics under scoped Weyl sheets. | No exact mirror law or terrain ranking. |
| `twistor_incidence_finite_packet_v0` | FAKE/BROKEN | Its baseline `mct_dynamic_admissibility_packet_v0_jax_results.json` hash is stale, blocking current-source reproducibility. | Refresh baseline hash/result and rerun finite twistor packet. |
| `winlose_pattern_derivation_discriminator` | SHALLOW | Source-fresh finite model-count work is real, but it retains b6 scaffold metadata, so law-style citation is provenance-moot. | Keep balance/outcome-coupling machinery; remove b6-law implications. |

## Optional And Probes

| surface | classification | evidence | upgrade |
|---|---|---|---|
| `system_v6/optional/catlab`, `nemo_hecke`, `ripserer`, `tensorkit` | tool-integration setup, not claims | Each contains only Julia `Project.toml`/`Manifest.toml`; no result claim is made there. | Treat as dependency surfaces; cite only with probe receipts. |
| `system_v6/probes/toolset_expansion_20260610_*` | tool-integration probes | Probe result JSONs record package availability/capability expansion, not scientific sim results. | Promote only when a packet consumes a probed API load-bearing. |
| `system_v6/probes/julia/julia_load_bearing_capability_probes.jl` + results | tool-integration probes | Results exist for `intervalarithmetic`, `differentialequations`, `symbolics`, `quaternions`, `cliffordalgebras`, and `z3`. | Keep as capability evidence; do not cite as claim evidence. |

## Ghost Citations

Filtered to cited sim-like packet names with no matching directory under `system_v6/sims/`:

| ghost citation | location | reading |
|---|---|---|
| `eng_carnot_axiswired` | `system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:59`; `system_v6/foundations/working_math_scaffold_20260609.md:153` | Cited as a result packet/probe, but no v6 sim dir exists; treat as legacy/tool-fit reference until a v6 packet is created or path is named. |
| `eng_szilard_axiswired` | `system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md:60`; `system_v6/foundations/working_math_scaffold_20260609.md:153` | Same: cited as result packet/probe, no v6 sim dir. |
| `ring_checkerboard_support` | `system_v6/foundations/working_math_scaffold_20260609.md:221` | Cited as a lego registry row, not a sim dir; the actual current sim-like candidate is `ring_checkerboard_support_graph_probe`, which exists. |
| `one_step_order_composition_witness_v0` | `system_v6/receipts/validity_audit_lane_b_engines_20260612.md:35,100` | Proposed rename target, no sim dir; not a completed packet. |
| `partial_one_step_family_membership_witness_v0` | `system_v6/receipts/validity_audit_lane_b_engines_20260612.md:36,101` | Proposed rename target, no sim dir; not a completed packet. |
| `one_step_precedence_witness_v0` | `system_v6/receipts/validity_audit_lane_b_engines_20260612.md:37,102` | Proposed rename target, no sim dir; not a completed packet. |
| `one_step_open_chain_qca_lr_rank_witness_v0` | `system_v6/receipts/validity_audit_lane_b_engines_20260612.md:71,103` | Proposed rename target, no sim dir; not a completed packet. |
| `one_step_render_layer_readout_witness_v0` | `system_v6/receipts/validity_audit_lane_b_engines_20260612.md:104` | Proposed rename target, no sim dir; not a completed packet. |

False positives excluded from the ghost list: receipt filenames in `receipts_index_20260612.md`, file stems such as `*_envelope_results`, and existing sim directories cited with suffixes.

## Top 3 Worst

1. `axis_triple_consistency_b6_v0/v1`: validators are green, but the b6 law is moot after `0313d47bc`; citing either as b6-law support would launder provenance-disowned doctrine.
2. `s8_local_information_table_v0` and `twistor_incidence_finite_packet_v0`: generic `all_pass` does not imply freshness; both have stale source/baseline hash evidence and must be rerun before current `VALID` citation.
3. `eng_carnot_axiswired` / `eng_szilard_axiswired`: foundations cite them as result/probe packets, but no `system_v6/sims/` directory exists, so later synthesis must either name the legacy path or create v6 packet directories.

## Boundary

No git staging or commit was performed. No packet result JSON was regenerated. This receipt is an audit receipt only and changes no classification registry by itself.
