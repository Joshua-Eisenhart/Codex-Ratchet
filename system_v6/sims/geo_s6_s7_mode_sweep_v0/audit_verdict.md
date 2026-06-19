# Fresh Audit Verdict: geo_s6_s7_mode_sweep_v0

Auditor: fresh codex1 lane; I did not build this packet and did not shape-fix it.

Scope: fresh audit of `geo_s6_s7_mode_sweep_v0` against the calibrated bar in `system_v6/receipts/audit_bar_calibration_20260610.md` and the committed `geo_s2_s5_mode_sweep_v0` / `geo_s3_s4_mode_sweep_v0` audit precedents. The only intended write from this audit is this `audit_verdict.md`; I did not `git add` or commit.

Route truth: partial Wizard v4.2 sim-mode audit. The controller loaded the v4.2 packet/manifest, the calibration bar, source/results, build card, and precedent audits; three Codex-native read-only sidecars completed bounded Q1/Q2, Q3/Q4, and Q5-Q8 lanes. No child subsubagent topology or full nine-parent Max Assembly/council completion is claimed.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This verdict accepts only the current on-disk modes 2-3 (`RESTRICTED`, `QUOTIENTED`) S6/S7 diagnostic rows at that ceiling.

Verdict: GENUINE WITH NAMED CAVEATS.

## Fresh Checks Run

- Read source/result files directly with `nl -ba`, `sed`, `rg`, `jq`, and JSON inspection.
- Ran scratch-only recomputation with `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ...`, reading committed parent/result JSONs without writing repo result files.
- Ran `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s6_s7_mode_sweep_v0/validate_geo_s6_s7_mode_sweep_v0.py`; it returned `ok=true`, `validator_ok=true`, `errors=[]`, exit `0`. The validator result file SHA stayed byte-identical before/after: `eb56bd710aa58071825074ce2aef866afcd7d93a02aeb0d24bd4cb9ec973193f`.
- Ran `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s6_s7_mode_sweep_v0/results/geo_s6_s7_mode_sweep_v0_envelope_results.json`; it returned `ok=true`.
- Spawned three read-only Codex sidecars:
  - `019eb579-5df7-7922-8841-3d7448651f0a`: Q1/Q2 S6 restricted and quotient.
  - `019eb579-7a16-7c62-93be-2bb3497da0f5`: Q3/Q4 S7 restricted and quotient.
  - `019eb579-915b-7a80-b2c0-81ad3de79c34`: Q5-Q8 N01, shape, standards, closure.
- Confirmed `git status --short -- system_v6/sims/geo_s6_s7_mode_sweep_v0` reports `?? system_v6/sims/geo_s6_s7_mode_sweep_v0/`.

## Q1 - S6 Restricted

Verdict: PASS.

Quoted source:

- Source flattens committed parent S6 `shell_leakage_rows` into rows with `terrain_id`, `eta`, `classification`, phase flags, finite-time z range, and `z_dot_at_chi0` at `geo_s6_s7_mode_sweep_v0.py:97-115`.
- Source computes the shell-band restriction with `eta_min <= sx(row["eta"]) <= eta_max` at `geo_s6_s7_mode_sweep_v0.py:118-123`.
- Source derives `before_class_counts`, `after_class_counts`, `excluded_class_counts`, and requires restricted counts `cross_shell=4`, `leave_foliation=10`, `projected_shell_preserve_but_Hopf_leave=2` at `geo_s6_s7_mode_sweep_v0.py:124-149`.
- Source computes the no-op control by canonical hashing the committed S6 `shell_leakage_rows` payload at `geo_s6_s7_mode_sweep_v0.py:150-155`.

Result evidence:

- Result records restricted counts `4/10/2`, before counts `10/25/5`, excluded counts `6/15/3`, excluded eta labels `5*pi/12`, `pi/12`, `pi/3`, and `pass=true` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:775-806`.
- Result records the no-op hash equality `65cd20af8ad2d2deb85d60c2437d9772f2f75feaf9049d08f4b5fdbfb65da178` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:807-811`.

