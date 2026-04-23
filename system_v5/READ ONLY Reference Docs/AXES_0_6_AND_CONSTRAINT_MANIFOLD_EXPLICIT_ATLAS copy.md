# Axes 0 Through 6 And Constraint Manifold Explicit Atlas

**Date:** 2026-03-30  
**Status:** Working support surface. This is an explicit atlas, not a doctrine rewrite.  
**Scope:** This packet gathers the active lower-axis mathematics, the current constraint-manifold ladder, the terrain and operator realization, and the downstream Jung / IGT / I Ching correlation layers in one place.

---

## 1. Honesty Boundary

This packet keeps four layers separate:

1. the current active mathematical stack
2. the current active geometric stack
3. the chart and language layers
4. the noncanon higher-axis residue

The most important honesty points are:

- the current active owner stack is `Axis 0` through `Axis 6`
- there are **7 active axes total**, because counting starts at zero
- `Axis 7` through `Axis 12` belong to a planned later mirror layer, not the current lower-axis engine atlas
- Jung, IGT, trigram, hexagram, yin-yang, and I Ching labels are **correlation layers**, not primary mathematics
- `Axis 0` is still open at the bridge-and-cut level even though its current basin is strong

---

## 2. Base Mathematical Objects

### 2.1 Constraint set and admissible manifold

| Object | Exact mathematics | Meaning |
|---|---|---|
| root constraint set | `C = { F01_FINITUDE, N01_NONCOMMUTATION, admissible probe rules, admissible composition rules }` | the admissibility charter |
| admissible manifold | `M(C) = { x : x is admissible under C }` | all admissible configurations |
| induced geometry | geometry on `M(C)` is the compatibility structure induced by `C` | geometry comes after constraints |
| axis slice | `A_i : M(C) -> V_i` | each axis is a function on the constraint manifold |

### 2.2 State spaces

| Object | Exact mathematics | Meaning |
|---|---|---|
| Hilbert carrier | `H = C^2` | one qubit carrier space |
| one-sheet density space | `D(C^2) = { rho in B(C^2) : rho >= 0, Tr(rho) = 1 }` | one-qubit density matrices |
| two-part cut-state space | `D(H_A tensor H_B)` | bipartite state space for correlation functionals |
| paired sheet realization | `M_hat_geom = disjoint union over s in {left,right} of S_s^3 hat`, where `S_s^3 hat = { (psi_s, rho_s) in S_s^3 x D(H) : rho_s = psi_s psi_s^dagger }` | current concrete sheet realization inside the constraint manifold |
| realization map | `iota : M_hat_geom -> M(C)` | the concrete geometry packet embedded into the admissible manifold |

### 2.3 Pauli basis

| Object | Exact matrix |
|---|---|
| identity | `I = [[1,0],[0,1]]` |
| Pauli x | `sigma_x = [[0,1],[1,0]]` |
| Pauli y | `sigma_y = [[0,-i],[i,0]]` |
| Pauli z | `sigma_z = [[1,0],[0,-1]]` |
| lowering operator | `sigma_minus = [[0,0],[1,0]]` |
| raising operator | `sigma_plus = [[0,1],[0,0]]` |

### 2.4 Density and Hamiltonian coordinates

| Object | Exact mathematics |
|---|---|
| density coordinates | `rho = 1/2 ( I + r_x sigma_x + r_y sigma_y + r_z sigma_z )` |
| Hamiltonian coordinates | `H_0 = n_x sigma_x + n_y sigma_y + n_z sigma_z` |
| z projectors | `P_0 = 1/2 ( I + sigma_z )`, `P_1 = 1/2 ( I - sigma_z )` |
| x projectors | `Q_plus = 1/2 ( I + sigma_x )`, `Q_minus = 1/2 ( I - sigma_x )` |

---

## 3. Full Constraint-Manifold Ladder

### 3.1 Full ladder in order

