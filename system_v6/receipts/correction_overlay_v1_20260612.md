# Correction Overlay v1 - Citation Seal (2026-06-12)

```yaml
receipt_kind: correction_overlay
status: binding_reading_overlay
claim_ceiling: correction_overlay_only
promotion_allowed: false
artifact_mutation: false
result_json_mutation: false
original_receipt_mutation: false
index_priority: first
write_scope: system_v6/receipts/correction_overlay_v1_20260612.md only
authority_inputs:
  owner_correction: 0313d47bc / owner_correction_axis0_not_built_20260612.md
  depth_audit: b4ee8f030 / static_shallowness_audit_20260612.md
  lane_b: 0abe953e2 / validity_audit_lane_b_engines_20260612.md
  lane_c: 53ae02357 / validity_audit_lane_c_doctrine_20260612.md
  codex_unlock_plan: 4142cecbe / codex_suggestions_unlock_plan_20260612.md
```

Bottom line: this overlay is the citation seal. Committed result JSONs and original receipts stay immutable/hash-pinned. Any conflicting earlier row must be read through this overlay first: current Axis-0 packets are static proxy/formula-taxonomy work, not built Axis-0; one-step packets keep their citable content but lose dynamic-response names; `b6=-b0*b3` is provenance-dead doctrine; `working_math_scaffold_20260609.md` and nearby foundation docs are usable only under the provenance classes below.

## 0. Binding Rules

1. This file changes readings, not artifacts. It does not rewrite result JSONs, source files, receipts, envelopes, hashes, or validator outputs.
2. If an earlier receipt, result, index row, or foundation line conflicts with this overlay, cite the earlier artifact only with this overlay's corrected reading.
3. The strongest allowed public status from this overlay is `correction_overlay_only`. Nothing here promotes a sim, axis, basin, bridge, engine, foundation relation, or doctrine claim.
4. Source tags in the tables below are binding provenance pointers, not reruns. `Lane B` means `0abe953e2`; `Lane C` means `53ae02357`; `Depth audit` means `b4ee8f030`; `Owner correction` means `0313d47bc`; `Codex plan` means `4142cecbe`.

## 1. Label Map

### 1.1 Global Stale Label Map

| Stale label or phrase | Corrected reading | Source lane finding |
|---|---|---|
| `axis0_plus_allo_response` | `static_axis0_proxy_positive_phi_gradient` | Lane B Axis-0 label patch pattern; Owner correction says no allostasis was measured. |
| `axis0_minus_homeostatic_response` | `static_axis0_proxy_negative_phi_gradient` | Lane B Axis-0 label patch pattern; Owner correction says no homeostasis was measured. |
| `minus_homeostatic_negative_feedback` | negative sign of the old static proxy field; read as `static_axis0_proxy_negative_phi_gradient`, not homeostasis | Lane B patch list plus Depth audit Axis-0 static-synthetic verdict. |
| `plus_allostatic_positive_feedback` and equivalent positive/allostatic sign labels | positive sign of the old static proxy field; read as `static_axis0_proxy_positive_phi_gradient`, not allostasis | Lane B patch pattern plus Owner correction. |
| `axis_readout_candidate_only` when attached to current Axis-0 packets | `static_proxy_readout_candidate_only - NOT a measurement of allostasis/homeostasis; Axis-0 remains unbuilt` | Owner correction re-scoped ceiling; Lane B repeats static-proxy risk. |
| `Axis-0 = the anchor alias class` | `old static proxy anchor alias class on the 33-cell carrier; not built Axis-0` | Lane B patch pattern; Owner correction central correction. |
| `Axis-0 response` in current packet-result citations | static-proxy sign/readout, unless a separate dynamic response packet is cited | Lane B Axis-0 patch list; Depth audit rule 1. |
| `Axis 0 response` in current packet-result citations | static-proxy sign/readout, unless a separate dynamic response packet is cited | Lane C stale-after-correction list; Owner correction. |
| `Axis-0 admission` in current Axis-0 estate packets | no Axis-0 admission; static proxy/formula taxonomy only | Owner correction; Lane B full classification table. |
| `THE Axis-0 readout` or `Axis-0 readout` for current Axis-0 estate | old static proxy readout on the 33-cell carrier; contender taxonomy only | Lane B label patch list; Lane C stale receipt corrections. |
| allostasis/homeostasis words inside owner-source semantic-target receipts | semantic target only; not evidence that the current Axis-0 packets measured the target | Lane C scaffold relation list preserves owner target but separates built static proxy. |
| `b6=-b0*b3`, `b_6=-b_0 b_3`, or `b_6 = -b_0 b_3` as doctrine | already-disowned scaffold artifact; keep only tested cover/topology machinery and Axis-6 precedence mechanics | Owner correction; Lane C scaffold relation list; Depth audit. |

