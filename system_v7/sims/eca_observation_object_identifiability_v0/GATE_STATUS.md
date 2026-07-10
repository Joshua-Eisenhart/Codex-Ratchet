# Gate Status

## Evidence Gates

| Gate | Verdict | Evidence |
|---|---|---|
| Preregistration and frozen manifests | PASS | 13/13 checks; all four manifest hashes reproduce |
| Julia exact lane | PASS | 2,655 records; all local tests pass |
| JAX exact lane | PASS | 2,655 records; all local tests pass |
| Cross-runtime required-field comparison | PASS | zero mismatches and zero missing fields |
| Fixture-budget universe | PASS | exact 531 by 5 ordering; no duplicate or omitted row |
| Source/result freshness | PASS | actual and declared Julia/JAX source hashes match |
| Structural monotonicity | PASS | version spaces and ambiguity are nonincreasing |
| Receipt mutation attacks | PASS | four field mutations and duplicate-row mutation detected |
| Controller local rerun | PASS | all five controller gates pass |
| Independent engine replay | PASS | Julia and JAX replay ledgers match stored ledger hash |
| Fresh fabrication audit | PASS WITH CAVEAT | no fabrication found; controller is not a third semantic engine |

The generic Python sim linter reports zero violations for `run_jax.py`. Its
attempt to parse `run_julia.jl` as Python reports a parse error and is not an
applicable Julia gate.

## Scientific Gates

| Budget | Consensus candidate | Main failure |
|---:|---|---|
| 1 | NO | 69.47% global coverage; 20.98% fixture floor |
| 2 | NO | 77.68% global coverage; 20.98% fixture floor |
| 4 | NO | 69.74% fixture floor; only 70 non-singleton fixtures |
| 8 | NO | every fixture system identified |
| 16 | NO | every fixture system identified |

No two consecutive budgets pass. The perception-like regime and future neural
benchmark remain blocked.

## Public Status

`passes local rerun`

The packet is intentionally `scratch_diagnostic`, with
`promotion_allowed=false` and `formal_admission_allowed=false`. It is not
`canonical by process` and cannot support claims about QIT stages, four
substages, the 16-by-4-by-2 schedule, general perception, MMMs, ontologies,
Axis0, physics, life, or consciousness.
