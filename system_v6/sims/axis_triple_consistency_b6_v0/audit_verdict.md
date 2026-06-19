# Independent audit verdict - axis_triple_consistency_b6_v0

Bottom line: VERDICT = `GENUINE-WITH-CAVEATS` as a negative-result consistency packet.

The relation failed on the reported Hopf realization. Keep the packet as a real scratch diagnostic
for the pinned realization family, with `classification=scratch_diagnostic`,
`promotion_allowed=false`, `formal_admission_allowed=false`, and
`claim_ceiling=axis_readout_candidate_only + consistency_row_only`. Do not promote it to a
canonical cross-axis law, Axis-6 admission, Axis-0/3/6 independence proof, bridge evidence, physics
evidence, or proof that the scaffold relation is false on every faithful realization.

## What Was Checked

I kept the audit read-only except for this file. I did not run result-writing builder entrypoints.
Fresh read-only checks:

- `git status --short` showed `system_v6/sims/axis_triple_consistency_b6_v0/` as untracked before
  this audit file; unrelated modified result JSONs already existed elsewhere in the worktree.
- The work-order commit `f6112e407` is present and its row says the
  `b6 = -b0*b3` row is computable only as a consistency row, not an independence proof.
- Panel 6 commit `eba5fdca0` is present and pins q2 at two test points:
  `eta=pi/6+fiber -> b6=-1` and `eta=pi/3+base -> b6=-1`.
- Panel 8 commit `bba04c9c4` is present and pins the b6 controls:
  chance agreement `1/2` and convention flip `c=+a*b`.
- Packet-local validator function call:
  `validate_axis_triple_consistency_b6_v0.validate_payload(...)` returned `ok=true`,
  `error_count=0`.
- Generic three-engine validator function call:
  `validate_three_engine_sim_result.validate(..., require_pytorch=True, strict_source_backed=True,
  require_tool_intent=True)` returned `ok=true`, `error_count=0`.
