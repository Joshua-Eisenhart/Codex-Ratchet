# UPLOAD BUNDLE 2 — Rosetta + Engines (pre‑IGT core)

Consolidated for easy re‑boot.

Includes: Rosetta Stone, Engine spec, Axis‑1/2 dual‑stack Szilard, Hexagram microstate encoding.


---

# SOURCE: 03_ROSETTA/ROSETTA_STONE.md

# ROSETTA STONE (v0.9, QIT + Game Theory + Mimetic Meme Manifolds)

> **Canon Pack note:** This file is the stable-name copy of `03_ROSETTA/ROSETTA_STONE.md`. Keep it QIT-native; do not drift into personality typing.


**Terminology patch (2025‑12‑23):** preferred term is **mimetic meme manifold** (Girard + Dawkins).
Legacy alias: “mimetic manifold” may appear in salvage text; treat as the same object unless explicitly distinguished.

This Rosetta is **not** the “engine schedule.”  
It’s the **dictionary**: symbols → clean QIT objects.

---

## 0) Minimal QIT substrate

- A system is a finite‑dimensional Hilbert space \(\mathcal{H}\) with \(\dim(\mathcal{H})=d\).
- A state is a density matrix \(\rho \succeq 0\), \(\mathrm{Tr}(\rho)=1\).
- A **channel** (topology map) is a CPTP map \(\mathcal{P}\).
- An **instrument / operator family map** is modeled (for now) as a CPTP map \(\mathcal{J}\).
  - (We can later upgrade \(\mathcal{J}\) to a full instrument \(\{\mathcal{J}_k\}\) if we explicitly want outcome records.)

Composition notation:
\[
(\mathcal{A}\circ \mathcal{B})(\rho) \;=\; \mathcal{A}(\mathcal{B}(\rho)).
\]

---

## 1) Canon quantities (metrics used in sims)

Von Neumann entropy:
\[
S(\rho) = -\mathrm{Tr}(\rho \log \rho).
\]

Negentropy potential (toy “work‑capacity” proxy):
\[
\Phi(\rho)=\log_2(d) - S(\rho).
\]

(If we add a Hamiltonian \(H\), we can also track \(E(\rho)=\mathrm{Tr}(H\rho)\).)

---


### 1.3 Axis‑0 VN‑potential polarity (N/S) — and why it looks like an entropy‑gradient

**Canon lock:** Axis‑0 is the **polarity/orientation** of VN information‑potential relative to max‑mix.  
It is **not** the same as operator sign, and it is **not** “high vs low entropy.”

Let \(\tau = I/d\). Define the VN information‑potential:
\[
\Phi(\rho) \equiv D(\rho\Vert \tau) = \log d - S(\rho)
\]

Axis‑0 sets a *signed orientation* for this potential:
\[
\Phi^{(A0)}(\rho)=
\begin{cases}
+\Phi(\rho) & A0=N\\
-\Phi(\rho) & A0=S
\end{cases}
\]


**Operational hook in the current sim harness (pre‑IGT):**
- `axis0_pole ∈ {N,S}` can be passed into the **Ni (cold reset)** topology map.
  - `S` keeps the baseline cold reference (`τ_cold = Gibbs(β_cold, H=+Z)`)
  - `N` flips the pole (`τ_cold = Gibbs(β_cold, H=−Z)`)
- Separately, some screening runners use an **axis0_mix_lambda** (JK‑fuzz) that mixes the initial state toward `I/d`.

These are *minimal* operationalizations meant to expose measurable axis‑0 sensitivities without committing to a full spacetime field model yet.
**Why “entropy‑gradient” keeps showing up:**  
Once the substrate has adjacency (ring/checkerboard/Hopf‑lattice), \(\Phi\) becomes a scalar field \(\Phi(x)\) and you can form discrete gradients \(\Phi(x)-\Phi(y)\) on edges.  
That derived object is the “Bit‑0 entropy‑gradient battery” concept — but the canon axis is still the polarity **N/S**, not the gradient itself.

**JK‑fuzz bridge (pre‑IGT):**  
Treat “JK‑fuzz” as a boundary possibility‑field (probability‑vector DOFs on the shell), while Axis‑0 is the polarity used to interpret radial potential flux between nested shells.

(See: `05_FOUNDATIONS/AXIS0_JKFUZZ_BRIDGE.md`.)


## 2) Axis‑6 (precedence) is canon‑locked

**Axis‑6 = precedence (token order).**  
It is *not* induction/deduction and it is *not* clockwise/counterclockwise.

### 2.1 Definition
Let \(\mathcal{P}\) be a topology map and \(\mathcal{J}\) be an operator family map.

- **Down mode** (Topo→Op):  
  \[
  \rho' = (\mathcal{J}\circ \mathcal{P})(\rho)
  \]
- **Up mode** (Op→Topo):  
  \[
  \rho' = (\mathcal{P}\circ \mathcal{J})(\rho)
  \]

### 2.2 Token order rule (hard lock)
- Token `NeTi` **means** apply \(\mathcal{P}_{Ne}\) then \(\mathcal{J}_{Ti}\)  
  ⇒ Down mode (Topo→Op)
- Token `TiNe` **means** apply \(\mathcal{J}_{Ti}\) then \(\mathcal{P}_{Ne}\)  
  ⇒ Up mode (Op→Topo)

This is the only meaning of “↓/↑” in this Rosetta.

---

## 3) The 4 topologies (Ne, Si, Se, Ni)

Each topology is a **map class** (a distinct QIT action type).  
Parameters can be tuned later; the class is what matters.

### 3.1 Map class definitions (canonical toy contract)

