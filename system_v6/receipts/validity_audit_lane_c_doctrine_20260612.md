# Deep Validity Audit - Lane C Doctrine / Receipts / Foundations (2026-06-12)

Bottom line: the doctrine layer is usable only with overlays. The worst leak is not a missing computation; it is provenance inflation: `working_math_scaffold_20260609.md` is front-mattered as owner-authored, but it contains mixed owner quotes, assistant glosses, Hermes wording, processed doctrine, and at least one owner-disowned scaffold relation. The centerpiece finding is that `b6 = -b0*b3` remains in two foundation docs and several downstream receipts even though `0313d47bc` disowns it as a scaffold artifact. The second large leak is stale Axis-0 language: several receipts still treat the old static 33-cell anchor family as Axis-0 rather than as static proxy formula taxonomy.

Claim ceiling: audit receipt only. No original receipt, foundation doc, result JSON, source doc, queue file, or git index was edited. Intended write scope was this file only.

## Shared Rubric Cited

- VALID: the result is computed from source, reproducible, controls fire for computed reasons, independently cross-audited or honestly labeled awaiting-audit, and the claim's name matches what was actually measured. Honest negatives, nulls, and deaths are valid.
- SHALLOW: real computation but the claim exceeds the measurement. Species include static/synthetic fields wearing measurement names, one-step witnesses wearing response/dynamics names, formula taxonomy wearing family-closure names, decorative tools, thin or unfair baselines, carrier-relative results cited carrier-free, pre-G.2a contract gaps, and results resting on provenance-disowned doctrine.
- FAKE/BROKEN: not reproducible from current source, hardcoded or echoed values presented as computed, claims with no computation behind them, red validators cited as green, quote fabrication, or decorative SMT asserting literals.

Built on, not redone: `b4ee8f030` static-shallowness audit, `b891e0611` Hermes scorecard, `0313d47bc` owner correction, and `276d42d81` receipts-index addendum.

## Fresh Audit Work

- Scope found: 142 files under `system_v6/receipts/`, five non-xlsx files under `system_v6/foundations/`, one source xlsx under foundations, `system_v6/README.md`, and no `system_v6/docs/` directory.
- Key current anchors read: `owner_correction_axis0_not_built_20260612.md`, `static_shallowness_audit_20260612.md`, `receipts_index_20260612.md`, `ecd_registry_supplement_1_20260612.md`, `axis_work_order_20260612.md`, `validity_audit_lane_b_engines_20260612.md`, `hermes_audit_forwarded_20260612.md`, and the foundation docs.
- Spot raw-source checks performed for the root and construction formulas: `MY INPUTS on Retrocausality.md:5-7`, `constraint-manifold-architecture.md:23-44,58-80`, `field-wide-compression-geometry.md:24-68`, `field-wide-compression-probe-contract.md:64-102`, and `axis-0-correlation-polarity.md:15-22`.
- No sim or result JSON was regenerated in this lane. This is a document validity/provenance audit, not a computation rerun.

## Scope Classification Summary

| Surface | Class | One-sentence evidence | Upgrade to VALID |
|---|---:|---|---|
| `system_v6/README.md` | VALID | The contract preserves re-earn-status, source/provenance discipline, no-v6-docs rule, and fenced Axis-0/bridge/physics status after the front-door refresh. | No upgrade needed; keep it current at closeouts. |
| `root_axioms_v0_DRAFT.md` | SHALLOW | It is honestly marked draft, but it is superseded by v0.1 and has the weaker pre-dynamic `M(C)` boundary. | Retire behind v0.1 or mark predecessor-only. |
| `root_axioms_v0_1_DRAFT.md` | VALID | The root claims are labeled owner quote vs assistant gloss, cite raw/wiki sources, and preserve draft/no-admission status. | Verify every quoted source line before using it as owner-facing canonical wording. |
| `two_engine_readout_automaton_20260609.md` | VALID | It cleanly names the two-component word, active-loop read rule, and directed order without promoting I Ching or payoff claims. | Add source-line anchors if this becomes authority beyond readout grammar. |
| `symbolic_layer_iching_taijitu_20260609.md` | SHALLOW | It fences symbolic status, but still includes `b6=-b0*b3` as the Axis-6 symbolic table and derives an up/down table from it. | Overlay: strike the b6-derived rows; preserve only symbolic/I Ching placement as proposal. |
| `working_math_scaffold_20260609.md` | SHALLOW | It is front-mattered as owner-authored, but line-level content mixes owner quotes, assistant glosses, Hermes wording, and the disowned `b_6=-b_0 b_3` relation. | Split owner quotes, standard math, assistant operationalization, Hermes proposal, and disowned scaffold rows into separate provenance classes. |
| `foundations/sources/Personality_theory_original_rosetta_preAI.xlsx` | VALID | The xlsx is a preserved primary artifact; this audit did not inspect workbook cells directly and relies on the transcription receipt for details. | Direct workbook spot-check before using any individual cell quote. |

## Scaffold Relation List

This is the owner-needed list of specific relation/equation surfaces found in the foundation docs. `owner-raw-source-verified` here means a cited raw/wiki source was spot-checked in this lane or the line is a direct owner quote inside the scoped file. `scaffold-only` means useful math or operationalization, but not owner doctrine by itself. `already-disowned` means the owner correction or later adjudication kills the relation as doctrine.

