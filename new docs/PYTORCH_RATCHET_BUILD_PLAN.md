# PyTorch Ratchet Build Plan

## Phase 1: Classical Baselines (DONE)
84 numpy legos verified. These show what math works in a classical computation substrate. They are the BEFORE picture.

## Phase 2: Constraint Cascade (DONE)
L0-L7 mapped. Shows what survives under constraints. 53→66→48→43→28 irreducible. 9 independent observables. The cascade reveals: geometry enriches, dynamics selects, ratchet kills reversible.

## Phase 3: PyTorch-Native Legos (NEXT)
Rebuild the 28 irreducible legos in PyTorch tensors with autograd. Each lego becomes a differentiable module:
```python
class DensityMatrix(torch.nn.Module):
    def __init__(self, bloch_params):
        self.bloch = torch.nn.Parameter(bloch_params)
    def forward(self):
        return (torch.eye(2) + sum(b*s for b,s in zip(self.bloch, paulis))) / 2
```

## Phase 4: Constraint Graph
Build the L0-L7 cascade as a PyTorch computational graph:
- Each constraint layer = a differentiable transformation
- Forward: apply all constraints in order
- Backward: gradient flows from output (what survived) back to input (what was tested)
- The gradient at each layer = the selection pressure

## Phase 5: Axis 0 via Autograd
The gradient of coherent information with respect to torus shell parameter η:
```python
eta = torch.tensor(eta_value, requires_grad=True)
state = hopf_torus_state(eta)        # differentiable torus construction
rho_AB = entangle(state)             # differentiable entangling
ic = coherent_information(rho_AB)    # differentiable I_c
ic.backward()                        # constraint flow
axis_0_gradient = eta.grad           # Axis 0 = this gradient field
```

## Phase 6: Full Ratchet as GNN
PyG graph neural network where:
- Terrain nodes carry quantum state features
- Operator nodes carry channel parameters
- Torus nodes carry geometric parameters
- Message passing = dynamics
- The GNN IS the engine
- Training objective: maximize sustained I_c (Axis 0)
- The learned parameters ARE the constraint manifold

## Phase 7: Validation
- Compare PyTorch ratchet against numpy baselines
- Same physics, different substrate
- Where they agree: substrate-independent truth
- Where they disagree: the substrate matters (classical vs quantum computation)
- The disagreements ARE the quantum content

## Tool Integration
- z3: constraint proofs at every phase (UNSAT = impossible = quantum constraint)
- sympy: symbolic derivation of gradient formulas before numerical computation
- clifford: Cl(3)/Cl(6) as torch-compatible geometric algebra
- TopoNetX: cell complex topology provides the graph structure for PyG
- PyG: message passing IS the dynamics, autograd IS the constraint flow
