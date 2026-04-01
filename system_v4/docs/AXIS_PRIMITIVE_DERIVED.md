# AXIS PRIMITIVE vs DERIVED TABLE

**Date:** 2026-03-29
**Status:** Updated authority table aligned to the locked axis packets and terrain-law ledger.

---

## Primitive axes

| Axis | Role | Values |
|---|---|---|
| Ax0 | torus-latitude entropy seat plus hemisphere threshold | continuous `eta` field / discrete `sgn(cos(2eta))` |
| Ax2 | representation frame | direct / conjugated |
| Ax3 | loop/path class | fiber / base-lift |
| Ax5 | generator family | T-kernel / F-kernel |

Derived, not primitive:

- Ax1 = Ax0 × Ax2 reduced branch split
- Ax4 = loop ordering / commutation family
- Ax6 = precedence closure `b6 = -b0*b3`

---

## Derived Axes And Closures

| Derived thing | From | Rule |
|---|---|---|
| Ax1 branch split | Ax0 × Ax2 | `U` branch = Se/Ni, `NU` branch = Ne/Si |
| Ax4 loop ordering | Ax3 × engine law | `UEUE` vs `EUEU` |
| Ax6 precedence | Ax0 × Ax3 | `b6 = -b0*b3` |
| Engine type | Ax3 × Ax4 | T1 = (outer,FeTi) or (inner,TeFi). T2 = (outer,TeFi) or (inner,FeTi). |
| IN/OUT flux | engine type + ambient geometry | T1 = IN, T2 = OUT. Not a primitive local axis. |
| Major/minor casing | Ax3 | outer = WIN/LOSE (major). inner = win/lose (minor). |
| Signed operator | Ax5 × Ax6 | T/F × UP/DOWN → one of 8 signed ops. |
| Token identity | topology + Ax5 + Ax6 | e.g. Se + T + UP = TiSe. |
| Chirality | Ax3 × Ax4 + ambient constraint | Left/Right Weyl. Geometry-level, not loop-local. |

---

## Addressing scheme

### Layer 1: Topology (Ax0 × Ax2)

| Ax0 | Ax2 | Topology |
|---|---|---|
| S | exp | Se |
| N | exp | Ne |
| N | cmp | Ni |
| S | cmp | Si |

### Layer 2: Loop embedding (Ax3 × Ax4)

| Ax3 | Ax4 | Engine type (derived) | Loop |
|---|---|---|---|
| outer | FeTi | T1 | T1 outer |
| inner | TeFi | T1 | T1 inner |
| outer | TeFi | T2 | T2 outer |
| inner | FeTi | T2 | T2 inner |

### Layer 3: Local substage (Ax5 × Ax6)

At every topology, Ax5 × Ax6 gives exactly 4 local substages:

| Ax5 | Ax6 | Se token | Ne token | Ni token | Si token |
|---|---|---|---|---|---|
| T | UP | TiSe | TiNe | TeNi | TeSi |
| T | DOWN | SeTi | NeTi | NiTe | SiTe |
| F | UP | FiSe | FiNe | FeNi | FeSi |
| F | DOWN | SeFi | NeFi | NiFe | SiFe |

---

## Full address formula

```
macro_stage = topology(Ax0, Ax2) + loop(Ax3, Ax4)    → 16 stages
micro_step  = macro_stage + substep(Ax5, Ax6) + op_slot    → 64 steps
```

Where:
- `topology(Ax0, Ax2)` selects Se, Ne, Ni, or Si
- `loop(Ax3, Ax4)` selects one of 4 loop contexts
- `substep(Ax5, Ax6)` selects which signed operator at that stage
- `op_slot` is the runtime clock position (not an axis — it's order memory)

---

## Ax1 role

Ax1 (Se/Ni vs Ne/Si) is the cross-diagonal partition. It is NOT independent of Ax0 and Ax2 — knowing any two determines the third.

Ax1 encodes which **graph edge** the traversal is currently on:
- Ax0 edges: Se↔Si, Ne↔Ni
- Ax2 edges: Se↔Ne, Si↔Ni
- Ax1 edges: Se↔Ni, Ne↔Si (cross-diagonal)

Ax1 is a **transition/dynamics** axis, not a position axis.

---

## Collision check

Verified by script against all 16 chart-locked macro-stages:

| Check | Result |
|---|---|
| Ax0 × Ax2 × Ax3 × Ax4 → 16 unique macro-stage addresses | PASS ✓ |
| Ax5 × Ax6 → 4 unique local substages at every topology | PASS ✓ |
| Full 64-microstep addressing | PASS ✓ |

---

## What this changes

The most important consequence: **IN/OUT flux is derived, not primitive**.

This means:
- Ax3 is directly structural (fiber vs base-lift; inner/outer is an engine overlay)
- Engine type is a compound property of Ax3 and Ax4
- The Weyl spinor chirality comes from geometry external to the loop system
- Many previously confusing labels (chirality, flux, casing) become derived invariants
- Less collapse-prone: engine type is no longer stuffed into one axis
