# Fresh Audit Verdict: geo_s2_s5_mode_sweep_v0

Scope: fresh audit of `geo_s2_s5_mode_sweep_v0`. I did not build this sim. The only intended write from this audit is this `audit_verdict.md`; I did not `git add` or commit.

Calibrated bar used: `system_v6/receipts/audit_bar_calibration_20260610.md`, especially exactness-class stability, route genuineness, can-fail controls, erasure honesty, scratch ceilings, and the rule that two-CAS end-to-end is preferred but not mandatory when one genuine derivation has independent solver/cross-engine binding. Program bar used: `system_v6/receipts/geometry_sim_program_canonical_20260610.md`, especially the four modes and the ceiling `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Commands And Read-Only Checks

- Read source/result files directly with `sed`, `nl -ba`, `rg`, and JSON pretty-printing under `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- Ran an independent read-only recomputation script against the committed S2/S5/lens anchors and the packet result JSON.
- Ran `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed ...`, which is read-only and returned a source-backed Julia caveat.
- Did not rerun `validate_geo_s2_s5_mode_sweep_v0.py` because that script writes `results/geo_s2_s5_mode_sweep_v0_validator_results.json`. Existing packet validator result says `ok=true`, `errors=[]`.
- Accident note: one maintenance audit helper wrote two tracked maintenance files while checking source-backed claims; I restored exactly those two accidental writes. `git status --short -- system_v5/evidence/three_engine_source_claim_audit_20260608.json system_v5/docs/maintenance/three_engine_source_claim_audit_20260608.md system_v6/sims/geo_s2_s5_mode_sweep_v0` then showed only `?? system_v6/sims/geo_s2_s5_mode_sweep_v0/`.

## Q1 Mode Semantics Real

Verdict: GENUINE for the S2 RESTRICTED narrowing/control rows.

Quoted source:

- Source computes restricted and excluded shell rows from committed S2 anchor rows: `restricted_shells = [row for row in shell_rows if eta_min <= sx(row["eta"]) <= eta_max]` and then derives `loop_before`, `loop_after`, and `loop_excluded` at `geo_s2_s5_mode_sweep_v0.py:83-92`.
- Source computes grid counts from `loop_before * physical_points` and `loop_after * physical_points` at `geo_s2_s5_mode_sweep_v0.py:93-107`.
- Source computes exact no-op hashes from the committed exact receipt rows at `geo_s2_s5_mode_sweep_v0.py:108-144`.
- Result row records `before_loop_count=5`, `after_loop_count=2`, `excluded_loop_count=3`, and excluded eta rows `pi/12`, `pi/3`, `5*pi/12` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:469-478`.
- Result row records the byte-exact no-op hash equality at `geo_s2_s5_mode_sweep_v0_envelope_results.json:480-497`.
- Result row records the empty-control policy `admissible_set_empty=true`, `after_loop_count=0`, and "do not coerce a zero-valued geometry row into existence" at `geo_s2_s5_mode_sweep_v0_envelope_results.json:461-467`.

Recomputation:

- Anchor shell count recomputed as `5`; eta band `[pi/6, pi/4]` keeps `pi/6`, `pi/4`; excluded rows are `pi/12`, `pi/3`, `5*pi/12`.
- Grid counts recomputed: `N=4: 40 -> 16, excluded 24`; `N=6: 90 -> 36, excluded 54`; `N=8: 160 -> 64, excluded 96`; `N=10: 250 -> 100, excluded 150`.
- The no-op hash recomputed to `e5d820bb5256ec63527b48bd897107e466611f41256d314c4a5e04d58c9174e3`, matching both packet hash fields byte-exact.
- The empty-control row honestly reports an empty admissible set; it does not fabricate a zero row.

## Q2 Quotient Descent Honesty

Verdict: GENUINE-WITH-CAVEAT G1.

Quoted source:

- Source imports lens quotient rows from the committed lens anchor at `geo_s2_s5_mode_sweep_v0.py:156-169`.
- Source emits `F.status="descends"` and `A.status="does_not_descend"` at `geo_s2_s5_mode_sweep_v0.py:178-197`.
- Result quotes the load-bearing rows: `F` has `status="descends"`, downstairs form, and committed curvature anchor at `geo_s2_s5_mode_sweep_v0_envelope_results.json:347-360`; `A` has `status="does_not_descend"`, reason, erased phase fact, and committed anchor at `geo_s2_s5_mode_sweep_v0_envelope_results.json:336-345`.
- Lens tower rows match committed values `N=1,2,3,4,8,16,64`, orbit count `128`, and class size/orbit size equal to `N` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:387-443`.

Recomputation:

- Gauge check: under a fiber-gauge change, `A -> A + d(lambda)` while `F=dA -> dA + d^2(lambda)=F`; for a nonconstant base `lambda`, `A` changes and `F` does not. This demonstrates the packet's descent split: `F` descends, `A` does not.
- Lens tower anchor recomputed from the committed lens result as `[(1,1,128),(2,2,128),(3,3,128),(4,4,128),(8,8,128),(16,16,128),(64,64,128)]`, matching the packet rows.

Named caveat:

- G1: the verdict values are mathematically right and audit-demonstrated, but the packet source itself does not perform an explicit gauge-variance/gauge-invariance computation for `A` and `F`. It emits the descent statuses and reasons by construction from anchor data. This is not fabricated, but it is weaker than the requested "computed/demonstrated, not asserted" load-bearing math.

## Q3 S5 Quotiented Distinguishability Matrix

Verdict: GENUINE.

Quoted source:

- Source constructs quotient signatures from pinned `A,b` only, while pre-quotient signatures include label/family/source plus `A,b`, at `geo_s2_s5_mode_sweep_v0.py:320-331`.
- Source builds the full pairwise matrix and named `collapsed_pairs` at `geo_s2_s5_mode_sweep_v0.py:334-356`.
- Source emits before/after matrices and `collapse_findings_by_name` at `geo_s2_s5_mode_sweep_v0.py:359-377`.
- Result records the after-quotient names, `off_diagonal_distinguishable_count=56`, `off_diagonal_pair_count=56`, and `collapsed_pairs=[]` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:633-990`.

Recomputation:

- Recomputed quotient signatures from the committed S5 `bloch_generator_table` using only pinned `A,b`.
- Recomputed names: `Ne_Spiral_R`, `Ne_Vortex_L`, `Ni_Pit_L`, `Ni_Source_R`, `Se_Cannon_R`, `Se_Funnel_L`, `Si_Citadel_R`, `Si_Hill_L`.
- Recomputed before collapsed pairs: `[]`.
- Recomputed after collapsed pairs: `[]`.
- Recomputed directed off-diagonal distinguishable count: `56`, matching result `56`.

Anti-collapse check:

- No averaging was found. The matrix is pairwise over named terrain rows, and any collapse would be recorded as a pair of names. No collapsed pair exists under this probe family.

## Q4 Order Row N01

Verdict: GENUINE-WITH-CAVEAT G2.

Quoted source:

- Source emits order rows at `geo_s2_s5_mode_sweep_v0.py:380-398`.
- Result records S2 `restrict_then_quotient_count=2`, `quotient_then_restrict_count=2`, and `N01_order_gap=0` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:1546-1554`.
- Result records S5 descriptions as both "upper Bloch half-ball" with `N01_order_gap=0` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:1555-1562`.

Recomputation:

- For S2, quotient-visible coordinate is `z=cos(2*eta)`. Restrict-then-quotient keeps eta rows `pi/6`, `pi/4`. Quotient-then-restrict with `z in [0, 1/2]` also keeps `pi/6`, `pi/4`. Gap recomputes as `abs(2-2)=0`.
- This hand recomputation matches the packet's S2 order gap.

Named caveat:

- G2: the S2 row value is correct under audit recomputation, and the S5 value is plausible because the constraint is already downstairs on the Bloch quotient. But the packet source's `order_rows()` function is literal construction with no anchor-row recomputation. This is BY_CONSTRUCTION in the packet source, not a computed both-ways N01 row.

## Q5 Standard Checks

Verdict: GENUINE-WITH-CAVEAT G3.

Passed checks:

- Per-row mode tags are present for `S2.RESTRICTED`, `S2.QUOTIENTED`, `S5.RESTRICTED`, and `S5.QUOTIENTED`; recomputation read all four as the expected tags.
- Cross-mode comparison table is present and like-for-like for S2 connection/curvature/counts and S5 fixed points/generator distinguishability at `geo_s2_s5_mode_sweep_v0_envelope_results.json:100-142`.
- Committed S2/S5/lens anchors are hash-bound. Recomputed hashes match result lines `49-54`:
  - S2: `47ecb1d4c83645ad0eb60286e3485871c40a6e5155263ca052867624234324d0`
  - S5: `8c5474786973f067e55c0200392c1a27cbe8bf5d71cfd632b507d066b6cc9b1e`
  - lens: `dad89dbeb1d6945f8bc7a7a099abae6b320d289f2de9eda1e7756ca8768c3e10`
- Controls can fail: z3 and cvc5 both report `verdict="unsat"` for the identity violation and `erased_flip_control_can_fail=true` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:144-175`.
- Tool manifest and tool integration depth are present at `geo_s2_s5_mode_sweep_v0_envelope_results.json:2-47`; tool calls are present at `geo_s2_s5_mode_sweep_v0_envelope_results.json:1573-1640`.
- Seed is present: `global_seed=20260610` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:1567-1569`.
- Ceilings are present: `classification="scratch_diagnostic"`, `promotion_allowed=false`, `formal_admission_allowed=false` at `geo_s2_s5_mode_sweep_v0_envelope_results.json:99`, `311`, and `1564`.
- RATCHETED is explicitly excluded at `geo_s2_s5_mode_sweep_v0_envelope_results.json:313-325`, consistent with the prompt.
- `rg -n "fixture" system_v6/sims/geo_s2_s5_mode_sweep_v0` returned no hits.

Validator/source-backed caveat:

- G3: strict source-backed validator failed the envelope's Julia rich-package claim:
  - command: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json`
  - result: `ok=false`; error: `julia: source-backed audit failed ... declared load-bearing packages not imported in source: Grassmann, Manifolds, Z3`.
