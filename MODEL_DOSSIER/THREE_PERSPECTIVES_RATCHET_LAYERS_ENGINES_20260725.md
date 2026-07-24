# One object, three perspectives — ratchet, layers, engines

**Date:** 2026-07-25
**Status:** PROPOSED model + measured negatives. Nothing admitted. `promotion_allowed: false` throughout.
**Method:** read from repo code and receipts (not re-derived), plus one new bridge sim run this session.
**Rule kept throughout:** the ratchet compares nested things and emits SMT-shaped verdicts. It never proves MSS. It can only rank the candidates actually put in front of it.

The three asks are one object at three depths, like the flat / spherical / spun presentations of the ring checkerboard:

| # | Perspective | Argument form | The question it answers |
|---|---|---|---|
| 1 | **Ratchet** | cosmological | where does anything begin, and what makes it move |
| 2 | **Layers** | ontological | what is the step-by-step process of being |
| 3 | **Engines** | anti-teleological | what does it converge on, without aiming |

---

# PART 1 — THE RATCHET (cosmological)

## 1.1 The tick, exactly

From `ROOT/ROOT_RATCHET_KERNEL_pack178.md`. Freeze at tick `r`:

```
K_r = ( D_r , G_r , Π_r , {⪯_i} , C_r , H_r )
```

- `D_r` finite typed distinction records available now
- `G_r` the replaceable exploration grammar
- `Π_r` executable probes
- `⪯_i` plural presumption orders (plural, never one)
- `C_r` frozen controls and claim ceilings
- `H_r` immutable prior receipts and failures

The tick:

```
P_r = G_r(D_r, H_r)                    propose
M_r(p) = Π_r(p ; D_r)                  measure
A_r = { p ∈ P_r : C_r(p, M_r(p)) }     admissible
F_{r,i} = Min_{⪯_i}(A_r) ,  F_r = {F_{r,i}}_i     frontier, one per order
```

Then the residual, kept as a **vector**, never a score:

```
Δ_r = Counterexamples(F_r) ∪ Unresolved(F_r) ∪ ContinuationMismatch(F_r)
    = (c_r, k_r, u_r, g_r, …)
O_{r+1} = Compile(Δ_r, C_r, H_r)
```

**If `Δ_r` supplies no new finite obligation, the process HOLDS.** It does not manufacture a next step to keep a story moving. That is the whole anti-narrative clause.

## 1.2 What the beginning is

There is no first substance. The cosmological content is: **a beginning exists exactly when `D ≠ ∅`** — when some pair must stay distinguished. Everything downstream is the consequence of keeping demanded distinctions while presuming as little as possible.

The drive is not entropy-as-a-number. From `HOW_THE_ENGINES_RUN_THE_RATCHET.md` §A.7, the code's load-bearing drive is:

```
coface_collapsed_demand_edge_mass          ← THE drive
```

and these are **explicitly killed as drives by the code itself**:

```
quotient_cell_count            KILLED_AS_DRIVE
raw_outcome_shannon_entropy    KILLED_AS_DRIVE
label_code_score               KILLED_AS_DRIVE
```

So the gradient that moves the ratchet is: *how much demanded distinction is currently being collapsed, and does a repair recover it.* Entropy-as-scalar is rejected as a driver in the source.

## 1.3 MSS, exactly (and only relatively)

From `ratchet_contract/mss.py`, binding owner correction in the docstring: **MSS = PARTITION COARSENESS, full stop.**

```
candidate C  ──►  π_C : partition of the observation surface X
                  (π_C(x) = π_C(y)  iff  reidentify(x,y) ∧ reidentify(y,x))

L_D(π)  = the demanded pairs (x,y) ∈ D that π merges     ← the entropy-geometry coface
Surv(D) = { π : L_D(π) = 0 }                             ← survivors
M(D)    = min_⪯ Surv(D) ,  where  π ⪯ ρ  iff  π is a coarsening of ρ
```

The comparison is three-stage and every stage is code:

