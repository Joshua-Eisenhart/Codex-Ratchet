# Fresh Audit Verdict: geo_s1_quaternion_model_v0

Audit stance: I did not build this sim. I inspected the local source/result files and ran the read-only validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json"}
```

## Q1. R Identification

Verdict: PASS. The conversion rotation is one fixed global matrix, not a per-point fit.

Quoted source:

- JAX pins `R_Q_TO_COMPLEX = jnp.asarray([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]], dtype=jnp.float64)` at source scope, before sample generation. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:43`.
- The same JAX leg applies that one matrix globally with `hopf_after_r = hopf_q @ R_Q_TO_COMPLEX.T`, while `no_r_dev` and `after_r_dev` are separately computed. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:187-191`.
- Julia likewise pins `const R_Q_TO_COMPLEX = [0.0 0.0 -1.0; 0.0 1.0 0.0; 1.0 0.0 0.0]`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_julia.jl:22-23`.

Result evidence: the emitted matrix has determinant `1.0`, JAX after-R deviation is `5.551115123125783e-16`, Julia after-R deviation is `2.220446049250313e-16`, and the wrong-convention skip-R deviations are about `1.414`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:19-51`.

## Q2. Method Independence

Verdict: PASS for method diversity; PASS for explicit double-cover volume numbers.

Quoted source:

- The envelope assembles three linking routes from different legs: PyTorch Gauss integral, JAX Hopf invariant integral, and PyTorch projected crossing count. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_envelope.py:96-100`.
- The Gauss method performs a double sum over stereographic curves using cross products and the `1/(4*pi)` normalization. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_pytorch.py:88-102`.
- The Hopf integral route computes a lattice `raw_abs_integral_A_wedge_F` and normalizes by `4*pi^2`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:121-132`.
- The crossing route explicitly scans segment intersections in a projected diagram and returns `signed_crossing_sum`, `linking_number`, and `crossing_count`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_pytorch.py:105-130`.

Linking result evidence: Gauss `0.9999828150550844`, Hopf integral `1.0000062749530492`, crossing `1.0`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:667-686`.

Volume route evidence: PyTorch Monte Carlo `19.381999999999998`, JAX metric lattice corrected `19.73923976772882`, and Julia quaternion measure `19.739208802178716`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:688-708`.

Double-cover volume evidence: the metric route emits both the naive `4*pi^2`-scale chart integral and corrected value. Final row has `naive_chart_integral_2_to_1_cover = 39.47847953545764`, `naive_target_4pi2 = 39.47841760435743`, `cover_correction = divide_by_2`, and `corrected_volume = 19.73923976772882`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:232-243`.

## Q3. Dictionary Honesty

Verdict: PASS. The dictionary and quaternion Hopf computation are algebraic and source-local; the quaternion Hopf image is not computed by converting to complex first.

Quoted source:

- JAX dictionary: `q_to_z` returns `[q0 + i q1, q2 - i q3]`, and `z_to_q` is the inverse layout. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:73-78`.
- Julia dictionary: `q_to_z(q)` returns `ComplexF64[q[1] + im * q[2], q[3] - im * q[4]]`, with inverse `z_to_q`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_julia.jl:45-51`.
- Quaternion Hopf is implemented as quaternion multiplication: `return quat_mul(quat_mul(q, i_unit), quat_conj(q))[..., 1:4]`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:103-105`.
- Julia mirrors that: `quat_hopf(q) = quat_mul(quat_mul(q, [0.0, 1.0, 0.0, 0.0]), quat_conj(q))[2:4]`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_julia.jl:57-69`.

Result evidence: emitted Q1 roundtrip deviations are `0.0`; group-law deviations are `2.482534153247273e-16` in Julia and `2.618455766672135e-16` in JAX. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:3-15`.

## Q4. Double Cover Along Path

Verdict: PASS for endpoints; PARTIAL for intermediate-sample reporting. The source computes the path action at `2*pi` and `4*pi`, but the result does not emit intermediate samples along the path.

Quoted source:

- JAX computes `q2 = quat_mul([cos(pi), sin(pi), 0, 0], q0)` and `q4 = quat_mul([cos(2*pi), sin(2*pi), 0, 0], q0)`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:203-205`.
- Julia computes the same endpoint check with `q2` and `q4`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_julia.jl:105-107`.

Result evidence: JAX emits `q_2pi_plus_q0_norm = 1.3877787807814457e-16` and `q_4pi_minus_q0_norm = 2.435541875787129e-16`; Julia emits `0.0` and `2.5438405243138006e-16`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:281-292`.