#### (Ne) — unitary transport
A reversible, entropy‑preserving transport:
\[
\mathcal{P}_{Ne}(\rho) = U_{Ne}\,\rho\,U_{Ne}^\dagger
\]
where \(U_{Ne}\) is unitary (e.g., \(U_{Ne}=e^{-i\theta \sigma_y/2}\) for one qubit).

#### (Si) — pinching / dephasing
A basis‑stabilizing channel that kills coherence in a preferred basis:
\[
\mathcal{P}_{Si}(\rho) = (1-p)\rho + p\,\Pi(\rho)
\]
where \(\Pi(\rho)=\sum_k P_k \rho P_k\) is “pinching” in some projector set \(\{P_k\}\).

For one qubit in the Z basis:
\[
\Pi_Z(\rho)=P_0\rho P_0 + P_1\rho P_1,\quad P_0=|0\rangle\langle 0|,\;P_1=|1\rangle\langle 1|.
\]

#### (Se) — hot mixing / “heat‑in contact”
A non‑unital mixing toward a “hot” reference state \(\tau_{hot}\):
\[
\mathcal{P}_{Se}(\rho) = (1-\gamma_{Se})\rho + \gamma_{Se}\,\tau_{hot}
\]
where \(\tau_{hot}\) is typically a Gibbs state \( \tau_{hot}\propto e^{-\beta_{hot} H}\) with small \(\beta_{hot}\).

#### (Ni) — cold reset / erasure‑leg mixing
A non‑unital mixing toward a “cold” reference state \(\tau_{cold}\):
\[
\mathcal{P}_{Ni}(\rho) = (1-\gamma_{Ni})\rho + \gamma_{Ni}\,\tau_{cold}
\]
with \(\beta_{cold}>\beta_{hot}\).

**Important:** Se and Ni are *not* “the same math twice”; they are the same *template* but with different fixed points and coupling strengths, giving different thermodynamic meaning in sims.

---

## 4) The 4 operator families (Ti, Te, Fi, Fe)

Again: operator families are QIT maps.  
We keep Jung labels as *names*, but the math stays clean.

### 4.1 Canon toy contract (chosen to enforce non‑commutation)
We want at least one pair that does not commute so Axis‑6 matters.

#### (Ti) — Z‑pinching instrument‑like
\[
\mathcal{J}_{Ti}(\rho) = (1-q)\rho + q\,\Pi_Z(\rho).
\]

#### (Te) — X‑pinching instrument‑like (non‑commutes with Ti)
\[
\mathcal{J}_{Te}(\rho) = (1-q)\rho + q\,\Pi_X(\rho)
\]
where \(\Pi_X\) pinches in the X basis (projectors onto \(|+\rangle,|-\rangle\)).

#### (Fi) — unitary feedback‑like rotation about X
\[
\mathcal{J}_{Fi}(\rho) = U_{Fi}\,\rho\,U_{Fi}^\dagger,\quad U_{Fi}=e^{-i\varphi \sigma_x/2}.
\]

#### (Fe) — unitary feedback‑like rotation about Z
\[
\mathcal{J}_{Fe}(\rho) = U_{Fe}\,\rho\,U_{Fe}^\dagger,\quad U_{Fe}=e^{-i\varphi \sigma_z/2}.
\]

---

## 5) The 8 operator modes (Ti↓/↑, Te↓/↑, Fi↓/↑, Fe↓/↑)

Given an operator family \(\mathcal{J}_X\) and a topology \(\mathcal{P}_T\):

