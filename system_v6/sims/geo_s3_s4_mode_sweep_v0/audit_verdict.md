# Fresh Audit Verdict: geo_s3_s4_mode_sweep_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: fresh audit of `geo_s3_s4_mode_sweep_v0`. I did not build this packet. The only intended write from this audit is this `audit_verdict.md`; I did not `git add` or commit.

Route truth: partial Wizard v4.2 sim-mode audit. The main controller read the v4.2 packet, authority docs, source, result, calibration bar, and S2/S5 precedent. Three Codex-native sidecar agents completed bounded read-only lanes for Q1/Q2, Q3/Q4, and Q5/Q6/Q7. No child subsubagent or full council topology is claimed.

Calibrated bar used: `system_v6/receipts/audit_bar_calibration_20260610.md`, especially route genuineness, can-fail controls, erasure honesty, exactness-class stability, scratch ceilings, and the calibrated rule that one genuine derivation plus independent solver/cross-engine binding can satisfy the audit bar when the split is honestly labeled. Precedent used: committed `geo_s2_s5_mode_sweep_v0/audit_verdict.md`, especially the hardened requirement that descent/order rows be computed rather than emitted by construction.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This verdict accepts only modes 2-3 (`RESTRICTED`, `QUOTIENTED`) on S3/S4 with the S4 operator-exclusion result. It does not accept mode 4/RATCHETED, terrain claims, trend claims, bridge/axis claims, or formal admission.

Verdict: GENUINE WITH NAMED CAVEATS.

## Fresh Checks Run

- Read source/result files directly with `nl -ba`, `sed`, `rg`, JSON inspection, and `shasum`.
- Ran scratch-only recomputation with `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`, reading committed result JSONs and parent S4 matrices without writing repo files.
- Ran an in-memory validator subset against the envelope instead of invoking `validate_geo_s3_s4_mode_sweep_v0.py`, because that CLI writes `results/geo_s3_s4_mode_sweep_v0_validator_results.json`.
- Ran `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s3_s4_mode_sweep_v0/results/geo_s3_s4_mode_sweep_v0_envelope_results.json`; it returned `ok=true`.
- Spawned three read-only Codex sidecars:
  - `019eb53d-5e47-7140-bcb4-fbfdecd027d3`: Q1/Q2 S4 restricted and quotient.
  - `019eb53d-78fc-7ce2-8f25-742fb37c284d`: Q3/Q4 S3 rows and order rows.
  - `019eb53d-9633-7050-ab9b-5e7c2a908231`: Q5/Q6/Q7 controls, hygiene, and ceiling.
- Did not run `geo_s3_s4_mode_sweep_v0.py` or the packet validator CLI because both write result files outside this audit's one-file write allowance.

## Q1 - S4 Restricted

Verdict: PASS.

Quoted source:

- Source computes operator action on every restricted shell point: `image_rows = [(row, apply_matrix(matrix, row)) for row in shell]` and classifies by `norm2(item[1]) == R0 * R0` in `geo_s3_s4_mode_sweep_v0.py:257-276`.
- The pass condition requires `R_x` and `R_z` to preserve while `D_z` and `D_x` leak in `geo_s3_s4_mode_sweep_v0.py:286-304`.
- Parent S4 action rows are real matrices in `geo_s4_operator_stage_v0_envelope_results.json`: `D_x` has pinned `diag(1,7/10,7/10)` at lines 24-47; `D_z` has pinned `diag(7/10,7/10,1)` at lines 133-155; `R_x` has pinned row `z'=y` at lines 241-263; `R_z` has pinned `z'=z` at lines 349-370.

Recomputation:

- Recomputed shell points from `{-1/2,0,1/2}^3` with `|r|^2=1/4`: six points.
- Recomputed `D_z`: preserves the two z-axis shell points, leaks four transverse points inward. Example: `(-1/2,0,0) -> (-7/20,0,0)`, output norm squared `49/400`, matching result lines 1535-1590.
- Recomputed `D_x`: preserves the two x-axis shell points, leaks four transverse points inward. Example: `(0,-1/2,0) -> (0,-7/20,0)`, output norm squared `49/400`, matching result lines 1445-1500.
- Recomputed `R_x`: preserves all six shell points, matching result lines 1625-1708.
- Recomputed `R_z`: preserves all six shell points, matching result lines 1710-1793.
- Result summary matches recomputation: `leak=["D_z","D_x"]`, `preserve_all_shell=["R_x","R_z"]`, and per-operator controls pass at result lines 1433-1443 and 1797-1806.

