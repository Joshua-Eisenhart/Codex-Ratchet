# The IGT engine layout, with explicit math

**Date:** 2026-07-25
**Built from four parallel extractions:** codex1-luna (JUNGIAN_FUNCTIONS map, `operator math explicit.md`, `terrain rosetta strong math.md`), codex1-terra (ENGINE_64_SCHEDULE_ATLAS, QIT geometry–entropy bridge master table, terrain Rosetta, I-Ching rosetta), wiki IGT cluster (9 concept pages incl. the tribunal record), and the sims-and-results sweep (Otto, Carnot/Szilard-QIT, chirality, both Rosetta probes, engine estate).
**Status rule for this whole document:** every item carries the status its source wrote. Nothing here is promoted. Conflicts are shown side by side and left open. The one measured headline that frames everything: **the IGT↔QIT correspondence itself is NOT yet an earned invariant** (§10) — IGT grammar and QIT dynamics are two lanes with a bridge that the estate's own probes honestly failed to close.

---

## 1. What IGT is

**IGT = Irrational Game Theory** (wiki, status "working reference, not canon"). Its object is the WIN/LOSE + win/lose two-engine pattern. It inverts the classical strategy square:

| Quadrant | Classical name | IGT stance |
|---|---|---|
| WinWin | maximax | kept |
| WinLose | maximin | kept |
| LoseWin | minimax-regret | kept |
| LoseLose | minimin | **"crowned king"** |

Three coordinates, verified mutually orthogonal by cell count: **outcome** (W/L), **mode** (competitive/dephasing vs cooperative/rotation), **magnitude** (BIG/small). Owner note on record: "win-lose can CHOOSE lose."

**The 4-ring** (the IGT atom): `{win,lose} × {WIN,LOSE} = {−1,+1}²`, a Hamming-1 square `Si—Ne / Se—Ni`. Enumeration result (scratch, promotion_allowed=false): of 16 configs satisfying alternation+balance, 4 survive closure, **exactly 2 have double-4-ring engine structure and they are mutual inverses — one chiral pair.** The two engines are those two survivors. Engine non-collapse separately simmed dual-backend, audited GENUINE.

---

## 2. The carrier geometry (bridge master table: `live geometry`)

```
ψ ∈ S³ = {ψ ∈ ℂ² : ‖ψ‖=1}          spinor carrier
π(ψ) = ψ†σ⃗ψ ∈ S²                   Hopf projection
ρ(ψ) = |ψ⟩⟨ψ| = ½(I + r⃗·σ⃗)         density form
T_η = {(e^{iα}cos η, e^{iβ}sin η)}   nested Hopf tori (Clifford torus at η=π/4)
A = −iψ†dψ = dφ + cos(2η)dχ          Hopf connection
```

**The two loop classes (Axis 3, current strongest reading — fenced, see §12):**

```
fiber loop:  γ_f(u) = ψ_s(φ₀+u, χ₀; η₀)              ρ_f(u) = ρ_f(0)   DENSITY-STATIONARY
base loop:   γ_b(u) = ψ_s(φ₀−cos(2η₀)u, χ₀+u; η₀)     ρ_b(u) varies     DENSITY-TRAVERSING
horizontality: A(γ̇_b) = 0
```

Inner loop = fiber, outer loop = lifted base. The density-visibility proof is on record: `ρ_in(u)` is independent of the inner parameter; `ρ_out(u)` varies.

**The two Weyl sheets:** `H_L = +H₀`, `H_R = −H₀` with `H₀ = n⃗·σ⃗`; Bloch form `ṙ_L = +2n⃗×r_L`, `ṙ_R = −2n⃗×r_R`. Tribunal caution on record: whether the L/R Weyl split is *selected* is disputed by the models; your correction on record rejects their framing and asserts it as a ratchet step.

---

## 3. The four terrain laws × two sheets = 8 terrains (status: "candidate, not closed" in every source)

`D[L](ρ) = LρL† − ½(L†Lρ + ρL†L)`, sign `s = +1` (Type-1/left/IN) or `s = −1` (Type-2/right/OUT):

