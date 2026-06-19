# Audit verdict: manifold_unified_run_v0

Scope: fresh cross-backend audit of `system_v6/sims/manifold_unified_run_v0/`. Read-only except this `audit_verdict.md`; no `git add` or commit. Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`.

Verdict: **QUALIFIED PASS at `scratch_diagnostic` ceiling only.**

The packet earns: first bounded simultaneous n=3 all-layer scratch run over one shared step-scoped trajectory envelope, with a computed cross-layer consistency matrix and three-engine/source-backed validators passing.

The packet does not earn: manifold-level admission, bridge/axis evidence, an `M(C,t)` theorem, formal proof of the entire geometric constraint manifold, committed-result status for this untracked packet, or the stronger claim that every layer row is freshly recomputed at every ratchet step.

## Audit route truth

- Main controller read authority/contracts and v4.2 packet, ran local source/result archaeology, validators, and scratch recomputation.
- Three Codex parent audit lanes completed: Q1 one-thing lineage, Q2/Q3 recomputation, and Q4-Q7 controls/schema/fence.
- This was **PARTIAL Wizard v4.2 Max Assembly**, not FULL: no validated child/subsubagent receipt bundle was accepted into topology counts. Parent receipts were used as audit side evidence and rechecked locally where load-bearing.

## Fresh checks run

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/validate_manifold_unified_run_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed --strict-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
git status --short -- system_v6/sims/manifold_unified_run_v0 system_v6/receipts/audit_bar_calibration_20260610.md
git cat-file -t 1b36e4a3c
git cat-file -t a54224476
git cat-file -t cdf437053
```

Validator outputs were `ok: true`. The three named parent commit hints resolve to commits in this checkout. `git status` reports `?? system_v6/sims/manifold_unified_run_v0/`, so this audit accepts only the on-disk scratch packet, not a committed packet.

One scratch recomputation command was local Python via stdin and wrote no repo files. One exploratory `jq` query was malformed and discarded; it is not used as evidence.

## Q1: one-thing check

Status: **PASS for step-scoped trajectory lineage; PARTIAL for row-local/engine-artifact lineage.**

Evidence:

- `build_card.md:8` declares one shared trajectory over S2/S3/S5/S6/spinor/flux/entropy/deformation rows.
- `manifold_unified_run_v0_common.py:182-313` builds the four-step trajectory from one parent-derived site set.
- `manifold_unified_run_v0_common.py:193-200` computes one `state_object_id` from the carrier, site rows, sequence, and seed parent.
- `manifold_unified_run_v0_common.py:294-310` stamps each step with that state id and a chained `trajectory_step_id`.
- `manifold_unified_run_v0_common.py:633-650` accepts only one distinct state id.
- `manifold_unified_run_v0_envelope_results.json:1190-1196` and `:1663-1677` record one distinct id: `b3f17fa7b1294471d51e917da05219c1b6431908a33e7a4bb05b99af879ac1fd`.
- Result step ids carry that state id at `manifold_unified_run_v0_envelope_results.json:2161`, `:2693`, `:3255`, and `:3770`.

Named caveat `CAVEAT_Q1_ROW_LOCAL_IDS`: nested rows such as `s2_geometry`, `s3_density_probe`, leakage, and spinor rows inherit the enclosing step lineage; they do not each carry their own `state_object_id`.

Named caveat `CAVEAT_Q1_ENGINE_ARTIFACT`: JAX/PyTorch call `build_core()` again (`manifold_unified_run_v0_jax.py:166`, `manifold_unified_run_v0_pytorch.py:96`) and Julia reads parents directly (`manifold_unified_run_v0_julia.jl:123-127`). This supports deterministic shared-source recomputation, not consumption of one persisted trajectory artifact by every engine.

## Q2: cross-layer consistency matrix

Status: **PASS.**

The matrix is typed by row class, not smoothed into one global epsilon:

- `diagnostic_float`: 12/12 pass.
- `diagnostic_float_plus_exact_enum`: 12/12 pass.
- `exact_symbolic_and_float`: 4/4 pass.
- `integer_scaled_plus_diagnostic_float`: 4/4 pass.
- `ledger_enum`: 4/4 pass.

The source creates typed rows at `manifold_unified_run_v0_common.py:320-399`; the result records `all_pass: true` and no findings at `manifold_unified_run_v0_envelope_results.json:292-295`.

Independent recomputations:

- Entropy convention: step-2 lens quotient recomputed `log(4) = 1.3862943611198906`, matching the envelope `drop_float` exactly (`manifold_unified_run_v0_envelope_results.json:2789-2795`) and the a54224476 entropy convention parent. A second parent-aligned check from the audit lane matched step-1 `k_leaf_union = 3.8438184547752363` with delta `0.0`.
- S2 holonomy: at q0 step 2, recomputed `-2*pi*cos(2*eta)` from `eta = 0.392699081699` as `-4.442882938155915`; envelope reports `-4.442882938156`, delta `8.53e-14`, inside diagnostic-float exactness class. Formula source: `manifold_unified_run_v0_common.py:127-147`; committed S2 formula is consumed from `geo_s2_connection_flux_foliation_v0`.
- Network current vs continuity identity: q0 step 3 integer-scaled recompute gives outgoing-minus-incoming `-160465274253`; `local - divergence = 524957644820`; reported network is `524957644820`; residual `0`. Proof rows are in `manifold_unified_run_v0_envelope_results.json:3312-3335` and solver proof fields in `:958-1018`.

## Q3: simultaneous recomputation

Status: **PARTIAL.**

Two layers at step 2+ are genuinely step-dependent:

- `entropy_ledger_row` changes across steps 1, 2, and 3 (`manifold_unified_run_v0_common.py:239-290`; result step-2 entropy at `manifold_unified_run_v0_envelope_results.json:2782-2796`, step-3 entropy at `:3295-3311`).
- `deformation_mode` changes across steps 1, 2, and 3 (`manifold_unified_run_v0_common.py:249-290`; result step-2 WARP at `manifold_unified_run_v0_envelope_results.json:2702-2780`, step-3 COMPRESSION at `:3264-3293`).

Named caveat `CAVEAT_Q3_CARRIED_ROWS`: the pre-hardening blanket recomputation wording was not earned. Source built shared base rows once and injected them into every step. Steps 1-3 all used `step_network(... conditioned=True)`, so `s2_geometry`, `s3_density_probe`, `s5_s6_terrain_flow`, `flux_continuity`, spinor rows, and leakage rows were not honestly separated into invariant versus dependent families. This was compatible with a shared-state invariant-layer run, but not proof of fresh per-step recomputation for every row family.

## Q4: rigidity re-fired in situ

Status: **PASS for finite parent-row rigidity consumption; PARTIAL for fresh unified-set proof.**

Evidence:

- Unified steps mark ratcheted rigidity rows as refired: step 2 WARP at `manifold_unified_run_v0_envelope_results.json:2702-2780`; step 3 COMPRESSION at `:3264-3293`.
- The cross-layer matrix requires no expansion mode for every step (`manifold_unified_run_v0_common.py:386-399`).
- Deformation controls record `pure_addition_never_expands` as z3/cvc5 `unsat` and quotient erased flip as z3/cvc5 `unsat` with phase-refined `sat` controls (`manifold_unified_run_v0_envelope_results.json:199-239`).

Named caveat `CAVEAT_Q4_PARENT_RIGIDITY`: the unified packet consumes the finite rows from `mct_dynamic_deformation_v0`; it does not build a new continuum/all-operation rigidity theorem or a new independent set-membership proof over all possible unified states.

## Q5: controls

Status: **PASS with parent-refire caveat.**

Per-layer erasure controls present and firing include:

- `deformation_pure_addition_never_expands`: z3/cvc5 `unsat`, fired.
- `deformation_quotient_erased_flip`: z3/cvc5 `unsat`, phase-refined controls `sat`.
- `density_quotient`: pass.
- `entropy_wrong_flat_eta`: detected.
- `entropy_wrong_lens_group_order`: detected.
- `naive_conditioning`: pass/failure surfaced.
- `spinor_blind_quotient_first`: pass.

