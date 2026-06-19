# audit_verdict.md - engine_readout_strategy_fidelity_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11 UTC
Scope: read-only audit of `engine_readout_strategy_fidelity_v0`; the only repo write in this audit is this file.
Wizard route truth: PARTIAL. Native subagent fanout was not run because this runtime only permits spawned subagents when the user explicitly asks for delegation. Evidence below is from direct source inspection, local gates, and fresh in-memory recomputation.

## VERDICT

SURVIVES WITH NAMED CAVEATS as a scratch diagnostic readout packet.

Earned:
- The committed 16-strategy automaton's alternating/paired periodicity claims are verified per strategy on regenerated n=8 loop-local dense states.
- The 16x16 readout distinguishability structure is computed and anti-collapse groups are named.
- The 720-vs-360 question is answered computationally: no strategy pair separates only on the double traversal; double_720 repeats the 360 readout classes.
- Python z3, Python cvc5, and Julia Z3 all bind computed rows and flip under the erased nontrivial inequality control.

Not earned:
- No strategy promotion.
- No formal admission.
- No engine or physics admission.
- No claim beyond n=8 loop-local readout diagnostics on the committed parent word.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Source Pins

Calibrated bar read: `system_v6/receipts/audit_bar_calibration_20260610.md`. I applied exactness-class stability rather than byte-stability, and kept route genuineness, can-fail controls, source pinning, and erasure honesty as verdict-bearing checks.

Foundations source: commit `dd9ec4999b2ccb982226344f232dda86307429fc`, `system_v6/foundations/two_engine_readout_automaton_20260609.md`.

Quoted source:
- line 8: "ACTIVE LOOP reads ONE component"
- line 10: "Se=LoseWin, Ne=WinLose, Ni=LoseLose, Si=WinWin"
- line 11: `C_D = Se->Ne->Ni->Si`; `C_I = Se->Si->Ni->Ne`
- lines 15-18 pin the four base readout rules:
  - Type1 outer deductive: `LOSE -> WIN -> LOSE -> WIN`
  - Type1 inner inductive: `win -> win -> lose -> lose`
  - Type2 outer inductive: `WIN -> WIN -> LOSE -> LOSE`
  - Type2 inner deductive: `lose -> win -> lose -> win`
- line 19 states the load-bearing structure note: deductive yields alternating; inductive yields paired.

Parent state source: commit `123b8e7d8f1b7aca5162facc5a7801f06372b02a`, `system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py`.

Parent pins:
- parent `PIN_SPEC` lines 46-52: `word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne`, `seat_i_uses_word_i_mod_8`, scratch ceiling.
- parent `STAGE_WORD` lines 108-117: same stage, loop, axis, and family sequence as this packet.
- parent result check from `engine_stage_word_cost_discriminator_v0_jax_results.json`: n=8 MPS-vs-dense `fidelity=1.0`, `infidelity=0.0`, `truncation_error_reported_as_infidelity=0.0`, and `bond_sizes_match_dense_ranks=true`.

Named caveat C1: current packet normalizes parent signed operators from glyphs (`Ti up/down`) into ASCII names (`Ti_up`, `Ti_down`, etc.). The stage, loop, axis, family, sign polarity, and word order match. This is traceable normalization, not a strategy break.

## Q1 - STATES GENUINE

PASS.

Evidence:
- Current Python leg `PIN_SPEC`, lines 57-63, consumes `123b8e7d8,dd9ec4999`, pins `n=8`, `states=dense_loop_local_replay`, the same D-then-I word, seat rule, and scratch ceiling.
- Current Python leg `STAGE_WORD`, lines 99-108, matches the parent stage/loop/axis/family order.
- Current envelope `source_hashes_fresh`, lines 58-60 and 159-160, checks declared source hashes for both engine legs.
- Stored envelope `pin_sha256=d0d6e5526d81dfd0159aa803797e4ad47939b061b939f213d451bd7292191e9b`; fresh recomputation of the Python `PIN_SPEC` hash matched.
- Fresh in-memory Python recompute matched stored fields exactly for `strategy_rows`, `periodicity_findings`, `distinguishability`, `controls`, `crossover_proofs`, and `values`.
- Fresh in-memory Julia recompute matched stored Julia values: `strategy_count=16`, `state_count_word=8`, `state_count_double_720=16`, `periodicity_violation_count=0`.

