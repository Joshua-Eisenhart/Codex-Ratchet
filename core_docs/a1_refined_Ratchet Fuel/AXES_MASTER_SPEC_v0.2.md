# AXES_MASTER_SPEC_v0.2

DATE_UTC: 2026-02-02T00:00:00Z
AUTHORITY: CANON (axis semantics + nonconflation rules)

REFERENCE
- See: CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md

GLOBAL LOCKS (HARD)
- Geometry is the constraint manifold and exists before Axes 0–6.
- Axes 0–6 are functions/slices on the constraint manifold; they are not primitives.
- Axis-3 is the engine-family split mapped directly to Weyl Spinor Flux (Inward vs Outward).

## 0) Notation

- Constraint manifold: **M** (shorthand for **M(C)**).
- Axis-i: **Aᵢ : M → Vᵢ** (a classification/slice).
- Axis indices (0–6) are bookkeeping labels for slices; they are not carriers.

## 1) Axis-0 (two-class slice)

- Codomain: **V₀ = {A0-CLASS-1, A0-CLASS-2}**
- Rule: Axis-0 is a two-class partition of **M** computed from admissible probes/operators.
- Candidate computations live in: AXIS0_SPEC_OPTIONS_v0.* (noncanon option sheets).

## 2) Axis-6 (precedence / composition sidedness)

- Codomain: **V₆ = {UP, DOWN}**
- Rule: Axis-6 selects which composition order is used when composing admissible operators/channels.
- Axis-6 is the sidedness/precedence slice; do not conflate with Axis-4.

## 3) Axis-5 (Texture / Generator Algebra)

- Codomain: **V₅ = {Line (Partition), Wave (Mixing)}**
- Rule: Axis-5 partitions the mathematical calculus toolhead into integration vs differentiation boundaries.
- **Wave Family (FeFi / Mixing):** Integration algebra that binds, smooths, and correlates continuous fields. Native to a topological Fourier ring basis: $\rho \mapsto \sum_k W_k \rho W_k^\dagger$. Primary physical operators: The Laplacian ($\nabla^2$) and the Fourier Transform ($\mathcal{F}$).
- **Line Family (TeTi / Partition):** Differentiation algebra that cuts, separates, and isolates sharp discrete boundaries. Native to the discrete computational checkerboard basis: $\rho \mapsto \sum_x P_x \rho P_x$. Primary physical operators: The Gradient ($\nabla$) and the Dirac Delta projector.

## 4) Axis-3 (engine-family split)

- Codomain: **V₃ = {Inward-Flux (Type-1), Outward-Flux (Type-2)}**
- Rule: Axis-3 selects the Weyl Spinor topological framework (Type-1 vs Type-2).
- Engine Type 1 (Deductive template) applies Inward flux; Engine Type 2 (Inductive template) applies Outward flux.

## 5) Axis-4 (Operator Family / Thermodynamic Optimization)

- Codomain: **V₄ = {DEDUCTIVE (FeTi), INDUCTIVE (TeFi)}**
- Rule: Axis-4 identically defines the thermodynamic optimization objective and sequence operator constraint.
- **Deductive Family (FeTi / Constraint):** Optimization objective $S \to 0$. Information-forming operators that isolate pure eigenstates and crystallize structural logic.
  - **Ti (Projector):** Discrete measurement / Lüders projection limits ($\rho \mapsto \sum_k P_k \rho P_k^\dagger$). Reduces degrees of freedom directly onto basis vectors.
  - **Fe (Laplacian):** Lindbladian master equation updates ($d\rho/dt = -i[H,\rho] + \sum(L\rho L^\dagger - \frac{1}{2}\{L^\dagger L, \rho\})$) to achieve absolute phase-locking or synchronization.
- **Inductive Family (TeFi / Drive):** Optimization objective $\Delta W \to \max$. Entropy-producing operators ($S \uparrow$) driven to expand search spaces and execute conditional dynamics.
  - **Te (Gradient):** Hamiltonian flows ($U\rho U^\dagger$) or gradient vector updates ($\theta \leftarrow \theta \pm \eta \nabla J(\theta)$) to apply continuous force fields.
  - **Fi (Fourier):** Spectral frequency projections ($\rho \mapsto F \rho F^\dagger / \text{Tr}(F \rho F^\dagger)$) governing absorption/emission resonances.

## 6) Axis-1 × Axis-2 (Topology4)

- Axis-1 and Axis-2 are slices whose product defines **Topology4** (four base regimes).
- The axis product is the base-class split itself.
- Graph edges / adjacency between bases are derived structure, not Axis-1/2.

## 7) Guardrails (nonconflation)

- Axis-4 ≠ Axis-6 (math class vs composition sidedness).
- Axis-1×Axis-2 base regimes ≠ edges/adjacency structures.
- Axis-3 defines the physical Weyl Spinor chirality constraint (inward/outward path flow).

## 8) Ratchet ingestion order (roadmap only)

- Candidate build order: **0 → 6 → 5 → 3 → 4 → (1×2)**
- This is a build order for admissions/evidence; it is not a precedence claim about geometry.
