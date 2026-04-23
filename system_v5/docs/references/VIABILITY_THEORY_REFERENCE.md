# Viability Theory: Formal Reference

Date: 2026-04-05
Status: Reference doc — the actual mathematics, not the system's application

---

## What It Is

Jean-Pierre Aubin (1991). A mathematical framework asking: given dynamics
and constraints, from which initial states can the system remain within
the constraints forever?

Not "where does the system converge to" (attractors).
"Where can the system SURVIVE" (viability).

---

## Formal Definition: The Viability Kernel

Setup: differential inclusion x'(t) ∈ F(x(t)), constraint set K ⊆ Rⁿ.

Viab_F(K) = { x₀ ∈ K : there exists a solution x(·) with x(0) = x₀
              such that x(t) ∈ K for all t ≥ 0 }

The set of all initial states from which AT LEAST ONE evolution exists
that remains in K for all future time.

Key properties:
- Viab_F(K) is the LARGEST closed viability domain in K
- If Viab_F(K) = K, then K is viable under F
- If Viab_F(K) = ∅, then K is a repeller (all evolutions eventually
  violate constraints)

For controlled systems x'(t) = f(x(t), u(t)) with u(t) ∈ U:
F(x) = {f(x,u) : u ∈ U}, and the viability kernel = largest closed
controlled invariant subset of K.

---

## The Tangential Condition (Nagumo-Aubin)

The contingent cone (Bouligand tangent cone) to K at x:

T_K(x) = { v ∈ Rⁿ : lim inf_{h→0+} (1/h) · dist(x + hv, K) = 0 }

All directions that "point into or along" K at x.

A closed set K is a viability domain iff:

  For all x ∈ K:  F(x) ∩ T_K(x) ≠ ∅

At every point in K, the dynamics must offer at least one direction
that does not immediately leave K.

---

## The Viability Theorem (Aubin, 1991)

K locally compact, F upper semicontinuous with compact convex values.
Then K is viable under F IFF the tangential condition holds.

Sharp necessary-and-sufficient characterization. When F reduces to
single-valued continuous f, this reduces to classical Nagumo theorem (1942).

---

## The Regulation Map

Given Viab_F(K), the regulation map R: Viab_F(K) → 2^U:

  R(x) = { u ∈ U : f(x,u) ∈ T_{Viab_F(K)}(x) }

Selects controls that keep evolution within the viability kernel.
The feedback law that "regulates" to maintain viability.

---

## Viable States vs Captured States

- Viable states (in Viab_F(K)): at least one evolution stays in K forever
- Captured states (in capture basin): at least one evolution reaches
  target C in finite time while remaining in K

Complementary: survival vs goal-reaching.

---

## Viability vs Attractors: The Precise Difference

| Property | Attractor Basin | Viability Kernel |
|---|---|---|
| Core question | Where does the system CONVERGE TO? | Where can the system SURVIVE? |
| Trajectory requirement | ALL trajectories converge | AT LEAST ONE trajectory remains |
| Time horizon | Asymptotic (t → ∞) | All time (no violation ever) |
| Constraint set | Not inherent; defined by dynamics | Central — K defines the problem |
| Control | Typically autonomous (no control) | Explicitly involves control |
| Emptiness | Attractors always exist (compact) | Viability kernel can be empty |

Aubin, Bayen & Saint-Pierre (2011) showed viability kernels can be
represented as unions of domains of attraction of chain control sets —
precise bridge between the concepts. But fundamentally different:
attractor basin = "where does it go?" Viability kernel = "can it stay?"

---

## Stochastic Viability (De Lara & Doyen, 2010)

Discrete-time stochastic: x_{t+1} = f(x_t, u_t, w_t), w_t random.

Stochastic viability kernel for threshold β ∈ [0,1]:

  SViab_β(K) = { x₀ ∈ K : ∃ feedback policy u(·) such that
                  P(x_t ∈ K for all t ≥ 0) ≥ β }

Maximal viability probability:

  V(x₀) = sup_{u(·)} P(x_t ∈ K for all t ≥ 0 | x(0) = x₀)

Bellman recursion:

  V(x) = sup_{u ∈ U(x)} E_w[ V(f(x,u,w)) · 1_{f(x,u,w) ∈ K} ]

Shifts from "does a viable trajectory exist?" to "what is the maximum
probability of remaining viable?" Bridges viability with chance-constrained
programming and robust control.

---

## Capture Basins

