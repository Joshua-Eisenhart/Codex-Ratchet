# Current Pre-Axis Sim Status
Generated: 2026-04-04
Source: system_v4/probes/a2_state/sim_results/* + SYSTEM_CONTEXT_HANDOFF__CURRENT.md sections 4 and 15

---

## Tier Map (what each tier covers)

| Tier | Label | Description |
|------|-------|-------------|
| 0 | Root constraints | Nonclassicality guards; what math is forbidden |
| 1 | Admissibility charter C | The rule set that defines admissible structure |
| 2 | Admissible manifold M(C) | The geometry space consistent with charter C |
| 3 | Geometry buildup / Operator basis | Operator selection, fiber/base grammar, load-bearing tests |
| 4 | Weyl working layer | Type1/Type2 engine Weyl chirality; CW/CCW handedness assignment |
| 5 | Bridge family Xi | Xi / Xi_hist; causal bridge over the engine sequence |
| 6 | Cut family A\|B / Entropy & Entanglement | VN entropy structure; entanglement object witnesses |
| 7 | Kernel Phi_0(rho_AB) | Coherent information kernel; entanglement object identity |
| 8 | Edge writeback / Graph topology | STEP_SEQUENCE ring topology; P1/P3/P4/P5 edge constraints |

---

## Per-Tier Status

| Tier | Label | Sim File | Result File | Status | Notes |
|------|-------|----------|-------------|--------|-------|
| 0 | Root constraints | none | none | NO SIM YET | Doctrinal; not mechanically executed |
| 1 | Admissibility charter C | none | none | NO SIM YET | No executable sim; dependency of all lower tiers |
| 2 | Admissible manifold M(C) | none | none | NO SIM YET | No executable sim yet |
| 3 | Geometry / Operator basis | sim_operator_basis_search.py | operator_basis_search_results.json | PARTIAL | B3.1–B3.4 and SymPy proofs pass for Type1. Type2 fiber/base grammar INVERTED and open. No top-level status field in result JSON. |
| 3/4 | Hopf pointwise pullback | sim_hopf_pointwise_pullback.py | hopf_pointwise_pullback_results.json | PASS | Fiber loops yield constant pullback (density-stationary). Base loops yield varying Bloch trajectory (density-traversing). Product-state I(A:B) identically zero — confirms nontrivial bridge required. product_guardrail_pass=true. |
| 4 | Weyl working layer | sim_weyl_geometry_ladder_audit.py | weyl_geometry_ladder_audit_results.json | PARTIAL | Type1 fully_matches=true. Type2 fully_matches=false. Weyl ladder audit PASS: holonomy varies across torus ladder, engine response varies, signatures separable (witness_separable=true, guardrail_pass=true). Type1/Type2 axis_delta magnitudes differ. Type2 inversion still open per `type2_weyl_inversion_status_note.md`. |
| 5 | Bridge family Xi bakeoff | sim_xi_bridge_bakeoff.py | xi_bridge_bakeoff_results.json | OPEN (evidence gathered) | 4 families compared: shell, point_ref, hist, chiral. Chiral is least-arbitrary (composite=0.80, only family with I_c>0 on all 6 configs, 6/6 sign-positive). Shell second (0.46). Hist worst on perturbation sensitivity. No closure claimed on Xi. |
| 5 | History vs pointwise Ax0 | sim_history_vs_pointwise_ax0.py | history_vs_pointwise_ax0_results.json | OPEN (diagnostic) | History-window bridges lead pointwise by MI gap ~0.93. hist_retro_exp wins for Type1 (3/3 tori), hist_fe_indexed wins for Type2 (3/3 tori). Both families remain open. |
| 6 | Cut / Entropy structure | sim_c2_entropy_structure_search.py | c2_entropy_structure_search_results.json | PASS | C2_status: "PASS (Entropy Structure Admitted)". 8/8 VN-positive stages: classical shortcut killed, purity proxy killed. Shannon/purity shortcuts insufficient; VN entropy is necessary. |
| 6 | Cut / Entanglement witness | sim_c1_entanglement_object_search.py | c1_entanglement_object_search_results.json | PARTIAL | C1_status: "PARTIAL — entanglement witnessed but not all negative controls killed". 16/16 stages witnessed. MI-based fake_coupling NOT killed (count=0). Concurrence/negativity fake coupling: ALL killed (16/16). MI-based mispair NOT killed (count=0). Concurrence/negativity mispair: 8/16 killed. |
| 7 | Kernel / Mispair characterization | sim_c1_mispair_probe.py | c1_mispair_probe_results.json | PASS (characterization) | verdict="operator-driven", verdict_clean=true. Fe/Fi universally entangling; Te/Ti non-entangling. Mispair entanglement is operator-family-driven, not chirality-driven. States are structurally distinguishable (avg trace distance ~0.41) but entanglement is operator-determined. Explains but does not close C1 PARTIAL. |
| 7 | Kernel discriminator (A0) | sim_a0_kernel_discriminator.py | a0_kernel_discriminator_results.json | PASS | Winner=K1_Ic (coherent information), score 5/6. K2_MI=4/6, K3_shell_Ic=4/6. K1_Ic passes: R1_signed, R3_bell_ceiling, R4_werner_monotone, R5_schmidt_sensitive, R6_cq_honest. Fails R2_sep_anchor only. 24-state battery. bridge_assumption="none (pure cut-state evaluation)". |
| 8 | Edge writeback / Graph topology | sim_edge_state_writeback.py | edge_state_writeback_results.json | PASS (artifact-confirmed) | P1 lookup_size=64, P2 assertion passed, P3 write_hits=8 (0 misses), P4 nonzero_cols=7, P5 admissibility_rate=0.5. All 7 dynamic slot columns have nonzero variance. JSON artifact now exists in sim_results. |

---

## Open Problems

1. **Tiers 0–2 (constraints, charter, manifold): No sims exist.** These are dependency layers for everything above. Their absence means the full pre-Axis ladder has no mechanical bottom.

2. **Tier 3/4 — Type2 Weyl inversion open.** `geometry_crosscheck.type2.fully_matches = false`. Type2 fiber/base grammar is inverted vs canonical. Wave-2 added a Weyl geometry ladder audit (`weyl_geometry_ladder_audit_results.json`) and a dedicated status note (`type2_weyl_inversion_status_note.md`), confirming the inversion is structural and documenting it. No fix or adjudication exists. B3.x results do NOT transfer to Type2 without additional proof work.

3. **Tier 5 — Bridge Xi: sims exist, not closed.** Wave-2 ran two dedicated bridge sims:
   - `xi_bridge_bakeoff_results.json`: 4-family comparison (shell, point_ref, hist, chiral). Chiral wins on composite score (0.80) and is the only family with I_c > 0 on all 6 engine×torus cells. Shell/point_ref/hist all have negative I_c everywhere.
   - `history_vs_pointwise_ax0_results.json`: History window family leads pointwise by MI gap of 0.93. Best history: hist_retro_exp (Type1) / hist_fe_indexed (Type2). Best pointwise: shell_cq. Verdict: "history_leads" — diagnostic only.
   - **Open:** No single winner selected. Chiral and history families are structurally different bridge approaches. No closure claimed on Xi.

4. **Tier 6 C1 PARTIAL — MI-based negative controls not killed.** `fake_coupling_kill_count = 0`, `mispair_kill_count = 0`. MI does NOT reliably kill fake coupling or mispair. Only concurrence/negativity kill fake coupling (16/16). Mispair concurrence/negativity: only 8/16. The C1 mispair targeted probe explains why (operator family), but the MI-based failure is a structural open.

5. **Tier 6 C1 mispair concurrence/negativity: 8/16 killed.** The 8 unresolved mispair stages involve Fe or Fi (universally entangling operators). Structural, not a probe failure. Open design question for the C1 contract.

6. **Tier 8 — RESOLVED.** `edge_state_writeback_results.json` with P1–P5 all pass. Artifact-confirmed 2026-04-04.

---

## Clean Passes

1. **C2 — Entropy Structure Admitted** (`c2_entropy_structure_search_results.json`, C2_status = "PASS"). Classical Shannon shortcut and purity proxy both killed on all VN-positive stages. VN entropy is necessary for the kernel tier. Clean artifact.

2. **B3.2 — Coord change preserves grammar** (operator_basis_search_results.json). coord_change_preserves_grammar = true. SymPy proof verified: Frobenius norm and characteristic polynomial invariant under Hadamard conjugation.

3. **B3.3 — Noncomm ablation degrades grammar** (operator_basis_search_results.json). noncomm_ablation_degrades_grammar = true. SymPy proof verified: [Ti,Fe]=0 for general rho; [Ti,Fi]≠0 at canonical rho. Noncommutativity is structurally necessary.

4. **B3.4 — All 4 operators load-bearing** (operator_basis_search_results.json). n_load_bearing = 4, n_demotion_candidates = 0. Fe, Fi, Te, Ti all required.

5. **B3.1 — Basis remap breaks grammar** (operator_basis_search_results.json). gap_change_fraction = 17.18. remap_breaks_grammar = true. The operator basis is non-arbitrary.

6. **C1 mispair characterization — operator-driven** (`c1_mispair_probe_results.json`, verdict_clean = true). Entanglement survival is determined by operator family (unitary rotation vs dephasing), not Weyl chirality. Type1/Type2 states are structurally distinguishable (avg trace distance ~0.41) but this distinction does not determine entanglement outcome.

7. **Geometry crosscheck Type1** (operator_basis_search_results.json). type1.fully_matches = true. Probe canonical matches Type1 engine operator assignment exactly.

8. **Kernel discriminator — K1_Ic wins** (`a0_kernel_discriminator_results.json`, verdict = "PASS"). Coherent information (K1_Ic) scores 5/6 vs MI (K2) 4/6 vs shell_Ic (K3) 4/6. K1 passes R1_signed, R3_bell_ceiling, R4_werner_monotone, R5_schmidt_sensitive, R6_cq_honest. Informative for Tier 7 kernel; Tier 7 remains embargoed.

9. **Hopf pointwise pullback — structural baseline** (`hopf_pointwise_pullback_results.json`). 64-sample fiber/base MI decomposition across 3 tori. Fiber loops show zero MI; base loops show nonzero Berry phase on inner/outer. Structural characterization, not a closure claim.

---

## What this does NOT claim

- This ledger does NOT claim that the full pre-Axis ladder is ratcheted or admitted. Tiers 0–2 have no sims. Tier 5 has sims but is not closed.
- This ledger does NOT collapse C1 PARTIAL into PASS. MI-based negative controls are still not killed.
- This ledger does NOT claim that the Type2 geometry/Weyl inversion is resolved. Dedicated status note + ladder audit exist but do not fix it.
- This ledger does NOT claim Bridge Xi is closed. Two bakeoff sims exist; chiral and history families are leading candidates. No winner selected.
- This ledger does NOT claim the kernel discriminator result (K1_Ic wins) unlocks Tier 7. Tier 7 remains embargoed until Tiers 3–6 close.
- Tier 8 edge writeback PASS is artifact-confirmed from `edge_state_writeback_results.json` (P1–P5 all pass, 7/7 dynamic slots nonzero variance).
- This ledger does NOT claim that B3.1 basis_remap failure (remap_breaks_grammar = true) is a negative result; the test was designed to confirm the basis is load-bearing, which it did.
- The SymPy proofs cover only the specific scopes stated in proof_scope fields (2x2 real-symmetric, specific unitaries). They do not generalize beyond their stated scope without additional proof work.