- Pytest read-only run:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B -m pytest -q -p no:cacheprovider system_v6/sims/axis_triple_consistency_b6_v0/tests`
  returned `4 passed`.
- Source and result hashes in the envelope matched the files on disk for Julia, JAX, and PyTorch.

The actual scaffold line cited by the receipt is:

> Axis 6 — precedence / signed orientation: b_6 = -b_0 b_3. Anchors: L_A vs R_A; Phi_T∘O vs O∘Phi_T. Turns 4 operators into 8 signed operators.

The nearby symbolic-layer source also states `b6 = -b0*b3` and gives the directional table
`inner+white=up`, `inner+black=down`, `outer+white=down`, `outer+black=up`. The relation is a real
source claim; the audit question is what this negative realization falsifies.

## Negative Result

The reported table values are internally consistent:

- total agreement: `16/48 = 0.3333333333333333`;
- total violations: `32/48`;
- non-neutral agreement: `16/32 = 0.5`;
- neutral-expected rows: `16`;
- convention-flip control agreement: `16/48`, not a global sign repair;
- scrambled b6 control: `12/48 = 0.25` on all rows and `12/32 = 0.375` on non-neutral rows;
- commuting control: `O=D_z`, `Phi_T=D_z` gives `48/48` neutral rows;
- SMT bindings: z3 and cvc5 both make the stronger full-agreement/no-violation claim `unsat`, and
  the erased-flip row `sat`.

The packet's `all_pass=true` means the negative table, controls, source locks, and validators are
coherent. It does not mean the relation holds.

## Computation Independence

Anti-by-construction status: PASS, with backend-granularity caveats.

Within each row, `b0`, `b3`, and `b6` are computed before the relation is evaluated:

- `b0` path: `sign(cos 2eta)` on the Hopf eta leaf.
- `b3` path: panel convention `fiber=+1`, `base/lifted_base=-1` applied to the Axis-3 fiber/base
  classification.
- `b6` path: pinned `S4:D_z` and pinned `S5:Ne_Spiral_R` at `h=1/2`, evaluated as
  `sign(||Phi_T(O(rho)) - O(Phi_T(rho))|| * Delta_z)` on the Hopf Bloch state.

Manual recomputation from those separate paths matched the packet on representative rows:

| row | b0 | b3 | b6 | expected `-b0*b3` | holds | weighted z |
|---|---:|---:|---:|---:|---|---:|
| `pi/8`, fiber, `chi=0` | `+1` | `+1` | `-1` | `-1` | true | `-0.027693987819115` |
| `pi/4`, base, `chi=0` | `0` | `-1` | `-1` | `0` | false | `-0.036755338799217` |
| `3*pi/8`, base, `chi=pi/4` | `-1` | `-1` | `+1` | `-1` | false | `0.01187583862488` |

The two panel-6 q2 anchors were evaluated and both passed:

| panel point | b0 | b3 | computed b6 | expected `-b0*b3` | panel expected | holds |
|---|---:|---:|---:|---:|---:|---|
| `eta=pi/6`, fiber | `+1` | `+1` | `-1` | `-1` | `-1` | true |
| `eta=pi/3`, base | `-1` | `-1` | `-1` | `-1` | `-1` | true |

The panel points therefore do not support a sign-convention-collapse reading. The full-sample failure
appears only after widening beyond the two pinned anchors.

Caveat: JAX and PyTorch lanes share the packet's Python common module for sample construction and
pin parsing; Julia is separately implemented and matches aggregate values. The lanes have
`reads_peer_result=false`, but this is not yet a fully independent per-row derivation in all three
backends. v1 should emit independent per-row sign vectors and hashes from each lane, including Julia.

## Live Readings

These readings remain live. Do not collapse them.

### A. Realization-unfaithful

Status: LIVE, currently the strongest explanation.

The build card explicitly names the compromise: `b6` is a Hopf-state realization of the pinned
`D_z`/`Ne_Spiral_R` precedence functional, and the full pinned Hopf sample is allowed to violate the
relation. The committed Axis-6 packet lives on the Family A 33-cell carrier, while this packet
transplants the same pinned precedence functional onto a bounded Family B Hopf sample. The parent
Axis-6 audit says the follow-on packet must compute Axis-3 on the same 33-cell carrier before making
the three-way claim. That has not happened here.

Evidence for this reading:

- Axis-6 parent: genuine precedence readout on the 33-cell Family A carrier.
- Axis-3 parent: genuine placement readout on the Family B Hopf carrier, with its own audit caveat
  that Axis0 comparison is surrogate/projection-only, not a proved shared carrier.
- This packet uses the Hopf carrier for all three signs; that is a useful shared object but not the
  same object as the Axis-6 parent carrier.
- The two panel anchors pass, but the widened Hopf sample fails.

Adjudication: cite the result as a finding about this Hopf realization family unless a later faithful
shared-carrier packet excludes the realization mismatch.

### B. The scaffold relation itself fails on faithful realizations

Status: LIVE but not earned by this packet alone.

The source relation is real and direct. The packet gives real pressure against a universal reading,
because it computes a can-fail table and finds actual violations. But the relation-false-on-faithful-
realizations claim requires excluding the realization-unfaithful reading. This packet does not do
that, because it uses a Hopf transplant of the pinned precedence functional rather than computing
Axis-3 on the original 33-cell Axis0/Axis6 carrier or proving a carrier isomorphism.

Adjudication: the deepest reading survives as an open candidate, not a citable conclusion.

### C. b3-or-b0 realization mismatch

Status: LIVE.

`b3` is especially exposed. The committed Axis-3 packet's public placement polarity is
`-1` for fiber/gamma_in and `+1` for base/gamma_out. This packet uses the panel convention
`fiber=+1`, `base=-1`, because panel 6 q2 requires that convention to make both anchors produce
`b6=-1`. That can be correct for the scaffold relation, but it means the row is not literally using
the committed Axis-3 packet's stored placement sign without a convention transform.

`b0` is also open. The scaffold local formula is `b0=sign(cos 2eta)=sign(r_z)`, and this packet uses
that. The committed Axis-0 packet, however, is a different Family A 33-cell scalar-field readout with
its own caveat that the chosen field formula is one candidate, not the final Axis-0 readout. This
packet therefore tests the scaffold-local Hopf `b0`, not the committed Axis-0 field on its own
carrier.

Adjudication: this reading remains live. v1 needs an explicit convention ledger that distinguishes
`axis3_committed_placement_sign`, `scaffold_b3_sign`, and any transformed sign used in the relation.

### D. Neutral-handling artifact

Status: LIVE only as a semantics caveat, not as the cause of the negative.

The 16 neutral-expected rows are exactly the `eta=pi/4` rows where `b0=0`, so
`expected_b6_negative_b0_b3=0`. All 16 fail because computed `b6` is nonzero (`8` rows `-1`, `8`
rows `+1`). Including those rows makes the relation look worse: `16/48`. Excluding them gives the
fair binary sign comparison and still yields exact chance: `16/32`.

Adjudication: neutral treatment does not explain away the result. It creates a separate boundary
semantics question: if the relation is exact, `b0=0` predicts neutral `b6`; if `b0=0` is a boundary
to exclude, the non-neutral relation still has no signal above chance.

## Chance Context

For the non-neutral rows, the result is exactly the chance baseline:

- null model: independent agreement with probability `p=1/2`;
- observed: `k=16` agreements in `n=32`;
- `P(X=16 | n=32, p=1/2) = 0.13994993409141898`;
- two-sided absolute-deviation binomial p-value is `1.0`, because the observation is exactly at the
  null expectation.

Compared to the scrambled non-neutral control (`12/32`), the real relation (`16/32`) is not
statistically distinguishable at this sample size. A two-sided Fisher exact comparison for
`[[16,16],[12,20]]` gives `p=0.4500338411722007`.

Adjudication: the non-neutral table is consistent with full independence of computed `b6` from
`-(b0*b3)` on this realization. It is not evidence for a weak relation.

## Standards And Boundaries

Standards pass for a scratch negative-result packet:

- schema is `three_engine_sim_result_v1`;
- mode is `all_three_full_sims`;
- `classification=scratch_diagnostic`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`;
- envelope was built through `scripts/build_three_engine_envelope.py`;
- `TOOL_MANIFEST` has non-empty reasons;
- `TOOL_INTEGRATION_DEPTH` declares load-bearing tools;
- strict source-backed/tool-intent generic validator returned no errors;
- z3/cvc5 bindings are real computed-count gates;
- controls are real and falsify tautology/sign-flip readings;
- builder boundary held before this audit file: `no_builder_audit_verdict=true`.

