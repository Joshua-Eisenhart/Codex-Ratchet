# Taijitu Axes 0 Through 6 Explicit Symbolic Layer

**Date:** 2026-03-30  
**Status:** Working support surface. Proposal-only symbolic layer.  
**Scope:** This packet gathers the explicit yin-yang, taijitu, I Ching, Jung, and IGT mappings for `Axis 0` through `Axis 6` without replacing the underlying engine mathematics.

---

## 1. Honesty Boundary

This packet keeps five things separate:

1. the actual lower-axis mathematics
2. the actual simulated geometry
3. the taijitu symbolic layer
4. the Jung and IGT label layer
5. the still-open or inverted symbolic assignments

The most important honesty points are:

- the active lower stack is `Axis 0` through `Axis 6`
- the taijitu layer is representational and comparative, not primary math
- `Axis 0` is still open at the bridge-and-cut level
- `Axis 3`, `Axis 4`, and `Axis 5` still carry open symbolic overlays
- the older probe [sim_yinyang_axis_mapping.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_yinyang_axis_mapping.py) contains earlier hypotheses that are not identical to the current lower-stack mapping

---

## 2. Exact Symbol Geometry Scaffold

### 2.1 The outer circle

The outer circle of the taijitu is treated here as the enclosing driven field:

```text
outer symbolic drive = Axis 0
```

This does **not** mean `Axis 0` is the full geometry itself.

The current math anchor remains:

```text
b_0 = sign( cos(2 eta) )
```

with:

```text
eta < pi / 4  -> upper or white side
eta = pi / 4  -> neutral threshold
eta > pi / 4  -> lower or black side
```

### 2.2 The taijitu on the Clifford torus

The live symbolic geometry witness already present in the repo uses:

```text
q(theta_1, theta_2)
= ( cos(pi/4) exp(i theta_1), sin(pi/4) exp(i theta_2) )
```

on the Clifford torus.

In that probe, the symbolic boundary uses:

```text
theta_1 = theta_2
```

and also

```text
theta_1 = theta_2 + pi
```

as the two branches of the S-curve.

### 2.3 Black and white regions

The same probe uses:

```text
black region: theta_1 - theta_2 in (0, pi)
white region: theta_1 - theta_2 in (pi, 2 pi)
```

That remains a useful symbolic geometry witness, but it does not override the lower-stack `Axis 0` seat and bridge definitions.

### 2.4 Dots

The same symbolic probe records the dot limits as:

```text
black dot: eta -> 0
white dot: eta -> pi / 2
```

These are treated here as symbolic limit points inside the taijitu layer.

---

## 3. Master Axis Table

| Axis | Explicit taijitu feature | Explicit Jung pairing | Explicit IGT pairing | Exact current math anchor | Current symbolic status |
|---|---|---|---|---|---|
| `Axis 0` | black versus white, plus the enclosing circle | `Ni/Ne` versus `Si/Se` | `WinLose/LoseLose` versus `LoseWin/WinWin` | `b_0 = sign( cos(2 eta) )`, later `Phi_0(rho_AB)` | strong symbolic alignment, bridge still open |
| `Axis 1` | black dot in white teardrop versus white dot in black teardrop | `Se/Ni` versus `Ne/Si` | `LoseWin/LoseLose` versus `WinLose/WinWin` | branch split derived from `Axis 0` and `Axis 2` | usable symbolic alignment |
| `Axis 2` | dots versus teardrops | `Se/Ne` versus `Si/Ni` | `LoseWin/WinLose` versus `WinWin/LoseLose` | direct versus conjugated frame | usable symbolic alignment |
| `Axis 3` | inner tail-chasing versus outer fat-tip-chasing | inner token set versus outer token set | inner token set versus outer token set | fiber versus lifted-base loop class | currently strongest symbolic reading |
| `Axis 4` | clockwise versus counterclockwise spin | proposed `TiFe` versus `FeTi` | implemented `FeTi` versus `TeFi` | `Phi_deductive = U circle E circle U circle E`, `Phi_inductive = E circle U circle E circle U` | open symbolic assignment |
| `Axis 5` | S-curve form family, lobe weighting, flatter versus curvier | `FeFi` versus `TiTe` | rotation-class tokens versus dephasing-class tokens | dephasing-family versus rotation-family split | open symbolic overlay |
| `Axis 6` | up versus down reading of the same symbol | judging-first versus perceiving-first ordered pairs | up versus down ordered tokens | `b_6 = - b_0 b_3` | strong symbolic alignment |

---

## 4. Axis 0

