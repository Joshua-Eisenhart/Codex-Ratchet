# Type-1 Engine v0 Results

Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic. promotion_allowed=false.

Parity pass: True at 1e-09
Max abs diff: 8.881784197e-16 at `stage_fingerprints.SeFi.fixed_point_bloch[1]`

## Fingerprints

All 8 distinct: True
Min pairwise distance: 0.597891141104 for ['FeSi', 'SiTe']

| Stage | Terrain | Operator | Casing | Fixed point | Entropy injected generic_a |
|---|---|---|---|---|---|
| TiSe | Se-in | Ti | LOSE | `[0.160680306849, -0.117819152662, 0.788076167804]` | 0.0107868309121 |
| SeFi | Se-in | Fi | win | `[0.275333616256, -0.35505397061, 0.0561406822025]` | -0.0288662618803 |
| NeTi | Ne-in | Ti | WIN | `[0, 0, 0]` | 0.0995432645255 |
| FiNe | Ne-in | Fi | lose | `[-6.31382424799e-16, -2.60055797883e-16, -2.53091092098e-16]` | 0.0241638292568 |
| NiFe | Ni-in | Fe | LOSE | `[0.0889306578482, 0.177328476069, -0.979927765133]` | 0.12904368464 |
| TeNi | Ni-in | Te | lose | `[-0.163198995036, 0.0440086378776, -0.595589216974]` | 0.139527821775 |
| FeSi | Si-in | Fe | WIN | `[3.33877221047e-17, 6.24817300168e-18, 2.83469315284e-17]` | 0.0390199865953 |
| SiTe | Si-in | Te | win | `[-1.19269346711e-17, 1.47837030872e-17, -9.8914467598e-34]` | 0.0724636132205 |

## Order Sensitivity

| Terrain | Outer | Inner | Max norm | Mean norm |
|---|---|---|---:|---:|
| Ne-in | NeTi | FiNe | 0.460719936161 | 0.259889382141 |
| Ni-in | NiFe | TeNi | 0.350432012067 | 0.204361462986 |
| Se-in | TiSe | SeFi | 0.393529418803 | 0.258588868548 |
| Si-in | FeSi | SiTe | 0.379510515354 | 0.205163919156 |

## Traversal Closure

| Traversal | Mean closure | Max closure | Note |
|---|---:|---:|---|
| double_outer_then_inner | 0.755212373476 | 1.26642117878 | no 720 assertion |
| inner | 0.673981990892 | 1.19980830314 | no 720 assertion |
| outer | 0.581299864732 | 0.840212132088 | no 720 assertion |

## Casing Cross-Check

| Stage | Doc casing | xlsx casing | Raw case | Normalized | MBTI |
|---|---|---|---|---|---|
| TiSe | LOSE | LOSE | True | True | ISTP |
| SeFi | win | win | True | True | ESFP |
| NeTi | WIN | WIN | True | True | ENTP |
| FiNe | lose | lose | True | True | INFP |
| NiFe | LOSE | LOSE | True | True | INFJ |
| TeNi | lose | Lose | False | True | ENTJ |
| FeSi | WIN | WIN | True | True | ESFJ |
| SiTe | win | win | True | True | ISTJ |

## Open Gaps

- Terrain parameters and L operators remain candidate terrain math (ATLAS:82-85; ATLAS:118-129).
- MBTI labels come from owner_xlsx_pre_llm, not the four markdown engine docs; labels are not load-bearing.
- Axis-0 Xi/rho_AB bridge is not built here.
- JAX and torch legs are queued, not included in v0.
- No 720 closure is asserted; only measured finite traversal closure norms are reported.

## Verdict

NumPy and Julia legs agree on stage fingerprints, order sensitivity, and traversal trajectories at 1e-9.
This is a source-faithful diagnostic implementation of the Type-1 chart, not promotion evidence.

## Entropy Gradient Axis Probe

Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic. promotion_allowed=false.

Parity pass: True at 1e-09
Max abs diff: 1.33226762955e-15 at `axis_ranking[0].mean_abs_dS_ratio`

Result artifacts:
- `results/entropy_gradient_axis_probe_numpy_results.json`
- `results/entropy_gradient_axis_probe_julia_results.json`

Full per-initial-state dS rows are in each result artifact under `per_leg_dS`.

### Per-Leg Mean dS

| Traversal | Leg | Stage | Terrain | Operator | Mean dS | Mean terrain dS | Mean operator dS | Phase |
|---|---:|---|---|---|---:|---:|---:|---|
| outer_deductive | 1 | TiSe | Se-in | Ti | 0.194793118736 | 0.0302763619461 | 0.164516756789 | heat |
| outer_deductive | 2 | NeTi | Ne-in | Ti | 0.0826090043068 | 0.0320934872218 | 0.050515517085 | heat |
| outer_deductive | 3 | NiFe | Ni-in | Fe | 0.0871376411565 | 0.0871376411565 | -3.17206578464e-17 | heat |
| outer_deductive | 4 | FeSi | Si-in | Fe | 0.0177837296099 | 0.0177837296099 | 1.58603289232e-17 | heat |
| inner_inductive | 1 | SeFi | Se-in | Fi | 0.0851550675742 | 0.0851550675742 | -4.95635278851e-18 | heat |
| inner_inductive | 2 | SiTe | Si-in | Te | 0.182853619438 | 0.105241938199 | 0.0776116812387 | heat |
| inner_inductive | 3 | TeNi | Ni-in | Te | 0.0669640438618 | 0.0295724260448 | 0.037391617817 | heat |
| inner_inductive | 4 | FiNe | Ne-in | Fi | 0.0105070076655 | 0.0105070076655 | -6.34413156929e-17 | heat |

### Axis Sorting Ranking

| Rank | Candidate | Corr(dS) | Mean abs dS ratio | Erased-control percentile | Wins? |
|---:|---|---:|---:|---:|---|
| 1 | operator_class | 0.323828941309 | 2.3620588964 | 84.2857 | False |
| 2 | axis1_eps_terrain | 0.139090679119 | 1.65473442946 | 52.8571 | False |
| 3 | axis2_frame | 0.0181676616916 | 1.02714962806 | 18.5714 | False |

Axis-1 derivation: Funnel/Pit are `dissipation_dominant` because their documented generators present dissipators first with a small Hamiltonian epsilon term; Vortex/Hill are `unitary_dominant` because their documented generators present Hamiltonian flow first with dissipative correction/dephasing. Axis-2 derivation: Se/Ne are direct; Ni/Si are conjugated. Operator class derivation: Ti/Te are T-pinch dephasing channels; Fi/Fe are F-rotation unitary channels.

### Cool/Heat Phase Map

| Traversal | Cool legs | Heat legs | Flat legs | Source-pressure note |
|---|---|---|---|---|
| outer_deductive | none | TiSe, NeTi, NiFe, FeSi | none | 17.5 cool/heat claim cited only; dS labels are measured here. |
| inner_inductive | none | SeFi, SiTe, TeNi, FiNe | none | 17.5 cool/heat claim cited only; dS labels are measured here. |

### Verdict

No candidate wins. Operator class has the largest measured correlation, but it reaches only the 84.285714 percentile against the exact label-erased control, below the 95% win rule. Axis-1 and Axis-2 are weaker. Because no clear winner exists, the dual-SMT gate was intentionally not run; the boolean gate remains open rather than decorative.
