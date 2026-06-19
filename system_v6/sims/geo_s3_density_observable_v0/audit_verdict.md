# Audit verdict - geo_s3_density_observable_v0

Fresh audit date: 2026-06-10

Scope: read-only audit of `system_v6/sims/geo_s3_density_observable_v0`, except this `audit_verdict.md`.

Inputs checked:

- Sim folder: `system_v6/sims/geo_s3_density_observable_v0/`
- Blind expected file: `/tmp/s3_blind_expected_20260610.md`
- Build spec: `system_v6/receipts/s3_build_spec_20260610.md`

## Bottom line

VERDICT: PASS_WITH_NAMED_GAPS for the S3 scratch-diagnostic ceiling only.

The packet correctly builds the genuinely-new S3 density/observable items named by the build spec, preserves the ceiling, passes the repo validators, and recomputes the required formulas. It is not an S4/S5 channel-geometry result, not formal admission, and not promotable.

The main gaps are exactness/receipt gaps, not formula-killing math errors:

1. The result gives plane offset as `c-a0`, but the blind expectation also asks for signed distance `(c-a0)/||a||`.
2. The entropy formula is correct as `H2((1+R)/2)`, but the result does not explicitly receipt the log base/bit convention or the `||r||=1` entropy edge handling.
3. D6 ellipsoid/fixed-point/basin facts are deliberately not computed as S3 claims, because the build spec forbids S4/S5 promotion here.
4. The requested H1-H7/E1-E6 pattern catalog was not found in the provided inputs or sim folder; this audit cannot certify that binding.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Source checks

Build-spec ceiling and scope:

- `system_v6/receipts/s3_build_spec_20260610.md:5` says the future packet ceiling is `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- `system_v6/receipts/s3_build_spec_20260610.md:17-23` marks dense Bloch fields, observable fields, Born fields, measurement updates, probe quotient map, trace/fidelity, and CPTP contractions as genuinely-new.
- `system_v6/receipts/s3_build_spec_20260610.md:24-25` marks channel ellipsoids, fixed points, and basins as out of scope.
- `system_v6/receipts/s3_build_spec_20260610.md:44` says not to build S4 channel ellipsoid image classification or S5 fixed-point/basin classification.
- `system_v6/receipts/s3_build_spec_20260610.md:131-135` requires `--require-pytorch --strict-source-backed`, honest tool depth, literal strength tokens, and no S4/S5 basin claim.

Blind expected anchors:

- `/tmp/s3_blind_expected_20260610.md:7-16` pins `sigma_y_standard`, the `-sigma_y_standard` Bloch basis, trace distance, and squared Uhlmann fidelity.
- `/tmp/s3_blind_expected_20260610.md:22-41` pins eigenvalues, positivity, determinant, purity, entropy, center/boundary controls, and outside-ball negative behavior.
- `/tmp/s3_blind_expected_20260610.md:47-62` pins `Tr(O rho)=a0+a.r`, level planes, signed distance, range, pinned-y, and nonlinear negative.
- `/tmp/s3_blind_expected_20260610.md:70-80` pins Born probabilities, normalization, bounds, boundary certainty, and non-unit direction guard.
- `/tmp/s3_blind_expected_20260610.md:86-105` pins selective/nonselective projective update maps and bad-update negative behavior.
- `/tmp/s3_blind_expected_20260610.md:111-139` pins quotient maps, ranks, kernels, and named probe-family rows.
- `/tmp/s3_blind_expected_20260610.md:145-184` pins trace distance, squared fidelity, mixed-state root term, and root-vs-squared convention.
- `/tmp/s3_blind_expected_20260610.md:186-218` gives S3 channel contraction expectations and S4/S5 tripwire facts.

Packet source anchors:

- `geo_s3_density_observable_v0_jax.py:174-183` constructs pinned `rho`, observable expectation, determinant, purity, trace, components, and Born probabilities symbolically.
- `geo_s3_density_observable_v0_jax.py:184-193` derives projectors and nonselective update components, then reduces against `||n||=1`.
- `geo_s3_density_observable_v0_jax.py:197-203` derives trace distance, squared Uhlmann fidelity, and wrong mixed-state fidelity control.
- `geo_s3_density_observable_v0_jax.py:361-464` emits S3.A through S3.G receipts.
- `geo_s3_density_observable_v0_jax.py:468-498` computes `Z_only`, `X_Z`, `X_Y_Z`, duplicate `Z`, and tetrahedral probe ranks/kernels.
- `geo_s3_density_observable_v0_jax.py:501-535` emits named CPTP contraction rows and explicitly says no S4/S5 claim.
- `geo_s3_density_observable_v0_jax.py:546-599` emits C1-C7 negative-model selectivity rows.
- `geo_s3_density_observable_v0_jax.py:603-613` emits fidelity convention and probe-family alternatives.

Committed prior evidence cited/checked:

- Build spec cites already-computed S1/Bloch-discriminator evidence at `system_v6/receipts/s3_build_spec_20260610.md:13-16`.
- The current packet copies that spec with matching SHA in `copied_inputs.s3_build_spec.matches_source=true`.
- The committed Bloch discriminator result has T2 `commuting_sigma_z_binned.affine_dimension=1` and `noncommuting_full_pauli_family.affine_dimension=3`.
- Current S3.E is consistent: `Z_only.rank=1`, `X_Z.rank=2`, `X_Y_Z.rank=3`, `duplicate_Z.rank=1`, and the C3 negative links to `bloch_root_admissibility_discriminator_v0 T2`.

## Per-check adjudication

### D1 - Ball fields

Status: PASS_WITH_GAP.

The formulas match the blind expected values. The envelope S3.A gives trace `1`, component traces `r_x,r_y,r_z`, eigenvalues `(1 +/- sqrt(r_x^2+r_y^2+r_z^2))/2`, positivity iff `r_x^2+r_y^2+r_z^2 <= 1`, determinant `(1-R^2)/4`, purity `(1+R^2)/2`, and entropy `H2((1+R)/2)`.

Gap: edge handling is only partially receipted. C1 covers outside-ball negativity, but the result does not explicitly receipt the center and boundary entropy controls or state that `H2` is bit-base/log2. This does not falsify the formula; it weakens the exactness receipt.

### D2 - Expectation and Born fields

Status: PASS_WITH_GAP.

Expectation and Born formulas are exact: S3.B gives `a0 + a_x*r_x + a_y*r_y + a_z*r_z`; S3.C gives `p_plus=(1+n.r)/2`, `p_minus=(1-n.r)/2`, normalization `1`, Cauchy-Schwarz bounds, and boundary certainty.

Gap: S3.B records plane equation and normal, but records offset as `c-a0`, not the blind expected signed distance `(c-a0)/||a||`. It also does not emit the empty/tangent/disk/whole-ball intersection cases from the blind file.

### D3 - Measurement update maps

Status: PASS_WITH_GAP.

The update maps are derived from projectors, not merely predeclared. S3.D gives selective `r -> +/- n`, probabilities from S3.C, and nonselective `r -> (n.r)n` with `diff_after_unit_constraint=["0","0","0"]`.

Gap: trace/positivity preservation is mathematically implied by projector/Kraus form and CPTP rows, but it is not separately receipted as an exact trace/positivity preservation row for S3.D. The zero-probability branch edge is not explicitly named in the result.

### D4 - Quotient map

Status: PASS.

S3.E emits explicit named-family rows:

- `Z_only`: `Q_N=[(0,0,1).r]`, rank `1`, kernel `span{e_x,e_y}`, quotient dimension `1`.
- `X_Z`: rank `2`, kernel `span{e_y}`, quotient dimension `2`.
- `X_Y_Z`: rank `3`, kernel `{0}`, quotient dimension `3`.
- `duplicate_Z`: rank `1`, duplicate does not raise rank.
- `tetrahedral_refinement_control`: rank `3`.

This is consistent with the committed Bloch-discriminator T2 dimensions: commuting `Z` probes have affine dimension `1`; full Pauli probes have affine dimension `3`.

### D5 - Trace distance and fidelity

Status: PASS.

S3.F gives `D=sqrt((r_x-s_x)^2+(r_y-s_y)^2+(r_z-s_z)^2)/2`, matching `||r-s||/2`. It gives squared Uhlmann fidelity with the determinant square-root term and names root fidelity as auxiliary only. The mixed-interior control correctly separates `F=7/8` from the wrong no-root formula `1/2`.

### D6 - Channels, tools, controls, and ceilings

Status: PASS_AS_S3_CONTRACTION_ONLY; NOT S4/S5.

S3.G computes the named affine maps and trace-distance contraction receipts for dephasing, depolarizing, and amplitude damping. It includes CPTP certification strings, fidelity monotonicity under the squared convention, and selected exact controls. The negative C6 non-CPTP expansive map fails contraction and CPTP certification.

The packet correctly does not compute or promote S4 ellipsoid classifications or S5 fixed-point/basin classifications. This is a feature under the build spec, not a defect. If D6 is read as requiring ellipsoid/fixed/basin computation inside this S3 packet, then that stronger D6 reading fails by design and should be routed to S4/S5.

Strength/tool checks pass:

- Literal strength tokens are present and validator-checked.
- Claim path excludes `numpy`, `scipy`, and `mpmath`.
- JAX/SymPy derive the formulas; z3/cvc5 check Born normalization with can-fail controls.
- PyTorch has a real S3-native lane for `torch.func` projective updates, probe rank, and contraction diagnostics; PyTorch diagnostic floats are marked `diagnostic_float_nonclaim`.
- Envelope ceilings are exact: scratch only, no promotion, no formal admission.

## Pattern-catalog binding

Status: NOT CERTIFIED.

I searched the provided authority inputs and the sim folder for `H1-H7`, `E1-E6`, and individual `H[1-7]` / `E[1-6]` catalog labels. The only direct hits in the provided S3 files were entropy notation like `H2`; no H1-H7/E1-E6 pattern catalog file or catalog rows were present.

Named gap: if H1-H7/E1-E6 is an external binding catalog, it was not supplied in the audit inputs and is not cited by the packet. This audit therefore cannot certify that catalog binding.

## Hand recomputations

All recomputations used the Makefile Python interpreter:

`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`

1. Entropy at mixed point `r=(1/2,0,0)`:
   - `R=1/2`, eigenvalues `(3/4,1/4)`.
   - `S_2=H2(3/4)=0.8112781244591328` bits.
   - Matches the formula `H2((1+R)/2)`.

2. Born pair for `r=(1/2,0,0)`, `n=(1/sqrt(2),0,1/sqrt(2))`:
   - `n.r=0.35355339059327373`.
   - `p_plus=0.6767766952966369`.
   - `p_minus=0.32322330470336313`.
   - `p_plus+p_minus=1.0`.

3. Update map output for the same `r,n`:
   - Selective `+` output is `n=(0.7071067811865475,0,0.7071067811865475)`.
   - Nonselective output `(n.r)n=(0.24999999999999994,0,0.24999999999999994)`.
   - This matches `r -> (n.r)n`.

4. Fidelity for `r=(1/2,0,0)`, `s=(0,1/2,0)`:
   - `r.s=0`, `||r||^2=||s||^2=1/4`.
   - `F=1/2*(1+sqrt((3/4)*(3/4)))=7/8=0.875`.
   - Wrong mixed-state no-root formula gives `1/2`; the packet's C7 catches this.

5. Trace distance for the same pair:
   - `D=||r-s||/2=sqrt(1/2)/2=0.3535533905932738`.

## Fresh commands

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json
```

