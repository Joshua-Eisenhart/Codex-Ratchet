# Independent audit verdict - ring_checkerboard_qca_v3

Bottom line: **GENUINE-WITH-CAVEATS at `scratch_diagnostic` ceiling.** v3 cures the v2 shift-relabel defect: the L/R engine rows are distinct realized brickwork unitaries, not calibration shifts wearing flux labels. The extracted open-chain indices are `L=-1` and `R=+1`, the paired/index-0 controls stay balanced at `0`, the self-rejection gate fires on a relabeled shift, and the gauge row is a real operator perturbation this time. Expectation 2 is earned only for this bounded open-chain local-unitary fixture, not as finite-ring automorphism-class QCA admission.

Future citation rule: cite this packet as **working-tree `ring_checkerboard_qca_v3`, independent audit verdict: expectation 2 earned at scratch open-chain fixture ceiling; not canonical/admitted; finite-ring nonzero GNVW automorphism-class index not claimed.** Do not cite it as a full QCA admission, finite-ring nontrivial index, all-cells binary dynamics, v4 coupling-law evidence, or physics/owner-source proof.

## Scope

Read-only audit except for this file. No `git add`, no commit, no result JSON rewrite.

Authority surfaces checked:

- `AGENTS.md`, `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v5/ops/SIM_FULL_WIZARD_PARALLEL_RUNBOOK.md`
- `system_v6/receipts/owner_doctrine_cellular_automata_ring_checkerboard_20260611.md`
- `system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md`
- `~/wiki/codex-ratchet-research/standard-math/gnvw-index-1d-qca.md`
- v2/v3 packet source and result files under `system_v6/sims/ring_checkerboard_qca_v2/` and `system_v6/sims/ring_checkerboard_qca_v3/`

Route truth: Wizard v4.2 packet and compact MMM were loaded, but this runtime did not expose Codex-native `spawn_agent` receipts. This is a partial local tool audit, not a Full Max Assembly parent/child topology.

## Fresh Checks