| Stage | Test | Fail → |
|---|---|---|
| 1 | IDENTITY_GATE: does `reidentify()` exactly reproduce the probe-induced partition? | INELIGIBLE (HOLD) — not scored down |
| 2 | demand-thickening: persistence / evolvability / extension push `D` through a continuation and recheck | INELIGIBLE (HOLD) |
| 3 | coarseness: `partition_coarser(π_A, π_B)` | verdict |

Verdicts, the complete set:

```
A_WEAKER   B_WEAKER   INCOMPARABLE   HOLD
```

**Never "MSS proved."** The docstring says it outright: *"RELATIVE only; no absolute MSS."* This matches your statement exactly — it can find the best among what it compares, and nothing more.

`frontier()` returns three things and never a winner:

- **PURGATORY** — each entry with its exact failure and a **re-entry condition**
- **BRANCHES** — survivors grouped by identical partition digest (this is re-merge)
- **ANTICHAIN** — non-dominated branches; a branch is dominated only if another survivor is a *strict* coarsening

## 1.4 Why it can only compare nested things

The kernel's nested-constraint clause:

```
𝒯_r = { (x_0,…,x_L) :  ⋀_i C_i(x_≤i)  ∧  ⋀_i R_i(x_i, x_{i+1})  ∧  H_r(x_≤L) }
X*_{i,r} = π_i(𝒯_r)
```

The survivor at layer `i` is a **projection of the whole compatible tower**. So enclosing layers constrain their contents *and* inner extendability constrains which enclosing layers survive. A flat single-layer comparison is not a defined operation in this kernel — there is nothing to project.

## 1.5 The pawl (what cannot move backward)

Direction is carried by receipts and exclusions, not by forcing survivor sets to shrink:

- no admitted claim without an executable witness and its controls
- no silent weakening of a gate, grammar, bound, or ceiling
- no erasure of failed candidates or countermodels
- no source-size weighting disguised as recurrence
- no selector access to source names or owner-hypothesis labels
- re-evaluation after material context change
- a deletion/countermodel witness for every claimed load-bearing constraint

Winners may fall; Purgatory may return. What cannot move is the record.

## 1.6 DEFECT FOUND — two comparison operators in one repo

| Where | Operator |
|---|---|
| v7 `RATCHET_SPEC.md` §6 + `mss.py` | partition refinement over `L_D=0` survivors |
| v8 `manifold/engine/whole_feedback_ratchet.py:412` | Pareto dominance over a failure/presumption **vector**, with `"incomparable failure sets"` fallback |

Neither file cross-references the other. These are different comparison laws producing different frontiers. **Open — yours to rule.** Note the v8 form is exactly the Pareto machinery the AR01 audit warned MSS must not become.

---

# PART 2 — THE MANIFOLD LAYERS (ontological)

## 2.1 The measured state, first

From `system_v7/constraint_core/ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md`:

```
scientific manifold layers admitted: 0
```

Every rung L0–L15 carries a status token ending in `__NOT_ADMITTED`, `__NOT_FORCED`, or `__NOT_EARNED`. This is the honest floor for the ontological question: **the process exists as candidates and local passes; nothing has been admitted as a layer of being.**

## 2.2 The search space is 21 rival ladders

Not one proposed ordering — twenty-one, on disk, mutually incompatible. Grouped:

**Executed / measured**
1. **L0–L15 audit ladder** — root → probe quotient → density-rank strata → spinor/Hopf → Weyl factors → Schmidt → metric → Berry → Chern-vs-cut-lattice → … Every rung `PASSES_LOCAL … NOT_ADMITTED`.
2. **v8 MANIFOLD_MAP, layers 0–10** — the only ladder with EARNED arrows: magma → algebra ladder → presumption order → anticommutation → quantum entropy axis → **Rényi α-axis** → Bures/FS/Berry → finite→continuum → real→complex → speculative fence. 10 earned rungs, 3 proposed, 4 speculative, 4 numerology.
3. **v8 base ladder R0–R3** — admissibility relation → nested compatibility → ordered relations → persistent distinctions. Frontier `F_1 = {b0_unrestricted_relation, probe_response_incidence}`; 7 in Purgatory; **noncommutation NOT earned at this level**.

