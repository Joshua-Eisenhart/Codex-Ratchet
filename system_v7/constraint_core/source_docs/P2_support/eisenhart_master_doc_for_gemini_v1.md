# Eisenhart Engine Master Doc (Send This to Gemini / Grok Heavy)
**Audience:** Another LLM (Gemini / Grok Heavy) that will help improve the Eisenhart “one-axiom boot → geometry → engine” system.  
**Goal:** Produce richer, deeper, drift-proof docs + improved sims, **without hallucinated derivations**.

---

## 0) Non‑Drift Contract (Must Follow)
### 0.1 Status tags are mandatory
Every claim must be tagged as **exactly one** of:
- **ASSUMED** (only Step 0 is allowed to be assumed)
- **DEFINED** (we choose a representation / formal object)
- **CHOSEN** (minimality/admissibility postulate; not forced)
- **DERIVED** (follows from prior steps + stated lemmas)
- **VALIDATED** (numerical test / sim output)

### 0.2 VALIDATED requires a numeric artifact (no phantom tests)
Any **VALIDATED** step must include an **artifact inline**:
- a JSON snippet, or
- a scalar metric with explicit value + tolerance.

No artifact ⇒ not VALIDATED.

### 0.3 Two-layer interpretation only (prevents semantic drift)
All interpretations of sim sweeps must be split into:

**Layer A — VALIDATED-by-sim (what code actually does & measures)**  
**Layer B — INTENDED semantics (future mapping; must say what’s missing to implement it)**

You may NOT treat intended semantics as validated until the missing implementation exists.

### 0.4 Vocabulary constraint (critical)
- Do **NOT** use the word **“bit”**. Use **AXIS 1..6**.
- Avoid “Cartesian origin” assumptions.
- Avoid infinity. Finitism only.
- Avoid primitive equality; use operational equivalence (~) when needed.

---

## 1) Provided Artifacts (You Must Use These as Ground Truth)
You will be given 3 files (or their contents pasted):

1) **Derivation ladder (status-correct):**  
   `eisenhart_derivation_ladder_v1_0.md`

2) **Translation guardrails (no drift):**  
   `eisenhart_fixpack_translation_rules_v1_1.md`

3) **Current diagonal Hopf proxy sim (fast sweeps):**  
   `eisenhart_one_axiom_full_system_v0_13_fast.py`

### 1.1 Current sim scope (do not over-interpret)
The v0.13 sim is a **DIAGONAL proxy** (probability mass over a nested Hopf-like lattice).  
It is **NOT** yet a full density-matrix SU(2) simulator.

**What is actually implemented (Layer A allowed):**
- **AXIS‑6**: contract/sharpen vs release/diffuse **AND** order swap (Topo∘Op vs Op∘Topo).
- **Metrics**: entropy ΔH, potential ΔΦ, fiber flux magnitude, noncomm_start/end.

**What is NOT implemented yet (Layer B only):**
- True Weyl spinors / SU(2) left-vs-right action (AXIS‑3 intended).
- Real chart lens / conjugation-permutation invariance (AXIS‑2 intended).
- Stroke legality + b accounting (AXIS‑1 intended beyond bath-rate proxy).

---

## 2) Canonical Axis Definitions (INTENDED semantics — do not “prove” these yet)
These are the user’s intended meanings. Treat as **INTENDED** unless the sim truly implements them.

### AXIS 1 — Isothermic SeNi vs Adiabatic NeSi
- Intended: bath coupling legality / exchange rules (not just a rate knob).

### AXIS 2 — Pi+Je vs Pe+Ji
- Intended: closed vs open; Eulerian vs Lagrangian; chart/representation choice.  
- Implementation requirement: chart transform must **also transform operators** (density-matrix mode).

### AXIS 3 — Weyl / Spinors / Left vs Right (dual Szilard stacks)
- Intended: chirality / topology flow reversal; two engine configurations; topology reverses on this axis.
- Implementation requirement: explicit SU(2) left vs right action (density-matrix or operator-aware mode).

### AXIS 4 — Engine cycle loop directions
- Intended: direction of traversal / cycle loop orientation; can show engine cycle loop directions.

### AXIS 5 — Lines & waves: gradients, phase, harmonics, eigen structure
- Intended: wave coupling / harmonic texture / eigenmode selection; not just a toggle.

### AXIS 6 — J‑dom vs P‑dom (Topology‑first vs Operator‑first) + Operator Sign
- Intended: determines operator sign / ordering; this is **already** closest to implemented in v0.13.

---

## 3) Root Boot Ladder (Required Output Format)
You must produce an improved ladder that boots from **one primitive axiom**.

### Step 0 (only assumption)
**Axiom R’ (single primitive):** Reality begins as maximal randomness with a **finite maximal VN entropy ceiling**.

Everything else must be DEFINED/CHOSEN/DERIVED/VALIDATED.

