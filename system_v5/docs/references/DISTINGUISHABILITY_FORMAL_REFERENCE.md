# Distinguishability: Formal Reference

Date: 2026-04-05
Status: Reference doc — the actual mathematics, not the system's application.
        This is the MOST SYSTEM-CRITICAL reference doc because "constraint on
        distinguishability" is the system's primitive substance.

---

## Trace Distance (Quantum Distinguishability Metric)

T(ρ, σ) = (1/2) ||ρ - σ||₁ = (1/2) Σᵢ |λᵢ|

where λᵢ are eigenvalues of (ρ - σ). Ranges from 0 (identical) to 1
(perfectly distinguishable / orthogonal support).

**Operational meaning (Helstrom-Holevo theorem):** Given equal priors,
maximum probability of correctly distinguishing ρ from σ in one shot:

  p_guess_max = (1/2)(1 + T(ρ, σ))

Trace distance IS optimal discrimination advantage. Variational form:
T(ρ,σ) = sup_{0 ≤ P ≤ I} Tr[P(ρ - σ)].

---

## Fidelity

F(ρ, σ) = (Tr[√(√ρ σ √ρ)])²

For pure states: F = |⟨ψ|φ⟩|². High fidelity = hard to distinguish.

Fuchs-van de Graaf inequalities connect trace distance and fidelity:
  1 - √F ≤ T ≤ √(1 - F)

---

## Holevo Bound

For ensemble {pᵢ, ρᵢ} encoding classical variable X, any measurement
producing outcome Y:

  I_acc(X:Y) ≤ χ = S(Σᵢ pᵢρᵢ) - Σᵢ pᵢS(ρᵢ)

χ = maximum classical information extractable per quantum system.
HSW theorem: χ is the asymptotically achievable classical capacity.

---

## Operational Equivalence

Two preparations P1, P2 are operationally equivalent (P1 ~ P2) if for
every measurement M and every outcome k:

  p(k|P1,M) = p(k|P2,M)

No experiment can distinguish them. Similarly for measurements.

### Spekkens' Generalized Noncontextuality

A noncontextual ontological model requires operationally equivalent
procedures to have equivalent ontological representations:

  P1 ~ P2 implies μ_P1(λ) = μ_P2(λ)

Spekkens (2005) proved quantum mechanics REQUIRES preparation
contextuality — operationally indistinguishable preparations must
sometimes map to different underlying distributions.

### Harrigan-Spekkens Classification

- ψ-ontic: every ontic state compatible with at most one pure quantum state
  (quantum states distinguishable at ontic level)
- ψ-epistemic: ontic distributions for distinct states can overlap
  (quantum indistinguishability reflects genuine ontic overlap)

PBR theorem (2012) severely constrains ψ-epistemic models.

---

## Indistinguishability Relations and Quotient Structures

Given states S and measurements/probes M, define:

  s1 ~_M s2  iff  for all m ∈ M: m(s1) = m(s2)

The quotient S/~_M = effectively distinct states given measurement M.

Examples:
- Topology: homeomorphism classes = quotient under continuous probes
- Algebra: isomorphism = indistinguishability under all homomorphisms
- Quantum: density matrices = quotient of pure state ensembles under
  all POVM measurements
- Thermodynamics: macrostates = quotient of microstates under
  macroscopic observables

**Refinement ordering:** More probes (M1 ⊂ M2) → finer equivalence
classes (~_M2 refines ~_M1). Lattice structure on equivalence relations.

**The density matrix IS a quotient structure.** Infinitely many pure-state
decompositions exist for a given ρ. No measurement distinguishes them.
The density matrix is the equivalence class representative under
"produces identical statistics for all POVMs."

---

## Coarse-Graining and Information Loss

Coarse-graining = surjective map φ: X_fine → X_coarse. States in the
same fiber φ⁻¹(y) become indistinguishable.

### Information Geometry of Coarse-Graining

Bradde, Bialek, Machta, Sethna: under renormalization group flow:
- Statistical manifold contracts in irrelevant directions
- Distances along relevant directions preserved exactly
- Distances along irrelevant directions contract by RG eigenvalues
- Models differing only in irrelevant parameters become indistinguishable

Information-theoretic derivation of universality: coarse-graining kills
fine-grained distinctions, leaving only universality classes.

