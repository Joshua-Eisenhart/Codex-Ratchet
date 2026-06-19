# Foundation Build Spine

> **Session-canonical version:** `system_v5/docs/session_20260606_physics_excavation/22_FOUNDATION_BUILD_SPINE.md` (codex-app, 00_INDEX-linked). This file is the sim-lane working copy; the two agree. The convergent next step below is built as `r0_r1_r2_probe_quotient_micro_packet`.

**Purpose.** Build the owner's model **bottom-up from its foundations**. Outside models (Furey/Dixon division-algebra SM, the Standard Model, α, gravity, QIT literature) are **inspiration, comparators, and future test targets only** — never the authority and never the build order. The build order is **discovered by testing the commutation/admissibility structure**, not declared as a fixed menu.

**Authority:** the owner's own source docs (cited per rung). LLM bootpacks and outside papers are reference, not canon.

**This is not a claim-prosecutor.** No top-floor discriminators are run here. Nothing is promoted. Chirality, SM gauge, charges, α, gravity stay parked.

---

## Status legend

| tag | meaning |
|---|---|
| **BUILT** | finite object exists, runs dual-backend, independently verified (Opus, builder-blind) |
| **SCRATCH** | object exists, codex2-built, not independently verified |
| **PROPOSED** | named, not yet built |
| **INSPIRATION** | outside model, used to suggest structure, not authority |
| **FUTURE-TEST** | a distant target the carrier will be tested against, not a current admission |
| **KILLED** | tried, failed the verification it claimed — graveyard, kept as a diagnostic |

---

## The order is measured, not declared

The rung *dependencies* below (you cannot define the admissible carrier before the admissible set is explicit) are structural. But the *operational order* — which operations must be sequenced and which are free — is an **empirical measurement**, the same N01 order-gap used at R2, applied to the operations themselves.

Witness (pure-python, builder-independent), pairwise `‖A∘B − B∘A‖` over candidate operations on the R2 carrier:

```
            U_z     U_x     U_y  deph_Z  deph_X    damp
   U_z    0.000   2.449   2.449   0.000   1.414   0.000
   U_x    2.449   0.000   2.449   1.414   0.000   0.466
   U_y    2.449   2.449   0.000   1.414   1.414   0.466
deph_Z    0.000   1.414   1.414   0.000   0.000   0.000
deph_X    1.414   0.000   1.414   0.000   0.000   0.300
  damp    0.000   0.466   0.466   0.000   0.300   0.000
```

Order-FREE (commute): `U_z·deph_Z`, `U_z·damp`, `U_x·deph_X`, `deph_Z·deph_X`, `deph_Z·damp`.
Order-FORCED (sequence matters): all `U_i·U_j` (i≠j), `U_z·deph_X`, `U_x·deph_Z`, `U_*·damp`, `deph_X·damp`.
**The build order falls out of this, it is not chosen.**

---

## R0 — Primitive: constraint on distinguishability

- **Owner anchors:** `OWNER_THESIS_AND_COSMOLOGY.md:13-32` ("only one primitive substance: constraint on distinguishability… entropy is a *later* admissible measure"), `:485-492` (`a=a iff a~b`); `NOMINALISM_IN_THIS_SYSTEM.md:199-223`.
- **Plain (his language):** the only primitive is what limits what can be told apart, under what probes. A thing is itself only by being distinguishable from something else under an admissible probe. Entropy is downstream, not the base.
- **Formal object:** finite possibility set `S` + indistinguishability relation `~_M` induced by a probe family `M`.
- **Admissible operations:** probing (apply a probe, read same/different).
- **Probe family / equivalence:** `M` = admissible probes; `a ~_M b` iff no probe in `M` separates them; identity = class in `S/~_M`.
- **Finite witness:** **BUILT** — `foundation_rung0to3_distinguishability_results.json` (the quotient + density-as-class). Independently verified.
- **Live alternatives:** entropy-as-primitive (the reading we *corrected away from*); whether `~` is primitive and `=` derived (his) or vice-versa.
- **What would kill it:** a probe-*independent* identity (a thing identical to itself with no probe family). The empty-`M` witness (no probes → one class → no identity) currently *supports* R0, doesn't kill it.
- **Next artifact:** none — anchored and witnessed.

## R1 — F01 + N01 as chosen root constraints

- **Owner anchors:** `CONSTRAINT_SURFACE_AND_PROCESS.md:16-26` (F01 finitude; N01 noncommutation; `M(C)={x: F01 ∧ N01}`; "constraints define a *surface*… they coexist").
- **Plain:** two **chosen** root constraints (not derived): everything finite (F01); composition order matters (N01). Simultaneous surface, not a sequence.
- **Formal object:** F01 = finite `S`, finite `M`, finite operators; N01 = noncommuting composition (`AB ≠ BA`).
- **Admissible operations:** finite probing; order-sensitive composition.
- **Probe family / equivalence:** finite `M` → finite-resolution quotient.
- **Finite witness:** **BUILT** — F01 (enlarge `M={Z}→{Z,X,Y}` ⇒ quotient refines, `resolution_change=4`) and N01 (`order_gap=1.0`, commuting control `0`), both in the rung-0-3 object; N01 independently re-computed.
- **Live alternatives:** is `{F01, N01}` the *minimal* root set, or is **non-associativity** a third root? (non-assoc is independently real at R3; its *foundational* status is open.)
- **What would kill it:** the admissible set being *insensitive* to erasing F01 or N01. The witness shows both are load-bearing.
- **Next artifact:** a test of whether non-associativity sits at R1 (root) or R3 (carrier). Currently placed at R3.

