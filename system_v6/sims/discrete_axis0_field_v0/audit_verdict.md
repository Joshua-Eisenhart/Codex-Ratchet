# Independent audit verdict - discrete_axis0_field_v0

Bottom line: VERDICT = GENUINE-WITH-CAVEATS at `scratch_diagnostic` strength.

`discrete_axis0_field_v0` is a real finite Axis-0 readout candidate packet. It computes an exact
rational scalar field on the rebuilt 33-cell Family A carrier, emits directed gradients over the
committed generator adjacency, derives per-cell allo/homeostatic polarity from signed outgoing
gradient flux, shows the readout is neither trivial nor fully frozen under one-step committed
updates, and keeps the binding ceiling at `axis_readout_candidate_only`.

It is not Axis-0 admission, not a bridge, not physics evidence, not a manifold promotion, and not
canonical. The packet directory is untracked in this checkout, so the repo status is `exists` plus
fresh local read-only rerun evidence, not committed/canonical process evidence.

## Verdict Details

Keep:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `claim_ceiling=axis_readout_candidate_only`
- public label: `GENUINE-WITH-CAVEATS`
- status ladder: `exists < passes local read-only validator/pytest rerun`; not committed here

Do not promote:

- no Axis-0 admission
- no axis-level closure
- no bridge/cut inference
- no physics interpretation
- no canonical-axis claim
- no multi-step dynamics claim

## Fresh Checks

All checks below were run read-only against repo files, except this audit file. Runner entrypoints
that rewrite result JSON were not used.

- Commit gate check:
  `git cat-file -t d6815079e` returned `commit`.
- Weld commit:
  `d6815079e` is the committed `manifold_super_sim_v2_weld` gate-opening commit with scratch
  ceiling and `promotion_allowed=false`.
- Packet local status:
  `git status --short -- system_v6/sims/discrete_axis0_field_v0` showed the packet directory as
  untracked before this audit file.
- Read-only packet validator:
  importing `validate_discrete_axis0_field_v0.validate_payload(...)` returned
  `ok=true`, `error_count=0`.
- Generic three-engine validator:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json`
  returned `ok=true`.
- Pytest:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/discrete_axis0_field_v0/tests`
  returned `5 passed`.
- Independent object rebuild through packet functions:
  `common.build_axis0_object()` returned `all_pass=true`; rebuilt `state_object_id` matched the
  envelope; rebuilt gradient signature matched the envelope.

## Carrier And Field

The carrier is rebuilt rather than copied as a raw persisted transition graph:

- `state_count=33`
- `edge_count=198`
- generator names: `Se_Funnel_L`, `Ni_Pit_L`, `Ni_Source_R`, `Ne_Spiral_R`, `D_z`, `R_x`
- `raw_transition_graph_persisted_here=false`
- carrier transition graph hash:
  `bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`
- source rows hash:
  `a8b7bda7b52c286a17314e0737cc2bac497e69e52767b914976c4028d1631072`
- Family A state object:
  `manifold_super_sim_v0:271b13f6f2128dda74723ab9dd780a1c6c72940d9e1c8adee549dcbb8c4125c4`
- weld state object:
  `manifold_super_sim_v2_weld:c2ab14953c1e4e07964bf41d52f53bfa8209f91835e57c81ea91b6fc684c0f76`
- packet state object:
  `discrete_axis0_field_v0:eb8bcca90a805de53692bb9462c1e47e7d83d4888f0d69acd87400d09a734d8f`

The scalar field is exact rational:

```text
phi(v) =
(2*x_scaled - 5*y_scaled + 7*z_scaled + 3*x_scaled*y_scaled
 - z_scaled^2 + 4*r2_scaled + 11*conditioned_shell_member) / 97
```

Manual recomputation for three cells matched the packet:

| cell | coord_scaled | phi | net outgoing gradient flux | polarity |
|---:|---|---:|---:|---|
| 0 | `[-2, 0, 0]` | `12/97` | `-38/97` | `axis0_minus_homeostatic_response` |
| 7 | `[-1, 1, -1]` | `-6/97` | `29/97` | `axis0_plus_allo_response` |
| 16 | `[0, 0, 0]` | `0` | `0` | `neutral_no_polarity` |

This is not a definitional polarity assignment: polarity is computed from signed outgoing
generator-gradient flux, not copied from `kappa`, nesting, placement, order, or labels.

## Gradients And Polarity

Gradient summary:

- `edge_count=198`
- `positive_gradient_edges=39`
- `negative_gradient_edges=51`
- `zero_gradient_edges=108`
- `nonzero_gradient_edges=90`
- signed gradient sum: `-184/97`
- gradient signature:
  `5035880ae9c17a768b0568b8cbb0f22800d9ee7a5cc454ea529c2df3ef10d391`

Polarity counts:

- `axis0_minus_homeostatic_response=17`
- `axis0_plus_allo_response=15`
- `neutral_no_polarity=1`

The Axis-0 language is honest: the packet uses response polarity words
`allo/homeostatic/neutral`, while Axis-3-style placement and Axis-6-style order appear only as
separate discriminator keys.

## Independence Discriminators

The packet's recorded majority-predictor failures are real:

- `kappa` majority accuracy: `0.5151515151515151`
- nesting majority accuracy: `0.5151515151515151`
- `kappa x nesting` frozen-factor majority accuracy: `0.5454545454545454`
- Axis-3-style placement majority accuracy: `0.5454545454545454`
- Axis-6-style order majority accuracy: `0.5454545454545454`

Fresh combined predictor audit:

- `kappa + nesting + axis6_order_key`: majority accuracy `0.6363636363636364`
- `kappa + axis3_placement_key + axis6_order_key`: majority accuracy `0.6363636363636364`
- `kappa + nesting + axis3_placement_key + axis6_order_key`: majority accuracy
  `0.6363636363636364`

So the readout is not recoverable from the tested placement/order/coloring/nesting rows in this
finite packet. The discriminator can fail: a sanity patch forcing `polarity = kappa` gives
`kappa_majority_accuracy=1.0`, so the threshold test would detect a recoverable realization.

## Stability Under Committed Updates

The packet computes one-step polarity survival over the committed generator adjacency:

- `edge_count=198`
- `stable_edge_count=163`
- `changed_edge_count=35`
- `stable_fraction=0.8232323232323232`
- `all_changed_every_step=false`
- `all_stable_every_step=false`

This is nonvacuous. The readout is not changing under every update, and it is not frozen by
construction. The earned scope is one-step generator-edge stability, not multi-step orbit
stability.

## Controls And Falsifiers

Fresh recompute of representative controls:

- constant field: `neutral_no_polarity=33`, `nonzero_gradient_edges=0`
- shuffled adjacency: preserves edge count but changes gradient signature from
  `5035880ae9c17a768b0568b8cbb0f22800d9ee7a5cc454ea529c2df3ef10d391`
  to `18459c0adaf0da985c1c24ebd1d2e8ea96be5a8952c8e007d1e9087f1ee0f6e8`

Packet controls marked fired:

- `constant_field`
- `shuffled_adjacency`
- `reversed_orientation`
- `erased_coloring`
- `erased_nesting`
- `label_shuffle`
- `row_count_only_ladder`
- `frozen_factor_projection`
- `three_polarities_independence_control`

Falsifier branches are reachable in the packet's code path. They are not decorative prose rows.

## SMT And Engine Scope

SMT rows are computed-value bindings:

- z3 binds `stable=163`, `changed=35`, `edge_count=198`, `nonzero=90`,
  `axis3_not_recoverable=1`, `axis6_not_recoverable=1`; identity verdict `unsat`;
  erased flip verdict `sat`.
- cvc5 binds the same computed values independently; identity verdict `unsat`;
  erased flip verdict `sat`.
- Julia Z3 lane also reports identity `unsat` and erased flip `sat`.

The SMT rows are real aggregate gates, not precomputed boolean assertions. Their scope is still
aggregate: per-cell `phi`, per-edge gradients, and per-cell polarity are checked by exact table
recomputation and validators, not proved by SMT.

Engine scope:

- Julia ran with `Graphs` and `Z3`, `reads_peer_result=false`, `all_pass=true`.
- JAX/Python ran with `networkx`, `sympy`, `z3`, `cvc5`, `reads_peer_result=false`,
  `all_pass=true`.
- PyTorch ran with `torch.func`, `torch_geometric`, `sympy`, `z3`, `cvc5`,
  `reads_peer_result=false`, `all_pass=true`.
- stable-edge counts agree exactly across engines: `julia=163`, `jax=163`, `pytorch=163`.
- generic validator strict source-backed/tool-intent mode passed.

## Named Caveats

G1_WORKTREE_NOT_COMMITTED:
The packet is untracked in this checkout. This audit can certify local evidence, not committed
repo truth. Future citation must say `working-tree packet` unless a later commit lands the packet
and this verdict.

G2_FAMILY_A_FILE_LAST_COMMIT_DRIFT:
The packet pins the Family A commit hint `42542f120`, but the current Family A envelope file's
last Git touch is `2ad726598` from a later tool-honesty sweep. The state object is unchanged
across `42542f120`, `2ad726598`, and `HEAD`, so this is not a carrier mismatch. Citation should
name the Family A state object and the rebuilt carrier hash, not rely only on file-last-commit
wording.

G3_ENGINE_INDEPENDENCE_SCOPE:
The JAX and PyTorch lanes share the packet common builder for the object and differ in source
backing/probe tools; Julia has a separate implementation and matches the counts. This is enough
for the declared three-engine exact readout candidate mode, but not proof of fully independent
algorithmic derivation in all lanes.