| Order | Layer | Exact mathematics | Current status |
|---|---|---|---|
| 1 | root constraints | `F01_FINITUDE`, `N01_NONCOMMUTATION` | active |
| 2 | admissibility set | `C` | active |
| 3 | admissible manifold | `M(C)` | active |
| 4 | axis-slice rule | `A_i : M(C) -> V_i` | active |
| 5 | favored finite realization | `H = C^2`, `D(C^2)`, probes, Pauli basis | active |
| 6 | normalized carrier | `S^3 = { psi in C^2 : ||psi|| = 1 }` | active |
| 7 | Hopf projection | `pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi in S^2` | active |
| 8 | Bloch sphere image | `S^2` | active |
| 9 | torus stratum | `T_eta = { psi_s(phi, chi; eta) : phi, chi in [0, 2pi) } subset S^3` | active |
| 10 | Clifford torus | `T_(pi/4)` | active |
| 11 | fiber-loop family | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | active |
| 12 | lifted-base-loop family | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | active |
| 13 | left Weyl sheet | `psi_left in S^3` | active |
| 14 | right Weyl sheet | `psi_right in S^3` | active |
| 15 | left density | `rho_left = psi_left psi_left^dagger` | active |
| 16 | right density | `rho_right = psi_right psi_right^dagger` | active |
| 17 | engine runtime manifold | paired sheet state plus torus coordinates plus stage controls | active |
| 18 | bridge target family | `Xi : geometry / history -> rho_AB` | open |
| 19 | bipartite cut-state family | `rho_AB`, `rho_A`, `rho_B` | open |
| 20 | `Axis 0` kernel family | `Phi_0(rho_AB)` | open but strongly narrowed |

### 3.2 Spinor chart

The current local carrier chart is:

```text
psi_s(phi, chi; eta)
= [ exp(i(phi + chi)) cos(eta),
    exp(i(phi - chi)) sin(eta) ]^T
```

with:

- `s in { left, right }`
- `eta in [0, pi/2]`
- `phi in [0, 2pi)`
- `chi in [0, 2pi)`

### 3.3 Hopf and torus geometry

| Object | Exact mathematics | Meaning |
|---|---|---|
| Hopf map | `pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi` | sends the spinor carrier to the Bloch sphere |
| density reduction | `rho(psi) = |psi><psi| = 1/2 ( I + r_x sigma_x + r_y sigma_y + r_z sigma_z )` | turns the spinor into a pure density state |
| torus stratum | `T_eta = { psi_s(phi, chi; eta) }` | one Hopf torus inside `S^3` |
| Clifford torus | `eta = pi / 4` | the symmetric torus |
| Hopf connection | `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` | separates the fiber direction from the horizontal direction |

### 3.4 Loop geometry

| Object | Exact mathematics | Meaning |
|---|---|---|
| fiber loop | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | pure fiber motion |
| lifted base loop | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | horizontal lifted base motion |
| horizontal condition | `A( dot(gamma_base^s) ) = 0` | base loop is horizontal in the Hopf connection |
| fiber density law | `rho_fiber^s(u) = rho_fiber^s(0)` | the density does not change |
| base density law | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | the density changes with `u` |

### 3.5 Weyl-sheet layer

| Object | Exact mathematics | Meaning |
|---|---|---|
| left spinor | `psi_left in S^3` | left sheet |
| right spinor | `psi_right in S^3` | right sheet |
| left density | `rho_left = psi_left psi_left^dagger` | left sheet density |
| right density | `rho_right = psi_right psi_right^dagger` | right sheet density |
| left Hamiltonian | `H_left = + H_0` | left free evolution |
| right Hamiltonian | `H_right = - H_0` | right free evolution |
| frame unitary | `V_s(u) = exp( -i H_s u )` | sheet-dependent frame transport |

### 3.6 Bridge and cut spaces

| Object | Exact mathematics | Meaning |
|---|---|---|
| bridge placeholder | `Xi : geometry sample or history window -> rho_AB in D(H_A tensor H_B)` | the open geometry-to-cut map |
| pointwise bridge family | `Xi_point : x -> ( c_x, rho_(c_x)(x) )` | pointwise bridge family |
| shell bridge family | `Xi_shell : x -> { ( r, w_r, rho_(A_r B_r)(x) ) }_r` | weighted shell-cut bridge family |
| history bridge family | `Xi_hist : h restricted to [t_0, t_1] -> { ( t, c, w_c, rho_c(t) ) }_(t,c)` | history-window bridge family |
| cut-state evaluation | `Phi_0(rho_AB)` | `Axis 0` acts only after a cut state exists |