- Interpretation: the packet really is hash-bound to committed Julia/PyTorch S2/S5 anchors, but the new mode-sweep source is a Python/JAX/SymPy/Z3/cvc5 packet. The envelope's `engine_contract.mode="all_three_full_sims"` and Julia load-bearing package declarations are too strong for the new source. The honest label is "Python/JAX/SymPy mode sweep over hash-bound committed three-engine anchors", not a fresh all-three full sim.

## Q6 Closure

Earned:

- RESTRICTED and QUOTIENTED modes are demonstrated on two committed stages, S2 and S5, with hash-bound FREE anchors.
- S2 RESTRICTED genuinely recomputes a constrained eta-shell family and exact boundary controls.
- S5 RESTRICTED genuinely names survivor/partial/excluded rows under `z >= 0`, including `Ni_Pit_L` excluded and `Ni_Source_R` surviving.
- S5 QUOTIENTED genuinely computes an 8x8 named terrain separation matrix via pinned `A,b` signatures and reports no collapsed pairs.
- Independent audit recomputation matches the recorded S2 narrowing values, no-op hash, S5 quotient matrix count, anchor hashes, and S2 N01 gap.

Not earned:

- No RATCHETED/mode-4 claim. The packet explicitly excludes RATCHETED and does not recompute induced geometry after sequential constraints.
- No stages beyond S2 and S5.
- No trend, monotonic program-level claim, or evidence that other stages will behave similarly.
- No fresh all-three full sim for this packet. Julia/PyTorch are inherited hash-bound anchors, not fresh source-backed mode-sweep lanes.
- No packet-source proof that `A` is gauge-variant and `F` gauge-invariant; that descent split is correct and audit-demonstrated, but not computed in the packet source.
- No packet-source computed N01 both-way row; S2 value is correct under audit recomputation, but the emitted row is by construction.

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

Caveats:

- G1: S2 quotient descent split `F descends / A does not` is mathematically correct and audit-demonstrated, but packet source emits the status rows by construction rather than computing an explicit gauge transformation.
- G2: N01 order rows are correct for the checked S2 case, but packet source emits literal order rows rather than computing both orders from anchor rows.
- G3: envelope overstates the new packet as `all_three_full_sims` with source-backed Julia load-bearing packages. The actual fresh computation is Python/JAX/SymPy/Z3/cvc5 over hash-bound committed S2/S5/lens anchors.

Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This earns modes 2-3 demonstrated on S2/S5 with named caveats, not mode 4, not other stages, and not a trend.

## Builder-Hardening Addendum: G1/G2/G3 Closure Pending Re-Audit

Status: builder hardening complete; prior verdicts stand pending fresh re-audit.

- G1 closed in the builder: the packet now computes an explicit gauge family `phi -> phi + alpha(chi,eta)`, emits computed `delta_A` with `d_chi=alpha1`, records the nonconstant sample `d_chi=1`, and computes symbolic `delta_F=0`. The descent split is emitted from those computed rows, not from a literal status assertion.
- G2 closed in the builder: `order_rows()` now computes restrict-then-quotient and quotient-then-restrict as two pipelines over the same anchor inputs. Fresh rows record S2 counts `2/2` with gap `0` and S5 counts `7/7` with gap `0`.
- G3 closed in the builder: the envelope mode is now `julia_canon_plus_jax_diagnostic`, lanes are `["julia", "jax"]`, and PyTorch is explicitly omitted because this packet has no graph/network/autograd claim path. The Julia load-bearing claim is now the fresh `Symbolics`/`Z3` gauge mirror, not inherited `Grassmann`/`Manifolds` anchor language.

Fresh rerun validators:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s2_s5_mode_sweep_v0/geo_s2_s5_mode_sweep_v0.py` returned `ok=true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s2_s5_mode_sweep_v0/validate_geo_s2_s5_mode_sweep_v0.py` returned `ok=true`, `errors=[]`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json` returned `ok=true`.

