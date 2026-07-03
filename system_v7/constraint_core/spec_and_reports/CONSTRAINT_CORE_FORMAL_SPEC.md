# The Constraint-Based Core — Formal Specification

**A math-first formalization of the constraint foundation, its forced first
construction, and its concrete finite realization.**

Version 1.0 · consolidated from the Codex-Ratchet and Wiki corpora
(`Constraints.md`, `terrain rosetta strong math.md`, `TERRAIN_LAW_LEDGER.md`,
`AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md`, `AXIS_3_4_5_6_QIT_MATH.md`)
plus a machine-checked audit of the concrete realization.

---

## 0. Purpose and reading order

This document states the constraint-based core as a layered formal system. It is
organized so that **each layer is forced by the one above it** — nothing is
asserted that is not either (a) a base postulate, (b) a definition, or (c) a
consequence that can be derived or numerically checked.

> **Framing (important).** The core is **not** a prohibition that declares most
> mathematics "illegal." It is a **monotone generative ratchet** on a
> *nominalist* foundation: all of mathematics can eventually be earned, but each
> structure must be *paid for* — admitted one minimal step at a time, and never
> un-admitted once earned. Legitimacy = *what a Turing machine can run* (finite,
> mechanical, concrete inscriptions), extended upward only when an **oracle**
> (the perceptual/inductive side, §3b) supplies a distinction the current
> machine cannot decide. "Constraints" are therefore the *cost function* of the
> ratchet, not a blacklist. The monotonic accumulation of earned distinctions is
> one and the same object as entropic monism's arrow and the ratchet's ordering
> index (U-2).

The layers are:

1. **Foundational postulates** (§1) — entropic monism, emergent identity, and
   the three base constraints C1–C3. These are the *only* primitive commitments.
2. **The allowable-mathematics charter** (§2) — what mathematics C1–C3 forbid
   and what they force. This is a consequence layer, not a design choice.
3. **The first forced construction** (§3) — the finite non-commutative
   refinement category, the weakest object that must exist if C1–C3 are
   consistent.
4. **The concrete finite realization** (§4–§7) — the `ℂ²` / `S³` Hopf carrier,
   the two Weyl sheets, the eight terrain generators, and the loop/stage
   structure. This is presented as **one admissible realization**, explicitly
   *selected*, not *assumed* (see the Declared Unknowns, §9).
5. **Audit** (§8) — a machine-checked verification that the concrete realization
   satisfies its own stated laws, and a precise statement of the one convention
   that had to be pinned down.
6. **Declared unknowns** (§9) — the open questions that must be held explicitly
   open so they do not leak back in as hidden assumptions.

A **strict separation** is maintained throughout: primary mathematics (§1–§8)
never depends on the correlation layers (Jungian functions, IGT tokens, I Ching
imagery). Those are downstream naming/checksum layers and are out of scope here.

### 0a. Source fidelity — canon vs. superseded

The corpus contains many LLM-generated documents; some over-hardened the
author's positions or contradict each other. This spec is **rebuilt against the
recent Wiki**, which the author maintains as the current statement, and
explicitly flags where an older transcript was misleading:

| Topic | **Canonical (recent Wiki)** | Superseded / lower-fidelity |
|-------|------------------------------|-----------------------------|
| Base constraints | `s1-qubit-ladder-f01-n01-t01-2026-06-10` — **F01 / N01 / T01**, qubit ladder | generic "C1/C2/C3", magma→group lattice (earlier draft of *this* doc) |
| Framing | **monotone generative ratchet** that *earns* all math step by step | "most math is illegal" (a filter framing, `Constraints.md` transcript) |
| Identity / oracle | `EM_BOOTPACK…AXIOMS_FOUNDATIONS` — oracle defines `~_Π`; TM runs *inside*; `a=b ⟺ a∼_Π b`; trace-distance `~_ε` | — |
| Non-associativity | **T01**: qubit matrix reps associative (control); true non-assoc in a later octonion lane | "seed is a free magma / non-associative" (earlier draft of this doc) |
| Claim grade | promotable routes only; float-tolerance is `diagnostic_float_nonclaim`; `promotion_allowed=false` | float-tolerance reported as "PASS" (earlier draft of this doc) |

Where this document previously asserted the superseded column, the correction is
called out inline (see §1.3, §3, §3a, §8) rather than silently overwritten, so
the drift is auditable rather than re-buried.

---

## 1. Foundational postulates

### 1.1 Entropic monism (the single substance)

There is exactly one primitive: **constraint on distinguishability**. Everything
else — objects, laws, geometry, dynamics, time — is a *pattern* in how that
constraint is organized. Concretely, the model does **not** posit a primitive
set of objects, a primitive identity, a primitive metric, or a primitive time.
It posits:

- a space of **states** (not objects),
- a collection of **admissible probes**,
- **constraints** on how probes may compose.

### 1.2 Emergent identity (the axiom replacement)

Primitive self-identity `a = a` is rejected and replaced by

$$ a = a \quad\Longleftrightarrow\quad a \sim b \ \text{ under all admissible probes.} $$

Read operationally: `a` is "the same" only insofar as no admissible probe can
distinguish it. Identity is therefore constraint-relative and *earned*, and
objects are equivalence classes rather than primitives.

### 1.3 Base constraints (canonical names: F01 / N01 / T01 + the meta-rule)

These are the current-wiki names (`s1-qubit-ladder-f01-n01-t01-2026-06-10`),
which supersede the generic C1/C2/C3 labels used in an earlier draft.

| ID | Name | Statement | Ratchet role |
|----|------|-----------|--------------|
| **M0** | Weakest-structure (meta) | Admit the *weakest* structure that resolves the pending query; best axioms assume the least. | Cost metric — smallest legal leap up the ladder (§3a). |
| **F01** | Finitude | Finite bound on distinguishability/resolution/capacity; the earned layer is always Turing-runnable with a **finite presentation** (finite variables, constraints, generators, relations). | Each rung a concrete enumerable object; infinities *earned as limits*, never assumed. |
| **N01** | Non-commutation **before** anticommutation | Root order-pressure `[A,B]=AB−BA ≠ 0`, or operationally `A(Bx) ≁_𝓜 B(Ax)`. Anticommutation `{A,B}=0` is a **sharpened Clifford special case, not the root**. | Commutativity (and the Clifford/anticommuting sharpening) are *earned*, not default. |
| **T01** | Ternary / bracketing / non-associativity boundary | `(AB)C − A(BC)` must be *tested*, not faked. In qubit **matrix** reps it is identically 0 (a required control); true algebra-level non-associativity is routed to a later **octonion / nonassociative extension lane**. | Non-associativity is earned on a named later rung, not present in the seed reps. |

**A1 (randomness-first), noted for completeness.** The current foundation doc
also carries a maximal-ignorance-prior axiom (randomness as an axiom, not noise
added later). It is recorded here as a foundational commitment; it does not enter
the §4–§7 realization directly.

> **Correction (supersedes an earlier draft of this spec).** A prior version
> claimed the seed structure is *itself* non-associative (a "free magma") and
> that associativity is climbed via A∞/E∞ towers. Per **T01**, that
> over-reached: qubit **matrix** multiplication is associative — `(AB)C−A(BC)=0`
> is a **control that must hold**, verified here as a `symbolic_identity` at 1Q
> and 2Q. Bracketing/non-associativity effects are permitted only in
> **channel / measurement / quotient schedules**, and *true* algebra-level
> non-associativity is an explicitly-earned later rung (octonion/alternative
> algebra, `[a,b,c]=(ab)c−a(bc)` alternating). N01 likewise is finer than "some
> ops don't commute": order-noncommutation is root, anticommutation is the
> earned Clifford sharpening.

---

## 2. The allowable-mathematics charter

From C1–C3 alone, whole classes of mathematics are inadmissible as *primitives*,
and a narrow class is *forced* to appear.

### 2.1 Forbidden at the base

Completed infinite sets · the real line as a completed object · global
coordinate systems · absolute metrics · free vector spaces with chosen bases ·
axiomatic identity objects · arbitrary functions on arbitrary domains. Each of
these presupposes infinite distinguishability or identity-without-probes. They
may reappear *later* only if constructed as explicit limits or approximations
(see U-7, §9).

### 2.2 Forced to appear early

| Order | Structure | Forced by |
|-------|-----------|-----------|
| earliest | Order/refinement: partial orders, refinement relations, coarse-graining hierarchies, lattices of equivalence classes | C3 — distinguishability precedes equality |
| next | Non-commutative composition: operator algebras, path-dependent composition, commutators/associators | C2 — order carries meaning |
| next | Morphisms before objects: transformation-centric formalisms; objects emerge as invariants/fixed points | C3 — transformations more primitive than things |

### 2.3 Admissible information measures

Entropy is admissible **only** as a measure of distinguishability under
constraint: a count of admissible refinements, bookkeeping of equivalence
classes, a measure of correlation constraint. This admits von Neumann entropy
(derived), conditional entropy (may be negative), and relative entropy between
admissible states. It does **not** admit entropy as heat, as time, as a
substance, or as an optimization objective at the base layer.

### 2.4 The meta-rule

> **Constraints must be explicit. Emergence must be implicit. Ambiguity must be
> declared.**

Only *gatekeeping* nuances (those whose omission would silently admit illegal
structure) are made explicit at the constraint layer; *dangerous* nuances are
recorded as open (§9); *emergent* nuances are left to be selected by
compatibility, ratcheting, or simulation.

---

## 3. The first forced construction

**Claim.** Given C0–C3, the weakest mathematical object that must exist is a
*finite non-associative, non-commutative, non-unital refinement structure* on
equivalence classes under probes — a **magmoid** (a precategory with a partial
binary composition, no associativity and no identity morphisms assumed). If it
did not exist, C0–C3 would be inconsistent.

> **Correction from v1.0.** An earlier draft called this a *category*. That is
> too strong: a category **assumes** associativity of composition
> `(f∘g)∘h = f∘(g∘h)` as an axiom, and (usually) identity morphisms. C0
> (weakest-structure) and C3 (no primitive identity) forbid assuming either. The
> correct seed is one rung *below* a category — a magmoid — with associativity
> and unitality left to be *earned* on the A∞ ladder (§3a). "Category" is a
> *target* the ratchet can climb to, not the seed.

### 3.1 Primitive ingredients

- **P1 (finite budget).** A finite bound `N` on distinguishable states under
  admissible probes. No topology, metric, or point-set — just the bound.
- **P2 (probes).** A collection `𝒫` of admissible probes; a probe `p ∈ 𝒫` acts
  on a state and returns a finite-resolution outcome. Probes need not commute.
- **P3 (composition).** For `p, q ∈ 𝒫`, the composition `p∘q` is admissible when
  defined, with `p∘q ≠ q∘p` permitted.

### 3.2 Emergent equivalence

Define `x ∼ y` iff for all `p ∈ 𝒫`, the outcomes of `p(x)` and `p(y)` are
indistinguishable. This yields equivalence classes with no privileged
representative and realizes §1.2 exactly.

### 3.3 Refinement preorder

On equivalence classes, define `[x] ⪯ [y]` iff every probe distinguishing
members of `[x]` also distinguishes members of `[y]` (`[y]` is at least as
refined). This is reflexive and transitive — a **preorder**, not yet
antisymmetric, and (by C2) **not yet a lattice**: because probes do not commute,
refinement is path-dependent (refining by `p` then `q` need not equal `q` then
`p`).

### 3.4 The surviving object

What remains is a set of equivalence classes `𝓔`, a preorder `⪯`, and a
**partially-defined, non-associative, non-commutative** composition of
refinement steps — i.e. a **finite refinement magmoid** with objects =
equivalence classes and arrows = admissible refinement steps, *without assumed
identity arrows and without assumed associativity*. Identity arrows and
associativity may be *earned* later (as fixed points and as A∞ coherence,
respectively).

### 3.5 Why it is unavoidable

Remove any ingredient and consistency breaks: drop finitude → infinite
distinguishability re-enters; drop non-commutation → refinement collapses toward
a Boolean lattice; drop weakest-structure → associativity/identity are smuggled
in for free; drop emergent equivalence → identity is smuggled in; drop
composition → no dynamics. Numbers, metrics, probability, entropy, geometry,
axes, engines, time, and causality have **not** appeared at this stage, by
design — they must be *earned*.

---

## 3a. The ratchet as the qubit ladder (F01/N01/T01 per rung)

The ratchet is monotone and generative: each rung is earned, none is un-earned,
and the target is "eventually everything." The **canonical ladder is the qubit
ladder** (not the abstract magma→group lattice an earlier draft drew):

```
 1Q ─▶ 2Q ─▶ 3Q ─▶ 4Q ─▶ 5Q ─▶ 6Q ─▶ 7Q ─▶ 8Q
 exact  bdry  Cl(6)  triality  safety  ── scaling / stress / overbuild ──
 Hopf   ctrl  floor  support   margin
```

| Rung | Carrier | density dim `4ⁿ−1` | Clifford | max anticommuting `2n+1` | chirality split |
|------|---------|--------------------|----------|--------------------------|-----------------|
| 1Q | `ℂ²`, `S³`, `CP¹` | 3 | `Cl₂` | 3 | 1+1 |
| 2Q | `ℂ⁴`, `S⁷`, `CP³` | 15 | `Cl₄` | 5 | 2+2 |
| 3Q | `ℂ⁸`, `S¹⁵`, `CP⁷` | 63 | `Cl₆` | 7 | 4+4 |
| … | … | … | … | … | … |
| 8Q | `ℂ²⁵⁶`, `S⁵¹¹`, `CP²⁵⁵` | 65535 | `Cl₁₆` | 17 | 128+128 |

- **1Q** is the exact Hopf foundation and is enough for geometric **curvature
  flux**: `A = dφ + cos2η dχ`, `F = dA = −2 sin2η dη∧dχ`, `∫F = −4π`
  (closed-form integral, verified §8). 3Q is the *minimum* `Cl(6)`/`ℂ⁸`/
  three-slot floor for the QIT-engine layer; 4Q–8Q are support / scaling /
  stress rungs, **not** new minimum claims. 8Q is a **finite overbuild ceiling**,
  not an infinite-escalation rule.
- **Max-anticommuting bound `m ≤ 2n+1` is a theorem, not a construction:** `m`
  pairwise-anticommuting Hermitian-unitary generators force a `Clₘ(ℂ)`
  representation of minimal complex dimension `2^⌊m/2⌋ ≤ 2ⁿ`, hence `m ≤ 2n+1`.

**"Smallest leaps up" = deepen by one qubit rung** only when a specific
downstream claim demands it — never climb past the current target for its own
sake. Every rung must emit an `F01_finitude_receipt`, an
`N01_noncommutation_receipt` (witnesses O1–O6), and a `T01_bracketing_receipt`
(matrix associator control + octonion-lane boundary).

---

## 3b. The oracle — it defines identity; the Turing machine runs inside it

The core formalizes the duality **deduction ↔ induction = TM ↔ oracle = reason ↔
perception**. The current foundation doc is explicit about the layering
(`EM_BOOTPACK … AXIOMS_FOUNDATIONS`):

> A Turing machine manipulates discrete symbols. A physical **oracle** is what
> makes those symbols *well-defined* by supplying the probe set Π and therefore
> the equivalence relation `~_Π`. **The oracle defines what counts as "the
> same"**; the TM is a *secondary* layer that runs *inside* those equivalence
> classes.

So the oracle is **prior**, not an add-on above the machine: it fixes the
probe-quotient `S/~_Π`, and the TM then computes on the resulting finite symbol
classes. Concretely (QIT-native):