**Rivals, un-executed**
4. classical bottom-up (0–2), 5. top-down 12→0, 6. spinor/QIT (0–8), 7. nonassociative octonion (L0–L7), 8. middle-out bidirectional, 9. flattened ablation control, 10. no-layers countermodel (flat lookup table reproduces every `admitted()` call).

**Numbering conflicts (unresolved, on disk)**
- Same names, different indices between `MODEL_LAYER_LEDGER` and `STATE_OF_THE_MODEL`.
- **L8 collision**: the executed script calls L8 the Chern bundle; the source contract calls L8 the cut lattice. Verbatim: *"retained as a conflict, not reconciled by taste."*
- Three incompatible inventories: weakest-structure ladder, 0–26 GCM stack, L1–L15 contract. The 0–26 object is not materialised, so no crosswalk can be executed.

## 2.3 Where your fuz z/Hartley claim already lands

v8 MANIFOLD_MAP **Layer 6, EARNED**:

```
S_α = (1−α)^{-1} ln Tr(ρ^α)
S_0 = ln rank(ρ)   …   S_1 = S_vN
S_0 ≥ S_1 ≥ S_∞
verdict: S0_ONEWAY_FORGET_OF_VN
```

That is your Hartley/Rényi-0 floor, already earned as a one-way arrow in the repo, on **rank** (basis-free) rather than set cardinality. Layer 8 `finite → continuum` carries an *exact Hartley-growth formula*. So the fuzz-as-floor reading is not new fuel — it is the one rung family the repo has actually earned.

## 2.4 Order kills already on record

These are the negatives you asked for at the layer level:

| Proposed order | Outcome |
|---|---|
| nested-tori shells as the rung after L4 | **KILLED** — Schmidt strata bind first, measured |
| L3-built-on-L2 linear numbering | **WITHDRAWN** — L2 and L3 are parallel branches off L1; rung numbering is a DAG, not a line |
| "the dig-down IS the ratchet" | **WITHDRAWN** — MSS picks the floor downward, the ratchet climbs upward; two different arrows |
| "T01 forced at O" (octonions force nonassociativity) | **WITHDRAWN** to installed-upward; measured assoc defect R=C=H=0, O=22.20, S=72.91 |
| shells as their own object | **KILLED** — radius, Schmidt spectrum, entropy, purity, negativity are one behavioural class (inversion error 3.7e-14) |
| BKM as the unique L6 metric | **KILLED** — BKM, Bures, Wigner–Yanase, RLD agree on every commuting radial tangent to 1.78e-15 |
| the presumption RANKING itself (both directions) | **VOID** — an LLM computing relative MSS is an LLM pretending to be the ratchet |

## 2.5 Admission criteria (what would let a layer in)

```
PROVISIONAL_TOOTH_WITHIN_SCHEDULE_PACKET
    the prior frontier collapses a live demanded edge;
    a packet-minimal repair carries every active edge;
    at least one declared gradient couples to that repair;
    claim-relevant controls pass.
NO_LIFT_NEEDED__DIG_CONTINUES     prior frontier already carries the added demand
UNRESOLVED_GATE__DIG_CONTINUES    nothing adequate has survived yet
```

Plus the rung-placement law: *the next rung is the admissibility test that **binds**, discovered empirically on the survivors of rung k — never read off the doc order.*

---

# PART 3 — THE ENGINES (anti-teleological)

## 3.1 The 16 stages, 4 loops, 2 engines — explicit

Carrier: `ρ = ½(I + r·σ)` on `S³`, nested Hopf tori `T_η`, `r = (sin2η cos2χ, sin2η sin2χ, cos2η)`.
Sheets: Type-1 left `H_L = +H₀`, `s=+1`; Type-2 right `H_R = −H₀`, `s=−1`; `H₀ = n·σ`.
Loops: inner = Hopf fiber `γ_f` (density-**stationary**), outer = lifted base `γ_b` (density-**traversing**), horizontal condition `A(γ̇_b)=0`, `A = dφ + cos2η dχ`.

**Four terrain generators** (`terrain math.md`, verbatim shape):