Commands run:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/codex_runtime_env_doctor.py --json`
  - Result: `summary.ok=true`; install state stable; expected blocked/avoid packages remain absent or broken as documented.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ring_checkerboard_qca_v3/results/ring_checkerboard_qca_v3_envelope_results.json`
  - Result: `ok: true`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=system_v6/sims/ring_checkerboard_qca_v3 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/ring_checkerboard_qca_v3/tests`
  - Result: `6 passed in 26.09s`.
- Custom import-time recomputation from `ring_checkerboard_qca_v3_common.build_rules()`, `index_table()`, `ring_closure_rows()`, and `classical_dephased_limit_check()`.
  - Result: rank/index rows, operator distances, gauge perturbation, self-rejection falsifier, and v0 continuity row recomputed as reported.

I did not rerun `validate_ring_checkerboard_qca_v3.py` because it writes `results/ring_checkerboard_qca_v3_validator_results.json`, outside the user's write boundary. The existing builder validator result was read: `ok=true`, `phase=builder`, `errors=[]`.

## Adjudication

### 1. Distinctness

Verdict: **PASS.**

Fresh operator-distance recomputation:

| comparison | max abs difference |
|---|---:|
| `engine_L_flux_IN_left_O1` vs `calibration_left_shift` | `1.311244345696571` |
| `engine_L_flux_IN_left_O1` vs `calibration_right_shift` | `1.311244345696571` |
| `engine_R_flux_OUT_right_O1` vs `calibration_right_shift` | `1.409569545945773` |
| `engine_R_flux_OUT_right_O1` vs `calibration_left_shift` | `1.409569545945773` |
| `engine_L_flux_IN_left_O1` vs `engine_R_flux_OUT_right_O1` | `0.6381018314028842` |

The v3 self-rejection falsifier also behaves correctly: forcing an engine to equal `calibration_right_shift` gives distance `0.0`, so the `distance <= 1e-8` self-rejection gate would fire on a relabeled shift.

### 2. Committed Engine Dynamics

Verdict: **PASS at fixture scope, with a source-scope caveat.**

The construction path is real: `brickwork_engine()` composes an open shift with `brickwork_local_unitary()`. The L row uses `alternating_deductive` brickwork with `flux_sign=-1` after open left transport. The R row uses `paired_inductive` brickwork with `flux_sign=+1` after open right transport.

Fresh nontriviality distances:

- L engine vs bare left shift: `1.3112443456965712`
- R engine vs bare right shift: `1.4095695459457729`

This is stronger than v2. What remains weaker than full doctrine is that the brickwork is a bounded unitary fixture implementing the committed alternating/paired discipline pattern from `fe06d49bd`; it is not a full all-cells QCA dynamics admission.

### 3. Indices

Verdict: **PASS.**

Fresh crossing-rank recomputation:

| row | right rank | left rank | signed log2 index | ratio |
|---|---:|---:|---:|---|
| `calibration_right_shift` | 4 | 1 | +1 | `2/1` |
| `calibration_left_shift` | 1 | 4 | -1 | `1/2` |
| `calibration_nonshifting_onsite` | 1 | 1 | 0 | `1/1` |
| `paired_block_index0` | 4 | 4 | 0 | `1/1` |
| `engine_L_flux_IN_left_O1` | 1 | 4 | -1 | `1/2` |
| `engine_R_flux_OUT_right_O1` | 4 | 1 | +1 | `2/1` |
| `engine_L_index0_control` | 1 | 1 | 0 | `1/1` |
| `engine_R_index0_control` | 1 | 1 | 0 | `1/1` |
| `gauge_engine_R_inserted_H` | 4 | 1 | +1 | `2/1` |
| `falsifier_R_engine_forced_left_unitary` | 1 | 4 | -1 | `1/2` |

The paired-index-0 finding is real and should be stated narrowly: the paired form's declared crossing-rank information flux is balanced under this support-rank probe. It does not mean the paired discipline is dynamically trivial; the v0 floor's corrected transient-SCC difference remains the relevant classical structural result.

### 4. Gauge Row

Verdict: **PASS, and stronger than v2.**

The v2 caveat was that the inserted Hadamard canceled to numerical identity. v3 does not repeat that weakness.

Fresh checks:

- `gauge_engine_R_inserted_H` vs `engine_R_flux_OUT_right_O1`: max abs difference `0.3994786153908377`
- `gauge_engine_R_inserted_H @ engine_R^dagger` vs identity: max abs difference `0.45344397788600305`
- recomputed index remains `+1`, ratio `2/1`

So this is a real onsite perturbation with recomputed ranks, not just a sanity row that cancels away.

### 5. Expectation 2

Verdict: **EARNED at scratch open-chain fixture ceiling.**

The v2 rejection's specific defect is cured: the L/R engine rows are no longer numerically equal to calibration shifts, and the extracted signs are opposite. The doctrine's index/flux alignment is therefore earned for the bounded open-chain local-unitary fixture:

- `L` engine: `-1`
- `R` engine: `+1`
- index-0 controls: no L/R distinction
- real-unitary falsifier: forcing R to the L left-moving unitary changes R to `-1` and kills the opposite-sign predicate
- z3/cvc5 rows bind the computed rank/index facts and the flip branch

What still blocks stronger citation: finite-ring automorphism-class GNVW index remains trivial; the packet is not canonical/admitted; it is not full all-cells QCA dynamics; it is not v4 coupling-law evidence.

### 6. Standard Contract

Verdict: **PASS with caveats.**

Accepted:

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- all three engine result files present and `all_pass=true`
- envelope `all_pass=true`
- generic three-engine validator green with `--require-pytorch --strict-source-backed --require-tool-intent`
- existing packet-local builder validator result green
- `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, `TOOL_INTENT_MATRIX`, positive/negative/boundary sections present
- z3 and cvc5 are load-bearing for computed rank/index binding
- ring closure rows remain trivial and do not claim nonzero finite-ring automorphism-class index
- no claim-bearing `wire_flow`, `right_wires`, or `left_wires` metadata path found; matches are guard/prose/result-boundary text

Caveats:

- The whole v3 packet is currently untracked working-tree material.
- No Full Wizard Max Assembly subagent topology ran; local audit only.
- The Julia `QuantumClifford` witness is thinner than the numeric rank/SMT path. The main claim is carried by realized matrices, support-rank extraction, cross-engine agreement, and SMT binding.
- The packet-local validator was not rerun because it would rewrite result JSON outside the allowed write boundary.

## Final Verdict

`ring_checkerboard_qca_v3` is **GENUINE-WITH-CAVEATS as a scratch open-chain QCA crossing-rank fixture with distinct brickwork L/R engine unitaries**.

Expectation 2 is **earned at scratch fixture ceiling**: the committed L/R discipline fixtures carry opposite open-chain indices (`L=-1`, `R=+1`) and the v2 calibration-relabel defect is cured.

It is **not** promoted beyond that ceiling. Future work must not cite this as finite-ring nontrivial automorphism-class index, canonical QCA admission, full all-cells dynamics, v4 coupling-law admission, or broader physics/ontology evidence.
