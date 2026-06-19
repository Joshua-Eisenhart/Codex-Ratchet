# Fresh cross-backend audit verdict -- six_bit_two_trigram_szilard_fixture_v0

Bottom line: `GENUINE-WITH-CAVEATS`.

The packet earns the bounded fixture claim: the six-bit carrier enumerates 64 states as `8 x 8` lower/upper trigram pairs; the per-cycle Szilard ledger rows recompute to `6`, `6`, `3`, `3`, and `2` ln2 coefficients for the unstructured full register, full trigram-pair record, lower-only record, upper-only record, and parity-pair record; the full `3+3` trigram split has zero record-cost delta against an unstructured six-bit state record; and the envelope completion preserves the values while keeping the promotion fences.

It is not clean enough for uncaveated stronger citation. The row is a finite exact-counting/classical-baseline fixture, not physics, QIT, Matrix64 completion, nonclassical evidence, or axis admission. The full-state structure effect is computed in the code/results, but only after the fixture defines the full recorded variable as an equiprobable `(lower_trigram, upper_trigram)` pair over `8 x 8`; partial-record savings are coarser-variable savings, not a cheaper full carrier.

## Verdict

- Repo verdict: `GENUINE-WITH-CAVEATS`.
- Classification ceiling stays: `scratch_diagnostic`.
- Row ceiling stays: `classical_baseline`.
- Promotion: `promotion_allowed=false`, `formal_admission_allowed=false`.
- Future citation status: cite as a bounded finite carrier and Szilard/Landauer ledger fixture only.

Rejected stronger readings:

- Not `GENUINE` without caveats because the packet is intentionally a finite counting fixture and the structure effect is conditional on the declared uniform record variable.
- Not `DECORATIVE`: the carrier enumeration, record-cost rows, per-cycle ledger coefficients, wrong-order controls, and cross-backend parity are computed and tested.
- Not `BY_CONSTRUCTION` only: the `3+3-6=0` identity is formulaic after the variable choice, but the packet enumerates the 64 states, pair support, parity support, ledger rows, and envelope parity.
- Not `BROKEN`: fresh read-only validators, pytest, and independent recomputation agree.

## Per-Cycle Ledger Adjudication

Fresh independent recomputation found:

| Row | Distinct records | Expected bits | Result row | Verdict |
|---|---:|---:|---:|---|
| `unstructured_6bit_state_record` | 64 | 6 | record/work/erase all `6`, net `0` | pass |
| `two_trigram_full_pair_record` | 64 | 6 | record/work/erase all `6`, net `0` | pass |
| `lower_trigram_only_record` | 8 | 3 | record/work/erase all `3`, net `0` | pass |
| `upper_trigram_only_record` | 8 | 3 | record/work/erase all `3`, net `0` | pass |
| `parity_pair_record` | 4 | 2 | record/work/erase all `2`, net `0` | pass |

Wrong-order controls preserve the safe-order fence: `measure -> feedback -> erase` is `sat`; `feedback -> measure -> erase` and `measure -> erase -> feedback` are `unsat`; no-measurement control has zero work credit.

Panel 7 fit is local and bounded: the ledger uses the same class of counting relation, where erased distinguishability carries a Landauer floor and perfect record does not create a free cycle because reset still costs the recorded information. This fixture is not a basin-relaxation packet and does not claim `ln(m)` over a trajectory merge; its local floor is the record bit count times `ln(2)`.

## Structure Row

The `3+3` trigram split does not reduce the full-state record cost:

```text
log2(8) + log2(8) - log2(64) = 3 + 3 - 6 = 0
```

Adjudication: `computed-but-definition-dependent`.

It is computed by the base Python fixture and independently mirrored by the Julia and JAX/SymPy lanes. But the computation is only meaningful under the declared full variable: an equiprobable pair `(lower_trigram, upper_trigram)` over all `8 x 8` combinations. The lower-only, upper-only, and parity-pair rows are cheaper because they erase coarser variables, not because the full 64-state carrier became cheaper.

## Envelope Completion

The envelope completion is legitimate for the stated ceiling.

- Mode: `julia_canon_plus_jax_diagnostic_pytorch_omitted`.
- Accepted lanes: `julia`, `jax`.
- Omitted lane: `pytorch`, explicitly because this fixture has no tensor/autograd/graph claim path.
- Values unchanged: `result_values_unchanged=true`.
- Parity checks: Julia and JAX both match base for cost rows, split delta, net ledger rows, wrong-order controls, and carrier count.
- Generic validator with `--require-tool-intent` passed.

Caveat: this is a cross-backend envelope over exact finite-counting mirrors, not three independent physics engines and not a PyTorch/nonclassical result.

## Fences

Fences pass.

- `classification=scratch_diagnostic`.
- `row_classification=classical_baseline`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- `no_physics_bridge=true`.
- `no_64_claims=true`.
- `not_qit_admission=true`.
- `not_axis_admission=true`.
- `not_matrix64_completion=true`.
- `divergence_log` is non-empty.

The Matrix64/64-state content is data about this finite carrier only. It must not be cited as all-64 completion, Matrix64 admission, engine placement, or physics bridge.

## Checks Run

- Read contract and process docs: `CODEX.md`, `system_v5/docs/LEGO_SIM_CONTRACT.md`, `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`, `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`.
- Read fixture sources/results under `system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/`.
- Read fixture build card, panel 7 receipt, and nearby Carnot/Szilard ledger references.
- Fresh read-only packet validator:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/validate_six_bit_two_trigram_szilard_fixture_v0.py`
  - result: `ok=true`.
- Fresh read-only generic envelope validator:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/results/six_bit_two_trigram_szilard_fixture_v0_envelope_results.json`
  - result: `ok=true`.
- Fresh pytest:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/six_bit_two_trigram_szilard_fixture_v0/tests`
  - result: `7 passed`.
- Fresh independent in-memory recomputation:
  - pair count `64`;
  - parity-pair count `4`;
  - expected bits `6, 6, 3, 3, 2`;
  - ledger errors `[]`.

Producer scripts were not rerun because they would rewrite result timestamps, and this audit was scoped read-only except for this verdict file.

## Citation Rule

Allowed citation:

`six_bit_two_trigram_szilard_fixture_v0` is a `GENUINE-WITH-CAVEATS` scratch diagnostic showing that a finite six-bit carrier can be represented as `8 x 8` lower/upper trigram pairs, with classical-baseline Szilard measure-feedback-erase ledger rows whose Landauer coefficients are `6`, `6`, `3`, `3`, and `2` times `ln(2)` for the declared record variables; the full trigram-pair record has zero cost delta relative to an unstructured six-bit full-state record; the envelope preserves these values across Julia and JAX/SymPy mirrors.

Forbidden citation:

Do not cite it as thermodynamic heat/work/bath mechanics, physical Landauer engine evidence, QIT admission, nonclassical evidence, Matrix64/all-64 completion, axis admission, bridge admission, PyTorch evidence, or proof that the trigram split makes full-state erasure cheaper. Do not cite partial-record savings without saying they come from coarser recorded variables.