### 3.7 Chart and index spaces

These are not primary manifolds, but they are part of the explicit structure:

| Object | Exact mathematics or structure | Meaning |
|---|---|---|
| IGT quadrant set | `{ WinLose, WinWin, LoseWin, LoseLose }` | hard four-way stage grammar on the perceiving topologies |
| stage-outcome set | `{ WIN, LOSE, win, lose }` | outer and inner stage results |
| ordered-token set | `{ TiSe, SeTi, FiSe, SeFi, TiNe, NeTi, FiNe, NeFi, TeNi, NiTe, FeNi, NiFe, TeSi, SiTe, FeSi, SiFe }` | function-token grammar |
| I Ching line-index scaffold | six binary structural lines using `Axis 1` through `Axis 6` | proposal-only 64-slot index scaffold |
| 64-slot structural scaffold | `8 terrains x 8 signed operators = 64` | proposal-only structural index layer |

---

## 4. Global Axis Table

| Axis | Current mathematical role | Current exact mathematics | Active or not | Jung layer | IGT layer | I Ching layer |
|---|---|---|---|---|---|---|
| `Axis 0` | entropy drive and later cut-state functional | torus seat plus later `Phi_0(rho_AB)` family | active, but open | `Ni/Ne` versus `Si/Se` | `WinLose/LoseLose` versus `LoseWin/WinWin` | not one of the six structural I Ching lines; acts as drive through them |
| `Axis 1` | derived terrain branch split | `Se/Ni` versus `Ne/Si` | active, derived | `Se/Ni` versus `Ne/Si` | `LoseWin/LoseLose` versus `WinLose/WinWin` | line 5 in the proposal-only six-line scaffold |
| `Axis 2` | direct versus conjugated frame | `tilde(rho) = rho` versus `tilde(rho) = V_s^dagger rho V_s` | active | `Se/Ne` versus `Si/Ni` | `LoseWin/WinLose` versus `WinWin/LoseLose` | line 6 in the proposal-only six-line scaffold |
| `Axis 3` | fiber versus lifted-base loop class | density-stationary path versus density-traversing path | active | inner token set versus outer token set | inner token set versus outer token set | line 3 in the proposal-only six-line scaffold |
| `Axis 4` | loop-order family | `unitary then non-unitary then unitary then non-unitary` versus `non-unitary then unitary then non-unitary then unitary` | active, derived | proposed pair-order split `TiFe` versus `FeTi` | implemented loop-family split `FeTi` versus `TeFi` | line 4 in the proposal-only six-line scaffold |
| `Axis 5` | operator family | dephasing family versus rotation family | active | `FeFi` versus `TiTe` | rotation-class tokens versus dephasing-class tokens | line 2 in the proposal-only six-line scaffold |
| `Axis 6` | precedence order | operator first versus terrain first | active, derived | judging-first versus perceiving-first ordered pairs | up versus down token order | line 1 in the proposal-only six-line scaffold |

### 4.1 Explicit Jung And IGT Axis-Pair Layer

This atlas now records the literal function-pair labels used for the Jung and IGT layers.

These labels remain downstream of the math. They do not replace the geometry, channels, or bridge objects.

| Axis | Explicit Jung pairing in this packet | Explicit IGT pairing in this packet |
|---|---|---|
| `Axis 0` | `Ni/Ne` versus `Si/Se` | `WinLose/LoseLose` versus `LoseWin/WinWin` |
| `Axis 1` | `Se/Ni` versus `Ne/Si` | `LoseWin/LoseLose` versus `WinLose/WinWin` |
| `Axis 2` | `Se/Ne` versus `Si/Ni` | `LoseWin/WinLose` versus `WinWin/LoseLose` |
| `Axis 3` | inner token set versus outer token set | inner token set versus outer token set |
| `Axis 4` | proposed pair-order split `TiFe` versus `FeTi` | implemented loop-family split `FeTi` versus `TeFi` |
| `Axis 5` | `FeFi` versus `TiTe` | rotation-class tokens versus dephasing-class tokens |
| `Axis 6` | judging-first versus perceiving-first ordered pairs | up versus down ordered tokens |

