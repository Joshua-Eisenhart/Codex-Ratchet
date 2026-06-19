# Independent audit verdict - discrete_axis3_placement_v0

Bottom line: VERDICT = GENUINE-WITH-CAVEATS at `scratch_diagnostic` strength.

`discrete_axis3_placement_v0` is a real finite Axis-3 placement readout candidate packet. It
computes the source-pinned Hopf predicates for `gamma_in` and `gamma_out`, matches the blind panel
q1 expectations, emits placement signs over a bounded Family B Hopf sample, includes live controls
and solver erased flips, and keeps the ceiling at `axis_readout_candidate_only`.

It is not Axis-3 admission, not a canonical axis, not bridge/cut evidence, not physics evidence,
not a manifold promotion, and not a proof of full cross-carrier independence. The packet directory
is untracked in this checkout, so the public repo status is `exists` plus fresh local read-only
validator/pytest evidence, not committed/canonical process evidence.

## Verdict Details

Keep:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `claim_ceiling=axis_readout_candidate_only`
- public label: `GENUINE-WITH-CAVEATS`
- status ladder: `exists < passes local read-only validator/pytest rerun`; not committed here

Do not promote:

- no Axis-3 admission
- no axis-level closure
- no bridge/cut inference
- no physics interpretation
- no canonical-axis claim
- no full multi-step dynamics claim
- no full cross-carrier Axis0/Axis3 independence claim

Wizard/process route truth: this audit was local/controller-only. I did not spawn Codex subagents
because the available spawn tool is restricted to turns where the user explicitly asks for
delegation. I also did not run packet entrypoints that rewrite result JSON, because this task was
read-only except for this audit file.

## Fresh Checks

All checks below were run read-only against repo files, except this audit file. Packet validators
were run before this file was written because the builder-boundary validator checks that the
builder did not create `audit_verdict.md`.

- Worktree status:
  `git status --short` showed `system_v6/sims/discrete_axis3_placement_v0/` as untracked.
- Authority docs read:
  `AGENTS.md`, `CODEX.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`,
  `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`, and
  `system_v5/ops/SIM_FULL_WIZARD_PARALLEL_RUNBOOK.md`.
- Axis authority read:
  `system_v6/receipts/axis_work_order_20260612.md`,
  `system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md`,
  `system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md`, and the Axis0 audit
  template/corrections in `system_v6/sims/discrete_axis0_field_v0/audit_verdict.md`.
- Fresh predicate recompute:
  four symbolic checks using the Makefile interpreter
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- Packet validator, read-only function call:
  `validate_discrete_axis3_placement_v0.validate_payload(...)` returned
  `ok=true`, `error_count=0`.
- Generic three-engine validator:
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis3_placement_v0/results/discrete_axis3_placement_v0_envelope_results.json`
  returned `ok=true`.
- Pytest without cache/bytecode writes:
  `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B -m pytest -q -p no:cacheprovider system_v6/sims/discrete_axis3_placement_v0/tests`
  returned `6 passed`.

## Panel-Match Adjudication

Panel q1 pre-registered two predicate expectations:

- `gamma_in`: base-stationary / reduced density stationary.
- `gamma_out`: horizontal, with `A(dot gamma)=0` exactly by
  `-cos(2 eta0)+cos(2 eta0)`.

Fresh recomputation for two loops each matched the panel.

| sample | family | eta | predicate result | panel match |
|---|---|---:|---|---|
| `in_1` | `gamma_in` | `pi/8` | `rho_delta=0`; density stationary | yes |
| `in_2` | `gamma_in` | `pi/4` | `rho_delta=0`; density stationary | yes |
| `out_1` | `gamma_out` | `pi/8` | density changes; `A(dot gamma)=0` | yes |
| `out_2` | `gamma_out` | `3*pi/8` | density changes; `A(dot gamma)=0` | yes |

The packet's stored first rows agree with this recompute:

- `gamma_in`: `density_stationary=true`, `max_density_distance_from_start=0.0`,
  placement `axis3_minus_fiber_placed_gamma_in`.
- `gamma_out`: `density_traversing=true`,
  `horizontal_condition_A_dot_gamma_zero=true`, `max_abs_connection_eval=0.0`,
  placement `axis3_plus_base_placed_gamma_out`.

Finding: no panel divergence. The classification predicates match the blind panel.

## Loop-Family Adjudication

The source formulas are legitimate:

- `gamma_in`: `phi=phi0+u`, `chi=chi0`, `eta=eta0`.
- `gamma_out`: `phi=phi0-cos(2eta)u`, `chi=chi0+u`, `eta=eta0`.

The finite 48-row loop family is:

```text
sheets {L,R}
x eta shells {pi/8, pi/4, 3*pi/8}
x phi_index {0,2}
x chi_index {0,1}
x loop family {gamma_in,gamma_out}
= 48 nondegenerate rows
```

The packet records `pin_block.pin_policy` and `pin_block_sha256`, and the validator requires 48
rows with 24 fiber and 24 base placements. This is a real code-level pin, not a result-file-only
story.

Hard caveat G1 `LOOP_FAMILY_CODE_PINNED_NOT_EXTERNALLY_PRE_REGISTERED`:
The build card says "Pin loop families before classification" and names `gamma_in/gamma_out`, but
it does not pre-register the exact 48-anchor sample rule before the builder code. The blind panel
pre-registers the two predicates, not the 48-row finite sampling family. This is the Axis0 G7
lesson at one level up: the formulas are source-pinned, but the finite sample family is
builder-chosen/code-pinned.

Could a legitimate alternative family change the proportions? Yes, at least at the reporting
level. A symmetric nondegenerate family with both `gamma_in` and `gamma_out` per anchor will keep
the 24/24-style split, but including pole/degenerate anchors in the main table, sampling different
eta shells, or moving Type1/2, chirality, or flux overlays into the primary family could change
the placement proportions or add neutral rows. Therefore cite the proportions as `under the
packet's pinned 48-row family`, not as a source-global Axis-3 distribution.