Result:

```json
{
  "ok": true,
  "result_json": "system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json"
}
```

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s3_density_observable_v0/geo_s3_density_observable_v0_exact_strength_validator.py
```

Result:

```json
{
  "errors": [],
  "ok": true,
  "result_json": "system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json"
}
```

## Named gaps

G1 - Entropy edge/base receipt gap.
The symbolic entropy formula is correct, but the result does not explicitly define `H2` as log2/bits or receipt the `R=1` no-`log(0)` boundary handling. Ceiling impact: blocks stronger exactness language, not scratch-diagnostic S3 acceptance.

G2 - Plane signed-distance receipt gap.
The packet emits plane equation, normal, and offset `c-a0`, but not signed distance `(c-a0)/||a||` or intersection type rows. Ceiling impact: S3.B should be described as expectation/level-plane exact, not full blind plane-geometry complete.

G3 - S3.D preservation receipt gap.
Trace/positivity preservation for projective update maps is implied by the projector construction, but not separately receipted as exact preservation. Ceiling impact: keep the map claim, avoid stronger "all preservation edge cases receipted" language.

G4 - D6 scope split.
The packet does not compute ellipsoid/fixed-point/basin classifications. Under the build spec this is correct; under a stronger D6 reading it is incomplete. Ceiling impact: S3 contraction only; route ellipsoid/fixed/basin to S4/S5.

G5 - H1-H7/E1-E6 catalog absent.
No supplied or local authority file for that pattern catalog was found in the audit inputs or sim folder. Ceiling impact: this audit cannot certify catalog binding.

## Final classification

Accepted as: bounded S3 one-qubit density/observable geometry scratch diagnostic.

Not accepted as: canonical, formal, S4 channel-ellipsoid geometry, S5 fixed-point/basin terrain, bridge/axis/physics claim, or H1-H7/E1-E6 catalog-certified packet.

## 2026-06-10 re-audit note - mechanical hardening additions

Scope: additive hardening only. Existing claim values, ceiling fields, and scratch-diagnostic status were preserved; this note does not promote the packet.

G1 closed mechanically: S3.A now emits explicit entropy-base receipt fields with natural log base `e` / nats as the primary program convention, labels the H2/log2 row as auxiliary bits, and receipts the `||r||=1` boundary with the coded `0*log(0)=0` limit.

G2 closed mechanically: S3.B now emits signed distance `(c-a0)/||a||` as `(c - a0)/sqrt(a_x^2 + a_y^2 + a_z^2)` and named intersection-type rows for whole-ball, empty, tangent-point, and disk cases.

G3 closed mechanically: S3.D now emits separate exact trace-preservation and positivity-preservation receipts for selective and nonselective projective update maps, including the zero-probability branch boundary.

G4 closed mechanically: S3.G now emits scope-routing fields that route channel ellipsoid classification to S4 and fixed-point/basin classification to S5, with `computed_here=false`.

G5 closed mechanically: `audit_inputs_note.md` was added to this sim folder and cites `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md` as the H1-H7 reference path and `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md` as the E1-E6 reference path.

Fresh reruns:

- JAX leg: `ok:true`.
- Julia leg: `ok:true`, `julia_z3:unsat`.
- PyTorch leg: `ok:true`.
- Envelope: `ok:true`, including `audit_gap_hardening_fields_present:true`.
- `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json`: `ok:true`.
- `system_v6/sims/geo_s3_density_observable_v0/geo_s3_density_observable_v0_exact_strength_validator.py`: `ok:true`, `errors:[]`.

## Remediation note - 2026-06-10

Tooling remediation step 3 rebuilt the S3 state/channel route so the Julia canon leg now routes density operators, Born/projector rows, and CPTP contraction rows through `QuantumOptics`; the Python leg now routes measurement/update and contraction rows through `qutip` Qobj and superoperator APIs. The prior hand Pauli/Bloch and PyTorch tensor rows remain only as controls/mirrors. Scientific claims and values are unchanged; the route is now load-bearing through the quantum-object APIs.

FINAL: RE-AUDIT PASS - G1-G5 mechanically closed; classification remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