Recomputation:

- Re-flattened the committed S6 parent, filtered `pi/6 <= eta <= pi/4`, and recomputed `40` total rows, `16` restricted rows, and restricted class counts `{"cross_shell":4,"leave_foliation":10,"projected_shell_preserve_but_Hopf_leave":2}`.
- Recomputed the requested 2-count class: the two restricted `projected_shell_preserve_but_Hopf_leave` rows are `Si_Hill_L eta=pi/6` and `Si_Hill_L eta=pi/4`.
- Recomputed the canonical no-op hash over parent `shell_leakage_rows` as `65cd20af8ad2d2deb85d60c2437d9772f2f75feaf9049d08f4b5fdbfb65da178`, byte-exact with both result fields.

Conclusion: S6 restricted narrowing is computed from committed S6 exports and the shell-band restriction, not asserted from a summary count.

## Q2 - S6 Quotiented

Verdict: PASS.

Quoted source:

- Source emits class-level rows for `projected_shell_preserve_but_Hopf_leave`, `cross_shell`, `leave_foliation`, and unobserved `move` at `geo_s6_s7_mode_sweep_v0.py:178-228`.
- The descended class is accepted because it is phase-independent with finite-time z range `0`; `cross_shell` is excluded as needing pre-quotient phase samples; `leave_foliation` is excluded as lift/Hopf-foliation data.

Result evidence:

- Result records `cross_shell` as `excluded_needs_pre_quotient_phase_samples` with witness `Ne_Spiral_R`, `eta=pi/12`, `phase_dependent=true`, `finite_time_z_range=0.9970320596669555`, and nonzero `z_dot_at_chi0` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:419-431`.
- Result records `leave_foliation` as `excluded_needs_lift_or_foliation_data` with witness `Ni_Pit_L`, `eta=pi/12`, `phase_dependent=true`, and nonzero finite-time z range at `geo_s6_s7_mode_sweep_v0_envelope_results.json:433-445`.
- Result records `projected_shell_preserve_but_Hopf_leave` as descended with witness `Si_Hill_L`, `eta=pi/12`, `phase_dependent=false`, `finite_time_z_range=0.0`, and `z_dot_at_chi0=0` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:455-467`.
- Descended/excluded class lists are recorded at `geo_s6_s7_mode_sweep_v0_envelope_results.json:470-475`.

Recomputation:

- Recomputed the witness fields from committed parent rows. The `cross_shell` witness is genuine: `Ne_Spiral_R eta=pi/12` has `phase_dependent=true`, finite-time z range `0.9970320596669555`, and `z_dot_at_chi0="-sqrt(6)*sin(pi/28)/3"`.
- Recomputed the descended preserve witness as phase-independent and z-range zero. The audit accepts that the Hopf-lift departure itself is not used as downstairs data.

Conclusion: the class split is computed with concrete witnesses. The class needing pre-quotient data is `cross_shell`; the witness is genuine and not a decorative label.

## Q3 - S7 Restricted

Verdict: PASS.

Quoted source:

- Source constants retain restricted grids `[8,16,32]` at `geo_s6_s7_mode_sweep_v0.py:48`.
- Source reruns `area_estimate`, `wilson_overlap_holonomy`, and `flux_estimate` over the retained grids at `geo_s6_s7_mode_sweep_v0.py:237-272`.
- Source emits parity cover rows via `grid_receipt(n, include_table=False)` and checks `every_class_size_2`, `two_times_physical_equals_chart`, and `parity_class_invariant_under_cover` for all retained rows at `geo_s6_s7_mode_sweep_v0.py:273-299`.

Result evidence:

- Result records kept grids `[8,16,32]`, excluded grids `[2,4,64]`, cover honored, and row counts `21/21/27` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:1125-1150` and in the reduced rerun payload.
- Result records parity rows with `chart_point_count`, `physical_point_count`, class-size/two-times checks, and balanced parity counts for the retained grids. For example, `N=16` has `chart_point_count=256`, `physical_point_count=128`, `every_class_size_2=true`, `two_times_physical_equals_chart=true`, and balanced parity counts.

Recomputation:

- Recomputed one restricted convergence row from source core functions: `eta=pi/6`, `N=16` area row returned `area_estimate=16.656492203102335`, `area_target=17.094656273292166`, `abs_error=0.4381640701898313`, `rel_error=0.025631639688151953`, `physical_cell_count=128`, `chart_cell_count=256`, and `max_partner_cell_area_abs_diff=6.106226635438361e-16`, matching the packet row exactly for checked fields.
- Recomputed the `N=16` grid receipt: `chart_point_count=256`, `physical_point_count=128`, `expected_physical_point_count=128`, `every_class_size_2=true`, `two_times_physical_equals_chart=true`, parity counts `64/64`, and the stored quotient table hash `551ffb53aa6f49576fa05a26dcc54ed398c2fdf0ae84c861953b60b63246bddb`.

Conclusion: S7 restricted is a real sub-grid rerun over `[8,16,32]` and honors the 2:1 cover on the checked row.

## Q4 - S7 Quotiented

Verdict: PASS.

Quoted source:

- Source defines `LENS_ORDER = 4` at `geo_s6_s7_mode_sweep_v0.py:50`.
- Source derives the obstruction: if `n % LENS_ORDER != 0`, the row fails because `N/4` is not an integral grid shift; otherwise it sets `shift = n // LENS_ORDER` and builds Z4 orbits at `geo_s6_s7_mode_sweep_v0.py:317-349`.
- Source tests grids `[2,3,5,6,8,10,16,32,64]` and requires `[8,16,32,64]` to admit and `[3,5,6,10]` to fail at `geo_s6_s7_mode_sweep_v0.py:352-367`.

Result evidence:

- Result records admitted grids `[8,16,32,64]` and failed grids `[2,3,5,6,10]` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:1000-1013`.
- Failing `N=6` records `computed_mod=2`, `failure_kind=incommensurate_with_lens_order`, and reason `N=6 is not divisible by lens_order=4; the N/4 grid shift is not integral` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:1039-1046`.
- Admitted `N=8` records `computed_mod=0`, `shift=[2,2]`, `chart_point_count=64`, `orbit_count=16`, and all orbit sizes equal to `4` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:1047-1061`.
- Admitted `N=16` records `shift=[4,4]`, `orbit_count=64`, and all orbit sizes equal to `4` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:1071-1084`.

Recomputation:

- Derived criterion: a finite `N x N` grid admits the Z4 lens quotient iff `N % 4 == 0`; equivalently the Z4 shift `(N/4,N/4)` is integral. When admitted, each orbit under `k=0..3` has size `4` and orbit count is `N^2 / 4`.
- Recomputed admitted `N=8`: `shift=[2,2]`, `chart_point_count=64`, `orbit_count=16`, min/max orbit size `4`, `computed_mod=0`.
- Recomputed failing `N=6`: `computed_mod=2`; `N/4` is non-integral, so the packet's incommensurate failure is honest.

Conclusion: the arithmetic obstruction is derived from the Z4 lens order and the integral grid-shift criterion, not a hand-picked admitted list.

## Q5 - N01 Rows

Verdict: PASS.

Quoted source:

- S6 order row computes `restrict_then` from restricted rows whose class descends, computes `quotient_first` from all rows whose class descends, then applies the eta restriction and computes the gap at `geo_s6_s7_mode_sweep_v0.py:370-388`.
- S7 order row computes admitted N values from the quotient row, intersects with restricted N values in both orders, and computes the gap at `geo_s6_s7_mode_sweep_v0.py:391-408`.

Result evidence:

- S6 result records `N01_order_gap=0`, `restrict_then_quotient_count=2`, `quotient_then_restrict_count=2`, and both row lists as `Si_Hill_L` at `pi/6` and `pi/4` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3192-3250`.
- S7 result records `N01_order_gap=0`, `restrict_then_quotient_rows=[8,16,32]`, `quotient_then_restrict_rows=[8,16,32]`, and counts `3/3` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3252-3272`.
- Validator requires nonempty row lists and count/list consistency at `validate_geo_s6_s7_mode_sweep_v0.py:117-125`.

Recomputation:

- S6: descended class set is `{"projected_shell_preserve_but_Hopf_leave"}`. Restrict-then-quotient returns the two restricted `Si_Hill_L` rows at `pi/6` and `pi/4`. Quotient-then-restrict first selects all descended parent rows, then eta-band filters to the same two rows. Gap `abs(2-2)=0`.
- S7: quotient-admitted set includes `8,16,32,64`; restricted set is `[8,16,32]`. Both orders return `[8,16,32]`. Gap `abs(3-3)=0`.
- Literal check: `rg` found no source-side `N01_order_gap.*0` in the builder source; the only zero expectations are validator assertions and result JSON.

Conclusion: both N01 zero gaps come from two genuine pipelines, not source-side zero literals.

## Q6 - Shape Repair

Verdict: PASS WITH CAVEAT C3.

Quoted source/result:

- Result labels the engine mode `julia_canon_plus_jax_diagnostic`, lanes `["julia","jax"]`, and PyTorch omitted because no graph/network/autograd claim path is scoped at `geo_s6_s7_mode_sweep_v0_envelope_results.json:197-213`.
- Result records `engines.jax` as the standard JAX-lane shape slot for the Python-exact parent-bound sidecar, with packages `sympy`, `z3-solver`, `cvc5`, `json`, `hashlib`, and `pathlib` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:215-235`.
- Shape-only repair receipt says it renamed the diagnostic Python lane to the standard `engines.jax` object expected by the shared validator and preserved computed row hashes at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3288-3313`.

Recomputation:

- Recomputed `mode_rows` canonical hash as `eed73d29b20f82fea8311e3a78f722b290fdcffb37958ee767597561e87f240c`, matching both `before_hash` and `after_hash`.
- Sidecar recomputed all three preserved subtree hashes exactly: `mode_rows`, `cross_mode_comparison_table`, and `order_control_rows`.
- Packet validator now returns `ok=true`, and strict source-backed validation returns `ok=true`.

Conclusion: the `engines.jax` change is shape-only with preserved computed rows. It is not evidence of an actual JAX-array proof; the envelope says that honestly.

## Q7 - Standard Checks

Verdict: PASS WITH NAMED CAVEATS.

Passed checks:

- Honest mode label: `julia_canon_plus_jax_diagnostic`; PyTorch omission is explicit at `geo_s6_s7_mode_sweep_v0_envelope_results.json:197-213`.
- Parent lineage hashes are present for S6 parent, S7 parent, geometry program, toolset receipt, and precedent mode-sweep packets at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3274-3280`.
- Julia leg is real and read-independent: source uses `Symbolics` and `Z3` at `geo_s6_s7_mode_sweep_v0_julia.jl:31-44` and `61-94`; envelope records Julia `ran=true`, `reads_peer_result=false`, load-bearing `Symbolics` and `Z3`, and result/source hashes at `geo_s6_s7_mode_sweep_v0_envelope_results.json:237-257`.
- Julia sidecar records `s6_bound_identity_value=0`, `s7_commensurate_sample_N8_mod4=0`, `s7_incommensurate_sample_N6_mod4=2`, and Z3 unsat controls for erased S6 exclusions and forced N6 commensurability at `geo_s6_s7_mode_sweep_v0_envelope_results.json:349-394`.
- Capability receipts are present at `geo_s6_s7_mode_sweep_v0_envelope_results.json:85-90`.
- Tool manifest/tool calls are one-to-one: `8` manifest entries and `8` tool calls. The calls are listed at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3318-3427`.
- Envelope payload fixture wording is absent: `jq -e 'tostring | ascii_downcase | contains("fixture") | not' ...` returned `true`. The only directory-level `fixture` hit is the validator guard text itself at `validate_geo_s6_s7_mode_sweep_v0.py:137`.
- Versions and seed are present: Python `3.13.6`, z3 `4.16.0.0`, cvc5 `1.3.3`, seed `20260611` at `geo_s6_s7_mode_sweep_v0_envelope_results.json:3285-3287` and `3428-3432`.
- Ceilings are present: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Controls can fail: z3/cvc5 both bind S6 raw counts `before=40`, `after=16`, `excluded=24`, prove the identity-violation query unsat, and the erased-exclusion controls unsat at `geo_s6_s7_mode_sweep_v0_envelope_results.json:156-186`.

