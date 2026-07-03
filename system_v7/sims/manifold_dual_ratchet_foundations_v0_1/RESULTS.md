# manifold_dual_ratchet_foundations_v0_1 RESULTS

classification: `scratch_diagnostic`
claim_ceiling: `QUARANTINE_EXPLORATORY`
promotion_allowed: `false`
formal_admission_allowed: `false`

Bottom-up dual-ratchet foundations diagnostic. No installed terrains are consumed; late structures are called regions.

## R1-R6 Conformance

| primitive | status | evidence |
|---|---|---|
| R1 | present_v0 | finite admitted-token cap, finite generation_ops/probe_family, terminating density-state checks |
| R2 | present_v0 | Adm_C only admits new survivor tokens; Hell is permanent; quotient survivor set plateaus under finite cap |
| R3 | present_v0 | Adm_C reads admitted signatures, history/Purgatory/Hell ledgers, and prior induced G_t |
| R4 | present_v0 | N01 order-sensitive update pairs must remain probe-distinguishable under finite quotient probes |
| R5 | added_v0_1 | mutated PARK/Purgatory replays are logged as fresh candidate ids with lineage; no implicit reintroduction |
| R6 | added_v0_1_OPEN_CHOICE | Purgatory is PARK; mu is monotone exclusion-event progress count; mu_choice: OPEN-CHOICE exclusion-event monotone: mu = hell_count + cumulative gate_to_purgatory + cumulative purgatory_to_admitted + cumulative purgatory_to_hell |

PARK status formalized: `PURGATORY == PARK`.

## Key Numbers

| order | final quotient classes | Hell | active Purgatory | Purgatory->Admitted | Purgatory->Hell | late regions | narrow classes/regions |
|---|---:|---:|---:|---:|---:|---:|---:|
| E_then_G | 42 | 39 | 957 | 5 | 37 | 11 | 33/5 |
| G_then_E | 42 | 39 | 957 | 5 | 37 | 11 | 33/5 |

## Binding Order

| structure | doc reference | E_then_G first bind | G_then_E first bind |
|---|---|---:|---:|
| stable_quotient_plateau | L1 quotient floor / stable quotient | 14 | 14 |
| cut_lattice_on_quotient | L8 cut lattice on quotient classes | 0 | 0 |
| axis0_phi0_readability | Axis-0 Phi_0 readout after Xi candidate density | 0 | 0 |
| nondegenerate_metric | L6 metric restricted to survivors | 1 | 1 |
| inhomogeneity | L7 inhomogeneity / curvature-like feedstock | 6 | 4 |
| regions_on_quotient | L12 region discovery from observables | 0 | 0 |

Axis-0 readability is reported as bound only after the quotient cut lattice exists: `E_then_G=True`, `G_then_E=True`.

## Cut Lattice And Phi_0

Cut definition: bipartition A|B of current quotient class ids; complements are identified by requiring the minimum class id in A.

OPEN-CHOICE: finite quotient-class carrier; exact only up to cut_lattice_exact_max_classes, singleton frontier above that cap.

| order | late exact total cut count | late evaluated cuts | late mode |
|---|---:|---:|---|
| E_then_G | 2199023255551 | 42 | bounded_singleton_frontier_OPEN_CHOICE |
| G_then_E | 2199023255551 | 42 | bounded_singleton_frontier_OPEN_CHOICE |

### Phi_0 Stabilization

| order | Xi_pt first stable | Xi_ref first stable | Xi_hist first stable | Xi_pt late Phi_0 | Xi_ref late Phi_0 | Xi_hist late Phi_0 |
|---|---:|---:|---:|---:|---:|---:|
| E_then_G | 14 | 14 | 14 | -0.108238422 | -0.108238422 | -0.108238422 |
| G_then_E | 14 | 14 | 14 | -0.108238422 | -0.108238422 | -0.108238422 |

### Late Candidate Agreement Matrix

#### E_then_G

| candidate | Xi_pt | Xi_ref | Xi_hist |
|---|---|---|---|
| Xi_pt | True | True | True |
| Xi_ref | True | True | True |
| Xi_hist | True | True | True |
#### G_then_E

| candidate | Xi_pt | Xi_ref | Xi_hist |
|---|---|---|---|
| Xi_pt | True | True | True |
| Xi_ref | True | True | True |
| Xi_hist | True | True | True |

## Hell And Purgatory

- `E_then_G` Hell monotonicity: measured reentry `0`; z3/cvc5 with axioms `unsat/unsat`, erased `sat/sat`.
- `E_then_G` Purgatory flux: gate->purgatory `999`, purgatory->admitted `5`, purgatory->hell `37`, admitted dwell times `[2, 3, 3, 5, 6]`.
- `G_then_E` Hell monotonicity: measured reentry `0`; z3/cvc5 with axioms `unsat/unsat`, erased `sat/sat`.
- `G_then_E` Purgatory flux: gate->purgatory `999`, purgatory->admitted `5`, purgatory->hell `37`, admitted dwell times `[2, 3, 3, 5, 6]`.

## SMT Theorem Statements

| theorem | z3 real | z3 erased | cvc5 real | cvc5 erased | flip |
|---|---|---|---|---|---|
| mu_monotonicity | unsat | sat | unsat | sat | True |
| e_not_in_adm | unsat | sat | unsat | sat | True |

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
- `Phi_0` is downstream of quotient cut-lattice formation and never an admission predicate.
- `Xi_pt`, `Xi_ref`, and `Xi_hist` are held as competitors; their signs are not merged.
- All geometry/region structure is computed on quotient classes `S/~_P`, not raw state space.
- Hell and Purgatory ledgers are written separately; Hell is permanent, Purgatory mutates and reattempts gates.

## OPEN-CHOICE Register

- R6 mu: exclusion-event monotone, not a final theorem measure.
- Cut lattice carrier: quotient-class bipartitions; exact all-bipartitions capped by `cut_lattice_exact_max_classes`, then singleton-frontier readout with exact total cut count retained.
- Xi density construction: diagonal two-bit cut-density state from quotient-side mass and cross-edge coupling.
- Weights: uniform `w_r` and `w_c` defaults.
- Xi_ref reference class: class `0` in the quotient-id convention.
