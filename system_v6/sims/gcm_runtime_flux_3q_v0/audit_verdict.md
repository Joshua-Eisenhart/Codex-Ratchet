# Independent Audit Verdict - `gcm_runtime_flux_3q_v0`

audit_status: independent audit verdict
freshness_tier: TIER-2 results-available; no prior packet audit existed
audit_mode: read-only audit except this verdict file
standards_codex: `system_v6/receipts/audit_standards_codex_v1.md`
binding_lessons: G.2a builder/audit boundary; GNVW lesson `ba5a3ccd6`; 3Q freeze gate `dd8e96be7`; Hermes flux split

Bottom line: VERDICT = `BY_CONSTRUCTION_DOCTRINE_VOID` for the claimed flux-in-left / flux-out-right doctrine signature. The packet does compute nonzero `J_cut` and `J_ent` deltas on the stored 3Q state, but the decisive L/R opposition is not earned: `engine_L_flux_IN_left_3q` is constructed by copying `engine_R_flux_OUT_right_3q` through `reverse_current_row(...)`, swapping state hashes, and negating all current deltas. Therefore the exact equal magnitudes are construction symmetry, not an emergent runtime-flux result.

This is not a total packet rejection. Keep the narrow `scratch_diagnostic` facts: the stored-state R current is computed, the 3Q floor row is real enough for this ceiling, substrate positive/red checks pass, the product-control subset is fenced, and the validator's mechanical checks are green. Do not cite the packet as proving the doctrine signature, L/R independent runtime flux, engine admission, invariant flux, physics, axis admission, or formal admission.

## Decisive Finding

The L and R rows are not independent.

Source construction:

- `current_row(...)` computes metrics from an explicit `initial_rho` and `final_rho`, including state hashes and stepwise `J_cut` / `J_ent` values.
- `reverse_current_row(...)` then deep-copies the source row, swaps `initial_state_sha256` and `final_state_sha256`, negates `J_chi`, negates every `J_cut` delta, and negates every `J_ent` delta.
- `runtime_rows(...)` computes only R from `rho0 -> CNOT(0,1) rho0`; L is then `reverse_current_row(right, row_id="engine_L_flux_IN_left_3q", ...)`.
- The named time-reversal row is also `reverse_current_row(right, ...)`, this time with `time_reversal_of="engine_R_flux_OUT_right_3q"`.

Relevant source paths:

- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:511-538`
- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:663-696`

Fresh read-only recompute found:

| row | `J_cut` | `J_ent` | `J_chi` | initial | final | `time_reversal_of` |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `engine_R_flux_OUT_right_3q` | `+1.618198443941263` | `+0.725253655648275` | `+2` | `e2b5145ddb18...` | `08ab5fd7ea65...` | `null` |
| `engine_L_flux_IN_left_3q` | `-1.618198443941263` | `-0.725253655648275` | `-2` | `08ab5fd7ea65...` | `e2b5145ddb18...` | `null` |
| `time_reverse_of_R_flux_OUT_right_3q` | `-1.618198443941263` | `-0.725253655648275` | `-2` | `08ab5fd7ea65...` | `e2b5145ddb18...` | `engine_R_flux_OUT_right_3q` |

The recomputed sums are exactly zero at stored precision: `J_cut_L + J_cut_R = 0`, `J_ent_L + J_ent_R = 0`, and `J_ent_log_L + J_ent_log_R = 0`. L is value-identical to the time-reversal row and has the same state pair. The only difference is metadata: L hides `time_reversal_of` as `null`.

Stored evidence:

- left values and state hashes: `system_v6/sims/gcm_runtime_flux_3q_v0/results/gcm_runtime_flux_3q_v0_results.json:27211-27413`
- right values and state hashes: `system_v6/sims/gcm_runtime_flux_3q_v0/results/gcm_runtime_flux_3q_v0_results.json:27415-27616`
- time-reversal row state hashes and marker: `system_v6/sims/gcm_runtime_flux_3q_v0/results/gcm_runtime_flux_3q_v0_results.json:27809-27819`

Adjudication: the exact magnitude equality is suspicious because it is forced. This is the same standards species as a construction tautology / definitional circularity for the doctrine claim. The current signs are real arithmetic consequences of the code path, but they do not discriminate doctrine from label construction.

## Scrambled Control

The scrambled control does not rescue the doctrine claim.

Stored scramble row:

- `J_cut = +0.544415592904852`
- `J_ent = +0.182531241501633`
- `J_chi = 0`
- initial state remains R's initial `e2b5145ddb18...`
- final state is `e453d213f158...`

Source path:

- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:706-713`
- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:840-849`

The builder's scramble assertion is only `differs_from_committed_LR_currents`: it checks that the scramble magnitude differs from R's magnitude. It does not construct a scrambled L/R pair and does not ask whether L/R opposition breaks under scrambling. If the same `reverse_current_row(...)` operation were applied to the scrambled row, it would again produce exact opposite signs by construction.

Adjudication: scramble shows the current functional responds to a different unitary, but it does not kill the L/R opposition. It is not the real discriminator requested by the prompt.

## SMT Crossover

The z3/cvc5 rows are decorative for the runtime-flux doctrine.

Source:

- z3 asserts `l_chi == stored_left`, `r_chi == stored_right`, `three_q_cuts == 3`, `two_q_cuts == 1`, then also asserts `l_chi == -2`, `r_chi == 2`, and `r_chi == -l_chi`; solver returns `sat`.
- cvc5 asserts the same integer equalities and returns `sat`.

Relevant source paths:

- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:752-807`
- `system_v6/sims/gcm_runtime_flux_3q_v0/gcm_runtime_flux_3q_v0_common.py:929-950`

Stored results:

- `z3.verdict = "sat"`
- `cvc5.verdict = "sat"`

These are not UNSAT proof-flip rows, do not include an erasure or same-sign mutation, and do not reason over `J_cut` or `J_ent`. They assert the chirality seed signs and cut counts. They do not prove the runtime current opposition.

Contrast: the binding GNVW v1 packet named by the prompt has actual UNSAT mutation/proof-flip structure (`contract_negation_result="unsat"`, `same_sign_mutation_result="unsat"`). This packet does not reproduce that standard.

## What Survives

`J_chi`: survives only as a carried orientation seed, not as this packet's runtime-flux proof. The packet points to `gcm_qca_runner_2q_v0` (`git_last_commit=81a982ea1`) for `J_chi`, while the prompt's binding GNVW lesson is `gcm_qca_runner_2q_v1` at `ba5a3ccd6`. The v1 lesson says the opposite chirality index survives but bare mirror-conjugacy does not. This packet did not consume that stronger v1 source surface.

`J_cut` / `J_ent`: the R row is a real stored-state delta under the committed CNOT update. The L row is not independent and cannot be cited as emergent opposite flux.

3Q necessity: survives as a scratch floor row. Stored result reports `three_q_cut_count=3`, `two_q_cut_count=1`, nonzero negativity on all three anchor cuts, and positive CKW margins. This supports "3Q exposes structure unavailable to 2Q's single cut" at scratch ceiling; it does not prove the L/R doctrine.

Product fencing: survives. The selected product-control subset has zero current; the full product lift is explicitly not claimed zero and records `32` zero rows, `512` nonzero rows, and max product current `0.969798830420203`.

Substrate and coordinates: survive. Positive substrate check is green; lineage-free/carve-erasure negative is red; coordinates are `layer=24_runtime_flux`, `nesting=integrated-onto-the-carve`, `qubit_depth=3Q`; fences exclude engine admission, formal invariant, physics, axis admission, and geometric Hopf flux.

G.2a: passes after this audit write. The builder did not write `audit_verdict.md`; this file declares independent/read-only audit status in its header, satisfying the post-audit idempotency helper.

## Classification

| path | current label | corrected label | evidence | blocker/demotion reason | next admissible step |
| --- | --- | --- | --- | --- | --- |
| `system_v6/sims/gcm_runtime_flux_3q_v0` | `scratch_diagnostic`, `all_pass=true` | `scratch_diagnostic`, doctrine row `BY_CONSTRUCTION_DOCTRINE_VOID` | stored/recomputed values match; validator function errors `[]` | L is `reverse_current_row(R)`, not independent committed L generator | build independent L and R dynamics from separately pinned generators, then run a scramble that constructs both labels under the same perturbation |
| `J_cut` / `J_ent` L/R opposition | pass in builder result | void for doctrine | exact L/R magnitude equality and state-pair reversal | opposition forced by copy/swap/negate constructor | recompute L from a real L generator and require failure under label-only reversal |
| z3/cvc5 crossover | load-bearing in manifest | decorative for runtime flux | both return `sat` over asserted constants | no UNSAT flip, no erasure mutation, no `J_cut`/`J_ent` structure | add same-sign/erased-construction mutants and require z3+cvc5 polarity flip |
| scramble control | pass in builder result | insufficient discriminator | one scramble row differs in magnitude from R | no scrambled L/R pair; does not test whether opposition breaks | build scrambled R and scrambled L independently and adjudicate whether opposition survives |
| 3Q floor row | pass | keep at scratch ceiling | `3` cuts vs `1`, all three anchor negativities nonzero, CKW margins positive | floor row does not imply L/R doctrine | use as input for a repaired runtime-flux packet |

## Commands And Checks

Fresh checks were read-only except this file:

```text
git status --short system_v6/sims/gcm_runtime_flux_3q_v0
```

Result: target packet is currently untracked as a directory in this checkout before this audit file.

```text
git show --stat --oneline ba5a3ccd6 --
git show --stat --oneline dd8e96be7 --
```

Result: `ba5a3ccd6` is the GNVW v1 audit preserving opposite chirality index but dropping mirror-conjugacy; `dd8e96be7` is the 3Q freeze audit opening the runtime-flux input surface.

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
# imported gcm_runtime_flux_3q_v0_common.py; called build_packet(write=False);
# compared recomputed rows to stored JSON; checked L/R sums, state hashes,
# scramble row, crossover proof objects, product controls, and 3Q necessity row.
PY
```

Result: stored rows matched recomputation; `validation_errors_on_stored=[]`; no entrypoint validators or pytest were run because they can write result files or cache artifacts outside the allowed write scope.

## Citation Rule

Allowed citation:

`gcm_runtime_flux_3q_v0` is a scratch diagnostic that computes a nonzero R-side 3Q runtime/QIT current on the frozen 3Q cut surface and records controls/fences. It may be used as evidence that the selected 3Q state and CNOT update produce stored `J_cut` and `J_ent` deltas, and that the 3Q floor exposes three cut surfaces unavailable at 2Q.

Mandatory citation caveat:

The flux-in-left / flux-out-right doctrine signature is `BY_CONSTRUCTION_DOCTRINE_VOID`: L is generated by reversing R, so exact opposite `J_cut` and `J_ent` signs are automatic.

Forbidden citation:

Do not cite this packet as L/R independent runtime flux, emergent doctrine signature, proof that scramble breaks the L/R opposition, structural SMT proof, engine admission, admitted invariant, axis/bridge/physics evidence, geometric Hopf flux, or formal admission.