### 1.2 Lane B File-By-File Label Corrections

Every file below is from Lane B's binding patch list, with current-tree glob expansion where Lane B named `results/*.json`.

| File | Offending string(s) | Corrected reading | Source lane finding |
|---|---|---|---|
| `system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_envelope_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `homeostatic` | Old static proxy sign/table; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_python_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `homeostatic` | Old static proxy sign/table; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v0/results/axis0_amendment_light_sweep_v0_validator_results.json` | family-level stale Axis-0 static-proxy naming under Lane B glob; no literal pattern hit in current file | Validator belongs to old static-proxy amendment family; cite only as validator over static-proxy formula taxonomy. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_envelope_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `homeostatic` | Entropy-candidate-vs-static-proxy sweep; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_jax_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `homeostatic` | Entropy-candidate-vs-static-proxy sweep; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_julia_results.json` | family-level stale Axis-0 static-proxy naming under Lane B glob; no literal pattern hit in current file | Julia mirror over static-proxy amendment family only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_validator_results.json` | family-level stale Axis-0 static-proxy naming under Lane B glob; no literal pattern hit in current file | Validator over static-proxy amendment family only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_envelope_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `Axis-0 readout`; `homeostatic` | Old static proxy contender sweep; no homeostasis; no Axis-0 admission/readout. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_jax_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 admission`; `homeostatic` | Old static proxy contender sweep; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_julia_results.json` | `Axis-0 admission` | Julia mirror binds old static-proxy contender table only; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_sweep_v0/results/axis0_contender_sweep_v0_validator_results.json` | family-level stale Axis-0 static-proxy naming under Lane B glob; no literal pattern hit in current file | Validator over old static-proxy contender sweep only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_envelope_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `Axis-0 readout`; `homeostatic` | Heavy formula taxonomy against old static proxy anchor; no homeostasis; no Axis-0 admission/readout. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_jax_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `homeostatic` | Heavy JAX mirror over old static proxy anchor alias class; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_julia_results.json` | `Axis-0 = the anchor alias class`; `Axis-0 admission` | Julia mirror over old static proxy anchor alias class; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_pytorch_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `homeostatic` | Heavy PyTorch mirror over old static proxy anchor alias class; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_contender_heavy_v0/results/axis0_contender_heavy_v0_validator_results.json` | `Axis-0 = the anchor alias class` | Validator sentence reads as old static proxy anchor alias class only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_envelope_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `homeostatic` | Co-survivor taxonomy against old static proxy anchor only; no homeostasis; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_jax_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `homeostatic` | JAX mirror over old static proxy co-survivor taxonomy only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_julia_results.json` | `Axis-0 = the anchor alias class`; `Axis-0 admission` | Julia mirror over old static proxy co-survivor taxonomy only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_pytorch_results.json` | `minus_homeostatic_negative_feedback`; `Axis-0 = the anchor alias class`; `Axis-0 admission`; `homeostatic` | PyTorch mirror over old static proxy co-survivor taxonomy only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_validator_results.json` | `Axis-0 = the anchor alias class` | Validator sentence reads as old static proxy anchor alias class only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `axis_readout_candidate_only`; `Axis-0 response`; `Axis-0 admission`; `Axis-0 readout`; `homeostatic` | Static synthetic field readout; `plus` -> `static_axis0_proxy_positive_phi_gradient`; `minus` -> `static_axis0_proxy_negative_phi_gradient`; no Axis-0 admission. | Lane B Axis-0 Label Patch List; Owner correction. |
| `system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_jax_results.json` | `axis_readout_candidate_only` | `static_proxy_readout_candidate_only`; no allostasis/homeostasis. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_julia_results.json` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `axis_readout_candidate_only`; `homeostatic` | Static synthetic field readout; `plus`/`minus` are phi-gradient signs only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_pytorch_results.json` | `axis_readout_candidate_only` | `static_proxy_readout_candidate_only`; no allostasis/homeostasis. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_validator_results.json` | family-level stale Axis-0 static-proxy naming under Lane B glob; no literal pattern hit in current file | Validator over static synthetic proxy field only. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_julia.jl` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `homeostatic` | Replace labels with static phi-gradient proxy names; DoF dynamics inherit proxy relativity. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/basin_dof_perturb_and_read_v0/results/basin_dof_perturb_and_read_v0_envelope_results.json` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `homeostatic` | Replace labels with static phi-gradient proxy names; finite graph rows remain formula-relative. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/basin_dof_perturb_and_read_v0/basin_dof_perturb_and_read_v0_envelope_spec.json` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `homeostatic` | Spec rows are static phi-gradient proxy polarity, not allostasis/homeostasis. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/basin_dof_perturb_and_read_v0/audit_verdict.md` | `axis0_minus_homeostatic_response`; `Axis-0 admission`; `Axis-0 readout`; `homeostatic` | Audit caveat becomes stronger: formula-relative static proxy readout only; no Axis-0 admission. | Lane B Axis-0 Label Patch List. |
| `system_v6/sims/discrete_axes12_pair_v0/results/discrete_axes12_pair_v0_envelope_results.json` | `axis0_plus_allo_response`; `axis0_minus_homeostatic_response`; `axis_readout_candidate_only`; `homeostatic` | Axis-0 columns are static proxy sign labels: positive/negative phi gradient, not response. | Lane B Axis One-Step Rename Requirements. |
| `system_v6/sims/discrete_axes12_pair_v0/audit_verdict.md` | `axis0_minus_homeostatic_response`; `axis_readout_candidate_only`; `homeostatic` | Axis-0 pair audit uses static proxy sign label only. | Lane B Axis One-Step Rename Requirements. |
| `system_v6/receipts/axis_work_order_20260612.md` | `allo/homeostatic`; `b6 = -b0*b3` | Axis-0 unbuilt; b6 law provenance-dead; topology/cover machinery reusable only. | Lane B patch list; Lane C stale-after-correction list. |
| `system_v6/receipts/axis0_contender_probe_registry_20260612.md` | `Axis-0 response`; `Axis-0 admission`; `Axis-0 readout`; `allostatic`; `homeostatic` | Registry becomes old static-proxy contender registry unless explicitly describing future dynamic target. | Lane B patch list; Lane C stale-after-correction list. |
| `system_v6/receipts/axis0_deep_vein_20260612.md` | `allostatic`; `homeostatic` where used as current built status | Source-mine semantic target only; current built Axis-0 estate did not measure it. | Lane B patch list; Lane C scaffold relation list. |
| `system_v6/receipts/axis0_deep_wave_sonnet_20260612.json` | `Axis-0 = the anchor alias class`; `axis_readout_candidate_only`; `Axis-0 response`; `Axis-0 admission`; `Axis-0 readout`; `allostatic`; `homeostatic` | Re-index as mixed external feed: owner semantic target separate from built static proxy. | Lane B patch list; Lane C stale-after-correction list. |
| `system_v6/receipts/axis3_contender_probe_registry_20260612.md` | `Axis-0 response` | Boundary comparators use current static-proxy/dynamic-rebuild terminology; no current Axis-0 response measurement. | Lane B patch list; Lane C stale-after-correction list. |
| `system_v6/receipts/axis6_contender_probe_registry_20260612.md` | `Axis-0 response` | Boundary comparators use current static-proxy/dynamic-rebuild terminology; no current Axis-0 response measurement. | Lane B patch list; Lane C stale-after-correction list. |
| `system_v6/receipts/axis_independence_mine_20260610.md` | `Axis-0 response`; `Axis 0 response`; `allostatic`; `homeostatic`; `b_6=-b_0 b_3` | Axis-0 rows are semantic target/static-proxy caveats only; b6 rows are dead as doctrine. | Lane B patch list; Lane C stale-after-correction list. |

## 2. Rename Map

These are citation names, not artifact renames. Original packet/result paths and hash-pinned contents remain unchanged.

| Old name / label | New citation name / corrected label | Original content unchanged? | Source lane finding |
|---|---|---:|---|
| `discrete_axis4_composition_v0` / Axis4 dynamic composition language | `one_step_order_composition_witness_v0` | yes | Lane B Axis One-Step Rename Requirements; Depth audit rule 2. |
| `discrete_axis5_family_partial_v0` / Axis5 family closure language | `partial_one_step_family_membership_witness_v0` or, for the family half, `one_step_operator_family_membership_witness_v0` | yes | Lane B Axis One-Step Rename Requirements; user binding instruction for codex plan #3. |
| `discrete_axis6_precedence_v0` / Axis6 product-law/precedence language | `one_step_precedence_witness_v0` | yes | Lane B Axis One-Step Rename Requirements; Owner correction disowns b6 law. |
| `ring_checkerboard_qca_v2` | `one_step_qca_open_chain_crossing_rank_witness_v0` | yes | Depth audit: QCA v2/v3 are one-step unitary/rank diagnostics. |
| `ring_checkerboard_qca_v3` | `one_step_open_chain_qca_lr_rank_witness_v0` | yes | Lane B Axis One-Step Rename Requirements. |
| `render_layer_readout_v1` | `one_step_render_layer_readout_witness_v0` | yes | Lane B Axis One-Step Rename Requirements. |
| `render_layer_readout_v0` if cited beyond predecessor status | `predecessor_degenerate_one_step_render_readout_v0` | yes | Depth audit downgrade list; Lane B classification table. |
| `ecd01_order_programmable_computer_v1` if cited as broad QIT engine dynamics | `bounded_margin_1_order_programmability_witness_v1` | yes | Lane B one clean positive; Depth audit rule 2 says one-step witness. |
| `ecd02_chiral_information_routing_v1` if cited as full chiral dynamics | `one_step_chiral_information_routing_death_diagnostic_v1` | yes | Lane B VALID bounded death; Depth audit one-step distribution pushforward. |
| `discrete_axes12_pair_v0` Axis-0 columns | `static_axis0_proxy_negative_phi_gradient` and `static_axis0_proxy_positive_phi_gradient` | yes | Lane B Axis One-Step Rename Requirements. |

## 3. Scaffold Provenance Overlay

This is the binding reading of `system_v6/foundations/working_math_scaffold_20260609.md` and nearby foundation docs. `owner-raw-source-verified` means Lane C spot-checked a cited raw/wiki source or found a direct owner quote inside the scoped file. `scaffold-only` means useful math/operationalization but not owner doctrine by itself. `already-disowned` means owner correction or later adjudication kills the relation as doctrine.

| Relation / equation | Source line(s) | Provenance class | Binding reading | Source lane finding |
|---|---|---:|---|---|
| `a=a iff a~b` | `working_math_scaffold_20260609.md:187,192`; `root_axioms_v0_1_DRAFT.md:9-17`; raw `MY INPUTS...:5-7` | owner-raw-source-verified | Raw owner relation; use as root pressure, not polished formal axiom without wording approval. | Lane C Scaffold Relation List. |
| `M(C) = { x : x is admissible under active constraint set C }` | `root_axioms_v0_1_DRAFT.md:57`; raw `constraint-manifold-architecture.md:23-44` | owner-raw-source-verified | Source upgrades to dynamic `M(C,t)` when update process matters; no manifold admission follows. | Lane C Scaffold Relation List. |
| `root constraints -> M(C) -> geometry on M(C) -> axes as A_i:M(C)->V_i -> carrier/readout/coupling/engine/bridge` | `root_axioms_v0_1_DRAFT.md:63-71`; raw `constraint-manifold-architecture.md:70-80` | owner-raw-source-verified | Valid build-order embargo; later receipts jumping to Axis-0/bridge/physics are stale. | Lane C Scaffold Relation List. |
| `B_n = (X_n, P_n, w_n, E_n, H_n, Q_n)` | `root_axioms_v0_1_DRAFT.md:75-83`; raw `field-wide-compression-geometry.md:34-68` | scaffold-only | Proposal-level field-wide bookkeeping object; not a built packet. | Lane C Scaffold Relation List. |
| `C_n : B_n -> B_{n+1}` | `root_axioms_v0_1_DRAFT.md:83`; raw `field-wide-compression-geometry.md:62-84` | scaffold-only | Proposal-level whole-field update object; must be packetized before use as result. | Lane C Scaffold Relation List. |
| `W_n = (X_n, P_n, E_n, H_n, Q_n, R_n, V_n)` | `root_axioms_v0_1_DRAFT.md:85`; raw `field-wide-compression-probe-contract.md:64-102` | scaffold-only | Valid contract shape for future packets, not a computation. | Lane C Scaffold Relation List. |
| Axis-0 as correlation persistence polarity under perturbation | `working_math_scaffold_20260609.md:264-276`; raw `axis-0-correlation-polarity.md:15-22` | owner-raw-source-verified / legacy-source | Semantic target is real source pressure; current built Axis-0 estate did not measure this. | Lane C Scaffold Relation List. |
| `H = C^2`; normalized spinor `psi in S^3` | `working_math_scaffold_20260609.md:27-33` | scaffold-only | Standard math carrier operationalization; not owner doctrine by itself. | Lane C Scaffold Relation List. |
| Density reduction `rho_s = psi_s psi_s^dagger` and explicit matrix | `working_math_scaffold_20260609.md:35-38` | scaffold-only | Standard QIT math; cite as model carrier math, not doctrine. | Lane C Scaffold Relation List. |
| Hopf projection `pi(psi)=psi^dagger sigma psi in S^2` | `working_math_scaffold_20260609.md:39` | scaffold-only | Standard Hopf/Bloch map; valid as math only. | Lane C Scaffold Relation List. |
| Nested torus `T_eta = {psi_s(phi,chi;eta)}` | `working_math_scaffold_20260609.md:41-45` | scaffold-only | Standard/operational carrier; ring-checkerboard mapping is separate source pressure. | Lane C Scaffold Relation List. |
| Weyl/chirality split `H_L=+H_0`, `H_R=-H_0` | `working_math_scaffold_20260609.md:49-51` | scaffold-only | Operationalization of L/R sheet; sign convention needs source/packet pin. | Lane C Scaffold Relation List. |
| Fiber loop `gamma_f^s(u)` and base loop `gamma_b^s(u)` | `working_math_scaffold_20260609.md:55-64` | scaffold-only | Useful Axis-3 placement formalization; not owner raw doctrine. | Lane C Scaffold Relation List. |
| Projectors `P_0,P_1,Q_+,Q_-` | `working_math_scaffold_20260609.md:66-73` | scaffold-only | Standard operator fixtures; valid only as carrier math. | Lane C Scaffold Relation List. |
| `Ti`, `Te`, `Fi`, `Fe` channel/operator formulas | `working_math_scaffold_20260609.md:70-75` | scaffold-only | Operational stage/operator definitions; packets must compute their behavior. | Lane C Scaffold Relation List. |
| Lindblad dissipator `D_L(rho)` and terrain laws | `working_math_scaffold_20260609.md:86-98` | scaffold-only | Assistant/standard formalization; use only with source-backed packet results. | Lane C Scaffold Relation List. |
| Count discipline `4 terrain families != 8 terrains != 16 placements != 64 states` | `working_math_scaffold_20260609.md:100-121` | scaffold-only with owner-process support | Good anti-collapse rule; exact 64 realization still must be computed. | Lane C Scaffold Relation List. |
| `L_A(rho)=A rho` and `R_A(rho)=rho A`; `Delta=Phi_tau(O(rho))-O(Phi_tau(rho))` | `working_math_scaffold_20260609.md:103-107` | scaffold-only | Valid Axis-6 candidate mechanics; separate from disowned b6 product law. | Lane C Scaffold Relation List. |
| Axis-0 `b_0=sign(cos 2eta)=sign(r_z)` | `working_math_scaffold_20260609.md:111` | scaffold-only | Geometric binarization only; post-owner-correction it is not built Axis-0. | Lane C Scaffold Relation List. |
| `Phi_0(rho_AB)=sum_r w_r I_c(A_r>B_r)` | `working_math_scaffold_20260609.md:111,177,179` | scaffold-only | Live candidate; Xi/rho_AB bridge remains open. | Lane C Scaffold Relation List. |
| Axis-4 `Phi_D=e^{tau_R L_R}e^{tau_C L_C}`, `Phi_I` reversed, trace-norm witness | `working_math_scaffold_20260609.md:115,165,177-181` | scaffold-only | Useful order/composition witness; one-step unless trajectory packet runs. | Lane C Scaffold Relation List. |
| Axis-5 entropy production / purity preservation witnesses | `working_math_scaffold_20260609.md:116` | scaffold-only | Operator-family witness only; no family closure. | Lane C Scaffold Relation List. |
| `b_6 = -b_0 b_3` | `working_math_scaffold_20260609.md:117`; `symbolic_layer...:28-31` | already-disowned | Owner never proposed it; cover tests put it at chance; strike as doctrine. | Lane C Scaffold Relation List; Owner correction. |
| Flux candidates and controls | `working_math_scaffold_20260609.md:123-127` | scaffold-only | Candidate current family; no final physical current selected. | Lane C Scaffold Relation List. |
| Higher carrier alternatives `C^2/S^3`, `Cl(6)`, `H/O`, spinor network, tensor network, `ijk` shell | `working_math_scaffold_20260609.md:133-147` | scaffold-only | Alternatives to preserve; none admitted by list membership. | Lane C Scaffold Relation List. |
| Dual-stack owner addendum | `working_math_scaffold_20260609.md:149-153` | owner-raw-source-verified for quote; scaffold-only for gloss | Owner quote supports dual-stacked Carnot/Szilard on spinor geometry; 720-cycle gloss remains testable reading. | Lane C Scaffold Relation List. |
| QIT-like engine definition and `Delta(rho)=Phi_D(Phi_I(rho))-Phi_I(Phi_D(rho))` | `working_math_scaffold_20260609.md:157-169` | scaffold-only | Operational test target; engine admission still blocked. | Lane C Scaffold Relation List. |
| Six controls for dual stack | `working_math_scaffold_20260609.md:181-183` | scaffold-only | Good packet contract; controls must fire in actual result. | Lane C Scaffold Relation List. |
| Ring-checkerboard / Mobius provenance claims | `working_math_scaffold_20260609.md:185-223` | owner-raw-source-verified for quoted provenance; scaffold-only for correspondences | Source chain is real; Hopf/Weyl/ring mapping remains candidate unless computed. | Lane C Scaffold Relation List. |
| Axis-0 family polarity `{Ne,Ni}` allostatic vs `{Se,Si}` homeostatic | `working_math_scaffold_20260609.md:264-276` | owner-raw-source-verified / standing-source | Semantic target; current Axis-0 estate remains unbuilt. | Lane C Scaffold Relation List. |
| Terrain/flux as geometry on `M(C,t)` | `working_math_scaffold_20260609.md:278-301`; raw `constraint-manifold-architecture.md:38-55` | scaffold-only with current-source support | Good current framing; still no final geometry/manifold admission. | Lane C Scaffold Relation List. |
| Three entropy columns never collapse; unitality numbers | `working_math_scaffold_20260609.md:303-309` | scaffold-only / computed-claim-needs-source | Cite exact terrain packet before authority use. | Lane C Scaffold Relation List. |
| Flux curvature `A=dphi+cos(2eta)dchi`, `F=dA=-2sin(2eta)deta^dchi`, `Phi=2pi(cos2eta1-cos2eta2)` | `working_math_scaffold_20260609.md:311` | scaffold-only | Standard curvature member; discriminator sim was in flight/not verified. | Lane C Scaffold Relation List. |
| Taijitu Axis-0 `b0=sign(cos 2eta)` and torus witness `q(theta1,theta2)` | `symbolic_layer...:14-16` | scaffold-only | Symbolic witness only; does not override Axis-0 bridge/open status. | Lane C Scaffold Relation List. |
| I Ching line-to-axis map | `symbolic_layer...:33-44` | scaffold-only | Proposal-only candidate map, not doctrine. | Lane C Scaffold Relation List. |
| Two loop orders `Se->Ne->Ni->Si` and `Se->Si->Ni->Ne` | `symbolic_layer...:89-96`; `two_engine_readout...:10-19` | owner-correction-embedded / valid readout grammar | Directed order grammar; check order separately from content. | Lane C Scaffold Relation List. |
| Expansion `4 -> 16 -> 64` by constrained placement | `two_engine_readout...:21-25` | scaffold-only | Structural target; no automatic 64 distinctness. | Lane C Scaffold Relation List. |

## 4. Receipt Corrections

These are Lane C's stale-after-correction rows committed as overlay corrections. Do not edit originals for this lane.

| Original surface | Stale claim | Binding one-line correction | Source lane finding |
|---|---|---|---|
| `working_math_scaffold_20260609.md:117` | `b_6=-b_0 b_3` as Axis-6 scaffold relation | Disowned scaffold artifact; keep only precedence mechanics `L_A/R_A` and `Phi_T O` vs `O Phi_T`. | Lane C Stale-After-Correction Overlay List. |
| `symbolic_layer_iching_taijitu_20260609.md:28-31` | Axis-6 symbolic row and directional table derive from b6 law | Strike b6-derived symbolic derivation; leave as proposal-only symbolic mapping. | Lane C Stale-After-Correction Overlay List. |
| `axis_work_order_20260612.md:1-27` | Axis-0 v0 earned and b6 consistency row staged | Axis-0 remains unbuilt; b6 law is provenance-dead and at-chance on tested covers. | Lane C Stale-After-Correction Overlay List. |
| `night_closeout_20260612_mass_spawn_wave.md` | Buildable 0-6 complete; Axis-0 contender program closed as Axis-0 | Re-read as old static-proxy/one-step witness estate complete at scratch ceilings only. | Lane C Stale-After-Correction Overlay List. |
| `axis0_contender_probe_registry_20260612.md` | The 33-cell anchor is the Axis-0 control | Anchor is a synthetic/static proxy, not Axis-0 measurement. | Lane C Stale-After-Correction Overlay List. |
| `axis0_registry_amendment_1_20260612.md` | Amendment candidates tested against old anchor as Axis-0 | Refile as static-proxy formula taxonomy. | Lane C Stale-After-Correction Overlay List. |
| `axis0_registry_final_state_supplement_20260612.md` | "Axis-0 family status... anchor alias class only" | "Old static-proxy anchor family status... alias class only." | Lane C Stale-After-Correction Overlay List. |
| `axis0_deep_wave_sonnet_20260612.json` | Several synthesis rows call the old family "Axis-0" and mix owner-source/sim-realization/llm elaboration | Re-index after owner correction; separate owner semantics from built static proxy. | Lane C Stale-After-Correction Overlay List. |
| `axis3_contender_probe_registry_20260612.md` | Axis-0 response keys appear as boundary comparators | Replace with current static-proxy/dynamic-Axis-0 terminology. | Lane C Stale-After-Correction Overlay List. |
| `axis6_contender_probe_registry_20260612.md` | Reads in the b6-law era and can be cited as product-law scaffold support | Use only operator/terrain precedence; no b6 product law. | Lane C Stale-After-Correction Overlay List. |
| `axis_independence_mine_20260610.md` | b6 scaffold consistency and Axis-0 independence framing | Mark b6 rows dead; Axis-0 rows static-proxy only. | Lane C Stale-After-Correction Overlay List. |
| `mct_pre_audit_checklist_20260610.md` | `axis0_status == readout_only_no_closure` sufficient fence | Add stronger `not built Axis-0; static proxy only unless dynamic response packet exists`. | Lane C Stale-After-Correction Overlay List. |
| `terrain_operator_map_20260609.md` | Axis-0 source map predates owner correction | Overlay dynamic allostasis/homeostasis target and reject static-anchor closure. | Lane C Stale-After-Correction Overlay List. |
| `doc_router_axes_terrains_operators_20260609.md` | Early router likely treats old axis/scaffold relations as current | Overlay `M(C,t)`, static-proxy Axis-0, and b6 disownment. | Lane C Stale-After-Correction Overlay List. |
| `math_geometry_test_map_20260609.md` | Bridge/Axis0 open language predates stronger owner correction | Reframe as dynamic manifold front-door first, not static Axis-0 candidate sweep. | Lane C Stale-After-Correction Overlay List. |
| `owner_doctrine_axes_as_existence_probes_20260612.md` | Expects Axis-0 readout survival/contender sweep as existence-grade path | Axis-0 contender sweep did not build Axis-0; existence probe requires dynamic response. | Lane C Stale-After-Correction Overlay List. |
| `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md` | Classical floor headline says earned before later definitional demotion | Cite transient SCC topology only; period 2/4 is implementation check. | Lane C Stale-After-Correction Overlay List. |
| `owner_prediction_64_subsubbasins_20260611.md` | 64-subsubbasin prediction as live target | Current joint results killed/narrowed the direct 64 reading; keep as source pressure only. | Lane C Stale-After-Correction Overlay List. |
| `physics_model_primary_deepread_20260612.md` | Quote authority for physics model | Already demoted; all consumed quotes require fresh verification or strike. | Lane C Stale-After-Correction Overlay List. |
| `receipts_index_20260612.md` | Some tiers omit latest audits or over-authorize stale rows | Add overlay index tier corrections; do not trust absent rows as non-citable if this lane created them. | Lane C Stale-After-Correction Overlay List. |

## 5. Index Hook

The receipts index should point to this file first.

Recommended index row:

```text
AUTHORITY_FIRST | correction_overlay_v1_20260612.md | binding correction overlay; supersedes conflicting rows in any earlier receipt, result JSON citation, foundation scaffold, or index tier; changes readings not artifacts; claim ceiling correction_overlay_only
```

Binding index rule:

- Before citing any pre-overlay Axis-0, Axis4/5/6, QCA v2/v3, render v1, ECD01/02-v1, b6, `working_math_scaffold`, foundations, or receipt-index row, check this overlay first.
- If the older row conflicts with this overlay, cite the older artifact as immutable historical evidence plus this overlay's corrected reading.
- Missing index rows for `static_shallowness_audit_20260612.md`, `validity_audit_lane_b_engines_20260612.md`, `validity_audit_lane_c_doctrine_20260612.md`, and this overlay are not non-citability evidence; they are index lag.

## 6. Verification / Hygiene

Fresh local checks used to build this overlay:

```text
git show --stat --oneline --decorate --no-renames 0313d47bc b4ee8f030 0abe953e2 53ae02357 4142cecbe
git show --format= --no-renames <authority_commit> -- <authority_receipt_path>
rg -l / rg -n over Lane B patch-list files for stale Axis-0/allostasis/homeostasis/anchor/b6 strings
rg -n over Lane C scaffold and stale-after-correction sections
git status --short
```

No git add, commit, rebase, push, result regeneration, receipt rewrite, or index mutation was performed.

## OVERLAY ADDENDUM 2 — commit-message overclaims caught by the full-state audit (2026-06-12)

The fresh-context full-state audit (gcm_climb_state_audit_20260612.md) flagged two of the
controller's own committed commit-message phrasings as exceeding their packets' audit
ceilings. The commits are immutable (never rewritten); the CORRECTED reading is binding:
- `0bafdec77` body "the two-loop split 2-vs-4 now LIVES on the manifold" -> CORRECTED:
  the runner verdict (0bc688808/0bafdec77 packets) is a SCRATCH CA run-surface on the
  carved object, carrier-and-pins-relative; NOT "the manifold", NOT runtime flux. Read
  "lives on the manifold" as "runs as a scratch CA surface on the candidate substrate".
- `81a982ea1` body "first runtime signature" -> CORRECTED: allowed ONLY as the scratch
  support-rank/chirality-INDEX result (the GNVW index, opposite L/R); NOT "the runtime
  flux family" (that is gcm_runtime_flux_3q_v0, still pending audit).
- `e7a56e517`/`dd8e96be7` "THE GATE TO RUNTIME FLUX" stands as GATE/INPUT wording only —
  never cite as flux-built.
Discipline reaffirmed: commit subjects are not audit verdicts; the audit_verdict.md ceiling
governs all downstream citation.
