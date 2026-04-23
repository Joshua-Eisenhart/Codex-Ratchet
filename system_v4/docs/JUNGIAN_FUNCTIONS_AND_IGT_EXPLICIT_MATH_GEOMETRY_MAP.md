# Jungian Functions And IGT Explicit Math And Geometry Map

**Date:** 2026-03-30  
**Status:** Working support surface. This is an explicit reference map, not a doctrine rewrite. It keeps three different layers separate:

1. the carrier geometry that is actually simulated
2. the function and operator math that is actually executed
3. the IGT stage grammar that labels the chart structure

---

## 1. Purpose

This packet answers one question as explicitly as possible:

**How do the eight Jungian functions map onto the current quantum-information-theoretic engine, its carrier geometry, and the IGT stage structure?**

Rules used here:

- no compression of the eight functions into vague metaphor
- no replacement of geometry with chart labels
- no replacement of operator math with chart labels
- no replacement of chart labels with geometry

So this packet keeps separate:

- the four perceiving functions: `Se`, `Ne`, `Ni`, `Si`
- the four judging functions: `Ti`, `Te`, `Fi`, `Fe`
- the combined ordered tokens such as `TiSe`, `NeTi`, `FeSi`, `NiFe`
- the IGT outcome labels: `WIN`, `LOSE`, `win`, `lose`

---

## 2. Base Geometry And State Math

All eight functions live on the same basic state-and-geometry ladder.

### 2.1 State space

| Object | Exact math | Meaning |
|---|---|---|
| Hilbert carrier | `H = C^2` | one qubit carrier space |
| density-state space | `D(C^2) = { rho in B(C^2) : rho >= 0, Tr(rho) = 1 }` | all allowed one-qubit density matrices |
| normalized carrier | `S^3 = { psi in C^2 : ||psi|| = 1 }` | unit spinor carrier |
| Bloch projection | `pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi in S^2` | map from the spinor carrier to the Bloch sphere |
| density reduction | `rho(psi) = |psi><psi| = 1/2 (I + r_x sigma_x + r_y sigma_y + r_z sigma_z)` | pure-state density matrix coming from a spinor |

### 2.2 Pauli basis

| Object | Exact matrix |
|---|---|
| identity | `I = [[1,0],[0,1]]` |
| Pauli x | `sigma_x = [[0,1],[1,0]]` |
| Pauli y | `sigma_y = [[0,-i],[i,0]]` |
| Pauli z | `sigma_z = [[1,0],[0,-1]]` |
| z-projector plus | `P_0 = 1/2 (I + sigma_z)` |
| z-projector minus | `P_1 = 1/2 (I - sigma_z)` |
| x-projector plus | `Q_+ = 1/2 (I + sigma_x)` |
| x-projector minus | `Q_- = 1/2 (I - sigma_x)` |

### 2.3 Carrier chart

The current carrier chart used in the live geometry packet is:

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

### 2.4 Two loop geometries

The same topology class can appear on either of two loop geometries.

| Loop geometry | Exact path | Meaning |
|---|---|---|
| fiber loop | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | phase-only loop on one torus; density does not change |
| lifted base loop | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | horizontal lifted base loop; density changes with `u` |
| fiber density law | `rho_fiber^s(u) = |gamma_fiber^s(u)><gamma_fiber^s(u)| = rho_fiber^s(0)` | density stays fixed |
| base density law | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | density changes along the path |

This gives the two actual geometry contexts for every topology:

- one fiber realization
- one lifted-base realization

So every perceiving function appears twice in the runtime terrain list:

- once on the fiber loop
- once on the lifted base loop

---

## 3. The Four Perceiving Functions

These four are not operators. They are topology-and-flow classes on the carrier geometry.

### 3.1 Exact perceiving-function table