| Terrain | Type-1 name | Type-2 name | Law | Character |
|---|---|---|---|---|
| Se | Funnel | Cannon | `ρ̇ = Σ_k D[L_k](ρ) − is·ε_F[H₀,ρ]` | dissipative-led radial **expansion** |
| Ne | Vortex | Spiral | `ρ̇ = −is[H₀,ρ] + ε_V Σ_k D[L_k](ρ)` | Hamiltonian-led **circulation** |
| Ni | Pit | Source | `ρ̇ = D[√γσ₋ or √γσ₊](ρ) − is·ε_P[H₀,ρ]` | dissipative **contraction** — sink (T1) / source (T2) |
| Si | Hill | Citadel | `ρ̇ = −is[H_C,ρ] + Σ_j κ_j(P_jρP_j − ½{P_j,ρ})`, `[H_C,P_j]=0` | invariant **strata** / retention |

What flips between the engines (source, verbatim): "Hamiltonian sign flips, rotation axis flips, z-attractor flips, jump operator flips (σ₋→σ₊), projector frame rotates. **Different channels, not relabelings.**"

Terrain ↔ IGT quadrant identity (Axis1×Axis2 product; consistent across all files): **Se = LoseWin, Ne = WinLose, Ni = LoseLose, Si = WinWin.**

---

## 4. The four operators — two rival tables, one marked live

**Table A — the runtime channels (bridge master table row 21: `live engine`; consistent across wiki + sims):**

| Op | Channel | Generator | Class | Native terrains |
|---|---|---|---|---|
| Ti | `(1−q₁)ρ + q₁(P₀ρP₀+P₁ρP₁)` | `L_Ti = (κ₁/2)(σ_zρσ_z − ρ)` | z-dephasing (CPTP) | Se, Ne (direct frame) |
| Te | `(1−q₂)ρ + q₂(Q₊ρQ₊+Q₋ρQ₋)` | `L_Te = (κ₂/2)(σ_xρσ_x − ρ)` | x-dephasing (CPTP) | Ni, Si (conjugated frame) |
| Fi | `U_x(θ)ρU_x(θ)†`, `U_x = e^{−iθσ_x/2}` | `−i[(ω₃/2)σ_x, ρ]` | x-rotation (unitary) | Se, Ne |
| Fe | `U_z(φ)ρU_z(φ)†`, `U_z = e^{−iφσ_z/2}` | `−i[(ω₄/2)σ_z, ρ]` | z-rotation (unitary) | Ni, Si |

Axis-5 split: {Ti, Te} = dephasing/pinch class; {Fi, Fe} = unitary rotation class. Kernel facts: Ti/Te destroy coherence in their basis (Ti leaves populations unchanged; Te changes them); Fi/Fe preserve purity.

**Table B — the kernel Rosetta (`apple axes` Part 2, candidate):** Ti = projector `Σ_k P_kρP_k` (carve), Te = gradient/Hamiltonian drive (push), Fe = Lindbladian coupling (diffuse), Fi = spectral filter (broadcast). **CONFLICT with Table A on Te/Fe/Fi roles — recorded, unresolved.** Table A is what the executable runtime uses; "live" ≠ ratified doctrine. Also on record: Axis-5 label drift ("FeFi vs TeTi" in some docs, "FeFi vs TiTe" in the taijitu) — preserved as drift.

---

## 5. Axis 6 and the 8 signed operators

```
UP   (↑): operator first    Ψ↑ = Φ_T ∘ 𝒪    elementally L_A(ρ) = Aρ  ~  I⊗A
DOWN (↓): terrain first     Ψ↓ = 𝒪 ∘ Φ_T    elementally R_A(ρ) = ρA  ~  Aᵀ⊗I
noncommutation witness: Δ_{T,O}(ρ) = Φ_T(O(ρ)) − O(Φ_T(ρ)) ≠ 0 in general
recorded relation: b₆ = −b₀·b₃
```