| Operator mode | Meaning | QIT action |
|---|---|---|
| \(X\downarrow\) | Topo→Op precedence | \(\rho'=(\mathcal{J}_X\circ\mathcal{P}_T)(\rho)\) |
| \(X\uparrow\) | Op→Topo precedence | \(\rho'=(\mathcal{P}_T\circ\mathcal{J}_X)(\rho)\) |

So “↓/↑” is not an intrinsic property of Ti/Te/Fi/Fe; it is **Axis‑6 composition order**.

---

## 6) The 8 terrains (topology × flow direction)

You want **8 terrains**:
\[
\text{Terrain} = (\text{Topology} \times \text{FlowDirection}) \in \{Ne1,Ne2,Si1,Si2,Se1,Se2,Ni1,Ni2\}.
\]

### 6.1 Minimal implementation (what the current sim already supports)
We implement “flow direction / handedness” as a parameterization of \(\mathcal{P}\):

- \(Ne1\): \(U_{Ne}=e^{-i\theta \sigma_y/2}\)
- \(Ne2\): \(U_{Ne}=e^{+i\theta \sigma_y/2}\) (sign flip)

For the other three topologies, \(1/2\) currently share parameters (this is a known simplification).  
Next sim pass can generalize this so **all four** topologies have distinct “1 vs 2” variants (e.g., by changing the basis pinched, temperature, or using recovery‑like channels).

### 6.2 Canon terrain table (current toy contract)
| Terrain | Base topology | QIT map class | “Direction” parameterization idea |
|---|---|---|---|
| Ne1 | Ne | unitary transport | \(U(\theta)\) |
| Ne2 | Ne | unitary transport | \(U(-\theta)\) |
| Si1 | Si | dephasing | pinch in Z (or basis \(B_1\)) |
| Si2 | Si | dephasing | pinch in rotated basis \(B_2\) *(next pass)* |
| Se1 | Se | hot mixing | toward \(\tau_{hot}^{(1)}\) |
| Se2 | Se | hot mixing | toward \(\tau_{hot}^{(2)}\) *(next pass)* |
| Ni1 | Ni | cold reset | toward \(\tau_{cold}^{(1)}\) |
| Ni2 | Ni | cold reset | toward \(\tau_{cold}^{(2)}\) *(next pass)* |

---

## 7) The 8×8 terrain×operator grid (what it is and what it is NOT)

### 7.1 What it IS
A **lookup table** for the 64 possible micro‑configurations:
\[
(\text{terrain}) \times (\text{operator mode}).
\]

It answers: “If the engine is at terrain \(Se2\) and we apply \(Te\uparrow\), what channel composition is that?”

### 7.2 What it is NOT
It is **not** the engine schedule, and it is not saying the engine visits all 64 states equally.

The schedule is a **path** through these 64 cells.

### 7.3 Full grid (labels only)
| Terrain \ Operator | Ti↓ | Ti↑ | Te↓ | Te↑ | Fi↓ | Fi↑ | Fe↓ | Fe↑ |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Ne1 | Ne1·Ti↓ | Ne1·Ti↑ | Ne1·Te↓ | Ne1·Te↑ | Ne1·Fi↓ | Ne1·Fi↑ | Ne1·Fe↓ | Ne1·Fe↑ |
| Ne2 | Ne2·Ti↓ | Ne2·Ti↑ | Ne2·Te↓ | Ne2·Te↑ | Ne2·Fi↓ | Ne2·Fi↑ | Ne2·Fe↓ | Ne2·Fe↑ |
| Si1 | Si1·Ti↓ | Si1·Ti↑ | Si1·Te↓ | Si1·Te↑ | Si1·Fi↓ | Si1·Fi↑ | Si1·Fe↓ | Si1·Fe↑ |
| Si2 | Si2·Ti↓ | Si2·Ti↑ | Si2·Te↓ | Si2·Te↑ | Si2·Fi↓ | Si2·Fi↑ | Si2·Fe↓ | Si2·Fe↑ |
| Se1 | Se1·Ti↓ | Se1·Ti↑ | Se1·Te↓ | Se1·Te↑ | Se1·Fi↓ | Se1·Fi↑ | Se1·Fe↓ | Se1·Fe↑ |
| Se2 | Se2·Ti↓ | Se2·Ti↑ | Se2·Te↓ | Se2·Te↑ | Se2·Fi↓ | Se2·Fi↑ | Se2·Fe↓ | Se2·Fe↑ |
| Ni1 | Ni1·Ti↓ | Ni1·Ti↑ | Ni1·Te↓ | Ni1·Te↑ | Ni1·Fi↓ | Ni1·Fi↑ | Ni1·Fe↓ | Ni1·Fe↑ |
| Ni2 | Ni2·Ti↓ | Ni2·Ti↑ | Ni2·Te↓ | Ni2·Te↑ | Ni2·Fi↓ | Ni2·Fi↑ | Ni2·Fe↓ | Ni2·Fe↑ |

---

## 8) Machine‑readable schema (CSV style)

This is the minimum row format you asked for (“axis toggles as metadata columns”):

```
terrain,topology,terrain_variant,operator_family,axis6_precedence,operator_mode,token_example,composition
Ne1,Ne,1,Ti,Down,Ti↓,NeTi,J_Ti ∘ P_Ne
Ne1,Ne,1,Ti,Up,Ti↑,TiNe,P_Ne ∘ J_Ti
...
```

(Engines doc maps which rows are actually visited by Type‑1 / Type‑2 schedules.)

---

## 9) Game Theory dialect layer (Classical GT ↔ IGT ↔ Engine tokens)

This section exists because your stated Rosetta goal is to translate **one structure** across multiple “languages,” including *classical game theory* and your *irrational game theory (IGT)* (case‑coded Win/Lose strings).

### 9.1 Base quadrant ↔ topology (uncased, hard lock)

These are the **four uncased** quadrant labels. They map to the **four base topologies**.

| Uncased quadrant (IGT) | Topology | Terrain intuition (engine) |
|---|---|---|
| **WinLose** | **Ne** | expansion / explore / “positive outcome for self vs other” |
| **WinWin** | **Si** | stabilize / cooperate / “mutual preserve” |
| **LoseWin** | **Se** | tradeoff / exploit / “other wins now / me later” |
| **LoseLose** | **Ni** | minimax survival / “accept loss to avoid total collapse” |

**No‑drift rule:** these four are **uncased only**. Casing is reserved for Type‑variant outer/inner roles (below).

### 9.2 Major/Minor size semantics (engine ↔ GT notation)

Engine locks establish:

- **Outer loop = major** (your older “Max / big”)  
- **Inner loop = minor** (your older “Min / small”)

So in the **case‑coded IGT strings**:
- **CAPS** (WIN/LOSE) = **outer/major/big**
- **lowercase** (win/lose) = **inner/minor/small**

### 9.3 Type‑variant strategy pairs (case‑coded labels, hard lock)

Each Type has **two tokens per quadrant**: one on the **outer/major** loop and one on the **inner/minor** loop.  
Your IGT label encodes that split by casing.

> Read rule: *the uppercase word in the label indicates the outer token; the lowercase word indicates the inner token* (the word order stays the quadrant’s Win/Lose order).

#### Type‑1 (Left / sink‑like, Weyl‑L)

| IGT variant label | Outer/major token | Inner/minor token |
|---|---|---|
| **WINlose** | NeTi | FiNe |
| **winWIN** | FeSi | SiTe |
| **LOSEwin** | TiSe | SeFi |
| **loseLOSE** | NiFe | TeNi |

#### Type‑2 (Right / source‑like, Weyl‑R)

| IGT variant label | Outer/major token | Inner/minor token |
|---|---|---|
| **winLOSE** | NeFi | TiNe |
| **WINwin** | TeSi | SiFe |
| **loseWIN** | FiSe | SeTi |
| **LOSElose** | NiTe | FeNi |

### 9.4 Full 16 macro‑token table (engine schedule metadata + IGT quadrant label)

This table is the “Rosetta join” between:
- engine wiring labels (Type / loop / major‑minor / Axis‑4),
- QIT tokens (TopoOp vs OpTopo giving Axis‑6 precedence),
- IGT quadrants (case‑coded variants).

| engine_type | loop | major_minor | axis4_stroke | IGT_quadrant | token | topology | operator_family | axis6_precedence |
|---|---|---|---|---|---|---|---|---|
| Type1 | inner | minor | induction | LOSEwin | SeFi | Se | Fi | DOWN |
| Type1 | inner | minor | induction | winWIN | SiTe | Si | Te | DOWN |
| Type1 | inner | minor | induction | WINlose | FiNe | Ne | Fi | UP |
| Type1 | inner | minor | induction | loseLOSE | TeNi | Ni | Te | UP |
| Type1 | outer | major | deduction | WINlose | NeTi | Ne | Ti | DOWN |
| Type1 | outer | major | deduction | winWIN | FeSi | Si | Fe | UP |
| Type1 | outer | major | deduction | LOSEwin | TiSe | Se | Ti | UP |
| Type1 | outer | major | deduction | loseLOSE | NiFe | Ni | Fe | DOWN |
| Type2 | inner | minor | deduction | winLOSE | TiNe | Ne | Ti | UP |
| Type2 | inner | minor | deduction | WINwin | SiFe | Si | Fe | DOWN |
| Type2 | inner | minor | deduction | loseWIN | SeTi | Se | Ti | DOWN |
| Type2 | inner | minor | deduction | LOSElose | FeNi | Ni | Fe | UP |
| Type2 | outer | major | induction | loseWIN | FiSe | Se | Fi | UP |
| Type2 | outer | major | induction | WINwin | TeSi | Si | Te | UP |
| Type2 | outer | major | induction | winLOSE | NeFi | Ne | Fi | DOWN |
| Type2 | outer | major | induction | LOSElose | NiTe | Ni | Te | DOWN |

### 9.5 Classical GT mapping (partly open)

The thread hard‑locks only this item:
- **minimin ↔ LoseLose ↔ Ni**

Other classical placements (maximax/maximin/minimax) have appeared, but were not globally locked in canon and must be treated as **OPEN / PROPOSED** until you pick one mapping.

### 9.6 Irrational Game Theory (IGT) in one sentence (what makes it “irrational”)

In your framing, IGT is “irrational” only relative to **local / immediate payoff**.  
It is “rational” relative to **future solvency / option‑space** (teleological ratchet lens).

So an IGT “policy” is closer to:
\[
\pi^* = \arg\max_\pi \; \mathbb{E}\Big[ W_T(\text{history})\Big]
\]
than to a single‑turn payoff maximizer.

(Exact form of \(W_T\) remains part of the Teleology layer; the Rosetta only needs the labels tied to tokens.)

---

## 10) Mimetic meme manifolds and Axes 7–12 (macro / “engine‑of‑engines” layer)

### 10.1 What “mimetic meme manifold” means in this system (as currently stated)

- A **single 6‑axis engine instance** is one system running a **Type‑1** or **Type‑2** loop on the QIT substrate.
- A **mimetic meme manifold** is the *macro* arena in which **many** such engine instances couple, imitate, synchronize, fork, and prune through language/meme dynamics (Girard mimesis + Dawkins memetics).
- Axes **7–12** are the (still **PROPOSED**) control‑axes for this coupling layer: they are intended to become **sim knobs** for “how engine instances influence one another” (strength, match, sync, boundary, meta‑cycle, etc.).

This is the point where “game theory” can become structural at the *collective* level — but it must not redefine any locked micro‑engine axes.

### 10.2 Mirror mapping: Axes 7–12 as macro analogs of Axes 1–6 (proposal present in thread)

One explicit draft mapping treats Axes 7–12 as the “mirror” of Axes 1–6:

| Micro axis | Micro meaning | Macro axis | Macro meaning (draft) |
|---|---|---|---|
| 1 | Coupling (bath legality) | 7 | Barrier / gate (match gate) |
| 2 | Chart (closed/open) | 8 | Topology (base/fiber) |
| 3 | Chirality (Type 1/2) | 9 | Match (parallel/contra) |
| 4 | Stroke (deduce/induce) | 10 | Sync (entangle/jump) |
| 5 | Texture (lines/waves) | 11 | Ratio (symmetric/asymmetric; hierarchy) |
| 6 | Precedence (order) | 12 | Meta‑cycle (resonant/dissonant; era/zeitgeist) |

Status: **PROPOSED** until you lock final names/values.

### 10.3 Alternate “12‑bit” naming scheme for 7–12 (proposal present in thread)

A second draft names 7–12 in more explicitly mimetic/selection terms:

- **Axis‑7 Active level:** coarse (macro meme scale) vs fine (micro‑habit scale)  
- **Axis‑8 Contagion:** constrain (deductive mimic constraint) vs release (inductive mimic freedom)  
- **Axis‑9 Measurement:** soft observe (weak group‑observation) vs hard dephase (strong enforcement)  
- **Axis‑10 Coupling:** base group (shared norm field) vs fiber ring (tight contagion ring)  
- **Axis‑11 Boundary:** pre‑selection (open futures) vs post‑selection (fixed canon / founder effect)  
- **Axis‑12 Symmetry:** isotropy (no preferred meme direction) vs anisotropy (cultural chirality / polarization)

Status: **PROPOSED** until consolidated with 10.2.

### 10.4 How this plugs into the Engine + IGT layer (minimal, no drift)

**Minimal integration rule (safe):**

- Keep Axes **0–6** as the **single‑engine** definition space (locked).
- Treat Axes **7–12** as a **second layer** that *couples engine instances* (macro manifold dynamics).

Then:

- The **base quadrants** (WinWin / WinLose / LoseWin / LoseLose) stay tied to the **single‑engine topologies** (Si / Ne / Se / Ni).
- The **IGT variants** (WINlose, winWIN, etc.) remain exactly what they are elsewhere in Rosetta: **cased role labels inside a Type‑variant pairing**.

**Important no‑drift note:**
Casing does **not** mean “macro vs micro.”  
Casing means **outer/major vs inner/minor role** *within the pairing* (and only for Type‑variant strategies). If you later want an explicit macro/micro driver notation, introduce a separate glyph/field — do not overload WIN/win/LOSE/lose.

### 10.5 What still needs tightening (honest list)

To make the mimetic meme manifold layer simulation‑ready, we still need:

1) A QIT‑native contract for the 7–12 axes (how they act on coupled systems \(A\otimes B\)).  
2) A precise definition of “mimetic distance / neighborhood” (graph vs manifold vs fiber bundle, under finitism).  
3) A canonical merge of the two 7–12 naming schemes (10.2 vs 10.3).