## R2 — M(C): finite admissibility space + admissible operations

- **Owner anchors:** `CONSTRAINT_SURFACE_AND_PROCESS.md:22` (M(C) def); `NOMINALISM_IN_THIS_SYSTEM.md:200-218` ("the density matrix IS the equivalence class").
- **Plain:** the set of finite objects that survive F01+N01; the quotient `S/~_M` is the identities; the density matrix realizes the class; the admissible **operations** and their **order are measured, not declared**.
- **Formal object:** `(S, M, ~_M, S/~_M, admissible-operation set + its measured commutation partial order)`.
- **Admissible operations:** measurement channels, CPTP maps, unitaries — ordered by the **measured commutation matrix** above.
- **Probe family / equivalence:** finite `M`; `~_M`; density matrix = class.
- **Finite witness:** **BUILT** for the distinguishability structure + density=class (independently verified) and the **operation-order witness** (the 6-operation commutation matrix). Order-free vs order-forced is empirical.
- **Live alternatives:** which operation set is the right admissible set (measurement channels only? + unitaries? + dissipators?). The order among whatever set is chosen is whatever the commutators say.
- **What would kill it:** an arbitrary / unstable operation order (no definite commutation structure). The matrix shows a definite structure.
- **Next artifact → the smallest next step (below).**

## R3 — Carrier / readout candidates (only after R2 is explicit)

- **Owner anchors:** `CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md` (S³/Hopf/Weyl as a *candidate* path, not forced).
- **Plain:** once M(C) + its operations are explicit, candidate **carriers** (what hosts the structure) are tested *against* R2 — not assumed.
- **Formal object:** candidate carriers (ℂ²/spinor, division-algebra ladder ℝ→ℂ→ℍ→𝕆), readouts.
- **Finite witness:** **BUILT/verified** — non-associativity = real, carrier-specific (octonion associator `2.0`, quaternion `0.0`, dies under carrier mutation); spinor double-cover real (vector/SO(3) loses the −1 holonomy) but ℂ²≅ℍ¹ realization = convention.
- **Live alternatives:** minimal carrier (spinor vs vector vs quaternion); whether the Hopf/S³ geometry is **forced or candidate** — currently **candidate**.
- **What would kill a carrier claim:** a readout that survives carrier mutation (then it's target-imprint, not carrier-real). This discriminator is used **diagnostically only**, not to prosecute claims.
- **Next artifact:** none yet — R3 waits on R2's operation layer.

## R4+ — Physics-facing targets (distant tests, not admissions)

- **Owner anchors / inspiration:** Furey/Dixon division-algebra SM (**INSPIRATION**), his SM-from-octonions intuition.
- **Plain:** SM gauge group, charges, 3 generations, α, gravity, chirality — the **horizon the carrier is tested against**, not current build targets, **not admitted**.
- **Status of each:**
  - chirality (σ_y / Weyl L-R) — **KILLED** at the σ_y level (by-construction: hardcoded operator + import from twice-rejected golden_weyl). Diagnostic only.
  - SM gauge / SU(3) color / 3-gen / charges — **SCRATCH / reproduced-not-derived** (top-floor, parked).
  - α (fine structure) — **KILLED/GRAVEYARD** (`0.0115 ≠ 1/137`, `derived_not_fit=false`).
  - Weinberg angle — **KILLED/GRAVEYARD** (fit 3/8, not derived).
  - gravity / knot mass — **SCRATCH** (G not derived).
- **Fence:** do not promote any R4+ object. Do not run more top-floor discriminators.

---

## Status separation (one place)

| object | rung | status |
|---|---|---|
| finite distinguishability structure (density = quotient `S/~_M`) | R0–R2 | **BUILT** (Opus-verified) |
| F01 + N01 load-bearing controls | R1 | **BUILT** (Opus-verified) |
| measured operation commutation-order | R2 | **BUILT** (Opus-verified) |
| non-associativity = carrier-specific | R3 | **BUILT** (Opus-verified) |
| spinor double-cover real / ℂ²≅ℍ¹ convention | R3 | **BUILT** (Opus-verified) |
| `mc_first_admissibility_packet` | R2 | **SCRATCH** (codex2, unverified) |
| full admissible-operations layer on M(C) | R2 | **PROPOSED** (the next step) |
| S³ / Hopf / nested-tori geometry | R3 | **PROPOSED / candidate** |
| Furey/Dixon division-algebra SM | R4+ | **INSPIRATION** |
| SM gauge / charges / 3-gen | R4+ | **FUTURE-TEST** (scratch parked) |
| gravity / knot mass | R4+ | **FUTURE-TEST** (scratch) |
| chirality σ_y REAL_CARRIER | R4+ | **KILLED** |
| α = 1/137, Weinberg angle | R4+ | **KILLED / graveyard** |

---

## Smallest next construction step (R0/R1/R2 only)

**Build the admissible-operations layer on the already-verified M(C).** Not a carrier, not geometry, not physics.

- **On:** the verified rung-0-3 finite distinguishability structure.
- **Add:** the finite admissible-operation set (measurement channels + unitaries + dissipators) and compute its **full commutation partial order by measurement** (extend the 6-op matrix above), so the operation order is *discovered*.
- **Finite witness to produce:** the measured commutation graph + the admissible-vs-excluded operation classification (which operations preserve the quotient structure, which collapse it).
- **What would kill it:** if the commutation structure is unstable under the choice of test states, or if "admissible operation" cannot be defined without smuggling in a carrier/geometry.
- **Stop condition:** stays at R2 — does **not** advance to a carrier (R3) until this operation layer is explicit and verified.