| Function | Expansion or compression | Open or closed thermodynamic class | Representation frame | Generator family | Exact current math form | Geometric motion | Canonical terrain names |
|---|---|---|---|---|---|---|---|
| `Se` | expansion | open / isothermal | direct frame | dissipative Lindblad | `dot(rho) = sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) ) - i epsilon_Se [ H_0, rho ]` | radial outward motion | funnel / cannon |
| `Ne` | expansion | closed / adiabatic | direct frame | Hamiltonian | `dot(rho) = -i [ H_0, rho ] + epsilon_Ne sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) )` | tangential circulation on `S^3` | vortex / spiral |
| `Ni` | compression | open / isothermal | conjugated frame | dissipative Lindblad with attraction | `dot(rho) = ( L_P rho L_P^dagger - 1/2 ( L_P^dagger L_P rho + rho L_P^dagger L_P ) ) - i epsilon_Ni [ H_0, rho ]` | radial inward contraction toward an attractor | pit / source |
| `Si` | compression | closed / adiabatic | conjugated frame | commuting Hamiltonian plus invariant strata | `dot(rho) = -i [ H_C, rho ] + sum_j kappa_j ( P_j rho P_j - 1/2 ( P_j rho + rho P_j ) )`, with `[ H_C, P_j ] = 0` | stratified retention in invariant layers | hill / citadel |

### 3.2 Direct-frame versus conjugated-frame law

The direct-frame versus conjugated-frame split is:

| Function | Frame law |
|---|---|
| `Se` | `tilde(rho)(u) = rho(u)` |
| `Ne` | `tilde(rho)(u) = rho(u)` |
| `Ni` | `tilde(rho)(u) = V_s(u)^dagger rho(u) V_s(u)` |
| `Si` | `tilde(rho)(u) = V_s(u)^dagger rho(u) V_s(u)` |

with the co-rotating frame unitary

```text
V_s(u) = exp( -i H_s u )
```

and

```text
H_left = + H_0
H_right = - H_0
```

### 3.3 Fiber and base realizations for each perceiving function

Each perceiving function appears on both loop geometries:

| Runtime terrain id | Perceiving function | Loop geometry |
|---|---|---|
| `Se_f` | `Se` | fiber loop |
| `Si_f` | `Si` | fiber loop |
| `Ne_f` | `Ne` | fiber loop |
| `Ni_f` | `Ni` | fiber loop |
| `Se_b` | `Se` | lifted base loop |
| `Si_b` | `Si` | lifted base loop |
| `Ne_b` | `Ne` | lifted base loop |
| `Ni_b` | `Ni` | lifted base loop |

### 3.4 The eight terrain realizations

The eight runtime terrains are the four perceiving functions embedded into the two loop geometries.

The important rule is:

- the **topology law** is inherited from `Se`, `Ne`, `Ni`, or `Si`
- the **path law** is inherited from the fiber loop or the lifted base loop

So each terrain has:

1. a topology generator law
2. a loop path law
3. a density-change law

| Terrain | Topology law | Exact path | Exact density law | Expansion or compression | Open or closed | Representation frame | Native judging functions | Terrain-name family |
|---|---|---|---|---|---|---|---|---|
| `Se_f` | `dot(rho) = sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) ) - i epsilon_Se [ H_0, rho ]` | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | expansion | open / isothermal | direct | `Ti`, `Fi` | funnel / cannon |
| `Si_f` | `dot(rho) = -i [ H_C, rho ] + sum_j kappa_j ( P_j rho P_j - 1/2 ( P_j rho + rho P_j ) )`, with `[ H_C, P_j ] = 0` | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | compression | closed / adiabatic | conjugated | `Te`, `Fe` | hill / citadel |
| `Ne_f` | `dot(rho) = -i [ H_0, rho ] + epsilon_Ne sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) )` | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | expansion | closed / adiabatic | direct | `Ti`, `Fi` | vortex / spiral |
| `Ni_f` | `dot(rho) = ( L_P rho L_P^dagger - 1/2 ( L_P^dagger L_P rho + rho L_P^dagger L_P ) ) - i epsilon_Ni [ H_0, rho ]` | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | `rho_fiber^s(u) = rho_fiber^s(0)` | compression | open / isothermal | conjugated | `Te`, `Fe` | pit / source |
| `Se_b` | `dot(rho) = sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) ) - i epsilon_Se [ H_0, rho ]` | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | expansion | open / isothermal | direct | `Ti`, `Fi` | funnel / cannon |
| `Si_b` | `dot(rho) = -i [ H_C, rho ] + sum_j kappa_j ( P_j rho P_j - 1/2 ( P_j rho + rho P_j ) )`, with `[ H_C, P_j ] = 0` | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | compression | closed / adiabatic | conjugated | `Te`, `Fe` | hill / citadel |
| `Ne_b` | `dot(rho) = -i [ H_0, rho ] + epsilon_Ne sum_k ( L_k rho L_k^dagger - 1/2 ( L_k^dagger L_k rho + rho L_k^dagger L_k ) )` | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | expansion | closed / adiabatic | direct | `Ti`, `Fi` | vortex / spiral |
| `Ni_b` | `dot(rho) = ( L_P rho L_P^dagger - 1/2 ( L_P^dagger L_P rho + rho L_P^dagger L_P ) ) - i epsilon_Ni [ H_0, rho ]` | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | `rho_base^s(u) = |gamma_base^s(u)><gamma_base^s(u)|` | compression | open / isothermal | conjugated | `Te`, `Fe` | pit / source |