Until those are locked, 7–12 should be treated as **exploration axes** that do not overwrite the 0–6 canon.


---

## 11) Derived axes (pairwise / higher‑order) as **math**, not narrative (PRE‑IGT)

You can treat the base axes (A0..A6) as **primitive knobs**, and then define **derived axes** as *measurable interaction operators* on any scalar metric M (e.g., commutator witness, holonomy norm, entropy delta).

### 11.1 Definition: derived‑axis interaction operator

For two binary axes Ai, Aj and a scalar metric M:

    I_ij(M) =
        E[M | Ai=1, Aj=1]
      - E[M | Ai=1, Aj=0]
      - E[M | Ai=0, Aj=1]
      + E[M | Ai=0, Aj=0]

This is the canonical “derived 2‑axis correlation.”

### 11.2 Axis‑0 connector (A0 as moderator of derived axes)

For a triple A0, Ai, Aj, define the **Axis‑0 connector**:

    ΔI_ij^(A0)(M) = I_ij(M | A0=S) − I_ij(M | A0=N)

Interpretation:

- If ΔI_ij^(A0) ≈ 0, then the interaction Ai×Aj is **stable** across A0 polarity.
- If large, then A0 acts as a **regime switch / gain control** on how Ai couples to Aj.

### 11.3 How to use this inside the canon (without inventing new primitives)