Conclusion: the S4 restricted split is computed from operator actions and shell norm checks, not asserted from operator type.

## Q2 - S4 Quotiented

Verdict: PASS.

Quoted source:

- Source tests descent by reading the third matrix row: `z_row = matrix[2]` and `well_defined = z_row[0] == 0 and z_row[1] == 0` in `geo_s3_s4_mode_sweep_v0.py:308-329`.
- The source records the concrete same-class witness pair `(0,1/2,0)` and `(0,-1/2,0)` and emits witness outputs in `geo_s3_s4_mode_sweep_v0.py:310-329`.
- The pass condition requires `D_z`, `D_x`, and `R_z` to descend and `R_x` to be excluded in `geo_s3_s4_mode_sweep_v0.py:330-345`.
- Julia sidecar source independently computes `rx_z_output = y`, substitutes the same witness pair, and checks `R_x_descends` false in `geo_s3_s4_mode_sweep_v0_julia.jl:42-63`.

Recomputation:

- `D_z`: z-row `[0,0,1]`, quotient map `z -> 1*z`; same-class witness outputs have z values `0,0`. Descends.
- `D_x`: z-row `[0,0,7/10]`, quotient map `z -> 7/10*z`; same-class witness outputs have z values `0,0`. This is the subtle case: `D_x` leaks the fixed-purity shell, but on the z-probe quotient its z output depends only on z, so it descends.
- `R_z`: z-row `[0,0,1]`, quotient map `z -> 1*z`; same-class witness outputs have z values `0,0`. Descends.
- `R_x`: z-row `[0,1,0]`; the same-class pair `(0,1/2,0) ~ (0,-1/2,0)` maps to outputs with z values `1/2` and `-1/2`. Excluded.
- Result rows match the recomputation: descended operators at lines 1248-1255; `D_x` row lines 1258-1294; `D_z` row lines 1296-1332; `R_x` exclusion and witness lines 1334-1370; `R_z` row lines 1372-1408.
- Julia result independently records `R_x_descends=false`, witness values `1//2,-1//2`, `R_z_descends=true`, and `z_measurement_descends=true` at `geo_s3_s4_mode_sweep_v0_julia_results.json:53-75`.

Conclusion: S4 quotient branch mortality is genuinely computed. `R_x` fails equivariance on the quotient by a concrete witness pair; `D_x` descends for the computed z-row reason.

## Q3 - S3 Restricted And Quotiented

Verdict: PASS.

Quoted source:

- Source computes all finite grid points and shell points with `finite_grid_points()` and `shell_points()` in `geo_s3_s4_mode_sweep_v0.py:84-90`.
- Source computes restricted/excluded rows, parent S3 density formulas, Born fields, observable fields, trace-distance/fidelity rows, and controls in `geo_s3_s4_mode_sweep_v0.py:106-201`.
- Source computes z-probe quotient classes from restricted shell points with `classes.setdefault(frac_text(z_probe_class(row)), []).append(vec_text(row))` in `geo_s3_s4_mode_sweep_v0.py:208-254`.

Recomputation:

- Recomputed the finite grid count as `27`.
- Recomputed the restricted shell count as `6` and excluded count as `21`, matching result lines 1155-1197.
- Recomputed S3 restricted density rows: on `|r|=1/2`, purity is `5/8`, eigenvalues are `1/4` and `3/4`, matching result lines 1129-1146.
- Recomputed Born z sample at `r_z=1/2`: `p_plus=3/4`, `p_minus=1/4`, matching result lines 1079-1090.
- Recomputed antipodal shell pair `(1/2,0,0)`, `(-1/2,0,0)`: trace distance `1/2`, fidelity `3/4`, matching result lines 1215-1238.
- Recomputed z-probe quotient classes:
  - z `-1/2`: `(0,0,-1/2)`.
  - z `0`: `(-1/2,0,0)`, `(0,-1/2,0)`, `(0,1/2,0)`, `(1/2,0,0)`.
  - z `1/2`: `(0,0,1/2)`.
  These match result lines 925-962.
- Recomputed observable descent witnesses:
  - `Z_measurement` descends: same-class pair `(1/2,0,0)`, `(-1/2,0,0)` gives probabilities `1/2,1/2`.
  - `X_measurement` does not descend: same pair gives `3/4,1/4`.
  - `Y_measurement` does not descend: pair `(0,1/2,0)`, `(0,-1/2,0)` gives `3/4,1/4`.
  These match result lines 981-1041.