### Entropy Increase

S(φ(ρ)) ≥ S(ρ). Coarse-grained distribution has strictly less
information about microstate. Second law = coarse-graining statement:
entropy increases because macroscopic observables cannot track
microscopic distinctions.

---

## Data Processing Inequality

### Classical

For Markov chain X → Y → Z:

  I(X;Z) ≤ I(X;Y)

Processing cannot increase mutual information. Cannot extract more
signal by post-processing.

### Quantum (Monotonicity of Relative Entropy)

For quantum channel N (CPTP map):

  D(N(ρ) || N(σ)) ≤ D(ρ || σ)

Proved by Lindblad (1975), Uhlmann (1977). Petz (1986, 1988)
characterized equality: holds iff a recovery channel exists.

### Implications for Distinguishability

  T(N(ρ), N(σ)) ≤ T(ρ, σ)

Physical evolution can only make states HARDER to distinguish, never
easier. This is the formal backbone: processing destroys information.

The DPI guarantees quotient structures under coarse-graining are
STABLE — once distinctions are lost, they stay lost.

---

## Blackwell Order

Experiment σ Blackwell-dominates σ' (σ' ≤_B σ) iff any of these
equivalent conditions hold:

1. **Utility dominance:** For every decision problem, expected utility
   under σ ≥ expected utility under σ'