| Relation / equation | Source line(s) | Provenance class | Evidence and current ceiling |
|---|---|---:|---|
| `a=a iff a~b` | `working_math_scaffold_20260609.md:187,192`; `root_axioms_v0_1_DRAFT.md:9-17`; raw `MY INPUTS...:5-7` | owner-raw-source-verified | Raw owner text contains the relation; use as root pressure, not as a polished formal axiom without wording approval. |
| `M(C) = { x : x is admissible under active constraint set C }` | `root_axioms_v0_1_DRAFT.md:57`; raw `constraint-manifold-architecture.md:23-44` | owner-raw-source-verified | Current source upgrades it to dynamic `M(C,t)` when update process matters; no manifold admission follows. |
| `root constraints -> M(C) -> geometry on M(C) -> axes as A_i:M(C)->V_i -> carrier/readout/coupling/engine/bridge` | `root_axioms_v0_1_DRAFT.md:63-71`; raw `constraint-manifold-architecture.md:70-80` | owner-raw-source-verified | Valid build-order embargo; later receipts that jump to Axis-0/bridge/physics are stale. |
| `B_n = (X_n, P_n, w_n, E_n, H_n, Q_n)` | `root_axioms_v0_1_DRAFT.md:75-83`; raw `field-wide-compression-geometry.md:34-68` | scaffold-only | Proposal-level field-wide bookkeeping object over owner compression wording; not a built packet. |
| `C_n : B_n -> B_{n+1}` | `root_axioms_v0_1_DRAFT.md:83`; raw `field-wide-compression-geometry.md:62-84` | scaffold-only | Proposal-level whole-field update object; must be packetized before use as result. |
| `W_n = (X_n, P_n, E_n, H_n, Q_n, R_n, V_n)` | `root_axioms_v0_1_DRAFT.md:85`; raw `field-wide-compression-probe-contract.md:64-102` | scaffold-only | Valid contract shape for future packets, not a computation. |
| Axis-0 as correlation persistence polarity under perturbation | `working_math_scaffold_20260609.md:264-276`; raw `axis-0-correlation-polarity.md:15-22` | owner-raw-source-verified / legacy-source | The semantic target is real source pressure; current built Axis-0 estate did not measure this. |
| `H = C^2`; normalized spinor `psi in S^3` | `working_math_scaffold_20260609.md:27-33` | scaffold-only | Standard math carrier operationalization; not owner doctrine by itself. |
| Density reduction `rho_s = psi_s psi_s^dagger` and explicit matrix | `working_math_scaffold_20260609.md:35-38` | scaffold-only | Standard QIT math; cite as model carrier math, not doctrine. |
| Hopf projection `pi(psi)=psi^dagger sigma psi in S^2` | `working_math_scaffold_20260609.md:39` | scaffold-only | Standard Hopf/Bloch map; valid as math only. |
| Nested torus `T_eta = {psi_s(phi,chi;eta)}` | `working_math_scaffold_20260609.md:41-45` | scaffold-only | Standard/operational carrier; ring-checkerboard mapping is separate source pressure. |
| Weyl/chirality split `H_L=+H_0`, `H_R=-H_0` | `working_math_scaffold_20260609.md:49-51` | scaffold-only | Operationalization of L/R sheet; owner-source supports L/R engines, but the sign convention itself needs source/packet pin. |
| Fiber loop `gamma_f^s(u)` and base loop `gamma_b^s(u)` | `working_math_scaffold_20260609.md:55-64` | scaffold-only | Useful Axis-3 placement formalization; not owner raw doctrine. |
| Projectors `P_0,P_1,Q_+,Q_-` | `working_math_scaffold_20260609.md:66-73` | scaffold-only | Standard operator fixtures; valid only as carrier math. |
| `Ti`, `Te`, `Fi`, `Fe` channel/operator formulas | `working_math_scaffold_20260609.md:70-75` | scaffold-only | Operational stage/operator definitions; packets must compute their behavior. |
| Lindblad dissipator `D_L(rho)` and terrain laws | `working_math_scaffold_20260609.md:86-98` | scaffold-only | Assistant/standard formalization of terrain families; use only with source-backed packet results. |
| Count discipline `4 terrain families != 8 terrains != 16 placements != 64 states` | `working_math_scaffold_20260609.md:100-121` | scaffold-only with owner-process support | Good anti-collapse rule; exact 64 realization still must be computed. |
| `L_A(rho)=A rho` and `R_A(rho)=rho A`; `Delta=Phi_tau(O(rho))-O(Phi_tau(rho))` | `working_math_scaffold_20260609.md:103-107` | scaffold-only | Valid Axis-6 candidate mechanics; separate from disowned b6 product law. |
| Axis-0 `b_0=sign(cos 2eta)=sign(r_z)` | `working_math_scaffold_20260609.md:111` | scaffold-only | Geometric binarization only; post-`0313d47bc` it is not built Axis-0. |
| `Phi_0(rho_AB)=sum_r w_r I_c(A_r>B_r)` | `working_math_scaffold_20260609.md:111,177,179` | scaffold-only | Live candidate; Xi/rho_AB bridge remains open. |
| Axis-4 `Phi_D=e^{tau_R L_R}e^{tau_C L_C}`, `Phi_I` reversed, trace-norm witness | `working_math_scaffold_20260609.md:115,165,177-181` | scaffold-only | Useful order/composition witness; one-step unless a trajectory packet runs. |
| Axis-5 entropy production / purity preservation witnesses | `working_math_scaffold_20260609.md:116` | scaffold-only | Valid as operator-family witness only; no family closure. |
| `b_6 = -b_0 b_3` | `working_math_scaffold_20260609.md:117`; `symbolic_layer...:28-31` | already-disowned | Owner correction `0313d47bc` says the owner never proposed it; cover tests also put it at chance. Strike as doctrine. |
| Flux candidates and controls | `working_math_scaffold_20260609.md:123-127` | scaffold-only | Candidate current family; no final physical current selected. |
| Higher carrier alternatives `C^2/S^3`, `Cl(6)`, `H/O`, spinor network, tensor network, `ijk` shell | `working_math_scaffold_20260609.md:133-147` | scaffold-only | Alternatives to preserve; none admitted by list membership. |
| Dual-stack owner addendum | `working_math_scaffold_20260609.md:149-153` | owner-raw-source-verified for quote; scaffold-only for gloss | Owner quote supports dual-stacked Carnot/Szilard on spinor geometry; 720-cycle gloss remains testable reading. |
| QIT-like engine definition and `Delta(rho)=Phi_D(Phi_I(rho))-Phi_I(Phi_D(rho))` | `working_math_scaffold_20260609.md:157-169` | scaffold-only | Operational test target; engine admission still blocked. |
| Six controls for dual stack | `working_math_scaffold_20260609.md:181-183` | scaffold-only | Good packet contract; controls must fire in actual result. |
| Ring-checkerboard / Mobius provenance claims | `working_math_scaffold_20260609.md:185-223` | owner-raw-source-verified for quoted provenance; scaffold-only for correspondences | Source chain is real; mapping to Hopf/Weyl/ring geometry remains candidate unless computed. |
| Axis-0 family polarity `{Ne,Ni}` allostatic vs `{Se,Si}` homeostatic | `working_math_scaffold_20260609.md:264-276` | owner-raw-source-verified / standing-source | This is the semantic target; current Axis-0 estate remains unbuilt. |
| Terrain/flux as geometry on `M(C,t)` | `working_math_scaffold_20260609.md:278-301`; raw `constraint-manifold-architecture.md:38-55` | scaffold-only with current-source support | Good current framing; still no final geometry/manifold admission. |
| Three entropy columns never collapse; unitality numbers | `working_math_scaffold_20260609.md:303-309` | scaffold-only / computed-claim-needs-source | Useful, but should cite exact terrain packet before authority use. |
| Flux curvature `A=dphi+cos(2eta)dchi`, `F=dA=-2sin(2eta)deta^dchi`, `Phi=2pi(cos2eta1-cos2eta2)` | `working_math_scaffold_20260609.md:311` | scaffold-only | Standard curvature member; scaffold itself says discriminator sim was in flight/not verified. |
| Taijitu Axis-0 `b0=sign(cos 2eta)` and torus witness `q(theta1,theta2)` | `symbolic_layer...:14-16` | scaffold-only | Symbolic witness only; does not override Axis-0 bridge/open status. |
| I Ching line-to-axis map | `symbolic_layer...:33-44` | scaffold-only | Explicit proposal-only; valid as candidate map, not doctrine. |
| Two loop orders `Se->Ne->Ni->Si` and `Se->Si->Ni->Ne` | `symbolic_layer...:89-96`; `two_engine_readout...:10-19` | owner-correction-embedded / valid readout grammar | Use as directed order grammar; check order separately from content. |
| Expansion `4 -> 16 -> 64` by constrained placement | `two_engine_readout...:21-25` | scaffold-only | Good structural target; no automatic 64 distinctness. |

