# PyTorch Ratchet Build Plan

## The Architectural Insight

The PyTorch computational graph IS the ratchet. Not a tool for simulating the ratchet — the architecture itself.

**Forward pass** = exploring the allowed mathematical space. All the density matrices, operators, geometries that COULD exist at this constraint layer.

**Backward pass** = constraints flowing from output back to input, selecting what survives. The gradient at layer k depends on layers k+1, k+2, ... all the way to the output. The future constrains the past. This is the non-classical "retrocausality" — not future-causes-past, but constraints-from-output-determine-input.

**Graph topology** = the constraint manifold. Which nodes connect to which determines what's computable. The topology IS the constraint, not a container for the constraint.

**Gradient** = what's load-bearing. If ∂output/∂parameter ≈ 0, that parameter doesn't matter — it's redundant.

**Axis 0** = ∇I_c on the shell topology. The gradient of coherent information with respect to the torus shell parameter η, flowing backward through the computational graph. Not a scalar at one cut. A gradient field on the manifold.

```python
# Axis 0 as autograd
eta = torch.tensor(eta_value, requires_grad=True)
state = hopf_torus_state(eta)           # differentiable: geometry → state
rho_AB = entangle(state)                # differentiable: state → joint
ic = coherent_information(rho_AB)       # differentiable: joint → I_c
ic.backward()                           # constraint flow: I_c → η
axis_0 = eta.grad                       # THIS IS AXIS 0
```

## Why numpy fails

numpy arrays are Cartesian grids. They represent states as coordinate vectors in a fixed basis. This imports:
- **Cartesian ontology**: states have definite values at grid points
- **Platonic representation**: the array IS the state (reification)
- **Classical computation**: no gradient flow, no constraint propagation

PyTorch tensors with autograd are:
- **Relational**: the computational graph traces RELATIONSHIPS between operations
- **Constraint-based**: backprop flows constraints backward (what must the input have been to produce this output?)
- **Non-Cartesian**: the graph topology, not a coordinate system, determines what's computable

## What exists (Phase 1-2: DONE)

### Phase 1: Classical baselines
84 numpy legos verified against theory. These show what math works in a classical computation substrate. They are the BEFORE picture — not the answer.

Legos cover: density matrices, Hopf tori, spinor transport, Cl(3)/Cl(6), gates, decompositions (Schmidt/SVD/Cartan), all operator axes, QFI/WY/QGT, channels/Choi/Lindblad/Stinespring, majorization/steering/coherence, Bell/witnesses/steering, symplectic/Kähler/Weyl, ML mappings, QEC (3-qubit + Steane + surface), SIC-POVM/MUB, Majorana/spinor reps, quantum thermo/Landauer, Wigner quasi-probability, Petz recovery, resource theories, quaternions/octonions, channel capacity/degradability, process tomography/diamond norm, Lorentz/SLOCC, contextuality/KS, DFS/noiseless, quantum Markov, teleportation/superdense, state discrimination/Helstrom, quantum walks, f-divergences/sandwiched Rényi, quantum chaos/ETH, random circuits/typicality, stabilizer/magic, de Finetti/symmetry, no-go theorems, hypothesis testing, entanglement swapping/distillation, quantum metrology, quantum Shannon protocols, tensor networks (MPS/MERA), cloning/QKD/illumination, QCA/Lieb-Robinson/OTOC, quantum games/Bayesian/Sanov, Wasserstein transport, reference frames/asymmetry, quantum combs/process tensors, holographic codes/toy AdS-CFT, knot invariants/topological entropy, adiabatic/VQE/QAOA, free probability/RMT, Pauli/Clifford hierarchy/Jordan/Schur-Weyl algebras.

### Phase 2: Constraint cascade
L0-L7 mapped. The narrowing pattern discovered:
- L0 (N01): 53 legos. BIFURCATION: 34 spectral + 19 geometric. z3 proves Berry without complex = UNSAT.
- L1 (CPTP): 53 survive. 8 reduced by monotonicity.
- L2 (d=2+Hopf): 61 survive. +5 new Hopf legos. z3 proves d=2 forces exactly 3 Pauli generators.
- L3 (chirality): 66 survive. +5 chirality legos. 37 require chirality. z3 proves σ_y forced as antisymmetric.
- L4 (composition): 48 survive. **18 KILLED.** Absolute measures die. Relative survive.
- L5 (su(2)): 48 survive. 27 require su(2).
- L6 (irreversibility): 43 survive. **5 KILLED.** Reversible legos die. z3 proves fixed-point uniqueness.
- L7 (dual-type): 43 survive. 21 type-sensitive.
- Minimal set: 28 irreducible (15 redundant purity proxies). 9 independent observables.

**The pattern:** Geometry enriches (L0-L3: 53→66). Dynamics selects (L4: 66→48). Ratchet kills reversible (L6: 48→43). Redundancy collapses (43→28→9 independent).

### Negative batteries (11 complete, 107+ failure modes)
Density matrices, entropy boundaries, channels, entanglement, geometry, topology, compound failures, advanced legos, constraint cascade stress test, boundary sweeps, mega boundaries.