- **Probes** `𝓜` (POVMs/instruments) with tolerance `ε`;
- **Observational equivalence** `ρ ∼_ε σ ⟺ ∀M∈𝓜, |p(M|ρ)−p(M|σ)| ≤ ε`,
  upper-bounded by trace distance: `ρ ∼_ε σ ⇐ D(ρ,σ)=½‖ρ−σ‖₁ ≤ ε` (verified §8);
- **A name denotes an equivalence class:** `a := [ρ]_{∼_ε}`. Hence `a = b ⟺ a
  ∼_Π b` — the operational-identity axiom, the exact backbone of **radical
  Humean nominalism**: no hidden essence, only operational indistinguishability.

**Where "oracle freedom" lives:** inside equivalence-class *degeneracy*. When
many microstates share one symbol class and the internal symbol dynamics don't
fix which representative occurs, the oracle selects the representative (subject
to global constraints). Pre-IGT, no teleological weighting is assigned — but
this degeneracy is the formal seat of the oracle. The monotone accumulation of
earned distinctions is entropic monism's arrow and the ratchet's ordering index
(U-2); entropy is the **readout** of the distinguishability process, *not its
substance* — and (per the current wiki) it is not an argument of admissibility
at the foundation.

---

## 4. The concrete finite realization — state space

Everything below is **one admissible realization** of the core: the smallest
non-commutative operator model (a single qubit) equipped with the Hopf/torus
geometry that supports nested non-commuting loops. Its status is *candidate
attractor*, not canon (U-1, §9).

### 4.1 Carrier and density spaces

| Object | Definition |
|--------|-----------|
| Hilbert carrier | `H = ℂ²` |
| density space | `𝒟(H) = { ρ ∈ B(H) : ρ ⪰ 0, Tr ρ = 1 }` |
| normalized carrier | `S³ = { ψ ∈ ℂ² : ‖ψ‖ = 1 }` |
| left / right spinor | `ψ_L, ψ_R ∈ S³` |

### 4.2 Pauli basis (exact matrices)

$$
I=\begin{pmatrix}1&0\\0&1\end{pmatrix},\
\sigma_x=\begin{pmatrix}0&1\\1&0\end{pmatrix},\
\sigma_y=\begin{pmatrix}0&-i\\i&0\end{pmatrix},\
\sigma_z=\begin{pmatrix}1&0\\0&-1\end{pmatrix},\
\sigma_-=\begin{pmatrix}0&0\\1&0\end{pmatrix},\
\sigma_+=\begin{pmatrix}0&1\\0&0\end{pmatrix}.
$$

with `σ_± = ½(σ_x ± i σ_y)` (verified, §8 C1). Density coordinates:
`ρ = ½(I + r_x σ_x + r_y σ_y + r_z σ_z)`.

### 4.3 Hopf chart and torus geometry

Spinor chart (`s ∈ {L,R}`, `η ∈ [0, π/2]`, `φ, χ ∈ [0, 2π)`):

$$
\psi_s(\phi,\chi;\eta)=\begin{pmatrix} e^{i(\phi+\chi)}\cos\eta \\ e^{i(\phi-\chi)}\sin\eta \end{pmatrix}.
$$

| Object | Definition |
|--------|-----------|
| Hopf projection | `π(ψ) = ψ† σ⃗ ψ = (r_x, r_y, r_z) ∈ S²` |
| **Bloch coordinates** | `r_x = sin2η·cos2χ`, **`r_y = −sin2η·sin2χ`**, `r_z = cos2η` |
| density reduction | `ρ_s = ψ_s ψ_s† = ½(I + r⃗·σ⃗)` |
| fiber-blindness | `ρ_s(φ+θ, χ; η) = ρ_s(φ, χ; η)` |
| torus family | `T_η = { ψ_s(φ,χ;η) : φ,χ ∈ [0,2π) } ⊂ S³` |
| Clifford torus | `T_(π/4)` (maximal orbit entropy, §6.1) |

> **Convention note (audit finding, §8 C2).** With the chart exactly as written
> in §4.3, the Hopf projection gives `r_y = −sin2η·sin2χ` — a **minus** sign
> relative to the `+sin2η·sin2χ` printed in `terrain rosetta strong math.md`.
> The density reduction `ρ = ½(I + r⃗·σ⃗)` is exact once the chart's own `r⃗` is
> used. This is a handedness convention (equivalently `χ → −χ`, or conjugating
> the chart), not a mathematical error, but it must be fixed once and used
> consistently. **This spec adopts the chart-consistent sign** `r_y =
> −sin2η·sin2χ`. If the `+` convention is preferred instead, replace the chart's
> second component phase `e^{i(φ−χ)}` with `e^{i(φ+χ)}·e^{−2iχ}`… — simplest is
> to define the chart with `χ → −χ`.

### 4.4 Loop geometry (Hopf connection)

Connection `𝒜 = −i ψ† dψ = dφ + cos2η dχ`. The two loop families per sheet:

- **inner / fiber loop** `γ_f^s(u) = ψ_s(φ₀+u, χ₀; η₀)` — density-stationary,
  `ρ_f^s(u) = ρ_f^s(0)`.
- **outer / lifted-base loop** `γ_b^s(u) = ψ_s(φ₀ − cos2η₀·u, χ₀+u; η₀)` —
  horizontal (`𝒜(γ̇_b) = 0`), density-traversing.

---

## 5. Weyl sheets and base dynamics

Two global orientation sheets share a base Hamiltonian `H₀ = n_x σ_x + n_y σ_y +
n_z σ_z` and take opposite signs:

| Sheet | Density | Hamiltonian | Bloch law |
|-------|---------|-------------|-----------|
| left (Type 1) | `ρ_L = ½(I + r⃗_L·σ⃗)` | `H_L = +H₀` | `ṙ⃗_L = +2 n⃗ × r⃗_L` |
| right (Type 2) | `ρ_R = ½(I + r⃗_R·σ⃗)` | `H_R = −H₀` | `ṙ⃗_R = −2 n⃗ × r⃗_R` |

The Bloch laws follow from `ρ̇ = −i[H, ρ]` and are verified to machine precision
(§8 C3). The sign flip `H_R = −H₀` is the single origin of the Type-1/Type-2
duality and of the opposite loop handedness.

Dissipator (GKSL form): `D[L](ρ) = LρL† − ½(L†Lρ + ρL†L)`.

---

## 6. The eight terrain generators

Each Weyl sheet carries four terrain generators indexed by a topology family
`{Se, Ne, Ni, Si}`. All eight are valid GKSL generators, so each stage channel
`Φ_τ^s(t) = exp(t·X_τ^s)` is completely positive and trace-preserving for `t ≥ 0`
(verified, §8 C4).

### 6.1 Left sheet (Type 1) generators

| Topology | Terrain | Generator |
|----------|---------|-----------|
| Se | Funnel | `X_F^L(ρ) = Σ_k D[L_k^{F,L}](ρ) − i ε_{F,L}[H_L, ρ]` |
| Ne | Vortex | `X_V^L(ρ) = −i[H_L, ρ] + ε_{V,L} Σ_k D[M_k^{V,L}](ρ)` |
| Ni | Pit | `X_P^L(ρ) = γ_{P,L} D[σ_−](ρ) − i ε_{P,L}[H_L, ρ]` |
| Si | Hill | `X_H^L(ρ) = −i[K_L, ρ] + Σ_j κ_{H,L,j}(P_j^{H,L} ρ P_j^{H,L} − ½{P_j^{H,L}, ρ})` |

### 6.2 Right sheet (Type 2) generators

| Topology | Terrain | Generator |
|----------|---------|-----------|
| Se | Cannon | `X_C^R(ρ) = Σ_k D[L_k^{C,R}](ρ) − i ε_{C,R}[H_R, ρ]` |
| Ne | Spiral | `X_S^R(ρ) = −i[H_R, ρ] + ε_{S,R} Σ_k D[M_k^{S,R}](ρ)` |
| Ni | Source | `X_{So}^R(ρ) = γ_{So,R} D[σ_+](ρ) − i ε_{So,R}[H_R, ρ]` |
| Si | Citadel | `X_{Ci}^R(ρ) = −i[K_R, ρ] + Σ_j κ_{Ci,R,j}(P_j^{Ci,R} ρ P_j^{Ci,R} − ½{P_j^{Ci,R}, ρ})` |

Operators are Pauli-affine: `L_k = a_{k0}I + a⃗_k·σ⃗`, projectors `P_j =
½(I + m̂_j·σ⃗)` with `[K, P_j] = 0`. **Exact terrain-pair separation:**

| Pair | Mathematical difference |
|------|------------------------|
| Funnel / Cannon | opposite Weyl sign; distinct dissipative family |
| Vortex / Spiral | opposite Hopf circulation handedness |
| Pit / Source | sink `D[σ_−]` (→ `|1⟩`) vs source `D[σ_+]` (→ `|0⟩`); verified §8 C6 |
| Hill / Citadel | distinct retained strata on opposite sheets |

### 6.3 Axis structure

Each terrain carries a bit-vector. Axis-0 `b₀ = sgn(cos2η) = sgn(r_z)` splits
the Bloch sphere at the Clifford torus (`η = π/4`), where the longitude-averaged
state `ρ̄(η) = diag(cos²η, sin²η)` reaches maximal entropy `S = ln 2` (verified,
§8 C7). Axis-3 `b₃` is `−1` inner / `+1` outer. **Axis-6 is derived, not
primitive:**

$$ b_6 = -\,b_0\, b_3 \qquad (\text{0 violations across all 8 terrains, §8 C5}). $$

`b₆ = +1` is op-first token order ("UP"); `b₆ = −1` is terrain-first ("DOWN").

---

## 7. Loops, stages, and the 16 placements

The four canonical loops are the sheet × loop-family products, distinct because
`Γ_f^L ≠ Γ_b^L`, `Γ_f^R ≠ Γ_b^R`, and `H_L ≠ H_R`:

`(ρ_L, Γ_f^L)`, `(ρ_L, Γ_b^L)`, `(ρ_R, Γ_f^R)`, `(ρ_R, Γ_b^R)`.

Each loop runs its four terrain stages `(carrier constraint ψ(t) ∈ Γ, density
law ρ̇ = X_τ(ρ))`, giving **4 terrains × 4 loops = 16 stage placements** — the
full stage atlas of the realization.

---

## 7a. The geometric constraint manifold — DOFs that must NOT collapse

> **Methodological lock (author instruction).** The axes are the **degrees of
> freedom of the constraint manifold**, and they exist *to be explored across
> their full range* — they must **not** be collapsed onto their most salient
> point. A reader (or an LLM) that folds two axes together, or reads only the
> Clifford/fixed-point value of one, has destroyed the object. Each axis below
> is an independent DOF; the engine's job is to traverse them, not to sit at
> their extremum. This section is deliberately gated: no claim here promotes
> past `scratch_diagnostic`.

### 7a.1 The axes are Carnot/Szilard-like DOFs in a different math base

The manifold's DOFs behave like the state variables of a thermodynamic engine,
but realized on a **finite QIT carrier** rather than a classical gas. Per the
current wiki (`dual-carnot-szilard-qit-engine-witness`), Carnot and Szilard are
**not rival engines** — they are two legality grammars dual-stacked on one
carrier:

- **Carnot** contributes *thermodynamic* legality (adiabatic/isothermal-analog
  transport on the manifold);
- **Szilard** contributes *measurement / memory / feedback* legality;
- the QIT-engine witness is their **noncommuting interaction** on a shared
  `ψ / ρ` carrier — `g_{DI}(ρ) = (D∘I − I∘D)(ρ) ≠ 0` is the engine's signature,
  and it is an instance of **N01** (order-pressure), not a new postulate.

### 7a.2 The 720° double loop (SU(2) double cover)

The engine runs on a **720° cycle = two 360° loops**, which is exact spinor
geometry, not analogy: `SU(2) → SO(3)` is a double cover, so a spinor returns to
itself only after `4π`, and the `4π` cycle factors canonically into two `2π`
loops. In this model:

- one 360° loop is the **deductive** loop, the other the **inductive** loop —
  the same duality as running a Carnot/Szilard engine *forward vs. reverse*
  (which of the two a loop is depends on traversal direction);
- there are **two independent engine models**, the **left and right Weyl
  spinors** (`H_L = +H₀`, `H_R = −H₀`; §5), each carrying its own pair of 360°
  loops;
- **deductive/inductive are swapped between inner and outer loops**, and the
  swap is *opposite* on the left vs. right engine — this is the chirality DOF and
  must be kept as its own axis, never merged with the sheet label. Inner/outer
  map to the **nested Hopf tori** (§7a.3).

These are four independent bits — {left/right} × {inner/outer} × {deductive/
inductive traversal} with the D/I assignment *derived* from the first two — and
collapsing any of them is the specific failure this section guards against.

### 7a.3 Nested geometry, flux, and the geometric ratchet

Flux is **not primitive** and **not early** (`weyl-flux.md`): within a *single*
torus shell (η const) the curvature restricts away and one obtains **holonomy,
not flux**. Flux is intrinsically an **inter-shell** (nested) quantity:

$$ \Phi(\eta_i,\eta_j) = 2\pi\big(\cos 2\eta_i - \cos 2\eta_j\big), \qquad
   \oint_{\text{shell}} A = -2\pi\cos 2\eta \ \text{(holonomy, single shell).} $$

This is the precise sense in which **"flux does not work unless geometry is
nested"** — and it is verified, not asserted (§8, `flux_nesting_ablation_jax.py`):

- **Nesting requirement.** A real flat-carrier ablation `A = 0` run through the
  *same* transport pipeline yields holonomy `≡ 0` and flux `≡ 0` (this closes
  hardening item #1 of the repo's own `audit_verdict.md`, which had used a
  hand-authored dict). A single shell gives nonzero holonomy but no defined flux.
- **The geometric ratchet.** Adjacent-shell pairwise fluxes are **order-
  sensitive** (their sign pattern flips when the shell filtration is reversed),
  while the **total Chern-like invariant is order-indifferent**
  (`|Φ(0,2)| = 7.295` either direction). *This is the ratchet embodied in
  geometry*: a direction-dependent, non-undoable pairwise accumulation whose
  global charge is conserved — the monotone-earning ratchet (§3a) realized as a
  transport asymmetry across nested shells.

### 7a.4 Non-associativity, G2, and the nested carrier (open, gated)

The nesting that flux requires is the same structure that the author expects to
carry a **G2-like** geometry. Per `octonion-g2-sedenion-carrier-geometry-audit`,
this is **installed by a stronger carrier constraint, not forced by the bare
root** (consistent with **T01**): true algebra-level non-associativity appears
only once the carrier is pushed to `Cl(0,6)` / ≥7 imaginary units / the
three-qubit-Weyl rung, where the octonion associator `[a,b,c] = (ab)c − a(bc)`
becomes non-zero (alternating). G2 = Aut(𝕆) is the **leading** candidate for the
nested-manifold symmetry; the quaternionic rung sits between, and the variant
set (Spin(7), sedenion extensions) is kept **explicitly open**. The Weyl spinors
"act differently when nested" precisely because the nesting changes which
division-algebra rung the carrier occupies — a claim the ratchet must *earn* at
the 3Q rung, not assume at 1Q.

---

## 7b. Building the manifold layer by layer, then running the axes

The manifold is **constructed bottom-up, each layer earned before the next**, and
only then are the axis DOFs run **one at a time** in the owner's order
`6 → 5 → 3 → 4 → 1 → 2 → 0` (`manifold_build_ladder.py`). This order runs the
most-derived / cheapest axes first and the late feedback-polarity gate (Axis 0)
last, matching the repo split "Axes 1–3 topology, 4–5 operators, 6 sign, 0 late."

