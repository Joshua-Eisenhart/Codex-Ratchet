# Audit verdict: terrain_operator_precedence_64_matrix

Fresh-audit scope: `/tmp/m64_pre_audit_checklist_20260610.md`, `/tmp/m64_blind_expected_20260610.md`, `system_v6/receipts/matrix64_mine_20260610.md`, and `system_v6/sims/terrain_operator_precedence_64_matrix/`.

Auditor status: I did not build this sim. Builder assertions were not used as evidence.

## Bottom line

VERDICT: GENUINE-WITH-CAVEATS.

The 64-cell chart matrix is a genuine scratch diagnostic for the named chart object. The headline `F7_trajectory = 64` survives source-locked manual recomputation and is honestly a trajectory-family distinctness result, not `F0_address` leakage. Caveats are about control/classification surfaces, not the existence of the computed 64-row behavior matrix.

This does not promote the object. Ceiling remains: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no runtime closure; no hexagram resolution; no canonical/admitted/Axis-level claim. The 64-lattice remains structural-scaffold language, and distinctness claims are only valid under named fingerprint families.

## Checks run

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json` -> `ok:true`.
- Same validator with `--require-source-backed` -> `ok:true`.
- Same validator with `--strict-source-backed` -> `ok:false`, because the source-backed audit saw `jax.scipy.linalg` as source-token-thin in the matrix source. This is a caveat: the call is transitive through the reused terrain packet, not directly visible in the matrix source.
- `scripts/lint_sim_contract.py` on the three Python files -> `checked:3`, `violation_total:0`. The same linter is Python-only and reports a parse error on the Julia file; that result is not an applicable Julia validation.
- Fresh manual recomputation from source-locked JAX operator and terrain packets, with no result-file rewrite.
- Search for promotion/conflation language over the sim folder and mine receipt.

## Per-check results

1. Label matrix attack: PASS.

Evidence: envelope `matrix_rows | length = 64`; every row has `ordered_outputs`, `Delta_T_O_matrix_plus_minus`, `Delta_T_O_norms`, `entropy_purity_deltas`, `observables`, `trajectory`, `generic_state_sweep`, and nested `address_key`. Source path uses source-locked imports in `terrain_operator_precedence_64_matrix_jax.py:103-104`, applies source channel and terrain channel at `:237-248`, and serializes behavior columns at `:338-374`. Manual recomputation from `source_locked_operator_base_packet_jax.py` and `terrain_generator_sheet_packet_jax.py` matched the two required cells.

2. Chart/runtime conflation attack: PASS.

Evidence: build card states this is the chart object, not the six-axis hexagram runtime probe, and forbids closure claims (`build_card.md:5-7`). The result boundary cites the four-construction table (`object_boundary.mine_receipt_four_construction_table = system_v6/receipts/matrix64_mine_20260610.md:61-84`). The mine receipt preserves the four live 64 constructions and explicitly says not to resolve them into one object (`matrix64_mine_20260610.md:61-84`).

3. Fingerprint theater attack: PASS, with a bounded caveat.

Evidence: `F0..F8 = 64/60/60/57/57/53/30/64/58`; `F0_address` is excluded from behavior claims by `controls.trivial_F0_control.excluded_from_behavior_claims=true`. The tolerance sweep is stable across `1e-6`, `1e-8`, and `1e-10`. `F2_order_pair=60` and `F3_delta=57`, so the two are not being presented as independent while exactly co-classifying.

Caveat: the strict source-backed validator flagged the local `jax.scipy.linalg` load-bearing declaration as source-token-thin because the actual matrix exponential call is in the reused terrain packet, not directly in the matrix source. This is not a row-computation failure, but it is a source-audit surfacing gap.

4. Classification gaming attack: CAVEAT.

Evidence-backed: F1 collapsed classes are named and supported by `F7_trajectory.fingerprint_key`. F6 has `n_distinct=30`, a full class map, and every collapsed F6 class is classified as `probe_coarseness` with `F7_trajectory.fingerprint_key` as the splitter.

Finding: the two `F8_axis_orthogonality` `intended_degeneracy_candidate` classes are over-labeled. The spec defines `intended_degeneracy_candidate` as a collapse that "survives all admitted F and controls" (`matrix64_mine_20260610.md:236-242`), but `F7_trajectory=64` splits every cell. Those F8 classes may be "zero-gap within F8" candidates, but they do not survive all fingerprint families.

5. Control circularity attack: CAVEAT.

Evidence: commuting control uses distinct operations `Si_Hill__Ti_plus` with `Delta_T_O_norms.fro = 9.813077866773595e-18`; noncommuting controls include `Si_Hill__Fi_plus` with manual `Delta_fro = 0.12241137979466175` and builder `Ne_Vortex__Ti_plus = 0.08151115599412681`. Normal F2 separates 28 signed pairs, matching the blind signed-pair law after pins.

Finding: the erased-precedence merge is underinstrumented as a class-map control. The source increments `erased_merged += 1` for each terrain/base pair and reports `32`, but does not emit a recomputed erased F2/F3 class map (`terrain_operator_precedence_64_matrix_jax.py:608-655`). The SMT erased-zero flip is real, but the G4 erased-precedence class-map evidence is asserted by count rather than stored as the checklist requested.

6. Decorative SMT attack: PASS, with claim boundary.

Evidence: result `crossover_proofs.z3` and `.cvc5` bind scaled entries from `signed_delta_selected_minus_counterfactual`, both return `unsat`, and both erased controls return `sat`. Source constructs z3/cvc5 separately in `terrain_operator_precedence_64_matrix_jax.py:541-605`. Fresh manual SMT on the checklist's `Si_Hill__Fi_plus` noncommuting cell also returned z3 `unsat`, cvc5 `unsat`, erased z3 `sat`, erased cvc5 `sat`.

Boundary: this is finite numeric entry-binding SMT over computed rows, not formal admission.

7. Reuse honesty attack: PASS-WITH-CAVEATS.

Evidence: JAX imports the source-locked operator and terrain packets (`terrain_operator_precedence_64_matrix_jax.py:41-45,103-104`), and the envelope records operator, terrain, and carrier lineage plus hashes in `source_reuse_lineage`. PyTorch similarly imports its source-locked packets. The carrier boundary stays lineage-only and does not promote to nested/rung maps.

Caveats: the Julia leg mirrors/reimplements the same forms and hashes the source packets, but does not literally import/include the source-locked Julia packet implementations. Also, the reused terrain packet's own `PIN_SPEC.rho_0_rho_1.reason` contains stale text saying the operator packet is absent; in this checkout the operator packet exists and the matrix JAX leg imports it.

8. Axis conflation attack: PASS, with the F8 label caveat above.

Evidence: `F8_axis_orthogonality` stores `axis6_precedence_sign`, `axis6_signed_delta_fro`, `axis4_inner_density_delta_fro`, `axis4_outer_density_delta_fro`, and `axis4_loop_class` as separate fields. The control reports Axis4 inner movement near zero (`2.455493422156577e-16`), Axis4 outer movement nonzero (`0.7071067811865476`), and Axis6 selected-output gap nonzero (`0.08151115599412681`). This matches the blind F8 pass shape (`/tmp/m64_blind_expected_20260610.md:71-80`).

9. Standard checks: PASS-WITH-CAVEATS.

Evidence: envelope and all three engine records carry `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`, and `reads_peer_result=false`. `claim_path_tools` excludes NumPy. Validator `--require-pytorch` passes. Search found no result-side "64 achieved", runtime closure, canonical/admitted promotion, or decoded claim outside quoted/spec boundary text.

Caveats: strict source-backed validation caveat above; Julia source lint by Python AST is not applicable.

## Overseer findings adjudication

F1. HEADLINE F7 trajectory = 64: ADJUDICATED GENUINE UNDER NAMED F7 ONLY.

The F7 key is computed from selected and counterfactual intermediate matrices, not from address labels (`terrain_operator_precedence_64_matrix_jax.py:314-319,407-412`). Manual source-locked recomputation produced `F7_trajectory=64`. Result language and boundary fields limit this to named-fingerprint distinctness and cite the four-construction boundary. It does not imply runtime closure or hexagram resolution.

F2. F1=60 vs hexagram 16: NO CONFLATION FOUND.

The chart result reports `F1_final_density=60`; the prior runtime hexagram object remains related-but-different `n_distinct=16` evidence. The boundary field points to the mine receipt's four-construction table and 16-class evidence. The four F1 collapsed pairs are `Si_Citadel__Fi +/-`, `Si_Citadel__Te +/-`, `Si_Hill__Fe +/-`, and `Si_Hill__Ti +/-`; each is classified as `probe_coarseness` with a computed stronger splitter `F7_trajectory.fingerprint_key`.

F3. F6=30 strongest collapse: EVIDENCE-BACKED, BUT COARSE.

F6 class map exists and has `n_distinct=30`, largest class size `4`. All F6 collapse verdicts are `probe_coarseness` split by F7, which is the right ceiling: F6 is a spinor/sheet/loop family, not a commute oracle. Under actual pins, the commute table has only four commuting unsigned pairs; F6 collapses many plus/minus pairs because it tracks sheet/loop/chirality magnitude rather than full ordered trajectory. Do not report F6 collapse as mathematical degeneracy.

F4. Blind-sheet diff: NO CONTRADICTIONS AFTER PIN RESOLUTION.

Resolved pins: `H0=(sigma_x+sigma_y+sigma_z)/sqrt(3)`, `eps=0.2`, `Si/Hill` uses z frame, `Si/Citadel` uses x frame (`terrain_generator_sheet_packet_jax.py:77-99`). The blind table says Se/Ne are pin-dependent; with non-axis-aligned `H0`, they resolve noncommuting. Ni `Ti/Fe` commute only if z-pinned; actual `H0` is not z-pinned, so they resolve noncommuting. Si resolves as Hill `Ti/Fe` commute, Hill `Te/Fi` noncommute, Citadel `Te/Fi` commute, Citadel `Ti/Fe` noncommute. The build's 32 unsigned-pair table matches that exactly: 28 noncommuting pairs and 4 commuting pairs.

## Manual recomputations

Source-locked inputs: `system_v6/sims/source_locked_operator_base_packet/source_locked_operator_base_packet_jax.py`; `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py`; pinned `rho_1=0.7*rho_0+0.3*I/2`; terrain `Phi=expm(0.4*X)`.

- Commuting cell: `Si_Hill__Ti_plus`, source-locked recompute `Delta_fro = 9.813077866773595e-18`, within `FP_TOL=1e-8`.
- Noncommuting cell: `Si_Hill__Fi_plus`, source-locked recompute `Delta_fro = 0.12241137979466175`, generic-state sweep nonzero in the result (`min_delta_fro = 0.1122464148251429`).
- Ladder count: manual `F0_address = 8 terrains * 8 signed operators = 64`; manual `F7_trajectory = 64`.
- SMT flip on manual `Si_Hill__Fi_plus`: z3 `Delta=0` -> `unsat`; z3 erased zero -> `sat`; cvc5 `Delta=0` -> `unsat`; cvc5 erased zero -> `sat`.

## Named gaps

1. G4 erased-precedence class-map evidence is underinstrumented. It reports the expected count `32`, but does not store a recomputed erased F2/F3 class map.
2. `F8_axis_orthogonality` intended-degeneracy labels overstate the spec. They should be narrowed to "F8 zero-gap class" or reclassified as `probe_coarseness` because F7 splits the same cells.
3. Strict source-backed validator flags a transitive source-token issue for `jax.scipy.linalg`. Either surface the transitive call evidence in the matrix source audit path, or demote the local matrix-source claim to "load-bearing via reused terrain packet".
4. Julia leg is a matched mirror with hashes, not literal reuse/import of the source-locked Julia packets. Keep it as parity evidence, not the strongest source-lock evidence.
5. F6=30 is useful as a family-specific collapse result, but it is coarser than commute classes. Do not use F6 collapse as evidence of intended mathematical degeneracy.

## Final ceiling

Keep this as a genuine `scratch_diagnostic` for `terrain_operator_precedence_64_matrix`. No promotion, no formal admission, no canonical/runtime/hexagram closure. The only full-64 behavior result admitted by this audit is: 64 distinct under `F7_trajectory`.

## Post-Hardening Re-Audit Addendum - 2026-06-09 PDT / 2026-06-10 UTC

Auditor status: I did not build, audit, or harden this sim. I treated the original verdict above as historical and recomputed/check-read the hardened result surfaces directly.

### Named-gap closure check

1. Gap 1 - CLOSED. Hardened envelope and JAX records now store `erased_precedence_class_maps`, not just the count `32` (`results/terrain_operator_precedence_64_matrix_envelope_results.json:60`, `:2504`; JAX copy at `results/terrain_operator_precedence_64_matrix_jax_results.json:593`, `:1404`). Stored counts are `F2 erased_class_count=32`, `F3 erased_class_count=29`, `erased_signed_pairs_merged=32`, and `normal_signed_pairs_split=28`.

   Hand recomputation from the stored maps:
   - `Ne_Vortex__Ti_plus/minus`: normal F2 splits into `F2_order_pair_class_15/16`, normal F3 splits into `F3_delta_class_15/16`; erased F2 merges both in `erased_precedence_F2_order_pair_class_08`, and erased F3 merges both in `erased_precedence_F3_delta_class_08`.
   - `Si_Hill__Fi_plus/minus`: normal F2 splits into `F2_order_pair_class_56/57`, normal F3 splits into `F3_delta_class_53/54`; erased F2 merges both in `erased_precedence_F2_order_pair_class_30`, and erased F3 merges both in `erased_precedence_F3_delta_class_27`.

2. Gap 2 - CLOSED. The two F8 collapse records are now surfaced as `f8_zero_gap_class` and classified as `probe_coarseness`; each names `F7_trajectory.fingerprint_key` as the splitter, and preserves the old `intended_degeneracy_candidate` label in `superseded_verdict` (`results/terrain_operator_precedence_64_matrix_envelope_results.json:3169`, `:3177`, `:3190`, `:33465`).

3. Gap 3 - CLOSED. The local JAX matrix record demotes `jax.scipy.linalg` to `supportive_via_reused_terrain_packet`, and records the transitive load-bearing source as `system_v6/sims/terrain_generator_sheet_packet/terrain_generator_sheet_packet_jax.py:20,443,447` (`results/terrain_operator_precedence_64_matrix_jax_results.json:7`, `:26`, `:30654`). Fresh validator rerun matches the intended closure: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json` returned `{"ok": true, ...}`.

