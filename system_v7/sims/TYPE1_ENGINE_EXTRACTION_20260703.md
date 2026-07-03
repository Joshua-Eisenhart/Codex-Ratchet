| Pattern | Direction | Terrain order | Axis flip sequence |
|---|---|---|---|
| Inductive | CW | `Se -> Si -> Ni -> Ne` | `Large -> small -> Large -> small` (`IGT:464-469`) |
| Deductive | CCW | `Se -> Ne -> Ni -> Si` | `small -> Large -> small -> Large` (`IGT:464-469`) |

The atlas repeats the chart lock: Inductive `Se -> Si -> Ni -> Ne`; Deductive `Se -> Ne -> Ni -> Si` (`ATLAS:156-179`).

## F. Type-2 Boundary

Type 2 is the mirror/right/out side: `right, flux OUT, H = -H0` (`IGT:491`). Terrains are `Se-out` Cannon, `Ne-out` Spiral, `Ni-out` Source, `Si-out` Citadel (`IGT:491-499`; `ATLAS:111-114`). The docs say what changes between types is “Hamiltonian sign flips, rotation axis flips, z-attractor flips, jump operator flips (sigma_- -> sigma_+), projector frame rotates” and that these are “Different channels, not relabelings” (`IGT:500`). Type-2 outer is inductive and inner deductive (`IGT:517-525`; `ATLAS:235-249`).

## G. Open Gaps

OPEN: Terrain generators are candidate, not closed. The atlas says the 8-terrain equations are one candidate realization and “not settled math” (`ATLAS:82-85`); exact `L` operators and epsilon parameters need sim testing (`ATLAS:118-129`).

OPEN: The source docs do not specify MBTI labels for Type-1 stages in the requested four-doc set (`IGT:527-534`; `ATLAS:217-231`).

OPEN: Axis-0 bridge remains the largest gap: without `Xi` mapping geometry to `rho_AB`, Axis 0 is scalar readout, not full functional (`IGT:215-218`; `IGT:656-658`).

OPEN: Axis-4 taijitu spin direction is open; runtime math is strong but symbolic spin assignment is not closed (`IGT:300-326`).

OPEN: Axis-3 has competing readings; inner/fiber vs outer/base is current strongest, while chirality, Type1/Type2 inversion, and flux in/out remain alternatives requiring discriminator tests (`IGT:273-292`; `ATLAS:293-304`).

OPEN: Signed functional role names are exploratory, not canon. The exact facts are fixed operator map plus up/down precedence; projector/quantizer, ascent/descent, entrainment/damping, broadcast/filtering are hypotheses (`SIGNED:997-1058`).

OPEN: Full 64 closure is not proven. The atlas says chart/runtime/hexagram 64 layers are schedule/index surfaces and must not claim closure or ontology (`ATLAS:264-270`; `ATLAS:331-345`).

## H. Delta vs Current Sims

Current `oracle_targets.py` is related but not identical. It says the active validation contract is “16 stages” as `8 terrain generators (t0..t7) x their 2 native operators`, with both terrain-first/down and operator-first/up outputs per row (`ORACLE:5-16`). It is `scratch_diagnostic; promotion_allowed=false` (`ORACLE:18-20`).

Same objects: current oracle uses density matrices/Pauli matrices (`ORACLE:24-28`), exact Ti/Te pinching and Fi/Fe unitary channels (`ORACLE:72-83`), 8 terrain generator indices with eps/kind/pole (`ORACLE:42-45`, `ORACLE:50-61`), and the same native split `{Ti,Fi}` for t0,t1,t4,t5 vs `{Te,Fe}` for t2,t3,t6,t7 (`ORACLE:42-45`), matching the direct/conjugated native rule (`LEDGER:157-173`).

Different indexing/contract: the source Type-1 spec is a named chart over `Se-in/Ne-in/Ni-in/Si-in`, outer/inner loops, exact tokens, and WIN/LOSE casing (`IGT:527-534`; `ATLAS:217-231`). The oracle rows are numeric `(t, op)` rows and do not carry source token names, Type-1 outer/inner casing, traversal labels, or MBTI (`ORACLE:88-102`). Therefore it is the same operator/terrain ingredient family at a lower runtime-contract layer, but not a verbatim Type-1 stage chart.

Current engines consume that oracle structure: PyTorch builds `stage_list = [(t, o) for t in range(8) for o in NATIVE[t]]` and computes down/up compositions (`torch_engine.py:79-92`); JAX does the same (`jax_engine.py:88-99`); Julia does the same (`julia_engine.jl:105-114`).

