# MATH-TO-CHART CORRELATION MATRIX

**Date:** 2026-03-27
**Status:** Correlation scaffold. Proposed math treated as proposal, chart surfaces as structured correlation layers.
**Source authority stack:** Constraint ladder (math) → Chart surfaces (correlation) → Axes (decomposition)

---

## Source surfaces used

| Source | File | What it provides |
|---|---|---|
| Topology math | `constraint ladder/Axis 1 2 topology math…md` | 4 flow classes with generators and feature matrix |
| Operator math | `constraint ladder/Axis 4 qit math…md` | CPTP composition orders, inductive/deductive loop words |
| Loop/chirality math | `constraint ladder/Axis 3 math Hopf fiber loop…md` | Hopf fiber vs lifted base loop, 8 stages from topology |
| Engine charts | `system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md` | IGT/chart tables for both engine types |
| Axis decomposition | `system_v4/docs/AXIS_PRIMITIVE_DERIVED.md` | Primitive axes and derived diagonals |

---

## Layer 1: TOPOLOGY MATH (Ax1 × Ax2 → 4 base classes)

| Class | Expansion/Compression | Open/Closed (Ax1) | Generator form | Geometry | Terrain pair |
|---|---|---|---|---|---|
| Se | Expansion | Isothermal (open) | Dissipative Lindblad, `L_k ρ L_k† − ½{L_k†L_k, ρ}`, div > 0 | Radial outward on Bloch ball | **Funnel / Cannon** |
| Ne | Expansion | Adiabatic (closed) | Unitary Hamiltonian, `−i[H,ρ]`, div = 0 | Tangential circulation on S³ | **Vortex / Spiral** |
| Ni | Compression | Isothermal (open) | Dissipative Lindblad with attraction, div < 0 | Radial inward, unique attractor | **Pit / Source** |
| Si | Compression | Adiabatic (closed) | Commuting `[H, P_i] = 0`, invariant subspaces | Stratified retention, no radial motion | **Hill / Citadel** |

**Key partition:** Se/Ni = dissipative (Lindblad). Ne/Si = Hamiltonian (unitary or commuting).

---

## Layer 2: OPERATOR MATH (Ax4 → CPTP composition order)

Two non-commuting operator classes: U = unitary channel, E = non-unitary CPTP.

| Loop family | Operator word | Rosetta order |
|---|---|---|
| Inductive | `U ∘ E ∘ U ∘ E` | Ne → Ni → Se → Si → Ne |
| Deductive | `E ∘ U ∘ E ∘ U` | Ne → Si → Se → Ni → Ne |

**Note:** This Rosetta order from the constraint ladder does NOT match the current chart lock (Se→Si→Ni→Ne / Se→Ne→Ni→Si). This is a known discrepancy — the constraint ladder uses a different starting topology and traversal from the Ax0/Ax2 Hamiltonian graph order.

---

## Layer 3: LOOP MATH (Ax3 → Hopf structure)

| Loop | Math name | Engine name | Properties |
|---|---|---|---|
| Hopf fiber loop | U(1) vertical fiber, `ψ → e^{iθ}ψ` | **Inner loop** | 360° closure, does not change Bloch vector, pure circulation |
| Lifted base loop | Horizontal lift of S² loop into S³ | **Outer loop** | 720° closure, changes Bloch vector, carries Berry phase |

**Structural fact (line 293-296):** Both loops admit the same 4 topological stages. The 8 stages are isomorphic as stage-sets even though the loops are inequivalent.

**Axis-3:** selects engine type (left/right Weyl), orients all stages together. Does NOT change the stage partition.

---

## Layer 4: CORRELATION MATRIX (all layers joined)

Each row is one of the 16 macro-stages. Columns correlate math objects to chart labels.

### Type-1 (Left Weyl, IN flux, H = +n·σ)

| Topo | Terrain | Outer (lifted base loop, deductive) | Signed op | IGT pattern | Ax6 | Inner (Hopf fiber, inductive) | Signed op | IGT pattern | Ax6 |
|---|---|---|---|---|---|---|---|---|---|
| Se | Se-in | TiSe | Ti↑ | LOSE | UP | SeFi | Fi↓ | win | DOWN |
| Ne | Ne-in | NeTi | Ti↓ | WIN | DOWN | FiNe | Fi↑ | lose | UP |
| Ni | Ni-in | NiFe | Fe↓ | LOSE | DOWN | TeNi | Te↑ | lose | UP |
| Si | Si-in | FeSi | Fe↑ | WIN | UP | SiTe | Te↓ | win | DOWN |

### Type-2 (Right Weyl, OUT flux, H = −n·σ)

| Topo | Terrain | Outer (lifted base loop, inductive) | Signed op | IGT pattern | Ax6 | Inner (Hopf fiber, deductive) | Signed op | IGT pattern | Ax6 |
|---|---|---|---|---|---|---|---|---|---|
| Se | Se-out | FiSe | Fi↑ | WIN | UP | SeTi | Ti↓ | lose | DOWN |
| Si | Si-out | TeSi | Te↑ | WIN | UP | SiFe | Fe↓ | win | DOWN |
| Ni | Ni-out | NiTe | Te↓ | LOSE | DOWN | FeNi | Fe↑ | lose | UP |
| Ne | Ne-out | NeFi | Fi↓ | LOSE | DOWN | TiNe | Ti↑ | win | UP |

---

## Layer 5: AXIS DECOMPOSITION (how the math maps to axes)

| Math object | Axis candidate | Status |
|---|---|---|
| Expansion vs compression | **Ax2** | Locked in constraint ladder |
| Open vs closed (isothermal vs adiabatic) | **Ax1** | Locked in constraint ladder |
| Outer (lifted base) vs inner (Hopf fiber) | **Ax3** (new: outer/inner, not IN/OUT) | Proposed — collision-free verified |
| Inductive vs deductive (U∘E vs E∘U) | **Ax4** | Locked in constraint ladder |
| T-kernel vs F-kernel (first/second strategy) | **Ax5** | Locked |
| Operator-first vs terrain-first (composition order) | **Ax6** | Locked in constraint ladder |
| N-perceiving vs S-perceiving | **Ax0** | Locked |
| Engine type (T1/T2), IN/OUT flux, chirality | **Derived** from Ax3 × Ax4 | Proposed |

---

## KNOWN DISCREPANCIES

| Discrepancy | Where | Status |
|---|---|---|
| Loop traversal order differs | Constraint ladder (Ne→Ni→Se→Si / Ne→Si→Se→Ni) vs chart (Se→Si→Ni→Ne / Se→Ne→Ni→Si) | Different starting topology. Same graph edges. Need reconciliation. |
| Ax3 definition | Constraint ladder says chirality / Weyl sign. New proposal says outer/inner. | Not contradictory — chirality = derived from Ax3 × Ax4 in new model |
| 8 stages = topology-before-chirality | Constraint ladder Ax3 doc says 8 stages exist before chirality. Current chart says terrains are split by IN/OUT. | Compatible if IN/OUT is derived, not primitive |
| Operator-stage mapping direction | Constraint ladder says Ax4 "does not define stages, it determines how operators act on them." Current chart bakes operators into stages. | Difference in layer ordering, not contradiction |

---

## WHAT THIS MATRIX DOES NOT CLAIM

- This does not resolve the traversal order discrepancy between constraint ladder and chart
- This does not prove Ax3 = outer/inner is correct (it's a collision-free proposal)
- This does not prove the 64-schedule grid occupancy is complete
- I Ching slot assignments are not included (they are index tags, not math objects)