## Receipt Classification Table

| Receipt | Class | One-sentence evidence | Upgrade to VALID |
|---|---:|---|---|
| `advisory_gemini31pro_open_math_20260609.md` | VALID | Advisory math response, not authority. | Use only as cite-or-discard input. |
| `advisory_grok43_open_math_20260609.md` | VALID | Advisory counterpart with no promotion surface. | Use only with independent source/math checks. |
| `altviews_capability_and_surface_miss_20260612.md` | VALID | Verbatim alt-view advisory over capability/surface miss, not doctrine. | Promote nothing; consume as adversarial input. |
| `attractor_basin_criterion_20260611.md` | SHALLOW | Defines useful basin criteria, but later static/depth audits require exact finite `S`, `R_C`, basin partition, and escape evidence before basin language. | Overlay the stricter basin-contract fields on every citation. |
| `audit_bar_calibration_20260610.md` | VALID | Process/audit-bar calibration, not a result claim. | None; keep as process authority. |
| `audit_standards_codex_v1.md` | SHALLOW | Process authority predates `0313d47bc`; Axis-0 and b6 audit examples need post-correction language. | Add overlay for static-proxy Axis-0 and disowned b6. |
| `axes12_deep_vein_20260612.md` | VALID | Deep-vein planning/source map only. | Verify raw owner quotes before authority use. |
| `axes45_deep_vein_20260612.md` | VALID | Deep-vein planning/source map only. | Verify raw source quotes before authority use. |
| `axis0_contender_probe_registry_20260612.md` | SHALLOW | Its registry is real, but its anchor is now re-scoped by `0313d47bc` to static proxy formula taxonomy, not Axis-0. | Rename as old-static-proxy contender registry or overlay every Axis-0 readout phrase. |
| `axis0_deep_vein_20260612.md` | SHALLOW | Same-file reclassification demotes NOT-CANON Axis-0 rough quotes behind raw owner sources. | Use only after raw-source verification; strike Section A as authority. |
| `axis0_deep_wave_sonnet_20260612.json` | SHALLOW | Useful external feed, but it contains stale "Axis-0 family/anchor alias" language and mixed provenance classes after the owner correction. | Re-index with post-`0313d47bc` provenance and static-proxy labels. |
| `axis0_registry_amendment_1_20260612.md` | SHALLOW | Amendment inherits the old static anchor frame. | Overlay static-proxy ceiling and rerun any future registry under dynamic Axis-0 criteria. |
| `axis0_registry_final_state_supplement_20260612.md` | SHALLOW | It closes the old 33-cell contender family, but calls the family Axis-0 after the owner says Axis-0 was not built. | Relabel as old static-proxy anchor alias class only. |
| `axis3_contender_probe_registry_20260612.md` | SHALLOW | Registry is useful, but its distinction-boundary language still references stale Axis-0 response rows. | Replace Axis-0 terms with static-proxy or dynamic-rebuild terms as appropriate. |
| `axis6_contender_probe_registry_20260612.md` | SHALLOW | Registry is useful, but its source context includes the disowned b6-law era. | Keep precedence mechanics; strike product-law implications. |
| `axis_independence_mine_20260610.md` | SHALLOW | Useful source mine, but b6 scaffold consistency and Axis-0 independence language are stale after `0313d47bc`. | Overlay b6 disownment and static-proxy Axis-0 wording. |
| `axis_work_order_20260612.md` | SHALLOW | It records later b6 at-chance/L(3,1) corrections, but the opening table still treats Axis-0 as earned and b6 as staged consistency row. | Add overlay: Axis-0 unbuilt; b6 law provenance-dead, topology machinery reusable. |
| `canon_algebra_artifact_v1_results_20260610.json` | VALID | JSON carries scratch ceiling/no admission and bounded algebra artifact status. | Source-lock before numeric reuse. |
| `capability_matrix_v0_20260609.md` | VALID | Capability matrix/planning surface only. | Refresh package statuses before current claims. |
| `capability_triage_20260610.md` | VALID | Bounded hygiene triage with no result promotion. | None beyond current package reruns. |
| `carnot_szilard_basin_map_20260612.md` | VALID | Correspondence map declares no packet built and no promotion; later basin-cycle packet carries earned rows. | Cite with `carnot_szilard_basin_cycle_v0` for computed claims. |
| `cfr_advisory_crosscheck_20260610.md` | VALID | Advisory cross-check material. | Use only as independent expectation/check input. |
| `cfr_blind_expected_20260610.md` | VALID | Blind expected-values receipt with scratch ceilings. | Compare against fresh packet output before citation. |
| `cfr_pre_audit_checklist_20260610.md` | VALID | Checklist, not result. | None. |
| `cfr_preflight_20260610.md` | VALID | Preflight result only. | Rerun preflight if packet source changed. |
| `coupling_law_family_table_20260611.md` | VALID | Explicitly separates owner-source, sim-realization, and llm-elaboration; candidate table only. | Verify individual source rows when consumed. |
| `coupling_law_mining_raw_20260611.json` | VALID | Raw mined feedstock with provenance classes. | Reverify quoted raw paths before doctrine use. |
| `cross_model_anchor_recompute_20260610.md` | VALID | Advisory cross-check/no promotion. | Fresh recompute before current authority. |
| `cross_model_anchor_recompute_panel2_20260610.md` | VALID | Advisory panel only. | Fresh source check before authority use. |
| `cross_model_anchor_recompute_panel3_20260610.md` | VALID | Pre-registration advisory. | Consume only against packet results. |
| `cross_model_anchor_recompute_panel5_20260610.md` | VALID | Pre-registration advisory. | Consume only against packet results. |
| `cross_model_anchor_recompute_panel6_20260611.md` | VALID | Pre-registration advisory. | Consume only against packet results. |
| `cross_model_anchor_recompute_panel6_20260612.md` | SHALLOW | It pre-registers a b6 sign convention after b6 is already suspect; later owner correction kills doctrine provenance. | Keep non-b6 panel targets; strike b6 as doctrine. |
| `cross_model_anchor_recompute_panel7_20260612.md` | VALID | Basin/Landauer blind panel used as advisory expectations. | Cite only with earned basin-cycle rows. |
| `cross_model_anchor_recompute_panel8_20260612.md` | SHALLOW | b6 falsifiability baselines are useful for dead-law archaeology, not live doctrine. | Refile as disowned-law negative-control note. |
| `day_integration_report_20260609.md` | SHALLOW | Strong integration ledger, but sections on b6/Axis-0/source status predate later correction. | Overlay post-`0313d47bc` and b6 disownment. |
| `density_matrix_as_quotient_doctrine_20260610.md` | VALID | Assistant-consolidation is labeled, owner root axiom is isolated, and no promotion is claimed. | Fresh source-line audit before canonical wording. |
| `desktop_checkout_audit_forwarded_20260612.md` | VALID | Advisory only; explicitly not canon for active checkout. | None; do not cite as active-checkout result. |
| `doc_router_axes_terrains_operators_20260609.md` | SHALLOW | Useful router but pre-correction Axis-0 and b6 routes are stale. | Add overlay for static-proxy Axis-0 and dead b6. |
| `dualstack_rebuild_mine_20260610.md` | VALID | Read-lane rebuild prep only. | Build/rerun before result claims. |
| `dynamic_manifold_upgrade_design_20260612.md` | VALID | Correctly defines dynamic rebuild target after owner correction, not sim evidence. | Implement and audit the dynamic chart. |
| `ecd_registry_supplement_1_20260612.md` | VALID | Current ECD adjudication scoreboard is explicit, bounded, and cross-audited; only ECD.01 survives. | Refresh source hashes for packet-local validators where lane B found drift. |
| `engine_capability_differentiators_20260612.md` | VALID | Planning registry for capability candidates. | Consume supplement for adjudicated results. |
| `env_redundancy_report_20260609.md` | VALID | Environment/dependency convention report only. | Refresh if env changes. |
| `estate_convention_ledger_20260610.md` | VALID | Convention ledger; no promotion by itself. | Refresh source locks before numeric citation. |
| `estate_lineage_remediation_20260610.md` | VALID | Lineage remediation tracker. | Revalidate referenced hashes before use. |
| `estate_value_reconciliation_20260610.md` | VALID | Reconciliation report with bounded rows. | Recompute exact values if cited. |
| `estate_value_reconciliation_v2_20260610.md` | VALID | Late-wave reconciliation with caveats. | Recompute exact values if cited. |
| `evening_mining_estate_s11_20260611.json` | VALID | Mining feedstock with provenance classes and open decisions. | Reverify raw owner decision rows before authority use. |
| `geometry_program_status_20260611.md` | SHALLOW | Useful status table, but "program status" can over-authorize without source/hash refresh and static-shallowness overlays. | Overlay lane-B and static-shallowness results. |
| `geometry_sim_program_canonical_20260610.md` | VALID | Canonical program receipt clearly fences scratch/no admission status. | Keep order current with later M(C,t) front-door correction. |
| `hermes_audit_forwarded_20260612.md` | VALID | Advisory Hermes scorecard with concrete findings verified/routed locally. | Use only its verified findings as live fix lanes. |
| `hermes_suggestion_dynamic_chart_20260612.md` | VALID | Advisory suggestion explicitly resolved as mid-build snapshot. | None. |
| `holodeck_model_deepread_20260612.md` | VALID | Deepread preserves provenance classes and fences proposal-level material. | Verify raw quotes before doctrine receipt use. |
| `iching_engine_symmetry_match_20260612.md` | VALID | Research-lane receipt; no sim/result promotion. | Build finite comparison before claims. |
| `lifted_ladder_spec_20260610.md` | VALID | Spec/read-lane only. | Build packet and audit. |
| `m64_blind_expected_20260610.md` | VALID | Blind expected-values pre-registration. | Compare against packet output. |
| `m64_pre_audit_checklist_20260610.md` | VALID | Outcome-blind checklist. | None. |
| `math_geometry_test_map_20260609.md` | SHALLOW | Useful map, but recent docs and owner correction lower several Axis-0/bridge readings. | Overlay recent-docs delta and owner correction. |
| `matrix64_mine_20260610.md` | VALID | Mine-first receipt, no build. | Build and audit before result claims. |
| `mct_advisory_crosscheck_20260610.md` | VALID | Advisory crosscheck with divergences preserved. | Consume only with packet result comparison. |
| `mct_advisory_gemini31pro_20260610.md` | VALID | Advisory response. | Cite/discard by source-backed checks. |
| `mct_advisory_gemini35flash_20260610.md` | VALID | Advisory response. | Cite/discard by source-backed checks. |
| `mct_advisory_grok43_20260610.md` | VALID | Advisory response. | Cite/discard by source-backed checks. |
| `mct_blind_expected_20260610.md` | VALID | Blind expected-values receipt. | Compare against packet output. |
| `mct_draft_gemini31_20260609.md` | VALID | Outside-model draft/proposal. | Use only as design fuel. |
| `mct_draft_grok43_20260609.md` | VALID | Outside-model draft/proposal. | Use only as design fuel. |
| `mct_mine_adjudication_20260610.md` | VALID | Mine/adjudication report, not build. | Build packet for claims. |
| `mct_pre_audit_checklist_20260610.md` | SHALLOW | Checklist includes pre-correction `axis0_status` readout-only language. | Update Axis-0 checks to static-proxy vs dynamic-rebuild distinction. |
| `mct_preflight_20260610.md` | VALID | Preflight only. | Rerun if source changed. |
| `mct_reconciled_spec_20260609.md` | VALID | Formal probe plan with scratch ceiling. | Build current M(C,t) packet. |
| `mct_wiki_source_map_20260610.md` | VALID | Source map, not result. | Reverify quoted lines before build card use. |
| `missing_things_audit_20260610.md` | VALID | Read-lane audit receipt; useful negative/absence discipline. | Refresh against current tree before absence claims. |
| `model_state_audit_20260611.md` | SHALLOW | State audit predates later correction wave and should not carry current authority alone. | Overlay lane-B, b6, ECD, and Axis-0 corrections. |
| `nested_ratchet_support/nr_assets_report.md` | VALID | Asset inventory only. | Use with fresh audit verdict for result claims. |
| `nested_ratchet_support/nr_expected_values.md` | VALID | Independent expected values. | Compare against actual runs. |
| `nested_ratchet_support/nr_fresh_audit_verdict.md` | VALID | Fresh verdict labels GENUINE-WITH-CAVEATS. | Keep caveats attached. |
| `nested_ratchet_support/nr_preaudit.md` | VALID | Pre-audit checklist. | None. |
| `nesting_advisory_crosscheck_20260610.md` | VALID | Advisory crosscheck. | Use only with audited nesting law. |
| `nesting_law_audit_20260610.md` | VALID | Deep audit kills/repairs draft claims against standard math. | Use `nesting_law_audited` as current merge. |
| `nesting_law_audited_20260610.md` | VALID | Merged audited nesting law is bounded and says no promotion/doctrine beyond cited math. | Keep standard-math caveats attached. |
| `night_closeout_20260612_mass_spawn_wave.md` | SHALLOW | Strong closeout, but it says buildable 0-6 complete and Axis-0 contender closed before the owner correction re-scoped Axis-0. | Overlay owner correction: old axis work complete only at static/proxy/witness ceilings. |
| `nonassoc_math_map_20260609.md` | VALID | Exploration map, not admission. | Build bounded packets for claims. |
| `octonion_orientation_reconciliation_20260610.md` | VALID | Convention reconciliation. | Keep as convention guard only. |
| `old_estate_mine_20260611.md` | VALID | Old-estate mining with partial status. | Reverify consumed items before build. |
| `old_sims_axis_variants_20260612.md` | VALID | Inventory plus proposed registry amendments only. | Promote only through registry/build packets. |
| `old_sims_complete_consume_20260612.md` | VALID | Complete consume table/feedstock only. | Verify individual source rows before consumption. |
| `owner_correction_axis0_not_built_20260612.md` | VALID | Binding owner correction with direct owner quote and precise re-scoping. | None; this is a current authority anchor. |
| `owner_doctrine_axes_7_12_and_engine_capability_20260612.md` | VALID | Owner-voice doctrine plus research question; no packet result. | Build capability packets under ECD/equalizer discipline. |
| `owner_doctrine_axes_as_existence_probes_20260612.md` | SHALLOW | Useful program doctrine, but pre-correction text expects Axis-0 readout survival and DoF test framing too soon. | Overlay Axis-0 unbuilt and dynamic-probe requirement. |
| `owner_doctrine_carnot_szilard_connection_20260612.md` | VALID | Doctrine plus computed v0 adjudication with explicit boundaries. | Cite only typed-counting mechanics, not heat/work physics. |
| `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md` | SHALLOW | It preserves corrections, but earlier adjudication text says v0 "earns" the classical floor before the same-file definitionally-forced demotion. | Cite only corrected SCC/transient-topology and later QCA caveats. |
| `owner_doctrine_entropy_type_ratchet_20260611.md` | VALID | Same-file corrections narrow v1/v2 scope and bottom out the regress honestly. | Cite only the permanent earned scope, not free discovery. |
| `owner_doctrine_holodeck_render_layer_20260612.md` | VALID | Kernel provenance is fenced and adjudication narrows render to its own readout family. | Use render v1 caveats for ECD.06 consumption. |
| `owner_doctrine_spinor_network_surface_20260611.md` | VALID | Same-file corrections demote v1/v2 and preserve v3 partial pre-registered rise. | Cite only v3 partial family-cell identity evidence. |
| `owner_prediction_64_subsubbasins_20260611.md` | SHALLOW | Prediction receipt is useful, but current basin/joint packets killed or narrowed several 64-subbasin readings. | Overlay joint v2/v3/v4 and lane-B negative statuses. |
| `panel9_blind_altviews_wave_targets_20260612.md` | VALID | Blind panel pre-registration only. | Consume only with packet adjudications. |
| `physics_model_primary_deepread_20260612.md` | FAKE/BROKEN | Same-file demotion says multiple quoted anchors do not verify and one source file path was not found at a checkable path. | Fresh source-quote verification; strike unverified quotes before any packet consumes them. |
| `post_demotion_sweep_audit_20260611.md` | VALID | Freshness/demotion audit. | Refresh after new demotions. |
| `program_plan_factory_20260611.md` | VALID | Process/factory plan, not result. | Keep Hermes as suggestion only. |
| `promotion_checklist_super_sim_v0_20260612.md` | SHALLOW | Mechanical eligibility is useful, but `ELIGIBLE_BY_CRITERION` can be misread as promotion despite owner-gated ceiling. | Rename/overlay as mechanical checklist only; no classification/admission change. |
| `qubit_ladder_engine_loop_pressure_20260610.md` | VALID | Read-only conceptual pressure receipt with no promotion. | Build discriminators before claims. |
| `receipts_index_20260612.md` | SHALLOW | Current-state addendum helps, but several AUTHORITY tiers need correction after `0313d47bc`, b6 disownment, and same-file demotions. | Add a tier overlay table; do not edit original rows in this lane. |
| `recent_docs_delta_20260609.md` | VALID | Delta report already lowers ceilings and sharpens build order. | Update with owner correction if cited today. |
| `ring_checkerboard_provenance_20260611.md` | VALID | Provenance mining distinguishes owner-source, LLM formalization, and build card scope. | Verify source lines when consumed. |
| `ring_checkerboard_support_mine_20260610.md` | VALID | Support mine preserves live readings and source routes. | Reverify exact source paths before build. |
| `rosetta_xlsx_transcription_20260609.md` | VALID | Transcription marks owner-authored pre-AI source and assistant candidates separately. | Spot-check workbook cells for critical citations. |
| `round3_discriminator_registry_20260611.md` | VALID | Registry contract/process authority. | Keep aligned with post-G.2a and Axis-0 corrections. |
| `route_genuineness_audit_20260610.md` | VALID | Route-level audit process surface. | None. |
| `s10_g2_family_mine_20260610.md` | VALID | Read-lane mine only. | Build packet for claims. |
| `s2_build_spec_20260610.md` | VALID | Build spec with scratch ceiling. | Build and audit. |
| `s3_build_spec_20260610.md` | VALID | Build spec with scratch ceiling. | Build and audit. |
| `s4_build_spec_20260610.md` | VALID | Build spec, not result. | Build and audit. |
| `s5_build_spec_20260610.md` | VALID | Build spec, not result. | Build and audit. |
| `s6_build_spec_20260610.md` | VALID | Build spec, not result. | Build and audit. |
| `s7_build_spec_20260610.md` | VALID | Build spec, not result. | Build and audit. |
| `s8_s9_adjudication_20260610.md` | VALID | Scope adjudication with parked packets. | Overlay later S8 table if consumed. |
| `screenshots_math_report_20260609.md` | VALID | Dated candidate material, explicitly not current/canonical. | Use only as provenance/candidate source. |
| `sedenion_witness_convention_20260610.md` | VALID | Convention guard only. | None. |
| `shell_flow_radiated_information_mine_20260610.md` | VALID | Mine-only receipt, no doctrine import. | Build finite bridge object before claims. |
| `spinor_network_surface_estate_20260611.md` | VALID | Mining receipt with doctrine gates and stop conditions. | Consume with owner_doctrine_surface corrections. |
| `stack_uniqueness_map_20260611.md` | VALID | Stack/gap map; no promotion. | Refresh after later packet closures. |
| `standing_queue_20260612.md` | SHALLOW | It preserves superseded block and current block, but the front-door refresh lane text is now historical and live queue may drift. | Treat as dated queue state; update at closeout. |
| `static_shallowness_audit_20260612.md` | VALID | Directly answers owner depth directive and re-scopes Axis-0/static/one-step/dynamic surfaces. | None; use as current anchor. |
| `strict_source_hygiene_20260611.md` | VALID | Strict-source process receipt. | Keep enforced in future receipts. |
| `substage_transition_convention_mining_20260611.md` | VALID | Mining receipt only; provenance classes defined. | Owner decision or packet before convention authority. |
| `terrain_operator_map_20260609.md` | SHALLOW | Useful source map, but pre-correction Axis-0/terrain framing requires overlay. | Apply dynamic Axis-0 and M(C,t) build-order corrections. |
| `tooling_presumption_audit_20260610.md` | VALID | Correctly demotes tool-presumption claims. | Keep with capability probes. |
| `tooling_remediation_steps_1_2_20260610.md` | VALID | Remediation report with verification outcomes. | Refresh after package/tool changes. |
| `toolset_expansion_20260610.md` | VALID | Fit-probe receipt with promotion false. | Keep as capability evidence only. |
| `twi_blind_expected_20260610.md` | VALID | Blind expected-values pre-registration. | Compare against packet output. |
| `twi_pre_audit_checklist_20260610.md` | VALID | Pre-audit checklist. | None. |
| `twistor_incidence_mine_20260610.md` | VALID | Mine-only receipt with not-owner-doctrine labels. | Build finite discriminator before claims. |
| `unified_run_sequence_policy_20260611.md` | VALID | Derivation-only sequence/seed policy. | Keep as policy, not result. |
| `validity_audit_lane_a_geometry_20260612.md` | VALID | Lane A directly audits geometry/topology/manifold packets, names stale source-hash failures, b6 shallowness, and dynamic-chart first-rung status without promoting admission. | Use as current geometry validity anchor; rerun if packet sources/results are regenerated. |
| `validity_audit_lane_b_engines_20260612.md` | VALID | Current lane-B audit classifies engine/QIT/basin/axis estate and names source-lock gaps. | Use as anchor for sim-layer citations. |
| `weld2_nonassoc_integration_mine_20260610.md` | VALID | Mine-only nonassoc integration map. | Build weld packet before claims. |
| `weld_feedstock_inventory_20260611.md` | SHALLOW | Useful inventory, but some feedstock rows can over-carry prior packet claims without source-lock refresh. | Reverify consumed row authority and lane-B statuses. |
| `wiki_corpus_basins_20260611.md` | VALID | Advisory corpus coverage. | Use only as source map. |
| `wiki_corpus_wave2_20260611.md` | VALID | Bounded corpus population receipt. | Reverify before quote authority. |
| `wiki_research_architecture_20260611.md` | VALID | Research architecture/process receipt. | None. |
| `wizard_runtime_audit_triage_20260610.md` | VALID | Runtime triage receipt. | Refresh if runtime changes. |
| `workedout_possibilities_mining_20260609.md` | VALID | Deep-mining report, no promotion. | Reverify source candidates before build. |