Given constraint K, target C ⊆ K, dynamics x' ∈ F(x):

  Capt_F(K,C) = { x₀ ∈ K : ∃ solution x(·) with x(0) = x₀,
                   x(t) ∈ K for all t ∈ [0,T], x(T) ∈ C for some T ≥ 0 }

States from which at least one evolution reaches target in finite time
while remaining viable until arrival.

The four-way duality:

| | Exists one trajectory | All trajectories |
|---|---|---|
| Stays in K | Viability kernel | Invariance kernel |
| Reaches C | Capture basin | Absorption basin |

Both viability kernels and capture basins are fixed points of set-valued
operators. Saint-Pierre's algorithm computes capture basins by backward
iteration from C.

---

## Invariance Kernel

Inv_F(K) = set of states from which ALL evolutions remain in K.
Guaranteed safety without control authority needed.
Viab_F(K) ⊇ Inv_F(K) always.

---

## Applications

### Evolutionary Biology / Population Viability

Bene, Doyen & Gabay (2001): viability analysis of fisheries — computing
(population, harvest) states from which sustainable harvesting is possible.

Co-viability analysis (CVA): simultaneously enforces ecological constraints
(stock ≥ threshold) and economic constraints (profit ≥ threshold).

Ecosystem Viable Yields (EVY): viability-based alternative to Maximum
Sustainable Yield (MSY).

Classical PVA uses forward simulation for extinction probability.
Viability-based PVA works BACKWARD from constraint satisfaction —
fundamentally different computation.

### Economics

Aubin, Dynamic Economic Theory (1997): reframes economics from
equilibrium/optimization to constraint satisfaction.

Sustainable development: viability kernel of (capital, consumption,
resource) under constraints like consumption ≥ c_min.

Debt dynamics: fiscal states from which solvency is maintainable.

Climate-economy: initial conditions from which climate targets achievable.

Satisficing vs optimizing (De Lara & Doyen): viability captures
"satisficing" (meeting thresholds) rather than "optimizing" (maximizing
utility). Formal alternative to classical welfare economics.

### Control Theory

Viability kernel = largest controlled invariant set in K.

Hamilton-Jacobi connection (Frankowska, Saint-Pierre): viability kernels
and capture basins are level sets of viscosity solutions to HJB equations.

Guaranteed viability vs optimal control: viability asks "does any
admissible trajectory exist?" — feasibility, not optimization. Viability
provides constraint qualification before optimization is meaningful.

---

## Computational Methods

### Saint-Pierre Algorithm (1994)

Foundational discrete approximation. Discretizes state space on grid.
Iterates backward: at each step, removes states from which no viable
evolution exists. Fixed point = approximate viability kernel.

### Limitations

**Curse of dimensionality:** O(Nᵈ) complexity. Infeasible beyond 3-4
state dimensions with Eulerian grids.

**Numerical diffusion:** Systematically overestimates viability kernel.
Computed kernels are outer approximations.

**Grid representation:** Output is grid points, not smooth boundary.

### Alternatives

- Lagrangian methods (Kaynama 2012-13): ellipsoidal/SVM representations,
  up to ~10 dimensions for linear systems
- Level-set methods: boundary as zero level set, HJ PDE solvers
- Sampling-based: randomized approaches avoiding full enumeration
- Machine learning: neural network approximations (emerging)

---

## Key People

| Person | Contribution |
|---|---|
| Jean-Pierre Aubin (1939-2023) | Founder. Viability Theory (1991), Dynamic Economic Theory (1997) |
| Patrick Saint-Pierre | Computational framework, viability kernel algorithm (1994) |
| Halina Frankowska | Hamilton-Jacobi equations in viability, set-valued analysis |
| Michel De Lara | Stochastic viability, dynamic programming extension |
| Luc Doyen | Stochastic viability, ecological-economic applications, co-viability |
| Christophe Bene | Fisheries and poverty viability applications |
| Marc Quincampoix | Differential games, discriminating kernels, numerical methods |

---

## Sources

Aubin (1991) Viability Theory, Birkhäuser. Aubin & Cellina (1984)
Differential Inclusions, Springer. Aubin, Bayen & Saint-Pierre (2011)
Viability Theory: New Directions, Springer. Saint-Pierre (1994) Applied
Mathematics & Optimization. De Lara & Doyen (2010) Systems and Control
Letters. Frankowska, HJ equations and viability. Bene, Doyen & Gabay
(2001) fisheries. Nagumo (1942) original tangential condition.
