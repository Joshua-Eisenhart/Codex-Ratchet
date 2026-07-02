# Julia QIT-Aligned Migration & Build Plan

Status: living plan, 2026-06-01. Supersedes the PyTorch carrier for new work. PyTorch sims are **sidelined**
(not deleted); JAX sims keep running as the cross-audit track; Julia rebuilds a fresh sim set from scratch.

---

## 0. The principle (what the whole stack serves)

**Spacetime IS entropy/information.** Geometry is not a container decorated with entanglement — the geometry
*is* the entanglement structure. This is now demonstrated, not asserted: on the Julia stack the **geometric
Hopf linking number** (computed from CliffordAlgebras fibers) **equals** the **information linking number**
(`A–C` log-negativity from ITensors), as the same integer, for linking numbers 1/2/3
(`geometry_is_information_unified.jl`, all match).

**Primary object** (unchanged, the thing every adapter must preserve): the **finite retrocausal possibility
field** — shell-indexed possible futures compress inward through compatibility into a present survivor and leave
an outward record. Everything below is an adapter/probe/proxy onto this object, promotion-controlled.

The architectural punchline: the possibility field **is** the branch-and-prune ensemble. Possible futures =
branches; compatibility/conservation constraints = pruning; the present survivor = the surviving attractor
basin; the outward record = the basin's invariants. So "branching + pruning + attractor basins" is not a
borrowed metaphor — it is the object's native computation.

---

## 1. The migration (what changes, what stays)

| Track | Decision |
|---|---|
| **PyTorch sims** (11 legos + `_tn_carrier` + all gates) | **Sidelined**, not deleted. Work redone in Julia. Read-only reference for the rebuild. |
| **JAX sims** | **Keep running** — the numerical stress-test / cross-audit track. |
| **Python tool stack** (quimb, sympy, z3, cvc5, gudhi, …) | Replaced by Julia-native equivalents. numpy → control-only. |
| **Julia** | New canon: carrier, geometry, dynamics, QIT, constraints, proofs. |

Why Julia and not "PyTorch is wrong": PyTorch's ATen is genuinely non-numpy and fine for arrays. The reason
to move is that the *tensor-network + geometric-algebra* tooling is mature and rigorous in Julia and absent or
numpy-tainted in Python (quimb is numpy; peps-torch is numpy-tainted). Julia lets spinors be **geometric
objects** (Grassmann even-subalgebra elements) instead of `ℂ²/ℂ⁴` arrays that smuggle a fixed metric.

---

## 2. The two complementary substrates (a fork held open, not collapsed)

The research surfaced two computational philosophies. **They are not competitors — they are two views the
cross-audit compares, and they cover different parts of the object.** Both are kept.

### 2A. Tensor-network substrate — the *entanglement / QIT* view
Represent a many-body state as a tensor network; read admissible QIT entropies off it.
- **ITensors.jl + ITensorMPS.jl** — 1-D MPS/MPO; native SU(2). (carrier, verified)
- **ITensorNetworks.jl** — arbitrary-graph TNs incl. **small exact 3-D grids** (the PoC 3-D path).
- **TensorKit.jl** — category-theoretic tensors with **custom spinor vector spaces + non-Abelian symmetry**.
- **PEPSKit.jl** — 2-D iPEPS (CTMRG/boundary-MPS) on TensorKit; for *scalable 2-D shells*.
- **TNRKit.jl** — HOTRG / ATRG_3D renormalization for *scaling* layered/3-D-like systems.
- *Use for:* log-negativity, conditional mutual information `I(A:C|B)`, coherent information, cut entropy —
  the admissible-entropy readouts; the entanglement = geometry correspondence.

### 2B. Geometric-algebra spinor-field substrate — the *geometry / dynamics / branching* view
Represent each state as a **native spinor object** (no global tensor contraction); evolve on the manifold.
- **Grassmann.jl** — Weyl spinors as elements of `Cl(p,q)⁺`; geometric product at the type level; Hopf
  fibration as a direct `hopf_lift` map, not a bond-dimension approximation.
- **CliffordAlgebras.jl** — `Cl(3,0)` rotors; the Hopf map `ψ ↦ ψe₃ψ̃`, fibers as rotor orbits. (verified)
- **DifferentialEquations.jl + ManifoldDiffEq.jl** — spinor dynamics `dψ/dt = Hψ` with retraction keeping
  `ψ` on `S³`/the spinor manifold (no drift).
