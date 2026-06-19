# Independent audit verdict - ring_checkerboard_qca_v2

Bottom line: **REJECT the claim that doctrine expectation 2 is earned as an independent L/R flux-engine alignment.** The packet does earn a useful scratch-level open-chain crossing-rank extraction fixture, but the decisive L/R engine rows are numerically the same operators as the calibration left/right shifts. That is too close to the v1 sin's shape: not metadata readback this time, but still a shift-calibration relabeling rather than distinct engine operators carrying the flux assignment.

Accepted ceiling: `scratch_diagnostic` mechanics only. `promotion_allowed=false`; `formal_admission_allowed=false`.

Citable sentence: `ring_checkerboard_qca_v2` independently recomputes the open-chain crossing-rank calibration indices (+1/-1/0) from realized unitary operators and preserves the finite-ring triviality boundary, but its L/R flux-engine rows are the calibration shifts under flux labels rather than distinct engine operators, so doctrine expectation 2 is not earned beyond a scratch calibration fixture.

## Audit Scope

This audit was read-only except for this file. I did not run packet-local builders that rewrite result JSON. I used import-time recomputation, read-only validators, grep, and pytest.

Authority surfaces checked:

- `AGENTS.md`, `CODEX.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`, `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`
- CA doctrine receipt `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`
- Panel 8 receipt `system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md`
- Standard-math note `~/wiki/codex-ratchet-research/standard-math/gnvw-index-1d-qca.md`
- Packet sources/results under `system_v6/sims/ring_checkerboard_qca_v2/`

Route truth: Wizard v4.2 packet was loaded, but no Codex-native `spawn_agent` tool was exposed in this runtime, so this was a **partial local tool audit**, not a Full Max Assembly topology.

## Fresh Checks

Commands run:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ring_checkerboard_qca_v2 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ring_checkerboard_qca_v2/tests`
  - Result: `6 passed in 40.39s`
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ring_checkerboard_qca_v2/results/ring_checkerboard_qca_v2_envelope_results.json`
  - Result: `ok: true`
- Custom scratch recompute from `ring_checkerboard_qca_v2_common.build_rules()` and `crossing_rank_data()`
  - Result: all packet rank/index rows matched recomputed operator data.
- Grep for live v1-style flow fields:
  - `right_wires`, `left_wires`, `wire_flow`, and true metadata-flow fields were not present as claim-bearing fields. Matches were guard text, negative strings, and result prose.

Existing builder validator file read:

- `system_v6/sims/ring_checkerboard_qca_v2/results/ring_checkerboard_qca_v2_validator_results.json`
  - `ok: true`, `phase: builder`.

I did not rerun `validate_ring_checkerboard_qca_v2.py` because it writes `ring_checkerboard_qca_v2_validator_results.json`, and the user allowed writing only this verdict file.

## Adjudication

### 1. Extraction Reality

Verdict: **PASS.**

Fresh recomputation from realized unitary operators gave:

| row | right rank | left rank | signed index | ratio |
|---|---:|---:|---:|---|
| `calibration_right_shift` | 4 | 1 | +1 | `2/1` |
| `calibration_left_shift` | 1 | 4 | -1 | `1/2` |
| `calibration_nonshifting_onsite` | 1 | 1 | 0 | `1/1` |
| `paired_block_index0` | 4 | 4 | 0 | `1/1` |

The packet declares its convention: support-factor vector-space ranks are converted through the base `d^2` channel exponent, so Panel 8's warning applies: check the signed index, not universalize the intermediate dimension bookkeeping. Under that convention, the extraction path is real and no flow metadata is on the claim path.

### 2. L/R Engine Rules

Verdict: **FAIL for independent flux-engine alignment.**

The rows recompute as advertised:

| row | right rank | left rank | signed index | ratio |
|---|---:|---:|---:|---|
| `engine_L_flux_IN_left_O1` | 1 | 4 | -1 | `1/2` |
| `engine_R_flux_OUT_right_O1` | 4 | 1 | +1 | `2/1` |

But the hard audit question was whether these are different operators than the calibration shifts. They are not.