Current `sixteen_stage_engine.json` explicitly labels its construction as “8 terrains x 2 native operators each, signed Axis-6 order” and keeps `scratch_diagnostic; promotion_allowed=false` (`system_v7/constraint_core/data_json/sixteen_stage_engine.json:1-3`, `:102-112`). So: same base terrain/operator objects, relabeled/indexed as `t0..t7 x native op`, with source chart fields missing unless a later mapping layer adds them.


tokens used
249,609
**Source-Faithful Type-1 Engine Extraction**

Aliases: `IGT` = `igt-pattern-explicit-math-reference.md`; `SIGNED` = `QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`; `ATLAS` = `ENGINE_64_SCHEDULE_ATLAS.md`; `LEDGER` = `TERRAIN_LAW_LEDGER.md`; `ORACLE` = `system_v7/constraint_core/engines/oracle_targets.py`.

## A. Type-1 Terrains

Type 1 is “left, flux IN, H = +H0” (`IGT:482`) / flux `IN` (`ATLAS:135-141`).

| Terrain | Name | Flux | Jungian function | Exact generator / candidate law |
|---|---|---|---|---|
| `Se-in` | Funnel | IN | Se | `rho_dot = Sigma D[L_k](rho) - i epsilon[H0,rho]` (`IGT:484-487`); atlas form `Sigma_k D[L_k](rho) - i epsilon_F [H0, rho]` (`ATLAS:103-108`). |
| `Ne-in` | Vortex | IN | Ne | `rho_dot = -i[H0,rho] + epsilon Sigma D[L_k](rho)` (`IGT:487`); atlas form `-i[H0, rho] + epsilon_V Sigma_k D[L_k](rho)` (`ATLAS:108`). |
| `Ni-in` | Pit | IN | Ni | `rho_dot = D[sqrt(gamma)sigma_-](rho) - i epsilon[H0,rho]` (`IGT:488`); atlas form `D[L_P](rho) - i epsilon_P [H0, rho]` (`ATLAS:109`). |
| `Si-in` | Hill | IN | Si | `rho_dot = -i[H_C,rho]+Sigma kappa_j(P_j rho P_j - 1/2{P_j,rho})` (`IGT:489`); atlas form `-i[H_C, rho] + Sigma_j kappa_j (P_j rho P_j - 1/2(P_j rho + rho P_j))` (`ATLAS:110`). |

Scratch Bloch-map parameters are given only as scratch forms: Se `.13`, `.78`, `.22*.86`; Ne `.94`, `.47`; Ni `.09`, `.70`, `.30*.92`; Si `.19`, `.58` (`IGT:486-489`). The atlas explicitly says this is “one candidate QIT realization” and “not settled math” (`ATLAS:82-85`).

## B. Four Operators

Quoted compact table (`IGT:471-479`):

| Operator | Channel | Generator | Class | Native terrains |
|---|---|---|---|---|
| Ti | `(1-q1)rho + q1(P0 rho P0+P1 rho P1)` | `(kappa1/2)(sigma_z rho sigma_z-rho)` | z-dephasing | Se, Ne direct (`IGT:475`) |
| Te | `(1-q2)rho + q2(Q+ rho Q+ + Q- rho Q-)` | `(kappa2/2)(sigma_x rho sigma_x-rho)` | x-dephasing | Ni, Si conjugated (`IGT:476`) |
| Fi | `U_x(theta)rho U_x(theta)^dagger` | `-i[(omega3/2)sigma_x, rho]` | x-rotation | Se, Ne direct (`IGT:477`) |
| Fe | `U_z(phi)rho U_z(phi)^dagger` | `-i[(omega4/2)sigma_z, rho]` | z-rotation | Ni, Si conjugated (`IGT:478`) |

Exact operator definitions: `Ti_q(rho) = (1 - q_1) rho + q_1 E_z(rho)` with `E_z(rho)=P_0 rho P_0 + P_1 rho P_1` (`SIGNED:136-148`); `Te_q(rho) = (1 - q_2) rho + q_2 E_x(rho)` with `E_x(rho)=Q_+ rho Q_+ + Q_- rho Q_-` (`SIGNED:284-296`); `Fi_theta(rho)=U_x(theta) rho U_x(theta)^dagger`, `U_x(theta)=exp(-i theta sigma_x / 2)` (`SIGNED:437-445`); `Fe_phi(rho)=U_z(phi) rho U_z(phi)^dagger`, `U_z(phi)=exp(-i phi sigma_z / 2)` (`SIGNED:549-557`).