Named caveats:

- C1 untracked-packet caveat: `system_v6/sims/geo_s6_s7_mode_sweep_v0/` is currently untracked. This audit accepts current on-disk evidence, not committed repo truth for the target packet.
- C2 route caveat: this was a partial v4.2 audit with three completed Codex-native sidecars and controller recomputation, not full Max Assembly with child subsubagents and all councils.
- C3 JAX-shape caveat: `engines.jax` is an honest validator-shape slot for the Python-exact sidecar. It is not an actual JAX-array or XLA proof lane.
- C4 validator-write caveat: the packet validator CLI writes `results/geo_s6_s7_mode_sweep_v0_validator_results.json`; the controller ran it as requested and confirmed byte-identical result content before/after.

Conclusion: standard checks pass under the stated diagnostic ceiling with the above caveats.

## Q8 - Closure

Verdict: PASS WITH CEILING.

Earned:

- The current S6/S7 packet extends the audited mode-sweep program to S6 and S7 for modes 2-3 only: `RESTRICTED` and `QUOTIENTED`.
- Together with the precedent audits, the on-disk packet set now has audited modes 2-3 coverage across S2/S5, S3/S4, and S6/S7.
- S6 adds shell-band leakage-class narrowing and class-level lens descent/exclusion over the committed stacked terrain/operator/Hopf parent.
- S7 adds restricted sub-grid convergence reruns with the 2:1 cover honored and a derived Z4 lens-grid commensurability obstruction.
- Both S6 and S7 N01 rows have computed two-pipeline zero gaps for the packet's stated count objects.

Not earned:

- No mode-4/RATCHETED result. The geometry program defines RATCHETED as sequential constraint application with induced-geometry recomputation, `G_{t+1} = {x in G_t : C_{t+1}(x)}`, at `system_v6/receipts/geometry_sim_program_canonical_20260610.md:10-14`; this packet explicitly excludes RATCHETED at `geo_s6_s7_mode_sweep_v0_envelope_results.json:396-408` and `build_card.md:36-39`.
- No S1 sweep. The closure spans S2-S7 only through the current paired mode-sweep packets; S1 has its own exactness/free-mode program.
- No trend, monotonic program-level claim, bridge/axis/manifold/physics claim, formal admission, or promotion.
- No committed-repo truth for the target packet while the directory remains untracked.
- No actual JAX-array proof beyond the honest shape-slot repair.

## Verdict

VERDICT: GENUINE WITH NAMED CAVEATS.

Caveats:

- C1: target packet directory is untracked; accepted as current on-disk evidence only.
- C2: partial v4.2 audit route; no full Max Assembly/council/subsubagent topology claim.
- C3: `engines.jax` is a shape-only Python-exact sidecar slot, not a JAX-array proof.
- C4: validator CLI was run despite its write behavior because the prompt requested it; the validator result content SHA stayed byte-identical before/after.

Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This completes the audited modes 2-3 sweep across the paired S2-S7 stage packets, with S6/S7 now covered on disk, but does not complete mode 4/RATCHETED, does not cover S1, and does not establish a trend or admission claim.

