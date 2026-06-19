# Fresh audit verdict: ratchet_s2_three_shell_chain_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: read-only audit of a codex2-built packet, except this `audit_verdict.md`. I did not git add or commit anything.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md`. The calibrated bar keeps convention/order pins, can-fail controls, route genuineness, erasure honesty, scratch ceilings, and fresh-context audits; it allows one genuine derivation plus independent solver/cross-engine binding when the split is honest.

Wizard route truth: partial Max Assembly only. I loaded the v4.2 packet, skills manifest, and compact MMM, but did not spawn native subagents because the available `spawn_agent` tool contract allows spawning only when the user explicitly asks for subagents/parallel agent work. This verdict is therefore based on direct source reads, parent/result inspection, fresh recomputation, and tool validators, not on completed council/subagent receipts.

Audit-time state:

- Target packet status: untracked local artifact, `?? system_v6/sims/ratchet_s2_three_shell_chain_v0/`.
- Calibration and both parents are tracked. The target packet itself is local artifact evidence until an explicit later staging/commit action.
- The packet validator result already existed and read `ok=true`, `errors=[]`. I did not rerun the packet validator as a command because it writes `*_validator_results.json`; I called its `validate(payload)` function read-only and got `ok=true`, `errors=[]`.
- Repo validator passed plain, `--require-source-backed`, and `--strict-source-backed`.

## Named caveats

- `CAVEAT_UNTRACKED_TARGET`: the target packet directory is untracked; this audit accepts local artifact evidence, not committed packet status.
- `CAVEAT_JAX_NAME`: the envelope calls the Python exact/SymPy/z3/cvc5 sidecar the `jax` lane. The result explicitly says it is "Python exact/SymPy plus z3/cvc5" and makes no JAX-array claim.
- `CAVEAT_PANEL5_SIGN_RECONCILIATION`: panel 5 literally pre-registered the annular flux signs as `pi*(1/2 - sqrt(3)/2)`, `-pi/2`, total `-sqrt(3)*pi/2`. The packet's primary Step 2 row uses the committed two-shell boundary orientation and records the opposite signs: `pi*(-1/2 + sqrt(3)/2)`, `pi/2`, total `sqrt(3)*pi/2`. The negative signs do appear in the packet as the flipped-orientation control and beta-generator quotient gaps. This is a sign-convention reconciliation caveat, not a hidden arithmetic defect, because the packet pins the orientation and the `pi/6 -> pi/4` anchor is byte-exact against `15b1d1899`.
- `CAVEAT_JULIA_TABLE_ROWS`: Julia mirrors exact scalar rows as explicit string rows; the load-bearing Julia computation is the Z3.jl chain-additivity proof with no peer-result read.
- `CAVEAT_NO_REQUIRE_PYTORCH`: I did not run `--require-pytorch`; the packet explicitly omits PyTorch for a no graph/network/autograd/PyTorch-specific claim path.
- `CAVEAT_ORDINAL_NOT_AUDITED`: I audited the packet content and parents, not the global claim that this is the fifth RATCHETED sim.

## Q1 - 3-leaf union

Verdict: PASS.

Source support:

- Target source cites `geo_union_rule_k_leaves_v0` at commit `8a46c8627` and computes weights with `densities = [1/2, sqrt(3)/2, 1]` normalized by their sum (`ratchet_s2_three_shell_chain_v0.py:243-274`).
- Parent source computes `rho_sin_2eta` and `weight = density / total` (`geo_union_rule_k_leaves_v0_python.py:81-92`).
- Parent result pins the finite-k rule as `leaf_density=rho(eta)=sin(2*eta)` and `finite_k_distinct_union_rule=...sin(2eta_i)/sum_j...` (`geo_union_rule_k_leaves_v0_envelope_results.json:234-240`, `664`).
- Parent audit unfences only finite distinct nonboundary fixed-eta Hopf leaves, with repeated leaves collapsed and boundary/transverse conditioning fenced (`geo_union_rule_k_leaves_v0/audit_verdict.md:168-185`).

Recomputation:

- `rho = (sin(pi/6), sin(pi/3), sin(pi/2)) = (1/2, sqrt(3)/2, 1)`.
- Sum is `(3 + sqrt(3))/2`.
- Weights are `(1, sqrt(3), 2)/(3 + sqrt(3))`, equivalently `((3 - sqrt(3))/6, (sqrt(3) - 1)/2, (3 - sqrt(3))/3)`.
- Weight sum recomputes to `1`.
- Parent-lineage source/result/audit hashes embedded in the envelope all recomputed equal to current file bytes.
- Equal-weight note is honest: these three rhos are `1/2`, `sqrt(3)/2`, and `1`, so the committed `pi/6`/`pi/3` equal-weight subtlety does not arise.

## Q2 - per-leaf geometry

Verdict: PASS.

Source support:

- Target source uses `A|_T = dphi + cos(2*eta) dchi` (`ratchet_s2_three_shell_chain_v0.py:216-240`).
- Target Step 1 records the self-dual `eta=pi/4` leaf with vanished `dchi` coefficient (`ratchet_s2_three_shell_chain_v0.py:289-293`).
- The two-shell parent audit already accepted the self-dual `eta=pi/4` row as the committed anchor (`ratchet_s2_two_shell_flux_v0/audit_verdict.md:42-52`).

Recomputation:

- `cos(2*pi/12)=cos(pi/6)=sqrt(3)/2`.
- `cos(2*pi/6)=cos(pi/3)=1/2`.
- `cos(2*pi/4)=cos(pi/2)=0`.
- These match the target result's `dchi` coefficients for `pi/12`, `pi/6`, and `pi/4`.

## Q3 - flux chain

Verdict: PASS with `CAVEAT_PANEL5_SIGN_RECONCILIATION`.

Source support:

- Target source computes coefficient gaps as `c1-c2`, `c2-c3`, and `c1-c3`, then multiplies by physical chi-period `pi` (`ratchet_s2_three_shell_chain_v0.py:277-286`, `352-385`).
- Target result pins `physical_chi_period_honoring_2_to_1_cover = pi` and records both annular fluxes plus the total row (`ratchet_s2_three_shell_chain_v0_envelope_results.json:760-790`).
- Two-shell parent pins the `pi/6 -> pi/4` physical-period Stokes row as `pi/2` with `stokes_match=0` (`ratchet_s2_two_shell_flux_v0_envelope_results.json:748-760`).

Recomputation under the packet/parent boundary orientation:

- `gap_12 = sqrt(3)/2 - 1/2`, so `flux_12 = pi*(-1/2 + sqrt(3)/2)`.
- `gap_23 = 1/2 - 0`, so `flux_23 = pi/2`.
- `gap_13 = sqrt(3)/2 - 0`, so `flux_13 = sqrt(3)*pi/2`.
- `flux_12 + flux_23 = sqrt(3)*pi/2 = flux_13`.
- Defect `flux_12 + flux_23 - flux_13 = 0`.
- Pairwise holonomy gap defect `gap_13 - gap_12 - gap_23 = 0`.

Panel-5 sign reconciliation:

- Panel 5's literal signs are the orientation-reversed version of the packet's primary row.
- The packet has explicit flipped signs in controls: `flux_12 = pi*(1 - sqrt(3))/2`, `flux_23 = -pi/2`, `flux_13 = -sqrt(3)*pi/2`.
- The quotient beta-generator row also carries `gap_12 = pi*(1/2 - sqrt(3)/2)`, `gap_23 = -pi/2`, `gap_13 = -sqrt(3)*pi/2`.

## Q4 - path specificity

Verdict: PASS.

Source support:

- Target source computes `direct_weights` and `pair_then_extend` as separate pipelines (`ratchet_s2_three_shell_chain_v0.py:295-304`).
- It serializes separate direct and pairwise objects and compares them (`ratchet_s2_three_shell_chain_v0.py:401-415`).
- Parent result records bracketing agreement only "when iterated union carries summed group mass" (`geo_union_rule_k_leaves_v0_envelope_results.json:877-912`).

Recomputation:

- Direct k=3 weights equal `((3 - sqrt(3))/6, (sqrt(3) - 1)/2, (3 - sqrt(3))/3)`.
- Pairwise-then-extend weights with group mass carried simplify to the same three weights.
- Direct object hash and pairwise object hash are both `8162bf7e49deac09771cf3a506c76938180f32c987ab93a952cb4b86b664596d`.
- Agreement is real for the two explicit pipelines. It does not prove arbitrary path/order commutation beyond the committed bracketing row.

## Q5 - Step 3 quotient

Verdict: PASS.

Source support:

- Target source applies `Z4` by `(phi, chi) -> (phi + pi/2, chi)` on all three leaves (`ratchet_s2_three_shell_chain_v0.py:387-399`).
- Target result records global phase gaps zero and alpha/beta generator gaps carrying the chain quantities (`ratchet_s2_three_shell_chain_v0_envelope_results.json:794-817`).

Recomputation:

- Z4 shifts only the global phase direction and preserves `eta`; therefore the three leaves and eta-chi annular chain are not erased.
- For the beta generator, the total survived gap is `-sqrt(3)*pi/2`.
- Adjacent beta gaps add: `pi*(1/2 - sqrt(3)/2) + (-pi/2) = -sqrt(3)*pi/2`.
- The packet's `chain_additivity_survives=true` and `flux_rows_survive=true` are supported for this scoped quotient row.

## Q6 - controls

Verdict: PASS.

Recomputations:

- Equal-weight defect propagates into annulus 12:
  - correct weighted coefficient `3/2 - sqrt(3)/2`;
  - equal-weight value `1/4 + sqrt(3)/4`;
  - defect `-5/4 + 3*sqrt(3)/4`;
  - physical defect `pi*(-5 + 3*sqrt(3))/4`;
  - control fires.
