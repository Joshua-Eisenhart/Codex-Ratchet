# Audit verdict - entropy_type_ratchet_v2

Audit mode: fresh read-only independent audit. This verdict file is the only audit-lane write; it is not builder output.

Bottom line: REJECT the strong `sequence_from_parent` claim as written. The packet is mechanically green and preserves the v1 construction/regression machinery, but the 28fc221a1 correction gate does not close because the executable operation IDs/functions are still supplied by packet-local translation tables rather than read from the parent sequence fields.

Accepted repo status: `passes local rerun` for the packet validators/tests below. Claim ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; not `canonical by process`; not doctrine closure.

## Gate Decision

- `sequence_from_parent`: NOT EARNED AS WRITTEN.
- `composed_sequence_rejected`: EARNED mechanically.
- v1 spoofed-enable regression: STILL LIVE.
- v1 construction mechanics: STILL STAND.
- alternative sequence test: LEGITIMATE SOURCE, NO OFF-DOCTRINE FINDING OBSERVED.
- 28fc221a1 correction gate: DOES NOT CLOSE.

The packet consumes parent rows and records parent row hashes, but it does not consume the parent artifact's machine-readable operation sequence as the source of operation IDs. The parent artifacts provide row order, constraints, and hashes; the packet-local code maps `(source, index/step)` to operation names and functions.

## Sequence-From-Parent Reality

The primary Python path:

- `entropy_type_ratchet_v2_common.py:405-415` defines `PARENT_OPERATION_MAP`, mapping `("trajectory", 0..3)` and `("deep", 3..7)` to packet-local operation IDs/functions.
- `entropy_type_ratchet_v2_common.py:425-462` walks parent rows, but assigns `step_id` from `PARENT_OPERATION_MAP`.
- `entropy_type_ratchet_v2_common.py:465-485` emits `sequence_source: consumed_parent_artifacts`.
- `entropy_type_ratchet_v2_common.py:496-507` executes functions from `PARENT_OPERATION_MAP`.
- `entropy_type_ratchet_v2_julia.jl:157-200` independently embeds the same index/step-to-operation mapping with local branches and a local function map.

Parent fields that exist but are not used as operation-ID authority:

- `system_v6/sims/manifold_unified_run_v0/results/manifold_unified_run_v0_step_trajectory_artifact.json:1263-1267` has `trajectory.sequence = ["leaf_conditioning", "lens_quotient", "terrain_restriction"]`.
- `system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json:484` has `pin_spec` with `single_leaf_deep_constraint_sequence` and step labels.

Rows actually consumed and hashed by v2:

- `trajectory.steps[0]`: constraint `no new constraint; hash-bound seed state`, row hash `7e6e7631b5826d8741102c734e86bb4bc8c2b4a8fbcb2b12abad34a02b604a67`.
- `trajectory.steps[1]`: constraint `leaf-conditioning via committed k-leaf union weights`, row hash `2e9bad64f327f1bad59ab04de6e44de634815670e29029f48ecbbd84995ec97f`.
- `trajectory.steps[2]`: constraint `lens quotient; global phase quotient preserves eta and density rows`, row hash `ac103c8890fd7fc39ad85dfc9755a0149c1dd095ccc3f22ea2591bbf4e64692a`.
- `trajectory.steps[3]`: constraint `terrain restriction on committed S6/S7 terrain rows`, row hash `a6606b18c0967055074f4d61e9f0f6b86af87c656a063a7a25891b56006cdcf6`.
- `ratchet_deep_chain_v0 rows[step=3]`: constraint `descended_single_leaf_phase_window`, row hash `dece00370147675577f91aad1763143fdc7b6c9fb7fe64ee2eafd0815499c769`.
- `ratchet_deep_chain_v0 rows[step=4]`: constraint `second_Z2_lens_on_quotient`, row hash `7758b1d0a29340057de445a524759d33f9b7151c98b5ed71c75d1eb088bb0497`.
- `ratchet_deep_chain_v0 rows[step=5]`: constraint `terrain_basin_restriction_Se_Funnel_L`, row hash `79892711ff4f90223c2f7655ac81d13b92e82876661e298f9ce8591633816c18`.
- `ratchet_deep_chain_v0 rows[step=6]`: constraint `terrain_then_operator_order_restriction`, row hash `205b9b9001719611bdfd84d0a37a3d0344d51adbca3040c72f1edbcc7129eeb6`.
- `ratchet_deep_chain_v0 rows[step=7]`: constraint `repeat_committed_T_pi_over_6_Z4_Z2_terrain_filters`, row hash `b2b31ebace8b5cd5ff44935d870f527f41f96c7238fb3077142604ea82750bda`.