Named gap: no emitted intermediate path samples are present in `Q5_double_cover`; only endpoint residuals are emitted.

## Q5. Standard Checks

Verdict: PASS for validator, raw-value SMT, controls, cross-leg independence, and NumPy boundary; ceiling is correctly low.

Quoted source/result:

- Raw-value SMT binds scaled values in both solvers: `raw_value_binding` has `gauss`, `hopf_integral`, and `crossing_count` all at `1000000` with tolerance `1000`; z3 and cvc5 verdicts are `unsat`, and scrambled-fiber controls are `sat`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:410-450`.
- JAX source constructs good scaled values `[1_000_000, 1_000_000, 1_000_000]`, scrambled values `[1_000_000, 1_000_000, 0]`, and requires good `unsat` plus scrambled `sat`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:196-201` and `system_v6/sims/geo_s1_quaternion_model_v0/geo_s1_quaternion_model_v0_jax.py:248-256`.
- Tautological controls fired: broken dictionary, single-method, wrong-convention, and scrambled-fiber controls are all present. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:353-408`.
- Cross-leg independence is explicit in the envelope: all three engines have `reads_peer_result: false`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:493-599`.
- NumPy is only the control lane; `foreign_runtime_manifest` labels `numpy_control` separately and declares no tensor exchange. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:624-663`.
- The claim ceiling is `classification = scratch_diagnostic`, `promotion_allowed = false`, and `formal_admission_allowed = false`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:352` and `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:665-714`.

Build gates all emit true, including `controls_fired`, `proofs_pass`, `Q1`-`Q5`, and `ceiling_exact`. Cite: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:317-329`.

## Hand Recomputation

1. Quaternion product vs SU(2) product.
   - Hand sample: `q=(0.5,0.5,0.5,-0.5)`, `r=(0.5,-0.5,0.5,0.5)`.
   - Hamilton product gives `q*r=(0.5,0.5,0.5,0.5)`.
   - SU(2) matrix product using `[[a+bi,c+di],[-c+di,a-bi]]` matched `SU2(q*r)` with max entry difference `0.0`.

2. Quaternion Hopf image by hand.
   - Same `q`: `q*i*qbar = (0,0,0,-1)`, vector part `(0,0,-1)`.
   - Applying fixed `R` gives `(1,0,0)`.
   - Complex dictionary gives `z1=0.5+0.5i`, `z2=0.5+0.5i`, so complex Hopf image is `(1,0,0)`.
   - Max component difference after `R`: `0.0`.

3. Crossing count.
   - From the final emitted crossing record, the two emitted sample crossing signs are `+1,+1`; sample sign sum is `2`, so sample-derived linking is `2/2 = 1`.
   - Source-level recomputation of `crossing_count(360)` returned the same full aggregate as the result: `crossing_count=2`, `signed_crossing_sum=2.0`, `linking_number=1.0`, with the same two sample crossings.
   - Gap: the result does not emit full projected curve coordinate data, so a recomputation solely from emitted projection coordinates is impossible from this artifact. The emitted aggregate and sample crossings are consistent, and the source algorithm recomputes the aggregate.

## Named Gaps

- Q5 double-cover emits endpoint residuals but not intermediate path samples.
- Crossing-count result emits aggregate crossing rows and sample crossings, but not the full projected curve coordinates. This blocks a fully independent crossing recomputation from emitted projection data alone.
- PyTorch `aligned_packages_load_bearing` lists only `torch.func`, while `claim_path_tools` and `TOOL_INTEGRATION_DEPTH` mark `torch` load-bearing for Gauss/Monte Carlo. The validator accepts this, but the metadata is slightly inconsistent.
- The Monte Carlo volume route is intentionally loose (`abs_error` about `0.3572`, tolerance `<0.5`). It is acceptable as one noisy independent route, not precision evidence.

## Verdict

VERDICT: SURVIVES AS `scratch_diagnostic`; no promotion.

The core claim survives this audit: fixed global `R`, honest quaternion dictionary, quaternion-multiplication Hopf path, distinct linking and volume routes, raw-value SMT controls, and explicit low ceiling are all present and validator-clean. The artifact should not be raised above `scratch_diagnostic` because the double-cover and crossing-count emissions are not rich enough for the stronger audit request: intermediate path samples and full projected crossing coordinate data are missing.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Post-Hardening Re-Audit Addendum - 2026-06-10

Audit stance: focused re-audit only. I did not build, audit, or harden this sim. I recomputed the requested checks from the emitted artifacts and appended this addendum without rewriting the prior verdict.

### Named Gap Closure

1. Double-cover path samples: CLOSED. The envelope now emits `Q5` path samples for both JAX and Julia with `path_sample_intervals = 16`; JAX samples run through `t_over_pi = 0.0 -> 4.0`, with the continuous overlap sequence crossing `psi_overlap_with_q0 = -0.9999999999999996` at `t_over_pi = 2.0`, and Julia emits the same crossing as `psi_overlap_with_q0 = -1.0` at `t_over_pi = 2.0`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:8321-8326`, `:8439-8451`, `:8569-8573`, `:8686-8698`. My recomputation over the emitted samples found 17 samples per leg, strictly increasing `t_over_pi`, max adjacent quaternion-step norm about `0.390180644032257`, and overlaps `+1 -> -1 -> +1`.

