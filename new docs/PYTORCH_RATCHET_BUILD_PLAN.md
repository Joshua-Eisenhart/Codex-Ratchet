# PyTorch Ratchet Build Plan

## Document Status
| Field | Value |
|-------|-------|
| **last_verified** | 2026-04-07 |
| **current_enforced** | Phase 1 (classical baselines) complete, Phase 2 (constraint cascade) complete |
| **discovered** | Computational graph = ratchet architecture (claim, not yet tested); ∇I_c as Axis 0 gradient field |
| **planned** | Phase 3-7 migration; TLA+ model checking for cascade ordering and ratchet liveness; formal ∇I_c derivation |

## Architectural model
The ratchet is a nested family of simultaneous constraint shells, not a ladder of replacements.

Let S0 ⊃ S1 ⊃ S2 ⊃ ... denote nested admissible state sets. Each layer adds constraints to the same state space. Higher layers do not erase lower layers; they refine them.

- Hopf tori are one shell.
- Weyl spinors are a more constrained shell.
- Clifford layers encode still more structure.
- Operator layers live on top of those shells.
- The engine runs at the most constrained level where all active shells are simultaneously present.

### Plan preservation note

The build plan must preserve the already-corrected operating order:
- the two root constraints bind the whole space
- candidate layers may be nested and simultaneously active
- the exact final layer order is still open
- likely candidate layers and likely candidate orders must remain non-canon until tested

That means the build program has two distinct jobs:
1. simulate each foundational lego independently
2. simulate which subsets and sequences of layers can actually nest on each other

Concrete preserved examples:
- density matrices are near-first admissible objects
- left/right Weyl spinors run on nested Hopf tori
- flux is a derived candidate family downstream of stagewise differential machinery
- bridge / cut-state / `Phi0` work comes after the relevant geometry/chirality/delta objects exist

## The computational claim
The PyTorch computational graph IS the ratchet.

Not a tool for simulating the ratchet — the architecture itself.

- Forward pass = exploring the allowed mathematical space.
- Backward pass = constraints flowing from output back to input, selecting what survives.
- Graph topology = the constraint manifold.
- Gradient = what is load-bearing.
- Zero gradient = what is redundant.

This is the non-classical retrocausal reading: not future-causes-past, but constraints-from-output-determine-input.

### Disconfirmation criteria
This claim is falsifiable. It would be wrong if:
1. **Gradient triviality:** Autograd ∇_η I_c gives no additional information beyond the numpy scalar I_c — i.e., the gradient direction is always trivially aligned with the parameter axis and its magnitude is predictable from finite differences alone.
2. **Graph topology independence:** The computational graph topology has no effect on the dynamics — i.e., any graph wiring (chain, star, tree) gives the same selection outcome for the same inputs.
3. **Forward sufficiency:** Backprop constraint flow produces the same selection as forward-only evaluation — i.e., iterating forward passes with rejection sampling matches backward-pass constraint selection in both result and computational cost.
4. **Substrate equivalence:** PyTorch-native legos match numpy baselines exactly with zero divergence across all 28 irreducible families — no family shows substrate-dependent behavior.