- Keep A0..A6 as the only primitive axes.
- Treat derived axes as **second‑order observables** (things we can measure, sweep, and optimize) — not new primary axes.
- Promote only those derived axes that are:
  1) stable across resolution/discretization, and  
  2) have an interpretable mechanistic bridge (e.g., maps cleanly to a QIT knob or a Hopf geometry invariant).

### 11.4 Screening snapshot (Hopf64, Macro‑4, PRE‑IGT)

This is a **toy screening run** (full factorial 2^7 configs) whose job is to reveal **which couplings are structurally loud** in the current operationalization.

**Top 10 derived pairs by |I_ij(W6)|**  
(W6 = precedence/commutator witness aggregate):

| pair   |   I_W6_abs |   I_K_abs |   dI_W6_by_A0 |   dI_K_by_A0 |
|:-------|-----------:|----------:|--------------:|-------------:|
| A1×A2  |      5.567 |     4.162 |         1.340 |        0.435 |
| A2×A4  |      4.967 |     2.072 |         0.937 |        0.317 |
| A1×A4  |      3.494 |     2.315 |         0.881 |       -0.128 |
| A4×A5  |      2.823 |     1.704 |        -0.144 |        0.038 |
| A2×A5  |      2.173 |     1.116 |        -0.786 |       -0.193 |
| A0×A2  |      1.597 |     0.321 |       nan     |      nan     |
| A3×A6  |      1.587 |     0.718 |        -0.011 |        0.143 |
| A5×A6  |      1.586 |     0.822 |         0.021 |        0.072 |
| A3×A5  |      1.584 |     0.642 |        -0.016 |       -0.014 |
| A2×A6  |      1.584 |     1.396 |        -0.044 |       -0.142 |

**Axis‑0 moderation (top examples)** — same run:

| pair   |   I_W6 |   I_W6_A0=N |   I_W6_A0=S |   dI_W6_by_A0 |
|:-------|-------:|------------:|------------:|--------------:|
| A1×A2  |  5.567 |       4.897 |       6.237 |         1.340 |
| A2×A4  | -4.872 |      -5.340 |      -4.403 |         0.937 |
| A1×A4  | -0.940 |      -1.381 |      -0.499 |         0.881 |
| A2×A5  |  1.786 |       2.179 |       1.393 |        -0.786 |
| A1×A5  | -0.183 |      -0.473 |       0.108 |         0.581 |
| A4×A5  |  0.607 |       0.679 |       0.535 |        -0.144 |

For the full tables and reproducible details see:

- `05_FOUNDATIONS/DERIVED_AXES_AXIS0_CONNECTOR_REPORT.md`
- `derived_axes_ordered_pairs_42_with_axis0_connector_pre_igt_v0_2.csv`

(Raw factorial outputs:
`derived_axes_fullfactorial_macro4_hopf64_pre_igt_v0_2.csv`,
`derived_axes_pairwise_interactions_macro4_hopf64_pre_igt_v0_2.csv`,
`derived_axes_axis0_moderation_macro4_hopf64_pre_igt_v0_1.csv`.)

### 11.5 What this is for (later layers)

This derived‑axis machinery is the bridge that lets us:

- keep the base canon stable,
- systematically explore higher‑order structure,
- and later (in IGT / mimetic‑meme manifolds / holodeck‑science) add complexity only when it is supported by measurable invariants.

---

# SOURCE: 04_ENGINES/ENGINES_SPEC.md

# Engines Spec v0.8 (PRE‑IGT) — Canon‑Locked Schedules + Axis Semantics

Status: **FOUNDATION CANON** (pre‑IGT).  
Goal: freeze *only* what must not drift so we can keep stress‑testing without renaming loops every round.