Those hashes are real evidence that parent rows were consumed. They are not sufficient evidence that the operation sequence semantics were read from parent-side sequence fields.

## Alternative Sequence

The alternative sequence is `LTZW`, selected from `ratchet_order_breadth_v0.controls.live_order_blind_signatures`, not invented as a local strawman. The packet reports:

- `alternative_source`: `ratchet_order_breadth_v0.controls.live_order_blind_signatures`
- `baseline_parent_order_token`: `LZWT`
- `alternative_token_order`: `LTZW`
- `finding_status`: `no_off_doctrine_availability_steps_observed`
- `off_doctrine_findings`: `[]`

This is honest as far as the emitted alternative table goes: the alternative changes row order but the first availability step for each doctrine type still matches the doctrine table. If a future alternative produces a non-empty `off_doctrine_findings` list, it must be cited as a FINDING, not smoothed into agreement.

## Regression Gates

Fresh direct injection rejected:

- packet-local literal composed sequence: `ComposedSequenceRejected: composed-in-packet sequence rejected; sequence must be consumed_parent_artifacts`
- wrong parent-order hash under `consumed_parent_artifacts`: `ComposedSequenceRejected: parent order hash mismatch`
- spoofed enable: `ShortcutRejected: declared-enable shortcut rejected before construction`

The packet validator also injects the composed sequence at `validate_entropy_type_ratchet_v2.py:120-125`, and pytest covers it at `test_entropy_type_ratchet_v2.py:85-92`.

## v1 Carry-Forward

The following v1-earned pieces still stand in v2:

- availability rows are construction-attempt sourced, not declared-enable sourced;
- premature evaluations fail with `MissingStructure` from real state paths;
- N01/order-shuffle control survives;
- type confusion is rejected without an explicit convention;
- operator attempts co-ratchet through the same constructed objects.

The doctrine-table comparison is mechanically honest in the narrow sense: it reports `agreement=true` and `findings=[]` for the primary table. But because the primary operation semantics still come through packet-local translation, the comparison supports reproduction against the mapped parent lineage, not full sequence-origin discovery.

## Tool, SMT, Schema, Boundary

Fresh commands run, all exit 0:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/entropy_type_ratchet_v2/validate_entropy_type_ratchet_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/entropy_type_ratchet_v2/test_entropy_type_ratchet_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/entropy_type_ratchet_v2/results/entropy_type_ratchet_v2_envelope_results.json
direct Python injection for composed sequence, wrong parent hash, and spoofed enable rejection
```

Observed outputs:

- packet validator: `{"ok": true, "result_json": "...entropy_type_ratchet_v2_envelope_results.json"}`
- pytest: `9 passed`
- strict three-engine validator: `{"ok": true, "result_json": "system_v6/sims/entropy_type_ratchet_v2/results/entropy_type_ratchet_v2_envelope_results.json"}`

Envelope result:

- `schema_version=three_engine_sim_result_v1`
- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `all_pass=true`
- SMT polarity: `negated_identity_over_discovered_status_matrix`
- z3/cvc5/Julia Z3 identity verdicts: `unsat`
- z3/cvc5/Julia Z3 erased-quotient perturbation verdicts: `sat`
- tool depths: `QuantumOptics`, `Z3`, `build_three_engine_envelope`, `sympy`, `z3`, `cvc5`, and `torch_geometric` are `load_bearing`; `torch` and `torch.func` are `supportive`.

I did not run engine/envelope writer scripts because this audit was read-only except for this verdict file, and those scripts would rewrite result JSON.

## Final Verdict

REJECT / PARTIAL.

`entropy_type_ratchet_v2` passes its mechanical validators and earns a better regression envelope than v1, but it does not close the 28fc221a1 gate. The packet's own `sequence_from_parent=true` is overbroad because operation IDs/functions are translated in-packet from parent indices/steps instead of read from the parent sequence fields.

Future citation rule: cite this packet only as `scratch_diagnostic` evidence that the v1 construction-attempt machinery, spoofed-enable/composed-sequence regression gates, alternative-order test, and SMT/tool envelope are green over a hash-bound parent-row lineage. Do not cite it as closing the sequence-origin correction or as widening the doctrine from `reproduced` back to `discovered` until a repaired packet reads operation IDs/order from parent sequence fields and rejects packet-local semantic placement.
