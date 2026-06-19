# Nonassociativity Branches

Claim ceiling: scratch/formal scout evidence only. Every branch here is fenced with `promotion_allowed=false` and `formal_admission_allowed=false`. These receipts do not admit final M(C), M(C+NA), PEPS3D, Axis0, physics, engine, bridge, gravity, or consciousness.

## Source Boundary

Primary sources:

- `/Users/joshuaeisenhart/.claude/projects/-Users-joshuaeisenhart-Codex-Ratchet/memory/project_nonassoc_three_branches_dual_backend.md`
- `/Users/joshuaeisenhart/.claude/projects/-Users-joshuaeisenhart-Codex-Ratchet/memory/reference_8_operators_math_geometry_stack_3qubit.md`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/three_spinor_associator_scout_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/nonassoc_basin_compare_scout_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/nc_vs_nonassoc_setmap_scout_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/three_spinor_associator_scout_jax_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/three_spinor_associator_scout_julia_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/nonassoc_basin_compare_scout_julia_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/nc_vs_nonassoc_setmap_scout_julia_results.json`

## Conceptual Spine

Non-associativity turns M(C) from an ordered spinor-network state space into a bracket-sensitive spinor-network history space.

Core readout:

`alpha(A,B,C; psi) = ((A*B)*C)psi - (A*(B*C))psi`

where `*` is compose-then-project-back-into-admissible-surface. The non-associativity lives in constraint return / cell gluing, not in raw matrix multiplication.

Cell hierarchy:

| Level | Readout |
|---|---|
| Edge | order / noncommutation, two inputs. |
| Face | holonomy / loop defect. |
| 3-cell | associator / bracketing defect, three inputs. |

This is why the three-input/three-qubit minimum matters. The session memory records convergence: 3 qubits is the minimum for both irreducible Weyl chirality and the non-associative associator.

## B1: Three-Spinor Associator Scout

Result path:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/three_spinor_associator_scout_results.json`

Mirror paths:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/three_spinor_associator_scout_jax_results.json`
- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/three_spinor_associator_scout_julia_results.json`

Receipt state:

| Field | Value |
|---|---|
| `classification` | `scratch_diagnostic` in canonical result; mirror uses `formal_scout` but still fenced. |
| `all_pass` | `true` |
| `promotion_allowed` | `false` |
| `formal_admission_allowed` | `false` |
| `parity_max_diff` | `1.1102230246251565e-16` |

Key numbers:

| Readout/control | Value |
|---|---|
| `positive.product_gap` | `2.0` |
| `positive.spinor_gap` | `2.0` |
| `positive.basis_probe_max_abs` | `0.977046201384958` |
| `positive.density_gap_fro` | `0.0` |
| raw matrix associativity gap | `0.0` |
| density sign gap | `0.0` |
| spinor sign gap | `2.0` |

Plain result:

The finite 3-spinor scout sees a nonzero lifted associator for the chosen operation triple. Raw matrix composition, quotient erasure, density-only readout, quaternionic restriction, and repeated-input alternativity controls collapse as expected.

Carrier lesson:

`rho=|psi><psi|` erases this associator witness. The carrier must preserve finite spinor-network sign/bracket information; density-only quotient is not enough.

Verdict memory:

Grok and Gemini verdicts were `GENUINE` for B1.

## B2: Nonassociative Basin Compare Scout

Result path:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/nonassoc_basin_compare_scout_results.json`

Mirror path:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/nonassoc_basin_compare_scout_julia_results.json`

Receipt state:

| Field | Value |
|---|---|
| `classification` | `scratch_diagnostic` |
| `all_pass` | `true` |
| `promotion_allowed` | `false` |
| `formal_admission_allowed` | `false` |
| `parity_max_diff` | `3.552713678800501e-15` |

Key verdict booleans:

| Verdict | Value |
|---|---|
| `assoc_required_H_only` | `true` |
| `na_not_required_HO` | `true` |
| `basins_differ_on_NA_axis` | `true` |
| `computed_admissibility_no_lookup` | `true` |
| `S_excluded_by_norm_not_associativity` | `true` |
| `start_independent` | `true` |

Plain result:

The associativity-required basin keeps `{H}`. The non-associativity-not-required basin keeps `{H,O}`. Sedenions remain excluded by zero divisors / norm failure, not by associativity alone.

Repair note:

Initial B2 had a real audit problem: Gemini flagged the erased-associativity-axis control as circular, because it painted the object to match the detector. The repair replaced lookup-style admission with computed predicates:

- N01 noncommutativity;
- norm multiplicativity / no zero divisors;
- associativity toggle;
- falsifiable control where dropping associativity admits `O` but excludes `S`.

Verdict memory:

After repair, Grok and Gemini both re-audited B2 as `GENUINE`.

## B3: NC Vs Nonassoc Set-Map Scout

Result path:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/nc_vs_nonassoc_setmap_scout_results.json`

Mirror path:

- `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/nc_vs_nonassoc_setmap_scout_julia_results.json`

Receipt state:

| Field | Value |
|---|---|
| `classification` | `scratch_diagnostic` |
| `all_pass` | `true` |
| `promotion_allowed` | `false` |
| `formal_admission_allowed` | `false` |
| `parity_max_diff` | `1.4210854715202004e-14` |

Key numbers:

| Row | Number |
|---|---|
| H associativity gap | `1.3322676295501878e-15` |
| H commutativity gap | `5.4807763267513705` |
| O associativity gap | `26.18002152586002` in JAX, `26.180021525860013` in Julia |
| O alternativity gap | `6.358389842764979e-15` in JAX, `4.772667874287579e-15` in Julia |
| J3(O) associativity gap | `32.35375677134946` in JAX, `32.35375677134947` in Julia |
| S associativity gap | about `63.411012480716884` |
| S explicit zero product norm | `0.0` |

Plain result:

Finite witnesses separate:

- `H` and `M2(C)` as noncommutative associative rows;
- `O` as alternative nonassociative without a finite zero-product witness;
- `J3(O)` as a formally real nonassociative Jordan observable;
- `S` as the explicit zero-divisor graveyard row;
- `R/C` as commutative controls below the noncommutative line.

Verdict memory:

Grok and Gemini verdicts were `GENUINE` for B3.

## What These Branches Earn

They earn bounded scratch evidence for:

- associator readout visible on a finite spinor-network carrier;
- density quotient erasure of that associator;
- non-associativity changing a finite admissibility basin under repaired controls;
- set-map distinction among `H`, `O`, `J3(O)`, and `S`.

They do not earn:

- final M(C);
- M(C+NA);
- PEPS3D admission;
- octonion primitive carrier admission;
- QIT-engine admission;
- Axis0;
- bridge;
- physics;
- gravity;
- consciousness.
