# Codex Deep Audit: Claude June 6 Physics Wave Receipts

Date: 2026-06-06

Scope: deep audit and bounded rerun of Claude's June 6 physics/frontier result batch. This audit treats Claude's prose as an untrusted claim sheet and checks the local artifacts directly.

## Ceiling

Accepted status: rerunnable scratch diagnostics only.

Not accepted: canonical-by-process, formal admission, physics admission, Standard Model admission, GR admission, Yang-Mills solution, M(C) admission, Axis0, bridge, final manifold completion, or layer completion.

The active moved root `/Users/joshuaeisenhart/Codex-Ratchet` does not currently expose `make layer-completion-claim-gate`. The older Desktop root named in the stricter pasted AGENTS contract does expose it. Running the older-root gate against the conservative noncompletion claim passed:

```text
make layer-completion-claim-gate CLAIM_FILE=/tmp/codex_deep_audit_20260606/claim_ceiling_text.txt
ok=true
violations=[]
```

This is not admission. It only confirms the conservative wording avoids completion-like overclaim.

## Commands And Artifacts

Audit artifacts:

- `/tmp/codex_deep_audit_20260606/audit.json`
- `/tmp/codex_deep_audit_20260606/audit_summary.txt`
- `/tmp/codex_deep_audit_20260606/rerun.json`
- `/tmp/codex_deep_audit_20260606/rerun_julia_cleanup.json`
- `/tmp/codex_deep_audit_20260606/scoped_cleanup_sources.txt`
- `/tmp/codex_deep_audit_20260606/post_cleanup_lint.json`
- `/tmp/codex_deep_audit_20260606/post_cleanup_rerun.json`
- `/tmp/contract_cleanup/build.txt`
- `/tmp/codex_deep_audit_20260606/claim_ceiling_text.txt`

Authority and process docs were read from both the active moved root and the older Desktop root where the stricter AGENTS contract lives.

Local checks:

- Parsed 32 claimed result JSONs.
- Checked source/result freshness.
- Checked scratch fences: `classification`, `promotion_allowed`, `formal_admission_allowed`, claim ceiling, blocked consumers where present.
- Checked result-side tool manifest and integration depth.
- Parsed external audit text where present.
- Ran `scripts/lint_sim_contract.py` on discovered JAX sources.
- Reran all 32 JAX sources with `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`.
- Reran all resolvable Julia peers with `/opt/homebrew/bin/julia --project=system_v5/julia_carrier`.

Initial pre-cleanup rerun result:

- JAX reruns: 32/32 exit 0.
- Julia peer reruns: all resolvable peers exit 0 after cleanup and manual source resolution.
- Post-rerun `all_pass`: 32/32 true.
- Max post-rerun parity delta: `1.1368683772161603e-13`.
- Source/result staleness found: none.

Post-cleanup scoped verification:

- External cleanup lane receipt: `CLEANUP_DONE sims_fixed=24 total_violations_after=0 any_promoted=false`.
- Scoped source lint after cleanup: `checked=24`, `violation_total=0`, `sims_with_violations=0`.
- AST NumPy scan over scoped JAX sources: `numpy_ast_violations=0`.
- Julia reruns: 24/24 scoped Julia peers exit 0.
- JAX reruns: 23/24 exit 0; `mp4_fine_structure_explore_jax.py` exits 2 while intentionally writing `all_pass=false`.
- Post-cleanup local claim checks: 23/24 `post_all_pass=true`; the only false row is `mp4_fine_structure_explore_jax.py`, the alpha graveyard result.
- Post-cleanup fences: 24/24 remain `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.
- Post-cleanup freshness: no stale scoped source/result pairs.
- Max post-cleanup parity delta: `1.1368683772161603e-13`.

## Mechanical Gate Finding

The initial audit found that `scripts/lint_sim_contract.py` failed 31/32 JAX sources. This was not a numerical rerun failure. It was a process-ceiling finding:

- Many sources emit `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH` in result JSONs but do not expose the exact module-level static fields the legacy AST linter expects.
- Several current artifacts intentionally use `classification=scratch_diagnostic`, while legacy contract lint expects older classifications such as `formal_scout`, `canonical`, `tool_lego_fit_probe`, or related accepted categories.
- Therefore none of these artifacts should be called `canonical by process`.

The external cleanup lane then changed the lint convention and source shape for the scoped 24-file session set:

- `scratch_diagnostic` is now a valid source classification only when fenced by `promotion_allowed=false` and `formal_admission_allowed=false`.
- The linter skips formal capability-admission proof requirements for fenced scratch diagnostics.
- The scoped 24 files now pass static contract lint with zero violations.

This is a ceiling-preserving scratch convention update, not a formal-scout promotion. `system_v5/ops/formal_scouts/validate_formal_scout_results.py` still rejects these receipts because `classification is not formal_scout`.

Correct label: source/result-side fenced scratch diagnostic, locally rerunnable where exit status allows, not canonical and not formal scout.

## Keep As Clean Scratch Witnesses

These reran, retained fences, had tight parity, and had no source staleness. They may be cited only as scratch diagnostics:

- `spinor_network_face_readout_taxonomy`
- `knot_mass_gravity_rung`
- `qit_engine_3qubit_face_knot_taxonomy`
- `mp_cross_model_convergence`
- `mp_full_sm_gauge`
- `mp_full_carrier_gravity`
- `mp_sedenion_three_generations`
- `mp_su2u1_electroweak`
- `mp_universal_clock`
- `mp_sequential_universe_density_carrier`
- `mc_first_admissibility_packet`
- `mp2_joint_gr_sm`
- `mp2_chiral_weak_from_weyl`
- `mp2_clifford_minimal_ideals`
- `mp2_nonassoc_third_constraint`
- `mp2_three_families_one_survives`
- `mp3_homochirality_cascade`
- `mp4_cosmological_constant_dissolves`
- `mp4_measurement_retrocausal`
- `mp4_hierarchy_gravity_weak`

Important wording repair: say "first finite M(C)-shaped scratch admissibility packet passed local controls." Do not say "M(C) is admitted" or "M(C) is made" without the scratch/admission ceiling.

## Reproduced Or Contested, Not Emergent

These are useful mechanism or representation witnesses but should not be reported as clean independent derivations:

- `mp2_three_gen_full_sm`: Grok flags by-construction. The sedenion/full-gauge scaffold is load-bearing but induced.
- `mp2_anomaly_cancellation`: Grok flags by-construction. Hypercharge trace follows from the chosen Cl(6)/occupation construction.
- `mp2_charge_quantization`: Grok flags by-construction. Multiples of 1/3 are arithmetic from the chosen ladder representation.
- `mp3_yang_mills_mass_gap`: finite mechanism witness only. Reruns clean, but no continuum Clay proof. Gemini flags by-construction.
- `mp3_matter_antimatter_chirality`: finite chirality-bias mechanism witness only. Reruns clean, but no baryogenesis or observed-ratio derivation. Gemini flags by-construction.
- `mp4_arrow_of_time_entropy`: finite ratchet mechanism witness only. Gemini flags by-construction.
- `mp4_evolution_is_the_ratchet`: finite mechanism witness only. Gemini flags by-construction.

Use wording like "finite mechanism witness" or "representation consistency witness", not "derived physics result."

## Graveyard Or Partial

These should be preserved as useful failures or partials:

- `mp2_weinberg_angle_explore`: `sin2_theta_w=0.375` appears, but `derived_not_fit=false` and both auditors classify by-construction. Graveyard as derivation.
- `mp4_fine_structure_explore`: computed `alpha_value=0.011490294021831283`; `matches_137=false`, `derived_not_fit=false`, divergence log says primary scalar does not match 1/137. Graveyard as alpha derivation.
- `mp4_chemistry_hopf_shells`: real Hopf-shell capacity proxy gives `[2, 8, 18, 32]`; `matches_2_8_8=false`. Partial capacity proxy, not chemistry-shell recovery.

## Metadata Or Audit Gaps

These need trail repair before Hermes or any index calls them clean:

- `qit_engine_3qubit_face_knot_taxonomy_results.json` omits `source_path` even though the source exists at `system_v5/ops/formal_scouts/qit_engine_3qubit_face_knot_taxonomy_jax.py`.
- `mp_sequential_universe_toy_results.json` is repaired semantically to `object_id=mp_sequential_universe_density_carrier`, but the filename still says toy and the result JSON omits `source_path`.
- `spinor_network_force_transition_channel_taxonomy` reruns and has parity, but no external audit receipt was found in the audited temp directories.
- `su3_color_from_g2_octonion_cl6` reruns and has parity, but no standalone external audit receipt was found in the audited temp directories.

## Hermes Handling

Hermes should ingest this batch as a fenced scratch-receipt pack, not as accepted canon.

Preferred index labels:

- `scratch_witness_rerun_passed`
- `mechanism_witness_only`
- `by_construction_reproduction`
- `graveyard_derivation_failed`
- `metadata_repair_needed`

Blocked labels:

- `physics solved`
- `Yang-Mills solved`
- `Standard Model derived`
- `GR+SM unified`
- `M(C) admitted`
- `Axis0 unlocked`
- `canonical by process`
- `formal admission`

Next admissible work:

1. Keep the post-cleanup scoped 24 as lint-clean fenced scratch diagnostics, not formal scouts.
2. Add missing `source_path` fields for the 3-qubit engine and repaired sequential-universe result.
3. Produce missing external audit receipts for force-transition taxonomy and SU3 color if they are to be indexed as clean.
4. Rerun or separately lint any non-scoped artifacts before treating the cleanup as global.
5. Keep constants and measured parameters in the graveyard until a new rung derives them without target fitting.

## Post-Cleanup Verification

After this audit snapshot and rerun, an external Claude lane ran `/tmp/contract_cleanup/driver.py` and touched audited source/result files under `system_v5/ops/formal_scouts/` and `system_v5/julia_carrier/`. Codex then ran a post-cleanup scoped verification pass over the 24 files listed in `/tmp/codex_deep_audit_20260606/scoped_cleanup_sources.txt`.

Receipt state:

- `/tmp/contract_cleanup/build.txt` reports `CLEANUP_DONE sims_fixed=24 total_violations_after=0 any_promoted=false`.
- The scoped linter rerun reports `checked=24`, `violation_total=0`.
- The no-NumPy AST scan reports `numpy_ast_violations=0`.
- `/tmp/codex_deep_audit_20260606/post_cleanup_rerun.json` records 24 Julia peer reruns, all exit 0.
- The same post-cleanup rerun records 23 JAX exits 0 and one JAX exit 2: `mp4_fine_structure_explore_jax.py`, which is the intended alpha graveyard row and writes `all_pass=false`.
- The formal-scout validator still rejects representative receipts with `classification is not formal_scout`.

Therefore this document now records both the completed pre-cleanup audit and the post-cleanup scoped verification. The batch is final-current only at the fenced scratch-diagnostic ceiling described above.