```
Se  X = λ Σ_{j=x,y,z} D[σ_j](ρ)  − i s ε_F [H₀,ρ]        depolarising expansion
Ne  X = − i s [H₀,ρ]                                       PURE Hamiltonian, no jumps
Ni  X = γ D[σ∓](ρ)              − i s ε_P [H₀,ρ]           sink (T1 σ₋) / source (T2 σ₊)
Si  X = − i s [ω m̂·σ, ρ] + κ(P₊ρP₊ + P₋ρP₋ − ρ)           invariant strata
D[L](ρ) = LρL† − ½{L†L, ρ}
```

**Four operators** (`operator math explicit.md`, the only four; on `ρ = [[a, u−iv],[u+iv, d]]`):

| Op | Channel | Explicit effect | Generator |
|---|---|---|---|
| Ti | `(1−q₁)ρ + q₁(P₀ρP₀+P₁ρP₁)` | off-diagonal → `(1−q₁)(u−iv)` | `(κ₁/2)(σ_zρσ_z−ρ)` |
| Te | `(1−q₂)ρ + q₂(Q₊ρQ₊+Q₋ρQ₋)` | `a → (1−q₂)a + q₂/2`, `v → (1−q₂)v` | `(κ₂/2)(σ_xρσ_x−ρ)` |
| Fi | `U_x(θ)ρU_x(θ)†` | `v → v cosθ − ((a−d)/2) sinθ`, `u` fixed | `−i[(ω₃/2)σ_x, ρ]` |
| Fe | `U_z(φ)ρU_z(φ)†` | `(u−iv) → e^{−iφ}(u−iv)`, `a,d` fixed | `−i[(ω₄/2)σ_z, ρ]` |

**Axis 6** is composition order only, not a fifth operator: `UP = Φ_T ∘ 𝒪` (operator first), `DOWN = 𝒪 ∘ Φ_T` (terrain first). Liouville form `L_A ~ I⊗A`, `R_A ~ Aᵀ⊗I`.

**A placement is a pair**: `𝒫_{s,ℓ,τ} = (γ_ℓ^s, X_τ^s, Φ_τ^s)` — side × loop-curve × terrain law. 4 loop curves, 8 terrain laws, **16 placements**.

The 16 cells with their chart verdicts:

| | Type-1 outer | Type-1 inner | Type-2 outer | Type-2 inner |
|---|---|---|---|---|
| Se | `TiSe` Ti↑ LOSE | `SeFi` Fi↓ win | `FiSe` Fi↑ WIN | `SeTi` Ti↓ lose |
| Ne | `NeTi` Ti↓ WIN | `FiNe` Fi↑ lose | `NeFi` Fi↓ LOSE | `TiNe` Ti↑ win |
| Ni | `NiFe` Fe↓ LOSE | `TeNi` Te↑ lose | `NiTe` Te↓ LOSE | `FeNi` Fe↑ lose |
| Si | `FeSi` Fe↑ WIN | `SiTe` Te↓ win | `TeSi` Te↑ WIN | `SiFe` Fe↓ win |

Composition: `Φ_loop = Ψ₄∘Ψ₃∘Ψ₂∘Ψ₁`, `Φ_engine = Φ_inner ∘ Φ_outer` with **unreset** handoff.

## 3.2 THE MAIN FINDING — the basin is a single point

Measured, three independent artifacts plus one new run this session:

| Source | Object | Attractors | Basin |
|---|---|---|---|
| `coratchet_basin_depth_multiview_v0` | fixed point of the **full 16-stage** Liouvillian, both types, Julia+JAX agree 5e-16 | **1** (multiplicity 1, residual ~1e-16) | whole ball |
| `attractors_basin_native_schedule_v0` | Attractors.jl on the 16-stage Bloch map, **5 schedules** | **1** each | fraction **1.0** each |
| `engine_pair_basin_map_sim` | 64-microstep cycle + the 4 loops separately | **1** each | volume fraction 1.0 |
| **new: `engine_to_ratchet_bridge_v0`** | 6 rival engine configs (all orders, both types, both families) | **1** each | all 16 states |