- **QuantumClifford.jl** — stabilizer/Clifford-group evolution tracking algebraic generators, not amplitudes.
- *Use for:* the geometry (fibration, chirality, winding), continuous dynamics, and the branch/prune ensemble.

**Routing rule:** entanglement/QIT claims → 2A (tensor networks); geometry/dynamics/branch-prune → 2B
(spinor fields). The cross-audit checks they agree on the **integer topological invariants** (linking, winding,
Chern), never on raw state vectors.

---

## 3. The shell / quasi-3-D architecture (nested Clifford shells)

True scalable 3-D PEPS does not exist in Julia and is #P-hard (`D¹²`+). The object is **stacked 2-D Clifford
shells** (nested Hopf tori), which is exactly the standard **quasi-3-D** approach — and it preserves the
fiber-bundle topology instead of flattening it.

- **Intra-shell (2-D surface):** each shell is a 2-D layer.
  - PoC: a grid of Grassmann **spinor objects** (`Array{Spinor,2}`), neighbor interaction = rotor geometric
    product `ψ_new = ∏ R_ij ψ_old`. Or an ITensorNetworks 2-D layer for the entanglement readout.
  - Scaling: a PEPSKit `InfinitePEPS` whose local space is a Grassmann/TensorKit spinor space.
- **Inter-shell (nesting = Hopf lift):** the coupling is the fiber-bundle map — the spinor of shell *n* is the
  **base coordinate** of the fiber at shell *n+1*. Implemented as `hopf_lift(SpinorShell{n}) -> SpinorShell{n+1}`
  in Grassmann (outer product + projection), encoding `S³→S²` exactly, not via bond dimension.
- **Scaling the stack:** TNRKit HOTRG to coarse-grain the layered network and find fixed points (the stable
  attractor configurations of the whole nested system).

PoC scale: **ITensorNetworks small exact 3-D** (`named_grid((2,2,2))` etc.) covers genuine 3-D topology before
any approximation is needed. The scaling fork (HOTRG vs quasi-2-D-slice vs — discouraged — JAX-hybrid) is
deferred until exact contraction is outgrown.

---

## 4. Branching & pruning — the possibility-field engine

Direct implementation of the primary object as an ensemble computation.

- **Branch:** `DifferentialEquations.jl` `EnsembleProblem` — spawn N trajectories (possible futures) from a
  perturbed spinor field (`prob_func` perturbs initial spinors on the Hopf manifold).
- **Evolve:** manifold-aware solver (RK4 on `S³` via ManifoldDiffEq) — each future evolves.
- **Prune:** `DiscreteCallback` enforcing **hard QIT-aligned constraints** at every step → `terminate!` a
  trajectory the instant it violates one:
  - geometric: `|ψ|² = 1`;
  - topological: local winding number consistent with the Hopf fibration;
  - evolutionary/QIT: fitness (entropy production / coherent information / capacity) above threshold.
- **Select:** `Attractors.jl` clusters survivors into basins; `basin_stability` = probability of a future
  (robust = large basin, fragile = small); `basin entropy` = fractal-boundary uncertainty → focus branching
  on high-entropy regions, prune low-entropy trivial ones.

This replaces "global tensor contraction of the full wavefunction" (exponential) with **constraint-pruned
ensemble sampling** — variation (branch) + selection (prune) → the attractor basins that define the survivor.
It is the literal computational form of "evolution works with constraints."

---

## 5. Constraint & proof layer (rigorous, not penalty-loss)

Replaces ad-hoc loss penalties with **hard structural constraints + rigorous proofs** — the
constraint-admissibility harness made executable.

**By-construction vs by-correction — the load-bearing asymmetry (this is *why* the cross-audit works).**
Julia enforces constraints **by construction**: a Grassmann spinor is a *type* whose geometric products close
to valid spinors (closure at dispatch), and ModelingToolkit solves `|ψ|²−1=0` as a DAE *simultaneously* with
the dynamics, so the constraint holds to solver tolerance structurally — not as a penalty. JAX enforces
**by correction**: native tensors carry no geometry, so the constraint is applied *after* each step
(custom_vjp tangent-space projection / renormalization inside `lax.while_loop` / penalty `λ(|ψ|²−1)²`). That
asymmetry is exactly why **Julia is the exact oracle and JAX the drifting approximation**, and it sharpens the
audit: if JAX's integer invariants drift from Julia's, the JAX projection is leaking (chirality/probability),
not a real physical effect. (JAX-side toolset for the parallel track: `diffrax`, `optax`, `riemannax`,
`jax.custom_vjp` — `(tbd)` candidate, validated against Julia, not canon.)

