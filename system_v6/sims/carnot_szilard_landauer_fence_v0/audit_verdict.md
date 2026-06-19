# Audit verdict: carnot_szilard_landauer_fence_v0

Bottom line: CAVEATED CLASSICAL FENCE PASS at `scratch_diagnostic` / `classical_baseline` ceiling only. The packet is not admissible as physics, bridge, nonclassical-stack, or formal-admission evidence. Future citation must say: this is exact pinned-coefficient classical legality/fence evidence, useful for what classical thermodynamic legality already excludes, never evidence that the nonclassical stack did anything.

## Verdict

Accepted as: `passes local rerun` for the saved envelope/validator surface, with `promotion_allowed=false` and `formal_admission_allowed=false`.

Not accepted as: canonical nonclassical evidence, thermodynamic cycle derivation, bridge evidence, manifold evidence, or proof that any Hopf/Weyl/quotient stack is active.

This does not repeat the full 9dad43b2b DECORATIVE failure in the narrow "label-only solver row" sense: the solver variables are bound to exact rational numerator/denominator values, and the broken-fence erasure flips to SAT. But it does not meet the strongest "own cycle ledger" standard either. The efficiency and erasure rows are pinned coefficient rows, not heat/work-ledger-derived engine rows.

## Tautology check

`super_carnot_eta_3_4` binds exact computed/pinned values:

- `eta_C = 1 - T_c/T_h = 1/2` from `T_h=2`, `T_c=1`.
- candidate `eta = 3/4`.
- z3/cvc5 assert the legal fence `eta <= eta_C` and the forbidden query `eta > eta_C`.

That is not merely `assert not(eta > eta_C)`, and it is not label-only. However, the candidate eta is not derived from a cycle ledger of heats and works. It is a pinned row coefficient. The same caveat holds for `single_bath_positive_work`, `below_landauer_half_paid`, and `unpaid_erasure_surplus`: they bind exact coefficients, but they do not derive those coefficients from an explicit work/heat/measurement/erasure ledger.

Audit classification for this point: not decorative as a solver-binding smoke test; decorative/insufficient if cited as an own-cycle thermodynamic derivation.

## Equality boundary

The boundary convention is named and consistent: closed reversible Carnot boundary admitted, `eta <= eta_C`; therefore `eta = eta_C` is SAT and only `eta > eta_C` is excluded.

## Pre-registered falsifiers

The pre-registered falsifiers behave as named in the saved envelope:

- super-Carnot SAT under intact fence: killed by UNSAT.
- below-Landauer SAT: killed by UNSAT.
- free/unpaid erasure surplus SAT: killed by UNSAT.
- equality-boundary inconsistency: killed by consistent SAT boundary.
- mixed bits/nats: killed by explicit conversion row and empty `typed_entropy_violations`.

Typed entropy is explicit: `1 bit * ln(2) = ln(2) nats`; Landauer and Szilard rows use `ln(2)` nats coefficients. I found no mixed bits/nats proof row.

## Broken-fence control

The dropped constraint is the legal Carnot fence (`eta <= eta_C`). With that constraint omitted, the super-Carnot row flips to SAT across Julia z3, JAX z3/cvc5, and PyTorch z3/cvc5 in the envelope.

Independent auditor scratch witness:

- SAT model: `eta = 3/4`.
- `eta_C = 1/2`.
- Numeric check: `0.75 > 0.5`.

Caveat: the saved result records the SAT flip but not the model witness. Future revisions should persist the model in the result JSON, not only in this audit.

## Connection row

The connection row is correctly labeled as `read_only_observation_not_admission`. It co-cites `manifold_information_throughput_v0` and `z4_syndrome_record_v0`, names the state-plus-record convention, and states the shared typed nats account only under finite state-plus-record bookkeeping. It also explicitly denies scalar conservation, bridge/physics admission, and cross-type entropy summing outside that convention.

## Shuffled-ledger / N01 control

The Julia lane computes a finite order graph for `measure -> feedback -> erase` versus `feedback -> measure -> erase`. Normal order is SAT; shuffled order is UNSAT because `measure_before_feedback` changes. JAX and PyTorch mirror the same normal/shuffled verdicts, but those two lanes are label/row mirrors for this control rather than graph-computed order checks.

## Validator reruns

Fresh read-only validator runs passed:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/carnot_szilard_landauer_fence_v0/validate_carnot_szilard_landauer_fence_v0.py`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/carnot_szilard_landauer_fence_v0/results/carnot_szilard_landauer_fence_v0_envelope_results.json`

I did not rerun the engine scripts because the user-set audit boundary was read-only except this verdict file, and those scripts rewrite result JSONs.

## Named caveats

1. Own-cycle ledger caveat: no explicit heat/work cycle ledger derives `eta`; the solvers consume exact pinned coefficients.
2. Persisted-model caveat: broken-fence SAT model is witnessed in this audit, but not stored in the packet result JSON.
3. N01 mirror caveat: Julia uses `Graphs`; JAX/PyTorch record the same order verdicts without independently computing graph reachability.
4. Workspace-state caveat: the whole packet is currently untracked in git, so this audit is over live workspace artifacts, not committed evidence.

## Future citation rule

Allowed citation: "classical fence / pinned exact coefficient SMT control showing Carnot/Landauer legality rows and typed entropy conversion under classical_baseline scratch_diagnostic ceiling."

Forbidden citation: any nonclassical admission, bridge claim, manifold/quotient progress, thermodynamic cycle derivation from heat/work ledgers, or evidence that the nonclassical stack exceeds the classical fence.