---

## 5. Axis 0

### 5.1 Continuous seat

The current geometric seat is the torus latitude:

```text
rho_bar(eta)
= (1 / (2 pi)) integral from 0 to 2 pi of rho(chi, eta) d chi
= diagonal matrix with entries cos^2(eta), sin^2(eta)
```

The entropy of this torus-orbit average is:

```text
S( rho_bar(eta) )
= - cos^2(eta) log( cos^2(eta) )
   - sin^2(eta) log( sin^2(eta) )
```

### 5.2 Discrete hemisphere threshold

```text
b_0 = sign( cos(2 eta) ) = sign( r_z )
```

with:

| Region | Condition | Label |
|---|---|---|
| upper hemisphere | `eta < pi / 4` | `N` / white |
| Clifford threshold | `eta = pi / 4` | neutral threshold |
| lower hemisphere | `eta > pi / 4` | `S` / black |

### 5.3 Open cut-state family

The current strongest family is:

| Candidate | Exact mathematics | Current status |
|---|---|---|
| coherent information | `I_c(A > B) = - S(A | B) = S(rho_B) - S(rho_AB)` | strongest simple candidate |
| conditional entropy | `S(A | B) = S(rho_AB) - S(rho_B)` | signed cut entropy family |
| mutual information | `I(A : B) = S(rho_A) + S(rho_B) - S(rho_AB)` | unsigned companion diagnostic |
| weighted shell-cut form | `sum over r of w_r I_c( A_r > B_r )` | strongest current global form |

### 5.4 What is earned versus open

| Layer | Current read |
|---|---|
| earned | geometry seat exists; coherent information is the strongest simple signed candidate |
| open | final bridge `Xi`, final cut `A | B`, exact shell/hist unification |
| killed or demoted | raw local `left | right` as final doctrine cut; runtime `ga0` as doctrine object |

### 5.5 Correlation layers

| Layer | Current correlation |
|---|---|
| Jung correlation | `Ni/Ne` versus `Si/Se` |
| IGT correlation | `WinLose/LoseLose` versus `LoseWin/WinWin` |
| I Ching correlation | not a line inside the six-line scaffold; treated as the drive moving through the 64-slot space |

---

## 6. Axis 1

### 6.1 Exact branch split

The current derived split is:

| Branch | Topologies |
|---|---|
| first branch | `Se`, `Ni` |
| second branch | `Ne`, `Si` |

The current packet often names these:

| Branch | Current label |
|---|---|
| `Se`, `Ni` | proper dissipative / isothermal branch |
| `Ne`, `Si` | unitary / non-dissipative branch |

### 6.2 Derived role

`Axis 1` is not primitive in the current owner stack.

It is a reduced branch split derived from `Axis 0` and `Axis 2`.

### 6.3 Correlation layers

| Layer | Current correlation |
|---|---|
| Jung correlation | `Se/Ni` versus `Ne/Si` |
| IGT correlation | `LoseWin/LoseLose` versus `WinLose/WinWin` |
| I Ching correlation | line 5 in the six-line proposal scaffold |

---

## 7. Axis 2

### 7.1 Exact frame law

The direct and conjugated frame laws are:

```text
direct representation:
dot(rho) = L(rho)
```

```text
conjugated representation:
tilde(rho) = V^dagger rho V
dot(tilde(rho))
= V^dagger L( V tilde(rho) V^dagger ) V - i [ -K, tilde(rho) ]
```

with

```text
K = i V^dagger dot(V)
```

and in the Weyl-sheet working realization

```text
V_s(u) = exp( -i H_s u )
```

### 7.2 Topology assignment

| Frame class | Topologies |
|---|---|
| direct | `Se`, `Ne` |
| conjugated | `Ni`, `Si` |

### 7.3 Correlation layers

| Layer | Current correlation |
|---|---|
| Jung correlation | `Se/Ne` versus `Si/Ni` |
| IGT correlation | `LoseWin/WinLose` versus `WinWin/LoseLose` |
| I Ching correlation | line 6 in the six-line proposal scaffold |

---

## 8. Axis 3

### 8.1 Exact path split

