# AXIS0_SPEC_OPTIONS_v0.2

DATE_UTC: 2026-01-31
STATUS: DRAFT (ROSETTA / THREAD-A ONLY; NOT THREAD-B CANON)

Purpose
- Provide **explicit, testable candidate definitions** for Axis-0 using standard quantum information theory (QIT) / math primitives.
- Keep Axis-0 definitions **independent of Axis labels** for Thread-B. Axis-0 here is a *rosetta handle* that points to one or more admissible math objects.

Context anchors observed in your attached notes (verbatim meaning, not endorsement)
- “ijk are the time dimensions… time is i as a scalar on the shells… shell contains j and k… future possibilities… shells compression at us are the future…” (your holographic-shell picture)
- “If your clock is the i scalar … your i scalar is a universal clock.”
- “correlations entropy can be negative”
- “need explicit math for the holographic jk fuzz field shells that do bookkeeping” (explicitly noted as currently missing)

This spec turns those anchors into **math objects** you can later ratchet (Thread-B) and then simulate (Thread-SIM).

---

## 0) Notation (standard QIT)

- Finite-dimensional Hilbert spaces.
- Density operator (density matrix): ρ
- Von Neumann entropy: S(ρ) := −Tr(ρ log ρ)
- Quantum relative entropy: D(ρ || σ) := Tr(ρ (log ρ − log σ)), defined when supp(ρ) ⊆ supp(σ)
- Mutual information: I(A:B)_ρ := S(ρ_A)+S(ρ_B)−S(ρ_AB)
  - Equivalent: I(A:B)_ρ = D(ρ_AB || ρ_A ⊗ ρ_B)
- Conditional entropy: S(A|B)_ρ := S(ρ_AB) − S(ρ_B)
  - Can be negative for entangled states.
- Coherent information: I_c(A→B)_ρ := −S(A|B)_ρ = S(ρ_B) − S(ρ_AB)

These are “legit official terms” you can later gate into Thread-B with glyph/term admission.

---

## 1) “i scalar” as a universal clock: what that can mean mathematically

You want: a scalar quantity i(·) such that:
1) It is computed from admissible structure (ρ, channels, instruments).
2) It is comparable across contexts (frame/observer independent in the sense of being representation-invariant).
3) It is monotone under a chosen “coarse-graining / bookkeeping” family (so it can order “earlier/later” without primitive time).

**Clock criterion (operational, no metaphysics):**
Choose a family of admissible maps {Φ_λ} (λ is just an index; not “time”).
Define i(λ) := f( Φ_λ(ρ) ).
Then i is a clock if, for the class of processes you care about, i(λ) is *monotone* in λ (nonincreasing or nondecreasing).

So: “universal clock” = “shared monotone under the bookkeeping maps”.

The main design lever is: choose f and choose Φ_λ.

---

## 2) Shell / boundary bookkeeping formalization (minimal)

To make “shells” precise without presuming metric geometry:

- Pick a nested sequence of **factorizations** (or nested subalgebras) representing “inside vs boundary vs outside”.

Example (factorization model):
H_total = H_in(λ) ⊗ H_bdy(λ) ⊗ H_out(λ)

As λ varies, the boundary split changes (coarse vs fine shell). This is an abstract version of “nested holographic shells”.

Then compute boundary/cut quantities like:
- I( in(λ) : out(λ) )  (global correlation across the cut)
- I( in(λ) : bdy(λ) )  (how boundary encodes inside)
- I( in(λ) : out(λ) | bdy(λ) )  (conditional mutual information; “residual correlation not explained by boundary”)

These are all explicit and simulatable.

---

## 3) Axis-0 candidate families (explicit formulas)

Axis-0 in your language: “entropy gradient / correlation gradient / negative entropy / entangled spacetime bookkeeping”.

So each candidate below produces:
- A scalar i(λ)  (“i scalar” at shell λ)
- A “gradient proxy” Δi(λ) := i(λ+1) − i(λ)  (no metric required; just differences across refinement steps)
- Optional “direction” (sign conventions)

### A0-A: Cut mutual information clock (boundary correlation content)

Definition:
i_MI(λ) := I( in(λ) : out(λ) )_ρ

Gradient proxy:
Δi_MI(λ) := i_MI(λ+1) − i_MI(λ)

Interpretation handle:
- If Δi_MI < 0 under your bookkeeping refinement, the “clock decreases” (choose sign or invert to taste).

Why this matches your needs:
- Mutual information is a relative entropy; it obeys data-processing monotonicity under local CPTP maps on either side of the cut.
- It is a clean “correlation precedes identity” scalar.