## Carrier And Independence

The Axis-3 carrier is Family B Hopf:

- carrier name: `Family_B_Hopf_torus_chart_carrier`
- Family B state object:
  `manifold_family_b_integrated_v0:ce89ce555d94cb523613db78bbfe382dc4746cbc039c8773e9aa769e3eb090f5`
- committed parent support size: `384`
- packet loop anchor rows used: `24`

The committed Axis0 packet lives on a different carrier, the Family A 33-cell carrier. Axis3
realizes the cross-carrier comparison through a declared surrogate projection:

```text
axis0_cell_id = (17*sheet_index + 5*eta_slot + 3*phi_index + chi_index) mod 33
```

Stored independence rows:

- `placement_not_recoverable_from_axis0_response=true`
- `axis0_response_not_recoverable_from_placement=true`
- `axis0_to_axis3_majority_accuracy=0.5`
- `axis3_to_axis0_majority_accuracy=0.6666666666666666`
- same Axis0 response / different placement witness exists
- same placement / different Axis0 response witness exists
- frozen-factor projection majority accuracy `0.5`

Hard caveat G2 `SURROGATE_PROJECTION_INDEPENDENCE_ONLY`:
The independence rows are not vacuous, because the surrogate projection is declared and witnesses
exist. But this is not a proved shared object or carrier isomorphism between Family B Hopf and the
Axis0 33-cell carrier. The earned claim is projection/surrogate-level bidirectional
nonrecoverability on these rows, not full cross-carrier independence.

## Overlays

The overlay rows exist and are honest:

| overlay | status | audit result |
|---|---|---|
| `Type1_Type2_inversion` | `staged_not_run` | honest alternative, not collapsed |
| `L_R_chirality` | `staged_not_run` | honest alternative, not collapsed |
| `flux_in_out` | `staged_not_run` | honest alternative, not collapsed |

These rows are correctly blocked from promotion. The packet does not claim that Type1/2,
chirality, or flux are resolved by the primary placement readout.

## Stability

The packet's stability scope is one-step loop-time density movement:

- edge count: `384`
- stable density-step edges: `192`
- changed density-step edges: `192`
- stable fraction: `0.5`
- `all_stable_every_step=false`
- `all_changed_every_step=false`
- `placement_label_survives_loop_steps=true`

This satisfies the axis0-style "neither trivial nor frozen" standard at the declared one-step
scope. It does not prove multi-step orbit stability, basin residence, terminal-class structure, or
long-time invariance.

## Controls And SMT

Controls fired:

- placement-degenerate control: `fired=true`, `neutral_count=8`
- shuffled-connection control: `fired=true`, `changed_count=24/24 gamma_out rows`
- falsifier branch: `wrong_sign_base_phi=phi0+cos(2eta)u` fails base placement as expected
- frozen-factor projection: `fired=true`, majority accuracy `0.5`
- three-polarities independence control: `fired=true`

SMT rows:

- z3 binds computed aggregate values and returns identity `unsat`, erased flip `sat`.
- cvc5 binds the same aggregate values independently and returns identity `unsat`, erased flip
  `sat`.
- Bound values include `fiber_count=24`, `base_count=24`, `stable_edge_count=192`,
  `changed_edge_count=192`, `neutral_control_count=8`,
  `shuffled_connection_changed_count=24`, and both independence booleans as `1`.

Caveat G3 `AGGREGATE_SMT_SCOPE`:
The solver rows are real computed-value bindings with erased flips, but they are aggregate gates.
They do not prove every row-local density matrix, path, or independence witness in SMT.

## Backend Scope

The envelope records Julia, JAX, and PyTorch lanes as run and `reads_peer_result=false`, and their
main counts match exactly:

| engine | fiber | base | stable | changed |
|---|---:|---:|---:|---:|
| Julia | 24 | 24 | 192 | 192 |
| JAX | 24 | 24 | 192 | 192 |
| PyTorch | 24 | 24 | 192 | 192 |

Caveat G4 `BACKEND_INDEPENDENCE_SCOPE`:
JAX and PyTorch consume the Python common builder for the full placement and independence object.
Julia independently checks the Cartesian loop counts, graph count, and Z3 aggregate identity, but
it does not rebuild the full row-local Axis0 projection or placement table independently. This is
enough for a candidate packet with the stated ceiling, not enough for a full independent
cross-backend derivation claim.

## Circularity Audit

1. Predicate/panel circularity: PASS. The two lead predicates were blind-panel pre-registered and
fresh recomputation matches them.
2. Loop-family choice circularity: CAVEAT. The formulas are source-pinned, but the 48-row finite
family is code-pinned, not build-card/panel pre-registered.
3. Cross-carrier independence circularity: CAVEAT. The Axis0 comparison uses a declared projection
surrogate, not a proved shared carrier.
4. Control/SMT/backend circularity: PASS WITH CAVEATS. Controls fire and solver flips are real,
but SMT is aggregate and backend independence is scoped.

## Vocabulary And Boundary

The three-polarities vocabulary is clean:

- Axis-3 uses placement words: `fiber/base/degenerate`, `gamma_in/gamma_out`.
- Axis-0 appears as response-polarity data only inside independence rows.
- Axis-6 appears only as a prohibited replacement/conflation boundary.

The packet does not use `allo/homeostatic` as Axis-3 classification and does not use
operator/terrain precedence as Axis-3 classification.

## Named Caveats

G1 `LOOP_FAMILY_CODE_PINNED_NOT_EXTERNALLY_PRE_REGISTERED`:
The exact 48-row family is selected in packet code, not frozen in the build card or blind panel.
Future work should pre-register the finite family in the card before any engine result exists.

G2 `SURROGATE_PROJECTION_INDEPENDENCE_ONLY`:
Axis0-vs-Axis3 nonrecoverability is real only for the declared projection from Hopf anchors to
Axis0 33-cell rows. Do not cite it as full cross-carrier independence.

G3 `AGGREGATE_SMT_SCOPE`:
SMT binds aggregate computed counts and erased flips. It does not prove row-local path/density
semantics.

G4 `BACKEND_INDEPENDENCE_SCOPE`:
Three engines agree on counts, but JAX/PyTorch share the common builder and Julia does not rebuild
the full row-local object.

G5 `STABILITY_IS_ONE_STEP`:
Nontrivial/nonfrozen stability is one-step loop-time density movement, not basin or long-time
stability.

G6 `WORKTREE_NOT_COMMITTED`:
The packet directory is untracked in this checkout. Future citation must cite a commit hash after
commit, or say `working-tree packet`.

G7 `VALIDATOR_BOUNDARY_AFTER_AUDIT_FILE`:
The packet-local builder-boundary validator was run before this file existed. After this audit
file is present, that exact validator's "builder did not create audit_verdict.md" check is no
longer a post-audit invariant unless run against the pre-audit state or interpreted as an envelope
build-time gate.

## Future Citation Rule

Use this full citation form:

```text
discrete_axis3_placement_v0 (independent audit: GENUINE-WITH-CAVEATS,
scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false,
claim_ceiling=axis_readout_candidate_only) computes a finite Axis-3 placement
readout candidate on the Family B Hopf carrier
state_object_id=manifold_family_b_integrated_v0:ce89ce555d94cb523613db78bbfe382dc4746cbc039c8773e9aa769e3eb090f5.
It matches the blind panel q1 predicates: gamma_in reduced density stationary;
gamma_out density traversing with exact A(dot gamma)=0. Under its code-pinned
48-row nondegenerate family it reports 24 fiber/gamma_in and 24 base/gamma_out
rows, one-step stability 192 stable / 192 changed over 384 loop-time edges,
placement-degenerate, shuffled-connection, wrong-sign, frozen-factor, and
three-polarities controls, and z3/cvc5 aggregate computed-value gates with SAT
erased flips. Carry caveats: loop family code-pinned not externally
pre-registered; Axis0 independence is surrogate-projection only; SMT aggregate;
backend independence scoped; stability one-step only; worktree/uncommitted until
later commit.
```

Short citation:

```text
`discrete_axis3_placement_v0` is a genuine scratch Axis-3 placement readout
candidate only: blind-panel-matching gamma_in/gamma_out predicates on a bounded
Family B Hopf sample, with controls/SMT/stability, under
`claim_ceiling=axis_readout_candidate_only`.
```

Do not cite it as Axis-3 admission, canonical Axis-3, bridge evidence, physics evidence, full
cross-carrier independence, full dynamics, or formal proof. Carry G1-G7 unless explicitly closed
by a later committed v1/audit.