G4_AGGREGATE_SMT_SCOPE:
The z3/cvc5 rows bind aggregate computed counts and erased flips. They gate nonvacuity,
stability, and independence booleans; they do not by themselves prove the per-cell gradient
formula or all row-local polarity derivations.

G5_STABILITY_IS_ONE_STEP:
The stability row is over committed one-step generator edges. It is nonvacuous and passes the
card's immediate readout-survival check, but it is not a multi-step orbit, basin-residence, or
long-time invariant claim.

G6_COMBINED_PREDICTOR_NOT_PERSISTED:
The packet persists separate kappa, nesting, frozen-factor, Axis-3, and Axis-6 discriminators.
This audit additionally computed the combined predictor and found it still fails to recover the
polarity. Axis0 v1 should persist the combined predictor row and the forced-recoverable negative
control in the result envelope.

## Future Citation Rule

First-axis citation template:

```text
discrete_axis0_field_v0 (independent audit: GENUINE-WITH-CAVEATS, scratch_diagnostic,
promotion_allowed=false, formal_admission_allowed=false,
claim_ceiling=axis_readout_candidate_only) computes one exact rational Axis-0
readout candidate A0: M(C) -> V0 on the rebuilt Family A 33-cell carrier
state_object_id=manifold_super_sim_v0:271b13f6f2128dda74723ab9dd780a1c6c72940d9e1c8adee549dcbb8c4125c4,
under the d6815079e weld-opened scratch gate. It earns:
field phi over Q with denominator 97; directed-gradient signature
5035880ae9c17a768b0568b8cbb0f22800d9ee7a5cc454ea529c2df3ef10d391;
polarity counts minus/homeostatic=17, plus/allo=15, neutral=1;
one-step stability 163 stable / 35 changed over 198 generator edges;
constant-field, shuffled-adjacency, reversed-orientation, erased-coloring,
erased-nesting, label-shuffle, row-count-only, and frozen-factor controls;
z3/cvc5 aggregate computed-value SMT gates with SAT erased flips.
Do not cite it as Axis-0 admission, bridge evidence, physics evidence,
canonical Axis-0, manifold promotion, full dynamics, or formal proof.
Carry caveats G1-G6 unless explicitly closed by a later committed v1/audit.
```

Short citation:

```text
`discrete_axis0_field_v0` is a genuine scratch Axis-0 readout candidate only:
exact finite field + directed-gradient polarity on the rebuilt Family A 33-cell
carrier, with nonrecoverability/stability/controls, under
`claim_ceiling=axis_readout_candidate_only`.
```

## Axis0 v1 Needs

1. Commit or otherwise snapshot the v0 packet before using it as a parent, so citations do not
   depend on an untracked working tree.
2. Persist the combined `kappa + nesting + placement + order` best-predictor discriminator and a
   forced-recoverable control where polarity is made equal to `kappa` or one order key.
3. Add multi-step orbit stability: generator sequences, terminal-class residence, leakage edges,
   and survival/flip rates over bounded paths.
4. Strengthen SMT from aggregate counts to row-local bindings for selected cells/edges, including
   a wrong-gradient or wrong-polarity flip that must be SAT or fail as expected.
5. Make the field/probe pre-registration explicit for v1: freeze the formula and probe family in
   the build card before any engine result is generated.
6. Add a temp-copy full regeneration audit after commit, because this read-only audit deliberately
   avoided runner entrypoints that rewrite result JSON.
7. Keep the same ceiling unless a separate gate opens: v1 remains a readout-candidate packet, not
   an axis admission packet.

## Sweep 3 Correction Annotation

G6 extension `SURROGATE_LEVEL_NONRECOVERABILITY_ONLY`:
The `conditioned_shell_member` input to `phi` is absent from every tested surrogate. A finer `(r2 x shell)` majority predictor reaches `69.7%`, above the recorded Axis-3-style and combined-surrogate predictors but still below recovery. Independence therefore holds at surrogate level, not as full nonrecoverability from every available field component. Future short citation wording should say `surrogate-level nonrecoverability/stability/controls`, not unqualified `nonrecoverability`.

G7 `PHI_FORMULA_BUILDER_CHOSEN_NOT_PRE_REGISTERED`:
The scalar formula coefficients in `phi=(2x-5y+7z+3xy-z^2+4r2+11shell)/97` were builder-chosen, not pre-registered in the build card before results. The contender registry later labels this committed formula as `A0.CP.0_committed`, which makes it one legitimate candidate among several, not THE Axis-0 readout. A different admissible polynomial on the same carrier could flip some or all polarities. Axis0 v1 must freeze `phi` and the probe family in the card before any engine result is generated.