| Path class | Exact mathematics | Density behavior |
|---|---|---|
| fiber | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` |
| lifted base | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` |

### 8.2 Current active definition

The active owner-stack definition is:

- fiber / density-stationary path
- lifted-base / density-traversing path

This is stronger than older left/right or flux-only readings.

### 8.3 Correlation layers

The explicit inner and outer token sets used here are:

| Side | Exact token set |
|---|---|
| inner | type two: `TiNe`, `FeNi`, `SeTi`, `SiFe`; type one: `TeNi`, `FiNe`, `SiTe`, `SeFi` |
| outer | type one: `NeTi`, `NiFe`, `TiSe`, `FeSi`; type two: `NiTe`, `NeFi`, `TeSi`, `FiSe` |

| Layer | Current correlation |
|---|---|
| Jung correlation | inner token set versus outer token set |
| IGT correlation | same inner token set versus outer token set in the stage grammar |
| I Ching correlation | line 3 in the six-line proposal scaffold |

---

## 9. Axis 4

### 9.1 Exact order family

The two composition families are:

```text
deductive order:
Phi_deductive = U circle E circle U circle E
```

```text
inductive order:
Phi_inductive = E circle U circle E circle U
```

where:

- `U` means the unitary branch
- `E` means the non-unitary or dissipative branch

### 9.2 Current loop-family correlation

| Loop family | Current token-family label |
|---|---|
| deductive | `FeTi` family |
| inductive | `TeFi` family |

### 9.3 Correlation layers

This atlas keeps two `Axis 4` label layers explicit:

1. the user-facing Jung pair-order split `TiFe` versus `FeTi`
2. the implemented runtime loop-family split `FeTi` versus `TeFi`

| Layer | Current correlation |
|---|---|
| Jung correlation | proposed pair-order split `TiFe` versus `FeTi` |
| IGT correlation | implemented loop-family split `FeTi` versus `TeFi` |
| I Ching correlation | line 4 in the six-line proposal scaffold |

---

## 10. Axis 5

### 10.1 Exact operator-family split

| Family | Exact mathematics |
|---|---|
| dephasing family | `Ti` and `Te` channels |
| rotation family | `Fi` and `Fe` channels |

More explicitly:

```text
Ti(rho) = (1 - q_1) rho + q_1 ( P_0 rho P_0 + P_1 rho P_1 )
```

```text
Te(rho) = (1 - q_2) rho + q_2 ( Q_plus rho Q_plus + Q_minus rho Q_minus )
```

```text
Fi(rho) = U_x(theta) rho U_x(theta)^dagger
```

```text
Fe(rho) = U_z(phi) rho U_z(phi)^dagger
```

### 10.2 Correlation layers

The explicit operator-pair split used here is:

| Side | Exact judging pair |
|---|---|
| first side | `FeFi` |
| second side | `TiTe` |

The matching IGT token-family split is:

| Side | Exact token family |
|---|---|
| rotation-class side | `FiNe`, `NeFi`, `FiSe`, `SeFi`, `FeNi`, `NiFe`, `FeSi`, `SiFe` |
| dephasing-class side | `TiNe`, `NeTi`, `TiSe`, `SeTi`, `TeNi`, `NiTe`, `TeSi`, `SiTe` |

| Layer | Current correlation |
|---|---|
| Jung correlation | `FeFi` versus `TiTe` |
| IGT correlation | rotation-class tokens versus dephasing-class tokens |
| I Ching correlation | line 2 in the six-line proposal scaffold |

---

## 11. Axis 6

### 11.1 Exact precedence law

`Axis 6` is derived from `Axis 0` and `Axis 3` in the active lower stack:

```text
b_6 = - b_0 b_3
```

This is equivalent to the binary exclusive-or rule in the 64-step audit.

### 11.2 Exact order meaning

| Value | Meaning |
|---|---|
| up | operator written first |
| down | terrain written first |

### 11.3 Full token law

| Topology | dephasing up | dephasing down | rotation up | rotation down |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

### 11.4 Correlation layers

The explicit ordered-pair split is:

| Side | Exact ordered-token family |
|---|---|
| judging first | `TiSe`, `TiNe`, `FeSi`, `FeNi`, `TeNi`, `TeSi`, `FiNe`, `FiSe` |
| perceiving first | `SeTi`, `NeTi`, `SiFe`, `NiFe`, `NiTe`, `SiTe`, `NeFi`, `SeFi` |

| Layer | Current correlation |
|---|---|
| Jung correlation | judging-first ordered pairs versus perceiving-first ordered pairs |
| IGT correlation | up versus down token position |
| I Ching correlation | line 1 in the six-line proposal scaffold |

---

## 12. Later Mirror Layer: Axes 7 Through 12

### 12.1 Current status

`Axis 7` through `Axis 12` are **planned later**, not part of the current active lower-axis engine atlas.

The active lower stack is exactly:

- `Axis 0`
- `Axis 1`
- `Axis 2`
- `Axis 3`
- `Axis 4`
- `Axis 5`
- `Axis 6`

### 12.2 Intended role of the later mirror layer

The later mirror layer is:

- not a new seventh lower axis
- not a reason to rename the active stack as `Axis 0` through `Axis 7`
- not part of the current one-engine lower-axis runtime truth

It is instead the planned many-engine interaction layer in which:

- `Axis 1` through `Axis 6` describe one engine
- `Axis 7` through `Axis 12` mirror `Axis 1` through `Axis 6` at the engine-on-engine layer
- each left/right engine pair can be treated as one interacting unit, or one "person", in that larger irrational-game-theory space

### 12.3 Noncanon mathematics currently available

The explicit noncanon mathematics in the older mirror suite is:

| Object | Exact mathematics |
|---|---|
| channel lift | given Kraus operators `K_j`, the Choi matrix is `Choi = sum_j vec(K_j) vec(K_j)^dagger` |
| mirror-axis object family | deviations of lifted channels away from the identity channel in Choi space |
| overlap test | normalized Hilbert-Schmidt inner product between Choi-space deviations |

### 12.4 Current honest read

| Object | Status |
|---|---|
| `Axis 0` through `Axis 6` | active lower-axis engine stack |
| `Axis 7` through `Axis 12` | later many-engine mirror plan only |
| irrational-game-theory many-engine layer | planned later, not current lower-axis runtime truth |

---

## 13. Eight Terrain Table

| Terrain | Perceiving topology | Loop class | Path mathematics | Density law | Direct or conjugated frame | Native judging functions | Current engine-type realization |
|---|---|---|---|---|---|---|---|
| `Se_f` | `Se` | fiber | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | direct | `Ti`, `Fi` | engine type one inner, engine type two outer |
| `Si_f` | `Si` | fiber | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | conjugated | `Te`, `Fe` | engine type one inner, engine type two outer |
| `Ne_f` | `Ne` | fiber | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | direct | `Ti`, `Fi` | engine type one inner, engine type two outer |
| `Ni_f` | `Ni` | fiber | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | conjugated | `Te`, `Fe` | engine type one inner, engine type two outer |
| `Se_b` | `Se` | lifted base | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | direct | `Ti`, `Fi` | engine type one outer, engine type two inner |
| `Si_b` | `Si` | lifted base | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | conjugated | `Te`, `Fe` | engine type one outer, engine type two inner |
| `Ne_b` | `Ne` | lifted base | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | direct | `Ti`, `Fi` | engine type one outer, engine type two inner |
| `Ni_b` | `Ni` | lifted base | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | conjugated | `Te`, `Fe` | engine type one outer, engine type two inner |

---

## 14. Eight Signed Judging Variants

| Signed variant | Exact operator | Order meaning | Exact tokens |
|---|---|---|---|
| `Ti` up | `rho -> (1 - q_1) rho + q_1 ( P_0 rho P_0 + P_1 rho P_1 )` | operator first | `TiSe`, `TiNe` |
| `Ti` down | same operator | terrain first | `SeTi`, `NeTi` |
| `Fe` up | `rho -> U_z(phi) rho U_z(phi)^dagger` | operator first | `FeSi`, `FeNi` |
| `Fe` down | same operator | terrain first | `SiFe`, `NiFe` |
| `Te` up | `rho -> (1 - q_2) rho + q_2 ( Q_plus rho Q_plus + Q_minus rho Q_minus )` | operator first | `TeNi`, `TeSi` |
| `Te` down | same operator | terrain first | `NiTe`, `SiTe` |
| `Fi` up | `rho -> U_x(theta) rho U_x(theta)^dagger` | operator first | `FiNe`, `FiSe` |
| `Fi` down | same operator | terrain first | `NeFi`, `SeFi` |