- Equal-weight defect propagates into annulus 23:
  - correct weighted coefficient `-3/2 + sqrt(3)`;
  - equal-weight value `1/4`;
  - defect `7/4 - sqrt(3)`;
  - physical defect `pi*(7 - 4*sqrt(3))/4`;
  - control fires.
- Flipped orientation flips all three chain signs and the control fires.
- Nothing-excluded control is byte-exact on the Step 1 exact joint object.
- Naive finite-union conditioning fails as `0/0` in ambient S3 measure.
- The `pi/6 -> pi/4` anchor row is byte-exact against `15b1d1899`: computed and parent stable JSON hashes are both `be059645e3704bae95dbde8c23aea45e9e714fa2e2ba88e4342365c60b69abd0`.

## Q7 - standard checks

Verdict: PASS with named caveats.

Fresh commands/checks:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/ratchet_s2_three_shell_chain_v0/results/ratchet_s2_three_shell_chain_v0_envelope_results.json
```

Result: `ok=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_s2_three_shell_chain_v0/results/ratchet_s2_three_shell_chain_v0_envelope_results.json
```

Result: `ok=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/ratchet_s2_three_shell_chain_v0/results/ratchet_s2_three_shell_chain_v0_envelope_results.json
```

Result: `ok=true`.

Read-only packet validator import:

```text
validate(payload) -> ok=true, errors=[]
```

Additional standard evidence:

- `schema_version=three_engine_sim_result_v1`, `mode=RATCHETED`, and `classification=scratch_diagnostic`.
- `promotion_allowed=false`, `formal_admission=false`, and `formal_admission_allowed=false`.
- Claim-path tools are exactly `sympy`, `z3`, `cvc5`, `Z3`.
- Tool calls are one-to-one and load-bearing for those four tools.
- Capability receipts are present: Python `3.13.6`, SymPy `1.14.0`, z3 `4.16.0`, cvc5 `1.3.3`, Julia `1.12.6`, Z3.jl `1.0.4`.
- Real Julia leg: source uses `using Z3`, constructs solver variables, binds positive/flipped coefficient rows, records `reads_peer_result=false`, and result `all_pass=true`.
- Fresh Julia Z3.jl scratch check returned positive negated identity `unsat` and erased-flip forced equality `unsat`.
- Seeds are deterministic and explicit: `symbolic_seed=2026061105`, `smt_seed=2026061105`, `julia_seed=2026061105`, eta shells `[pi/12, pi/6, pi/4]`, Z4 order `4`.
- `rg -n "fixture|stub|mock|placeholder|todo|hack|fake|simulated|toy|synthetic|dummy|hardcoded|hard-coded" system_v6/sims/ratchet_s2_three_shell_chain_v0` returned no hits.
- Fences are explicit: no arbitrary finite/countable unions beyond the cited k-leaf rule, no transverse/non-leaf conditioning, no boundary leaves, no general order theorem, no manifold/axis/bridge/physics/promotion/formal-admission claim.

## Q8 - closure

Verdict: PASS, scoped closure.

This earns:

- a local three-shell RATCHETED `scratch_diagnostic` packet for `T_pi/12 union T_pi/6 union T_pi/4`;
- valid use of the committed k-leaf union rule for finite distinct nonboundary fixed-eta Hopf leaves;
- the three-leaf weights `(1, sqrt(3), 2)/(3 + sqrt(3))`;
- per-leaf connection coefficients `sqrt(3)/2`, `1/2`, `0`, including the self-dual `pi/4` leaf;
- a two-annulus flux chain and telescoping Stokes/holonomy additivity row under the committed two-shell boundary orientation;
- Z4 quotient survival for scoped chain quantities;
- real path-specificity comparison between direct k=3 conditioning and pairwise-then-extend with group mass carried;
- load-bearing SymPy exact rows, z3/cvc5 identity flips, and Julia Z3.jl identity flips under a scratch ceiling.

This does not earn:

- committed packet status by itself;
- literal panel-5 sign identity without the orientation-reconciliation caveat;
- 4+ shell chain claims beyond computed/cited parent rows;
- arbitrary finite/countable union theorem beyond the committed k-leaf rule;
- transverse, non-leaf, boundary-leaf, or singular-intersection conditioning;
- general order/path theorem;
- terrain/operator step;
- manifold, axis, bridge, physics, or `M(C,t)` claim;
- formal admission, promotion, canonical admission, or queue/status movement.

## Verdict

`GENUINE-WITH-CAVEATS`.

`ratchet_s2_three_shell_chain_v0` passes this fresh audit as a local, untracked, scoped `scratch_diagnostic` artifact. The math rows, parent lineage, controls, strict source-backed validators, Python z3/cvc5 checks, and Julia Z3.jl check support the three-leaf k-leaf ratchet plus the flux chain and telescoping additivity under the packet's committed two-shell boundary orientation. The sign difference against panel 5's literal flux wording is real and named; the packet reconciles it through its pinned orientation, flipped-orientation control, beta-generator row, and byte-exact two-shell anchor.

Accepted ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; local artifact evidence only until explicitly tracked/committed by a later action.