Standards caveats:

- SMT is aggregate-count SMT, not row-local sign derivation SMT.
- Julia matches aggregate values but does not export the same per-row sign table/hash as JAX,
  PyTorch, and the envelope.
- The packet is untracked in this checkout at audit time, so status is `exists` plus fresh read-only
  validator/test evidence, not committed/canonical process evidence.
- This audit did not run result-writing entrypoints, because the request allowed writing only this
  `audit_verdict.md`.

## Named Caveats

`G1_REALIZATION_FAITHFULNESS_OPEN`:
The result is about the pinned Hopf realization of the precedence functional. It does not exclude
that the scaffold relation holds on a more faithful shared carrier.

`G2_B0_B3_CONVENTION_MISMATCH_OPEN`:
The packet uses scaffold/panel `b0` and panel `b3`, not the committed Axis-0 scalar field nor the
committed Axis-3 placement sign without convention transformation.

`G3_BACKEND_GRANULARITY`:
Three engines agree on counts, but JAX/PyTorch share common Python construction and Julia lacks a
persisted per-row sign-vector hash.

`G4_NEUTRAL_SEMANTICS_OPEN`:
The `b0=0` rows all violate exact neutral prediction. This strengthens the negative if included, but
v1 must decide whether boundary rows are in-scope relation rows or excluded boundary rows.

`G5_AGGREGATE_SMT_SCOPE`:
SMT binds computed counts and erased flips. It does not prove every row-local sign path.

## Citable Sentence

`axis_triple_consistency_b6_v0` is a genuine scratch negative consistency result: on the pinned Hopf
realization using `b0=sign(cos 2eta)`, panel `b3` convention `fiber=+1/base=-1`, and pinned
`S4:D_z` with `S5:Ne_Spiral_R` at `h=1/2`, the scaffold row `b6=-b0*b3` fails on the 48-row Hopf
sample (`16/48` total agreement; `16/32` non-neutral agreement, exactly chance), while the two panel
6 anchor points pass; this is a finding about that realization family, not proof that the source
scaffold relation is false on faithful realizations.

## What v1 Needs

1. Compute `b0`, `b3`, and `b6` on one faithful shared carrier. The highest-value discriminator is
   Axis-3 on the same 33-cell Family A carrier already used by Axis0/Axis6, or a proof-backed
   carrier map showing why the Hopf carrier is faithful for all three signs.
2. Freeze the sign convention ledger before results: committed Axis-3 placement sign, scaffold
   `b3`, panel `b3`, and any transform between them.
3. Decide neutral semantics before results: include `b0=0` as exact neutral-prediction rows, or
   exclude them as boundary rows with a separate boundary diagnostic.
4. Emit per-row sign vectors and canonical hashes from Julia, JAX, PyTorch, and the envelope; do not
   rely only on aggregate counts.
5. Replace aggregate-only SMT with row-local bindings for selected rows, including one holding row,
   one violating row, and one neutral/boundary row.
6. Pre-register the finite sample family and controls in the build card before generating results.
7. Add a stronger statistical design if the goal is to distinguish weak dependence from chance:
   more non-neutral rows, preregistered power, and an exact comparison to scrambled/sign-flip controls.