4. Gap 4 - CLOSED. Julia record has `julia_reuse_mode="matched_mirror_with_source_hashes_not_literal_import"` (`results/terrain_operator_precedence_64_matrix_julia_results.json:1744`; envelope copy at `results/terrain_operator_precedence_64_matrix_envelope_results.json:2427`).

5. Gap 5 - CLOSED. Hardened records include `f6_result_note="family-specific collapse (sheet/loop/chirality magnitude family); coarser than commute classes; not evidence of intended mathematical degeneracy"` (`results/terrain_operator_precedence_64_matrix_jax_results.json:2068`; envelope copy at `results/terrain_operator_precedence_64_matrix_envelope_results.json:3168`).

### Byte-stability and ceiling check

- Fingerprint ladder is stable at `64/60/60/57/57/53/30/64/58` for `F0..F8` (`results/terrain_operator_precedence_64_matrix_envelope_results.json:1487-1495`, with matching Julia/PyTorch rows at `:1503-1511` and `:1519-1527`).
- JAX/JULIA commuting control remains `9.813077866773595e-18`; JAX/JULIA noncommuting control remains `0.08151115599412681`; PyTorch differs only at floating precision (`1.962615573354719e-17`, `0.08151115599412674`) and envelope `max_divergence` is `6.938893903907228e-17` (`results/terrain_operator_precedence_64_matrix_envelope_results.json:1485-1497`, `:1517-1529`, `:1535`).
- Pair split surface remains `28` normal signed pairs separated under F2, hence `4` signed pairs not separated under normal F2; erased F2/F3 merges all `32` signed pairs (`results/terrain_operator_precedence_64_matrix_envelope_results.json:726`, `:1462`, `:2504`).
- F8 triple remains `2.455493422156577e-16 / 0.7071067811865476 / 0.08151115599412681` for inner-density near-zero, outer-density nonzero, and Axis6 selected-output gap (`results/terrain_operator_precedence_64_matrix_envelope_results.json:731-739`).
- Ceiling remains exact: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`, and `claim_ceiling="scratch_diagnostic only; no axis-level admission, no Axis-6 earned doctrine claim, no engine/runtime closure, no IGT"` (`results/terrain_operator_precedence_64_matrix_envelope_results.json:780`, `:792`, `:5565`, `:31740`).

### Fresh validators

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json` -> `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/terrain_operator_precedence_64_matrix/results/terrain_operator_precedence_64_matrix_envelope_results.json` -> `ok:true`.

### Stale-surface scan

Fresh search for stale open-gap wording found the original historical findings above and the build-card's verdict vocabulary only. This addendum is the current post-hardening status surface; the original Named gaps section is preserved as historical append-only text, not a live open-gap verdict.

Final ceiling restated: `scratch_diagnostic`; no promotion; distinctness only under named families; `64-lattice` remains structural-scaffold language; chart-vs-runtime boundary remains intact.

Final line: GENUINE-WITH-CAVEATS sustained.