State counts:
- Python/JAX result: `state_count_word=8`, `state_count_double_720=16`.
- Julia result: same counts by fresh in-memory recompute.

## Q2 - THE STRATEGY MAPPING

PASS.

Traceability:
- Foundations lines 14-19 provide four base readout strategies and the alternating/paired rule.
- Current Python `BASE_STRATEGIES`, lines 117-157, implements exactly those four base strategies.
- Current row expansion, lines 302-344, expands each base strategy across its four `stage_slot` entries, yielding 16 rows.
- Measurement mapping, lines 322-327, records source, component read rule, stage-to-readout map, and state binding.

Untraceable strategies: none found. All 16 rows are four stage-slot expansions of one of the four cited source rules.

## Q3 - PERIODICITY TABLE

PASS.

Declared rule in code:
- lines 289-299 define `alternating` as bits 0=2, 1=3, and 0!=1; `paired` as bits 0=1, 2=3, and 0!=2; double_720 additionally requires the second four labels repeat the first four.

Fresh recomputation samples:
- `type1_outer_deductive_slot_Se`: `LOSE WIN LOSE WIN`, bits `0 1 0 1`, predicted `alternating`, word and double_720 OK.
- `type1_inner_inductive_slot_Se`: `win win lose lose`, bits `1 1 0 0`, predicted `paired`, word and double_720 OK.
- `type2_outer_inductive_slot_Se`: `WIN WIN LOSE LOSE`, bits `1 1 0 0`, predicted `paired`, word and double_720 OK.
- `type2_inner_deductive_slot_Se`: `lose win lose win`, bits `0 1 0 1`, predicted `alternating`, word and double_720 OK.

Load-bearing result:
- All 16 strategy rows recomputed clean.
- `periodicity_findings=[]`.
- `periodicity_violation_count=0`.

Violations honestly reported: none existed in the stored result or fresh recomputation.

## Q4 - 16x16 DISTINGUISHABILITY MATRIX

PASS, with anti-collapse result stronger than the prompt's double-only example request.

Declared comparison rule:
- Current Python distinguishability code, lines 357-375, computes `separated_matrix_360` by `left["readout_word"] != right["readout_word"]` and `separated_matrix_double_720` by `left["readout_double_720"] != right["readout_double_720"]`.

Named indistinguishable groups at 360:
- `type1_outer_deductive_slot_Se`, `type1_outer_deductive_slot_Ne`, `type1_outer_deductive_slot_Ni`, `type1_outer_deductive_slot_Si`
- `type2_outer_inductive_slot_Se`, `type2_outer_inductive_slot_Si`, `type2_outer_inductive_slot_Ni`, `type2_outer_inductive_slot_Ne`
- `type2_inner_deductive_slot_Se`, `type2_inner_deductive_slot_Ne`, `type2_inner_deductive_slot_Ni`, `type2_inner_deductive_slot_Si`
- `type1_inner_inductive_slot_Se`, `type1_inner_inductive_slot_Si`, `type1_inner_inductive_slot_Ni`, `type1_inner_inductive_slot_Ne`

Named indistinguishable groups at double_720: the same four groups, with each readout repeated twice.

720-vs-360 separation:
- Fresh exhaustive set difference found `only_double_separation_pairs_count=0`.
- Stored and recomputed values: `unique_readouts_360=4`, `unique_readouts_double_720=4`, `double_720_separates_more_than_360=false`.
- Therefore no pair exists to "verify one" for double-only separation. The correct computational answer is: none.

## Q5 - CONTROLS AND SOLVERS

PASS.

Control code:
- lines 379-405 define shuffled path, trace-constant, and permuted-seat controls.
- lines 409-437 bind computed Python rows to z3 and assert existence of a periodicity violation.
- lines 440-465 bind computed Python rows to cvc5 and assert existence of a periodicity violation.
- Julia `z3_periodicity` was recomputed in-memory without writing repo results.

Fresh recomputed controls:
- `shuffled_stage_word_breaks_periodicity_table=true`; four failures.
- `strategy_blind_trace_constant=true`; all 16 trace values are `1.0`.
- `permuted_seat_assignment_breaks_alternating_paired_split=true`; two failures.

Solver verdicts:
- Python z3: violation query `unsat`; erased-flip control `sat`.
- Python cvc5: violation query `unsat`; erased-flip control `sat`.
- Julia Z3: violation query `unsat`; erased-flip control `sat`.