## Receipts-Index Tier Spot Check

Spot-checked tier assignments from `receipts_index_20260612.md`.

| Indexed row | Index tier | Audit verdict | Correction |
|---|---:|---:|---|
| `owner_correction_axis0_not_built_20260612.md` | AUTHORITY | VALID | Correct current authority. |
| `static_shallowness_audit_20260612.md` | absent from addendum/table | SHALLOW index gap | Add as AUTHORITY for depth/static re-scope. |
| `validity_audit_lane_b_engines_20260612.md` | absent | SHALLOW index gap | Add as AUTHORITY for engine/basin/axis validity audit. |
| `axis_work_order_20260612.md` | AUTHORITY; amended | SHALLOW | Needs overlay: old Axis-0/b6 rows are stale; topology corrections remain useful. |
| `axis0_registry_final_state_supplement_20260612.md` | AUTHORITY under pre-correction static-proxy ceiling | SHALLOW but honest caveat | Keep only if the display name says "old static proxy family." |
| `physics_model_primary_deepread_20260612.md` | DEMOTED | VALID tier | Correct; it is not quote authority. |
| `hermes_audit_forwarded_20260612.md` | ADVISORY with verified fix lanes | VALID tier | Correct if only verified concrete findings are live. |
| `promotion_checklist_super_sim_v0_20260612.md` | ADVISORY / owner-gated | VALID tier, SHALLOW receipt wording risk | Tier is right; receipt title/status should not look like promotion. |
| `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md` | AUTHORITY | SHALLOW | Same-file corrections narrow what is authoritative; cite corrected SCC/QCA caveats only. |
| `receipts_index_20260612.md` itself | n/a | SHALLOW | It needs an overlay-current-state appendix for this lane, not original row edits. |