- **ModelingToolkit.jl** — conservation laws (spinor norm, chirality, probability) as **algebraic constraints
  (DAEs)** the solver respects structurally; `structural_simplify` eliminates redundant variables.
- **IntervalArithmetic.jl + BranchAndPrune.jl** — rigorous branch-and-prune: bisect state space, discard
  regions that *provably cannot* satisfy constraints; guarantees no valid future is wrongly pruned →
  **proof of which futures are impossible**.
- **HomotopyContinuation.jl** — solve the polynomial fixed-point system → **all** attractors/repellers
  algebraically (the complete critical-point map) before simulating.
- **Z3.jl** — SMT verdict-flip proofs (replaces z3/cvc5): claim true → UNSAT-negation; bound to measured values.
- **Attractors.jl / DynamicalSystems.jl** — basin verification (basin stability, tipping points, Wada basins).

Proof ladder (unchanged doctrine): `exists < runs < passes rerun < canonical by process`. A claim is canonical
only with: ModelingToolkit hard-constraint satisfaction + an interval/Z3 proof + basin verification + the
kill-controls of §7.

---

## 6. The cross-audit: Julia (oracle) ∥ JAX (stress-test)

The two tracks actively validate each other. **Compare integer topological invariants, never state vectors.**

- **Julia = algebraic oracle:** Grassmann/QuantumClifford give exact conservation (Hopf invariant, chirality
  eigenvalues) by type-closure. Deviation here = an algorithmic error, not numerical drift.
- **JAX = numerical stress-test:** push batch sizes / resolutions past Julia's precompile/memory limits.
- **Divergence detection:** geometric (not Euclidean) distance at synced checkpoints; compute the **linking /
  winding / Chern number** in both. Integer-valued invariants are the pass/fail:
  - JAX drifts, Julia constant → JAX custom-VJP / projection is leaking (chirality/probability);
  - both drift → discretization (RK order) too coarse for the Hopf curvature;
  - Julia exact but slow, JAX fast but drifting → use Julia state to periodically re-initialize JAX (shadowing).
- **Interop:** disk checkpoints (HDF5/Zarr) at topological events, not inner-loop data passing; power-spectrum +
  topological-invariant comparison. *(This cross-audit recipe is `(tbd)` candidate guidance from research, to be
  validated, not canon.)*

---

## 7. Success criteria & kill-controls (binding)

A Julia sim object is admissible only if its load-bearing claim dies under **all** applicable kill-controls:
- **pure-QIT:** the signal dies under **dephasing** (a commuting/classical operation) — no classical smuggle.
- **gauge-invariant:** invariant under local SU(2) (a CliffordAlgebras/Grassmann rotor).
- **topological:** the invariant is **integer** and constant over evolution; non-integer/drifting = QIT violation.
- **geometry-necessary:** flatten the connection / unlink the fibration → the claim dies.
- **information-necessary:** product/separable state → the claim → 0 (use no-classical-analog measures:
  log-negativity, negative conditional entropy — not measures with a classical shadow like bare `I(A:C|B)`).
- **carrier-genuine:** the carrier is the actual TN/spinor-field (bond ≥ 8 / real Schmidt rank), not a relabel.
- **no numpy:** the carrier + contraction touch zero numpy (Julia end-to-end).
- **candidates kept separate:** `log Z`, `I_c`, `I(A:B)`, log-negativity reported as distinct columns until the
  chart tests decide which carries Axis0 — never fused into one score.

---

## 8. Tool roster (status)

**Installed + verified live:** Grassmann, CliffordAlgebras, ITensors, ITensorMPS, ITensorNetworks,
DifferentialEquations, QuantumClifford, QuantumOptics, Z3, Symbolics, Graphs, TensorOperations, DynamicalSystems,
Attractors, ModelingToolkit, JSON. (Julia 1.12.6, project `system_v5/julia_carrier/`.)

