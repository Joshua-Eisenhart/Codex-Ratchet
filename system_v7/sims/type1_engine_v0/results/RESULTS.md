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
