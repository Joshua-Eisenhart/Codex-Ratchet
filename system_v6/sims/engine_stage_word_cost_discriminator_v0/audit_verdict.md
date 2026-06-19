# Fresh Audit Verdict: engine_stage_word_cost_discriminator_v0

Audit date: 2026-06-10.

Auditor role: codex1 cross-backend audit of codex2 builder output. Scope was read-only except this `audit_verdict.md`. I did not git add or commit.

VERDICT: MIXED, with the owner's locality-cost claim surviving at the computed finite sizes but not earning a clean SURVIVES packet.

The local 8-stage word result is real for this pure-state tensor-network lift: loop-local `double_720` max chi is `[4, 8, 4]` for n=8/12/16 in both Julia and quimb, and the all-to-all/Haar controls fire in quimb. The packet stays MIXED because (1) the random-word control was not like-for-like across engines, (2) Julia delegated all-to-all/Haar controls to quimb, and (3) capability-probe gates are missing for `ITensorMPS` and `quimb.tensor`. This is a cost discriminator only: no engine admission, no physics admission, no asymptotic linearity proof.

## Calibration Bar

Applied bar: `system_v6/receipts/audit_bar_calibration_20260610.md`.

Relevant calibration:

- Keep route genuineness, can-fail controls, capability-probe gate for load-bearing tools, erasure honesty, scratch ceilings, and fresh-context audits (`audit_bar_calibration_20260610.md:5`).
- Exact/symbolic rows need exactness-class stability, but diagnostic-float rows may move if movement is reported (`audit_bar_calibration_20260610.md:7-11`).
- One genuine derivation plus independent solver/cross-engine binding can satisfy the bar with an honest split label (`audit_bar_calibration_20260610.md:11`).

## Q1. Stage Word Genuine

Verdict: PASS WITH S4-LIFT CAVEAT.

The 8-stage word is pinned in both legs:

- `engine_stage_word_cost_discriminator_v0_jax.py:45-50` pins `word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne`, `seat_i_uses_word_i_mod_8`, and the action list `Ti_z_axis_ZZ, Fe_Rz_ZZ, Ti_down_ZZ, Fe_down_Rz_ZZ, Te_x_axis_XX, Fi_Rx_XX, Te_down_XX, Fi_down_Rx_XX`.
- `engine_stage_word_cost_discriminator_v0_jax.py:107-115` defines the same eight entries as D-loop Se/Ne/Ni/Si with Ti/Fe on Z, then I-loop Se/Si/Ni/Ne with Te/Fi on X.
- `engine_stage_word_cost_discriminator_v0_julia.jl:64-72` mirrors that word.
- Stored results record the seat rule: `traversal seat i receives STAGE_WORD[(i mod 8)+1]; double_720 repeats the traversal once` in `results/engine_stage_word_cost_discriminator_v0_jax_results.json` and `..._julia_results.json`.

The word is genuinely loop-local in the implemented dynamics:

- `engine_stage_word_cost_discriminator_v0_jax.py:181` sets `seat = (step - 1) % n`.
- `engine_stage_word_cost_discriminator_v0_jax.py:198-201` uses all-to-all pairs only in the `all_to_all` control; otherwise the two-site pairs are `((seat - 1) % n, seat)` and `(seat, (seat + 1) % n)`.
- `engine_stage_word_cost_discriminator_v0_julia.jl:139-160` implements the same seat and neighbor-pair rule with Julia 1-based indices.

Source tie:

- `system_v6/foundations/two_engine_readout_automaton_20260609.md:10-19` gives `C_D = Se->Ne->Ni->Si`, `C_I = Se->Si->Ni->Ne`, with deductive order alternating and inductive order paired.
- `system_v6/foundations/two_engine_readout_automaton_20260609.md:21-23` defines the abstract object as stage base `{Se,Ne,Ni,Si}` plus fibered readout/operator placement.
- `system_v6/foundations/working_math_scaffold_20260609.md:66-75` defines the S4 families: Ti Z-dephasing, Te X-dephasing, Fi X-rotation, Fe Z-rotation.
- `system_v6/sims/geo_s4_operator_stage_v0/geo_s4_operator_stage_v0_jax.py:35-46` pins `source_forms=(Ti=z_dephase,Te=x_dephase,Fi=x_rotation,Fe=z_rotation)`.

Named caveat: this packet uses a pure-state unitary axis-lift of S4 forms for tensor-network cost. It does not simulate the density-channel dephasing maps as mixed-state channels. The builder names this limit in `engine_stage_word_cost_discriminator_v0_jax.py:548-552` and the envelope disallows density-channel dephasing claims at `engine_stage_word_cost_discriminator_v0_envelope.py:187-193`.