### 7b.1 Layer ladder (all earned, `scratch_diagnostic`)

| Layer | Earned check |
|-------|--------------|
| **L1 carrier** | normalized qubit state, `‖ψ‖ = 1` |
| **L2 geometry** | Hopf chart → Bloch vector on the unit sphere (`‖r⃗‖ = 1`) |
| **L3 Weyl/chirality** | `H_L=+H₀`, `H_R=−H₀` give measurably opposite Bloch precession |
| **L4 transport + nesting** | flux needs ≥2 shells; `A=0` ablation → 0 (§7a.3, `flux_nesting_ablation_jax.py`) |
| **L5 placement (16)** | all 8 terrain generators are valid CPTP semigroups (min eigenvalue ≥ 0) |

### 7b.2 Axis run (six read out; Axis 0 gated)

| Axis | Meaning | Readout | Earned |
|------|---------|---------|--------|
| **6** | signed precedence | `b₆ = −b₀·b₃`, 0/8 violations | ✓ |
| **5** | operator family | 4 generator archetypes are distinct channels | ✓ |
| **3** | inner/outer (fiber/base) | fiber loop leaves `ρ` invariant; base loop moves it | ✓ |
| **4** | deductive/inductive | generator composition order `UE ≠ EU` (an N01 instance) | ✓ |
| **1** | unitary/CPTP | purity preserved (unitary) vs decreased (dissipative) | ✓ |
| **2** | representation frame | direct vs conjugated frame give distinct Bloch trajectories | ✓ |
| **0** | feedback polarity | Ne/Ni = +entropy/allostatic; Se/Si = −entropy/homeostatic | **UNBUILT** |

### 7b.3 Axis 0 — the gate, and *why* it stalls (reproduced honestly)

Per doctrine (`axis0-current-doctrine-state-card`), **Axis 0 remains unbuilt**:
prior estates used static shell labels with no entropy field from evolving states
and no perturb-evolve-classify loop, so they measured a static coordinate
polynomial, not feedback polarity. The owner's own definition
(`AXIS0_SPEC_OPTIONS_v0.3`) is a **response derivative**, *not* an entropy sign:

$$ \text{allostatic if } \tfrac{dD}{d\lambda} > 0, \qquad
   \text{homeostatic if } \tfrac{dD}{d\lambda} \le 0. $$

This build runs a **real** perturb-evolve-classify loop (state-derived quantities,
dynamic steady states, averaged perturbation directions) and tests **six**
principled functionals for the target split Ne/Ni(+) vs Se/Si(−): participation
ratio of deviation, norm-deviation, purity, von-Neumann entropy, `dD/dλ`, and
entropy-production `dS`. **None realizes the split.** Every functional either
flatlines to one sign or isolates the **Ni** family alone.

The root cause is localized, not hand-waved: **Ni (Pit/Source) is the only family
whose dissipator (`D[σ_∓]`) is *source-locked* in the ledger**; the Se/Ne/Si
dissipators depend on the ledger's *symbolic* operator families `L_k, M_k, P_j`,
which are **not yet locked**. So Axis 0 cannot be a fixed functional imposed on
the states — it depends on operator content the ratchet has not yet earned. This
reproduces the repo's `NO-STABLE-DISTINCTION-YET` verdict from first principles
and says *what must be earned next*: the locked Se/Ne/Si dissipators. **No
parameter was tuned to force the split** — doing so would manufacture canon.

---

## 7c. The co-ratchet — entropy and operators must be earned too

The primal ratchet (§3a) earns *states/structures* on the manifold. But entropy
and operators are **not external instruments** — they also run on the manifold
and must themselves be earned. This is the **co-ratchet**, and it has an exact
mathematical home in **Tomita–Takesaki modular theory + the GNS construction**.
The subtle "entropy and operators can be seen as one" is literally true there
(verified in `constraint_core_symbolic.py` / the modular checks, all exact):

1. **Entropy *is* a Hamiltonian.** A state `ρ` generates its own **modular
   Hamiltonian** `K_ρ = −log ρ`, and `S(ρ) = ⟨K_ρ⟩_ρ`. Von-Neumann entropy is
   the expectation of the operator the state itself defines — entropy and
   operator are two faces of one object. *(verified: `0.439354 = 0.439354`.)*
2. **Relative entropy = modular free energy.** `S(ρ‖σ) = ⟨K_σ − K_ρ⟩_ρ ≥ 0`.
   The entropy *difference* is an operator expectation. *(verified, `≥ 0`.)*
3. **GNS: the state builds the operator Hilbert space.** `⟨A,B⟩_ρ = tr(ρ A†B)`
   is positive-semidefinite, so the Hilbert space of operators is *reconstructed
   from* the state. This is the exact sense in which **probes and density
   matrices emerge first, and operators/entropy run on them** — the Hamiltonian
   is downstream of the Hilbert space the state generates, your "difference
   between a Hamiltonian and a Hilbert space." *(verified: Gram matrix PSD.)*
4. **The co-ratchet shares the primal monotone.** Relative entropy is
   **non-increasing under every CPTP map** (data-processing inequality). So the
   co-ratchet (entropy/operator side) ratchets in the *same* monotone direction
   as the primal ratchet (§3a) — they are **dual, not independent**.
   *(verified: `0.3404 ≥ 0.2352`.)*

**Consequence for the build.** Each layer runs on the previous one in a
non-commuting, finitist way — and the operator/entropy content earned at each
layer is fixed by the co-ratchet, not chosen freely. This is exactly why Axis 0
(§7b.3) cannot yet close: its readout is an entropy/operator object, and the
co-ratchet has not yet earned the locked Se/Ne/Si dissipators it needs. The
families to test as they are earned — coherent information `I_c = −S(A|B)`,
conditional and mutual entropy, spectral/gradient algebras, Lagrangian vs
Eulerian readouts — are **candidate co-ratchet rungs**, each admissible only once
its operator content is locked and its map is named (`shell-local-to-coupled`
discipline). Axis 0's strongest current candidate family in the repo is precisely
**coherent-information / negative conditional entropy**, consistent with this.

---

## 7d. The three-qubit floor: octonions, Cl(0,6), and G2

Many objects in the model **cannot run below three qubits**, and this is not a
modelling convenience — it is forced by where non-associativity becomes available
under **T01**. The Cayley–Dickson ladder makes the floor precise
(`three_qubit_octonion_fep.py`, all `scratch_diagnostic`, reproducing the repo's
`nonassociativity-carrier-layer-status-2026-06-07` numbers exactly):

| Algebra | dim | associator max-norm | `dim Der` (automorphism Lie algebra) |
|---------|-----|---------------------|--------------------------------------|
| ℝ | 1 | 0 | 0 |
| ℂ | 2 | 0 | 0 |
| ℍ | 4 | **0** (associative) | 3 |
| **𝕆** | 8 | **2.0** (non-assoc., witness basis `[1,2,4]`) | **14 = dim G₂** |
| 𝕊 | 16 | 2.0 (also non-alternative, defect 2.0; zero divisors) | — |

Two facts fix the floor:

1. **Non-associativity is earned at 𝕆, not before** (associator `H = 0`, `O = 2.0`)
   — exactly the T01 boundary: qubit *matrix* reps are associative; genuine
   algebra-level non-associativity requires the octonionic rung. This is the
   octonion/G2 lane the earlier sections deferred to.
2. **The octonion carrier *is* three qubits.** The left-multiplication operators
   `L_{e₁},…,L_{e₆}` satisfy the Clifford relation `{L_i, L_j} = −2δ_ij`, generate
   an algebra of **rank 64 = Cl(0,6)**, and act irreducibly on **ℂ⁸ = 3 qubits**
   (verified; quaternion control `L_{e₁}, L_{e₂}` → rank 4 = Cl(0,2) → ℂ² = 1
   qubit). So the smallest carrier that holds the full non-associative structure —
   and with it the **G₂ = Aut(𝕆)** symmetry (`dim Der(𝕆) = 14`) the nested manifold
   (§7a.4) expects — is exactly the **3-qubit / ℂ⁸ / 3-qubit-Weyl** rung.

**Placement guardrail (from the carrier-status doc, honored here).**
Non-associativity is **root-native but rung-later**: current receipts place it as
**R3 carrier / bracketing pressure**, *not* an R1/R2 root constraint. It must not
be promoted to a root constraint "unless a bounded discriminator shows that
erasing associator sensitivity changes the R1/R2 admissible set itself." The
sedenion rung (𝕊: non-alternative, zero divisors) and Spin(7) remain open. G₂ is
the leading nested-manifold symmetry candidate, not a closed result.

---

## 7e. Pure-QIT active inference (FEP) — no smuggled classical math

The model runs an **active-inference / free-energy** loop, but in a **pure-QIT**
form: every quantity is a density matrix or a relative entropy — no classical
probability vectors, no Gaussian recognition densities, no Laplace approximation.
The translation (`three_qubit_octonion_fep.py`, on the 3-qubit carrier of §7d):

- **Variational free energy → Umegaki relative entropy.** Classical
  `F = E_q[−ln P(y,x)] − H[q]` becomes `F = S(ρ_q ‖ ρ_model) = tr ρ_q(log ρ_q −
  log ρ_model) ≥ 0`. Surprise, complexity−accuracy, and the KL+surprise
  decomposition all carry over as **modular / relative-entropy** quantities —
  which is exactly the **co-ratchet** object of §7c (relative entropy = modular
  free energy). FEP and the co-ratchet are the *same* free energy.
- **Perception/action = belief update = CPTP map.** Minimizing `F` by updating
  `ρ_q` is a quantum channel, and by the **data-processing inequality** `F` is
  non-increasing under it (verified: `F: 1.59 → 0.29` under a dephasing update).
  This is the active-inference descent, realized as a legal CPTP step — no
  classical gradient smuggled in.
- **Markov chains ≈ Feynman path integrals, finitely and non-commutingly.** Both
  are **finite ordered products of propagators** `K = ∏_t U_t`; what makes the
  path-sum quantum rather than classical-stochastic is **N01 non-commutation**
  `[U_s, U_t] ≠ 0` (verified: forward vs reversed composition differ). The path
  integral is admissible only in the finitist + non-commuting form — a Markov
  blanket is a **finite cut carrier**, not a continuum limit.

**Claim ceiling (from `fep-to-axis0-bridge-claim-ceilings`, binding).** Pure-QIT
FEP supplies **support vocabulary only** — boundary/blanket questions,
prediction-first update loops, persistence under uncertainty, information-geometry
neighbor terms, epistemic-probe value. It **cannot** close `Axis 0`, `Φ0`, the cut
kernels `ρ_AB`/`Ξ`, gravity, field-wide compression, or consciousness. In
particular the banned identifications hold: *"the Markov blanket is the Axis 0
cut"* and *"expected free energy is Φ0"* are **not** claimed. FEP proposes finite
boundary/probe fixtures for Axis-0-adjacent questions; it does not admit the
bridge.

This closes back onto §7b.3: Axis 0's strongest candidate readout is coherent
information / negative conditional entropy — a QIT quantity FEP can *motivate* but
not *certify*. The certification must come from the co-ratchet earning the locked
Se/Ne/Si dissipators, not from the FEP lane.

---

## 7f. The 16-stage operator atlas and the 8-of-16 accessibility law

The 16 placements of §7 are not just loop×terrain products — each is a **distinct
kind of mathematics that operates on information differently** (a distinct
information operator). Their fine structure, reconciled from the owner's original
pre-LLM pattern source (`sixteen_stage_atlas.json`), is:

- **16 stages = 4 terrains × 2 judgments × 2 engines.** Each stage is named by its
  **native operator** in the owner's Jungian notation `(perceiving)(judging)` — e.g.
  `SiTe`, `NeFi`. The perceiving function fixes the QIT **terrain**; the judging
  function is the stage's dominant sub-operator.
- **8 shared operator-types, 2 engine realizations.** The eight operator-types
  `{SiTe, SiFe, NeTi, NeFi, SeTi, SeFi, NiTe, NiFe}` each appear **twice** — once on
  the **left** engine (`H_L=+H₀`, Type-1 Weyl spinor) and once on the **right**
  (`H_R=−H₀`, Type-2), distinguished by the introversion/extraversion (I↔E)
  chirality flip. `SiTe` = ISTJ on the left (terrain **Hill**), ESTJ on the right
  (terrain **Citadel**).
- **The 8-of-16 accessibility law.** A person **is one engine** (left *or* right
  Weyl spinor) and therefore accesses **exactly 8 of the 16 stages** — the 8 on
  their own sheet. The full engine can *integrate all 16 into process*; an
  individual carrier cannot. (This is stated as the model's personality-type
  reading; it is a **correlation overlay**, §0a — not primary math.)
- **4 sub-stages per stage → 64 addresses.** Each stage carries a **4-sub-stage
  function stack**, giving `16 × 4 = 64` — the same 64-address space audited under
  Axis 6. The four sub-stages of a stage **share one Axis-6 sign**: the ordering is
  fixed *inside* a stage, so `b₆ = −b₀·b₃` does not change across the four
  sub-stages (consistent with the 0/8 exhaustive check of §6/§8).

**Worked reconciliation — gradient descent.** The owner's expectation that
"gradient descent operates on only 2 topologies, probably `Si`, as `SiTe`" is
confirmed by the atlas: `SiTe` occupies **exactly two** of the eight terrains —
**Hill** (left) and **Citadel** (right), both `Si` (`sixteen_stage_atlas.json`).
So gradient descent, in this model, is the `Si`-terrain / `SiTe` operator, realized
once per engine — a single operator seen from two chiralities, not two separate
methods.

**Interpretive stance (from the source doc).** The correlation columns — Jung
functions, MBTI types, the IGT win/loss game, Big-5, the 4F/nervous-system and
political-compass overlays — are **many correlated perspectives on one operator**,
"different faces of the same thing… not distinct separate things." They are
**not** claimed as canonical or as perfect correlations (the owner notes the engine
patterns are correct for Type-1/Type-2 but "not all the correlations listed are
perfect"). They sit at the §0a correlation-overlay tier, above the primary QIT math.

> **Claim ceiling.** This section is a **structural map + one worked
> reconciliation**, `scratch_diagnostic`. The stage↔operator identifications
> (e.g. gradient descent = `SiTe`) are candidate correspondences to be earned
> per-operator, not admitted theorems; the personality-type reading is an
> explicitly non-canonical correlation overlay.

---

## 7g. Running the engine: the 64-microstep schedule and unique processing

The engines are not just an atlas — they **run**, stepping through a **64-microstep
schedule**. Reconciled from the repo source (`ENGINE_64_SCHEDULE_ATLAS.md`,
`QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md`), the live runtime object is:

$$ 64 = \underbrace{2}_{\text{engines (L/R)}} \times
        \underbrace{8}_{\text{terrains } (4\text{ topo}\times 2\text{ flux})} \times
        \underbrace{4}_{\text{judging operators}}. $$

> **[AUDIT FLAG 2026-07-01 — PENDING OWNER DECISION, do not silently resolve.]**
> This `64 = 2×8×4` treats every terrain×operator pairing as runnable. The
> native-operator law (§7q/§7t) licenses only 2 operators per terrain, i.e.
> `16 = 8×2` legal stages, under which `64 = 16 stages × 4 sub-stages` and the
> other 48 pairings are *inadmissible addresses*, not unused ones. The two
> readings of 64 are incompatible as stated; the owner decides which is canonical.

**The four judging operators are exact quantum channels on `M₂(ℂ)`** (verified
CPTP + correct fixed algebra, `engine_64_schedule_sim.py`):

| Op | Channel | Type | Bloch action |
|----|---------|------|--------------|
| `Ti` | z-basis pinching (cond. expectation onto `A_z=span{I,σ_z}`) | unital CPTP dephasing | contracts x,y → z-axis |
| `Te` | x-basis pinching (onto `A_x=span{I,σ_x}`) | unital CPTP dephasing | contracts y,z → x-axis |
| `Fi` | inner automorphism by `σ_x` (`SU(2)` x-rotation) | reversible unitary | rotates about x, preserves purity |
| `Fe` | inner automorphism by `σ_z` (`SU(2)` z-rotation) | reversible unitary | rotates about z, preserves purity |

**Up / down = the N01 ordering.** Each microstep composes a terrain flow `T_P`
with a judging operator `J` in one of two orders (Axis 6 precedence):

- **`down` (terrain-first):** `Φ_{PJ} = J ∘ T_P` — e.g. `SiTe` = **gradient
  descent** (compression terrain, then x-pinching). *This is the source-exact
  form of §7f's gradient-descent finding.*
- **`up` (operator-first):** `Φ_{JP} = T_P ∘ J` — e.g. `Te^up` = **gradient
  ascent / preconditioning**.

### The unique-processing result (the point of running the engine)

Does each of the 64 microsteps do **genuinely unique** information processing?
The answer depends entirely on the **observable**, and this exhibits the same
**collapse phenomenon** the repo documents for `eng_64` (`64 stages, only 16
distinct fingerprints`). The exact collapse *count* is observable-dependent — my
coarse order-blind readout yields **11** distinct, not the repo's 16 (a different
coarse observable) — so this is an independent demonstration of the degeneracy,
not a reproduction of that specific count:

| Readout | Distinct microsteps / 64 |
|---------|--------------------------|
| **order-blind, coarse** (single seed, symmetrized up/down, coarse scalar) | **11 / 64** — heavy collapse |
| **N01 order-sensitive** (terrain-first, multi-seed Bloch fingerprint) | **64 / 64** — full uniqueness |

**All 64 microsteps carry a real up≠down order gap** `‖T_P∘J − J∘T_P‖ > 0`
(mean ≈ 0.54). So the uniqueness of each engine stage is **not** obtained by
adding more terrains or operators — it is an **N01 (noncommutation) property of
the readout**. A sim that reads an order-blind observable will always see the
schedule collapse; a sim that reads the order-sensitive observable sees 64
distinct processors. This is the concrete fix for "each stage must do unique
processing," and it names precisely why prior sims stalled.

### Deep-ratchet layer precision

"Getting the most-ratcheted layers precise" is a gate, not a slogan. The deepest
geometric layer (L4 transport/holonomy, §7b.1) is **locked to its closed form**
`∮A = −2π cos2η`: independent recomputation gives `−4.442882938` with residual
`≈ 3×10⁻¹⁰`, and it is already converged at 256 transport steps (the residual is
the connection's finite-difference `ε`, not step count). Every layer above L4
inherits this precision floor.

> **Claim ceiling.** `scratch_diagnostic`, `promotion_allowed=false`. The 64
> schedule is run as a **finite enumeration with an order-sensitive observable**;
> this earns "unique processing under N01" and "closed-form layer precision," not
> full 64-state runtime-visitation closure or bridge/Axis-0 admission.

---

## 7h. The manifold as a nested attractor-basin hierarchy

The 2 engines, 4 topologies, flux, and 8 terrains are all **structure of the one
geometric constraint manifold**; the co-ratchet (operators + entropy, §7c) couples
to that structure as **sub-basins**. The whole model is then one attractor basin
with sub-basins and sub-sub-basins. This section earns that architecture against
the repo's **basin-manifold claim contract** (`basin-manifold-claim-contract.md`),
using the repo's own three-way attractor typing
(`attractor-basins-formal-reference.md`).

**Claim shape (contract-compliant).**
- *State space:* density matrices on `ℂ²` (Bloch ball), extensible to the 3-qubit
  carrier of §7d.
- *Update rule:* ordered CPTP cycle `E = Φ_n ∘ … ∘ Φ_1` (terrain GKSL flow, then
  judging operators).
- *Admissibility:* a state is in basin `B` if repeated `E` compresses it toward a
  persistent regime `A` and bounded perturbations stay recoverable.
- *Three attractor types (kept distinct, per repo):* **state** (→ one matrix),
  **process** (→ the channel-cycle structure), **equivalence** (→ a probe-class
  `[ρ]_P` — the strongest earned type, and exactly the identity logic
  `a=a ⟺ a∼b`).

**Top level — 8 terrain basins.** Iterating each terrain generator from 40 random
initial states to its limit set (`nested_basin_results.json`) gives **8 distinct
basins** (min pairwise distance of the rich fingerprint — center + dispersion +
purity + entropy + z-bias — is `> 0`; DOF-no-collapse holds under the full
fingerprint, though **6 of 8 centroids sit near the origin** — a coarse
centroid-only readout collapses them, the same lesson as §7g).

**Kill test — viability vs attractor (contract req; `falsification-sim-designs.md`).**
Running each terrain from many ICs and asking whether *all* trajectories converge
to a single point cleanly **splits the 8**:

| Terrain type | Terrains | Endpoint spread | Verdict |
|---|---|---|---|
| `Ne`, `Ni` | Vortex, Spiral, Pit, Source | `≈ 0.000–0.001` | **attractor** (converges to point/class) |
| `Se`, `Si` | Funnel, Cannon, Hill, Citadel | `≈ 0.03–0.09` | **viability** (bounded, non-converging) |

This attractor/viability split — arrived at from an **independent** dynamical test
— coincides with the **Axis-0 polarity** (`Ne/Ni` allostatic/+ vs `Se/Si`
homeostatic/−, §7b.3). Two unrelated probes landing on the same `Ne/Ni | Se/Si`
partition is meaningful corroboration of that DOF (it is *not* a closure of
Axis-0's owner-defined `dD/dλ` readout, which remains open, §7b.3).

**Sub-basins — the operator/entropy co-ratchet.** Within a terrain basin, the four
judging operators refine the limit set into **distinct sub-basins**:
- **Pit** (attractor terrain): 4 sub-basins, min separation **0.445** — a pinned
  fixed point gives the operators a definite state to separate.
- **Hill** (viability terrain): 4 sub-basins, min separation **0.005** — a bounded
  class offers less to split. (Honest asymmetry, not a defect.)

**Killed non-basin explanation (contract req #8).** The sub-basin structure is
genuinely `N01`-driven, not an artifact of the readout: a **noncommuting** pair
`(Te,Fe)` has order gap `0.268`; a **commuting control** `(Tz,Tz)` has order gap
`2×10⁻¹⁷` — the structure vanishes exactly when noncommutation is removed.

> **Claim ceiling.** `scratch_diagnostic`, `promotion_allowed=false`. Earned:
> 8 distinct terrain basins (rich fingerprint), a clean attractor/viability kill
> split coinciding with Axis-0 polarity, operator sub-basins with a passing
> commuting-control kill test. **Not** earned: full basin-boundary topology,
> sub-sub-basin depth beyond one level, or promotion of any basin to
> state-attractor closure (most terrains are equivalence/viability class, per the
> repo's narrower-claim guidance).

---

## 7i. Source-locking the terrains, and why Axis-0 is not terrain-local

The standing blocker across §7b.3, §7h, and every prior model was that only Ni's
dissipator (`σ∓`) was source-locked; the Se/Ne/Si dissipators were symbolic
families (`D[L_k]`, `D[M_k]`, `P_j`), so an agent had to *choose* them — which
manufactures canon. This section closes that, using the repo's own **scratch Bloch
maps** (`igt-pattern-explicit-math-reference.md` §12) as the source of truth.

**Source-locking (achieved).** Each terrain's scratch Bloch map pins a **fixed
point**, which determines its GKSL content without invention:
- **Se (Funnel/Cannon)** — the scratch map `(√.78 x, √.78 y, .78 z + .22·.86)` is a
  **generalized amplitude damping** toward `z* ≈ +.86` (Funnel) / `−.86` (Cannon),
  *not* the pure `D[σ_z]` dephasing used earlier. Realized as
  `γ₊ D[σ₊] + γ₋ D[σ₋]` with `z* = (γ₊−γ₋)/(γ₊+γ₋)`.
- **Ni (Pit/Source)** — already source-locked: `D[σ₋]` → `z*=−1` (Pit),
  `D[σ₊]` → `z*=+1` (Source).
- **Ne (Vortex/Spiral)** — Hamiltonian-dominant + weak isotropic depolarizing
  (scratch `.94·R_N` → center), fixed point at the maximally mixed state.
- **Si (Hill/Citadel)** — projective invariant-subspace preservation.

Integrated as GKSL generators (CPTP by construction), the settled fixed points
track the scratch targets: Funnel `+0.78` (target `+.86`), Pit `−0.90` (`−.92`),
Cannon `−0.77` (`−.86`), Source `+0.91` (`+.92`) — the small offsets are the
competing `−iε[H,ρ]` term tilting the pole, which is physical
(`axis0_sourcelock_diagnosis.json`).

**Axis-0 is orthogonal to every single-trajectory functional (the real reason it
stalls).** With source-locked terrains, five principled Axis-0 readouts were
tested against the target split `Ne/Ni` (active/+) vs `Se/Si` (conservative/−):

| Functional | Result grouping | Which axis it tracks |
|---|---|---|
| entropy production `ΔS` | `{Se,Ni}−`, `{Ne,Si}+` | **Axis-1** (dissipative/unitary) |
| response derivative `dD/dλ` | `{Se,Ni}` high, `{Ne,Si}` low | **Axis-1** |
| trajectory activity (arc length) | `Ne,Ni,Se +`, `Si −` (3/4) | mixed |
| future-option multiplicity | `{Se,Ni}` many, `{Ne,Si}` few | **Axis-1** |
| participation ratio (§7b.3) | all `+` | none |

**None realizes `Ne/Ni | Se/Si`.** The diagnosis is structural, not a tuning
failure: the three DOF partitions of the four topologies are **mutually
orthogonal** —

- **Axis-0 (perceiving):** active `{Ne,Ni}` | conservative `{Se,Si}`
- **Axis-1 (dynamics):** dissipative `{Se,Ni}` | unitary `{Ne,Si}`
- **Axis-2 (frame):** direct `{Se,Ne}` | conjugated `{Ni,Si}`

Any single-trajectory *scalar* (entropy, response, activity, branch count) tracks
the **dynamical** contrast (Axis-1), which cuts *across* Axis-0 — so it necessarily
collapses `Ne/Ni` vs `Se/Si`. This is exactly why models "get stuck validating
Axis-0." The teeth map (`axis0-physics-source-teeth-map.md`) already says so: Axis-0
is a **late object** on the full spine `Ω_r/JK → branch-kill → C_G → Ξ → ρ_AB →
Φ0`, *not* a terrain-local readout. Realizing it requires building that spine (the
ring-checkerboard / many-futures layer), not a better one-shot functional.

> **Claim ceiling.** `scratch_diagnostic`, `promotion_allowed=false`. Earned:
> source-locked GKSL content for all 8 terrains (fixed points matched to scratch
> maps); a first-principles proof that Axis-0's grouping is orthogonal to the
> dynamical functionals (5 tested), corroborating the doctrine that Axis-0 is a
> late spine object. **Not** earned: a working Axis-0 readout (still open, now for
> a *principled* reason — it needs the Ω_r/JK spine, not terrain-local dynamics).

---

## 7j. Exploration — the JK-fuzz field and a candidate Axis-0 resolution

*(This section is deliberately exploratory — candidate-grade, feeding the ratchet
rather than gated by it. The owner's process earns canon; this is raw material.)*

The Axis-0 seat, per doctrine (`jk-fuzz-field.md`, `axis0-physics-source-teeth-map.md`),
is the **JK fuzz field** — a finite field of admissible future continuations:

```
probe-state → nested layer → fuzz field F_jk(l,x) → Ξ_fuzz cut ρ_AB → Φ_0 readout
```

**Finite-path-integral substrate (reproduced).** The finite Feynman path packet
(`finite-feynman-path-integral-foundation-packet`) was reproduced: 8 admissible
length-4 words over `{A,B}` forbidding `BB`; `‖AB−BA‖ = √2`; unconstrained
`(A+B)⁴` amplitude matches the doc to 14 digits; the constraint is load-bearing
(dropping it changes the path sum). This is a working finite, ordered,
noncommuting, constraint-gated substrate for `F_jk`.

**A candidate Axis-0 resolution (falsifiable).** Eight principled Axis-0 readouts
have now been tested (§7b.3, §7i, plus JK-fuzz bipartite mutual information and
distinguishability-flow here); **none realizes the Axis-0 split**, and of those,
**four track Axis-1 directly** (dissipative/unitary `{Se,Ni}|{Ne,Si}` — entropy
production, response `dD/dλ`, future multiplicity, JK-fuzz bipartite MI) while the
rest are simply blind or partial (participation ratio: no split; von Neumann:
isolates `Ni`; trajectory activity: 3/4). This forced a sharper look, which surfaced
a **contradiction**
in the current definition:

> The owner calls **Ni "positive entropy,"** but Ni (Pit/Source) converges to a
> **pure** state — the **lowest** *state* entropy (`S* ≈ 0.12`). So the "entropy" in
> the Axis-0 polarity **cannot be state entropy**.

The candidate fix: Axis-0 is the Jungian **intuition vs sensing** axis — `Ne,Ni`
(intuition) perceive **many admissible futures**; `Se,Si` (sensing) perceive **one
actual present**. "Positive entropy" then means **fuzz-field entropy** — entropy
over the admissible-future distribution `F_jk`, *not* `S(ρ)`:

$$ \text{Axis-0 polarity} = \operatorname{sign}\frac{d}{d\lambda}\,H_{\text{fuzz}}(\text{future dist})
   \quad\text{not}\quad \operatorname{sign}\frac{d}{d\lambda}\,S(\rho). $$

Supporting signal: **distinguishability-flow** (a fuzz proxy — how a cloud of
nearby states' pairwise distinguishability evolves) is the **only** readout whose
family means order correctly: intuition `0.731` > sensing `0.706` (though `Se`
overlaps `Ni` per-terrain, so it is a lead, not a closure). This is consistent with
the doctrine that Axis-0 is a **late spine object** requiring the `Ω_r/JK`
many-futures layer — the ring-checkerboard support — not a terrain-local scalar.

**Suggested next rung.** Build `F_jk` as a first-class finite distribution over
admissible continuations on a ring-checkerboard support, assemble `Ξ_fuzz → ρ_AB`,
and test `Φ_0 = sign(d H_fuzz/dλ)`. And, project-wide: **name STATE entropy and
FUZZ entropy as distinct quantities everywhere** — that single rename resolves the
Ni contradiction and should de-drift the Axis-0 doc cluster.

---

## 7k. Exploration — why fuzz collapses to channel rank, and Axis-0 as a loop property

*(Exploratory continuation of §7j — candidate-grade, feeding the ratchet.)*

I built the JK-fuzz field as a first-class object on the **ring-checkerboard
support** (`ring-checkerboard-...-runbook`, spherical-checkerboard presentation:
nested shells with inside/outside inversion and a radial gradient — the presentation
the runbook names as most visible for Axis-0). A terrain's admissible future
continuations are its **Kraus branches**; `F_jk` is the distribution over them;
`H_fuzz` is the entropy of that future distribution (§7j's candidate).

**Result — and the obstruction it exposed.** The fuzz tree-entropy (depth-3
ring-checkerboard walk) gives `{Ne,Si}` high vs `{Se,Ni}` low — **Axis-1 again**.
The reason is structural and worth stating as a model fact:

> The fuzz tree-entropy tracks the **dissipative/unitary balance** (Axis-1):
> unitary-dominant terrains (`Ne, Si`) preserve distinguishable leaves, while
> dissipative terrains (`Se, Ni`) collapse them. The **Kraus branch count** (=
> dissipator rank + `K₀`: `Ne=4, Se=3, Ni=2, Si=2`) feeds the branching but does
> *not* strictly order the entropy — `Si` (rank 2) exceeds `Se` (rank 3) because
> `Si` barely dissipates. Both drivers — branching *and* collapse — are **dynamics
> (Axis-1)** properties. So *any* fuzz measure built from Kraus branches **inherits
> Axis-1**. This is why all future-multiplicity readouts collapse.

**Refined hypothesis (the real lesson).** Axis-0 "tense" — orientation toward
future-possibility (intuition) vs present-actuality (sensing) — is **not** about how
many futures a channel spawns. It is a property of the **composed engine loop**
(deductive `UEUE` vs inductive `EUEU`, Axis-4), not of a single terrain. *A terrain
in isolation has no tense.* Testing at the loop level (full deductive/inductive loop,
distinguishability-preservation readout) gives the **best result across all 11
readouts tested**: `Ne+, Se−, Si−` correct (3/4); only `Ni` sits on the wrong side,
and it does so for a understood reason — `Ni` is the source-locked **pure attractor**
(Pit/Source → pole), which closes distinguishability regardless of tense.

**Full readout ladder (11 tested, none terrain-local realizes `{Ne,Ni}|{Se,Si}`):**
entropy production, response `dD/dλ`, trajectory activity, future multiplicity,
participation ratio, von Neumann, JK-fuzz bipartite MI, distinguishability flow,
`dH_fuzz/dλ`, fuzz tree entropy → all Axis-1 or blind; **engine-loop tense → 3/4,
best.**

This is strong first-principles support for the owner's doctrine that **Axis-0 is a
late object, downstream of loop/engine structure** — not a terrain-local readout.

**Concrete next rung.** Test Axis-0 at the full **720° = 2×360° double-loop** level
(outer/inner deductive-inductive swap), handling `Ni` as the pure-attractor special
case; or build `Φ_0` as a genuinely **downstream** `ρ_AB → Φ_0` readout taken
*after* the loop, not from terrain-local channels. And project-wide: the finding that
**fuzz multiplicity = channel rank = Axis-1** should be recorded so future work does
not keep re-deriving Axis-1 while aiming at Axis-0.

---

## 7l. Exploration — the 720° loop at spinor level (why density-level readouts were doomed)

*(Exploratory continuation — candidate-grade. This one changes the strategy.)*

The engine-loop result (§7k) said Axis-0 is a loop property. Reading the loop docs
surfaced the **tribunal's sharpest constraint** (`igt-pattern-explicit-math-reference.md`,
the Codex2 challenge):

> "720° behavior disappears under `ρ = |ψ⟩⟨ψ|` unless the engine keeps lifted
> phase/path/interference data. The engine MUST work at the **spinor level**, not
> just the density level, or the 720° structure is invisible."

This is decisive for the whole Axis-0 investigation: **all 11 readouts in §7b.3, §7i,
§7j, §7k were computed at the density (`ρ`) level** — where the 720°/tense structure
is *provably invisible*. That is very likely **why every one of them collapsed to
Axis-1**: they were measuring a projection that had already discarded the degree of
freedom Axis-0 lives in.

**Verified at spinor level.** Working with amplitudes `|ψ⟩ ∈ ℂ²` (not `ρ`):
- The SU(2) double cover is exact: a 360° loop gives `⟨ψ₀|U|ψ₀⟩ = −1.0000`, a 720°
  loop gives `+1.0000` — the sign structure `ρ` erases.
- **Measurement in the loop destroys the lifted phase** — the tense signature. The
  720° phase-return magnitude decays with measurement strength: `1.000 → 0.996 →
  0.975 → 0.860` at strengths `0.0, 0.3, 0.6, 0.9`. Strong measurement (sensing)
  collapses the interference; weak/none (intuition) preserves it.

**What this establishes and what it doesn't.** Established: Axis-0 tense is a
**spinor-level, loop-level, measurement-sensitive** property — not density-level, not
terrain-local. This matches the tribunal constraint *and* the teeth-map "late object"
doctrine exactly. **Not** yet closed: a clean per-terrain `Ne/Ni+ | Se/Si−`
realization — the crude spinor-level `E`-operators used here (measurement models per
terrain) muddy the split (`Ne` unitary is clean at 1.000; `Si` renormalization
overshoots). The honest next rung is **principled spinor-level `E`-operators** — a
proper weak-measurement model matched to each terrain's native judging operator — run
around the full 720° = 2×360° double loop with the outer/inner deductive-inductive
swap, `Ni` treated as the source-locked pure-attractor special case.

> **Strategic takeaway.** The Axis-0 sims should be **re-based at the spinor level**.
> The density-level tooling (all of §7b–§7k) is correct for Axes 1–6 but structurally
> blind to Axis-0. This is the single most useful redirection this investigation
> produced, and it was the tribunal's own prescription all along.

---

## 7m. The Axis-0 stall resolved: Axis-0 = Axis-1 XOR Axis-2

*(This is the strongest result of the Axis-0 investigation. Candidate-grade, but exact
and doc-grounded.)*

The spinor-level rung (§7l) said Axis-0 is not density-local. Pursuing it further —
principled spinor weak-measurement operators, the full 720° double loop, and the
repo's own strongest bridge kernel (coherent information `I_c(A⟩B)` on a nested
shell-cut) — **none realized the `{Ne,Ni}|{Se,Si}` split**. That makes **14** distinct
Axis-0 readouts tested, all failed. The reason is now exact.

**The structural fact.** Read against the repo's operator table
(`igt-pattern-explicit-math-reference.md` lines 475–478) the three axis partitions are:

| Axis | split | `Se` | `Ne` | `Ni` | `Si` |
|------|-------|------|------|------|------|
| **Axis-1** (dynamics) | dissipative `{Se,Ni}` \| unitary `{Ne,Si}` | 0 | 1 | 0 | 1 |
| **Axis-2** (frame)    | direct `{Se,Ne}` \| conjugated `{Ni,Si}`   | 0 | 0 | 1 | 1 |
| **Axis-0** (perceiving) | N/intuition `{Ne,Ni}` \| S/sensing `{Se,Si}` | 0 | 1 | 1 | 0 |

Reading the last row as the XOR of the first two is **exact for all four families**:

> **Axis-0 = Axis-1 ⊕ Axis-2.** `{Ne,Ni}` (intuition/N) are exactly the terrains where
> the dynamical axis and the frame axis **disagree** (Ne = unitary+direct, Ni =
> dissipative+conjugated); `{Se,Si}` (sensing/S) are where they **agree**.

**Why this resolves the stall.** XOR is the textbook **not-linearly-separable**
function. Any single scalar functional measures one (approximately linear) direction in
the terrain space, so it can realize Axis-1 or Axis-2 — never their parity. Every one
of the 14 readouts therefore *had* to collapse onto Axis-1 (or occasionally Axis-2);
the target was provably unreachable by construction. This is not a tooling failure — it
is a theorem about what a single readout can see. (The identity is deterministic algebra
on the axis labels; it needs no statistical corroboration. A multivariate
leave-one-family-out fit was run but is **statistically vacuous** — 3 training points
against 4 features is underdetermined, so a perfect score is guaranteed and carries no
evidential weight; it is not cited as support.)

**Why this matches the doctrine.** The repo already says Axis-0 "cannot be evaluated on
a single isolated spinor; it needs a **bipartite cut-state `ρ_AB`**" via the Ξ bridge,
and calls it "the single biggest open problem." A bipartite construction is precisely a
**two-subsystem** (hence two-axis) object — exactly what computing a parity requires.
The discrete Axis-0 projection `{Ne,Ni}→N, {Se,Si}→S` is then the **ground-truth target
the Ξ bridge must reduce to**, not a functional to be guessed.

**Falsifiable, constructive next step.** Build Ξ as a genuine 2-subsystem readout whose
sign equals `sign(Axis-1) ⊕ sign(Axis-2)` — e.g. a history-window pullback (time-averaged
`I_c` over a full 720° trajectory) that couples the dynamical and frame characters
multiplicatively rather than additively. The XOR statement is the precise structural
form of "Axis-0 is visible only jointly in Axis-1 and Axis-2, never from either alone."

> **Model recommendation.** Record `Axis-0 = Axis-1 ⊕ Axis-2` in the axis doctrine, and
> stop searching for Axis-0 in single-cut dynamics. The bridge should be *engineered to
> compute the parity*, with the discrete N/S lattice as its correctness target.

---

## 7n. Why the parity is unreachable by entropy: the two-sector theorem

*(Deepening §7m. The gauge proof and sector theorem are solid; the bridge's phase
readout is isolated as the open piece.)*

§7m established `Axis-0 = Axis-1 ⊕ Axis-2` as an identity on the axis labels. This
section asks the constructive question — can a genuine bipartite `ρ_AB` object *compute*
that parity — and in failing to force it, proves exactly why the whole investigation
stalled.

**1. Axis-2 (frame) is a gauge choice — a symbolic identity (grade: `symbolic_identity`).**
The direct/conjugated frame is `ρ ↦ V†ρV`, a **unitary similarity**. Every state invariant
— von Neumann entropy, purity, coherent information, mutual information — is a function of
the **eigenvalues** of `ρ` alone, and unitary similarity preserves the spectrum **exactly**:
`spec(V†ρV) = spec(ρ)` for *any* unitary `V`, by definition of similarity. So the invariance
is an algebraic identity, not a numerical result — the empirical `2×10⁻¹⁵` over 200 random
states (below) is a *confirmation* of the identity, not its basis. The frame carries *no*
information any state functional can read: half of Axis-0's content is provably **not in the
state**, as a theorem.

**2. The two axes are different kinds of charge, in orthogonal sectors.** Decompose a
density matrix into its **eigenvalues** (the entropy sector) and its **eigenvectors**
(the phase sector). Under frame conjugation the eigenvalues move by `1.8×10⁻¹⁶` while the
state itself moves by `0.67`: the frame lives **entirely in the eigenvector sector**.

> **Two-sector theorem.** Axis-1 is an **entropy charge** (eigenvalue sector — read by
> `S`, `I_c`, `MI`, purity). Axis-2 is a **phase/gauge charge** (eigenvector sector —
> invisible to every entropy functional). `Axis-0 = Axis-1 ⊕ Axis-2` therefore requires
> **one entropy readout and one phase readout, multiplied**. No single scalar functional
> spans both sectors — which is the precise, sector-level reason **all 14** tested
> readouts (every one an entropy-type functional) could never see Axis-0.

**3. Why the frame needs a second system.** The frame becomes physical only through the
dissipation basis: frame-sensitivity is `0.22` for the dissipative terrains `{Se,Ni}` and
**exactly 0** for the unitary terrains `{Ne,Si}` (whose dynamics commute with `H₀`).
Reading a *basis* requires a reference to read it against — which is precisely **why the
repo insists Axis-0 needs a bipartite cut-state `ρ_AB`**: register B supplies the
reference frame for register A's basis.

**4. Bridge status — entropy sector solved; phase sector instrumented but a2 lives at the
operator layer.** The Ξ bridge is a **two-output, two-sector map**: `χ₁` = entropy charge
(eigenvalue sector, purity sign — **works**), `χ₂` = phase charge (eigenvector sector), with
`Axis-0 = χ₁·χ₂`. The `χ₂` story resolved in two steps. First (§7v) an **open-path**
Bargmann/Pancharatnam phase was built and shown to be a genuine **eigenvector-sector meter**:
nonzero on an open segment while a *closed* loop is gauge-invariant (`H₀` and `V†H₀V` share a
spectrum) and therefore blind. *(An earlier prototype that scored 4/4 by assigning `χ₂` from
the known frame bit was circular and is discarded.)* Then (§7v fourth-audit flag, §7w) it was
shown that `χ₂` is **not a2-specific** — it responds to all three binary operations on the
frame element (a2: V-vs-I; ε: V-vs-V†; K: V-vs-V\*), and its terrain-generator readout tracks
the a1 dynamics bit, not a2. The direct/conjugated (a2) bit is earned **exactly, but at the
operator layer** (§7t, W-covariance); it provably does not descend to a terrain-generator
observable (§7w). So the parity `Axis-0 = a1 ⊕ a2` reads end-to-end at the **operator layer**;
at the terrain layer it is carried, not measured.

> **Model recommendation.** Axis-0's bridge is not a functional to be discovered but a
> **two-sector instrument to be built**: an entropy meter (have it) and a relational phase
> meter (open). Both closed-loop holonomy and all entropy functionals are provably
> insufficient for the second. This is the sharpest statement yet of what the Ξ bridge
> must be.

---

## 8. Audit — with claim-grade discipline

**Claim-grade rule (from the current wiki per-rung standard).** Claim-bearing
rows must use a promotable proof route — `symbolic_identity`,
`closed_form_integral`, `exact_integer_combinatorial`,
`representation_theorem_with_constructive_receipt`, or
`finite_exhaustive_enumeration`. The following are **forbidden** for
claim-bearing rows and count only as `diagnostic_float_nonclaim`:
`bare_float_tolerance`, `max_deviation_only`, `abs_error_only`, `validator-green
only`. All rows below therefore carry an explicit grade, and the whole spec
holds at ceiling **`scratch_diagnostic`, `promotion_allowed = false`** — nothing
here admits final `M(C)`, the QIT engine, physics, or geometry-complete claims.

**Promotable rows** (`sympy` symbolic / closed-form; `constraint_core_symbolic.py`):

| # | Claim | Grade | Result |
|---|-------|-------|--------|
| T01 | matrix associator `(AB)C − A(BC) = 0` at 1Q, 2Q | `symbolic_identity` | **holds** (identically zero over symbolic ℂ entries) |
| N01 | witnesses O1 (commute), O2 (noncommute), O3 (nc & not-ac: `A=X,B=X+Z`), O4 (anticommute `X,Z`) | `exact` (Pauli) | **all hold** |
| spine | max pairwise-anticommuting family `= 2n+1`; splits `2^{n-1}+2^{n-1}` | `representation_theorem` | **holds** (`Clₘ` min-dim bound) |
| flux | Hopf curvature `∫F = −4π` | `closed_form_integral` | **holds** (exact `−4π`) |
| σ± | `σ_± = ½(σ_x ± i σ_y)` | `symbolic_identity` | **holds** |
| b₆ | derived axis law `b₆ = −b₀·b₃` | `exact_integer` / `finite_exhaustive` | **holds** (0/8) |
| flux-nest | flat carrier `A=0` (real pipeline) → holonomy ≡ 0, flux ≡ 0 | `ablation` (same-pipeline) | **holds** (closes audit hardening #1) |
| flux-nest | single shell → holonomy `−4.4429` but flux undefined; needs ≥2 nested shells | `transport` vs `closed_form` | **holds** (agree to 6 digits) |
| ratchet | pairwise flux order-sensitive; total `|Φ(0,2)|=7.295` order-indifferent | `closed_form` | **holds** (geometric ratchet) |
| assoc | associator: `H=0`, `O=2.0` (witness `[1,2,4]`), `S=2.0` | `exact` / `finite_exhaustive` | **holds** (non-assoc at 𝕆, T01) |
| carrier | octonion `L_{e1..e6}` → Cl(0,6), rank 64 → ℂ⁸ = 3 qubits; `dim Der(𝕆)=14=dim G₂` | `exact` (Clifford + rank) | **holds** (3-qubit floor) |
| fep | pure-QIT `F=S(ρ_q‖ρ_model)≥0`; DPI monotone under belief-update; path-order N01 | `rel_entropy` / `DPI` | **holds** (support only; ⇏ Axis0/Φ0) |
| ops | Ti/Te CPTP+unital dephasing; Fi/Fe unitary purity-preserving | `Choi_PSD` / `exact` | **holds** (4 operators match spec) |
| sched | 64-microstep schedule: order-blind → 11/64 (collapse); N01 order-sensitive → 64/64 | `finite_enum` + order-observable | **holds** (unique processing needs N01) |
| ratchet-prec | L4 holonomy `−4.442882938` vs `−2π cos2η`, residual ≈3e-10 | `closed_form` | **holds** (deepest layer locked) |
| basins | 8 terrain basins distinct (rich fingerprint); kill test splits Ne/Ni=attractor, Se/Si=viability | `limit_set` + `kill_test` | **holds** (coincides w/ Axis-0 polarity) |
| subbasins | operators refine basins (Pit sep 0.445, Hill 0.005); commuting control kills order gap (2e-17) | `sep` + `commuting_kill` | **holds** (N01-driven, not artifact) |
| src-lock | 8 terrains GKSL from scratch fixed points (Funnel +.78/tgt+.86, Pit −.90/−.92, Source +.91/+.92) | `fixed_point_match` | **holds** (Se/Ne/Si no longer agent-chosen) |
| axis0-orth | 5 Axis-0 functionals all track {Se,Ni}\|{Ne,Si} (Axis-1), none realizes {Ne,Ni}\|{Se,Si} | `partition_orthogonality` | **holds** (Axis-0 is a late spine object, not terrain-local) |

**Diagnostic-float rows** (`numpy`/`scipy`; `constraint_core_audit.py`) —
`diagnostic_float_nonclaim`, i.e. supporting evidence only, **not** promotable as
stated. Each has a named exact route for later promotion:

| # | Claim | Float result | Exact route to promote |
|---|-------|--------------|------------------------|
| C2 | Bloch coords from chart | `r_x,r_z` match; **`r_y = −sin2η sin2χ`** (convention, §4.3) | symbolic `π(ψ)` identity |
| C2 | density `ρ = ½(I+r⃗·σ⃗)` | ≤ 2e-16 | symbolic identity |
| C2 | fiber-blindness | ≤ 1e-15 | symbolic invariance under `φ` |
| C3 | Weyl laws `ṙ⃗ = ±2n⃗×r⃗` | ≤ 2e-16 | symbolic superoperator identity |
| C4 | 8 generators CPTP | min Choi eig > 0 (sampled `t`) | GKSL theorem receipt (canonical form) |
| C6 | Pit/Source fixed points | `r_z → ∓1.0000` | symbolic steady-state of `D[σ_∓]` |
| C7 | entropy peak at `η=π/4` | `S=ln2` at `η≈0.787` | closed-form `argmax` of `S(η)` |

**Summary.** The F01/N01/T01 spine and the Hopf flux are at promotable grade
(symbolic/closed-form). The §4–§7 realization laws are at
`diagnostic_float_nonclaim` — internally consistent and evidenced, but each must
be re-run through its named exact route before any promotion, and all remain
under the `scratch_diagnostic` ceiling. The one substantive discrepancy in the
source corpus was the `r_y` orientation convention, resolved in §4.3.

---

## 8b. Computational substrate as a charter constraint

The allowable-mathematics charter (§2) is not only about which *mathematics* is
admissible — it silently constrains which **computational substrate** may
express the kernel, because a numerical library ships its own implicit
foundations. A substrate is charter-aligned to the degree that it does *not*
smuggle in the structures §2.1 forbids.

### 8b.1 What the charter demands of a substrate

| Charter clause | Substrate requirement |
|----------------|----------------------|
| C1 Finitude | No treatment of completed reals as ontological. Exact rationals, arbitrary precision, or interval/tolerance arithmetic preferred over bare IEEE doubles as *primitives*. |
| C2 Non-commutation | Composition is first-class and order-explicit; no hidden commutative broadcasting default. |
| C3 Emergent identity | No primitive `==` on values as the identity notion; equivalence is *probe-relative* (tolerance / indistinguishability under a finite-resolution test). |
| §2.2 morphisms-first | Behavior attaches to transformations/composition; objects emerge as invariants — not an object-with-methods (OO) model with primitive object identity. |
| purity | No hidden global mutable state (a mutated buffer is a smuggled primitive-identity object persisting across "probes"). |

### 8b.2 Alignment of the four substrates

| Substrate | C1 finitude | C2 / composition | C3 / identity | morphisms-first | Verdict |
|-----------|-------------|------------------|---------------|-----------------|---------|
| **Julia** | strong — native `Rational`, `BigFloat`, interval arithmetic; `≈` as default comparison | strong | good — `≈` and parametric types over primitive `==` | **strong** — multiple dispatch *is* morphism-first; objects emerge from type combinations | **closest to the kernel foundation** |
| **JAX** | partial — still IEEE floats, but tolerance-based comparison idiomatic | strong — `jit`/`vmap`/`grad` are composition transformations | partial | good — pure functional, explicit PRNG keys, no in-place mutation | **best functional substrate** for dynamics/transforms |
| **NumPy** | weak — IEEE doubles stand in for reals; broadcasting = free basis-full vector space | weak — commutative broadcasting is the default | weak — primitive `==` | weak — array-of-values, object-centric | **oracle only** (finite operator checks), never the kernel |
| **PyTorch** | partial | good autodiff | weak — mutable tensors import object identity | weak — OO/mutable model | autodiff strength; least aligned of the three you use |

### 8b.3 Important nuance about the §8 audit

The §8 audit was written in NumPy/SciPy, but its **methodology is
charter-compliant even though its substrate is not**: every check is
tolerance-based, never `==`. `‖r_meas − r_pred‖ < tol`, `min Choi eigenvalue >
−tol`, and "indistinguishable outcomes under a finite-resolution probe" are
literally C3 (`a = a iff a ∼ b under all admissible probes`) with the machine
tolerance playing the role of the finite probe budget (C1). So NumPy is
acceptable as an **external oracle** for finite operator claims, but not as the
substrate that *expresses* the constraint kernel — for that, Julia (for exact/
dispatch-native kernel structure) and JAX (for pure functional dynamics) are the
aligned choices. This matches the observed practice of building the aligned
simulation in Julia and using JAX's modified-NumPy semantics rather than stock
NumPy.

### 8b.4 Recommended division of labor

- **Julia** — the constraint kernel itself: refinement category (§3), exact
  axis-bit algebra (§6.3), and any construction where C1 exactness matters.
- **JAX** — the dynamics layer: `Φ_τ^s(t) = exp(t·X_τ^s)` semigroups, Bloch-law
  integration (§5), `vmap` over the 16 placements (§7).
- **NumPy/SciPy** — external oracle only (§8), for cross-checking finite operator
  claims to machine tolerance.

---

## 9. Declared unknowns (held explicitly open)

Per the meta-rule (§2.4), these may **not** appear implicitly anywhere else in
the system as premises.

| ID | Open question | Rule |
|----|---------------|------|
| U-0 | Does geometry emerge before, after, or with Axis-0? | No argument may assume geometry-first or axis-first without derivation. |
| U-1 | Is nested Hopf/S³ the unique minimal compatible manifold, or one attractor among several? | Treat Hopf/S³ as a **candidate**, not canon. |
| U-2 | Is the ordering ("i-scalar") strictly monotone, piecewise, cyclic, or multivalued? | "Clock" permitted only as *ordering*, never as time. |
| U-3 | Are there exactly 7 irreducible axes? | No axis count is final until derived. |
| U-4 | Are there exactly two stable engine types? | Engine enumeration must be empirical (ratchet + sims). |
| U-5 | Do the four terrain classes map to physical sectors (dark energy/matter, baryonic, hadronic)? | **Speculative.** No physics claim may feed back into kernel math. |
| U-6 | Does emergent identity converge to classical identity at scale? | Never assume a classical-identity limit unless derived. |
| U-7 | Is the allowable-math set closed under limits/completion? | Completions must be explicitly justified, never assumed. |
| U-8 | Is probability emergent bookkeeping, unavoidable approximation, or eliminable? | Probability is descriptive, not ontological. |

---

## 7o. The gauge degeneracy: why the parity is a late object, and its link to the co-ratchet

*(Continuation of §7n, building the open piece. Stated in pure structural indices per §9a.
**Corrected 2026-07-01** after an external audit — see the correction note at the end of
this section. The exact δ=0 gauge degeneracy survives; the "linear law" claim was withdrawn.)*

§7n isolated the open piece as a **relational, open-path phase observable** for `χ₂` — a
system `A` entangled with a reference `B` the gauge does not rotate. Building it produced
a sharp structural fact and a clean scaling law.

**The relational readout works — and exposes a gauge degeneracy.** With `A` maximally
entangled with a fixed reference `B`, the frame bit `a2` shifts the `A`–`B` relational
coherence `⟨00|ρ_AB|11⟩` — *for dephasing objects* (`a1=0`): coherence `0.075` vs `0.28`.
But **for unitary objects** (`a1=1`) it is invisible, for an exact reason:

> The frame conjugation `V = exp(−iH₀s)` **commutes** with unitary dynamics about the
> same axis: `‖[V, e^{−iH₀t}]‖ = 2.6×10⁻¹⁶`. So the two unitary objects `(a1=1,a2=0)` and
> `(a1=1,a2=1)` are the **identical channel** (difference `3×10⁻¹⁶`). The parity
> `p = a1 ⊕ a2` therefore **cannot be a single-channel observable** among the unitary
> objects — two physically identical channels carry different `p`.

**Symmetry-breaking dissipation makes the frame bit physical (no linear law).** Real terrain
generators are not purely unitary — they carry subdominant dissipation. Adding a dissipation
of strength `δ` to a unitary-dominant object breaks the gauge degeneracy and the frame bit
becomes physical, growing monotonically from exactly zero at `δ = 0`:

> **The frame bit's physicality is zero at `δ = 0` (split `6×10⁻¹⁷`, pure gauge) and
> increases monotonically with `δ`.** The dependence is an ordinary saturating first-order
> response — under a genuine GKSL dephasing semigroup (dephasing generator `L=σz⊗I` on
> subsystem A, integrated over fixed evolution time `T=1` with the unitary phase at `t=0.7`;
> these conventions are pinned in `axis0_gauge_breaking_sim.py` v3) the ratio `split/δ` falls
> from `0.15` (at `δ=0.05`) to `0.039` (at `δ=2.0`), *not* a constant. (A different `T`/rate
> convention gives different constants — an independent run reported `0.30→0.06` — but the
> same qualitative saturating decay; the point is the ratio is *not* constant, unlike the
> withdrawn single-Kraus model.) There is **no linear law**: a
> previous version of this section reported `a2-physicality = k·δ` with `R² = 0.999997`, but
> that came from modelling the dissipation as a single Kraus step `K₀=√(1−δ/2)I,
> K₁=√(δ/2)Z`, which is affine in `δ` **by construction** (`split/δ` constant to `5×10⁻¹⁷`
> all the way to `δ=2`). The `R²=1` was an algebraic identity of the parametrization, not a
> discovered law — withdrawn.

**Why this matters — the co-ratchet link.** This explains, structurally, *why Axis-0 is a
late object*: the parity is unreadable until the **entropy sector is switched on**. The
gauge charge only becomes a physical observable once symmetry-breaking dissipation lifts
the unitary degeneracy — which is precisely the **co-ratchet** claim of §7c that entropy
and operators must be *earned* before the higher structure can be read. The perceiving
axis is not merely downstream of the dynamics and frame axes (§7m); it is downstream of
the entropy sector *becoming active*. Axis-0's readability is proportional to how much the
co-ratchet has advanced.

> **Model recommendation.** Record the two claims that survive: (i) the **exact gauge
> degeneracy at `δ=0`** — the two unitary objects are provably the identical channel, so the
> parity is not a single-channel observable there; and (ii) the **qualitative co-ratchet
> link** — the frame bit becomes readable only once dissipation (the entropy sector) is
> switched on, monotone in `δ`. This still makes "Axis-0 is a late object" a structural
> statement: the parity's readability is gated by the earned entropy. Do **not** record any
> linear/`R²=1` law — that was a parametrization artifact.

> **Correction note (2026-07-01).** An external audit of the bundle flagged this section. The
> single-Kraus dissipation model made `split/δ` constant by construction (`R²=1` an algebraic
> identity). Rebuilt with a genuine GKSL semigroup, the linear law vanishes (`split/δ` falls
> `0.15→0.039`) while the δ=0 degeneracy and the qualitative co-ratchet link are unchanged.
> This is the impressive-label-before-earning pattern the §9a discipline warns against,
> caught inside the bundle — logged as a ratchet kill-test rather than hidden. Verified in
> `axis0_gauge_breaking_sim.py` (v3) and the audit-response figure.

---

## 7p. Maximal differentiation of the eight terrains

*(Strong per-terrain sim on the manifold. Structural indices only per §9a; the fingerprint
and the near-degeneracy finding are solid.)*

Each of the eight terrains is realized as its **exact source-locked GKSL generator**
(from the scratch Bloch maps, `igt-pattern` lines 486–497), indexed `t0…t7` with no
labels in the math. The goal is **maximal differentiation** — every terrain provably doing
distinct information processing, separated as far as possible.

**A single fixed point is not enough.** From a maximally-mixed start, the four dissipative
terrains pin to their exact `z*` poles (`t0→+0.78`, `t2→−0.91`, `t4→−0.78`, `t6→+0.91`,
tracking the `±.86/±.92` targets), but the four unitary-dominant terrains all collapse to
the centre `r=0` — degenerate. Differentiation requires a **rich dynamical fingerprint**,
not the endpoint.

**The 14-feature fingerprint.** Per terrain: fixed-point Bloch vector (3) + radius +
fixed-point entropy + Liouvillian decay rates (2) + oscillation magnitude + total
dissipativity + signed drift + trajectory arc length + **signed chirality** + **trajectory
handedness** + **signed swept area** (an `eps`-odd geometric-phase proxy). The last three are
the load-bearing additions: scalar invariants alone cannot see the sheet sign `eps`, which
for the unitary terrains is a pure chirality (mirror trajectories with identical spectra).

**Result — all eight distinct, with one honest near-degeneracy.** Under the standardized
fingerprint, pairwise distances have **mean 5.5, max 6.9, min 0.35**. The degeneracies fall
in a clear order: fixed point separates 6; the Liouvillian spectrum splits decay vs
oscillation; signed chirality breaks `t1≠t5`; handedness and swept area break `t3↔t7` (from
0.28 to 0.35). The bottleneck pair `t3–t7` (the two **projective** terrains) is a **genuine
structural fact, not a sim artifact**: their generator is nearly **sheet-symmetric** (weak
Hamiltonian content), so only `eps`-odd geometric features distinguish them at all. Every
other pair is `3–7` apart — well separated.

> **Model recommendation.** The eight terrains are maximally differentiated by a 14-feature
> dynamical fingerprint, and the *residual* structure is itself informative: the projective
> terrains are the least chirally-distinct, marking them as the manifold's most
> sheet-symmetric point. When the full engines (Julia/JAX/PyTorch) are run, this fingerprint
> is the natural per-terrain validation target — each engine stage should reproduce its
> terrain's fingerprint row.

---

## 7q. Operator–geometry fusion: the surface is the operator

*(Co-ratchet at the operator level. Honest mixed result: the fusion claim is confirmed
exactly for half the terrains and sharpened, not forced, for the other half.)*

At this level of the co-ratchet the terrains **max-constrain** the operators: each terrain
admits exactly **2** native operators, in a signed Axis-6 order — and, per the owner, the
operator is not a map acting *on* the terrain surface; the **surface itself is the
operator** (the GR analogy: spacetime *is* the gravitational field, not a background it
acts on). This section tests that fusion literally.

**The native-operator law (a rosetta labelling).** From the operator table (`igt-pattern`
470–478): direct terrains `{Se,Ne}` admit **Ti** (z-dephasing) + **Fi** (x-rotation);
conjugated terrains `{Ni,Si}` admit **Te** (x-dephasing) + **Fe** (z-rotation). This is
which two operators are *admitted*, signed by Axis-6.

**Four lab-frame metrics fail to prefer the native pair — an honest null.** Superoperator
HS-overlap (2/8), supercommutator (4/8), Axis-6 order-gap (2/8), and operator-algebra
containment (2/8) all decline to single out each terrain's two documented native operators.
Every metric is dominated by the terrain's shared **fixed-axis geometry** rather than the
operator's role. **This null is genuinely ambiguous** and must not be read as evidence *for*
fusion: it is equally consistent with "the operator is the geometry, so no lab-frame metric
can separate them" (the owner's claim) and with "the native-operator pairing is arbitrary at
the terrain level" (the deflationary reading). A null result cannot adjudicate between those
two — reporting it as confirmation of fusion (as an earlier version of this section did)
inverts a null into evidence. The fusion claim is instead settled by the *containment
residual split* below, and — decisively — by the exact W-covariance derivation of §7t.

**The sharp, honest split.** Projecting each terrain's Liouvillian onto the full
4-operator algebra gives a residual that splits cleanly by family:

| terrain family | residual outside operator algebra | reading |
|----------------|-----------------------------------|---------|
| projective (`t3,t7`) | **0.000** | surface **is** its operator algebra (pure dephasing/rotation) |
| depolarizing (`t1,t5`) | **0.115** | nearly fused |
| source-locked (`t0,t2,t4,t6`) | **0.67–0.71** | irreducible geometric surplus |

For the **projective and depolarizing** terrains the fusion is **literal and exact**
(residual `0.00–0.12`): geometry and operator are the same object — the strong GR-ether
case. For the **source-locked** terrains the generator carries a pole-seeking `σ±`
amplitude-damping charge that lies **outside any fixed operator algebra**.

**The surplus is exactly non-unitality — a one-line theorem (grade: `symbolic_identity`).**
The numerical containment split is now upgraded to an exact algebraic statement. All four
operator generators are **unital**: `Ti(I) = Te(I) = Fi(I) = Fe(I) = 0` (dephasing
`½(σρσ−ρ)` and coherent `−i[H,ρ]` both annihilate `I`). Any linear span of unital maps is
unital, so **every element of the operator algebra is unital.** The source-locked terrains
carry amplitude damping `D[σ±]`, which is **non-unital**: `‖L(I)‖ = √2 ≠ 0` exactly for all
four (`t0,t2,t4,t6`), while the fused terrains have `‖L(I)‖ = 0` exactly (`t1,t3,t5,t7`).
Therefore the source-locked generators **provably cannot lie in the operator algebra** — the
surplus is non-unitality, and the celebrated 8/8 fusion bit is exactly the indicator
`𝟙[‖L(I)‖ ≠ 0]`. This replaces the falsified co-moving-frame test (which was only suggestive)
with a theorem: no frame can move a non-unital generator into a unital algebra, because
unitality is basis-independent (`L(I)=0 ⟺ UL U†(I)=0`).

> **Model recommendation.** Record a **two-tier fusion**, now with the split as a theorem:
> the fused terrains (projective/depolarizing) literally *are* their operators — both are
> unital, geometry and operator provably inseparable — while the source-locked terrains carry
> a **non-unital** amplitude-damping charge (`‖L(I)‖ = √2`) that no unital operator algebra
> can contain, in any frame. The 8/8 fusion bit is exactly `𝟙[‖L(I)‖ ≠ 0]`. The "2 native
> operators per terrain" law is a valid Axis-6 *labelling* (which operators are admitted) but
> is **not** a claim that the terrain reduces to those operators: half the terrains carry
> surplus non-unitality. This is the precise, proven form of "the surface is the operator" —
> true literally for the unital half, and provably false (with the exact obstruction named)
> for the non-unital half.

---

## 7r. The 16 engine stages on the fused-operator foundation

*(The stage layer, built directly on §7p–§7q. All indices structural per §9a.)*

The 16 engine stages are **8 terrains × 2 native operators each**, each in a signed Axis-6
order (operator-first vs terrain-first). Built on the fusion foundation of §7q, the stage
layer inherits the two-tier structure and adds the Axis-6 order dimension.

**Three properties, all verified.**

1. **All 16 stages are distinct** under a dynamical fingerprint (both Axis-6 orders on a
   fixed probe): mean pairwise distance `4.6`, minimum `0.25`. The bottleneck is the pair
   `t3:Te–t7:Te` — the two projective Si stages — the same near-degeneracy identified in
   §7p and §7q, now confirmed to propagate to the stage layer.
2. **All 16 stages are order-sensitive (N01, 16/16).** Operator-first and terrain-first give
   different outputs for every stage, so each stage does **unique information processing** —
   the N01 non-commutation is load-bearing at the stage level, not just the operator level.
3. **The fusion split is exactly 8/8.** From the §7q containment residuals, **8 of the 16
   stages are operator-fused** (the projective and depolarizing terrains, residual
   `0.00–0.12`) and **8 are source-surplus** (the amplitude-damping and source-locked
   terrains, residual `0.67–0.71`).

**The cross-section link (one bit, read three ways — not threefold convergence).** The 8
source-surplus stages are exactly the **dissipative half** — the same half that makes the
perceiving parity readable under §7o. It is tempting to call the agreement across §7o, §7p,
and §7q a threefold convergence, but that would overstate it: all three partitions are
functions of the **same underlying bit — the dissipative/unitary contrast (Axis-1)**.
§7o's readability, §7q's containment residual, and the dissipative half of §7p are three
*readings of one bit*, so their agreement is **internal consistency, not independent
corroboration**. The genuinely non-trivial fact is narrower and worth stating plainly: the
operator-algebra containment (§7q) lines up with the entropy-gated readability (§7o) because
both are downstream of dissipation — which is the co-ratchet claim, not three separate
confirmations of it.

> **Model recommendation.** The 16 stages are a fully differentiated, order-sensitive set on
> the fused-operator foundation, with a clean 8-fused / 8-source-surplus partition. (This
> partition is a reading of the Axis-1 dissipative/unitary bit, so its agreement with §7o/§7q
> is consistency, not independent convergence — see the cross-section note above.) Each of
> the two engine types (`eps = ±`) accesses 8 of the
> 16 stages (the eight-of-sixteen access law). When the real Julia/JAX/PyTorch engines run,
> the per-stage fingerprint (`sixteen_stage_engine.json`) and the fused/source-surplus tag
> are the concrete validation targets: each engine stage must reproduce its fingerprint row
> and land in its predicted fusion tier.

---

## 7s. The eight-of-sixteen access law (engine type as Weyl chirality)

*(The engine-type layer, built on §7r. Indices structural per §9a. Grounded in
`engine-math-reference.md` line 55: Type-1/Left-Weyl = the four "in" terrains
{Funnel, Vortex, Pit, Hill}; Type-2/Right-Weyl = the four "out" terrains
{Cannon, Spiral, Source, Citadel}.)*

The owner's law: there are 16 stages, but **each person is one engine type and accesses
only 8 of them.** The two engine types are the two Weyl chiralities (`eps = ±1`, sheet
Hamiltonians `H_L = +H₀` and `H_R = −H₀`). The question is whether the 8/8 split is a
genuine dynamical constraint or merely a relabeling. Three tests, all structural.

**1. The partition is exact and pole-mirrored.** The Left engine (`eps=+1`) accesses the
four in-terrains `t0–t3`; the Right (`eps=−1`) accesses the four out-terrains `t4–t7`;
overlap zero, union all eight. Run on their native sheets, the dissipative terrains reach
pole-mirror fixed points: `t0` at `z*=+1` mirrors `t4` at `z*=−1`, and `t2` at `z*=−1`
mirrors `t6` at `z*=+1` (each pair sums to zero). The out-terrains are the **pole-flipped
images** of the in-terrains — exactly what opposite Weyl handedness (`ṙ = ±2 n×r`) requires.

**2. The engine type is the global sign of the loop geometric phase — and it is the
terrain's, not the meter's.** Driving each stage as a closed loop (terrain flow + operator,
modulated around the sheet's `H₀` rotation) and measuring the signed swept Bloch area (the
eps-odd geometric-phase proxy of §7p): all 8 Left-engine stages give positive geometric
phase, all 8 Right-engine stages negative. **A circularity had to be ruled out first:** `eps`
appears in *both* the terrain Hamiltonian and the measurement drive, so the "global sign"
could have been the meter's chirality, not the stage's. Decoupling the two `eps` values
across all 16 stages, **the sign follows the terrain 14/16 and the drive only 2/16** — the
chirality genuinely lives in the stage, the law earning itself against its own hostile probe.

**3. Access violation flips the stages — the two-tier structure (corrected 2026-07-01).**
Forcing a stage onto the wrong sheet reverses its geometric-phase sign. Under a fully
chirality-neutral meter the flip holds **14/16**, and the two failures are exactly `t3:Fe`
and `t7:Fe` — the same sheet-symmetric projective Si pair that was the bottleneck in §7p and
§7r. The manifold's weakest chirality fails first, precisely where the fingerprint predicted.
The published `16/16` is real **only because the loop carries the sheet's own `H₀`**; that is
defensible (the engine's Hamiltonian arguably *is* part of the stage) but must be adopted as
the loop's definition explicitly, or the theorem is `14/16`. The failures are all `Fe`
stages — `Fe` is a fixed-sign z-rotation that competes with the terrain's signed one.

**The two-tier structure (mirrors §7q's fusion split).** The probe revealed an exact
symmetry on half the stages: the **dephasing stages (`Ti`, `Te`) negate identically under
`eps`-flip** — `|a(+) + a(−)| = 0` to machine precision for all 8 — because dissipators are
conjugation-invariant while the coherent term flips (`y → −y` negates the swept area). This
is an exact *symbolic-identity theorem* on the 8 pinching stages. The **rotation stages
(`Fi`, `Fe`) are dynamical and approximate** (deviation up to `0.18`). So the access law is
two-tier, exactly paralleling §7q: exact on the pinching half, dynamical on the rotation
half. Within each engine the 8 stages remain fully distinct (min pairwise `0.15`/`0.20`).

> **Model recommendation.** The eight-of-sixteen access law is a **structural theorem in the
> strongest sense for half of it**: on the 8 dephasing stages the engine sign is an exact
> conjugation-symmetry identity; on the 8 rotation stages it is dynamical, holding `14/16`
> under a chirality-neutral meter with the two failures pinned to the known `t3/t7` projective
> bottleneck. The chirality provably lives in the terrain (`14/16` vs `2/16` decoupled), not
> the meter — the circularity is ruled out. To claim the full `16/16`, **adopt explicitly
> that the engine loop carries the sheet's own `H₀`** (the Hamiltonian is part of the stage);
> otherwise state the theorem as `14/16` + the exact 8-stage identity. Either way the split is
> earned dynamically, not stipulated. Validation target for the real engines: a Left-engine
> run gives positive loop areas, a Right-engine run negative, with the dephasing stages exact.

---

## 7t. The native-operator law earned: exact W-covariance (from the audit)

*(New positive result, 2026-07-01, produced by an external audit of the bundle and verified
here independently. This is the exact derivation the §7q null could not supply.)*

§7q established that no lab-frame metric prefers each terrain's two native operators, and was
careful to call that an honest null. The audit supplied what was missing: an **exact symmetry
that derives the native-operator law**.

**The theorem.** Let `W = (σx + σz)/√2` be the Hadamard involution (`W = W† = W⁻¹`). Then `W`
conjugation maps the **direct** operator pair to the **conjugated** pair, exactly as channels:

> `W · Ti · W = Te` (residual `3.4×10⁻³³`) and `W · Fi · W = Fe` (residual `4.5×10⁻¹⁷`) —
> all residuals here and in §7u are **Frobenius norms** `‖·‖_F` of the superoperator
> difference, not squared norms; `Ti→Te` is an exact Pauli-basis permutation, hence the
> `10⁻³³` floor,
> where `Ti` = z-dephasing, `Te` = x-dephasing, `Fi` = x-rotation, `Fe` = z-rotation.

This is because `W σz W = σx` and `W σx W = σz` exactly — `W` swaps the `z` and `x` axes
simultaneously. So the operator table's own definition (§7q, `igt-pattern` 473–478) —
"conjugated = the `x↔z` image of direct" — **is** frame covariance under `W`. The
native-operator law is no longer a labelling; it is a **theorem**: the conjugated terrains
take the conjugate operator pair because their frame is the `W`-image of the direct frame.

**The decidable fork, settled.** The spec's stated Axis-2 element is `V_s(u) = exp(−iH₀u)`
(§ Axis-2, the co-rotating frame). Does `V` implement the `x↔z` swap? **No — and this is a
correction to the spec.** A rotation about the `H₀` axis `(1,1,1)/√3` can send `σz→σx` (the
120° cyclic permutation `x→y→z→x`), but that same rotation then sends `σx→σy`, so it maps
`Fi` to a *Y*-rotation, **not** `Fe`. Only the involution `W` (rotation by π about the `x–z`
diagonal `(1,0,1)/√2`) swaps `z↔x` for **both** operator pairs at once. Therefore:

> **The native-operator law is earned as covariance under the Hadamard involution `W`, and
> the spec's `V = exp(−iH₀u)` is a stand-in that does not implement the direct↔conjugated
> map.** Either the repo's canonical Axis-2 conjugation should be corrected to `W` (the
> `x↔z` involution), or `V = exp(−iH₀u)` is a genuinely different Axis-2 element and `W` is a
> separate exact symmetry of the operator algebra that the model has not yet named. The
> operator table as written encodes `W`.

> **Model recommendation.** Promote the native-operator pairing from a rosetta labelling
> (§7q) to an **earned structural law**: it is exact `W`-covariance, `Ti↔Te` and `Fi↔Fe`
> under `W = (σx+σz)/√2`, verified to machine precision. Flag the Axis-2 definition for
> repair: the frame element that realizes direct↔conjugated is the `x↔z` Hadamard involution,
> not the `H₀`-axis rotation currently written as `V_s(u)`. This is the shortest path to
> earning the law, and it is a concrete, decidable correction to the spec rather than another
> exploration. Verified in `audit_response_w_covariance_sim.py`.

---

## 7u. Axis-2 is a two-layer object — the W-vs-V fork resolved

*(Follow-up to §7t, running the consistency check the fork demanded. Result: not a spec
repair but a structural refinement — Axis-2 carries two composable layers.)*

§7t left a decidable fork: the native-operator law is exact covariance under the Hadamard
involution `W = (σx+σz)/√2`, but the spec's Axis-2 element is the co-rotating frame
`V_s(u) = exp(−iH₀u)` with connection `K = iV†V̇` (§7n). Either `V` is wrong and should be
`W`, or `W` is a separate symmetry. Testing `W` against the four properties Axis-2 must
satisfy settles it — and the answer is **neither is wrong: Axis-2 has two layers.**

| property Axis-2 must satisfy | `V = exp(−iH₀u)` | `W = (σx+σz)/√2` |
|------------------------------|:----------------:|:---------------:|
| gauge-invariant (preserves all state invariants, §7n) | ✓ `9×10⁻¹⁶` | ✓ `8×10⁻¹⁶` |
| implements direct↔conjugated operator map (§7t) | ✗ `Ti→Te 0.67, Fi→Fe 2.15` | ✓ `Ti→Te 3×10⁻³³, Fi→Fe 4×10⁻¹⁷` |
| phase-sector element (moves eigenvectors, not spectrum, §7n) | ✓ | ✓ `Δλ 9×10⁻¹⁶` |
| carries a connection `K = iV†V̇` (changes effective dynamics, §7n) | ✓ `K = H₀` | ✗ `K = 0` |

**The two layers.** `V` and `W` are **different kinds of Axis-2 object**, each supplying what
the other lacks:

- **Continuous layer — `V = exp(−iH₀u)`:** a `u`-dependent co-rotating frame. Its connection
  `K = iV†V̇ = H₀` is nonzero, so it changes the effective dynamics — the §7n role. But a
  rotation about the `H₀` axis cannot implement the `x↔z` operator swap (it sends `Fi` to a
  Y-rotation, not `Fe`).
- **Discrete layer — `W = (σx+σz)/√2`:** a fixed `ℤ₂` involution. Being `u`-independent,
  `V̇ = 0` so its connection is zero — it is not a continuous frame. But it carries the exact
  direct↔conjugated operator map (`Ti↔Te`, `Fi↔Fe`) — the §7t role.

**They compose consistently.** `W` acts on the continuous frame by conjugating its
connection: `K → WKW = H₀ − 2σy/√3` (the connection's `y`-component flips because `WσyW =
−σy`). This is exactly the §7n clause "the connection `K = iV†V̇` changes the effective
dynamics," now realized as the discrete direct/conjugated bit acting on the continuous
frame's connection. So the two layers are one coherent axis, not rival elements.

> **Model recommendation.** **No spec repair is needed — Axis-2 is refined, not corrected.**
> The stated element `V_s(u) = exp(−iH₀u)` is the **continuous layer** (co-rotating frame,
> connection `K = H₀`); the Hadamard `W` is the **discrete layer** (the direct↔conjugated
> `ℤ₂` involution) that the spec was missing, and it is what earns the native-operator law of
> §7q/§7t. Record Axis-2 as a two-layer object `(V continuous frame) × (W discrete
> direct/conjugated bit)`, composing via `K → WKW`. This closes the §7t fork: the native
> operator law is earned as covariance under the discrete layer, and the continuous frame
> keeps its §7n role intact. Verified in `axis2_two_layer_sim.py`.

**The sharper open item this surfaces (better-posed than the fork).** The `W`-covariance is
exact at the **operator** level (`Ti↔Te`, `Fi↔Fe`). It does **not** extend to the **terrain**
level: neither `W` nor `V` conjugates the direct terrain generators into their conjugated
partners — `‖ U L_direct U† − L_conj ‖ = 1.4–2.0` (Frobenius) for both elements, on all four
candidate pairings. So the direct/conjugated assignment *on terrains* (the `a2` bit) still
rests on the repo's source table alone; it is not yet derived from a frame symmetry. This is
the actual remaining gap in Axis-2 — a sharper, more tractable question than "which element
is the frame," which the two-layer resolution retired.

---

## 7v. χ₂ — the open-path phase readout for the eigenvector sector (earned as a sector meter; see the grade-correction flag below and §7w)

*(The last genuinely open item at this layer. §7n proved Axis-0's parity needs both charges
read; χ₁ (entropy) read cleanly, but χ₂ (the eigenvector-sector phase charge) had no working
instrument — closed-loop holonomy was proven gauge-invariant and therefore identically zero.
This builds and validates χ₂.)*

**The instrument.** χ₂ is the **Bargmann/Pancharatnam open-path geometric phase** of a state's
top eigenvector against two fixed references `r₀, r₁` (states the gauge does not act on):

```
χ₂(ρ) = −arg( ⟨r₀|e⟩ ⟨e|r₁⟩ ⟨r₁|r₀⟩ ),   e = top eigenvector of ρ
```

This is the exact fix for why holonomy failed. A **closed** loop of frame conjugations is
gauge-invariant and returns to the identity → phase 0 (§7-era finding). An **open path** of
three distinct states has a nonzero relational phase that is *still* gauge-invariant under
per-ket rephasing `|ψ⟩ ↦ e^{iφ}|ψ⟩` — it reads the eigenvector sector without the closed-loop
cancellation.

**Verified properties (all in `chi2_openpath_readout_sim.py`).**

| property | result |
|----------|--------|
| **open-path, not closed** | 3 distinct states → `−1.01` (nonzero); degenerate/closed → `0.0` |
| **gauge-invariant** (per-ket rephasing) | diff `0.0` (exact) |
| **two-sector orthogonality** | varying eigenvectors at fixed spectrum moves χ₂ (`0 → 0.64`) while `S ≡ 0.5004`; varying spectrum at fixed eigenvector holds χ₂ `= 0.6397` while `S` runs `0.33 → 0.67` |
| **the Ξ parity readout** | χ₂ distinguishes the direct frame `V` from its conjugate `V*` by `1.22`; entropy is blind (`9×10⁻¹⁶`) |

**The Ξ parity, robust.** Over **2000 random probes**, entropy cannot see the
direct↔conjugated frame bit at all (`max|S_direct − S_conj| = 9×10⁻¹⁶`), while χ₂ reads it on
**99.7%** (`mean |Δχ₂| = 1.57`). The only misses are the measure-zero set where the eigenvector
lands on a reference pole — closable with a third reference. Crucially, the frame bit is read
from a **genuine operation** (`V` vs `V*`, complex conjugation of the frame element), not from
a label: this is *not* the circular "read χ₂ off the assignment" that an earlier audit
correctly flagged.

> **Model recommendation.** *(Superseded in scope by the grade-correction flag immediately
> below and by §7w — read those first.)* **χ₂ is an earned eigenvector-sector meter.** The
> two-sector theorem of §7n now has both meters: χ₁ = entropy charge (eigenvalue sector,
> already earned), χ₂ = Bargmann open-path phase (eigenvector sector). But χ₂ is **not
> a2-specific** — the fourth audit showed the demonstration read the K-mirror pair, and §7w
> shows the a2 (direct/conjugated) bit is realized at the **operator layer** (§7t), not at the
> terrain-generator layer. So the `Axis-0 = Axis-1 ⊕ Axis-2` parity of §7m reads end-to-end at
> the **operator layer**; the terrain-level a2 bit (§7u generator-map residuals `1.4–2.0`) is
> resolved in §7w as a no-go, not an open meter. Grade: the
> open-path/gauge-invariance/two-sector properties are exact identities; the 99.7% frame-read
> is an empirical robustness result over random probes.

> **[AUDIT FLAG 2026-07-01 — grade correction from the fourth audit; χ₂ is NOT closed as an
> a2 meter.]** Two findings, machine-verified (`chi2_decisive_test_sim.py`):
> (i) **The `V` vs `V*` pair is the K-mirror pair, not the model's a2 pair.** `V* = K(V)`
> (complex conjugation; `H₀* = (σx−σy+σz)/√3`, the y-flipped axis). Three distinct binary
> operations exist on the frame element — a2 (`V` vs `I`), ε (`V` vs `V†`), and K (`V` vs
> `V*`) — and χ₂ responds to **all three** (mean discriminations 0.94 / 1.13 / 1.51) while
> entropy is blind to all three. χ₂ is therefore an earned **eigenvector-sector meter**, but
> it is not **charge-specific**: the §7v demonstration read the K-pair while labelling it the
> a2 bit — a third conflation of the kind §7u just resolved for V/W.
> (ii) **The decisive terrain-level test fails with this instrument.** Applying the
> non-circular pair (χ₁ = 𝟙[‖L(I)‖=0] per §7q's non-unitality theorem; χ₂ = trajectory
> Bargmann phase sign) across the 8 terrain generators: `sign(χ₁)⊕sign(χ₂)` matches the
> `{Ne,Ni}|{Se,Si}` target on only **2/8** (6/8 under the opposite sign convention; neither is
> a readout). The failure is structural, not statistical: the Bargmann phase is
> **ε-contaminated** (sheet-sensitive — e.g. `t1 = +0.510` vs its mirror `t5 = −0.000`),
> while the N/S target is ε-even. Per §7m's own falsification fork this outcome is the third
> branch: **the test is not yet decisive because the instrument lacks charge-specificity.**
> Consequences: §7m remains **admissible candidate** (not "exact/earned" — the parity has
> still never been read); the sharpened open item replacing "build χ₂" is: **construct an
> ε-even (K-invariant), a2-specific eigenvector functional** — a meter covariant under
> `V`-vs-`I` while invariant under the K-mirror and the sheet sign. The rosetta's
> "χ₂ earned" tier should read "earned as sector meter; a2-specificity open".

---

## 7w. The terrain-level a2 bit — resolved as a layer statement, not a missing meter

The fourth audit (§7v flag) sharpened the open item to: *construct an ε-even,
a2-specific eigenvector functional* that reads the direct/conjugated bit off the eight
terrain generators. This section reports that attempt and its resolution
(`eps_even_a2_specificity_sim.py`).

**The ε-contamination is removable.** Symmetrizing the open-path phase over each terrain's
ε-mirror, `φ̄(t) = ½[φ(t) + φ(mirror(t))]`, produces an exactly ε-even functional — the
mirror pairs `t0/t4, t1/t5, t2/t6, t3/t7` collapse onto identical values to machine
precision (`|diff| = 0`). So the sheet-sensitivity the audit flagged is not an obstruction
in itself; it can be quotiented out.

**But the ε-even functional still does not separate a2.** After ε-symmetrization the
*direct* terrains (`a2=0`: t0,t1,t4,t5) occupy the range `[0.107, 0.255]` and the
*conjugated* terrains (`a2=1`: t2,t3,t6,t7) occupy `[0.106, 0.418]` — the ranges **overlap**
(t3,t7 at 0.106 fall *below* t0,t4 at 0.107). Removing the ε-charge exposes what the phase
magnitude actually tracks: the **dynamics type** (damping / depolarizing / projective =
the a1 non-unitality bit of §7q), not the direct/conjugated frame bit.

**Why — and where a2 does live.** The reason is structural, and it closes the item rather
than leaving it open. The direct↔conjugated bit **is** realized exactly — by the Hadamard
`W` of §7t — but at the **operator layer**: `‖W·Ti·W − Te‖ = 9×10⁻¹⁶` (W conjugates the four
judging operators into their a2-partners). It does **not** descend to the terrain generators:
`‖W·L(tᵢ)·W − L(a2-partner)‖ ≈ 2.05` (mean over the four a2-pairs), matching the §7u
generator-map residuals `1.46–1.95`. So a2 is an **operator-layer label**, one level above the
terrain-generator flows. No terrain-generator functional can read it — not because we have
not found the right meter, but because a2 is not a terrain-generator property.

> **Model recommendation.** The terrain-level a2 open item is **resolved as a layer
> statement**: a2 is earned at the operator layer (§7t, W-covariance, exact) and is provably
> *not* a terrain-generator observable (any ε-even generator functional reads a1, and W
> conjugates operators but not generators). This upholds the fourth audit's grade — χ₂ stays
> an **earned eigenvector-sector meter, not a2-specific** — and converts "build an ε-even
> a2-specific terrain functional" from an open construction into a **no-go with a located
> home**. §7m's parity `Axis-0 = a1 ⊕ a2` therefore reads end-to-end only when a2 is taken at
> its native operator layer; at the terrain layer the parity is carried, not measured. Grade:
> the ε-evenness and the operator-vs-terrain split are exact identities; the non-separation is
> a finite-exhaustive check over the eight generators. `§7m` remains **admissible candidate**
> at the terrain layer and **instrumented** at the operator layer.

---

## 9a. Simulation hygiene and the rosetta layer

**Principle (owner-directed).** Sims must be **pure real math and structure** — no
interpretive jargon in the computation — so that no conflation can enter through naming.
Labels are applied only afterward, in a **separate rosetta layer**, and only where the
earned structure independently supports them.

**What the sims contain now.** The Axis-0 sims (`axis0_xor_sim.py`,
`axis0_sector_sim.py`) were refactored to carry only structural primitives:

| symbol | pure meaning (no label) |
|--------|-------------------------|
| `eps ∈ {+1,−1}` | sheet sign; `H = eps·H₀` |
| `a1 ∈ {0,1}` | dynamics bit: 1 = spectrum-preserving (unitary), 0 = spectrum-contracting (dephasing) — **eigenvalue sector** |
| `a2 ∈ {0,1}` | frame bit: 1 = conjugated `V†ρV`, 0 = identity — **gauge / eigenvector sector** |
| `p = a1 ⊕ a2` | parity bit — the third observed 2\|2 split |

No terrain names, no `Se/Ne/Ni/Si`, no "intuition/sensing" appear in the math. The
identity `p = a1 ⊕ a2` and the two-sector theorem are stated over these indices alone.

**The rosetta layer** (`rosetta_layer.json`) maps the earned structure to every label
system, each tagged with an **earned status**:

- **earned** — the structure realizes it exactly: `a1`→Axis-1, `a2`→Axis-2, `p`→Axis-0
  (N/S); the 8 `(a1,a2,eps)` tuples → the 8 terrain names.
- **witness** — usable symbolic crosswalk that must **not** replace the math anchor:
  the Jungian intuition/sensing reading of `p`; the taijitu yin/yang split (its two
  **seed-dots** — each half carrying a dot of the other — are an apt witness for the
  XOR: the N class is exactly where the two charges *disagree*, i.e. each "contains" the
  other).
- **candidate** — suggested by the structure, not yet closed, never a design input: the
  **Carnot/Szilard** correspondence (the 4-stage isothermal↔adiabatic cycle = the
  dissipative↔unitary `E/U` loop word; Szilard measure→work→reset = dephasing + Landauer
  entropy cost; the actual engine remains **pure QIT**, no classical thermo smuggled in);
  and the **I-Ching** correspondence (only the `2⁶ = 64` count is grounded so far;
  per-hexagram semantics are fenced — recorded to *check as structure is earned*, per the
  owner's stance that the system may naturally reflect I-Ching patterns but must never
  have them forced on).

**Connected but fenced lanes.** The constraint core couples to three further owner
models through its **dynamic geometry** (the nesting shells of §7a that expand and
contract, not a static background): the **holodeck/FEP** model (a root predictive model
of memory and perception — the pure-QIT FEP of §7e is its constraint-core kernel); and
**entropic-monism cosmology** with **dynamic shells** (the dark-energy/dark-matter
sector). These are recorded as connected lanes, deliberately **not** expanded into this
spec — their claim ceilings (`legacy-physics-cosmology`, `fep-to-axis0-bridge-claim-ceilings`)
fence them, and the constraint core earns only the finite QIT structure, leaving the
cosmological reading as a downstream overlay.

---

## 10. Foundation lock

> All mathematics, geometry, and dynamics are emergent from constraint.
> Identity is equivalence under admissible probes. Entropy measures
> distinguishability under constraint. Geometry is a stabilized description of
> compatibility. Axes classify irreducible compatibility distinctions. Engines
> are selected cycles, not inventions.

The concrete realization in §4–§7 is a **machine-checked, internally consistent**
instance of this foundation — offered as a candidate attractor under C1–C3, with
its one convention ambiguity resolved and its open questions held explicitly
open.