Short read:

- the four fiber terrains are density-stationary
- the four lifted-base terrains are density-traversing
- the topology generator law stays the same when only the loop embedding changes

### 3.5 IGT quadrant assignment of the perceiving functions

This is the current chart-facing IGT structure:

| Perceiving function | IGT quadrant |
|---|---|
| `Ne` | `WinLose` |
| `Si` | `WinWin` |
| `Se` | `LoseWin` |
| `Ni` | `LoseLose` |

This chart assignment is **not** the geometry itself. It is the current stage-grammar labeling of the perceiving topologies.

---

## 4. The Four Judging Functions

These four are not topology classes. They are the operator family acting on the state.

### 4.1 Exact judging-function table

| Function | Exact channel | Exact infinitesimal generator | Mathematical class | Native terrain frame |
|---|---|---|---|---|
| `Ti` | `rho -> (1 - q_1) rho + q_1 ( P_0 rho P_0 + P_1 rho P_1 )` | `L_Ti(rho) = (kappa_1 / 2) ( sigma_z rho sigma_z - rho )` | dephasing / projection along the `z` basis | direct-frame terrains `Se`, `Ne` |
| `Te` | `rho -> (1 - q_2) rho + q_2 ( Q_+ rho Q_+ + Q_- rho Q_- )` | `L_Te(rho) = (kappa_2 / 2) ( sigma_x rho sigma_x - rho )` | dephasing / projection along the `x` basis | conjugated-frame terrains `Ni`, `Si` |
| `Fi` | `rho -> U_x(theta) rho U_x(theta)^dagger`, with `U_x(theta) = exp( -i theta sigma_x / 2 )` | `L_Fi(rho) = -i [ (omega_3 / 2) sigma_x, rho ]` | unitary rotation about the `x` axis | direct-frame terrains `Se`, `Ne` |
| `Fe` | `rho -> U_z(phi) rho U_z(phi)^dagger`, with `U_z(phi) = exp( -i phi sigma_z / 2 )` | `L_Fe(rho) = -i [ (omega_4 / 2) sigma_z, rho ]` | unitary rotation about the `z` axis | conjugated-frame terrains `Ni`, `Si` |

### 4.2 Kernel-family split

| Function | Kernel family |
|---|---|
| `Ti` | dephasing / projection family |
| `Te` | dephasing / projection family |
| `Fi` | unitary rotation family |
| `Fe` | unitary rotation family |

### 4.3 Direct-frame affinity versus conjugated-frame affinity

| Terrain frame | Native judging functions |
|---|---|
| direct frame (`Se`, `Ne`) | `Ti`, `Fi` |
| conjugated frame (`Ni`, `Si`) | `Te`, `Fe` |

---

## 5. Exact Ordered-Token Law

The current system does not stop at individual perceiving or judging functions.
It also uses ordered pair tokens.

The token is determined by:

1. the perceiving topology
2. the judging kernel family
3. whether operator-first order or terrain-first order is active

### 5.1 Operator-first and terrain-first

| Order | Meaning |
|---|---|
| operator first | the judging function is written first |
| terrain first | the perceiving function is written first |

### 5.2 Full token table

| Perceiving function | Dephasing token, operator first | Dephasing token, terrain first | Rotation token, operator first | Rotation token, terrain first |
|---|---|---|---|---|
| `Se` | `TiSe` | `SeTi` | `FiSe` | `SeFi` |
| `Ne` | `TiNe` | `NeTi` | `FiNe` | `NeFi` |
| `Ni` | `TeNi` | `NiTe` | `FeNi` | `NiFe` |
| `Si` | `TeSi` | `SiTe` | `FeSi` | `SiFe` |

