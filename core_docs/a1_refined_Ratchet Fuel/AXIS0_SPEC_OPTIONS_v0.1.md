# AXIS 0 — Correlation Response (Detailed Options for Sims)

> Goal: define Axis-0 *purely* in QIT / information terms (so it can live in Thread B),
> while keeping a clean Rosetta overlay (Ne/Ni vs Se/Si etc.) for human readability.

This document is **not** asserting "true physics." It is a menu of *candidate realizations*
that are all:
- explicit (formulas),
- finite-dimensional,
- testable in the existing sim harness.

---

## 0) Canonical meaning (do not drift)

Axis 0 is a **polarity of correlation response under perturbation**:

- **Allostatic**: correlation *diversity* increases under perturbation  
- **Homeostatic**: correlation deviation is suppressed under perturbation

Operationally: Axis-0 is about how correlations *move* when you shake the system, not about
"entropy sign" or "hot/cold".

---

## 1) Ingredients (shared across all options)

Let a finite system be split into subsystems. Let ρ be a density operator.

### 1.1 Perturbation family
Choose a 1-parameter CPTP family 𝒩_ε such that:
- 𝒩_0 is identity (no perturbation)
- ε ≥ 0 is the perturbation strength (noise, mixing, randomization, coupling, etc.)

Examples:
- local depolarizing: 𝒩_ε = ⊗_i 𝒟_ε^(i)
- local dephasing: 𝒩_ε = ⊗_i 𝒵_ε^(i)
- amplitude damping: 𝒩_ε = ⊗_i 𝒜_ε^(i)

### 1.2 Correlation statistic(s)
Pick a correlation statistic C(ρ) and/or a *distribution* of correlation weights.

Standard pieces:
- von Neumann entropy: S(ρ) = -Tr(ρ log ρ)
- mutual information: I(A:B) = S(ρ_A) + S(ρ_B) - S(ρ_AB)
- conditional entropy: S(A|B) = S(ρ_AB) - S(ρ_B)
- coherent information: I_c(A→B) = -S(A|B)

### 1.3 Axis-0 sign (generic)
Define a real-valued *Axis-0 index*:
    A0 = d/dε  D(𝒩_ε(ρ)) |_{ε=0}
for some "correlation diversity / spread" functional D.

Then:
- A0 > 0  ⇒ allostatic
- A0 < 0  ⇒ homeostatic
- |A0| small ⇒ "weak" or neutral

In sims: approximate with finite difference:
    A0 ≈ [D(𝒩_δ(ρ)) - D(ρ)] / δ

---

## 2) Option A — Pairwise MI spread ("correlation diversity" literal)

For n subsystems, define pairwise weights:
    w_ij(ρ) = max(I(i:j), 0) / Σ_{a<b} max(I(a:b), 0)

Define a diversity functional (entropy of the MI distribution):
    D_MI(ρ) = - Σ_{i<j} w_ij log w_ij

Interpretation:
- high D_MI => mutual information spread across many pairs (global-ish)
- low D_MI  => MI concentrated in few pairs (local-ish)

Axis-0 index:
    A0_MI = d/dε D_MI(𝒩_ε(ρ)) |_{0}

---

## 3) Option B — Local-vs-global MI ratio (simple, robust)

Choose a "local neighborhood" graph G (edges E).

Local MI:
    MI_local(ρ) = (1/|E|) Σ_{(i,j)∈E} I(i:j)

Global MI:
    MI_global(ρ) = (2/(n(n-1))) Σ_{i<j} I(i:j)

Ratio:
    R(ρ) = MI_global(ρ) / (MI_local(ρ) + κ)

(κ>0 prevents division blowups.)

Axis-0 index:
    A0_R = d/dε R(𝒩_ε(ρ)) |_{0}

Interpretation:
- A0_R > 0 : perturbation pushes correlation outward / globalizes it
- A0_R < 0 : perturbation tightens correlation locally / suppresses deviation

---

## 4) Option C — Negative conditional entropy / coherent info ("literal negative entropy")

Pick a bipartition A|B (or many shells/cuts later).

Coherent information:
    I_c(A→B; ρ) = S(ρ_B) - S(ρ_AB) = -S(A|B)

This is >0 for many entangled states and is the standard way to quantify
"negative conditional entropy" as a usable resource.

Two ways to use it as Axis-0:

### 4.1 Coherent-info spread across many cuts
For a family of cuts 𝒞:
    D_c(ρ) = variance_{cut∈𝒞} [ I_c(cut; ρ) ]   (or an entropy of binned values)

Axis-0 index:
    A0_c = d/dε D_c(𝒩_ε(ρ)) |_{0}

### 4.2 Survival under perturbation
Axis-0 index:
    A0_survive = d/dε [ average_{cut∈𝒞} I_c(cut; 𝒩_ε(ρ)) ] |_{0}

Interpretation:
- allostatic if coherent info survives and/or spreads under perturbation
- homeostatic if perturbation collapses it locally / damps it

---

## 5) Option D — Boundary bookkeeping / holographic compression proxy (matches your "shell" story)

If you have an interior/boundary split:
- ρ_bulk on bulk degrees
- boundary is some reduced description ρ_bdy = Tr_bulk(ρ_full) or an encoding map

Given a reconstruction map ℛ (learned or hand-specified), compare:
- correlation in bulk vs correlation in reconstructed bulk

Example stats:
    ΔMI = MI(ρ_bulk) - MI(ℛ(ρ_bdy))
    ΔS  = S(ρ_bulk)  - S(ℛ(ρ_bdy))
    ||ρ_bulk - ℛ(ρ_bdy)||_F  (Frobenius error)

Axis-0 can be defined as the sensitivity of these deltas under perturbation:
    A0_book = d/dε [ ΔMI(𝒩_ε(ρ_full)) ] |_{0}
(or use ΔS, or error)

Interpretation:
- allostatic: bookkeeping becomes *more distributed* (boundary captures more global correlation under shake)
- homeostatic: bookkeeping remains local / suppresses deviations

---

## 6) "i-scalar clock" candidates (for later, but explicit)

You can define a scalar i(ρ) that is:
- computed on shells/cuts,
- monotone under your admissible dynamics/coarse-graining,
- and therefore can parametrize "ordering" without assuming classical time.

Candidate i(ρ):
- i1 = Σ_{shell cuts} I_c(shell_cut; ρ)
- i2 = Σ_{shell cuts} I(A_shell : B_shell)   (mutual info across each shell boundary)
- i3 = Σ_{shell cuts} D(ρ_shell || σ_shell)  (relative entropy to reference)

Then define a "clock parameter" τ by:
    τ = i(ρ)
or (if needed) τ = f(i) for a monotone f.

---

## 7) Minimal sim ladder (fast → deep)

1) **2 qubits, Bell seed**
   - Verify negative conditional entropy exists (S(A|B) < 0).
   - Apply small noise 𝒩_ε and compute A0 for Options A–C.

2) **4 qubits, graph state**
   - Use multiple bipartitions (cuts) and compute coherent info spread.
   - Compare local vs global MI ratio.

3) **6–10 qubits, simple shell partition ladder**
   - Define nested regions A_r and compute i(ρ) across r.
   - Check robustness to different coarse-grainings.

4) **Boundary bookkeeping**
   - Add encoding/reconstruction and measure ΔMI and ||·||_F sensitivity.

---

## 8) Rosetta hooks (non-canon overlays)

- allostatic ↔ Ne/Ni ("positive feedback on novelty & global patterning")
- homeostatic ↔ Se/Si ("negative feedback on deviation & local stability")

Use these only for readability and debugging; keep the kernel math in QIT terms.
