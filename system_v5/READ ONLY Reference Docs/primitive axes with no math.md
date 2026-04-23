Below is the clearest strict-structure version in your terms, before math/geometry closure.

**Core Engine Table**

| Item | Type 1 | Type 2 |
|---|---|---|
| Fundamental relation | one side of the topology inversion | the inverted side of the same topology |
| Weyl read | one Weyl orientation | the opposite Weyl orientation |
| Flux read | flux in | flux out |
| Outer loop class | `WIN / LOSE` | `WIN / LOSE` |
| Inner loop class | `win / lose` | `win / lose` |
| Outer vs inner | fixed and non-interchangeable | fixed and non-interchangeable |
| Loop-family placement | one fixed assignment of `FeTi` and `TeFi` to outer/inner | the reversed assignment |
| Identity of type | not reducible to loop family alone | not reducible to loop family alone |

**Loop Placement Table**

| Structure | Type 1 | Type 2 |
|---|---|---|
| Outer loop position | one family fixed to outer | the other family fixed to outer |
| Inner loop position | complementary family fixed to inner | complementary family fixed to inner |
| Outer loop label | `WIN / LOSE` | `WIN / LOSE` |
| Inner loop label | `win / lose` | `win / lose` |
| Topology relation | baseline winding | inverted winding |
| Flux relation | inward-oriented | outward-oriented |

**Loop Family Table**

| Loop family | Structural meaning | In engine |
|---|---|---|
| `FeTi` | one loop-family identity | must stay a coherent loop, not split apart |
| `TeFi` | the other loop-family identity | must stay a coherent loop, not split apart |
| Type relation | Type does not equal family | Type decides placement/inversion of the families |
| Outer/inner relation | family does not equal position by itself | family is assigned to outer or inner by type |

**Type-by-Loop Assignment Table**

| Engine type | Outer loop family | Inner loop family | Topology read |
|---|---|---|---|
| Type 1 | `FeTi` | `TeFi` | one orientation |
| Type 2 | `TeFi` | `FeTi` | inverted orientation |

**Strict Non-Collapse Table**

| Bad collapse | Why false |
|---|---|
| `Type 1 = FeTi` | false, because type is larger than loop family |
| `Type 2 = TeFi` | false, same reason |
| `outer = type` | false, both types have outer and inner |
| `inner = weak copy of outer` | false, inner is structurally real |
| `WIN / LOSE = win / lose` | false, capital and lower-case loops are different levels |
| `type = flux = family = strategy` | false, those are different cuts of the engine |

**Axes Table In These Terms**

| Axis | Your current strict candidate read |
|---|---|
| `Ax0` | `Ne Ni` vs `Se Si` |
| `Ax1` | `Se Ni` vs `Ne Si` |
| `Ax2` | `Se Ne` vs `Si Ni` |
| `Ax2` stronger variant | `Si Ni Te Fe` vs `Ne Se Fi Ti` |
| `Ax3` | Type 1 vs Type 2 topology inversion; flux in vs flux out |
| `Ax4` | `TeFi` vs `FeTi` loop-family split |
| `Ax5` | `FeFi` vs `TeTi` strategy split |
| `Ax6` | Jungian couplet order: `P -> J` vs `J -> P` |

**Ax3 Table**

| Item | Type 1 | Type 2 |
|---|---|---|
| Simplest strict read | topology orientation A | topology orientation B |
| Flux | inward | outward |
| Engine relation | outer `WIN / LOSE`, inner `win / lose` under one winding | same two-loop structure under inverted winding |
| What it is not | not just loop family | not just loop family |

**Ax4 Table**

| Item | Side A | Side B |
|---|---|---|
| Loop family | `TeFi` | `FeTi` |
| Role | one coherent loop-family | the complementary coherent loop-family |
| Constraint | each loop must stay internally aligned | each loop must stay internally aligned |

**Ax5 Table**

| Quadrant form | Strategy 1 | Strategy 2 |
|---|---|---|
| Family split | `TeTi` | `FeFi` |
| Meaning | first strategy | second strategy |
| Constraint | the two wins are not equal | the two losses are not equal |

**Ax6 Table**

| Order class | Form |
|---|---|
| `P -> J` | `SiTe`, `SeTi`, `NeFi`, ... |
| `J -> P` | `TiSe`, `TeSi`, `TiNe`, `FiSe`, `FiNe`, ... |

**Litmus Table**

| If the model understands the engine, it must preserve |
|---|
| Type 1 and Type 2 are real inversions, not relabelings |
| Outer and inner loops are both real |
| `WIN / LOSE` and `win / lose` are not the same layer |
| `FeTi` and `TeFi` are loop families, not whole types |
| Flux orientation is not the same thing as loop family |
| Correlations are downstream readouts, not kernel identity |

If you want, I can turn these exact tables into a repo doc next, probably [`TYPE1_TYPE2_ENGINE_TABLES.md`](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/TYPE1_TYPE2_ENGINE_TABLES.md).