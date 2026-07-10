# Dual-Ratchet Four-Count Nonforcing SMT v0 Results

Status: fresh deterministic local rerun passed at the finite
`scratch_diagnostic` ceiling.

## Verdict

```text
FINITE_COUNT_FREE_AXIOMS_NONFORCING_ONLY_CARDINALITY_CONTAMINATED_CONTROLS_FORCE_FOUR
```

Z3 `4.16.0` and cvc5 `1.3.3` agreed on every one of 105 queries per solver.
The solver-free validator replayed 78 SAT models from each solver. It accepted
no model on trust and read no solver library.

## Baseline Countermodels

Both solvers admitted every searched length:

```text
[2, 3, 4, 5, 6, 7, 8]
```

The raw receipts include complete sign-indexed transition tables and traces
for each model. Compact baseline witnesses are:

| L | Z3 word/sign | Z3 closed trace | cvc5 word/sign | cvc5 closed trace |
|---:|---|---|---|---|
| 2 | `GE` / up | `0,5,0` | `EG` / up | `7,5,7` |
| 3 | `GGE` / up | `0,5,5,0` | `EGE` / up | `7,7,5,7` |
| 4 | `EGGG` / down | `4,5,4,8,4` | `EGGE` / up | `7,6,8,5,7` |
| 5 | `EEGEG` / down | `4,2,8,5,5,4` | `EGEGE` / up | `7,5,6,7,5,7` |
| 6 | `EEEGEE` / down | `1,8,0,0,4,2,1` | `EEGEGE` / up | `7,6,4,4,7,2,7` |
| 7 | `GGGEGEE` / up | `7,5,1,1,0,0,2,7` | `EEEEGEE` / up | `7,7,7,7,7,2,5,7` |
| 8 | `EGEGEEEE` / up | `8,7,1,3,0,5,8,7,8` | `EEEEEEGE` / up | `7,6,7,6,7,6,7,5,7` |

Here `G` and `E` are anonymous work kinds, not source operator labels. Each
listed non-four model is an explicit countermodel to the claim that the
baseline forces `L=4` in this formalization.

## Candidate Axioms

Each candidate was added to the baseline alone:

| Candidate | Admitted lengths in both solvers | Forces only 4? |
|---|---|---:|
| Cyclic alternation | `2,4,6,8` | false |
| Every-leg primary progress | `2,3,4,5,6,7,8` | false |
| Simple phase cycle | `2,3,4,5,6,7,8` | false |
| No early return | `2,3,4,5,6,7,8` | false |
| Noncommutation witness on cycle | `2,3,4,5,6,7,8` | false |
| Opposite sign breaks closure | `2,3,4,5,6,7,8` | false |
| Selected maps bijective | `2,3,4,5,6,7,8` | false |
| Any one kind flip breaks closure | `2,3,4,5,6,7,8` | false |
| Any one leg deletion breaks closure | `2,3,4,5,6,7,8` | false |
| Reverse word breaks closure | `2,3,4,5,6,7,8` | false |

No preregistered clean candidate forced `L=4` in `2..8`.

## Contamination Controls

All four prohibited controls admitted exactly `[4]` in both solvers:

| Rejected control | Why it carries four |
|---|---|
| Exactly two of each kind | `L = 2 + 2` |
| Binary x binary exact coverage | exactly four covered pairs |
| Explicit four-step word | states the four positions and order |
| Exactly four legs | states the desired count |

Thus, among the preregistered additions, only cardinality-contaminated premises
forced four.

## Validation

- Solver queries: `105` per solver, `210` total.
- SAT models independently replayed: `78` per solver, `156` total.
- Cross-solver status disagreements: `0`.
- Unknown solver results: `0`.
- Malformed-input self-tests: `6/6` rejected as intended.
- Object-preservation validator: `ok: true`, zero errors, zero warnings.
- Deterministic rerun: all five pass-A/pass-B artifact hashes matched.

Canonical artifact hashes:

```text
z3_raw_solver_receipt.json       c6b6a79269c0a549045140f7ab868c7842de501bd3e8a2cbb9ef443a5fe95873
cvc5_raw_solver_receipt.json     3264ed3bd64a8bf74b57c599f082f6f1b3660845d3a6b0abafbebb2451a5d3b8
agreement_validation.json        9a2f5cbe68013ac93803a2a5dfd97f1c2d7766ff73463af80e71355f56fee689
malformed_input_selftest.json    d6866ac734c2c01e27262a5eee51c9a048d30a52e30b458acc950f34ee177f5b
wizard_v4_3_validation.json      f54effb76a53ca913a7b8b72ca1d8cae20bafd9c7d454aba7b8b798c11727502
deterministic_rerun_hashes.json  c246a2c5ab5441b766eb841dc4ce8a7b7ac9de588a52f8a6bdcbe2943ec4ca5c
```

## Meaning For `16 x 4`

This result does not alter the source definition. It says the tested
count-free temporal properties do not independently earn its multiplier four.
The source-defined 16 slots can still be expanded by the four source operators
as a declared schedule or candidate carrier, but this finite scout supplies no
derivation that makes that `16 x 4` schedule necessary.

No theorem is claimed beyond the nine-state carrier, the explicit formulas in
`spec.json`, and the bounded search `L=2..8`.