### Core ladder shape (you may improve it)
- Step 1: finitism (finite carrier d)
- Step 2: operational equivalence (~) instead of primitive equality
- Step 3: entropic monism **only within an explicit admissibility postulate**
- Step 4: noncommutation → order-as-time
- Step 5: engine cycle with accounting (Szilard-style b reservoir)
- Step 6: ring–checkerboard dual chart lens (FT invariance)
- Step 7: su(2) minimality **only within a CHOSEN unitary/probe postulate**
- Step 8: Hopf substrate from SU(2) ≅ S³ and U(1) quotient
- Step 9: axes as binary switches (DEFINED) + validated by sweeps

**IMPORTANT:** If you claim DERIVED, show the lemma chain.

---

## 4) What You Must Deliver (Gemini/Grok Output Checklist)
Deliver **three** outputs, each rich and self-contained:

### Output A — “Reader Master Doc” (high clarity, deep detail)
A standalone explanation that a new reader can understand:
- full ladder, with status tags
- definitions of ring–checkerboard model (see Section 5)
- notation conventions
- why noncommutation matters (order as time)
- how the engine emerges (constraint/release + accounting)
- how the Hopf lattice emerges (within chosen SU(2) postulate)
- explicit separation of VALIDATED vs INTENDED

### Output B — “Math/Code Compact Spec” (minimal, executable, formal)
- clean math definitions (operators, state, metrics)
- pseudocode or code skeleton
- explicit invariants and asserts (entropy nonnegativity, normalization, etc.)
- no prose fluff

### Output C — “Upgrade Plan + Tests” (concrete next steps)
A prioritized roadmap with:
1) **Density-matrix mode** with true SU(2) action
2) AXIS‑3 implemented as **left vs right SU(2)** action
3) AXIS‑2 implemented as **chart lens** that conjugates operators + permutes indices
4) AXIS‑1 implemented as **stroke legality + b accounting** (no free ΔS<0)
5) richer AXIS‑5 harmonic/eigen tooling
6) expanded metrics: loop-flux, work proxy vs ∇Φ, noncomm norms, invariance tests

Each item must include:
- what to implement
- what to test
- what artifact to report

---

## 5) Ring–Checkerboard Model (You Must Expand This Fully)
You must write a **complete** definition and notation for the ring-checkerboard system, including:

### 5.1 Nested checkerboard address space
- levels ℓ = 0..L-1
- each level has a board/grid (i,j) plus a ring/fiber index k
- define flatten/unflatten maps
- define nesting rules and how “pieces/rules” could live on deeper levels (e.g., chess encoded in sublayers)

### 5.2 Ring structure and entropy gradient
- define the ring coordinate (phase/fiber)
- define VN entropy gradient field / potential Φ and how it couples to dynamics
- define how “ring gradients” correspond to flows and engine strokes

### 5.3 Finite gravity / boundedness connection (finitism geometry)
Explain how the nested spherical checkerboard supports finitism:
- bounded state count
- largest possible number / capacity bound concepts (don’t assume infinity)
- how “gravity” or “collapse” could be modeled as contraction along the nesting hierarchy (as an interpretation, clearly tagged)

### 5.4 Black/white hole singularity interpretation (INTENDED)
If you discuss black holes / white holes / dark energy bubbles:
- clearly mark as **INTENDED ontology**
- propose what metrics in the model would correspond to “collapse” vs “expansion”
- propose tests in the sim that would generate those signatures

---

## 6) Hard Technical Questions You Must Answer
You must address these explicitly:

1) **How do we justify “entropy-only invariants” without smuggling?**  
   Propose an admissibility postulate that is minimal and drift-proof.

2) **How do we get SU(2) from finitism?**  
   Explain what must be CHOSEN (unitary/probe postulate) and why it is minimal.

3) **What does AXIS‑6 *really* represent mathematically?**  
   Give a clean operator algebra statement: order swap + contract/release dual.

4) **What would a true Szilard accounting variable b look like in this model?**  
   Provide explicit update equations and legality checks.

5) **How can we ensure LLMs don’t re-inject infinity or equality?**  
   Provide explicit “forbidden patterns” and replacement patterns.

---

## 7) Output Formatting Requirements (so it’s usable)
- Use headings, equations, and code blocks.
- Include explicit artifacts for VALIDATED claims.
- For any sim claims: include top_cooling/top_heating snippets + metrics.
- Make everything copy/paste friendly.

---

## 8) Prompt to the LLM (Gemini / Grok) — Use This Verbatim
**System goal:** Improve the Eisenhart one-axiom boot and engine model without drift.

**You must:**
1) Respect status tags and artifact rules.
2) Produce Outputs A/B/C (Section 4).
3) Expand ring–checkerboard model fully (Section 5).
4) Keep a strict Layer A vs Layer B separation.

**You may:**
- Propose better axioms / postulates, but must tag them CHOSEN and justify minimality.
- Propose alternative finite geometries, but must keep Hopf/SU(2) path available.

**You may not:**
- Assume infinity.
- Use “bit”; use AXIS 1..6.
- Claim DERIVED when it’s CHOSEN.
- Claim VALIDATED without numeric artifact.

---

## 9) Attachments / Paste Zone
Paste the contents of these 3 files after this doc (or attach them):
1) eisenhart_derivation_ladder_v1_0.md
2) eisenhart_fixpack_translation_rules_v1_1.md
3) eisenhart_one_axiom_full_system_v0_13_fast.py