This spec is intentionally **not** a physics proof. It is the *formal engine grammar* that all sims and later IGT overlays must compile against.

---

## 0) Non‑negotiable canon locks (do not drift)

### 0.1 Axes vs derived properties
- **AXIS‑3 = Type / Chirality** (Type‑1 vs Type‑2).  
  *Outer/inner is not an axis; it is a derived casing/role.*
- **AXIS‑4 = Macro topology order only** (Deduction vs Induction).
- **AXIS‑6 = Precedence only** (what acts first).  
  - **UP** = Op→Topo  
  - **DOWN** = Topo→Op  
  (Token string order encodes this; see §3.)

### 0.2 Topology and operator alphabets
- **Topologies (arena/terrain):** `Ne, Si, Se, Ni`
- **Operator families (move style):** `Ti, Te, Fi, Fe`

Rosetta (QIT map‑classes) provides the test harness mapping for each symbol, but **this spec stays symbol‑level**.

---

## 1) The four macro topology cycles (Axis‑4)

Axis‑4 is *only* the topology order. Two allowed cycles:

### Deduction order (Axis‑4 = deduction)
`Ne → Si → Se → Ni → Ne`

### Induction order (Axis‑4 = induction)
`Ne → Ni → Se → Si → Ne`

Which cycle you are in is determined by **(Type × loop casing)**:

- **Type‑1 outer = deduction**
- **Type‑1 inner = induction**
- **Type‑2 outer = induction**
- **Type‑2 inner = deduction**

---

## 2) Canon engine schedules (macro‑4)

These are the four **macro‑4** loops (one token per topology per cycle).  
They are the smallest “engine skeletons” that later expand into macro‑8 and micro‑16/32 schedules.

### 2.1 Type‑1 (Left / Chirality‑1)

**Type‑1 OUTER (major casing) — Deduction**
1. `NeTi`
2. `FeSi`
3. `TiSe`
4. `NiFe`

**Type‑1 INNER (minor casing) — Induction**
1. `SeFi`
2. `SiTe`
3. `FiNe`
4. `TeNi`

### 2.2 Type‑2 (Right / Chirality‑2)

**Type‑2 OUTER (major casing) — Induction**
1. `FiSe`
2. `TeSi`
3. `NeFi`
4. `NiTe`

**Type‑2 INNER (minor casing) — Deduction**
1. `TiNe`
2. `SiFe`
3. `SeTi`
4. `FeNi`

> Note: the Type‑2 outer loop is a cycle; choosing a “start token” is a rotation choice.  
> The ordering above matches the FIXPACKET canonical listing.  
> Rotating to start at `NeFi` gives: `NeFi → NiTe → FiSe → TeSi` (which makes the induction topology order explicit).

---

## 3) Axis‑6 precedence (token string order)

Axis‑6 is encoded by whether the token is written as **TopoOp** or **OpTopo**.

- **TopoOp ⇒ DOWN ⇒ Topo→Op**
  - example: `NeTi` means apply **Ne** then **Ti**