Interpretation: the solver checks are load-bearing for the finite periodicity identity because they bind computed row bits and flip under erasure. They are not merely decorative manifest entries.

## Q6 - STANDARD / SCHEMA / HYGIENE

PASS WITH NAMED CAVEATS.

Mechanical checks run before this file existed:
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/engine_readout_strategy_fidelity_v0/validate_engine_readout_strategy_fidelity_v0.py` -> `ok=true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json` -> `ok=true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim ..._envelope.py` -> no violations for `Z3`, `z3`, `cvc5`.
- Same capability gate on `..._jax.py` -> no violations for `z3`, `cvc5`.
- Same capability gate on `..._julia.jl` -> no violations for `Z3`.
- `scripts/codex_runtime_env_doctor.py --json` -> `summary.ok=true`, `install_state=stable_observed`.

Source-backed rich-tool audit:
- `scripts/audit_three_engine_source_claims.py --results-dir system_v6/sims/engine_readout_strategy_fidelity_v0/results --json-out /tmp/engine_readout_strategy_fidelity_source_claim_audit.json --md-out /tmp/engine_readout_strategy_fidelity_source_claim_audit.md`
- Julia lane: `source_backed_rich_tool_claim` for `Z3`.
- Python/JAX lane: `source_backed_rich_tool_claim` for `z3` and `cvc5`.
- Envelope-level caveat C2: generic three-engine source audit verdict is `blocked_missing_engine_lane` because there is no PyTorch lane. The packet itself declares `julia_canon_plus_jax_diagnostic` and says no PyTorch lane is scoped because there is no graph/network/autograd claim path. This is an honest mode/lanes caveat, not evidence against the readout claim.

Schema and mode:
- Envelope schema is `three_engine_sim_result_v1`.
- Envelope/result mode is `FREE`.
- Engine contract declares lanes `["julia", "jax"]`, no peer result reads, and `julia_canon_plus_jax_diagnostic`.

Parent lineage:
- Envelope declares controller `main_codex_thread`, no native subagents, no external workers, and builder-only packet route truth. This is honest for the original builder packet.
- Audit route caveat C3: this file adds an audit verdict after the builder packet. The packet-local validator intentionally required no `audit_verdict.md`; rerunning that specific validator after this write would now fail its builder-packet invariant by design.

Tools and one-to-one calls:
- Load-bearing tools have concrete calls: Python `z3`, Python `cvc5`, Julia `Z3`.
- Supportive serialization/std-library manifest entries do not each have separate tool-call rows. Caveat C4: one-to-one is satisfied for load-bearing claim-path tools, not for every supportive stdlib/serialization entry.

No fixture wording:
- Search over the packet found no `fixture`, `dummy`, `toy`, `stub`, `mock`, or `placeholder` wording. `fake` did not appear as a claim object in this packet.

Versions and seeds:
- Python tool versions recorded: `cvc5=1.3.3`, `numpy=2.3.4`, `z3` import present with `__version__=null`.
- Runtime doctor observed Python 3.13.6, Julia 1.12.6, active Julia project `system_v5/julia_carrier/Project.toml`.
- Seeds: Python/JAX `20260610`, Julia `20260610`.

Ceilings:
- Envelope, Python/JAX, and Julia all record `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Envelope disallowed claims include `strategy promotion`, `formal admission`, and `physics or engine admission`.

## Q7 - CLOSURE

Closure earned:
- Real loop-local n=8 dense states were regenerated in Python/JAX and Julia-side dense/Z3 logic was recomputed in-memory for this audit.
- The foundations automaton's per-strategy alternating/paired periodicity claims survived on the computed readouts.
- The 16x16 separation matrix survived recomputation.
- Anti-collapse groups are explicit and named.
- The double traversal does not add separations beyond one 360 readout cycle.
- Controls fire in the expected directions.

Closure not earned:
- No stronger automaton admission.
- No parent cost-discriminator promotion beyond its own committed scratch ceiling.
- No PyTorch/graph/autograd lane claim.
- No bridge, axis, physics, engine, or formal admission claim.

Final accepted status label for this packet: `passes local rerun` for the audited diagnostic claims above, with `scratch_diagnostic` ceiling. Not `canonical by process` for any stronger consumer.