### Key findings
- Engine is SEPARABLE without entangling gate (discord only, zero entanglement)
- Discord-without-entanglement gap = 0.25 (engine's regime)
- I_c = +0.457 on 2-qubit WITH entangling gate
- Entropy: MI + min-entropy constraint-selected, vN is 9th
- Geometry: CP¹/Fubini-Study THE surviving geometry
- Y-axis not special (rotational symmetry, convention only)
- Mass equivalence: evolution = engine (Fisher = Cramér-Rao exact, error threshold +14%)
- z3: L4 requires L0, L6 requires L4. Dependencies structural (UNSAT). Kills commute.

---

## What's needed (Phase 3-7: NEXT)

### Phase 3: PyTorch-native legos
Rebuild the 28 irreducible legos as differentiable PyTorch modules. Each becomes a `torch.nn.Module` with parameters that autograd can differentiate through.

```python
class DensityMatrix(torch.nn.Module):
    """Density matrix as differentiable torch module."""
    def __init__(self, bloch_params):
        super().__init__()
        self.bloch = torch.nn.Parameter(bloch_params)  # 3 real params
    
    def forward(self):
        # Pauli decomposition: ρ = (I + r·σ)/2
        rho = torch.eye(2, dtype=torch.complex64) / 2
        for i, sigma in enumerate(paulis):
            rho = rho + self.bloch[i] * sigma / 2
        return rho
    
    def entropy(self):
        rho = self.forward()
        evals = torch.linalg.eigvalsh(rho)
        return -torch.sum(evals * torch.log2(evals.clamp(min=1e-15)))
```

Key: `torch.nn.Parameter` makes it differentiable. `autograd` can compute ∂entropy/∂bloch.

### Phase 4: Constraint graph as differentiable pipeline
Build L0-L7 as a sequence of differentiable transformations:

```python
class ConstraintCascade(torch.nn.Module):
    def __init__(self):
        self.L0_noncommutation = NoncommutationConstraint()
        self.L1_cptp = CPTPConstraint()
        self.L2_hopf = HopfCarrierConstraint()
        # ... through L7
    
    def forward(self, lego_set):
        surviving = self.L0_noncommutation(lego_set)
        surviving = self.L1_cptp(surviving)
        # ... through L7
        return surviving
    
    # Backward: gradient flows from what survived back to what was tested
    # The gradient at each layer = the selection pressure at that layer
```

### Phase 5: Axis 0 via autograd
The gradient of coherent information with respect to torus shell parameter η:

```python
eta = torch.tensor([TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER], requires_grad=True)
states = hopf_torus_states(eta)          # differentiable torus → spinor
rho_AB = entangling_channel(states)      # differentiable entangling
ic = coherent_information(rho_AB)        # differentiable I_c
ic.sum().backward()                      # constraint flow backward
axis_0_gradient = eta.grad               # ∇I_c on shell manifold = Axis 0
```

This is not a scalar. It's a gradient FIELD on the nested torus structure.

### Phase 6: Full ratchet as GNN
PyG graph neural network where:
- Terrain nodes carry quantum state features (torch tensors)
- Operator nodes carry channel parameters (learnable)
- Torus nodes carry geometric parameters (η, differentiable)
- Message passing = dynamics (state flows along edges)
- The GNN IS the engine (not a simulation OF the engine)
- Training objective: maximize sustained I_c (Axis 0 gradient)
- The learned parameters ARE the constraint manifold

### Phase 7: Validation against classical baselines
- Run PyTorch ratchet against numpy baselines
- Same physics, different computation substrate
- Where they AGREE: substrate-independent truth (the math is correct regardless)
- Where they DISAGREE: the substrate matters (classical vs quantum computation)
- The disagreements ARE the quantum content — what numpy can't capture

---

## Tool integration requirements

| Tool | Role | Not this | This instead |
|------|------|----------|--------------|
| PyTorch | Core computation substrate | Wrapper around numpy | ALL tensors, ALL operations, ALL gradients |
| PyG | Message passing dynamics | Build graph, inspect | Message passing IS the dynamics. GNN IS the engine. |
| z3 | Constraint proofs | Post-hoc SAT check | UNSAT impossibility proofs at every structural claim |
| sympy | Symbolic derivation | Verify known formula | Derive gradient formulas BEFORE numerical computation |
| clifford | Geometric algebra | Roundtrip test | Cl(3)/Cl(6) as torch-compatible computation substrate |
| TopoNetX | Topology | Verify Betti numbers | Cell complex topology SHAPES the PyG graph |

---

## Folder structure
```
/new docs/                             ← Active prototyping docs
/new docs/new content/                 ← Research reference (18+ math files)
/system_v4/probes/                     ← Sim code (84 numpy legos + engines)
/system_v4/probes/a2_state/sim_results/ ← 530+ JSON results
/READ ONLY Legacy core_docs/           ← Archived old core_docs
/system_v5/READ ONLY Reference Docs/   ← Selected legacy reference
```