**Falsification protocol (Phase 3):**
For each of the 28 irreducible families:
- Compute I_c via numpy (scalar). Compute ∇_η I_c via autograd (vector). Compare: does the gradient contain information not recoverable from finite-difference approximation of the scalar? Specifically: is autograd ∇I_c cheaper, more accurate, or directionally different from (I_c(η+ε) - I_c(η-ε))/2ε?
- Permute graph topology (at minimum: chain vs star vs random). Measure: does the constraint cascade produce different surviving sets?
- Run forward-only rejection sampling alongside backward-pass selection. Compare: same survivors? Same cost? Same numerical precision?
- If ALL four conditions show null results across ALL 28 families, numpy is sufficient and the PyTorch claim is falsified. Partial nulls (some families show divergence, others don't) require analysis of which structural features predict substrate sensitivity.

## Axis 0: formal math

Axis 0 is not a scalar at one cut. It is a gradient field on the shell topology.

### Definition
Let η ∈ ℝⁿ parameterize the nested shell family (e.g., torus radii, Clifford angles). Let ρ(η) be a differentiable density operator on the composite system AB. Let I_c(A⟩B) = S(B) - S(AB) be the coherent information. Then:

**Axis 0 := ∇_η I_c(ρ(η))**

This is a vector field on the shell parameter space, not a scalar.

### Connection to quantum Fisher information (QFI)
The quantum Fisher information for parameter η is:

F_Q(η) = 4 ∂²D_B(ρ(η), ρ(η + dη)) / ∂(dη)²

where D_B is the Bures distance: D_B(ρ, σ) = 2(1 - √F(ρ, σ)), and F is the Uhlmann fidelity.

The Cramér-Rao bound gives: Var(η̂) ≥ 1/F_Q(η).

**Key relationship:** ∇I_c tells you the direction of steepest change in coherent information. F_Q tells you how distinguishable nearby states are along that direction. If ∇I_c is large where F_Q is also large, the gradient is metrologically meaningful — the shell parameter controls a physically distinguishable degree of freedom.

### Connection to Bures metric
The Bures metric on the state manifold is:

ds²_B = (1/4) Tr[dρ · L]

where L is the symmetric logarithmic derivative (SLD): dρ/dη = (Lρ + ρL)/2.

The QFI is the Bures metric component: F_Q(η) = Tr[ρ L²].

∇_η I_c lives in the tangent space of the shell parameter manifold. The Bures metric determines the natural inner product on that tangent space. This means ∇I_c has a well-defined magnitude (not just direction) when measured against Bures geometry.

### Connection to Berry curvature
If the shell family traces a closed loop in parameter space η(t), the Berry phase is:

γ = ∮ A · dη,  where A_μ = i⟨ψ|∂_μψ⟩

The Berry curvature is F_μν = ∂_μ A_ν - ∂_ν A_μ.

**Key relationship:** Berry curvature measures the geometric (non-dynamical) content of the shell family. Where Berry curvature is nonzero, the shell family has topological content that cannot be removed by reparameterization. If ∇I_c aligns with regions of high Berry curvature, the coherent information gradient is geometrically protected — it survives smooth deformations.

### Autograd implementation (planned, Phase 5)
```python
eta = torch.tensor(eta_value, requires_grad=True)
state = hopf_torus_state(eta)
rho_AB = entangle(state)
ic = coherent_information(rho_AB)
ic.backward()
axis_0 = eta.grad  # ∇_η I_c
```

### Open questions (discovered, not yet resolved)
- Is ∇I_c continuous across shell boundaries, or does it have discontinuities at constraint transitions (L4, L6)?
- Does the QFI diverge at the same points where the constraint cascade kills families?
- Is there a Berry phase associated with the full L0-L7 loop, and if so, is it quantized?

## Why numpy is only the baseline
numpy arrays are Cartesian grids. They represent states as coordinate vectors in a fixed basis.

That imports:
- Cartesian ontology
- Platonic representation
- classical computation without gradient flow

PyTorch tensors with autograd are:
- relational
- constraint-based
- non-Cartesian

## Phase 1: classical baselines (done)
The numpy legos are the classical baseline set (count: see `system_v4/probes/` directory). They are useful because they show what works before the constraint layers are applied.

Their job is not to define the target architecture. Their job is to reduce presupposition.

The baseline families include density matrices, Hopf tori, spinor transport, Cl(3)/Cl(6), channels, entropies, steering/coherence, Bell tests, topology, QEC, tensor networks, quantum Shannon, QKD, QCA, holography, RMT, and the rest of the current lego inventory.

## Phase 2: constraint cascade (done)
The L0-L7 cascade is the discovered narrowing pattern.

- L0 (N01): 53 legos. Bifurcation into spectral + geometric.
- L1 (CPTP): 53 survive.
- L2 (d=2+Hopf): 61 survive.
- L3 (chirality): 66 survive.
- L4 (composition): 48 survive. Absolute measures die.
- L5 (su(2)): 48 survive.
- L6 (irreversibility): 43 survive. Reversible legos die.
- L7 (dual-type): 43 survive.
- Minimal set: 28 irreducible.
- Independent observables: 9.

Core pattern:
- geometry enriches (L0-L3)
- dynamics selects (L4)
- ratchet kills reversible (L6)
- redundancy collapses (43 → 28 → 9)

## Negative batteries
The negative batteries are not optional. They are the boundary structure of the system.

Current status: see battery index files in `system_v4/probes/` for current counts and coverage. They cover density matrices, entropy boundaries, channels, entanglement, geometry, topology, compound failures, advanced legos, cascade stress tests, boundary sweeps, and mega boundary sweeps.

## What the current math says
- The engine is separable without an entangling gate.
- Discord can remain when entanglement is zero.
- Geometry that survives is CP¹ / Fubini-Study.
- L4 and L6 are structural kill points.
- Kills commute under the discovered ordering.
- The classical baseline is not wasted; it is the prerequisite comparison class.

---

## Phase 3: PyTorch-native legos (next)
The next phase is not “more demos.” It is rebuilding the irreducible set as differentiable modules.

Goal:
- each surviving family becomes a `torch.nn.Module`
- each module exposes parameters, forward maps, and gradients
- each module is tested against a classical baseline and at least one negative control
- each module should use the actual stack load-bearing where relevant, not only declare the stack in a manifest
- backprop is part of the computation, not just a later interpretation

### Hard-way requirement

The PyTorch phase is only aligned with the actual plan if it does the hard work on the real math objects:
- actual density matrices
- actual channels / generators
- actual spinor / torus geometry
- actual graph / topology structures when those structures are part of the object

Not enough:
- scalar surrogate losses detached from the object family
- manifest-only proof / graph declarations
- compound ranking before the foundations are explicit

Example shape:
```python
class DensityMatrix(torch.nn.Module):
    def __init__(self, bloch_params):
        super().__init__()
        self.bloch = torch.nn.Parameter(bloch_params)

    def forward(self):
        rho = torch.eye(2, dtype=torch.complex64) / 2
        for i, sigma in enumerate(paulis):
            rho = rho + self.bloch[i] * sigma / 2
        return rho
```

## Phase 4: constraint graph as simultaneous differentiable shells
L0-L7 become simultaneously active differentiable constraint modules — not a sequential pipeline where data flows through one stage at a time, but nested shells that all constrain the same state space at once.

The important point is not that the graph exists.
The important point is that the graph encodes the admissibility structure: which states survive all shells simultaneously.

## Phase 5: Axis 0 via autograd
Axis 0 is the gradient field of coherent information across shell parameters.

```python
eta = torch.tensor([TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER], requires_grad=True)
states = hopf_torus_states(eta)
rho_AB = entangling_channel(states)
ic = coherent_information(rho_AB)
ic.sum().backward()
axis_0_gradient = eta.grad
```

This is the formal version of your retrocausal point:
constraints flow backward through the shell graph.

## Phase 6: full ratchet as GNN
PyG is not decorative. It is the graph substrate for the computation.

- terrain nodes carry state features
- operator nodes carry channel parameters
- shell nodes carry geometric parameters
- message passing is the dynamics
- training objective is a constraint-aware quantity such as sustained I_c

## Phase 7: validation against classical baselines
PyTorch-native results must be compared against the numpy baseline.

Where they agree: substrate-independent truth.
Where they diverge: that divergence is the quantum content that the classical substrate misses.

---

## Tool integration requirements

| Tool | Role | Must do | Must not be reduced to | Status |
|------|------|---------|------------------------|--------|
| PyTorch 2.8 | core substrate | tensors, gradients, autograd | numpy wrapper | installed |
| PyG 2.7 | graph dynamics | message passing as computation | graph inspection only | installed |
| z3 4.16 | structural proof | UNSAT impossibility checks | post-hoc SAT check | installed |
| cvc5 1.3 | SMT cross-check + synthesis | cross-check z3 UNSAT; SyGuS for minimal generators | redundant z3 clone | **NEW — installed** |
| sympy 1.14 | symbolic derivation | derive formulas before numerics | verify-only layer | installed |
| clifford 1.5 | geometric algebra | native Cl(3)/Cl(6) computation | roundtrip test | installed |
| geomstats 2.8 | Riemannian manifolds | shell metrics, geodesics, curvature, Fréchet means | numpy wrapper with manifold labels | **NEW — installed** |
| e3nn 0.6 | E(3)-equivariant NN | symmetry-native PyTorch (O(3)/SU(2)) | decorative equivariance claim | **NEW — installed** |
| rustworkx 0.17 | fast graph kernels | DAG ordering, dependency/routing/causal workloads | NetworkX clone without using its speed | **NEW — installed** |
| XGI 0.10 | hypergraphs + simplicial | multi-way operator/state/shell interactions | pairwise graph with extra labels | **NEW — installed** |
| TopoNetX 0.4 | cell-complex topology | higher-order topological structure | Betti-number checker | installed |
| GUDHI 3.12 | persistent homology / TDA | filtrations, persistence diagrams, simplicial/Rips | unused import | **was installed, now canonical** |
| Lean 4 | interactive theorem prover | math formalization above SMT | — | **planned — not installed** |
| TLAPS | temporal logic model checking | ratchet safety/liveness, shell nesting invariants | post-hoc narrative | **planned — not installed** |

### TLA+ integration plan (planned)
TLA+ (see [TLAPM Proofs](https://proofs.tlapl.us/doc/web/content/Home.html)) is a formal specification language for verifying temporal properties of systems. Target use cases:
- **Ratchet irreversibility:** Prove that once a family is killed at layer L_k, no subsequent layer can revive it.
- **Shell nesting invariant:** Prove S0 ⊃ S1 ⊃ S2 ⊃ ... is maintained under all allowed operations.
- **Cascade ordering:** Verify that the kill ordering (L4 kills absolute measures, L6 kills reversible) is a necessary consequence of the constraint definitions, not an accident of sim execution order.
- **Liveness:** The ratchet eventually reaches a fixed point (the 28 irreducible families are stable under further constraint application).

Not yet installed. Will require TLAPM (TLA+ Proof Manager) for machine-checked proofs.

## Migration Registry

All irreducible families from the minimal surviving set (currently 28 per L0-L7 cascade — this count is discovered, not prescribed; if the cascade is re-run with different constraints, the number may change). Each must be migrated from numpy baseline to torch module, tested against baseline, and paired with a negative battery.

| # | Irreducible family | Numpy baseline | Baseline? | Torch target | Tools needed | Negative battery | Status |
|---|---|---|---|---|---|---|---|
| 1 | density_matrix | sim_pure_lego_density_matrices.py | YES | torch DensityMatrix module | sympy, z3 | negative_density_matrices | PASS 2026-04-08 |
| 2 | purification | sim_pure_lego_density_matrices.py | PARTIAL | torch Purification module | sympy, z3 | negative_density_matrices | PASS 2026-04-08 |
| 3 | z_dephasing | sim_pure_lego_channels_choi_lindblad.py | YES | torch ZDephasing module | z3, clifford | negative_channels | PASS 2026-04-08 |
| 4 | x_dephasing | sim_pure_lego_channels_choi_lindblad.py | YES | torch XDephasing module | z3, clifford | negative_channels | PASS 2026-04-08 |
| 5 | depolarizing | sim_pure_lego_channels_choi_lindblad.py | YES | torch Depolarizing module | z3 | negative_channels | PASS 2026-04-08 |
| 6 | amplitude_damping | sim_pure_lego_channels_choi_lindblad.py | YES | torch AmplitudeDamping module | z3, sympy | negative_channels | PASS 2026-04-08 |
| 7 | phase_damping | sim_pure_lego_channels_choi_lindblad.py | YES | torch PhaseDamping module | z3 | negative_channels | PASS 2026-04-08 |
| 8 | bit_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch BitFlip module | z3 | negative_channels | PASS 2026-04-08 |
| 9 | phase_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch PhaseFlip module | z3 | negative_channels | PASS 2026-04-08 |
| 10 | bit_phase_flip | sim_pure_lego_channels_choi_lindblad.py | YES | torch BitPhaseFlip module | z3 | negative_channels | PASS 2026-04-08 |
| 11 | unitary_rotation | sim_pure_lego_channels_choi_lindblad.py | PARTIAL | torch UnitaryRotation module | clifford, sympy | negative_channels | PASS 2026-04-08 |
| 12 | z_measurement | **NONE** | **NO** | torch ZMeasurement module | z3 | negative_channels | PASS 2026-04-08 |
| 13 | CNOT | sim_pure_lego_gates_decompositions.py | YES | torch CNOT module | z3, sympy | negative_entanglement | PASS 2026-04-08 |
| 14 | CZ | sim_pure_lego_gates_decompositions.py | YES | torch CZ module | z3 | negative_entanglement | PASS 2026-04-08 |
| 15 | SWAP | sim_pure_lego_gates_decompositions.py | YES | torch SWAP module | z3 | negative_entanglement | PASS 2026-04-08 |
| 16 | Hadamard | sim_pure_lego_stabilizer_magic.py | YES | torch Hadamard module | z3, clifford | negative_channels | PASS 2026-04-08 |
| 17 | T_gate | sim_pure_lego_stabilizer_magic.py | YES | torch TGate module | z3 | negative_channels | PASS 2026-04-08 |
| 18 | iSWAP | sim_pure_lego_gates_decompositions.py | YES | torch iSWAP module | z3 | negative_entanglement | PASS 2026-04-08 |
| 19 | cartan_kak | sim_pure_lego_gates_decompositions.py | YES | torch CartanKAK module | sympy, clifford | negative_entanglement | PASS 2026-04-08 (16.7s) |
| 20 | eigenvalue_decomposition | sim_pure_lego_density_matrices.py | YES | torch EigenDecomp module | sympy | negative_density_matrices | PASS 2026-04-08 |
| 21 | husimi_q | sim_pure_lego_wigner_quasiprobability.py | YES | torch HusimiQ module | sympy | negative_density_matrices | PASS 2026-04-08 |
| 22 | l1_coherence | sim_pure_lego_majorization_steering_coherence.py | YES | torch L1Coherence module | z3, sympy | negative_entropy_boundaries | PASS 2026-04-08 |
| 23 | relative_entropy_coherence | sim_pure_lego_majorization_steering_coherence.py | YES | torch RECoherence module | z3, sympy | negative_entropy_boundaries | PASS 2026-04-08 |
| 24 | wigner_negativity | sim_pure_lego_wigner_quasiprobability.py | YES | torch WignerNegativity module | sympy | negative_density_matrices | PASS 2026-04-08 |
| 25 | hopf_connection | sim_pure_lego_quaternion_octonion.py | YES | torch HopfConnection module | clifford, toponetx | negative_geometry | PASS 2026-04-08 |
| 26 | chiral_overlap | **NONE** | **NO** | torch ChiralOverlap module | clifford | negative_geometry | PASS 2026-04-08 |
| 27 | mutual_information | sim_pure_lego_all_axes_discord.py | YES | torch MutualInformation module | z3, sympy | negative_entropy_boundaries | PASS 2026-04-08 |
| 28 | quantum_discord | sim_pure_lego_all_axes_discord.py | YES | torch QuantumDiscord module | z3, sympy | negative_entropy_boundaries | PASS 2026-04-08 (C4 bug under fix) |

## Folder structure
```
/new docs/                              ← active prototyping docs
/new docs/new content/                  ← research reference
/system_v4/probes/                      ← sim code
/system_v4/probes/a2_state/sim_results/  ← JSON results
/READ ONLY Legacy core_docs/            ← archived old core_docs
/system_v5/READ ONLY Reference Docs/     ← selected legacy reference
```