---

## 15. IGT Correlation Layer

### 15.1 Topology quadrants

| Perceiving topology | IGT quadrant | dephasing strategy | rotation strategy |
|---|---|---|---|
| `Ne` | `WinLose` | `NeTi` | `FiNe` |
| `Si` | `WinWin` | `SiTe` | `FeSi` |
| `Se` | `LoseWin` | `TiSe` | `SeFi` |
| `Ni` | `LoseLose` | `TeNi` | `NiFe` |

### 15.2 Engine type one

| Step | Topology | outer token | outer outcome | inner token | inner outcome |
|---|---|---|---|---|---|
| 1 | `Se` | `TiSe` | `LOSE` | `SeFi` | `win` |
| 2 | `Ne` | `NeTi` | `WIN` | `FiNe` | `lose` |
| 3 | `Ni` | `NiFe` | `LOSE` | `TeNi` | `lose` |
| 4 | `Si` | `FeSi` | `WIN` | `SiTe` | `win` |

### 15.3 Engine type two

| Step | Topology | outer token | outer outcome | inner token | inner outcome |
|---|---|---|---|---|---|
| 1 | `Se` | `FiSe` | `WIN` | `SeTi` | `lose` |
| 2 | `Si` | `TeSi` | `WIN` | `SiFe` | `win` |
| 3 | `Ni` | `NiTe` | `LOSE` | `FeNi` | `lose` |
| 4 | `Ne` | `NeFi` | `LOSE` | `TiNe` | `win` |

---

## 16. I Ching Correlation Layer

This layer is explicitly a **proposal-only index layer**.

It is not primary mathematics.

### 16.1 What is currently lowest-risk to say

| Claim | Current status |
|---|---|
| the six structural binary axes can be arranged into a six-line scaffold | available as proposal scaffold only |
| `Axis 0` is not one of those six lines and instead drives traversal through the 64 structural states | available as proposal scaffold only |
| the 64-slot table exists as a correlation index | available as proposal scaffold only |
| hexagram names are historical tags, not mathematical facts | active language rule |

### 16.2 Current line placement in the proposal scaffold

| Line | Axis |
|---|---|
| line 1 | `Axis 6` |
| line 2 | `Axis 5` |
| line 3 | `Axis 3` |
| line 4 | `Axis 4` |
| line 5 | `Axis 1` |
| line 6 | `Axis 2` |

And:

| Object | Placement |
|---|---|
| `Axis 0` | external drive through the six-line structural space |
| `Axis 7` through `Axis 12` | not part of the current six-line lower scaffold |

### 16.3 Explicit Taijitu Axis Map

This subsection records the current explicit symbolic layer from the yin-yang packet.

It is still a proposal-only representational layer.

| Axis | Explicit taijitu feature | Explicit Jung pairing | Explicit IGT pairing | Math anchor kept separate |
|---|---|---|---|---|
| `Axis 0` | black versus white, plus the enclosing circle | white / yang = `Ne/Ni`; black / yin = `Se/Si` | white / yang = `WinLose/LoseLose`; black / yin = `LoseWin/WinWin` | `b_0 = sign( cos(2 eta) )`, later `Phi_0(rho_AB)` |
| `Axis 1` | black dot in white teardrop versus white dot in black teardrop | `Ni/Se` versus `Ne/Si` | `LoseLose/LoseWin` versus `WinLose/WinWin` | branch split derived from `Axis 0` and `Axis 2` |
| `Axis 2` | dots versus teardrops | dots = `Si/Ni`; teardrops = `Ne/Se` | dots = `WinWin/LoseLose`; teardrops = `WinLose/LoseWin` | direct versus conjugated frame |
| `Axis 3` | tail chasing inner versus fat-tip chasing outer | inner token set versus outer token set | inner token set versus outer token set | fiber versus lifted-base loop class |
| `Axis 4` | clockwise versus counterclockwise spin | open symbolic pair-order reading | open symbolic loop-direction reading | implemented runtime split is `FeTi` versus `TeFi` |
| `Axis 5` | S-curve form family, lobe-size family, hotter versus cooler visual weighting | `FeFi` versus `TiTe` | rotation-class tokens versus dephasing-class tokens | operator-family split |
| `Axis 6` | up versus down reading of the symbol | judging first versus perceiving first ordered pairs | up versus down ordered tokens | `b_6 = - b_0 b_3` |

