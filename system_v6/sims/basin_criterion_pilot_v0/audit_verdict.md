# basin_criterion_pilot_v0 audit verdict

Auditor: codex2 cross-backend fresh audit.
Scope: read-only audit except this file. Note: my local recomputation ran the pilot/tests, and the pilot's current `build_payload()` rewrites its untracked result JSONs when invoked. I did not run `git add` or `git commit`.

## Verdict

`basin_criterion_pilot_v0` is **GENUINE-WITH-CAVEATS as a scratch-diagnostic criterion pilot**.

It does **not** satisfy the full 9-requirement basin-packet contract. It earns:

- the criterion made operational on the committed affine terrain/source surfaces;
- reproducible panel classifications for the implemented rows (`Ne_Spiral_R`, `Ni_Source_R`);
- independent recomputation support for the audit-requested `Se_Funnel_L` and `Ni_Pit_L` affine classifications;
- the honest affine result that the committed affine terrain rows do not expose multiple isolated sub-basins;
- the correct frontier: nonlinear/composite/stage-word objects, not affine one-attractor rows.

It does **not** earn:

- a formal basin theorem;
- a saturated `R_C` transition semigroup;
- a basin partition into terminal/metastable/leaky classes;
- a Morse/Conley graph admission;
- a QIT-engine omega-limit claim;
- a real Julia runtime lane;
- sub-basin claims.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Contract Sources Checked

The committed basin contract at `50f16d82d` says an attractor-basin object needs state/update/trapping/escape evidence. Key source lines:

- `system_v6/receipts/attractor_basin_criterion_20260611.md:27-31`: attractor-basin status requires receipt-backed rows and `F(A) subset A` or an inward/tangent continuous-time test.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:41-44`: `Se_Funnel_L` and `Ni_Pit_L` preserve the Bloch ball, while the conditioned `T_pi/6` shell is shell-breaking.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:53-55`: negative real spectrum supports affine attraction; purely imaginary/zero transverse modes do not.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:91-94`: zero conditioned-shell survivors are not a hidden attractor.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:314-321`: terminal/closed communicating class requires a closed finite `R_C` graph class; plain communicating class is weaker.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:331-343`: the 9 basin-packet requirements.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:351-358`: missing negative controls demote, and clustering/model agreement is never a basin.
- `system_v6/receipts/attractor_basin_criterion_20260611.md:360-368`: the pilot card must carry the binding contract before execution.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md:3-13`, especially exactness-class stability, route genuineness, can-fail controls, and source-backed route checks.

## Commands Run

```bash
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_criterion_pilot_v0/basin_criterion_pilot_v0.py
```

Result: `{"ok": true, "result_path": "system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json"}`.

```bash
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/basin_criterion_pilot_v0/tests/test_basin_criterion_pilot_v0.py
```

Result: `3 passed in 1.18s`.

```bash
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json
```

Result: shape validator passed.

```bash
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json
```

Result: failed on the Julia lane: no source-backed rich package evidence for `Z3`/`sympy` in a real Julia source.

## 9-Requirement Adjudication

| Requirement | Verdict | Audit finding |
|---|---:|---|
| 1. finite `S` | PARTIAL | The envelope declares bounded Bloch-ball affine state plus finite `Z4 x Z2` deep-chain representatives (`results/...envelope_results.json:67-80`). This is enough for a pilot, but not one finite basin graph. |
| 2. `Adm_C` | PARTIAL | `Adm_C` is named as scratch gates, shell survivor predicates, and quotient well-definedness (`results/...:51-53`). It is not a single executable predicate over one saturated `S`. |
| 3. explicit `R_C` | FAIL/BLOCKED | The source and result explicitly say saturated `R_C` is not instantiated (`basin_criterion_pilot_v0.py:334-337`, `results/...:63-65`). Affine `A,b` exists only for selected panel rows. |
| 4. trapping test | PARTIAL | Whole-ball trapping/inwardness is recomputable for `Se_Funnel_L`; conditioned `T_pi/6` trapping fails. The result itself marks trapping `fail` for `T_pi/6` (`results/...:87-90`, `123-126`). |
| 5. Lyapunov/monotone observable | PASS, bounded | `V_narrow` is emitted from deep-chain narrowing measures (`results/...:507-556`). It is a ratchet-step observable, not a Lyapunov proof for a completed `R_C` basin graph. |
| 6. escape tests | PASS, bounded | Shell-breaking rows and empty survivors are real escape/failure evidence (`results/...:447-460`). The mortality exhibit supports quotient/order failure, not a full basin boundary. |
| 7. basin partition | FAIL/BLOCKED | The result says no terminal/metastable/leaky partition over the saturated carrier was computed (`results/...:138-141`). |
| 8. engine-DoF perturbation | PASS, bounded | The adjacent swap changes well-definedness/mortality status (`results/...:366-372`). This is an order-DoF diagnostic, not the QIT stage-word omega-limit test. |
| 9. seven negative controls | PARTIAL/FAIL for full contract | All seven names are present, but `root_off`, `F01_only`, and `N01_only` are blocked, while the others are diagnostic/cited controls rather than all computed firing controls (`results/...:474-503`). |

Bottom line: the pilot carries the 9-row contract with honest pass/fail/blocked status, but the full basin-packet contract is not passed.

## Recomputations

### `Se_Funnel_L`

Committed affine row recomputed from `geo_s5_terrain_flows_v0_jax_results.json`:

- `A = -4/5 I + K` where `K` is antisymmetric.
- Eigenvalues: `-4/5`, `-4/5 - 2I/5`, `-4/5 + 2I/5`; numeric real parts all `-0.8`.
- Fixed point: `(0,0,0)`.
- Whole-ball trapping check: for `r=(x,y,z)`, `d||r||^2/dt = 2 r dot (A r) = -8/5 (x^2+y^2+z^2)`, so the vector field is strictly inward on the unit sphere except at the origin.
- Whole-ball classification: globally attracting origin for the committed affine flow.

Conditioned-shell row recomputed/read from `ratchet_s6_terrain_sweep_v0_envelope_results.json:1901-1981`:

- `z_dot = -sqrt(2)*cos(theta + pi/4)/5 - 2/5`.
- `d||r||^2/dt = -8/5`.
- `shell_average_z_dot = -2/5`.
- `shell_compatibility = shell_breaking`.
- survivor set is empty; fixed point has `z=0`, radius squared `0`, while `T_pi/6` requires `z=1/2` and radius squared `1`.

Classification: whole Bloch ball is attracting; conditioned `T_pi/6` is `shell_breaking`, `neither`, `empty_conditioned_survivor`. It is not invariant-but-not-attracting and not repelling under the criterion.

### `Ni_Pit_L`

Committed affine row recomputed from `geo_s5_terrain_flows_v0_jax_results.json`:

- `charpoly = lambda**3 + lambda**2 + 189*lambda/400 + 203/2400`.
- Eigenvalues numerically: `-0.341645905918435`, `-0.3291770470407825 +/- 0.3731199415923834 i`.
- Fixed point:
  - `x = -8*(8 + 5*sqrt(3))/203`
  - `y = 8*(-8 + 5*sqrt(3))/203`
  - `z = -139/203`
- `||r_star||^2 = 37113/41209 < 1`.
- Whole-ball answer: the committed row states the whole Bloch ball converges to `r_star` because the pinned spectrum has negative real part; recomputed eigenstructure supports this.

Conditioned-shell row from `ratchet_s6_terrain_sweep_v0_envelope_results.json:1655-1735`:

- `z_dot = -sqrt(2)*cos(theta + pi/4)/5 - 3/4`.
- `d||r||^2/dt = -9/8`.
- `shell_average_z_dot = -3/4`.
- `shell_compatibility = shell_breaking`.
- survivor set is empty; fixed point has `z=-139/203`, radius squared `37113/41209`, not the shell values.

Classification: whole Bloch ball is attracting to one displaced fixed point; conditioned `T_pi/6` is `shell_breaking`, `neither`, `empty_conditioned_survivor`.

### Affine one-attractor expectation

Confirmed for the scoped affine question. The pilot result says committed affine rows yield unique attracting fixed points, attracting slices, or non-attracting orbits, and no generic multiple isolated basins (`results/...:766-772`). The audit recomputations above support that for `Se_Funnel_L` and `Ni_Pit_L`.

## Guard Audit

Grep target:

```bash
rg -n "\\b(attractor|basin|sub-basin|subbasin|Morse|Conley|terminal|closed communicating class|communicating_class|omega-limit|omega|trapping|escape|R_C|Adm_C)\\b" system_v6/sims/basin_criterion_pilot_v0 -g '!audit_verdict.md'
```

Findings:

- No promoted QIT-engine omega-limit row exists. The result lists `QIT-engine omega-limit admission` under `not_earned` (`results/...:165-173`). This is honest.
- The guard text is present and correctly blocks similarity/model-agreement basin language (`results/...:92-95`, `499-501`).
- The result uses affine `fixed_point_and_basin_statement` from the committed S5 row (`results/...:300`) and scopes it to whole-ball affine attraction, not conditioned-shell basin language.
- Caveat: `Ni_Source_R` is labeled `terminal/closed_communicating_class` (`results/...:101-104`, `337`), but the contract says that term requires a closed finite `R_C` graph class (`attractor_basin_criterion_20260611.md:314-315`). Because `R_C` and basin partition are blocked, this term is overearned. The earned wording is `attracting affine fixed point on the whole Bloch ball`, not terminal/closed communicating class.

## Shape And Process

- Canonical helper: verified. The source imports `build_envelope` (`basin_criterion_pilot_v0.py:24-25`) and calls it (`basin_criterion_pilot_v0.py:588-635`). The helper signature is `build_envelope(sim_id, lanes, mode, claim_path_tools, crossover_proofs, divergence, ...)` (`scripts/build_three_engine_envelope.py:134-150`), and emits `schema_version = three_engine_sim_result_v1` (`scripts/build_three_engine_envelope.py:181-203`).
- Envelope shape: generic validator passed.
- Source-backed shape: `--require-source-backed` failed on the Julia lane. The artifact is honest that Julia is a validator slot only (`results/...:374-388`, `419-443`), but any real-Julia-runtime claim is rejected.
- PyTorch: omission is honest for this packet (`results/...:386-388`).
- Build card: `/tmp/basin_pilot_card.md` exists and carries the binding contract, but no packet-local committed `build_card.md` exists under `system_v6/sims/basin_criterion_pilot_v0/`. The committed contract now requires the card rule (`attractor_basin_criterion_20260611.md:360-368`).
- Parent lineage: `parent_lineage` is empty (`results/...:505`). That is acceptable for a local pilot envelope but not evidence of the requested worker/tree route.
- SMT: z3/cvc5 run, but only as a boolean `all_pass` gate (`basin_criterion_pilot_v0.py:428-444`, `results/...:340-350`). This is not structural SMT over erased flips or finite transitions.
- Tool calls: only one `sympy` tool call is recorded (`results/...:774-785`). `z3` and `cvc5` are in `TOOL_MANIFEST`, but not in `tool_calls`.
- Seeds: no `seed`/`seeds` field is present. The packet is deterministic symbolic/no-RNG in practice, but the envelope does not record that explicitly.
- Ceilings: preserved throughout (`classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; `results/...:180`, `462`, `506`).