## Q2. Headline Numbers

Verdict: PASS for computed rows and n=8 no-silent-truncation check.

Stored local `double_720` max chi:

- Julia: n=8/12/16 = `[4, 8, 4]`.
- quimb/JAX-labeled lane: n=8/12/16 = `[4, 8, 4]`.
- Envelope `cost_readout.local_double_max_chi` records both as `[4, 8, 4]`.

Fresh recomputation:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import importlib.util, json
from pathlib import Path
path = Path('system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py')
spec = importlib.util.spec_from_file_location('ewc', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
row = mod.run_scenario(8, 'loop_local', 'double_720', dense_crosscheck=True)
print(json.dumps({'max_chi': row['max_chi'], 'dense_crosscheck': row['dense_crosscheck'], 'truncation': row['truncation']}, sort_keys=True))
PY
```

Fresh result:

- `max_chi = 4`.
- `chi_trace = [1,1,1,1,2,2,2,4,4,4,4,4,4,4,4,4]`.
- Dense-vs-MPS `fidelity = 1.0`, `infidelity = 0.0`, `truncation_error_reported_as_infidelity = 0.0`.
- Dense Schmidt ranks `[2,2,2,4,4,4,2]` match MPS bond sizes `[2,2,2,4,4,4,2]`.
- Truncation row: `cutoff = 1e-14`, `max_bond = null`, `max_norm_deviation_from_unit = 0.0`.

Julia truncation caveat: `engine_stage_word_cost_discriminator_v0_julia.jl:212-217` reports cutoff/maxdim plus norm-deviation proxy because `ITensorMPS.apply` does not expose discarded weight in this route.

## Q3. Controls' Teeth

Verdict: PASS for all-to-all/Haar controls in quimb; PARTIAL for cross-engine controls; RANDOM-WORD DIVERGENCE EXPLAINED.

All-to-all control:

- Stored quimb all-to-all `double_720`: n=12 max chi `64`, n=16 max chi `64`.
- Fresh rerun returned n=12 max chi `64` with seed `20272829` and n=16 max chi `64` with seed `20276829`.
- n=16 was run; it was not honestly capped by `max_bond` in quimb. `engine_stage_word_cost_discriminator_v0_jax.py:42` sets `MAX_BOND = None`, and stored/fresh rows show `max_bond = null`.

Haar baseline:

- Stored quimb Haar `double_720`: n=12 max chi `64`; n=16 max chi `256`.
- Envelope records `haar_n16_double_max_chi.jax = 256` and `julia = delegated_to_quimb`.

Random-word control:

- Stored quimb random `double_720`: `[8, 16, 16]`.
- Stored Julia random `double_720`: `[8, 8, 8]`.
- The named divergence is n=16: quimb `16`, Julia `8`.

Divergence adjudication:

The cause is different sampled random words, not demonstrated backend disagreement on the same word.

Evidence:

- Python uses `np.random.default_rng(seed)` at `engine_stage_word_cost_discriminator_v0_jax.py:241-242` and samples `rng.integers(0, len(STAGE_WORD))` at `engine_stage_word_cost_discriminator_v0_jax.py:174-177`.
- Julia uses `MersenneTwister(seed)` at `engine_stage_word_cost_discriminator_v0_julia.jl:175` and samples `rand(rng, 1:length(STAGE_WORD))` at `engine_stage_word_cost_discriminator_v0_julia.jl:131-134`.
- First eight recorded n=16 random `double_720` stages differ between engines. Julia starts `Ne/Se/Si/Ne/Ne/Ne/Ne/Ne`; quimb starts `Ni/Se/Ne/Si/Si/Ni/Ne/Se`.

Like-for-like fix test:

I monkeypatched the quimb lane to use Julia's recorded 32-step random stage sequence for n=16 `double_720`. Result:

- quimb original random n=16 max chi: `16`.
- quimb with Julia random sequence max chi: `8`.
- chi trace with Julia sequence: `[1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4,4,4,4,4,4,8]`.

Therefore the divergence is explained by non-identical RNG/control fixtures under the same observable name. It should not be read as a numerical truncation or backend disagreement. It is still an audit caveat because the envelope labels it as the same named observable set.

## Q4. MIXED Verdict

Verdict: BUILDER MIXED IS JUSTIFIED; independent verdict is MIXED.

Builder logic:

- `engine_stage_word_cost_discriminator_v0_envelope.py:116-124` returns `EXCLUDED` if local boundedness or all-to-all firing fails; returns `SURVIVES` only if local boundedness, all-to-all, Haar, and random-word separation all pass; otherwise returns `MIXED`.
- `engine_stage_word_cost_discriminator_v0_envelope.py:264` says MIXED means loop-local chi stayed bounded and all-to-all/Haar controls fired, but shuffled-word did not separate at every n in both engines.
- The quimb/JAX-labeled leg alone records `cost_verdict = SURVIVES` because its own random-word rows are `[8, 16, 16]`; the combined envelope records `cost_readout.verdict = MIXED` after comparing against Julia random rows `[8, 8, 8]`.

Why not EXCLUDED:

- Local word is bounded at computed n in both engines.
- quimb all-to-all and Haar controls fire.
- n=8 dense crosscheck gives exact fidelity and no apparent truncation loss.

Why not SURVIVES:

- Random-word separation is not a clean cross-engine result: Julia n=12 random `8` equals local `8`, and n=16 quimb-vs-Julia divergence was caused by different sampled words.
- Nonlocal all-to-all/Haar controls are delegated to quimb rather than run in Julia.
- Capability-probe gates are missing for declared load-bearing `ITensorMPS` and `quimb.tensor`.

Independent verdict on the same vocabulary: MIXED.

The finite locality-cost claim survives as a bounded computed diagnostic, but the packet does not earn a full SURVIVES verdict under the calibrated bar because the strongest controls and tool gates are not all clean.

## Q5. Periodicity Proof

Verdict: PASS as a finite readout-grammar proof; not a cost-growth proof.

Encoding:

- z3: `engine_stage_word_cost_discriminator_v0_jax.py:318-342` creates four Boolean readout bits, asserts alternating constraints `r0=r2`, `r1=r3`, `r0!=r1`, and paired constraints `r0=r1`, `r2=r3`, `r0!=r2`. Joint assertion is UNSAT.
- z3 erased control removes the nontrivial inequalities and keeps equalities, making a common constant readout SAT; stored control model is all false.
- cvc5: `engine_stage_word_cost_discriminator_v0_jax.py:345-380` mirrors the same Boolean equality/inequality structure with `checkSat()`.

Fresh recomputation:

- z3 positive verdict: `unsat`.
- z3 erased control: `sat`.
- cvc5 positive verdict: `unsat`.
- cvc5 erased control: `sat`.

The proof is derived from finite Boolean readout constraints in the source, not from a precomputed result literal. Caveat: it proves alternating-vs-paired readout incompatibility, not MPS cost boundedness.

## Q6. Standard Hygiene

Verdict: PARTIAL PASS WITH NAMED CAVEATS.

Passes:

- Mode and ceiling are explicit: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Honest lane naming: `engine_stage_word_cost_discriminator_v0_jax.py:2-5` says the file uses the validator-compatible JAX label but the load-bearing Python tensor-network tool is quimb.
- Envelope disallows proof of asymptotic linearity, physics/engine admission, formal admission, density-channel dephasing simulation, and extrapolation beyond n=8/12/16.
- Wall-clock, memory rows, and seeds are present in Python rows; Julia rows include wall-clock and memory units and a top-level seed.
- Tool calls are structured for quimb, z3, cvc5, ITensors, and ITensorMPS.
- No fixture wording was found by source/result search.

Named caveats:

1. `capability_probe_missing`: `scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py` reports `quimb` ok, `z3` ok, `cvc5` ok, but `quimb.tensor` missing probe. The same gate on the Julia source reports `ITensors` ok but `ITensorMPS` missing probe.
2. `strict_source_backed_validator_fail`: `scripts/validate_three_engine_sim_result.py --strict-source-backed ..._envelope_results.json` fails with `declared load-bearing packages imported but source-token-thin: quimb.tensor`.
3. `random_word_not_like_for_like`: random-word JAX/quimb vs Julia divergence is explained by different RNG APIs and sampled stage words, so the control is useful but not a same-word cross-backend comparison.
4. `nonlocal_controls_delegated`: all-to-all and Haar controls are quimb-only in this builder pass; Julia records them as delegated.
5. `julia_truncation_proxy`: Julia records cutoff/maxdim plus norm-deviation proxy, not discarded-weight truncation.
6. `version_metadata_partial`: Python records package versions for quimb/cvc5/numpy and `z3=null`; Julia records package names but not explicit package versions in the result.
7. `S4_lift_not_density_channel`: this packet lifts the S4 operator word into pure-state local unitaries for tensor-network cost. It does not rerun the S4 density/Bloch quotient channels.

## Commands And Checks

Fresh commands run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported engine_stage_word_cost_discriminator_v0_jax.py and ran:
# run_scenario(8, 'loop_local', 'double_720', dense_crosscheck=True)
# z3_periodicity_proof()
# cvc5_periodicity_proof()
PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported the same source and ran:
# run_scenario(12, 'all_to_all', 'double_720')
# run_scenario(16, 'all_to_all', 'double_720')
# run_scenario(16, 'random_word', 'double_720')
# run_scenario(16, 'random_word', 'double_720') with Julia's recorded random stage sequence
PY
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/engine_stage_word_cost_discriminator_v0/results/engine_stage_word_cost_discriminator_v0_envelope_results.json
=> FAIL: source-token-thin quimb.tensor
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py
=> FAIL: quimb.tensor missing_probe

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_julia.jl
=> FAIL: ITensorMPS missing_probe
```

## Final Ceiling

Accepted ceiling: computed scratch cost discriminator for Reading B at n=8/12/16. The finite local word is bounded in the stored and freshly checked rows, and quimb all-to-all/Haar controls show higher cost. The packet may support "the committed 8-stage loop-local word is cheaper than the tested nonlocal controls at these finite sizes."

Rejected ceiling: asymptotic linearity, generic efficient proof, engine admission, physics admission, density-channel dephasing simulation, canonical S4 completion, or full cross-backend SURVIVES verdict.

Final line: VERDICT=MIXED; local-loop boundedness survives the finite checks, but control parity/tool-gate caveats block SURVIVES.

## Re-Audit Addendum: H1/H2/H3 Hardening Final Verdict

Re-audit date: 2026-06-11.

Auditor role: independent Codex re-audit of the hardening that followed the MIXED verdict above. Scope was read-only except appending this addendum. I did not build or harden the packet, and I did not git add or commit.

FINAL COST-DISCRIMINATOR VERDICT: SURVIVES.

One-line reason: the named hardening resolves the three prior blockers for the finite cost-discriminator packet: shared-word random controls now agree across engines, Julia has its own bounded all-to-all rows plus an honest n=16 boundary row, and load-bearing capability aliases are additive/probe-backed without weakening fake-route failure.

This is a cost-discriminator verdict only: no engine admission, no physics admission, no formal admission, no density-channel dephasing claim, and no asymptotic claim beyond the computed n=8/12/16 rows.

### H1. Shared Stored Random Word

Verdict: CLOSED.

Evidence:

- `engine_stage_word_cost_discriminator_v0_jax.py` and `engine_stage_word_cost_discriminator_v0_julia.jl` both store `SHARED_RANDOM_STAGE_INDICES` as explicit packet data and replay it for `scenario=random_word`.
- The table indexes the full 8-entry `STAGE_WORD`, preserving operator identity:
  - `0 Se D Ti↑ Z Ti`
  - `1 Ne D Fe↑ Z Fe`
  - `2 Ni D Ti↓ Z Ti`
  - `3 Si D Fe↓ Z Fe`
  - `4 Se I Te↑ X Te`
  - `5 Si I Fi↑ X Fi`
  - `6 Ni I Te↓ X Te`
  - `7 Ne I Fi↓ X Fi`
- Shared `double_720` index lengths match the traversal lengths: n=8 has 16 entries, n=12 has 24, and n=16 has 32. The n=16 first eight mapped entries are `6:Ni/I/Te↓/X/Te`, `0:Se/D/Ti↑/Z/Ti`, `7:Ne/I/Fi↓/X/Fi`, `3:Si/D/Fe↓/Z/Fe`, `3:Si/D/Fe↓/Z/Fe`, `2:Ni/D/Ti↓/Z/Ti`, `7:Ne/I/Fi↓/X/Fi`, `4:Se/I/Te↑/X/Te`.
- Named shared-word random `double_720` chi now agrees at every n:
  - Julia: n=8/12/16 = `[8, 16, 16]`.
  - quimb/JAX-labeled lane: n=8/12/16 = `[8, 16, 16]`.
  - This includes the predicted n=16 repair from the prior monkeypatch experiment: `16 == 16` is the current stored shared-word row, while the prior Julia-word replay prediction `8 == 8` explained the old divergence mechanism.
- Own-sampled random rows are separately labeled supplementary:
  - Julia own-sampled `double_720`: `[8, 8, 8]`.
  - quimb/JAX own-sampled `double_720`: `[8, 16, 16]`.

### H2. Julia All-To-All Controls

Verdict: CLOSED WITH HONEST n=16 BOUNDARY.

Evidence:

- Stored Julia all-to-all `double_720` rows are present:
  - n=8 max chi `8`, status `computed`.
  - n=12 max chi `64`, status `computed`.
  - n=16 status `infeasible_delegated`, row role `honest_infeasibility_boundary_stress`.
- Fresh in-memory Julia recomputation from the current source, without rewriting result JSON, regenerated the n=12 all-to-all `double_720` row as:
  - `max_chi=64`, `final_chi=64`, `status=computed`, `max_norm_deviation_from_unit=0.0`.
- The boundary row is honest: it does not fake a Julia n=16 all-to-all value, and the envelope records quimb n=16 all-to-all `64` with Julia `infeasible_delegated`.

### H3. Capability Aliases And Gate Strength

Verdict: CLOSED.

Evidence:

- Capability probe receipts exist and pass:
  - `system_v4/probes/a2_state/sim_results/quimb_capability_results.json`: `summary.all_pass=true`.
  - `system_v4/probes/a2_state/sim_results/itensors_capability_results.json`: `summary.all_pass=true`.
  - `system_v4/probes/a2_state/sim_results/z3_capability_results.json`: `summary.all_pass=true`.
  - `system_v4/probes/a2_state/sim_results/cvc5_capability_results.json`: `summary.all_pass=true`.
- `scripts/verify_load_bearing_has_capability_probe.py --sim engine_stage_word_cost_discriminator_v0_jax.py` exits 0. It maps `quimb.tensor -> quimb` and reports no violations.
- `scripts/verify_load_bearing_has_capability_probe.py --sim engine_stage_word_cost_discriminator_v0_julia.jl` exits 0. It maps `ITensorMPS -> itensors` and reports no violations.
- The gate-script diff is additive alias registration only: it adds `quimb.tensor/quimb_tensor -> quimb` and `ITensorMPS/ITensorMPS.jl -> itensors`, with no weakening of missing-probe behavior.
- Fake-route negative control still fails: a temp sim declaring `definitely_fake_tool_for_audit` as `load_bearing` reports `missing_probe` and exits 1.
- `scripts/validate_three_engine_sim_result.py --strict-source-backed engine_stage_word_cost_discriminator_v0_envelope_results.json` exits 0.

### Byte-Stable / Exact Rows

Verdict: PASS for the audited exact rows.

Evidence:

- Local loop `double_720` max chi remains byte-stable at `[4, 8, 4]` in both Julia and quimb/JAX-labeled results.
- Shared random-word `double_720` max chi is `[8, 16, 16]` in both engines.
- Julia all-to-all boundary controls are n=8 `8`, n=12 `64`, n=16 `infeasible_delegated`.
- quimb/JAX all-to-all `double_720` rows are n=8 `16`, n=12 `64`, n=16 `64`.
- quimb/JAX Haar `double_720` n=16 remains `256`.
- Dense n=8 loop-local crosscheck remains `fidelity=1.0`, `infidelity=0.0`, with dense Schmidt ranks matching MPS bond sizes.
- SMT polarity remains the same and load-bearing: z3 positive `unsat`, z3 erased control `sat`; cvc5 positive `unsat`, cvc5 erased control `sat`.
- Builder source/result language explicitly reserves verdict promotion for independent re-audit and does not self-upgrade the packet to SURVIVES.

### Commands Run

Fresh checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py
=> exit 0; quimb and quimb.tensor both ok

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_julia.jl
=> exit 0; ITensors and ITensorMPS both ok

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/engine_stage_word_cost_discriminator_v0/results/engine_stage_word_cost_discriminator_v0_envelope_results.json
=> exit 0

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e '<in-memory source load without exit(main()); run_scenario(12, "all_to_all", "double_720")>'
=> max_chi=64, final_chi=64, status=computed, max_norm_deviation_from_unit=0.0
```

Negative control:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim /tmp/fake_capability_route_XXXX.py
=> exit 1; definitely_fake_tool_for_audit missing_probe
```

### Final Ceiling

Accepted ceiling: finite scratch cost discriminator for the declared pure-state S4-axis lift at n=8/12/16. With like-for-like controls in place, local word chi `[4, 8, 4]` stays bounded against all-to-all controls reaching `64`, Haar reaching `256`, and shared-word random controls agreeing across Julia and quimb/JAX-labeled lanes.

Rejected ceiling: engine admission, physics admission, formal admission, density-channel dephasing simulation, canonical S4 completion, proof of asymptotic linearity, or extrapolation beyond computed n.

Final line: VERDICT=SURVIVES for the finite cost discriminator only.