Contraction coefficients: Type-1 **0.3989**, Type-2 **0.3406** — strict contractions. By Banach, a strict contraction has exactly one fixed point and its basin is everything.

**The anti-teleological answer, stated plainly:** the engines do not aim at anything, and — as currently installed — they also do not *select* anything. A single global attractor with whole-space basin means every initial state ends in the same place. There is no basin structure, therefore no selection at the dynamical level.

## 3.3 Structure appears only in the controls

This session's run, same harness, negative controls:

| Candidate | Attractors | Basin sizes |
|---|---|---|
| all 6 real engine configs | 1 | [16] |
| `NEG_commuting_z_only` | **4** | [4,4,4,4] |
| `NEG_unitary_only` (no dissipation) | **16** | [1×16] |
| `NEG_single_terrain_Se` | 1 | [16] |
| `NEG_no_operator` | 1 | [16] |

This reproduces the repo's own controls exactly (`T10` unitary erasure → multiplicity 2, strict attraction destroyed; `T11` commuting z-dephase → multiplicity 2, non-unique fixed manifold retained).

**Reading:** richness lives where contraction fails. Full dissipation collapses everything to one point; no dissipation preserves everything; the interesting middle is not currently occupied by any native schedule.

## 3.4 Where selection actually lives — the new bridge result

The repo names the missing engineering: *"the bridge engine behaviour → partition → ratchet input."* Built this session (`system_v8/ratchet_bridge/`). Engine → behaviour under a probe family → induced partition `π` → the real `mss.frontier()`.

Sweeping the probe resolution (the knob that sets what is distinguishable at all):

| probe res | distinct partitions | what happens |
|---|---|---|
| 0 (coarse) | 3 | all 6 real engines collapse X to **1 cell** — every demanded distinction destroyed → all in Purgatory |
| **1 (middle)** | **9** | **the rival orders separate**: doc S→N **7 cells**, owner N→S **6**, AR01 **9**, reversed **6**, Type-2 **8**, inductive **8**. All survive D |
| 2 (fine) | 2 | everything discrete (16 cells), identical digests — no discrimination |

**So the ratchet CAN see the difference between rival loop orders — but only in a narrow band of probe coarseness.** Too coarse and every engine destroys the demand set; too fine and no engine merges anything. This is the same failure mode the repo already recorded (`restricting_outer_changes_inner: false` on all nine base carriers — the demand set could not separate any carrier).

**And a new negative:** at the discriminating resolution, all six real engine configs land in **Purgatory at Stage 1 — identity-honesty**. Cause is exact and instructive: I declared the probe family as raw observables but defined `reidentify` through post-loop behaviour. Those are two different probe families `M`, and the gate correctly refuses a candidate whose identity claim is not the one its probes expose. **The fork this exposes is real and is a layer question:** is engine identity read *before* the loop or *after* it? The answer changes every partition, hence every ratchet verdict.

## 3.5 What is already killed at engine level