## Stale-After-Correction Overlay List

Do not edit originals in this lane. A future overlay receipt should carry these corrections.

| Original surface | Stale claim | One-line correction |
|---|---|---|
| `working_math_scaffold_20260609.md:117` | `b_6=-b_0 b_3` as Axis-6 scaffold relation | Disowned scaffold artifact; keep only precedence mechanics `L_A/R_A` and `Phi_T O` vs `O Phi_T`. |
| `symbolic_layer_iching_taijitu_20260609.md:28-31` | Axis-6 symbolic row and directional table derive from b6 law | Strike b6-derived symbolic derivation; leave as proposal-only symbolic mapping. |
| `axis_work_order_20260612.md:1-27` | Axis-0 v0 earned and b6 consistency row staged | Axis-0 remains unbuilt; b6 law is provenance-dead and at-chance on tested covers. |
| `night_closeout_20260612_mass_spawn_wave.md` | Buildable 0-6 complete; Axis-0 contender program closed as Axis-0 | Re-read as old static-proxy/one-step witness estate complete at scratch ceilings only. |
| `axis0_contender_probe_registry_20260612.md` | The 33-cell anchor is the Axis-0 control | Anchor is a synthetic/static proxy, not Axis-0 measurement. |
| `axis0_registry_amendment_1_20260612.md` | Amendment candidates tested against old anchor as Axis-0 | Refile as static-proxy formula taxonomy. |
| `axis0_registry_final_state_supplement_20260612.md` | "Axis-0 family status... anchor alias class only" | "Old static-proxy anchor family status... alias class only." |
| `axis0_deep_wave_sonnet_20260612.json` | Several synthesis rows call the old family "Axis-0" and mix owner-source/sim-realization/llm elaboration | Re-index after owner correction; separate owner semantics from built static proxy. |
| `axis3_contender_probe_registry_20260612.md` | Axis-0 response keys appear as boundary comparators | Replace with current static-proxy/dynamic-Axis-0 terminology. |
| `axis6_contender_probe_registry_20260612.md` | Reads in the b6-law era and can be cited as product-law scaffold support | Use only operator/terrain precedence; no b6 product law. |
| `axis_independence_mine_20260610.md` | b6 scaffold consistency and Axis-0 independence framing | Mark b6 rows dead; Axis-0 rows static-proxy only. |
| `mct_pre_audit_checklist_20260610.md` | `axis0_status == readout_only_no_closure` sufficient fence | Add stronger `not built Axis-0; static proxy only unless dynamic response packet exists`. |
| `terrain_operator_map_20260609.md` | Axis-0 source map predates owner correction | Overlay dynamic allostasis/homeostasis target and reject static-anchor closure. |
| `doc_router_axes_terrains_operators_20260609.md` | Early router likely treats old axis/scaffold relations as current | Overlay M(C,t), static-proxy Axis-0, and b6 disownment. |
| `math_geometry_test_map_20260609.md` | Bridge/Axis0 open language predates stronger owner correction | Reframe as dynamic manifold front-door first, not static Axis-0 candidate sweep. |
| `owner_doctrine_axes_as_existence_probes_20260612.md` | Expects Axis-0 readout survival/contender sweep as existence-grade path | Axis-0 contender sweep did not build Axis-0; existence probe requires dynamic response. |
| `owner_doctrine_cellular_automata_ring_checkerboard_20260611.md` | Classical floor headline says earned before later definitional demotion | Cite transient SCC topology only; period 2/4 is implementation check. |
| `owner_prediction_64_subsubbasins_20260611.md` | 64-subsubbasin prediction as live target | Current joint results killed/narrowed the direct 64 reading; keep as source pressure only. |
| `physics_model_primary_deepread_20260612.md` | Quote authority for physics model | Already demoted; all consumed quotes require fresh verification or strike. |
| `receipts_index_20260612.md` | Some tiers omit latest audits or over-authorize stale rows | Add overlay index tier corrections; do not trust absent rows as non-citable if this lane created them. |