Native assignment is explicitly the i/e split: `Ti, Fi` native to direct-frame `Se, Ne`; `Te, Fe` native to conjugated-frame `Ni, Si` (`LEDGER:157-173`).

## C. Eight Signed Operators

Signed means precedence/action-side, not new maps: `up = operator-first ordered word`, `down = terrain-first ordered word` (`SIGNED:20-27`). Axis-6 action side is `UP = L_A(rho)=A rho`, `DOWN = R_A(rho)=rho A`; token level is `up = operator-first word`, `down = terrain-first word` (`SIGNED:897-922`). Composition convention: operator-first `JP` means `Phi_JP = T_P o J`; terrain-first `PJ` means `Phi_PJ = J o T_P` (`SIGNED:955-987`).

Exact stage-map table (`SIGNED:1162-1175`):

| Signed variant | Exact compositions |
|---|---|
| `Ti^up` | `Phi_TiSe = T_Se o Ti_q`; `Phi_TiNe = T_Ne o Ti_q` |
| `Ti^down` | `Phi_SeTi = Ti_q o T_Se`; `Phi_NeTi = Ti_q o T_Ne` |
| `Te^up` | `Phi_TeNi = T_Ni o Te_q`; `Phi_TeSi = T_Si o Te_q` |
| `Te^down` | `Phi_NiTe = Te_q o T_Ni`; `Phi_SiTe = Te_q o T_Si` |
| `Fi^up` | `Phi_FiNe = T_Ne o Fi_theta`; `Phi_FiSe = T_Se o Fi_theta` |
| `Fi^down` | `Phi_NeFi = Fi_theta o T_Ne`; `Phi_SeFi = Fi_theta o T_Se` |
| `Fe^up` | `Phi_FeSi = T_Si o Fe_phi`; `Phi_FeNi = T_Ni o Fe_phi` |
| `Fe^down` | `Phi_SiFe = Fe_phi o T_Si`; `Phi_NiFe = Fe_phi o T_Ni` |

IGT’s same table in `Phi_T(...)` notation: `Ti↑ = Phi_T(Ti(rho))`, `Ti↓ = Ti(Phi_T(rho))`, `Te↑ = Phi_T(Te(rho))`, `Te↓ = Te(Phi_T(rho))`, `Fi↑ = Phi_T(Fi(rho))`, `Fi↓ = Fi(Phi_T(rho))`, `Fe↑ = Phi_T(Fe(rho))`, `Fe↓ = Fe(Phi_T(rho))` (`IGT:502-513`).

## D. Type-1 Eight Stages

Type-1 outer loop is deductive `FeTi`; inner loop is inductive `TeFi` (`IGT:517-525`; `ATLAS:226-231`).

| Terrain | Outer stage | Outer order | Outer result | Inner stage | Inner order | Inner result |
|---|---|---|---|---|---|---|
| `Se-in` | `TiSe` | `Se-in(Ti(rho))` = terrain(operator(rho)) | `LOSE` | `SeFi` | `Fi(Se-in(rho))` = operator(terrain(rho)) | `win` (`IGT:529-532`; `ATLAS:219-222`) |
| `Ne-in` | `NeTi` | `Ti(Ne-in(rho))` = operator(terrain(rho)) | `WIN` | `FiNe` | `Ne-in(Fi(rho))` = terrain(operator(rho)) | `lose` (`IGT:532`; `ATLAS:222`) |
| `Ni-in` | `NiFe` | `Fe(Ni-in(rho))` = operator(terrain(rho)) | `LOSE` | `TeNi` | `Ni-in(Te(rho))` = terrain(operator(rho)) | `lose` (`IGT:533`; `ATLAS:223`) |
| `Si-in` | `FeSi` | `Si-in(Fe(rho))` = terrain(operator(rho)) | `WIN` | `SiTe` | `Te(Si-in(rho))` = operator(terrain(rho)) | `win` (`IGT:534`; `ATLAS:224`) |

MBTI labels: OPEN in the four requested docs. They provide IGT casing and terrain/operator tokens, not MBTI labels for the Type-1 chart (`IGT:527-534`; `ATLAS:217-231`).

## E. Traversals

The two traversals are explicitly:

| Pattern | Direction | Terrain order | Axis flip sequence |
|---|---|---|---|
| Inductive | CW | `Se -> Si -> Ni -> Ne` | `Large -> small -> Large -> small` (`IGT:464-469`) |
| Deductive | CCW | `Se -> Ne -> Ni -> Si` | `small -> Large -> small -> Large` (`IGT:464-469`) |

