# axis_relation_matrix_probe_v0 RESULTS

classification: `scratch_diagnostic`
claim_ceiling: `QUARANTINE_EXPLORATORY`
promotion_allowed: `false`
formal_admission_allowed: `false`

## Readout Scope

Rows: 56 = 8 Type-1 stages across both traversals x 7 fixed probe states.

- a1: operator factor, Fi/Fe unitary=1 and Ti/Te proper CPTP/GKSL=0.
- a2: terrain frame, Ni/Si conjugated=1 and Se/Ne direct=0.
- a4: traversal order, outer/deductive=0 and inner/inductive=1.
- a5: operator family, F=1 and T=0.
- a6: local precedence, operator-first `terrain_after_operator`=1 and terrain-first `operator_after_terrain`=0.
- b0: sign of probe-state `r_z`; zero is retained as 0 and excluded from b6 rows.
- b3: chart-role loop, outer=+1 and inner=-1.
- b6: derived only where b0 is nonzero as `-b0*b3`.
- a0: undefinable here because Xi/cut bridge or an admitted a0 proxy is not present.

## Laws

- b6 = -b0*b3: `True` over 48 defined rows.
- a0 = a1 XOR a2: `skipped_undefinable`.

## Relation Matrix

| pair | n | NMI | corr | null95 NMI | null95 abs corr | verdict |
|---|---:|---:|---:|---:|---:|---|
| a1-a2 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a1-a4 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a1-a5 | 56 | 1.000000 | 1.000000 | 0.094072 | 0.357143 | dependent_above_95pct_null |
| a1-a6 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a1-b0 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| a1-b3 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a1-b6 | 48 | 0.000000 | 0.000000 | 0.081704 | 0.333333 | independent_at_this_depth |
| a2-a4 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a2-a5 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a2-a6 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a2-b0 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| a2-b3 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a2-b6 | 48 | 0.000000 | 0.000000 | 0.081704 | 0.333333 | independent_at_this_depth |
| a4-a5 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a4-a6 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a4-b0 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| a4-b3 | 56 | 1.000000 | -1.000000 | 0.136879 | 0.428571 | dependent_above_95pct_null |
| a4-b6 | 48 | 0.000000 | 0.000000 | 0.261715 | 0.583333 | independent_at_this_depth |
| a5-a6 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a5-b0 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| a5-b3 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a5-b6 | 48 | 0.000000 | 0.000000 | 0.081704 | 0.333333 | independent_at_this_depth |
| a6-b0 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| a6-b3 | 56 | 0.000000 | 0.000000 | 0.094072 | 0.357143 | independent_at_this_depth |
| a6-b6 | 48 | 0.000000 | 0.000000 | 0.081704 | 0.333333 | independent_at_this_depth |
| b0-b3 | 56 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| b0-b6 | 48 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | independent_at_this_depth |
| b3-b6 | 48 | 0.000000 | 0.000000 | 0.261715 | 0.583333 | independent_at_this_depth |

## Conflation Stress Test

Reachable (a4, a6, b3) combinations: 4 / 8.
Reachable combinations: `[[0, 0, 1], [0, 1, 1], [1, 0, -1], [1, 1, -1]]`.

Verdict: fewer than 8 combinations are reachable. In this built Type-1 chart, a4 and b3 are structurally coupled by the outer/deductive and inner/inductive assignment; a6 remains separately realized across both loops.

## SMT Gate

Above-null relation pairs gated: `[['a1', 'a5'], ['a4', 'b3']]`.
SMT status: `ran`.

## Parity

numpy/Juliа parity at 1e-9: `True`.
Parity diffs: `[]`.

## Honest Verdict Counts

- law: 1
- dependent above 95% null: 2
- independent at this depth: 26
- undefinable: 1

Generated: 2026-07-03T19:52:48Z