## Top 5 Worst Findings

1. `working_math_scaffold_20260609.md` has file-level `OWNER-AUTHORED` frontmatter but line-level mixed provenance; that is exactly the b6/A0-A8 scaffold-artifact failure mode.
2. `b6=-b0*b3` is still visible in foundation surfaces after being both owner-disowned and computationally at-chance on tested covers.
3. The old Axis-0 registry/final-state receipts still say "Axis-0" where the owner correction requires "static proxy formula taxonomy on the 33-cell carrier."
4. `physics_model_primary_deepread_20260612.md` is quote-broken for authority; its own demotion is correct, but any downstream consumer must reverify or strike quotes.
5. `receipts_index_20260612.md` is stale as a front door because it omits the two validity audits and still presents some rows with authority tiers that need overlay correction.

## Verification / Hygiene

Fresh commands used in this lane included:

```text
find system_v6/receipts -type f | sort | wc -l
find system_v6/foundations -type f | sort
find system_v6/docs -type f
rg -n "b4ee8f030|b891e0611|0313d47bc|276d42d81|owner correction|static shallowness|Hermes|scorecard|receipts[-_ ]index|ECD|L\(3,1\)|b6|disown|disowned|provenance" system_v6/receipts system_v6/foundations system_v6/README.md system_v6/docs
git show --stat --oneline --decorate --no-renames b4ee8f030 b891e0611 0313d47bc 276d42d81
nl -ba system_v6/foundations/working_math_scaffold_20260609.md
nl -ba system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md
nl -ba system_v6/foundations/two_engine_readout_automaton_20260609.md
nl -ba system_v6/foundations/root_axioms_v0_DRAFT.md
nl -ba system_v6/foundations/root_axioms_v0_1_DRAFT.md
nl -ba system_v6/README.md
nl -ba /Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/MY\ INPUTS\ on\ Retrocausality.md
nl -ba /Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md
nl -ba /Users/joshuaeisenhart/wiki/concepts/field-wide-compression-geometry.md
nl -ba /Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md
nl -ba /Users/joshuaeisenhart/wiki/concepts/axis-0-correlation-polarity.md
```

No git add, commit, rebase, or result regeneration was performed.