- **OpTopo ⇒ UP ⇒ Op→Topo**
  - example: `TiNe` means apply **Ti** then **Ne`

This is the canon resolution of the earlier drift (“Axis‑6 determines sign”).  
**Axis‑6 determines precedence, and precedence can induce sign‑flips in derived witnesses** (commutators / oriented holonomy), but Axis‑6 itself is not “±”.

---

## 4) Outer vs inner (derived casing, not an axis)

We keep casing meaning minimal:

- **Outer = major casing** (one macro‑4 loop per Type)
- **Inner = minor casing** (the other macro‑4 loop per Type)

Any stronger claims (outer = low impedance, etc.) must be treated as:
- **Derived** (from measurable witnesses), and
- **Stress‑tested** (across microstate sweeps, discretization refinements, and multi‑qubit extensions).

A safe *measurable* placeholder that keeps you honest:

> Define an impedance‑like witness Z for a loop as a function of  
> (entropy along the loop) and (oriented holonomy / commutator magnitude).  
> Major/minor should be predictable from Z *only if* the geometry claim is true.

---

## 5) Expansion layers (macro‑8, micro‑16, micro‑32)

This spec locks the macro‑4 skeletons. Expansion is defined by adding:
- the complementary operator family per topology stage, and
- the precedence realizations (Axis‑6 UP/DOWN) that create the micro‑tokens.

The “full 32 microcycle per engine” should be generated from:
- the macro‑4 loop + its inner/outer pairing + precedence rules,
not hand‑written per doc.

---

## 6) Axis‑1 / Axis‑2 (Szilard / dual‑stack hooks)

These axes are active in PRE‑IGT and **must not be ignored**:

- **AXIS‑1 (bath gating / legality):** governs which couplings are allowed (adiabatic vs isothermal in the toy harness).
- **AXIS‑2 (chart lens):** governs whether the system is treated as “closed/Lagrangian” vs “open/Eulerian”.

Dual‑stack means: run two coupled loops (e.g., Type‑1 + Type‑2) with axis‑1/2 controlling coupling channels and impedance matching.

This spec does **not** lock one final physical interpretation; it locks only that:
- axis‑1 and axis‑2 are present,
- they change measured loop behavior,
- and they are essential for the Szilard‑style reading.

---

## 7) Minimal PRE‑IGT test requirements

Any implementation claiming “canon‑compliant engine” must pass:

1. **Token compilation:** schedule tokens exactly match §2.
2. **Axis‑4 invariance:** topologies follow the correct macro order for each loop.
3. **Axis‑6 invariance:** string order maps to precedence UP/DOWN exactly.
4. **Non‑commutation requirement:** if you swap in commuting channels, precedence witnesses collapse (commutator / holonomy goes to ~0).
5. **Discretization robustness:** refining the Hopf lattice should preserve qualitative signatures (not numerical equality).

---

## 8) Open knots (explicitly not solved here)

- Exact physical dictionary (GR/SM, dark sector)
- Full thermodynamic interpretation of dual‑stack Szilard mechanics
- Any IGT payoff functional (explicitly out of scope for PRE‑IGT)



---

# SOURCE: 04_ENGINES/AXIS1_AXIS2_DUALSTACK_SZILARD.md

# AXIS‑1 / AXIS‑2 + Dual‑Stacked Szilard Mechanics (PRE‑IGT Canon Patch v0.1)

This patch exists because the current pre‑IGT canon has been **over‑validated on AXIS‑3/4/6** (chirality, flow direction, precedence),
while **AXIS‑1/2** are the axes that make the engine a *Szilard‑class* information‑thermodynamic machine rather than “just” a non‑commuting map loop.

This is not an IGT layer. This is still **pre‑IGT**.

---

## 1) Why AXIS‑1 and AXIS‑2 matter for “Szilard-class” claims

### AXIS‑1 (bath gating) = thermodynamic legality constraint

If we claim “engine ≈ Szilard/Carnot,” we must prevent illegal moves:

- you don’t get a free reset,
- you don’t lower entropy without paying the right coupling cost,
- you don’t export/import entropy when the stroke is supposed to be adiabatic.

Therefore AXIS‑1 must be implemented in sims as a **gate** on the bath‑coupled stroke families.

Minimal sim rule (pre‑physics, but legality‑preserving):

- If AXIS‑1 = adiabatic, bath strength ≈ 0 (or the stroke becomes a purely unitary/stirring surrogate).
- If AXIS‑1 = isothermal, bath strength > 0 (hot mixing / cold reset are enabled).

### AXIS‑2 (chart lens) = representation / “oracle” split

AXIS‑2 is the “lens” that decides whether operations are composed in a single chart or across a chart connector.

This is where your **Pi+Je vs Pe+Ji** “Lagrangian vs Eulerian” framing belongs.

The important mechanical point:

- In **closed/Lagrangian**, the token behaves like “act inside one chart.”
- In **open/Eulerian**, the token behaves like “act across two charts” (checkerboard↔ring connector inserted between the token components).

This is also the clean place to anchor your axiom:

> **a = a iff a ~ b** (identity is operational equivalence).

Different charts are not “different realities”; they are different coordinate systems / probes.
The *oracle* is what fixes which equivalences are admissible.

---

## 2) The dual‑stacked Szilard architecture (your unique engine claim)

### The core pre‑IGT necessity claim

A **single oriented engine** can accumulate an oriented quantity (call it holonomy / winding / phase‑area / commutator flux) until it stalls.

Therefore the minimal indefinite architecture is a **conjugate pair**:

- Type‑1 provides one orientation,
- Type‑2 provides the conjugate orientation,

and they must be **stacked** so that the net winding is bounded.

This is the *mechanical* sense in which you have a “dual‑stacked Szilard,” distinct from a single cyclic engine.

### What “stacked” means in canon terms

Not IGT. Not psychology. Just mechanics:

- **Stack = compose two engine cycles as a paired macro‑cycle.**
- The pairing has an **orientation** (order matters).
- The pair can share a “battery/memory” variable (future work) once we add a proper Szilard accounting layer.

---

## 3) Concrete test contracts to add (PRE‑IGT)

To prevent drift, these become explicit tests.

### Test A — AXIS‑1 ablation (bath gating)

Run the same loop under:

- strong bath coupling (isothermal)
- weak/no bath coupling (adiabatic)

Expect:

- isothermal mode can sustain nontrivial steady signatures (entropy/potential not collapsing)
- adiabatic mode collapses toward “stirring” / saturation.

### Test B — AXIS‑2 ablation (chart lens)

Run the same loop under:

- closed chart (no connector)
- open chart (connector inserted)

Expect:

- open chart amplifies order‑sensitivity signatures (commutator/holonomy witnesses).

### Test C — dual‑stack boundedness

Compare:

1) Type‑1 only repeated cycles
2) Type‑2 only repeated cycles
3) Type‑1+Type‑2 stacked pair (both possible stack orders)

Measure a **boundedness witness**:

- holonomy drift per cycle
- or commutator flux per macro‑cycle
- or loop area vector stability (Hopf/ring discretization)

Expect:

- one‑type runs drift/saturate,
- the paired stack has a parameter regime where drift is bounded.

---

## 4) What stays OPEN

- Exact mapping of the four topologies to the four classical “cylinders”
  ({compression, expansion}×{isothermal, adiabatic}) is still a bridge decision until the thermodynamic accounting is explicitly implemented.

- The full Szilard accounting layer (Landauer erasure cost, memory register, work extraction bookkeeping) remains **OFF** for now (still pre‑IGT).

---

## 5) Implementation note (avoid CPTP sign mistakes)

Any “sign flip” associated to precedence (AXIS‑6) must live in a **derived witness**:

- commutator [A,B] = A∘B − B∘A
- holonomy/loop‑area orientation
- ΔΦ / ΔS witness with explicit bookkeeping

Not in “negative channels.”



---

# SOURCE: 04_ENGINES/HEXAGRAM_MICROSTATE_ENCODING.md

# 14 — Two‑Trigram / Hexagram Encoding of the 64 Microstates (PRE‑IGT) v0.1

**Status:** CANON‑SAFE *encoding layer* (notation / indexing).  
**Not a physics claim.** This patch standardizes how we *index* the already‑defined 64 microstates.

## Why this exists

In the foundations work, the engines are repeatedly described as a:

- **“6‑bit / 2‑trigram / 64‑state”** structure,
- where the **first trigram** selects the **terrain/topology side**, and
- the **second trigram** selects the **operator/play side**.

We already have a concrete 64‑microstate test harness (Hopf‑spinor PRE‑IGT) and its reports.

This patch locks a single canonical encoding so:

- every future sim can enumerate the same 64 states,
- the “two trigrams” language becomes *literal* in the code index,
- “32 microstates per engine type” becomes a derived fact,
- future 12‑axis / 4‑trigram proposals have a stable base.

## Canon core objects (recap)

These are already canon‑locked elsewhere:

- **Type / chirality (Axis‑3):** Type‑1 vs Type‑2.
- **Topology (terrain):** Ne, Si, Se, Ni.
- **Operator family:** Ti, Te, Fi, Fe.
- **Precedence (Axis‑6):** UP (Op→Topo) vs DOWN (Topo→Op), derived from token order.

From these, the microstate space is already:

\[
\text{Microstate} \in \{\text{Type}\}\times\{\text{Topology}\}\times\{\text{Operator}\}\times\{\text{Precedence}\} 
\]

with cardinality:

\[
2 \times 4 \times 4 \times 2 = 64.
\]

## The encoding

We encode a microstate as a **6‑bit word** (a “hexagram”):

\[
(b_0 b_1 b_2)\;(b_3 b_4 b_5)
\]

- **Terrain trigram** = \(b_0 b_1 b_2\)
- **Operator trigram** = \(b_3 b_4 b_5\)

### Terrain trigram \(b_0 b_1 b_2\): Type × Topology

We want 8 terrain states = 2 Types × 4 Topologies.

- \(b_0\) encodes **Type (Axis‑3 chirality)**
  - \(b_0=0\) ⇒ **Type‑1**
  - \(b_0=1\) ⇒ **Type‑2**

- \((b_1 b_2)\) encodes **Topology** (2‑bit code)

Canonical topology code (locked for indexing; can be re‑aliased visually later):

| \(b_1 b_2\) | Topology |
|---|---|
| 00 | Ne |
| 01 | Si |
| 10 | Se |
| 11 | Ni |

So the 8 terrain states are:

| \(b_0 b_1 b_2\) | Terrain |
|---|---|
| 000 | Ne (Type‑1) |
| 001 | Si (Type‑1) |
| 010 | Se (Type‑1) |
| 011 | Ni (Type‑1) |
| 100 | Ne (Type‑2) |
| 101 | Si (Type‑2) |
| 110 | Se (Type‑2) |
| 111 | Ni (Type‑2) |

### Operator trigram \(b_3 b_4 b_5\): Operator × Precedence

We want 8 operator‑modes = 4 operator families × 2 precedence states.

- \(b_3\) encodes **Domain family**
  - \(b_3=0\) ⇒ **T‑domain** (Ti/Te)
  - \(b_3=1\) ⇒ **F‑domain** (Fi/Fe)

- \(b_4\) encodes **polarity within domain**
  - if T‑domain: \(b_4=0\Rightarrow \text{Ti},\; b_4=1\Rightarrow \text{Te}\)
  - if F‑domain: \(b_4=0\Rightarrow \text{Fi},\; b_4=1\Rightarrow \text{Fe}\)

- \(b_5\) encodes **Precedence (Axis‑6)**
  - \(b_5=0\) ⇒ **DOWN** (Topo→Op)
  - \(b_5=1\) ⇒ **UP** (Op→Topo)

So the 8 operator modes are:

| \(b_3 b_4 b_5\) | Operator‑mode |
|---|---|
| 000 | Ti↓ |
| 001 | Ti↑ |
| 010 | Te↓ |
| 011 | Te↑ |
| 100 | Fi↓ |
| 101 | Fi↑ |
| 110 | Fe↓ |
| 111 | Fe↑ |

## Mapping to tokens (macro vs micro)

### Macro token (16)

A macro token is a **(Topology, Operator)** pair:

\[
\text{MacroToken} \in \{\text{Ne,Si,Se,Ni}\}\times\{\text{Ti,Te,Fi,Fe}\}
\]

### Micro token instance (32 per Type)

A micro token instance is:

\[
\text{MicroToken} = (\text{Type}, \text{Topology}, \text{Operator}, \text{Precedence})
\]

Fix Type and you have:

\[
4 \times 4 \times 2 = 32
\]

This is the “**32 states per engine type**” statement, now explicitly derived.

## What this encoding does NOT include (by design)

This 6‑bit encoding intentionally excludes several other axes/knobs because they are:

- **global run conditions** (not microstate identity), or
- **continuous parameters**, or
- **derived from schedules rather than state identity**.

Examples:

- **Axis‑4 (induction/deduction)** is a **macro topology ordering** property (schedule), not a microstate label.
- **Axis‑1 (bath gating)** and **Axis‑2 (chart lens)** are **run‑level knobs** that modulate map implementations.
- **Axis‑0 (VN polarity N/S)** is a **state scalar / hemisphere label** in the physical interpretation layer.

## Relation to the 12‑axis / 4‑trigram proposal

The canon already treats Axes 7–12 as **PROPOSED**.

This patch only says:

- If Axes 7–12 are eventually adopted, they should be encoded as **two additional trigrams** appended to this 6‑bit word,
- and (as the salvage notes say) they should be **derived/coupled** knobs rather than unrelated new primitives.

No further claims are made here.

## Minimal software contract

Any “PRE‑IGT microstate runner” should be able to:

1. enumerate the 64 microstates in lexicographic order \(0..63\),
2. decode index → (Type, Topology, Operator, Precedence),
3. generate the corresponding initial condition on the chosen manifold,
4. execute one full macro‑cycle (or a steady‑cycle),
5. record signatures (S, Φ, W6, holonomy/area, etc.).

---

# SECTION: EM_UPLOAD_03_WORLDVIEW_ROADMAP_STATUS_v3_3