### 4.1 Explicit symbolic reading

`Axis 0` is the black-versus-white split and the enclosing circular drive of the symbol.

The current explicit symbolic assignment is:

| Side | Jung functions | IGT outcomes |
|---|---|---|
| white / yang | `Ne`, `Ni` | `WinLose`, `LoseLose` |
| black / yin | `Se`, `Si` | `LoseWin`, `WinWin` |

### 4.2 Exact current math anchor

The current lower-stack math anchor remains:

```text
b_0 = sign( cos(2 eta) ) = sign( r_z )
```

and:

```text
S( rho_bar(eta) )
= - cos^2(eta) log( cos^2(eta) )
   - sin^2(eta) log( sin^2(eta) )
```

The symbolic layer does **not** replace the later cut-state family:

```text
Phi_0(rho_AB)
```

### 4.3 Exact symbolic caution

The taijitu side of `Axis 0` is strong.

The final `Axis 0` cut-state bridge is still open.

---

## 5. Axis 1

### 5.1 Explicit symbolic reading

The explicit symbolic split is:

| Side | Symbol feature | Jung pairing | IGT pairing |
|---|---|---|---|
| first side | black dot in white teardrop | `Ni`, `Se` | `LoseLose`, `LoseWin` |
| second side | white dot in black teardrop | `Ne`, `Si` | `WinLose`, `WinWin` |

### 5.2 Exact current math anchor

The lower-stack anchor is:

```text
Axis 1 = { Se, Ni } versus { Ne, Si }
```

### 5.3 Useful comparison to older probe language

The older symbolic probe also described `Axis 1` as interpenetration:

```text
rho_interpenetration = rho - rho_diagonal_blocks
```

That remains a useful symbolic witness, but the current atlas keeps the lower-stack branch split explicit.

---

## 6. Axis 2

### 6.1 Explicit symbolic reading

The explicit symbolic split is:

| Side | Symbol feature | Jung pairing | IGT pairing |
|---|---|---|---|
| first side | teardrops | `Ne`, `Se` | `WinLose`, `LoseWin` |
| second side | dots | `Si`, `Ni` | `WinWin`, `LoseLose` |

### 6.2 Exact current math anchor

The lower-stack anchor is:

```text
direct side = { Se, Ne }
conjugated side = { Si, Ni }
```

and:

```text
tilde(rho) = rho
```

versus

```text
tilde(rho) = V_s^dagger rho V_s
```

### 6.3 Older symbolic-probe witness

The older symbolic probe used:

```text
rho_dot - rho_drop
```

to represent concentrated versus spread symbolic structure.

That remains useful as a symbolic witness, but the lower-stack anchor remains the direct-versus-conjugated frame split.

---

## 7. Axis 1 Times Axis 2 Four-Part Table

This is the current explicit four-part placement:

| Slot in the symbol | Function | IGT quadrant |
|---|---|---|
| white dot | `Ni` | `LoseLose` |
| black teardrop | `Se` | `LoseWin` |
| white teardrop | `Ne` | `WinLose` |
| black dot | `Si` | `WinWin` |

This is the cleanest current `Axis 1 x Axis 2` taijitu table.

---

## 8. Axis 3

### 8.1 Explicit symbolic reading

The strongest current symbolic reading is:

| Side | Symbol feature | Current explicit token set |
|---|---|---|
| inner | tail chasing | type two: `TiNe`, `FeNi`, `SeTi`, `SiFe`; type one: `TeNi`, `FiNe`, `SiTe`, `SeFi` |
| outer | fat-tip chasing | type one: `NeTi`, `NiFe`, `TiSe`, `FeSi`; type two: `NiTe`, `NeFi`, `TeSi`, `FiSe` |

### 8.2 Exact current math anchor

The lower-stack anchor is:

```text
fiber path:
gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)
```

and:

```text
lifted base path:
gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)
```

### 8.3 Explicit caution

The older symbolic probe mapped `Axis 3` to mirror-flip and left/right chirality.

The current lower-stack atlas does **not** use that as the active `Axis 3` definition.

The current stronger symbolic reading is inner versus outer.

---

## 9. Axis 4

### 9.1 Explicit symbolic reading

The explicit open symbolic split is:

| Side | Symbol feature | Current status |
|---|---|---|
| first side | clockwise spin | open |
| second side | counterclockwise spin | open |

### 9.2 Explicit Jung and IGT layer

The current explicit label layer is:

| Layer | Explicit split |
|---|---|
| Jung-facing symbolic layer | `TiFe` versus `FeTi` |
| implemented runtime family | `FeTi` versus `TeFi` |