Token spelling = execution order, left to right: `TiSe` = Ti then Se-flow (↑); `SeFi` = Se-flow then Fi (↓).

| Signed op | Composition | Native placements |
|---|---|---|
| Ti↑ | `Φ_T(Ti(ρ))` | Se-in, Ne-out |
| Ti↓ | `Ti(Φ_T(ρ))` | Ne-in, Se-out |
| Te↑ | `Φ_T(Te(ρ))` | Ni-in, Si-out |
| Te↓ | `Te(Φ_T(ρ))` | Si-in, Ni-out |
| Fi↑ | `Φ_T(Fi(ρ))` | Ne-in, Se-out |
| Fi↓ | `Fi(Φ_T(ρ))` | Se-in, Ne-out |
| Fe↑ | `Φ_T(Fe(ρ))` | Si-in, Ni-out |
| Fe↓ | `Fe(Φ_T(ρ))` | Ni-in, Si-out |

---

## 6. The 16 placements — formal object and full stage charts

Formal placement (`terrain rosetta strong math.md`): **`𝒫_{s,ℓ,τ} = (γ_ℓ^s, X_τ^s, Φ_τ^s)`** with `s ∈ {L,R}`, `ℓ ∈ {f,b}`, `τ ∈ {Se,Ne,Ni,Si}`. Structural lock: 4 loop curves × — no, precisely: {4 loops} × {4 terrain families} with 8 terrain laws = **16 placements**. Each placement is one terrain law resolved along one loop curve on one sheet, carrying one signed operator.

**Type-1 (left sheet ρ_L, flux IN, H_L = +H₀):**

| Terrain | OUTER = lifted base, deductive FeTi | | INNER = fiber, inductive TeFi | |
|---|---|---|---|---|
| | cell / Ax6 / result | explicit map | cell / Ax6 / result | explicit map |
| Se-in | `TiSe` / Ti↑ / **LOSE** | `Φ_Se(Ti(ρ_L))` | `SeFi` / Fi↓ / win | `Fi(Φ_Se(ρ_L))` |
| Ne-in | `NeTi` / Ti↓ / **WIN** | `Ti(Φ_Ne(ρ_L))` | `FiNe` / Fi↑ / lose | `Φ_Ne(Fi(ρ_L))` |
| Ni-in | `NiFe` / Fe↓ / **LOSE** | `Fe(Φ_Ni(ρ_L))` | `TeNi` / Te↑ / lose | `Φ_Ni(Te(ρ_L))` |
| Si-in | `FeSi` / Fe↑ / **WIN** | `Φ_Si(Fe(ρ_L))` | `SiTe` / Te↓ / win | `Te(Φ_Si(ρ_L))` |

**Type-2 (right sheet ρ_R, flux OUT, H_R = −H₀):**

| Terrain | OUTER = inductive TeFi | | INNER = deductive FeTi | |
|---|---|---|---|---|
| Se-out | `FiSe` / Fi↑ / **WIN** | `Φ_Se(Fi(ρ_R))` | `SeTi` / Ti↓ / lose | `Ti(Φ_Se(ρ_R))` |
| Si-out | `TeSi` / Te↑ / **WIN** | `Φ_Si(Te(ρ_R))` | `SiFe` / Fe↓ / win | `Fe(Φ_Si(ρ_R))` |
| Ni-out | `NiTe` / Te↓ / **LOSE** | `Te(Φ_Ni(ρ_R))` | `FeNi` / Fe↑ / lose | `Φ_Ni(Fe(ρ_R))` |
| Ne-out | `NeFi` / Fi↓ / **LOSE** | `Fi(Φ_Ne(ρ_R))` | `TiNe` / Ti↑ / win | `Φ_Ne(Ti(ρ_R))` |

**NOTE on loop-geometry assignment (CONFLICT on record):** the JUNGIAN map §6.4 says Type-2 outer = inductive **on the fiber loop** and inner = deductive **on the lifted base** — i.e., in Type-2 the loop-geometry↔outer/inner assignment SWAPS relative to Type-1. The terrain r