The atlas repeats the chart lock: Inductive `Se -> Si -> Ni -> Ne`; Deductive `Se -> Ne -> Ni -> Si` (`ATLAS:156-179`).

## F. Type-2 Boundary

Type 2 is the mirror/right/out side: `right, flux OUT, H = -H0` (`IGT:491`). Terrains are `Se-out` Cannon, `Ne-out` Spiral, `Ni-out` Source, `Si-out` Citadel (`IGT:491-499`; `ATLAS:111-114`). The docs say what changes between types is “Hamiltonian sign flips, rotation axis flips, z-attractor flips, jump operator flips (sigma_- -> sigma_+), projector frame rotates” and that these are “Different channels, not relabelings” (`IGT:500`). Type-2 outer is inductive and inner deductive (`IGT:517-525`; `ATLAS:235-249`).

## G. Open Gaps

OPEN: Terrain generators are candidate, not closed. The atlas says the 8-terrain equations are one candidate realization and “not settled math” (`ATLAS:82-85`); exact `L` operators and epsilon parameters need sim testing (`ATLAS:118-129`).

OPEN: The source docs do not specify MBTI labels for Type-1 stages in the requested four-doc set (`IGT:527-534`; `ATLAS:217-231`).

OPEN: Axis-0 bridge remains the largest gap: without `Xi` mapping geometry to `rho_AB`, Axis 0 is scalar readout, not full functional (`IGT:215-218`; `IGT:656-658`).

OPEN: Axis-4 taijitu spin direction is open; runtime math is strong but symbolic spin assignment is not closed (`IGT:300-326`).

OPEN: Axis-3 has competing readings; inner/fiber vs outer/base is current strongest, while chirality, Type1/Type2 inversion, and flux in/out remain alternatives requiring discriminator tests (`IGT:273-292`; `ATLAS:293-304`).

OPEN: Signed functional role names are exploratory, not canon. The exact facts are fixed operator map plus up/down precedence; projector/quantizer, ascent/descent, entrainment/damping, broadcast/filtering are hypotheses (`SIGNED:997-1058`).

OPEN: Full 64 closure is not proven. The atlas says chart/runtime/hexagram 64 layers are schedule/index surfaces and must not claim closure or ontology (`ATLAS:264-270`; `ATLAS:331-345`).

## H. Delta vs Current Sims

Current `oracle_targets.py` is related but not identical. It says the active validation contract is “16 stages” as `8 terrain generators (t0..t7) x their 2 native operators`, with both terrain-first/down and operator-first/up outputs per row (`ORACLE:5-16`). It is `scratch_diagnostic; promotion_allowed=false` (`ORACLE:18-20`).

Same objects: current oracle uses density matrices/Pauli matrices (`ORACLE:24-28`), exact Ti/Te pinching and Fi/Fe unitary channels (`ORACLE:72-83`), 8 terrain generator indices with eps/kind/pole (`ORACLE:42-45`, `ORACLE:50-61`), and the same native split `{Ti,Fi}` for t0,t1,t4,t5 vs `{Te,Fe}` for t2,t3,t6,t7 (`ORACLE:42-45`), matching the direct/conjugated native rule (`LEDGER:157-173`).

Different indexing/contract: the source Type-1 spec is a named chart over `Se-in/Ne-in/Ni-in/Si-in`, outer/inner loops, exact tokens, and WIN/LOSE casing (`IGT:527-534`; `ATLAS:217-231`). The oracle rows are numeric `(t, op)` rows and do not carry source token names, Type-1 outer/inner casing, traversal labels, or MBTI (`ORACLE:88-102`). Therefore it is the same operator/terrain ingredient family at a lower runtime-contract layer, but not a verbatim Type-1 stage chart.

Current engines consume that oracle structure: PyTorch builds `stage_list = [(t, o) for t in range(8) for o in NATIVE[t]]` and computes down/up compositions (`torch_engine.py:79-92`); JAX does the same (`jax_engine.py:88-99`); Julia does the same (`julia_engine.jl:105-114`).

Current `sixteen_stage_engine.json` explicitly labels its construction as “8 terrains x 2 native operators each, signed Axis-6 order” and keeps `scratch_diagnostic; promotion_allowed=false` (`system_v7/constraint_core/data_json/sixteen_stage_engine.json:1-3`, `:102-112`). So: same base terrain/operator objects, relabeled/indexed as `t0..t7 x native op`, with source chart fields missing unless a later mapping layer adds them.