## Focused Re-Audit Addendum: G1/G2/G3 Hardening

Scope: re-audit only of the three named caveats G1/G2/G3 after hardening. I did not build this packet. I did not `git add` or commit. The only write from this pass is this addendum.

Fresh checks run:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json` returned `{"ok": true, "result_json": "system_v6/sims/geo_s2_s5_mode_sweep_v0/results/geo_s2_s5_mode_sweep_v0_envelope_results.json"}`.
- Independent read-only recomputation against the current result JSON and committed S2/S5 anchors matched the rows quoted below.
- Grep check for hardcoded order/mode literals in source found no source-side hardcoded `all_three_full_sims`, no source-side `N01_order_gap.*0`, and no source-side hardcoded `restrict_then_quotient_count.*2/7` or `quotient_then_restrict_count.*2/7`. The only remaining expected literal gap checks are in the validator assertions.

G1 re-audit: closed. The packet now computes an explicit gauge transformation in source: `alpha = alpha0 + alpha1 * chi`, `a_gauge["d_chi"] = a_chi + diff(alpha, chi)`, `delta_a = a_gauge - A`, and `delta_f = diff(A'_chi, eta) - diff(A'_eta, chi) - F`. The quoted result rows are `computed_delta_A={"d_chi":"alpha1","d_eta":"0","d_phi":"0"}`, `computed_delta_A_nonzero_sample_alpha_chi={"d_chi":"1","d_eta":"0","d_phi":"0"}`, `computed_original_F_eta_chi="-2*sin(2*eta)"`, `computed_transformed_F_eta_chi="-2*sin(2*eta)"`, and `computed_delta_F_eta_chi="0"`. Hand check for the packet's `alpha=chi` sample: `delta_A_eta=0`, `delta_A_chi=1`, `F0=-2*sin(2*eta)`, `F'= -2*sin(2*eta)`, `delta_F=0`.

G2 re-audit: closed. `order_rows()` now calls computed S2 and S5 pipelines, not literal count rows. For S2, `s2_order_row()` constructs `restricted_first`, maps those rows through `quotient(row) -> z=cos(2*eta)`, constructs `quotient_first`, filters by `0 <= z <= 1/2`, then computes `gap = abs(len(restrict_then_quotient) - len(quotient_then_restrict))`. Independent recomputation for S2 gave `restrict_then_quotient=[{"eta":"pi/6","z":"1/2"},{"eta":"pi/4","z":"0"}]`, `quotient_then_restrict=[{"eta":"pi/6","z":"1/2"},{"eta":"pi/4","z":"0"}]`, and `gap=0`, matching result counts `2/2` and `N01_order_gap=0`.

G3 re-audit: closed. The envelope is now honest: `engine_contract.mode="julia_canon_plus_jax_diagnostic"`, `lanes=["julia","jax"]`, and `omitted_lanes={"pytorch":"omitted: no graph/network/autograd claim path in this mode-sweep diagnostic"}`. Strict source-backed validation passes under that declared mode. The remaining Julia load-bearing claim is not inherited `Grassmann`/`Manifolds`; it is `aligned_packages_load_bearing=["Symbolics","Z3"]` with `role_id="julia_symbolics_gauge_mirror"`, and it gates rows through `build_gates["julia_symbolics_gauge_mirror"]=true` plus tool-call gates `["julia_symbolics_gauge_mirror","s2_quotient_descends_F_not_A"]`.

Audit-critical rows unchanged:

- S2 narrowing row remains `before_loop_count=5`, `after_loop_count=2`, `excluded_loop_count=3`.
- Excluded eta rows remain `["pi/12","pi/3","5*pi/12"]`.
- S5 quotient row remains `off_diagonal_distinguishable_count=56`, `off_diagonal_pair_count=56`, `collapsed_pairs=[]`.

Plain meaning of the S5 `56/56` row: all eight named terrain generators remain pairwise distinguishable under the declared quotient probe family after quotienting. The declared probe family is the committed pinned affine Bloch generator data `A,b`; the matrix is computed by hashing each named row's pinned `A,b`, comparing every directed off-diagonal pair, and recording named collapsed pairs. Independent recomputation over `Ne_Spiral_R`, `Ne_Vortex_L`, `Ni_Pit_L`, `Ni_Source_R`, `Se_Cannon_R`, `Se_Funnel_L`, `Si_Citadel_R`, and `Si_Hill_L` gave `56/56` distinguishable directed off-diagonal pairs and `collapsed_pairs=[]`.

Conclusion: G1 closed; G2 closed; G3 closed. Verdict for the packet under the original bar: `GENUINE`, with the original accepted parts standing and the three named caveats closed by hardening. Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no RATCHETED/mode-4 claim, no stages beyond S2/S5, and no trend/program-level promotion.
