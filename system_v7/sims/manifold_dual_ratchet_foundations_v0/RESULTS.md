# manifold_dual_ratchet_foundations_v0 RESULTS

classification: `scratch_diagnostic`
claim_ceiling: `QUARANTINE_EXPLORATORY`
promotion_allowed: `false`
formal_admission_allowed: `false`

Bottom-up dual-ratchet foundations diagnostic. No installed terrains are consumed; late structures are called regions.

## Key Numbers

| order | final quotient classes | Hell | active Purgatory | Purgatory->Admitted | Purgatory->Hell | late regions | narrow classes/regions |
|---|---:|---:|---:|---:|---:|---:|---:|
| E_then_G | 42 | 39 | 957 | 5 | 37 | 11 | 33/5 |
| G_then_E | 42 | 39 | 957 | 5 | 37 | 11 | 33/5 |

## Binding Order

| structure | doc reference | E_then_G first bind | G_then_E first bind |
|---|---|---:|---:|
| stable_quotient_plateau | L1 quotient floor / stable quotient | 14 | 14 |
| nondegenerate_metric | L6 metric restricted to survivors | 1 | 1 |
| inhomogeneity | L7 inhomogeneity / curvature-like feedstock | 6 | 4 |
| regions_on_quotient | L12 region discovery from observables | 0 | 0 |

## Hell And Purgatory

- `E_then_G` Hell monotonicity: measured reentry `0`; z3/cvc5 with axioms `unsat/unsat`, erased `sat/sat`.
- `E_then_G` Purgatory flux: gate->purgatory `999`, purgatory->admitted `5`, purgatory->hell `37`, admitted dwell times `[2, 3, 3, 5, 6]`.
- `G_then_E` Hell monotonicity: measured reentry `0`; z3/cvc5 with axioms `unsat/unsat`, erased `sat/sat`.
- `G_then_E` Purgatory flux: gate->purgatory `999`, purgatory->admitted `5`, purgatory->hell `37`, admitted dwell times `[2, 3, 3, 5, 6]`.

## E/G Order Verdict

Order is load-bearing in this bounded run: the recompute orders differ in binding_order_measured. Final quotient count, Purgatory flux, and region count remain the same when not listed.

## Exploration-Width Control

- `E_then_G` wide minus narrow: classes `+9`, regions `+6`, richness drop without wild churn `True`.
- `E_then_G` narrow-control diagnostic: late region count agrees at `5`, but narrow final class count differs numpy/julia `33/42` after the late branch; primary wide-run parity remains the gate.
- `G_then_E` wide minus narrow: classes `+9`, regions `+6`, richness drop without wild churn `True`.
- `G_then_E` narrow-control diagnostic: late region count agrees at `5`, but narrow final class count differs numpy/julia `33/42` after the late branch; primary wide-run parity remains the gate.

## Proto-Regions

### E_then_G

late quotient-region count: `11`

| region | quotient classes | token mass | mean MI bits | mean entropy bits | terminal flow basin |
|---:|---|---:|---:|---:|---|
| 0 | [0, 24, 26] | 3 | 0.000000000 | 0.000000000 | False |
| 1 | [1, 4, 25, 28] | 4 | 0.000000000 | 0.000000000 | False |
| 2 | [2] | 1 | 0.000000000 | 0.000000000 | True |
| 3 | [3, 5, 6, 9, 10, 11, 12, 13, 17, 18, 30, 41] | 12 | 0.333333333 | 0.000000000 | False |
| 4 | [7, 16, 22, 31, 33, 34, 39, 40] | 8 | 0.500000000 | 0.000000000 | False |
| 5 | [8, 20, 35] | 3 | 0.666666667 | 0.000000000 | False |
| 6 | [14] | 1 | 0.000000000 | 0.000000000 | True |
| 7 | [15, 32, 38] | 3 | 0.666666667 | 0.000000000 | False |
| 8 | [19, 21, 36, 37] | 4 | 1.000000000 | 0.000000000 | False |
| 9 | [23, 29] | 2 | 1.000000000 | 0.000000000 | False |
| 10 | [27] | 1 | 0.000000000 | 0.000000000 | True |

### G_then_E

late quotient-region count: `11`

| region | quotient classes | token mass | mean MI bits | mean entropy bits | terminal flow basin |
|---:|---|---:|---:|---:|---|
| 0 | [0, 24, 26] | 3 | 0.000000000 | 0.000000000 | False |
| 1 | [1, 4, 25, 28] | 4 | 0.000000000 | 0.000000000 | False |
| 2 | [2] | 1 | 0.000000000 | 0.000000000 | True |
| 3 | [3, 5, 6, 9, 10, 11, 12, 13, 17, 18, 30, 41] | 12 | 0.333333333 | 0.000000000 | False |
| 4 | [7, 16, 22, 31, 33, 34, 39, 40] | 8 | 0.500000000 | 0.000000000 | False |
| 5 | [8, 20, 35] | 3 | 0.666666667 | 0.000000000 | False |
| 6 | [14] | 1 | 0.000000000 | 0.000000000 | True |
| 7 | [15, 32, 38] | 3 | 0.666666667 | 0.000000000 | False |
| 8 | [19, 21, 36, 37] | 4 | 1.000000000 | 0.000000000 | False |
| 9 | [23, 29] | 2 | 1.000000000 | 0.000000000 | False |
| 10 | [27] | 1 | 0.000000000 | 0.000000000 | True |

## Parity And Boundaries

numpy/Julia parity at 1e-9 on per-step class counts, entropy tables, metric spectra, tier counts, flux totals, binding order, and narrow-control deltas: `True`.

- `Adm_C` excludes entropy; entropy remains downstream readout.
- All geometry/region structure is computed on quotient classes `S/~_P`, not raw state space.
- Hell and Purgatory ledgers are written separately; Hell is permanent, Purgatory mutates and reattempts gates.