What it doesn’t capture:
- “Negative entropy” is not directly in I(A:B); it appears more naturally in conditional entropy.

### A0-B: Conditional entropy / coherent information clock (negative entropy allowed)

Definition (choose one; they are equivalent up to sign):
i_Scond(λ) := S( in(λ) | out(λ) )_ρ
i_coh(λ)   := I_c( in(λ) → out(λ) )_ρ = − i_Scond(λ)

Key property:
- i_Scond can be negative (entanglement signature).
- i_coh is positive when i_Scond is negative.

Gradient proxy:
Δi_Scond(λ) := i_Scond(λ+1) − i_Scond(λ)

Why this matches your notes:
- This is the most literal “correlations entropy can be negative” implementation.

### A0-C: Conditional mutual information clock (boundary-explains-what?)

Definition:
i_CMI(λ) := I( in(λ) : out(λ) | bdy(λ) )_ρ

This measures:
- Correlation between inside and outside *not accounted for* by the boundary.

Why it’s useful:
- It directly encodes a “bookkeeping boundary”: if the boundary perfectly mediates/records the correlation, this quantity shrinks.

### A0-D: Relative entropy to a “factorized / classicalized” reference (quantumness / decoherence pressure)

Pick a reference map Δ_λ (“dephase at shell λ” or “factorize at shell λ”).
Define:
i_ref(λ) := D( ρ_λ || Δ_λ(ρ_λ) )
where ρ_λ := Φ_λ(ρ)

This is a “how much nonclassical correlation / coherence remains” scalar.
It’s QIT-native but depends on choosing Δ_λ (that choice can be ratcheted).

---

## 4) Mapping your “jk fuzz” + path integral intuition into QIT (explicit, testable)

You currently *explicitly note* that you do not yet have “explicit math for the holographic jk fuzz field shells that do bookkeeping”.

Here is a clean way to make it explicit without importing classical time:

### QIT analog of “sum over paths” = Kraus-history expansion

Any CPTP map Φ has Kraus operators {K_α}:
Φ(ρ) = Σ_α K_α ρ K_α†  with Σ_α K_α†K_α = I

A multi-step process (no time assumed; just ordered composition) yields:
ρ_out = Σ_{α_1,...,α_n} (K_{α_n}...K_{α_1}) ρ_in (K_{α_1}†...K_{α_n}†)

This is mathematically the same “sum over histories” structure (discrete path integral).

### Interpreting “jk fuzz”
If you want α to be a 2D index α=(j,k), you can choose Kraus sets {K_{j,k}}.
Then the “fuzz” is:
- the multiplicity of admissible (j,k) histories,
- and the induced environment state in a Stinespring dilation.

Stinespring form:
There exists a unitary U and environment |0⟩_E such that:
Φ(ρ) = Tr_E[ U (ρ ⊗ |0⟩⟨0|) U† ]

The environment output state ρ_E is a fully quantum “which-path” record.
Then you can define an axis-0 candidate clock as:
i_env(λ) := S( ρ_E(λ) )     (environment entropy)
or
i_sys_env(λ) := I( system : environment )  (system-environment mutual information)

This is the cleanest place where your “bookkeeping on a boundary” becomes literal QIT.

---

## 5) How this aligns with the SIM evidence you already have (dMI, dSAgB)

Your SIM evidence reports include:
- dMI_mean
- dSAgB_mean
and they appear with opposite signs.

This matches the identity:
I(A:B) = S(A) − S(A|B)

So, when S(A) is held fixed by construction in a sim suite,
ΔI(A:B) = −ΔS(A|B)

Thus:
dMI ≈ − dSAgB

Meaning:
- Your existing Axis-0 sim metrics are already probing the A0-A vs A0-B relationship.

---

## 6) What to ratchet first (minimal “lego” ordering)

To avoid premature physics assumptions, ratchet in this order:

1) Admit the **entropy primitives**: von Neumann entropy, relative entropy, mutual information, conditional entropy, coherent information.
2) Ratchet “shell bookkeeping” as *nested partitions / factorizations* (no geometry yet).
3) Ratchet “gradient proxy” as differences across refinement steps (Δi), not derivatives.
4) Only then add geometric/physics overlays (holographic shells, gravity-as-compression) as rosetta labels on top.

---

## 7) Deliverables for next revision (v0.3 targets)

- A0 shell family formalism as either:
  (a) nested factorization; or
  (b) nested subalgebras; or
  (c) nested quantum error-correcting code subspaces (more holography-aligned)
- A single “Axis0 test harness contract” describing:
  - what inputs a sim must provide (ρ, partition(s), channel family)
  - what metrics must be emitted (i_*, Δi_*, negative-conditional-entropy fraction, invariance checks)