| Claim | Status |
|---|---|
| schedule-specificity of basin structure | **EXCLUDED** — all 5 schedules give 1 attractor, fraction 1.0; pre-registered as expected to die |
| the native order is selected by basin quality | **FALSE** — `native_order_selected: false` both engines; T1 native ranks 17–32 of 33, T2 ranks 3–18 |
| basin genericity vs random CPTP cycles | **FAILED both runtimes**, both engines |
| Type-1/Type-2 mirror relation | **FAILS** — Hausdorff 0.1234 > tolerance 0.09 |
| distinctive / co-ratchet / Axis-0 / perception claims from the basin | **found_fabrication: true** at the semantic layer (repo's own audit) |
| shuffled-schedule control | changes basin structure (0.640 / 0.126) — order *does* matter to geometry |
| commuting-generator control | collapses both centres to origin — non-commutation is load-bearing |

---

# PART 4 — THE PROPOSED MODEL (one object, three depths)

```
   D ≠ ∅                          ← cosmological beginning: something must stay distinct
     │
     │  MSS picks the floor  (downward: weakest structure that still separates D)
     ▼
   TOWER  𝒯 = {(x_0 … x_L)}        ← ontological process: layers are projections π_i(𝒯)
     │
     │  RATCHET climbs  (upward: which constraint BINDS next on the survivors)
     ▼
   ENGINE = a compatible tower made executable
     │
     │  iterate Φ_engine
     ▼
   BASIN                           ← anti-teleological end: whatever the contraction leaves
```

The three are the same object read at different depth:

- **the ratchet** is the tower's *comparison* law
- **the layers** are the tower's *slices*
- **the engine** is the tower *running*
- **the basin** is the engine's *limit*

And the honest current state of that model:

| Depth | State |
|---|---|
| beginning (D) | defined; drive = collapsed-demand-edge mass; scalar entropy killed as driver |
| tower (layers) | 21 rival ladders, **0 admitted**; 1 earned arrow family (Rényi/Hartley) |
| engine | 16 stages explicit and running; two engines cross-verified to 5e-16 |
| basin | **single point, whole-space basin — no structure, no selection** |

**The gap this exposes** is the most useful thing in this document: your model wants the engines to converge on a *basin structure*, and the measured engines converge on a *point*. Selection is not happening in the dynamics. It is happening — if anywhere — one level up, in which candidate towers survive `L_D = 0` and sit on the coarseness antichain.

Three ways the basin could acquire structure (see §6.2 — route 1 as originally written is now **measured false**):
1. ~~**Couple two engines** — a product of two contractions can have structure the factors lack.~~ **RETRACTED, see §6.2.**
2. **Leave the contraction regime** — the controls prove structure appears when contraction fails; a schedule with a unitary-dominant stroke may sit between 1 and 16 attractors. (Necessary but not sufficient — pure preservation selects nothing.)
3. **Nest** — `engine_pair_basin_map_sim` already shows loop-basin ⊂ engine-basin (`nesting_holds`); useful only if nesting adds persistent state or renesting, not if it wraps the same point attractor.

---

# PART 5 — OPEN, YOURS TO RULE

1. **Two comparison operators** (partition refinement vs Pareto-over-presumption-vector) — §1.6.
2. **Identity before or after the loop** — §3.4. Changes every partition.
3. **Loop order** — OD-11. Rivals measured side by side here; the doc order, your S→N/N→S hypothetical, and the AR01 order give 7 / 6 / 9 cells. Different, not ranked.
4. **L8 identity** — Chern bundle or cut lattice.
5. **Which of 21 ladders** enters the tournament as the tower.
6. **Probe-family thickness** — the ratchet only discriminates in a narrow band; D and M must be chosen, and that choice is a modelling act, not a measurement.

---

# PART 6 — CORRECTIONS (external review, then measured)

External review (GPT) raised four objections to Parts 1–5. Two were **tested this session and confirmed against the running engine**; two are adopted as method corrections. Nothing here is smoothed — the superseded statements stay visible above with pointers.

## 6.1 The arrow was drawn linear; the kernel is cyclic — ADOPTED

Part 4 drew `D≠∅ → tower → engine → point basin`, which ends. That is wrong-shaped and the source says so: the kernel's own residual compiler closes the loop, `O_{r+1} = Compile(Δ_r, C_r, H_r)`. Corrected shape:

```
𝓕_r ──► {𝒯_α} ──► Hist(𝓔_α) ──► π_α ──► MSS_{D_r⁺} ──► 𝓕_{r+1}
 fuzz     rival        engine       induced      coarsest        renested
 field    nests        histories    partition    survivors       field
```

Also adopted: `D ≠ ∅` **activates** the executable ratchet; it is not the ontological floor. The floor candidate is the finite distinction field `p: E₀ → K`, `|Ω_c| = 2^{n_c}`, `H₀(Ω_c) = n_c` — the fuzz. This matches your own position from the previous turn, and the repo's one earned arrow family (Rényi Layer 6).

## 6.2 "Products of contractions can create structure" — MEASURED FALSE

My route 1 in Part 4. Computed directly (`rotation_and_product_test_v0`):

| quantity | value |
|---|---|
| engine-1 contraction coefficient | 0.149446413909 |
| engine-2 contraction coefficient | 0.149446413909 |
| direct-product unit eigenvalues | **1** |
| direct-product subdominant modulus | 0.13226717053 |
| `product_is_contraction` | **true** |

A direct product of two contractions is a contraction with a unique fixed point. **Coupling two engines by direct product cannot create basin structure.** Structure requires state-dependent, record-mediated, or obstruction-mediated coupling. Route 1 as written is retracted.

## 6.3 Cyclic rotation — CONFIRMED, and it dissolves part of OD-11

Claim tested: "cyclic rotations are the same loop." If so, rotated orders have **conjugate** return maps and therefore identical Liouvillian spectra. Measured:

| pair | predicted same cycle | max spectral gap | verdict |
|---|---|---|---|
| `doc Se→Ne→Ni→Si` vs `owner-hyp Ne→Ni→Si→Se` | yes | **0.0** | **SAME CYCLE, different phase** |
| `reversed-doc Si→Ni→Ne→Se` vs `doc-inductive Se→Si→Ni→Ne` | yes | **0.0** | same cycle — deduction reversed *is* induction, confirmed numerically |
| `doc` vs `AR01 Ne→Si→Se→Ni` | no | 0.007724 | genuinely different cycle |
| `doc` vs `reversed-doc` | no | 0.069291 | different cycle |
| `AR01` vs `reversed-doc` | no | 0.061567 | different cycle |

**Consequence for OD-11.** The apparent conflict between the doc's deductive order and your S→N / N→S hypothetical is **not a conflict about the cycle** — they are the same 4-cycle read from different starting phases, spectra identical to machine zero. What remains open is narrower and cleaner:

1. **which phase is stage 1** — a labelling/interpretation choice (it does change the one-step map, which is conjugate, not equal), and
2. the **AR01 / recovery-pack order**, which is a genuinely different cycle and remains an error.

## 6.4 One-step partitions conflate phase with cycle — METHOD CORRECTION

Part 3.4 reported rival orders producing 7 / 6 / 9 cells at probe resolution 1, and treated that as the orders differing. §6.3 shows the doc and owner orders are the same cycle, so that difference measures **starting phase**, not cycle identity. Rotations give conjugate one-step maps: same spectrum, different single-step partition.

Correction adopted: the candidate's signature for ratchet comparison must be the **transition relation over the full history**, not a one-step partition or a terminal attractor. Three typed objects instead of my pre-loop/post-loop fork:

```
π_in  ──T_α──►  π_out          with behaviour signature
b_α = ( ρ_0…ρ_16 , D_jk , R_0…R_16 , Δ_order , Δ_direction , Δ_Axis6 , Δ_deletion )
```

This also supersedes §3.4's framing of the identity-honesty failure: it is not "pick pre-loop or post-loop," it is "the candidate is identified by its transition, and both endpoints are typed."

## 6.5 What is NOT adopted

The review's proposed F0–F10 dependency DAG is a **new candidate ladder — number 22** — and goes into the tournament with the other 21. It is not adopted as the manifold. The review states the rule itself ("no LLM-generated table should be treated as canon") and that rule applies to its own table.

Its `16 = 4 topologies × 2 flux × 2 Axis-6` coordinate system is checkable and holds, but only as a **relabelling**: in the 16-cell chart the Axis-6 arrow is a function of (terrain, loop) — for Se, outer=UP / inner=DOWN; for Ne, outer=DOWN / inner=UP — so arrow substitutes for loop bijectively given terrain. It is one coordinate system written two ways, not two independent ones.

---

## Artifacts

- `system_v8/ratchet_bridge/engine_as_candidate.py` — engine presented as a ratchet `CandidatePackage`
- `system_v8/ratchet_bridge/run_bridge.py` — rival orders + 4 negative controls + probe sweep
- `system_v8/ratchet_bridge/rotation_and_product_test.py` — §6.2 and §6.3 tests
- `system_v8/ratchet_bridge/results/engine_to_ratchet_bridge_v0.json`
- `system_v8/ratchet_bridge/results/rotation_and_product_test_v0.json`
- `classification: tool_lego_fit_probe`, `promotion_allowed: false`
