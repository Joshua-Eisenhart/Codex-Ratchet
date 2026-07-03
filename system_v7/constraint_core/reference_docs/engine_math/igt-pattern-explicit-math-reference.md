# IGT Pattern And Constraint Ratchet — Explicit Math Reference

## 2026-06-06 acronym and manifold-order correction

In the owner-pattern lane, `IGT` means **Irrational Game Theory**. Its object is
the WIN/LOSE + win/lose two-engine pattern. QIT operators, terrains, axes,
Jung/I-Ching/taijitu labels, and token tables are implementation/readout/test
surfaces; they do not replace IGT itself.

Do not acronym-collapse IGT into infinite game theory, information geometry
theory/topology, generic game theory, or a QIT operator table unless the page is
explicitly discussing those external meanings as separate support material.

Also load [[constraint-manifold-architecture]] first: IGT/axis/engine mappings
sit downstream of the geometric constraint manifold `M(C)`. Until `M(C)` is made
as a finite admissibility object, IGT-to-QIT and bridge-facing rows remain chart
grammar, pressure, or controls — not admission.

**Status:** Working reference. Source-grounded, not canon. Nothing here is admitted.

**What this doc is:** The full current picture — the ratchet method, the constraint chain, the axes as exploration space, the IGT strategy grammar, the geometry/entropy landscape to explore, and what math is strongly constrained vs what has wiggle room.

**What this doc is not:** A finished theory. A proof. A settled axis system. The axes are candidate splits with varying levels of math support. The geometries are candidate carriers. The IGT labels are chart grammar, not physics.

**Terminology note:** The 16 strategy entries are **strategy placements**, not independent operators. The actual operator maps are Ti, Te, Fi, Fe. Each placement is one operator composed with one terrain in a specific order.

**Three distinct "order" concepts (do not collapse):**
1. **Pair-readout order:** which token appears first/second in labels like `winWIN`.
2. **Axis-6 composition order:** operator-first `Φ_T(O(ρ))` vs terrain-first `O(Φ_T(ρ))`.
3. **Four-step loop order:** terrain sequence inside a loop (e.g. Se→Ne→Ni→Si).

**Fences:**
- Strategy phrases ("maximize wins", "climb the hill") are IGT readings, not math, until a named functional is attached.
- "Chirality breaking" here is **strategy-grammar chirality** — a candidate. Geometric chirality needs a carrier-side witness.

---

## Part I: The Ratchet

### 1. What the ratchet is

Start from constraints. Pick the minimal thing they force. That minimal thing constrains the next layer. Take minimal leaps with minimal assumptions. Build up to more complex structure. The geometry that is **allowed** to exist under the constraints is the carrier geometry. The constraints themselves ratchet — each admitted layer narrows what the next layer can be.

The constraint manifold and the carrier geometry are **not the same thing**:
- The constraint manifold `M(C)` = all configurations admissible under the constraints
- The carrier geometry = the specific geometric structure living inside `M(C)`
- The geometry **becomes** constraints on the next layer

This is not proof by deduction. It is constraint-driven exploration: massive branching, selection pressure, what survives is the attractor basin. The graveyard of killed alternatives IS the evidence.

### 2. The two root constraints

```
F01  FINITUDE:        dim(H) < ∞, |P| < ∞, |O| < ∞, |Γ| < ∞
                      Only finite carriers, probes, operators, and paths are admissible.

N01  NONCOMMUTATION:  AB ≠ BA in general, Aρ ≠ ρA in general
                      Order belongs to the object.
```

Everything else derives from or is killed by these. They are operational, not philosophical.

**On minimality:** The ratchet method already embodies minimality — you don't add structure until the previous layer leaves no weaker surviving option. This is not a third constraint. It is what proof and logic already require: presume the least. If you have to add something, it should be because the constraints and kill tests left no simpler alternative, not because you chose it. The graveyard of killed alternatives is the evidence that a step earned its current pressure.

### 3. The extended axioms (what is banned)

| Axiom | What it bans | Why |
|---|---|---|
| No primitive identity | `a = a` is not free; identity requires contrast under admissible probes | Identity is earned, not given |
| Probe-relative indistinguishability | `a ~ b iff ∀p∈P, p(a) ≈ p(b)` for finite P | Replaces primitive equality |
| Identity principle | `a = a iff a ~ b` — self-identity requires boundary/contrast | The core move: identity from distinguishability |
| No primitive time | Ordered composition exists without primitive time parameter | Time is derived |
| No primitive geometry | No coordinates, no metric, no geometry at root | Geometry is induced |
| No free closure | No algebraic totality by default | Composition must be explicitly admitted |
| No primitive probability | No distributions at root | Probability is derived |
| No primitive metric | No distance, norm, or coordinate chart | All later |
| No optimization | No utility primitives | Constraint-only admission |

### 4. The ratchet chain (current best ordering)

```
constraints → M(C) → S³ → T_η → (ψ_L, ψ_R) → (ρ_L, ρ_R, γ_f, γ_b) → Ξ → ρ_AB → entropy
```

Expanded:

| Step | Layer | What is admitted | What constrains it | Status |
|---|---|---|---|---|
| 1 | Root constraints | F01 + N01 | — | Solid |
| 2 | Admissibility set C | Probe rules, composition rules, all the bans above | F01 + N01 | Solid |
| 3 | Admissible manifold M(C) | All configurations admissible under C | C | Active |
| 4 | Axis-slice rule | Each axis is a function `A_i : M(C) → V_i` | M(C) | Active |
| 5 | Finite carrier realization | `H = C²`, density states, probes, Pauli basis | F01 forces finite dim; N01 forces noncommutative algebra | Likely but not proven inevitable |
| 6 | Normalized spinor carrier | `S³ = {ψ ∈ C² : ‖ψ‖ = 1}` | Step 5 | **Strong survivor candidate** (see §5) |
| 7 | Hopf projection | `π(ψ) = ψ†σψ ∈ S²` | Step 6 | Active |
| 8 | Torus strata | `T_η = {ψ_s(φ,χ;η)}` nested Hopf tori in S³ | Step 7 | Active |
| 9 | Weyl sheets | `ψ_L, ψ_R` with `H_L = +H₀`, `H_R = −H₀` | Chirality from step 6 | **Leading pressure; not closed** (see §5) |
| 10 | Loop geometry | Fiber loop (density stationary) + lifted-base loop (density traversing) | Hopf connection on S³ | Active |
| 11 | Terrain generators | 8 Lindblad/Hamiltonian channels | Steps 9-10 | Working carrier, could be wrong |
| 12 | Engine runtime | Dual stacked engines, 4 stages each, L/R chirality | Steps 10-11 | Working carrier, could be wrong |
| 13 | Bridge Ξ | geometry/history → ρ_AB bipartite cut state | Steps 9-12 | Open |
| 14 | Axis 0 functional | Φ₀(ρ_AB) — entropy/correlation readout | Step 13 | Open but narrowed |

### 5. What the ratchet pressures (with derivation chain and challenges)

The ratchet does not close things in one deductive step from axioms. It creates pressure by **killing alternatives at each layer**. "Strong survivor" means "what survives after everything simpler or weaker has been excluded by the current tests." Each step below shows what the previous layer constrains, what alternatives were killed, and what survives.

**Step: Finite noncommutative algebra**
- *Previous layer:* F01 + N01
- *Killed:* infinite-dimensional carriers (F01), commutative algebras (N01), dimension 1 (all 1×1 matrices commute)
- *Survives:* M_n(ℂ) for n ≥ 2 — finite-dimensional matrix algebras over ℂ
- *Challenge (Grok/Codex2):* Why ℂ and not ℝ or ℍ? Why matrix algebras and not Jordan algebras, finite group algebras, or process categories?
- *Response:* These are live alternatives to explore. ℂ is the standard choice; ℝ gives SO(n) which is commutative for n=2; ℍ gives Sp(n) which is valid but more complex. The ratchet should test all and see what survives.