## Named Caveats

- **G1 - Contract partial, not full pass.** `R_C` explicit is blocked, conditioned-shell trapping fails, basin partition is blocked, and several controls are blocked/diagnostic. This prevents full basin-packet admission.
- **G2 - Implemented rows differ from audit-requested exact rows.** The pilot computes `Ne_Spiral_R` and `Ni_Source_R` (`basin_criterion_pilot_v0.py:45`). This audit separately recomputed `Se_Funnel_L` and `Ni_Pit_L`; those rows are not first-class `criterion_rows` in the pilot.
- **G3 - Vocabulary overearn.** `terminal/closed_communicating_class` is not earned without a closed finite `R_C` graph and absent-exit proof.
- **G4 - Negative controls named, not all fired.** `root_off`, `F01_only`, and `N01_only` are blocked; `quotient_erased`, `commutative_collapse`, `shuffled_order`, and `similarity_only_cluster` are bounded diagnostics/citations.
- **G5 - Julia lane is a slot, not a runtime.** Honest label, but source-backed validation fails for Julia load-bearing package claims.
- **G6 - SMT is too shallow for basin admission.** z3/cvc5 gate the aggregate boolean, not finite transition closure, erased flips, or boundary/exits.
- **G7 - Process artifact gap.** `/tmp/basin_pilot_card.md` exists, but there is no packet-local committed `build_card.md`; parent lineage is empty.
- **G8 - Rerun side effect.** The pilot/test rerun rewrote untracked result JSONs because the current source writes lane/envelope outputs during `build_payload()`. No staging or commit was done.

## Closure

The pilot earns a real scratch-diagnostic result: the basin criterion is executable on committed terrain rows, the affine classifications are coherent, the conditioned shell is correctly demoted to shell-breaking failure evidence, and the affine sub-basin expectation is honestly negative.

The pilot does not earn basin admission. The next admissible build is a composite/stage-word or deep-chain packet with an explicit finite `S`, executable `Adm_C`, explicit `R_C`, trapping/escape graph, basin partition, structural SMT/controls, and a real source-backed runtime story.

## Builder-Hardening Addendum - 2026-06-11

Status: bounded hardening round completed; ceiling remains `scratch_diagnostic`.

- G2 closed: `Se_Funnel_L` and `Ni_Pit_L` are now first-class `criterion_rows` in the packet-generated envelope and leg results.
- G3 closed: generated result rows and summary vocabulary no longer use the overearned finite-transition terminal-class label; attracting affine rows use `attracting affine fixed point on the whole Bloch ball`.
- Scope carried forward: G1/G4/G5 remain honest caveats. The explicit `R_C` transition-graph packet is still the named successor for terminal-class language, absent-exit proof, blocked controls, and finite partition work; the Julia lane remains a validator slot label, not a runtime promotion.
- Build card persisted: `system_v6/sims/basin_criterion_pilot_v0/build_card.md`.
- Fresh packet rerun: `{"ok": true, "result_path": "system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json"}`.
- Fresh validator: `{"ok": true, "result_json": "system_v6/sims/basin_criterion_pilot_v0/results/basin_criterion_pilot_v0_envelope_results.json"}`.