2. **Garbling:** σ' is a garbling of σ — there exists stochastic matrix
   γ such that σ'(s'|w) = Σ_s γ(s,s') σ(s|w)
3. **Strategy inclusion:** achievable conditional action distributions
   under σ' ⊆ those under σ

**Blackwell's theorem (1951, 1953):** These three are equivalent.

The Blackwell order is a PARTIAL order — not total. Two experiments can
be incomparable. The space of experiments is a rich partially ordered set.

A more informative experiment better distinguishes between states of the
world. Garbling (adding noise) reduces distinguishability.

---

## Hypothesis Testing

### Neyman-Pearson Lemma

Among all tests with Type I error ≤ α, the most powerful test is the
likelihood ratio test:

  φ*(x) = 1 if L(x) > κ, 0 if L(x) < κ

where L(x) = p₁(x)/p₀(x). Optimal: no other test of same size has
greater power.

The likelihood ratio is the sufficient statistic for distinguishing
H0 from H1. Compresses all data into one number capturing all
discriminatory information.

### Quantum Neyman-Pearson

Replaces distributions with density matrices, likelihood ratios with
Helstrom measurement. Quantum Stein's lemma: asymptotic optimal exponent
for Type II error (at fixed Type I) = quantum relative entropy D(ρ||σ).

---

## Fisher Information

I(θ) = E_θ[(∂/∂θ log p(X|θ))²]

### Cramér-Rao Bound

  Var_θ(T) ≥ 1/I(θ)

No unbiased estimator can have variance below inverse Fisher information.

### Geometric Interpretation

Fisher information defines a Riemannian metric on the statistical manifold:

  ds² = I(θ) dθ²

High Fisher information = nearby parameter values produce very DIFFERENT
(distinguishable) distributions. Low = nearly identical — parameter hard
to estimate because changing it barely changes observations.

### Fisher-Rao Metric

The Fisher-Rao metric is (up to constant) the UNIQUE Riemannian metric
on probability space invariant under sufficient statistics (Čencov's
theorem, 1982). The geometry of distinguishability is canonical.

### Quantum Fisher Information

QFI(θ) = Tr[ρ(θ) L²] where ∂ρ/∂θ = (Lρ + ρL)/2

Quantum Cramér-Rao: Var(θ̂) ≥ 1/(n · QFI(θ)).
QFI = 4 × Bures metric, connecting to fidelity.

---

## Resource Theory of Distinguishability

### Asymmetric (Wang & Wilde, 2019)

Objects: pairs (ρ, σ) — "boxes" outputting one of two states.
Free operations: quantum channels applied identically to both.
Monotone: any divergence satisfying DPI.
Asymptotic conversion rate = ratio of relative entropies.

### Symmetric (Salzmann, Datta, Gour, Wang, Wilde, 2021)

Objects: classical-quantum sources.
Monotone: symmetric distinguishability (related to Chernoff divergence).
Conversion rate = ratio of quantum Chernoff divergences.

### Discrimination Tasks as Complete Monotones (Takagi & Regula, 2019)

For ANY resource theory, performance advantage in discrimination tasks
forms a complete family of monotones. State ρ convertible to σ by free
operations IFF ρ outperforms σ in every discrimination task.

Distinguishability advantages completely characterize the resource ordering.

---

## Identity from Distinguishability

### Leibniz's Principle of Identity of Indiscernibles (PII)

  ∀x,y: (∀P: P(x) ↔ P(y)) → x = y

Three versions:
- PII(1) weak: no two share all properties and relations
- PII(2) moderate: no two share all non-spatiotemporal properties
- PII(3) strong: no two share all monadic properties

### Quantum Challenge

Two electrons in a singlet share all intrinsic and state-dependent
properties. Under permutation invariance, even PII(1) appears violated.

Weak discernibility (Saunders, Muller, Seevinck): fermions in singlet
satisfy the irreflexive relation "has opposite spin to." Allows weak
discernibility without distinct monadic properties.

### Formal Takeaway

Identity is not primitive — it is derived from distinguishability:
- Two objects are "the same" when no available operation/measurement
  can tell them apart
- What counts as "same" depends on probe resolution (coarse-graining)
- The density matrix quotient IS this: states identified when no POVM
  separates them
- DPI guarantees stability: if indistinguishable now, no processing
  will separate them

Identity is relational, resolution-dependent, probe-relative.
The formal structure: fix operations → define equivalence relation →
take quotient. The quotient IS the ontology at that resolution.

---

## Cross-Cutting Spine

| Layer | Structure | Role |
|---|---|---|
| Trace distance / Fidelity | Metric on state space | Quantifies distinguishability |
| Operational equivalence | Equivalence relation | Defines "sameness" |
| Quotient structures (S/~_M) | Quotient set | The effective ontology |
| Coarse-graining / RG | Surjection | Creates indistinguishability |
| Data Processing Inequality | Monotonicity | Distinguishability cannot increase |
| Blackwell order | Partial order on experiments | Ranks discriminatory power |
| Neyman-Pearson | Optimal test | Best possible discrimination |
| Fisher information | Riemannian metric | Local distinguishability |
| Resource theory | Resource ordering | Distinguishability as resource |
| Leibniz PII | Philosophical principle | Identity = maximal indistinguishability |

The DPI is the linchpin: once distinctions are lost, they stay lost.
Blackwell ranks distinction-power. Fisher measures the local version.
Neyman-Pearson gives the optimal binary case. Resource theories formalize
the economy. Leibniz is the closure: identity IS the limit of
indistinguishability.

NOTE: This entire cross-cutting spine is the formal mathematics behind
the system's axiom a=a iff a~b. The axiom says: identity requires
distinguishability from something else under an admissible probe family.
The spine above is what that looks like when formalized across the
relevant literatures:
- "admissible probe family" = POVM / measurement set / experiment (Blackwell)
- "distinguishability" = trace distance / fidelity / Fisher information
- "identity" = equivalence class in the quotient S/~_M
- "iff" = the DPI guarantees stability: indistinguishability now means
  indistinguishability forever under processing
- "a~b" = operational equivalence / indistinguishability relation

The constraint on distinguishability (the system's primitive substance)
is the constraint that DEFINES which probe families are admissible (F01:
they must be finite) and how they compose (N01: order matters). The
constraint surface M(C) is the quotient of all possible states under
the equivalence relation induced by all admissible probes simultaneously.

---

## Sources

Helstrom (1976) Quantum Detection and Estimation Theory. Holevo (1973).
Spekkens (2005) arXiv:quant-ph/0406166. Harrigan & Spekkens (2010).
PBR (2012). Lindblad (1975), Uhlmann (1977), Petz (1986, 1988).
Blackwell (1951, 1953). Neyman & Pearson (1933). Fisher (1925).
Čencov (1982). Wang & Wilde (2019). Salzmann et al. (2021).
Takagi & Regula (2019) PRX. Saunders (2006), Muller & Seevinck (2009).
Bradde & Bialek (2017). Stanford Encyclopedia: Identity of Indiscernibles,
Identity and Individuality in Quantum Theory.