This is the exact current ordered-token law used by the address tables and the `64`-step audit.

### 5.3 The eight signed judging-function variants

These are the four judging functions with the two possible precedence variants.

Important rule:

- the **operator map** does not change between up and down
- the **signed variant** changes the ordered token position in the stage grammar

| Signed judging variant | Exact operator map | Exact infinitesimal generator | Precedence meaning | Exact ordered tokens | Native topology set | Current chart placements |
|---|---|---|---|---|---|---|
| `Ti` with up precedence | `rho -> (1 - q_1) rho + q_1 ( P_0 rho P_0 + P_1 rho P_1 )` | `L_Ti(rho) = (kappa_1 / 2) ( sigma_z rho sigma_z - rho )` | operator first | `TiSe`, `TiNe` | `Se`, `Ne` | type-one outer `Se`; type-two inner `Ne` |
| `Ti` with down precedence | `rho -> (1 - q_1) rho + q_1 ( P_0 rho P_0 + P_1 rho P_1 )` | `L_Ti(rho) = (kappa_1 / 2) ( sigma_z rho sigma_z - rho )` | terrain first | `SeTi`, `NeTi` | `Se`, `Ne` | type-two inner `Se`; type-one outer `Ne` |
| `Fe` with up precedence | `rho -> U_z(phi) rho U_z(phi)^dagger`, with `U_z(phi) = exp( -i phi sigma_z / 2 )` | `L_Fe(rho) = -i [ (omega_4 / 2) sigma_z, rho ]` | operator first | `FeSi`, `FeNi` | `Si`, `Ni` | type-one outer `Si`; type-two inner `Ni` |
| `Fe` with down precedence | `rho -> U_z(phi) rho U_z(phi)^dagger`, with `U_z(phi) = exp( -i phi sigma_z / 2 )` | `L_Fe(rho) = -i [ (omega_4 / 2) sigma_z, rho ]` | terrain first | `SiFe`, `NiFe` | `Si`, `Ni` | type-two inner `Si`; type-one outer `Ni` |
| `Te` with up precedence | `rho -> (1 - q_2) rho + q_2 ( Q_+ rho Q_+ + Q_- rho Q_- )` | `L_Te(rho) = (kappa_2 / 2) ( sigma_x rho sigma_x - rho )` | operator first | `TeNi`, `TeSi` | `Ni`, `Si` | type-one inner `Ni`; type-two outer `Si` |
| `Te` with down precedence | `rho -> (1 - q_2) rho + q_2 ( Q_+ rho Q_+ + Q_- rho Q_- )` | `L_Te(rho) = (kappa_2 / 2) ( sigma_x rho sigma_x - rho )` | terrain first | `NiTe`, `SiTe` | `Ni`, `Si` | type-two outer `Ni`; type-one inner `Si` |
| `Fi` with up precedence | `rho -> U_x(theta) rho U_x(theta)^dagger`, with `U_x(theta) = exp( -i theta sigma_x / 2 )` | `L_Fi(rho) = -i [ (omega_3 / 2) sigma_x, rho ]` | operator first | `FiNe`, `FiSe` | `Ne`, `Se` | type-one inner `Ne`; type-two outer `Se` |
| `Fi` with down precedence | `rho -> U_x(theta) rho U_x(theta)^dagger`, with `U_x(theta) = exp( -i theta sigma_x / 2 )` | `L_Fi(rho) = -i [ (omega_3 / 2) sigma_x, rho ]` | terrain first | `NeFi`, `SeFi` | `Ne`, `Se` | type-two outer `Ne`; type-one inner `Se` |

This is the full current list of the eight signed judging-function variants.

---

## 6. IGT Structure

The current repo keeps IGT as a **stage grammar**. It is not the operator algebra and it is not the carrier geometry.

### 6.1 Topology-to-IGT map