**Step: ℂ² as minimal carrier (spinors, not vectors)**
- *Previous layer:* Finite noncommutative algebra
- *Killed:* ℂ¹ (commutative), ℂ³ or higher (ℂ² already satisfies N01 — you don't add complexity when a simpler structure survives), **vectors** (see below)
- *Survives:* ℂ² — the smallest space where matrices don't commute. Elements of ℂ² are spinors by definition.
- *Why spinors, not vectors:* A vector lives in a space that presumes a metric, an inner product, and Cartesian coordinate structure. Vectors transform under SO(n), which requires a prior notion of "rotation in a pre-existing space." A spinor is more primitive: it lives in ℂ² with only complex linearity and norm. It transforms under SU(2), which is the double cover of SO(3) — meaning rotations are *derived* from spinor structure, not the other way around. Spinors presume less than vectors. Vectors presume a Cartesian background that the constraints ban (no primitive coordinates, no primitive metric, no primitive geometry). Spinors don't need that background. They ARE the carrier from which geometric structure later emerges.
- *Challenge (Grok 4.3):* "Nothing privileges ℂ² over two qubits or a qutrit" — ℂ² is the minimal carrier that satisfies N01. You don't reach for ℂ³ until ℂ² fails.
- *Challenge (Codex2):* "Forced only if phase/cover/holonomy is load-bearing" — under N01, composition order is part of the object. Phase encodes composition order (the relative phase between components of ψ tracks how operations were sequenced). Vectors in ℝ³ lose this — they have no phase. So yes, phase is load-bearing under the constraints.

**Step: SU(2) as the symmetry group**
- *Previous layer:* ℂ² carrier
- *Killed:* U(2) (includes global phase, which is not probe-distinguishable under F01), GL(2,ℂ) (not norm-preserving)
- *Survives:* SU(2) — norm-preserving, determinant-1 transformations on ℂ². Isomorphic to unit quaternions.
- *Status:* Strong. This is standard and well-understood.

**Step: Density matrices as state language**
- *Previous layer:* ℂ² carrier + probe-relative equivalence (extended axiom 2)
- *Killed:* Pure state vectors alone (can't represent probe-relative uncertainty or mixed states)
- *Survives:* ρ = |ψ⟩⟨ψ| for pure states, general ρ ≥ 0 with Tr(ρ) = 1 for mixed states
- *Challenge (Codex2):* "Natural after choosing QIT, but not root-closed" — but the extended axioms (no primitive probability, probe-relative identification) point directly at density matrices as the minimal state description that handles uncertainty without probability primitives.

**Step: S³ as carrier geometry**
- *Previous layer:* ℂ² + normalization (states are unit vectors)
- *Killed:* Unnormalized ℂ² (physically meaningless rays), S² / Bloch sphere (loses global phase)
- *Survives:* S³ = {ψ ∈ ℂ² : ‖ψ‖ = 1}
- *Challenge (all 3):* "S² loses phase, but does phase matter?" — under the constraints, order matters (N01). Phase carries order information. S² quotients it out. S³ preserves it. The constraints point to S³.
- *Challenge (Gemini):* "Bloch Ball B³ is more natural for mixed states" — valid for mixed states. S³ is for pure spinor states. Both may be needed at different layers.

**Step: Hopf fibration and tori**
- *Previous layer:* S³ geometry
- *Killed:* Nothing yet — this is the natural decomposition of S³, not a choice among alternatives
- *Survives:* π: S³ → S² (Hopf map), T_η nested tori, Hopf connection A = dφ + cos(2η)dχ
- *Challenge (Grok/Gemini):* "This is a choice of coordinates" — partially valid. The Hopf fibration is canonical for S³ (it's the unique nontrivial circle bundle over S²), not an arbitrary foliation. But whether the torus parameterization is the right one vs other decompositions is testable.

**Step: L/R Weyl sheets (ratcheted, not imposed)**
- *Previous layer:* S³ + Hopf structure + N01 (noncommutation forces orientation)
- *Killed:* Single-sheet spinor with no orientation (would lose noncommutative order information), arbitrary multi-sheet decompositions (more complex than needed — two is the minimum that captures left vs right)
- *Survives:* Two sheets with opposite orientations: H_L = +H₀, H_R = −H₀
- *Why this is ratcheted:* Noncommutation (N01) forces that left and right action are distinct (Aρ ≠ ρA). On S³ with SU(2), this naturally gives two orientations. The Weyl split is the minimal realization of this orientation structure on the spinor carrier. It's not imported from physics — it follows from the constraint that order is part of the object, applied to the carrier geometry.
- *Challenge (all 3):* "Where does H₀ come from?" — H₀ is the generator of SU(2) action on the carrier. It exists once SU(2) is admitted. The ± sign is the orientation.
- *Challenge (Codex2):* "L/R must produce a measurable invariant, not just relabeling" — correct. The invariant is the opposite precession: ṙ_L = +2n×r_L vs ṙ_R = −2n×r_R. This is measurable.

**Step: Loop geometry (fiber vs base)**
- *Previous layer:* S³ + Hopf connection
- *Killed:* Arbitrary paths on S³ (not structured by the connection)
- *Survives:* Fiber loops (along connection fiber, density stationary) and lifted-base loops (horizontal, density traversing)
- *Status:* Strong. The Hopf connection determines which loops change density and which don't.

**Step: 720° behavior**
- *Previous layer:* SU(2) carrier
- *Killed:* Nothing — this is automatic from the double cover SU(2) → SO(3)
- *Survives:* 360° gives −ψ (sign flip), 720° returns to +ψ
- *Critical challenge (Codex2):* "720° behavior disappears under ρ = |ψ⟩⟨ψ| unless the engine keeps lifted phase/path/interference data." This is the sharpest point from the tribunal. The engine MUST work at the spinor level, not just the density level, or the 720° structure is invisible. This constrains the engine design.

### 5b. Alternatives not yet killed (from tribunal)

The following carrier geometries are admissible under F01+N01 and have not been excluded. They should be explored or explicitly killed:

| Alternative | What it is | Why it might survive | How to kill it |
|---|---|---|---|
| Higher qudits ℂ³, ℂ⁴ | Qutrits, 2-qubit systems | Richer operator algebras | Show M01 excludes them at this layer, or show they're needed later |
| Finite groups/monoids | S₃, dihedral, braid representations | Satisfy N01 without Hilbert space | Show they can't support the required probe structure |
| Flag manifolds | SU(n)/T^{n-1} | Natural generalizations of S³ | Show no advantage at minimal dimension |
| Choi-state geometry | Geometry of channels, not states | Could be the right level for engine dynamics | Test whether channel-space structure adds information |
| Finite spectral triples | Noncommutative geometry à la Connes | Directly encode F01+N01 | Explore whether this is a better foundation than Hilbert space |
| Real/quaternionic carriers | ℝ², ℍ¹ | Different field choices | Show ℂ is selected by live constraints (spectral theorem?) or explore alternatives |
| Process categories | Monoidal categories of finite processes | Directly encode composition + order | May be more general than needed under M01 |

---

## Part II: The 7 Axes As Exploration Space

Each axis is a binary split on the constraint manifold. Some have strong math. Some are proposals with multiple candidate realizations. The axes are numbered 0-6 (7 total). Axes 7-12 are a planned later mirror layer for engine-on-engine interaction (not active).

### Axis 0 — The drive

**What it splits:** {Ne, Ni} vs {Se, Si} — the perceiving topologies that are dynamically "active" vs "conservative."

**IGT correlation:** {WinLose, LoseLose} vs {LoseWin, WinWin}

**Taijitu correlation:** White/yang vs black/yin; the enclosing circle

**Current math seat:**
```
ρ̄(η) = (1/2π) ∫₀²π ρ(χ,η) dχ = diag(cos²η, sin²η)

S(ρ̄(η)) = −cos²η log(cos²η) − sin²η log(sin²η)

b₀ = sign(cos(2η)) = sign(r_z)
```

Upper hemisphere (`η < π/4`): N-terrains / white / yang
Lower hemisphere (`η > π/4`): S-terrains / black / yin
Clifford threshold (`η = π/4`): maximum entropy

**Strongest candidate functional (open):**
```
Φ₀(ρ_AB) = −Σ_r w_r S(A_r|B_r)_ρ = Σ_r w_r I_c(A_r > B_r)_ρ
```
where `I_c` = coherent information, `S(A|B)` = conditional entropy.

**What's settled:** Something entropy-like drives the engine. The torus latitude η is a natural seat. The N/S terrain split is real.

**What's open:** The bridge Ξ that maps geometry to a bipartite cut state ρ_AB. Without that bridge, Axis 0 is a scalar readout, not the full functional. This is the single biggest open problem.

**Different ways to think about it:**
- Thermodynamic: hot core (N-terrains, high entropy region) vs cold shell (S-terrains, low entropy region)
- Information-theoretic: high mutual information vs low mutual information across a cut
- Game-theoretic: the external drive/environment that the engines operate within
- Homeostasis vs allostasis (from the owner's framing — but this is interpretation, not math)

### Axis 1 — Branch split (derived)

**What it splits:** {Se, Ni} vs {Ne, Si}

**IGT correlation:** {LoseWin, LoseLose} vs {WinLose, WinWin}

**Taijitu correlation:** Black dot in white teardrop vs white dot in black teardrop

**Current math:**
```
{Se, Ni}: proper dissipative / CPTP dynamics
{Ne, Si}: unitary / Hamiltonian-dominated dynamics
```

**Status:** Derived from Axis 0 × Axis 2. Not primitive. The branch split is real but it doesn't add independent information beyond the two axes it derives from.

**Different ways to think about it:**
- Isothermal (Se, Ni: dissipation dominant) vs adiabatic (Ne, Si: unitary dominant)
- Open channels vs closed channels
- Information-losing vs information-preserving

### Axis 2 — Representation frame

**What it splits:** {Se, Ne} vs {Ni, Si} — direct frame vs conjugated frame

**IGT correlation:** {LoseWin, WinLose} vs {WinWin, LoseLose}

**Taijitu correlation:** Teardrops vs dots

**Current math:**
```
Direct frame:      ρ̃(u) = ρ(u)
Conjugated frame:  ρ̃(u) = V_s(u)† ρ(u) V_s(u)

V_s(u) = exp(−iH_s u)
H_L = +H₀  (left sheet)
H_R = −H₀  (right sheet)
```

The conjugated frame introduces a connection term `K = iV†V̇` that changes the effective dynamics.

**Status:** Strong lower-stack anchor. The direct/conjugated split is real math — it's the difference between working in the lab frame vs the co-rotating frame. This determines which operators are native to which terrains.

**Different ways to think about it:**
- Lab frame vs rotating frame
- Stationary observer vs co-moving observer
- Simple dynamics vs dynamics with a gauge connection

### Axis 3 — Loop class

**What it splits:** Fiber loop (inner) vs lifted-base loop (outer)

**Taijitu correlation:** Tail-chasing inner vs fat-tip-chasing outer

**Current math:**
```
Fiber loop:       γ_f(u) = ψ_s(φ₀+u, χ₀; η₀)
                  ρ_f(u) = ρ_f(0)  [density stationary]

Lifted-base loop: γ_b(u) = ψ_s(φ₀−cos(2η₀)u, χ₀+u; η₀)
                  ρ_b(u) = |γ_b(u)⟩⟨γ_b(u)|  [density traversing]

Horizontal condition: A(γ̇_b) = 0
where A = −iψ†dψ = dφ + cos(2η) dχ  (Hopf connection)
```

**Status:** Current strongest reading is inner/fiber vs outer/base. Older readings (L/R chirality, Type1/Type2 topology inversion, flux in/out) are live alternatives but should not overwrite inner/outer without a discriminator test.

**Different ways to think about it:**
- Phase loop vs density loop
- The loop where nothing changes (fiber) vs the loop where everything changes (base)
- Inner process vs outer process
- In the IGT: small outcome (inner, lowercase) vs big outcome (outer, UPPERCASE)
- In Szilard/Carnot: possibly one maps to the isothermal step, the other to the adiabatic step

### Axis 4 — Loop order (inductive vs deductive)

**What it splits:** The order in which unitary (U) and dissipative (E) steps compose.

**Taijitu correlation:** Clockwise vs counterclockwise spin (assignment open)

**Current math:**
```
Deductive:  Φ_D = U ∘ E ∘ U ∘ E     (unitary first)
Inductive:  Φ_I = E ∘ U ∘ E ∘ U     (dissipative first)

Stronger form:
Φ_D = e^{τ_R L_R} e^{τ_C L_C}
Φ_I = e^{τ_C L_C} e^{τ_R L_R}

First-order difference ≈ τ_R τ_C [L_R, L_C]   (the commutator)
```

The difference between inductive and deductive is **literally the commutator**. If the generators commute, the two orders are the same and the axis collapses. This is N01 (noncommutation) made visible.

**Loop family correlation:**
```
Deductive family: FeTi (loop order Se → Ne → Ni → Si)
Inductive family: TeFi (loop order Se → Si → Ni → Ne)
```

**Status:** Runtime math is strong. Which taijitu spin direction maps to which order is open.

**Different ways to think about it:**
- Theory-first (deductive: rotate then measure) vs data-first (inductive: measure then rotate)
- Hypothesis → test → hypothesis → test vs observation → model → observation → model
- The traditional scientific method can run in both directions
- Each engine has one loop of each type — the difference is which is inner vs outer

**What's not defined yet in pure QIT:** Axis 4 maps clearly to deduction vs induction in the owner's model. But what exactly is the QIT object for "deduction" vs "induction"? The composition order of generators is the current best answer, but the full story connecting this to information processing is open.

### Axis 5 — Operator family

**What it splits:** {Ti, Te} dephasing/projection vs {Fi, Fe} unitary rotation

**IGT correlation:** Dephasing-class tokens vs rotation-class tokens. Competitive (T) vs cooperative (F).

**Taijitu correlation:** S-curve/lobe properties (open)

**Current math:**

| Family | Operators | Math class | Information effect |
|---|---|---|---|
| Dephasing (T) | Ti: z-pinching, Te: x-pinching | CPTP, non-unitary, semigroup | Irreversible: kills coherence, loses information |
| Rotation (F) | Fi: x-rotation, Fe: z-rotation | Unitary, group | Reversible: moves coherence, preserves information |

```
Ti generator: L_Ti(ρ) = (κ₁/2)(σ_z ρ σ_z − ρ)     [gradient/Lindblad/semigroup]
Te generator: L_Te(ρ) = (κ₂/2)(σ_x ρ σ_x − ρ)     [gradient/Lindblad/semigroup]
Fi generator: L_Fi(ρ) = −i[(ω₃/2)σ_x, ρ]            [spectral/Hamiltonian/group]
Fe generator: L_Fe(ρ) = −i[(ω₄/2)σ_z, ρ]            [spectral/Hamiltonian/group]
```

**Status:** The operator/generator split is strong. The taijitu S-curve/lobe overlay is open.

**Different ways to think about it:**
- Information destruction (T) vs information rotation (F)
- Entropy-increasing (T: dephasing) vs entropy-preserving (F: rotation)
- Low entropy operators vs high entropy operators (in the IGT sense)
- Gradient algebra (finite differences, semigroups, non-invertible) vs spectral algebra (eigenvalues, groups, invertible)
- One earlier working name: "finite gradient algebra vs finite spectral algebra" (FGA vs FSA) — slightly made up terms but pointing at a real mathematical distinction
- Literal hot (T: entropy production) vs cold (F: entropy preservation) — but this is NOT the same as Axis 0 (which is more like homeostasis vs allostasis)

### Axis 6 — Composition order / sidedness

**What it splits:** Operator-first `Φ_T(O(ρ))` vs terrain-first `O(Φ_T(ρ))`

**IGT correlation:** Judging-first tokens vs perceiving-first tokens; up vs down

**Taijitu correlation:** Up vs down reading

**Current math:**
```
b₆ = −b₀ · b₃

Left action:  L_A(ρ) = Aρ
Right action: R_A(ρ) = ρA

Channel precedence: Φ_T ∘ O  vs  O ∘ Φ_T

Liouville separation: I ⊗ A  vs  Aᵀ ⊗ I
```

**Status:** Strong math and symbolic alignment. The noncommutator
```
Δ_{T,O}(ρ) = Φ_T(O(ρ)) − O(Φ_T(ρ))
```
is the directly measurable signal. JAX/Julia parity confirmed at 1e-10.

**Different ways to think about it:**
- Act then observe vs observe then act
- Transform the state, then let the environment act vs let the environment act, then transform
- In the IGT: which strategy placement comes from which composition direction

---

## Part III: The Geometry/Entropy Landscape To Explore

### 6. Geometry options

All of these are real mathematical objects that could serve as carrier geometry. The constraints narrow the field but don't pick a unique winner.

| Geometry | What it is | Why it might be right | Current status |
|---|---|---|---|
| S³ / SU(2) | Unit spinors in C² | Minimal carrier candidate under F01+N01; natural double cover | Active working carrier |
| Hopf fibration S³ → S² | Fiber bundle with U(1) fiber | Natural decomposition of S³; gives inner/outer loop structure | Active |
| Nested Hopf tori | T_η foliating S³ | Parameterize the carrier; give Axis 0 its seat | Active |
| Quaternions H | Unit quaternions ≅ SU(2) | Same as S³ but with explicit multiplication; natural for rotations | Aligned, needs explicit use |
| Clifford algebras Cl(n) | Generated by anticommuting elements | Very strong candidate under the constraints; Pauli matrices are Cl(3) generators | Very likely needed |
| Bloch sphere S² | Image of Hopf map | Natural but **may lose too much information** — no phase | Possibly excluded |
| PEPS2D / Hopfield bonds | Tensor network as geometry | Current scratch carrier; bonds = geometry surface | Could be wrong |
| G₂ | Exceptional Lie group, 14-dim | Relevant to 7 imaginary octonion units; 7 axes might connect | To explore |
| Spin(7) | Double cover of SO(7) | 7-axis system on a 7D carrier structure | To explore |
| General G-structures | Reduced structure groups on the frame bundle | The "allowed geometry on M(C)" could be a G-structure | To explore |

### 7. Entropy options

| Entropy | Formula | What it measures | Where it might appear |
|---|---|---|---|
| von Neumann | `S(ρ) = −Tr(ρ log ρ)` | Total mixedness | Axis 0 seat, general entropy drive |
| Conditional entropy | `S(A|B) = S(ρ_AB) − S(ρ_B)` | Residual uncertainty of A given B (can be negative for quantum states) | Axis 0 functional |
| Coherent information | `I_c(A>B) = −S(A|B) = S(ρ_B) − S(ρ_AB)` | Quantum channel capacity direction | Axis 0 strongest candidate |
| Mutual information | `I(A:B) = S(ρ_A) + S(ρ_B) − S(ρ_AB)` | Total correlations | Axis 0 diagnostic |
| Rényi entropies | `S_α(ρ) = (1/(1−α)) log Tr(ρ^α)` | Family parameterized by α | Alternative entropy measures |
| Relative entropy | `S(ρ‖σ) = Tr(ρ(log ρ − log σ))` | Distinguishability of states | Connects to F01 directly |
| Min-entropy | `H_∞(ρ) = −log λ_max(ρ)` | Worst-case predictability | Operational under F01 |
| Entropy production rate | `σ = dS/dt ≥ 0` | Irreversibility rate | Axis 5 T vs F split |
| Purity | `Tr(ρ²)` | Not an entropy but related | How mixed the state is |

### 8. Classical engines to learn from (and transcend)

The owner's model draws from Carnot and Szilard engines but needs pure QIT versions with **no classical math**.

| Engine | What it is | What it teaches | QIT version needed |
|---|---|---|---|
| **Carnot** | 4-stage: isothermal expansion → adiabatic expansion → isothermal compression → adiabatic compression | Maximum efficiency; the 4-stage cycle structure | Quantum Carnot with density states, CPTP stages, and entropy as the working substance |
| **Szilard** | 1-bit engine: measure → extract work → reset | Information-to-work conversion; Landauer's principle | Quantum Szilard with QIT measurement, work extraction as a channel, and erasure as an explicit entropy cost |
| **Both stacked** | The owner's target: 2 Szilard-like engines, one inductive, one deductive, dual-stacked | The actual QIT engine target | Not yet built |

The key insight from the owner: these classical engines already contain deep patterns about the 4-stage structure, the inner/outer loop structure, hot/cold reservoirs, and work/information conversion. The IGT patterns map onto these engine stages. But the actual engine must be pure QIT — no classical thermodynamics, no classical information theory, no classical probability.

---

## Part IV: The IGT Strategy Grammar

### 9. The 4-ring

```
{win, lose} × {WIN, LOSE} = {−1, +1}²

Si(WIN, win) ──── Ne(WIN, lose)
      │                  │
Se(LOSE, win) ──── Ni(LOSE, lose)
```

Two independent binary axes:
- Small (lowercase): win/lose — inner loop outcome
- Large (UPPERCASE): WIN/LOSE — outer loop outcome

### 10. The 2 traversals (proven: only 2 exist)

| Pattern | Direction | Terrain order | Axis flip sequence |
|---|---|---|---|
| Inductive (CW) | Se → Si → Ni → Ne | Large → small → Large → small |
| Deductive (CCW) | Se → Ne → Ni → Si | small → Large → small → Large |

### 11. The 4 operators

| Operator | Channel | Generator | Bloch map (scratch) | Class | Native terrains |
|---|---|---|---|---|---|
| Ti | `(1−q₁)ρ + q₁(P₀ρP₀+P₁ρP₁)` | `(κ₁/2)(σ_zρσ_z−ρ)` | `(λ₁x, λ₁y, z)`, λ₁=.69 | z-dephasing | Se, Ne (direct) |
| Te | `(1−q₂)ρ + q₂(Q₊ρQ₊+Q₋ρQ₋)` | `(κ₂/2)(σ_xρσ_x−ρ)` | `(x, λ₂y, λ₂z)`, λ₂=.73 | x-dephasing | Ni, Si (conjugated) |
| Fi | `U_x(θ)ρU_x(θ)†` | `−i[(ω₃/2)σ_x, ρ]` | `R_x(.41)r` | x-rotation | Se, Ne (direct) |
| Fe | `U_z(φ)ρU_z(φ)†` | `−i[(ω₄/2)σ_z, ρ]` | `R_z(−.37)r` | z-rotation | Ni, Si (conjugated) |

### 12. The 8 terrains

**Type 1 (left, flux IN, H = +H₀):**

| Terrain | Nickname | Generator | Scratch Bloch map |
|---|---|---|---|
| Se-in | Funnel | `ρ̇ = Σ D[L_k](ρ) − iε[H₀,ρ]` | `R_N(.13)(√.78x, √.78y, .78z+.22·.86)` |
| Ne-in | Vortex | `ρ̇ = −i[H₀,ρ] + ε Σ D[L_k](ρ)` | `.94 R_N(.47)r` |
| Ni-in | Pit | `ρ̇ = D[√γσ₋](ρ) − iε[H₀,ρ]` | `R_N(.09)(√.70x, √.70y, .70z−.30·.92)` |
| Si-in | Hill | `ρ̇ = −i[H_C,ρ]+Σκ_j(P_jρP_j−½{P_j,ρ})` | `R_{M_in}(.19)(P_{M_in}(r)+.58(r−P_{M_in}(r)))` |

**Type 2 (right, flux OUT, H = −H₀):**

| Terrain | Nickname | Generator | Scratch Bloch map |
|---|---|---|---|
| Se-out | Cannon | `ρ̇ = Σ D[L_k](ρ) + iε[H₀,ρ]` | `R_{−N}(.13)(√.76x, √.76y, .76z−.24·.86)` |
| Ne-out | Spiral | `ρ̇ = +i[H₀,ρ] + ε Σ D[L_k](ρ)` | `.94 R_{−N}(.47)r` |
| Ni-out | Source | `ρ̇ = D[√γσ₊](ρ) + iε[H₀,ρ]` | `R_{−N}(.09)(√.68x, √.68y, .68z+.32·.92)` |
| Si-out | Citadel | `ρ̇ = +i[H_C,ρ]+Σκ_j(P_jρP_j−½{P_j,ρ})` | `R_{M_out}(−.19)(P_{M_out}(r)+.55(r−P_{M_out}(r)))` |

What changes between types: Hamiltonian sign flips, rotation axis flips, z-attractor flips, jump operator flips (σ₋ → σ₊), projector frame rotates. **Different channels, not relabelings.**

### 13. The 8 signed operators

| Signed op | Base | Composition | Bloch form | Native terrains |
|---|---|---|---|---|
| Ti↑ | z-dephase | Φ_T(Ti(ρ)) | `T(λ₁x, λ₁y, z)` | Se-in, Ne-out |
| Ti↓ | z-dephase | Ti(Φ_T(ρ)) | `(λ₁T_x, λ₁T_y, T_z)` | Ne-in, Se-out |
| Te↑ | x-dephase | Φ_T(Te(ρ)) | `T(x, λ₂y, λ₂z)` | Ni-in, Si-out |
| Te↓ | x-dephase | Te(Φ_T(ρ)) | `(T_x, λ₂T_y, λ₂T_z)` | Si-in, Ni-out |
| Fi↑ | x-rotation | Φ_T(Fi(ρ)) | `T(R_x(θ)r)` | Ne-in, Se-out |
| Fi↓ | x-rotation | Fi(Φ_T(ρ)) | `R_x(θ)T(r)` | Se-in, Ne-out |
| Fe↑ | z-rotation | Φ_T(Fe(ρ)) | `T(R_z(φ)r)` | Si-in, Ni-out |
| Fe↓ | z-rotation | Fe(Φ_T(ρ)) | `R_z(φ)T(r)` | Ni-in, Si-out |

### 14. The 2 engine types

| Property | Type 1 (left) | Type 2 (right) |
|---|---|---|
| Chirality | left Weyl | right Weyl |
| Hamiltonian | `H_L = +H₀` | `H_R = −H₀` |
| Flux | IN | OUT |
| Outer loop | deductive: Se→Ne→Ni→Si | inductive: Se→Si→Ni→Ne |
| Inner loop | inductive: Se→Si→Ni→Ne | deductive: Se→Ne→Ni→Si |
| Outer family | FeTi | TeFi |
| Inner family | TeFi | FeTi |

**Type 1 chart:**

| Step | Terrain | Outer token | Outer math | Outer | Inner token | Inner math | Inner |
|---|---|---|---|---|---|---|---|
| 1 | Se-in | TiSe | Se-in(Ti(ρ)) | LOSE | SeFi | Fi(Se-in(ρ)) | win |
| 2 | Ne-in | NeTi | Ti(Ne-in(ρ)) | WIN | FiNe | Ne-in(Fi(ρ)) | lose |
| 3 | Ni-in | NiFe | Fe(Ni-in(ρ)) | LOSE | TeNi | Ni-in(Te(ρ)) | lose |
| 4 | Si-in | FeSi | Si-in(Fe(ρ)) | WIN | SiTe | Te(Si-in(ρ)) | win |

**Type 2 chart:**

| Step | Terrain | Outer token | Outer math | Outer | Inner token | Inner math | Inner |
|---|---|---|---|---|---|---|---|
| 1 | Se-out | FiSe | Se-out(Fi(ρ)) | WIN | SeTi | Ti(Se-out(ρ)) | lose |
| 2 | Si-out | TeSi | Si-out(Te(ρ)) | WIN | SiFe | Fe(Si-out(ρ)) | win |
| 3 | Ni-out | NiTe | Te(Ni-out(ρ)) | LOSE | FeNi | Ni-out(Fe(ρ)) | lose |
| 4 | Ne-out | NeFi | Fi(Ne-out(ρ)) | LOSE | TiNe | Ne-out(Ti(ρ)) | win |

### 15. The 16 strategy placements by quadrant

**Casing rule:** WIN/LOSE = outer/major loop; win/lose = inner/minor loop. Casing ≠ position.

**Position rule:** 1st position = dephasing placement; 2nd position = rotation placement. Fixed.

**What flips between engine types:** which casing (big/small) appears in which position.

#### Se = LoseWin

| Label | Engine | 1st token | 1st math | 1st | 2nd token | 2nd math | 2nd |
|---|---|---|---|---|---|---|---|
| **LOSE**win | T1 | TiSe | Se-in(Ti(ρ)) | LOSE | SeFi | Fi(Se-in(ρ)) | win |
| lose**WIN** | T2 | SeTi | Ti(Se-out(ρ)) | lose | FiSe | Se-out(Fi(ρ)) | WIN |

#### Ne = WinLose

| Label | Engine | 1st token | 1st math | 1st | 2nd token | 2nd math | 2nd |
|---|---|---|---|---|---|---|---|
| **WIN**lose | T1 | NeTi | Ti(Ne-in(ρ)) | WIN | FiNe | Ne-in(Fi(ρ)) | lose |
| win**LOSE** | T2 | TiNe | Ne-out(Ti(ρ)) | win | NeFi | Fi(Ne-out(ρ)) | LOSE |

#### Ni = LoseLose

| Label | Engine | 1st token | 1st math | 1st | 2nd token | 2nd math | 2nd |
|---|---|---|---|---|---|---|---|
| lose**LOSE** | T1 | TeNi | Ni-in(Te(ρ)) | lose | NiFe | Fe(Ni-in(ρ)) | LOSE |
| **LOSE**lose | T2 | NiTe | Te(Ni-out(ρ)) | LOSE | FeNi | Ni-out(Fe(ρ)) | lose |

#### Si = WinWin

| Label | Engine | 1st token | 1st math | 1st | 2nd token | 2nd math | 2nd |
|---|---|---|---|---|---|---|---|
| win**WIN** | T1 | SiTe | Te(Si-in(ρ)) | win | FeSi | Si-in(Fe(ρ)) | WIN |
| **WIN**win | T2 | TeSi | Si-out(Te(ρ)) | WIN | SiFe | Fe(Si-out(ρ)) | win |

### 16. The hexagram scaffold (proposal only)

| Line | Axis | Math role |
|---|---|---|
| 1 (bottom) | Axis 6 | composition order |
| 2 | Axis 5 | operator family |
| 3 | Axis 3 | loop class |
| 4 | Axis 4 | inductive/deductive |
| 5 | Axis 1 | branch split |
| 6 (top) | Axis 2 | representation frame |
| external | Axis 0 | drive through the space |

Lower trigram (lines 1-3): order × family × loop = "how the operator acts"
Upper trigram (lines 4-6): direction × branch × frame = "what kind of dynamics"

2⁶ = 64 structural states. 8 terrains × 8 signed operators = 64. These are the same count from two different views — whether they are the same object is a testable claim.

---

## Part V: What Needs Exploring

### 17. Near-term sim targets

| Target | What to test | Math needed | Status |
|---|---|---|---|
| 720° spinor loop | First 360° ≠ second 360° under SU(2) carrier | Explicit spinor double-cover sim | Not started |
| Quaternion carrier | Rewrite the Hopf/S³ carrier using explicit quaternion multiplication | Unit quaternions ≅ SU(2) | Not started |
| Clifford algebra carrier | Realize operators using Clifford generators | Cl(3,0) contains Pauli algebra | Very likely needed |
| Carnot QIT engine | 4-stage quantum Carnot with density states and CPTP channels | Already have finite-map probes; need pure QIT version | Candidate probes exist |
| Szilard QIT engine | Measurement → work extraction → erasure as explicit channels | Need quantum measurement channel + Landauer erasure | Not started |
| Dual-stacked engine | 2 Szilard-like engines, inductive + deductive, on 720° spinor | The full target | Far out |
| Axis 0 bridge/cut | Map geometry to bipartite ρ_AB; compute coherent information | Need Ξ bridge map | Open — biggest gap |
| Axis 4 discriminator | Does CW/CCW taijitu predict Φ_D/Φ_I? | Symbol-to-runtime test with controls | Ready to test |
| Axis 5 S-curve | Does taijitu S-curve/lobe predict T/F operator split? | Symbol-to-operator test | Ready to test |
| G₂ / Spin(7) structure | Can the 7-axis system be realized as a G₂ or Spin(7) geometry? | Lie algebra computation | Exploration |
| Bloch sphere exclusion test | Does M(C) require more structure than S² carries? | Information-loss test under Hopf projection | Needs designing |
| Anti-commutation emergence | Do the constraints force anti-commutation relations at some layer? | Starting from N01, look for Clifford-like structure | Exploration |
| Spinor network on carrier | Build actual spinor network (not just single spinor) on the S³ carrier | Multi-site spinor geometry | Not started |

### 18. What the owner wants (not to drift from)

- Build the dual-stacked QIT engine. That is the goal.
- The IGT patterns are the map to the engine structure — not jargon, not metaphor, a real structural pattern.
- Process docs one by one to find patterns to test and ideas to explore.
- Build sims layer by layer. Exact math. Test what's right rather than assert it.
- Explore many branches. The goal is QIT engines. The path is not fixed.
- No canon until it's done. Space to try things and see what works.
- The ratchet is the method. Start from constraints. Minimal leaps. Build up.

---

## Sources

- `Personality theory._.xlsx`
- `JUNGIAN_FUNCTIONS_AND_IGT_EXPLICIT_MATH_GEOMETRY_MAP copy.md`
- `AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md`
- `Formal constraints and geometry .md`
- `terrain rosetta strong math.md`
- `apple axes terrain operator math.md`
- `TAIJITU_AXES_0_6_EXPLICIT_SYMBOLIC_LAYER copy.md`
- `TAIJITU_PROBE_RECONCILIATION_CARD copy.md`
- `INTENT_SUMMARY copy.md`
- Codex2 parity run results
- Cross-ref: `qit-igt-engine-valid-results-and-running-guide-2026-06-05.md`

---

## Appendix: Multi-Model Tribunal (2026-06-04)

Three models independently analyzed this framework. Same prompt, no anchoring.

**Models:** Grok 4.3 (xAI), Gemini 2.5 Pro (Google), Codex2/GPT-5.5 (OpenAI via codex exec)

### Unanimous

- Ξ bridge is the #1 gap — all three
- Finite noncommutative algebra is strongly constrained — all three
- Axis 0 is the weakest axis — all three
- Axes 3, 5, 6 are the strongest — all three
- 720° is standard SU(2), not novel — all three
- The ratchet method itself is the genuinely novel element — all three

### Split

| Point | Grok 4.3 | Gemini 2.5 Pro | Codex2 |
|---|---|---|---|
| Are spinors selected? | No | Yes if ℂ² survives the carrier tests | Only if phase is load-bearing |
| Is L/R chirality selected? | No | No | Left/right action natural; Weyl extra |
| Best first test | Extremal channel spectra | Ξ with purification candidate | Full 16-token ablation with controls |
| Axis 1 risk | Downstream only | Contingent on Ax0 | Risks duplicating Ax5 |

### Sharpest challenges from each

**Grok 4.3:** "Check whether Hopf-torus foliation + L/R produces correlation spectra outside the convex hull of generic CPTP maps. If not, the geometric superstructure adds no predictive power."

**Gemini 2.5 Pro:** "Test Ξ via purification: path γ_f should give constant entanglement, γ_b should give varying. If all paths give similar profiles regardless of Ξ choice, the geometry-to-information link is broken."

**Codex2:** "720° behavior disappears under ρ = |ψ⟩⟨ψ| unless the engine keeps lifted phase/path/interference data. Degenerate probes can erase all order gaps."

### Owner correction on tribunal

All three models treated the L/R Weyl split as "imposed from physics" or "extra structure." This is wrong within the framework. The L/R split is a ratchet step: N01 forces that left and right action are distinct, SU(2) on S³ gives two natural orientations, and presuming the least selects the two-sheet realization as the simplest structure that preserves the noncommutative order information. This is not an import — it's what survives.

The tribunal's blind spot reveals a documentation gap: **the ratchet derivation for each step must be explicit in the doc, not just the endpoint.** The doc has been updated to show killed alternatives at each step (§5).