Fresh matrix comparisons:

- `engine_R_flux_OUT_right_O1` vs `calibration_right_shift`: max abs diff `0.0`
- `engine_L_flux_IN_left_O1` vs `calibration_left_shift`: max abs diff `0.0`

The phase dressing cancels along the shifted wire. Therefore the engine rows prove that assigning the R label to the right-shift calibration and the L label to the left-shift calibration gives opposite signs. They do **not** prove that distinct L/R engine local unitaries realize the O1 flux assignment.

### 3. Gauge Check

Verdict: **WEAK PASS for recomputation; not a strong gauge stress test.**

The packet inserts a concrete Hadamard at input label `2` and output label `3`, then recomputes ranks. The recomputed row remains:

- `gauge_engine_R_inserted_H`: right rank `4`, left rank `1`, signed index `+1`, ratio `2/1`

However, the actual matrix comparison found:

- `gauge_engine_R_inserted_H` vs `engine_R_flux_OUT_right_O1`: max abs diff `2.220446049250313e-16`

So the inserted unitary is real in code, and the ranks are recomputed, but the chosen insertion cancels to numerical identity for this shift. It is acceptable as a basis-covariance sanity row; it is not strong evidence that a nontrivial gauge perturbation was survived.

### 4. Falsifier And Index-0 Controls

Verdict: **PASS.**

Index-0 controls:

- `engine_L_index0_control`: `0`
- `engine_R_index0_control`: `0`
- `paired_block_index0`: `0`
- `lr_distinction_detected`: `false`

Falsifier:

- `falsifier_R_engine_forced_left_unitary`: signed index `-1`
- `opposite_signs_after_mutation`: `false`
- z3/cvc5 flip verdict: `sat`

This is a real reachable mutation, but because the base engine rows are themselves calibration shifts, it supports the extraction fixture more than it supports independent engine doctrine.

### 5. Ring Closure And Classical Floor

Verdict: **PASS.**

All six ring closure rows recompute to signed index `0`, and each labels the automorphism-class index as `0`. The packet does not claim a nonzero finite-ring automorphism-class GNVW index.

The dephased classical-floor continuity row reproduces the corrected v0 floor:

- alternating transient SCC count: `352`
- paired transient SCC count: `128`
- ratio: `2.75`
- `phase_structure_reproduced`: `true`

The packet correctly keeps this as dephased continuity, not QCA index evidence.

### 6. Tools, Schema, Validators, Boundary

Verdict: **PASS with caveats.**

Passes:

- Three-engine generic validator is green with `--require-pytorch --strict-source-backed --require-tool-intent`.
- Packet tests pass.
- Existing packet validator result is green.
- `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, `TOOL_INTENT_MATRIX`, classification, promotion boundary, and finite-ring boundary are present.
- z3 and cvc5 bind computed rank/index rows and include the real-unitary flip.

Caveats:

- The whole packet is currently untracked in git.
- The Julia `QuantumClifford` row is a weak package witness (`S"X"` / `S"Z"` distinctness) rather than load-bearing for the crossing-rank computation. The main claim still has load-bearing support from the realized matrices, QuantumOptics matrix units, SMT binding, and cross-backend agreement.
- The post-audit packet validator was not rerun because it would rewrite result JSON, outside the user's write boundary.
- No Full Wizard Max Assembly subagent topology ran in this runtime.

## Final Verdict

`ring_checkerboard_qca_v2` is **GENUINE-WITH-CAVEATS as a scratch open-chain crossing-rank extraction fixture**.

It is **REJECTED as an earning of doctrine expectation 2** if expectation 2 means the L/R engines themselves, as distinct local unitaries realizing the flux assignment, now align with index/flux. The extracted signs are real, the controls are real, and the ring-boundary honesty is good; the missing piece is operator independence from the calibrating shifts.

Next admissible repair: replace the L/R engine rows with genuinely distinct local unitaries or brickwork circuits that are not matrix-identical to the shift calibrations, then rerun extraction, nontrivial gauge insertion, index-0 controls, falsifier, and three-engine validator.
