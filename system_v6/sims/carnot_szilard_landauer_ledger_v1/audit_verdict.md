# Audit verdict: carnot_szilard_landauer_ledger_v1

Bottom line: PASS AS CAVEATED CLASSICAL LEDGER FENCE / EXCLUSION EVIDENCE at `scratch_diagnostic` packet ceiling and `classical_baseline` row ceiling only. The three v0 fence gaps close for this packet: ledger-derived rows replace pinned efficiency rows, broken-fence SAT witnesses are persisted in result JSON, and N01/order controls run in all claim-bearing lanes. This is not nonclassical evidence, bridge evidence, physics admission, manifold evidence, or formal admission.

## Verdict

Accepted as: `passes local rerun` for the saved envelope, packet-local validator, pytest checks, generic three-engine validators, and independent scratch recomputation performed in this audit.

Not accepted as: canonical nonclassical evidence, bridge evidence, thermodynamic novelty, physics admission, or proof that any nonclassical stack did anything. Future citation must keep the phrase `classical_baseline` or equivalent classical exclusion boundary.

The v0 standard was `system_v6/sims/carnot_szilard_landauer_fence_v0/audit_verdict.md` at commit `e10273983`. Its named gaps were:

1. pinned coefficient rows, not ledger-derived rows;
2. no persisted SAT model witness;
3. Julia-only graph-computed N01, with JAX/PyTorch mirrors only.

All three are closed here, with the caveats named below.

## Ledger Derivation

The Carnot rows are ledger-derived in the relevant sense. In `carnot_szilard_landauer_ledger_v1_common.py`, `ledger_totals()` computes `q_hot`, `q_cold`, `work_out`, `energy_residual`, `entropy_production`, and `eta` from per-stroke entries. The z3 and cvc5 paths bind those totals as solver variables, assert first-law conservation, derive `sigma = -q_hot/T_h - q_cold/T_c`, derive `eta * q_hot = work_out`, and use `sigma >= 0` as the second-law constraint. I found no hidden `eta <= eta_C` assertion in the Python z3/cvc5 path.

Fresh scratch recomputation:

- reversible Carnot: `q_hot=2`, `q_cold=-1`, `work_out=1`, `energy_residual=0`, `entropy_production=0`, `eta=1/2`; z3 SAT, cvc5 SAT.
- sub-Carnot irreversible: `q_hot=2`, `q_cold=-3/2`, `work_out=1/2`, `energy_residual=0`, `entropy_production=1/2`, `eta=1/4`; z3 SAT, cvc5 SAT.
- super-Carnot candidate: `q_hot=2`, `q_cold=-1/2`, `work_out=3/2`, `energy_residual=0`, `entropy_production=-1/2`, `eta=3/4`; z3 UNSAT, cvc5 UNSAT under intact `sigma >= 0`.
- broken-fence control: same super-Carnot ledger with `sigma >= 0` dropped is SAT, with `eta=3/4 > eta_C=1/2`.

So the super-Carnot exclusion comes from the ledger's own heat/work/entropy constraints, not from a pinned `eta` fence. `eta_C=1-T_c/T_h=1/2` is also reproduced by the reversible ledger because `sigma=0`, `q_hot=2`, `q_cold=-1`, and `work_out=1`.

Szilard/Landauer is ledger-bookkeeping derived rather than a full heat/work cycle derivation: the paid row records measure, feedback, and erase entries; work and erasure cost are both `k*T*ln(2)`; unpaid erasure and half-paid Landauer rows are UNSAT from `paid >= required`. That closes v0's pinned-cost gap for the stated finite record/erasure ledger, but it remains a classical bookkeeping lane.

## Persisted Witnesses

The broken-fence SAT model is persisted in the result JSON, not only in this audit:

- envelope key: `controls.broken_fence_drop_entropy_constraint_super_carnot`;
- JAX/PyTorch z3 models: `q_hot=2`, `q_cold=-1/2`, `work_out=3/2`, `entropy_production=-1/2`, `eta=3/4`;
- JAX/PyTorch cvc5 models: same values in cvc5 syntax;
- Julia Z3 model: scaled values `q_hot_scaled2=4`, `q_cold_scaled2=-1`, `work_out_scaled2=3`, `entropy_prod_scaled4=-2`, `energy_residual_scaled2=0`, with adjacent derived `eta=3/4`, `eta_c=1/2`.

Manual relaxed-constraint check from the persisted model:

- `2 + (-1/2) - 3/2 = 0`;
- `(3/4) * 2 = 3/2`;
- `-2/2 - (-1/2) = -1/2`;
- `3/4 > 1/2`.

The Python source creates those witnesses from `solver.model()` and cvc5 `getValue()` after a real SAT check. The Julia source persists `Z3.model(solver)` for scaled exact integer variables.

## Misledgered Control

The deliberately omitted entry is caught in all three lanes. The packet reports:

- `omitted_entry=too_small_cold_rejection`;
- `errors=["missing_strokes:too_small_cold_rejection", "first_law_energy_residual_nonzero"]`;
- derived bad ledger residual `energy_residual=1/2`, `entropy_production=-1`.

Fresh scratch recomputation returned the same `status=caught`.

## N01, Boundary, And Units

N01/order control is no longer Julia-only:

- Julia uses `Graphs.SimpleDiGraph`, `Graphs.has_path`, and order predicates.
- JAX computes boolean adjacency plus transitive reachability.
- PyTorch computes boolean adjacency plus transitive reachability.

All three report normal `measure -> feedback -> erase` as SAT and permuted `feedback -> measure -> erase` as UNSAT. This is a finite three-step order control, not dynamics or nonclassical evidence.

The Julia Z3.jl lane is honest but weaker than the Python solver-native lanes. It uses exact `Rational` totals encoded as scaled integers. My scaled-residual audit checked:

- reversible: scaled `q_hot=4`, `q_cold=-2`, `work=2`, `energy=0`, `sigma=0`;
- sub-Carnot: scaled `q_hot=4`, `q_cold=-3`, `work=1`, `energy=0`, `sigma=2`;
- super-Carnot: scaled `q_hot=4`, `q_cold=-1`, `work=3`, `energy=0`, `sigma=-2`;
- misledgered: scaled `q_hot=4`, `q_cold=0`, `work=3`, `energy=1`, `sigma=-4`.

Caveat: Julia blocks forbidden rows by exact Julia-rational precheck plus `Z3.BoolVal(false)`. That is an honest scaled-integer workaround and a useful exact reference lane; it is not as strong as the JAX/PyTorch Python z3/cvc5 encodings that assert the inequalities directly in the solver.

The equality boundary is explicit and consistent: closed reversible Carnot boundary is admitted; `eta=eta_C` is SAT; only `eta > eta_C` is excluded.

The bits/nats convention is explicit: `1 bit * ln(2) = ln(2) nats`; typed entropy violations are empty; the connection row preserves the finite state-plus-record/no cross-type entropy-sum boundary.

## Tool And Schema Honesty

The solvers are genuinely primary instruments in the Python lanes. z3/cvc5 derive SAT/UNSAT from ledger variables and constraints, not from labels. Tool declarations are consistent with this ceiling:

- z3 and cvc5 are load-bearing for ledger SAT/UNSAT and persisted model witnesses;
- Graphs/JAX/PyTorch adjacency are load-bearing/supportive for the finite N01 order control;
- sympy records the exact `ln(2)` typed conversion;
- `torch.func` constructs a finite ledger tensor before solver binding in the PyTorch lane.

The result remains bounded:

- `classification=scratch_diagnostic`;
- `row_classification=classical_baseline`;
- `promotion_allowed=false`;
- `formal_admission_allowed=false`;
- purpose boundary denies physics admission, bridge claim, nonclassical evidence, or promotion.

## Fresh Checks

Read-only checks run before this audit verdict file was created:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/carnot_szilard_landauer_ledger_v1/validate_carnot_szilard_landauer_ledger_v1.py
```

Result: `ok: true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/carnot_szilard_landauer_ledger_v1/tests -q
```

Result: `3 passed in 0.16s`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_envelope_results.json
```

Result: `ok: true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/carnot_szilard_landauer_ledger_v1/results/carnot_szilard_landauer_ledger_v1_envelope_results.json
```

Result: `ok: true`.

Additional scratch recomputation imported the packet helpers without writing result files and independently reproduced the Carnot, broken-fence, erasure, and misledgered-control statuses. I did not rerun the engine or envelope scripts in place because the user boundary was read-only except this file and those scripts rewrite result JSONs.

## Named Caveats

1. Classical ceiling caveat: this is classical exclusion/fence evidence only.
2. Julia workaround caveat: Julia's scaled-integer Z3 lane is exact and honest, but some UNSAT polarity is enforced through exact precheck plus `BoolVal(false)`, not solver-native rational inequality.
3. Szilard scope caveat: the Szilard/Landauer lane is an explicit finite record/erasure coefficient ledger, not a full heat/work thermodynamic cycle ledger.
4. N01 scope caveat: N01 is a finite three-step order predicate, not dynamics.
5. Workspace caveat: `system_v6/sims/carnot_szilard_landauer_ledger_v1/` is currently untracked, so this audit is over live workspace artifacts, not committed evidence.

## Future Citation Rule

Allowed citation: `carnot_szilard_landauer_ledger_v1` is classical ledger-derived exclusion evidence showing that the explicit Carnot/Szilard/Landauer ledgers kill super-Carnot and below-Landauer variants under exact finite ledger constraints, with persisted broken-fence SAT witnesses and all-lane N01 controls, at `scratch_diagnostic` / `classical_baseline` ceiling.

Forbidden citation: any nonclassical admission, bridge claim, manifold/quotient progress, thermodynamic novelty, physics evidence, or proof that the nonclassical stack exceeds the classical fence.