**Installing (wave 2):** IntervalArithmetic, JuMP, HomotopyContinuation, Evolutionary, BlackBoxOptim,
TensorKit, PEPSKit.

**Queued (latest research):** TNRKit (HOTRG renormalization), ManifoldDiffEq (manifold ODE), BranchAndPrune
(rigorous pruning), NamedGraphs (ITensorNetworks 3-D grids).

**Discarded:** QuantumPEPS.jl (inactive, qubit-VQE, classical-smuggling). quimb/peps-torch (numpy).

---

## 9. Verified foundation (Phase 0 — done)

| Object | File | Result |
|---|---|---|
| Linking = log-negativity on ITensors, Clifford-rotor gauge-invariant, pure-QIT | `hopf_linking_itensors_clifford_object.jl` | LN = linking # (3/4/5), bond 8/16/32, all_pass |
| Clifford-native Hopf map (S³→S², exact fiber, linking #=1) | `hopf_map_clifford.jl` | base \|b\|=1, fiber dev=0, linking=1, pass |
| Unified geometry == information (same integer) | `geometry_is_information_unified.jl` | all match L=1/2/3 |

---

## 10. Phased build plan

- **Phase 0 — Foundation (done):** linking object + Hopf map + unified geometry==information on Julia.
- **Phase 1 — Stack install + validation (in progress):** finish wave-2 + queued; **smoke-test each package
  live** (resolved ≠ runs) — Grassmann Weyl spinor, ManifoldDiffEq retraction step, QuantumClifford stabilizer,
  Z3 verdict-flip, ITensorNetworks exact 3-D contraction, Attractors basin, BranchAndPrune interval prune.
- **Phase 2 — Spinor-field engine (2B):** Grassmann spinor type + `hopf_lift` + ManifoldDiffEq evolution +
  the EnsembleProblem branch/prune with hard constraints → first attractor basins of a single shell.
- **Phase 3 — Shell architecture:** `SpinorShell` (2-D grid of spinors), inter-shell Hopf-lift coupling, the
  nested-tori stack; TNRKit fixed points of the stack.
- **Phase 4 — Entanglement readouts (2A) on the shells:** log-negativity / `I(A:C|B)` / coherent information
  on ITensorNetworks views of the shells; confirm geometry==information at shell scale.
- **Phase 5 — Constraint proofs + basins:** ModelingToolkit hard constraints, HomotopyContinuation all
  fixed points, IntervalArithmetic/Z3 proofs, Attractors basin stability/entropy.
- **Phase 6 — Cross-audit vs JAX:** integer topological invariants (linking/winding/Chern) Julia ∥ JAX;
  divergence detection; shadowing re-init.
- **Phase 7 — Rebuild the manifold-layer sim set:** port the layer objects (Hopf, Weyl, Clifford, terrains,
  gluing, G-structure) onto this stack, geometry-native via Grassmann, each passing §7 kill-controls.

---

## 11. Open forks (held open — owner decides, not collapsed)

1. **Substrate routing:** TN (2A) vs spinor-field (2B) per claim — kept dual; the cross-audit is the arbiter.
2. **Scaling 3-D:** HOTRG-on-TensorKit (rigorous) vs quasi-2-D shell-slice (approximate) vs JAX-hybrid
   (discouraged — reintroduces smuggling). Decide at the exact-contraction wall.
3. **Carrier for 2-D shells:** ITensorNetworks (exact, verified) vs PEPSKit (scalable, symmetry-native) —
   validate PEPSKit live before adopting; `exists ≠ better`.
4. **Weyl-spinor metric:** `Cl(3,0)` (Euclidean, done) vs `Cl(3,1)` / `Cl(4,0)` (spacetime/chirality) — choose
   when Weyl chirality becomes load-bearing.

---

## 12. What this is NOT (anti-overclaim)

This is a plan + a verified Phase-0 foundation, not a finished system. The dual-substrate, shell architecture,
branch/prune engine, and cross-audit are **designed and tool-backed**, not yet built past Phase 0. The cross-audit
recipe and several research suggestions are `(tbd)` candidates to validate, explicitly not canon. No claim here is
`canonical by process`; the whole stack is pre-admission until the §7 kill-controls and §5 proofs are run per object.