Evidence: `manifold_unified_run_v0_envelope_results.json:199-289`.

Layer-decoupled control split:

- Reproduces independently: `conditioned_total_abs_current` unified `0.242675773674` equals decoupled parent recompute; `zero_terrain_current` equals expected `0.0`.
- Differs under coupling: leaf conditioning changes total current `0.735575785391 -> 0.242675773674`; terrain erasure zeroes flux `-0.222173886214 -> 0.0`.

Evidence: `manifold_unified_run_v0_envelope_results.json:168-193`.

Nothing-excluded passes at the local identity/object-preservation level (`manifold_unified_run_v0_envelope_results.json:195-198`). The naive failure is explicit at `:267-283`.

Named caveat `CAVEAT_Q5_PARENT_CONTROL_PAYLOADS`: many controls are pulled from parent control payloads in `manifold_unified_run_v0_common.py:402-458`, not recomputed from first principles inside this unified runner.

## Q6: standard/schema/tool checks

Status: **PASS with untracked-packet caveat.**

- Schema/mode: `three_engine_sim_result_v1`, `mode: RATCHETED`, `classification: scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false` (`manifold_unified_run_v0_envelope_results.json:84-100`, `:1186-1189`, `:1543-1557`).
- Engine divergence: Julia/JAX/PyTorch all report `0.242675773674`, max divergence `0.0` on `step3.conditioned_total_abs_current` (`manifold_unified_run_v0_envelope_results.json:1064-1079`).
- Real Julia leg: imports/uses `QuantumOptics` and `Z3` (`manifold_unified_run_v0_julia.jl:4-9`), builds `NLevelBasis`/`Ket`/`dm` (`:101-118`), and writes a Julia-Z3 continuity proof (`:65-99`, `:157-168`).
- z3/cvc5/Julia-Z3 identity with erased flips: all report `unsat` with erased `sat`, with formula terms bound, edge-current terms in solver, and divergence derived in solver (`manifold_unified_run_v0_envelope_results.json:958-1018`; local targeted jq confirmed all three).
- Parent lineage: six consumed inputs are SHA-bound; the three primary parents carry commit hints `1b36e4a3c`, `a54224476`, `cdf437053` (`manifold_unified_run_v0_envelope_results.json:1218-1245`, `:1511-1515`).
- Capability receipts and one-to-one tool calls: receipt ids match tool-call ids (`manifold_unified_run_v0_envelope_results.json:106-155`, `:1197-1217`, `:1558-1661`).
- Tool manifests and depths include load-bearing z3/cvc5/sympy, QuantumOptics/Z3, torch_geometric/torch.func/sympy, with supportive JAX/torch where declared (`manifold_unified_run_v0_envelope_results.json:1-83`; `:1107-1184`).
- Versions and seed are recorded (`manifold_unified_run_v0_envelope_results.json:1517-1541`, `:1553`).
- No fixture/mock/dummy wording was found under the packet path. The only `theorem`/admission/bridge hits are fence/negative-control wording, not positive claim wording.
- Fence held: build card blocks manifold admission, bridge/axis, and `M(C,t)` theorem (`build_card.md:3-16`); envelope repeats disallowed claims and fence (`manifold_unified_run_v0_envelope_results.json:1058-1063`, `:1544-1551`).

Named caveat `CAVEAT_Q6_UNTRACKED_PACKET`: `git status --short -- system_v6/sims/manifold_unified_run_v0` reports the entire packet as untracked. This audit verifies the current on-disk scratch packet only.

Named caveat `CAVEAT_Q6_NONPRIMARY_COMMIT_HINTS`: non-primary consumed parents have SHA bindings but `commit_hint: null` in lineage; the three primary parents resolve to commits.

## Q7: closure

Earned:

- A bounded one-sequence, one-seed, n=3 simultaneous scratch run over the declared layer families.
- A computed cross-layer consistency matrix with no findings under per-row exactness classes.
- Fresh local validator pass, three-engine source-backed validator pass, and strict source-backed validator pass.
- Independent recomputation of entropy convention, S2 holonomy, and integer-scaled continuity identity.
- Real solver erased flips across z3, cvc5, and Julia-Z3.
- A named layer-decoupled split showing which rows reproduce independently and which differ under coupling.

Not earned:

- No manifold-level admission.
- No bridge/axis claim.
- No `M(C,t)` theorem.
- No formal proof of the whole geometric constraint manifold.
- No claim beyond one sequence, one seed state, n=3 scale.
- No claim that every nested row has its own lineage id.
- No claim that every layer family is freshly recomputed at every ratchet step.
- No committed packet status while the packet directory remains untracked.

## Final ceiling

Accepted public status label: `exists` for the untracked packet. The local validators passed and support the scratch diagnostic verdict, but this audit does not introduce a fifth public status label and does not call the packet `canonical by process` because the packet is untracked and this audit did not stage/commit it.

Claim ceiling: `scratch_diagnostic`, `promotion_allowed:false`, `formal_admission_allowed:false`.

Final verdict: **QUALIFIED PASS / GENUINE-WITH-NAMED-CAVEATS at scratch ceiling.**

## Builder hardening addendum - 2026-06-11

Status: **bounded hardening complete for Q1/Q3; Q4 remains honest scope.**

Closed `CAVEAT_Q3_CARRIED_ROWS`:

- Claim language is now: `step-dependent families recomputed per step; invariant families carried with stated justification`.
- `STEP-DEPENDENT`: `s2_geometry`, `s5_s6_terrain_flow`, `flux_continuity`, `entropy_ledger_row`, `deformation_mode`.
- `STEP-INVARIANT`: `s3_density_probe`, `spinor_signed_rows`, `s5_s6_leakage_rows`, `s6_taxonomy`.
- Each invariant family has a stated reason in `row_family_step_classification` explaining why the conditioned object is unchanged for that layer.
- The lens step now changes the S2 holonomy spectrum for `q0`: pre-lens `-4.442882938156`, lens `-1.110720734539`, post-lens `-1.110720734539`. The lifted holonomy value remains `-4.442882938156`; the changed row is the Z4 lens primitive holonomy spectrum.

Closed `CAVEAT_Q1_ENGINE_ARTIFACT` and `CAVEAT_Q1_ROW_LOCAL_IDS`:

- Persisted artifact: `system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.json`.
- Artifact SHA sidecar: `system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.sha256`.
- Artifact content hash: `63e283d11bba8ab88ead11d1fe2aff215161864e45bfc7f3722208fa01d1317c`.
- Julia, JAX, PyTorch, and the envelope all consume the persisted artifact and verify the hash before reading step state.
- Nested rows now carry `state_object_id`, `trajectory_step_id`, `row_step_class`, and `row_step_lineage_id`; validator gate `nested_row_lineage_present` is `true`.

Carried `CAVEAT_Q4_PARENT_RIGIDITY` as scope, not a fix:

- The packet still consumes finite rigidity rows from `mct_dynamic_deformation_v0`.
- No new continuum/all-operation rigidity theorem and no new independent set-membership proof are claimed.