| Perceiving function | IGT quadrant | Dephasing strategy | Rotation strategy |
|---|---|---|---|
| `Ne` | `WinLose` | `NeTi` | `FiNe` |
| `Si` | `WinWin` | `SiTe` | `FeSi` |
| `Se` | `LoseWin` | `TiSe` | `SeFi` |
| `Ni` | `LoseLose` | `TeNi` | `NiFe` |

### 6.2 Outer-loop and inner-loop meaning

| Loop realization | Meaning in the current chart grammar |
|---|---|
| outer loop | `WIN` / `LOSE` in capital letters |
| inner loop | `win` / `lose` in lower-case letters |

### 6.3 Engine type one full chart

Engine type one uses:

- outer loop: deductive order on the lifted base loop
- inner loop: inductive order on the fiber loop

| Step | Perceiving function | Outer token | Outer outcome | Inner token | Inner outcome |
|---|---|---|---|---|---|
| 1 | `Se` | `TiSe` | `LOSE` | `SeFi` | `win` |
| 2 | `Ne` | `NeTi` | `WIN` | `FiNe` | `lose` |
| 3 | `Ni` | `NiFe` | `LOSE` | `TeNi` | `lose` |
| 4 | `Si` | `FeSi` | `WIN` | `SiTe` | `win` |

### 6.4 Engine type two full chart

Engine type two uses:

- outer loop: inductive order on the fiber loop
- inner loop: deductive order on the lifted base loop

| Step | Perceiving function | Outer token | Outer outcome | Inner token | Inner outcome |
|---|---|---|---|---|---|
| 1 | `Se` | `FiSe` | `WIN` | `SeTi` | `lose` |
| 2 | `Si` | `TeSi` | `WIN` | `SiFe` | `win` |
| 3 | `Ni` | `NiTe` | `LOSE` | `FeNi` | `lose` |
| 4 | `Ne` | `NeFi` | `LOSE` | `TiNe` | `win` |

### 6.5 Signed judging operators

The chart also tracks eight signed judging operators:

| Signed operator | Ordered tokens |
|---|---|
| `Ti` with operator-first order | `TiSe`, `TiNe` |
| `Ti` with terrain-first order | `SeTi`, `NeTi` |
| `Fe` with operator-first order | `FeSi`, `FeNi` |
| `Fe` with terrain-first order | `SiFe`, `NiFe` |
| `Te` with operator-first order | `TeNi`, `TeSi` |
| `Te` with terrain-first order | `NiTe`, `SiTe` |
| `Fi` with operator-first order | `FiNe`, `FiSe` |
| `Fi` with terrain-first order | `NeFi`, `SeFi` |

### 6.6 Axiswise Jung And IGT Pairings

This packet now makes the axiswise Jung and IGT pairings explicit.

These pairings are still label layers. They do not replace the underlying geometry or operator mathematics.

| Axis | Explicit Jung pairing | Explicit IGT pairing |
|---|---|---|
| `Axis 0` | `Ni/Ne` versus `Si/Se` | `WinLose/LoseLose` versus `LoseWin/WinWin` |
| `Axis 1` | `Se/Ni` versus `Ne/Si` | `LoseWin/LoseLose` versus `WinLose/WinWin` |
| `Axis 2` | `Se/Ne` versus `Si/Ni` | `LoseWin/WinLose` versus `WinWin/LoseLose` |
| `Axis 3` | inner token set versus outer token set | inner token set versus outer token set |
| `Axis 4` | proposed pair-order split `TiFe` versus `FeTi` | implemented loop-family split `FeTi` versus `TeFi` |
| `Axis 5` | `FeFi` versus `TiTe` | rotation-class tokens versus dephasing-class tokens |
| `Axis 6` | judging-first versus perceiving-first ordered pairs | up versus down ordered tokens |

The explicit `Axis 3` token partition is:

| Side | Exact token set |
|---|---|
| inner | type two: `TiNe`, `FeNi`, `SeTi`, `SiFe`; type one: `TeNi`, `FiNe`, `SiTe`, `SeFi` |
| outer | type one: `NeTi`, `NiFe`, `TiSe`, `FeSi`; type two: `NiTe`, `NeFi`, `TeSi`, `FiSe` |

The explicit `Axis 5` token-family partition is:

| Side | Exact token set |
|---|---|
| rotation-class side | `FiNe`, `NeFi`, `FiSe`, `SeFi`, `FeNi`, `NiFe`, `FeSi`, `SiFe` |
| dephasing-class side | `TiNe`, `NeTi`, `TiSe`, `SeTi`, `TeNi`, `NiTe`, `TeSi`, `SiTe` |

The explicit `Axis 6` order partition is:

| Side | Exact ordered-token set |
|---|---|
| judging first | `TiSe`, `TiNe`, `FeSi`, `FeNi`, `TeNi`, `TeSi`, `FiNe`, `FiSe` |
| perceiving first | `SeTi`, `NeTi`, `SiFe`, `NiFe`, `NiTe`, `SiTe`, `NeFi`, `SeFi` |

---

## 7. Runtime Geometry Versus IGT Chart Geometry

These are **not** the same thing.

### 7.1 Runtime geometry

The runtime geometry is:

1. normalized spinor carrier on `S^3`
2. Hopf projection to `S^2`
3. nested Hopf tori at latitude `eta`
4. fiber-loop and lifted-base-loop path families
5. left and right Weyl sheet realization

### 7.2 IGT chart geometry

The IGT chart structure is:

1. four perceiving topologies
2. two loop realizations for each topology
3. two engine-type orientations
4. one outer outcome label and one inner outcome label for each topology
5. one ordered-token pair for each stage realization

### 7.3 Exact separation

| Thing | What it is |
|---|---|
| `Se`, `Ne`, `Ni`, `Si` | topology-and-flow classes on the carrier geometry |
| `Ti`, `Te`, `Fi`, `Fe` | operator maps acting on the state |
| `TiSe`, `NeTi`, `FeSi`, `NiFe`, and the rest | ordered function tokens combining topology and operator |
| `WIN`, `LOSE`, `win`, `lose` | IGT stage labels |

---

## 8. One Complete Map

This is the compact whole picture.

| Layer | Exact objects |
|---|---|
| carrier geometry | `S^3`, `S^2`, nested Hopf tori, fiber loop, lifted base loop, left Weyl sheet, right Weyl sheet |
| perceiving functions | `Se`, `Ne`, `Ni`, `Si` |
| judging functions | `Ti`, `Te`, `Fi`, `Fe` |
| ordered pair tokens | `TiSe`, `SeTi`, `FiSe`, `SeFi`, `TiNe`, `NeTi`, `FiNe`, `NeFi`, `TeNi`, `NiTe`, `FeNi`, `NiFe`, `TeSi`, `SiTe`, `FeSi`, `SiFe` |
| IGT quadrant labels | `WinLose`, `WinWin`, `LoseWin`, `LoseLose` |
| IGT stage outcomes | `WIN`, `LOSE`, `win`, `lose` |
| engine type one stage rows | `TiSe`, `NeTi`, `NiFe`, `FeSi`, `SeFi`, `SiTe`, `TeNi`, `FiNe` |
| engine type two stage rows | `FiSe`, `TeSi`, `NiTe`, `NeFi`, `SeTi`, `SiFe`, `FeNi`, `TiNe` |

---

## 9. Current Strongest Read

The strongest current explicit read is:

- `Se`, `Ne`, `Ni`, and `Si` are the perceiving topology classes on the carrier geometry
- `Ti`, `Te`, `Fi`, and `Fe` are the judging operators acting on density matrices
- each perceiving topology appears on both loop geometries
- the current runtime uses a fixed four-operator subcycle
- the ordered tokens are generated by topology plus operator family plus token order
- the IGT structure labels the stage grammar, not the operator algebra and not the carrier geometry

---

## Primary Sources For This Packet

1. `system_v4/docs/AXIS_0_1_2_QIT_MATH.md`
2. `system_v4/docs/AXIS_3_4_5_6_QIT_MATH.md`
3. `system_v4/docs/TERRAIN_LAW_LEDGER.md`
4. `system_v4/docs/TERRAIN_NAMING_MATH_LEDGER.md`
5. `system_v4/docs/ENGINE_GRAMMAR_DISCRETE.md`
6. `system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md`
7. `system_v4/docs/MATH_CHART_CORRELATION_MATRIX.md`
8. `system_v4/docs/AXIS_PRIMITIVE_DERIVED.md`
9. `system_v4/probes/engine_core.py`
10. `system_v4/probes/sim_64_address_audit.py`