Conclusion: S3 restricted and quotient rows are computed from the finite Bloch shell and explicit witness pairs.

## Q4 - N01 Order Rows

Verdict: PASS.

Quoted source:

- S3 order row computes `restrict_then_quotient` from shell z classes and `quotient_then_restrict` from finite-grid z values, then computes `gap = abs(len(...)-len(...))` in `geo_s3_s4_mode_sweep_v0.py:348-365`.
- S4 order row computes `preserve_shell & descend` versus quotient-descending operators that preserve the z interval, then computes the same count gap in `geo_s3_s4_mode_sweep_v0.py:369-391`.

Recomputation:

- S3 restrict-then-quotient rows: `[-1/2,0,1/2]`.
- S3 quotient-then-restrict rows: `[-1/2,0,1/2]`.
- S3 gap: `abs(3-3)=0`, matching result lines 1812-1831.
- S4 restrict-then-quotient rows: shell-preserving operators that also descend are `["R_z"]`. `R_x` preserves shell but is excluded on the quotient.
- S4 quotient-then-restrict rows: quotient descenders preserving the z interval are `["D_x","D_z","R_z"]`; `D_x` has scale `7/10`, `D_z` scale `1`, `R_z` scale `1`.
- S4 gap: `abs(1-3)=2`, matching result lines 1833-1850.

Conclusion: the meaningful split is real under the packet's stated counting object: S3 commutes on this finite shell/probe sample; S4 does not because `D_z` and `D_x` are killed by the shell-first path but survive the quotient-first path.

## Q5 - Controls And SMT Flip

Verdict: PASS.

Controls checked:

- S3 nothing-excluded control is byte-exact: both hashes are `6868d512...b3e7e`, result lines 1199-1204.
- S4 nothing-excluded control is byte-exact: both hashes are `380808e8...fdcc8`, result lines 1438-1443.
- S3 everything-excluded control is honest: `admissible_set_empty=true`, `after_count=0`, and no zero-valued row fabricated, result lines 1148-1154.
- S4 everything-excluded control is honest: `admissible_set_empty=true`, `operator_rows={}`, result lines 1427-1432.
- Per-operator controls can fail and do fail for generic dephasing shell preservation: `D_x_generic_transverse_fails_preservation=true`, `D_z_generic_transverse_fails_preservation=true`, result lines 1797-1802.
- z3 and cvc5 bind raw integer counts `before=27`, `after=6`, `excluded=21`, derive `before - after - excluded`, and both main contradiction checks return `unsat`, result lines 635-666.
- Erased-exclusion controls fail as required: both z3 and cvc5 have `erased_flip_control_can_fail=true` with erased verdict `unsat`, result lines 644-665.

Conclusion: controls are can-fail and load-bearing enough for this diagnostic claim. The SMT proof is bounded to the S3 count identity, not a broad geometry proof.

## Q6 - Standard Hygiene

Verdict: PASS WITH CAVEATS C1-C4.

Passed checks:

- Honest mode label: result uses `engine_contract.mode="julia_canon_plus_jax_diagnostic"`, lanes `["julia","jax"]`, and explicitly omits PyTorch because no graph/network/autograd claim path is scoped, result lines 677-693.
- Executed modes are only `RESTRICTED` and `QUOTIENTED`; `RATCHETED` is explicitly excluded, result lines 899-911.
- Parent lineage hashes are present and recomputed on disk for S3 parent, S4 parent, audit bar, geometry program, and toolset receipt, result lines 1853-1859.
- Strict source-backed validator returned `ok=true` for the envelope.
- Julia leg is real result evidence: `packages_used=["Symbolics","Z3","JSON","SHA"]`, `aligned_packages_load_bearing=["Symbolics","Z3"]`, `reads_peer_result=false`, and tool calls are present in `geo_s3_s4_mode_sweep_v0_julia_results.json:30-108`.
- Capability receipts are present: `runtime_doctor`, `toolset_expansion_receipt`, and Julia sidecar receipt at result lines 89-93.
- One-to-one tool calls are present for `Symbolics`, `Z3`, `sympy`, `z3`, and `cvc5`, result lines 1869-1940.
- `rg -n "fixture" system_v6/sims/geo_s3_s4_mode_sweep_v0` returned no hits.
- Seed is present: `global_seed=20260610`, result lines 1863-1865.
- Ceilings are present: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`, result lines 94-103 and 774-775.
- Builder hardening addendum states computed descent and two-pipeline order rows, result lines 71-75 and 623-628.

Named caveats:

- C1 untracked-packet caveat: `git status --short -- system_v6/sims/geo_s3_s4_mode_sweep_v0` reports `?? system_v6/sims/geo_s3_s4_mode_sweep_v0/`. The packet can pass this audit as current on-disk evidence, but it is not committed repo truth yet.
- C2 validator-write caveat: I did not run the packet builder or packet validator CLI because both write result files. I used scratch recomputation, existing result files, in-memory validator checks, and the source-backed validator.
- C3 version caveat: the envelope lists package names and capability receipts but does not itself record exact package versions. Version evidence is indirect through `system_v6/receipts/toolset_expansion_20260610.md` and existing runtime receipts.
- C4 route caveat: this audit had three completed Codex sidecars, but not full v4.2 Max Assembly with child subsubagents and council waves. No full-council route claim is made.

Conclusion: hygiene passes for the stated diagnostic ceiling with named caveats. No by-construction S2/S5 G1-style defect remains in the audited S3/S4 descent or order rows.

## Q7 - Closure

Earned:

- Modes 2-3 (`RESTRICTED`, `QUOTIENTED`) are demonstrated on S3 density/observable rows and S4 operator rows.
- S4 restricted headline is accepted: `R_x` and `R_z` preserve the fixed-purity shell; `D_z` and `D_x` leak generic transverse shell points inward.
- S4 quotient branch mortality is accepted: `D_z`, `D_x`, and `R_z` descend to the z-probe quotient; `R_x` is excluded by a concrete same-class witness pair.
- S3 restricted shell rows, z-probe quotient classes, and descended/non-descended observables are accepted.
- N01 rows are accepted: S3 gap `0`, S4 gap `2`, with the S4 gap counted as `abs(1 shell-first descender - 3 quotient-first descenders)`.
- Controls are accepted for this diagnostic packet, including byte-exact no-op controls, honest empty controls, per-operator failing controls, and z3/cvc5 erased flips.

Not earned:

- No RATCHETED/mode-4 result.
- No terrain-generator or 56/56 terrain claim; the packet explicitly keeps the S5 terrain precedent as context only.
- No trend claim across stages.
- No bridge, axis, manifold, physics, or formal admission claim.
- No committed-repo truth claim while the packet directory remains untracked.
- No fresh write-producing rerun of the builder or packet validator in this audit turn.

## Verdict

VERDICT: GENUINE WITH NAMED CAVEATS.

Caveats:

- C1: target packet directory is untracked.
- C2: builder and packet validator CLI were not rerun because they write result files; fresh audit used scratch-only recomputation and read-only/source-backed validation.
- C3: exact package versions are indirect rather than recorded in the envelope itself.
- C4: route is a partial v4.2 audit with three Codex sidecars, not full Max Assembly/council topology.

Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This earns modes 2-3 on S3/S4 with the operator-exclusion result, not mode 4, not terrain claims, not trend claims, and not admission.

## Block K

Gates cited: `AGENTS.md` sim-mode Max Assembly contract; `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`; `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`; `system_v5/docs/LEGO_SIM_CONTRACT.md`; `system_v6/receipts/audit_bar_calibration_20260610.md`; `geo_s2_s5_mode_sweep_v0/audit_verdict.md`; strict source-backed validator.

Admission decisions: local audit accepts the packet as genuine at `scratch_diagnostic` ceiling with named caveats; formal admission blocked; mode-4, terrain, trend, bridge, axis, manifold, and physics claims blocked.

Narrative substitutions intercepted: `R_x/R_z preserve` was checked by applying matrices to all six shell points; `D_x descends` was checked from the z-row `[0,0,7/10]`; S4 gap `2` was checked from the named count objects, not accepted from headline prose.

Worker claims verified: sidecar Q1/Q2, Q3/Q4, and Q5/Q6/Q7 claims were checked against source, result JSON, parent matrices, scratch recomputation, and strict source-backed validation.

Worker claims not verified: no write-producing builder rerun, no packet validator CLI rerun, no full child/council Wizard topology.

Status label changes to registry: none.

Blocked actions: no git add, no commit, no result rewrite, no validator-result rewrite, no promotion/admission wording.