### 16.4 Four-Part Taijitu Slot Table

The current explicit four-part symbolic placement is:

| Slot in the symbol | Function | IGT quadrant |
|---|---|---|
| white dot | `Ni` | `LoseLose` |
| black teardrop | `Se` | `LoseWin` |
| white teardrop | `Ne` | `WinLose` |
| black dot | `Si` | `WinWin` |

This is the current explicit `Axis 1 x Axis 2` table used in the symbolic layer.

### 16.5 Explicit Axis 3 And Axis 6 Directional Table

The strongest current explicit symbolic up/down table is:

| Loop side and color | Direction | Exact token set |
|---|---|---|
| inner and white | up | type two: `TiNe`, `FeNi`; type one: `TeNi`, `FiNe` |
| inner and black | down | type two: `SeTi`, `SiFe`; type one: `SiTe`, `SeFi` |
| outer and white | down | type one: `NeTi`, `NiFe`; type two: `NiTe`, `NeFi` |
| outer and black | up | type one: `TiSe`, `FeSi`; type two: `TeSi`, `FiSe` |

This table is the most concrete current symbolic realization of the `Axis 3` and `Axis 6` layer.

### 16.6 Explicit Axis 4 And Axis 5 Symbolic Candidates

The symbolic packet also carries the following open candidate structure:

| Axis | Candidate symbolic split | Current status |
|---|---|---|
| `Axis 4` | clockwise versus counterclockwise spin | open which direction corresponds to which runtime family |
| `Axis 4 x Axis 5` right-facing | counterclockwise tail chaser versus clockwise head chaser | open symbolic overlay |
| `Axis 4 x Axis 5` left-facing | counterclockwise head chaser versus clockwise tail chaser | open symbolic overlay |
| `Axis 5` | flatter versus curvier S-curve | open symbolic overlay |
| `Axis 5` | relative white/black lobe size | open symbolic overlay |
| `Axis 5` | white-heavier as hotter versus black-heavier as cooler | symbolic metaphor only |

### 16.7 Why the I Ching layer stays fenced

Because:

- it is an index and correlation layer
- several of its old line-value interpretations rely on older unsettled `Axis 3`, `Axis 4`, and `Axis 5` meanings
- the current authority map explicitly forbids using it as primary math

---

## 17. Current Strongest Read

The cleanest current explicit read is:

- the lower active mathematical stack is `Axis 0` through `Axis 6`
- there are seven active axes total because counting starts at zero
- `Axis 0` is the only entropy-backed axis and is still open at the bridge/cut layer
- `Axis 1` is derived from the `Axis 0` and `Axis 2` terrain split
- `Axis 2` is the direct versus conjugated frame law
- `Axis 3` is the fiber versus lifted-base loop split
- `Axis 4` is the unitary/non-unitary loop-order family
- `Axis 5` is the dephasing versus rotation operator family
- `Axis 6` is the operator-first versus terrain-first precedence law
- `Axis 7` through `Axis 12` belong only to the later many-engine mirror plan and are not part of the active lower owner stack

---

## 18. Companion Packets

For more detail on specific sublayers:

1. `system_v4/docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP.md`
2. `system_v4/docs/TAIJITU_AXES_0_6_EXPLICIT_SYMBOLIC_LAYER.md`
3. `system_v4/docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md`
4. `system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`
5. `system_v4/docs/AXIS_0_1_2_QIT_MATH.md`
6. `system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md`
7. `system_v4/docs/TERRAIN_LAW_LEDGER.md`
8. `system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md`
9. `system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md`
10. `system_v4/docs/64_HEXAGRAM_STATE_SPACE.md`