### 9.3 Exact current math anchor

The lower-stack anchor is:

```text
Phi_deductive = U circle E circle U circle E
```

and:

```text
Phi_inductive = E circle U circle E circle U
```

### 9.4 Explicit caution

The symbolic spin direction is still open.

The implemented loop family is clearer than the symbolic clockwise-versus-counterclockwise assignment.

---

## 10. Axis 5

### 10.1 Explicit symbolic reading

The explicit symbolic candidates are:

| Candidate symbolic split | Current status |
|---|---|
| flatter S-curve versus curvier S-curve | open |
| smaller lobe contrast versus larger lobe contrast | open |
| white-heavier versus black-heavier visual weighting | symbolic metaphor only |

### 10.2 Explicit Jung and IGT layer

The explicit current pair layer is:

| Layer | Explicit split |
|---|---|
| Jung layer | `FeFi` versus `TiTe` |
| IGT token-family layer | rotation-class tokens versus dephasing-class tokens |

The exact token-family partition is:

| Side | Exact tokens |
|---|---|
| rotation-class side | `FiNe`, `NeFi`, `FiSe`, `SeFi`, `FeNi`, `NiFe`, `FeSi`, `SiFe` |
| dephasing-class side | `TiNe`, `NeTi`, `TiSe`, `SeTi`, `TeNi`, `NiTe`, `TeSi`, `SiTe` |

### 10.3 Exact current math anchor

The lower-stack anchor is:

```text
dephasing family = { Ti, Te }
rotation family = { Fi, Fe }
```

---

## 11. Axis 6

### 11.1 Explicit symbolic reading

The strongest current symbolic reading is:

| Side | Symbol feature | Explicit ordered-pair law |
|---|---|---|
| up | reading where the judging side leads | judging-first tokens |
| down | reading where the perceiving side leads | perceiving-first tokens |

### 11.2 Exact token-family split

| Side | Exact token set |
|---|---|
| judging first | `TiSe`, `TiNe`, `FeSi`, `FeNi`, `TeNi`, `TeSi`, `FiNe`, `FiSe` |
| perceiving first | `SeTi`, `NeTi`, `SiFe`, `NiFe`, `NiTe`, `SiTe`, `NeFi`, `SeFi` |

### 11.3 Exact directional table using Axis 3 and color

| Loop side and color | Direction | Exact token set |
|---|---|---|
| inner and white | up | type two: `TiNe`, `FeNi`; type one: `TeNi`, `FiNe` |
| inner and black | down | type two: `SeTi`, `SiFe`; type one: `SiTe`, `SeFi` |
| outer and white | down | type one: `NeTi`, `NiFe`; type two: `NiTe`, `NeFi` |
| outer and black | up | type one: `TiSe`, `FeSi`; type two: `TeSi`, `FiSe` |

### 11.4 Exact current math anchor

The lower-stack anchor is:

```text
b_6 = - b_0 b_3
```

---

## 12. Six-Line Structural Placement

The current proposal-only structural scaffold stays:

| Line | Axis |
|---|---|
| line 1 | `Axis 6` |
| line 2 | `Axis 5` |
| line 3 | `Axis 3` |
| line 4 | `Axis 4` |
| line 5 | `Axis 1` |
| line 6 | `Axis 2` |

and:

| Object | Placement |
|---|---|
| `Axis 0` | external drive through the six-line space |
| `Axis 7` through `Axis 12` | not part of the current lower six-line symbolic scaffold |

---

## 13. Current Strongest Read

The cleanest current symbolic read is:

- `Axis 0` aligns strongly with black versus white and the enclosing circular drive
- `Axis 1` aligns with the two interpenetrating dot-and-teardrop pairings
- `Axis 2` aligns with dots versus teardrops
- `Axis 3` aligns best with inner versus outer, not left versus right
- `Axis 4` is still symbolically open even though the implemented runtime family is strong
- `Axis 5` is still symbolically open even though the operator-family split is strong
- `Axis 6` aligns strongly with up versus down reading and judging-first versus perceiving-first order

---

## 14. Primary Inputs For This Packet

1. [AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md)
2. [JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP.md)
3. [64_HEXAGRAM_STATE_SPACE.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/64_HEXAGRAM_STATE_SPACE.md)
4. [THE_8X8_ENGINE_MAPPING.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THE_8X8_ENGINE_MAPPING.md)
5. [sim_yinyang_axis_mapping.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/probes/sim_yinyang_axis_mapping.py)