Fresh full rerun and validators:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/manifold_unified_run_v0_trajectory.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/manifold_unified_run_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/manifold_unified_run_v0_pytorch.py
julia --project=system_v5/julia_carrier system_v6/sims/manifold_unified_run_v0/manifold_unified_run_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/manifold_unified_run_v0_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/validate_manifold_unified_run_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed --strict-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
```

All validator outputs returned `ok: true`. Byte-stable audited values retained include step-2 entropy drop `1.3862943611198906`, step-3 entropy drop `0.9162907318741551`, step-3 total current `0.242675773674`, and max engine divergence `0.0`. The intended diff is the new per-step S2 primitive holonomy spectrum at the lens step.

## Focused re-audit addendum - 2026-06-11

Scope: read-only re-audit of the Q1/Q3 hardening closures, except this appended addendum. I did not build this packet and did not run any builder that rewrites results. I did not `git add` or commit.

Q3 closure: **earned.** The row-family split is explicit and principled in source: `s2_geometry`, `s5_s6_terrain_flow`, `flux_continuity`, `entropy_ledger_row`, and `deformation_mode` are `STEP-DEPENDENT`; `s3_density_probe`, `spinor_signed_rows`, `s5_s6_leakage_rows`, and `s6_taxonomy` are `STEP-INVARIANT`, each with a non-empty `why` justification. Recomputed invariant check: after stripping lineage-only fields, `s3_density_probe` has the same payload hash at all four steps, `7437ac0c9b318cc7de5c47a7956f88494352c39af449abea23051627ee8636a1`, which supports the stated "rho unchanged" invariant argument for this bounded sequence.

Q3 decisive step-dependent check: the S2 holonomy-spectrum family genuinely changes at the lens step. For q0, the before/after/current reported and independently recomputed primitive holonomy values are:

```text
integrated_seed:     eta=0.392699081699, lens_group_order=null, spectrum=[-4.442882938156], recomputed=-4.442882938156
leaf_conditioning:   eta=0.392699081699, lens_group_order=null, spectrum=[-4.442882938156], recomputed=-4.442882938156
lens_quotient:       eta=0.392699081699, lens_group_order=4,    spectrum=[-1.110720734539], recomputed=-1.110720734539
terrain_restriction: eta=0.392699081699, lens_group_order=4,    spectrum=[-1.110720734539], recomputed=-1.110720734539
```

The envelope claim now reads exactly: `step-dependent families recomputed per step; invariant families carried with stated justification`. I found no positive "all layers recomputed" blanket claim. The remaining stronger language is fenced/negative only: the build card says the packet does not claim every layer family is freshly recomputed at every step, and the envelope lists `freshly recomputed every row family at every step` under `disallowed_claims`.

Q1 closure: **earned.** The persisted trajectory artifact exists at `results/manifold_unified_run_v0_step_trajectory_artifact.json` with sidecar `results/manifold_unified_run_v0_step_trajectory_artifact.sha256`. Fresh hash check matched sidecar `a7b502700bf37019974e57490f468d06141f2c6ddb2d45f8233a83e15f712254`; artifact content hash is `63e283d11bba8ab88ead11d1fe2aff215161864e45bfc7f3722208fa01d1317c`. Julia verifies before use in `load_verified_trajectory_artifact()`; JAX, PyTorch, and envelope call `build_core()`/`base_leg_payload()`, which now call `load_trajectory_artifact()` and verify both file SHA and content SHA before returning rows. The old deterministic rebuild path is now builder-only for `write_trajectory_artifact()`; engine/envelope consumption goes through the persisted artifact. Nested row lineage is present: validator gate `nested_row_lineage_present` returned `true`.

Byte-stability spot check: previously audited values remain byte-stable for the checked fields: step-2 entropy drop `1.3862943611198906`, step-3 entropy drop `0.9162907318741551`, step-3 total current `0.242675773674`, and max engine divergence `0.0`. The genuine replacement is the per-step S2 primitive holonomy spectrum at the lens step, verified above.

Fresh validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_unified_run_v0/validate_manifold_unified_run_v0.py
=> {"ok": true, "errors": [], "result_json": "/Users/joshuaeisenhart/Codex-Ratchet/system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed --strict-source-backed system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_envelope_results.json"}
```

One-line conclusion: **closures earned; final unified-run status remains QUALIFIED PASS / GENUINE-WITH-NAMED-CAVEATS at `scratch_diagnostic` ceiling: first simultaneous all-layer scratch run, one literal persisted trajectory, computed consistency matrix, n=3 scale, one sequence only, no manifold admission, no bridge/axis claim, no `M(C,t)` theorem, no promotion/formal admission.**