2. Projected curve coordinates and crossing recomputation: CLOSED. The envelope now emits projected coordinates for both curves under the crossing route, including `curve1_projected_xyz`, `curve2_projected_xyz`, `crossing_plane = xy`, and final `segments_per_curve = 360`, `signed_crossing_sum = 2.0`, `final_value = 1.0`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:125-132`, `:739-755`, `:8210-8227`. Recomputing from the emitted JSON coordinates alone, using consecutive emitted points as segments and the emitted `xy`/`z` crossing convention, gave:

```text
120 segments: crossing_count=2, signed_sum=2.0, linking=1.0
240 segments: crossing_count=2, signed_sum=2.0, linking=1.0
360 segments: crossing_count=2, signed_sum=2.0, linking=1.0
```

For the final 360-segment row, the recomputed hits were `(segment_curve1=17, segment_curve2=346, sign=+1, z_delta=-0.708878292056549)` and `(segment_curve1=182, segment_curve2=190, sign=+1, z_delta=0.7405477794846742)`, matching the emitted crossing records at `:8210-8218`.

3. Metadata consistency: CLOSED. The prior mismatch is gone for the PyTorch leg: `claim_path_tools` includes `torch` and `torch.func`; PyTorch `aligned_packages_load_bearing` lists both `torch` and `torch.func`; and the PyTorch engine-local `tool_integration_depth` marks both as `load_bearing`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:8867-8874`, `:9105-9128`. The top-level `TOOL_INTEGRATION_DEPTH` remains envelope-assembly-only for `hashlib/json/pathlib` supportive tooling, so the honest story is: envelope tools supportive at top level; claim-path load bearing belongs to engine-local tool metadata.

4. Monte Carlo volume role: CLOSED. `mc_volume_role` is present on the Monte Carlo route rows and in the multi-method volume table, labeled `loose independent route (abs_error ~0.357, tol 0.5); not precision evidence`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:8283-8310`, `:9212-9218`.

### Byte-Stability Check

The requested stable values are present: Julia group law `2.482534153247273e-16`, Julia Hopf-after-R `2.220446049250313e-16`, Gauss linking `0.9999828150550844`, Hopf-integral linking `1.0000062749530492`, crossing linking `1.0`, Monte Carlo volume `19.381999999999998` (the requested `19.382` rounded), JAX corrected volume `19.73923976772882`, and Julia volume `19.739208802178716`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:10-15`, `:43-47`, `:78-84`, `:112-123`, `:8218-8227`, `:8270-8310`, `:9221-9233`.

All solver verdicts are stable and load-bearing: `cvc5` `unsat`, `julia_z3` `unsat`, and `z3` `unsat`; the scrambled-fiber controls remain `sat` for `cvc5` and `z3`. Cites: `system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json:8933-8973`.

### Validator Reruns

Using the Makefile interpreter `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json"}
```

Additional stricter check also passed:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/geo_s1_quaternion_model_v0/results/geo_s1_quaternion_model_v0_envelope_results.json"}
```

### Stale Surface Check

Search found the prior append-only `audit_verdict.md` gap text still present as historical audit record, plus the intended Monte Carlo loose-route label. The current hardened result/source surfaces no longer imply the four named gaps remain open; this addendum supersedes the historical gap bullets without rewriting them.

Final line: all four named gaps are CLOSED under the post-hardening evidence checked here; validator reruns pass; the artifact remains `scratch_diagnostic`, no promotion.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; `S^3 ~= SU(2) ~= Sp(1)` is framed here as overlapping descriptions and a representation test, not competitor carriers.
