# Claude Layout Audit And Improvement

**Created:** 2026-05-22
**Status:** audit of pasted Claude layout; improvements patched into
`QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md`; no runtime promotion

## Verdict

The pasted Claude layout is useful after correction. It restores several
important source details, but it also tries to promote some exploratory
interpretations too far.

Net:

```text
accepted: terrain law restoration, A1/A6 derived-chain, engine triple-swap,
          fiber/base versus inner/outer distinction

fenced:   FGA/FSA names, flux as manifold-level/pre-axial, A6 left/right
          as the sole source definition

rejected: any claim that flux is already a root constraint, or that A4 is
          only an operator-pair selector
```

## Source-Locked Parts That Survive

### Constraint-Manifold Ladder

Survives.

The 20-layer ladder is source-backed:

```text
F01/N01
-> C
-> M(C)
-> A_i : M(C) -> V_i
-> H=C^2, D(C^2), Pauli basis
-> S^3
-> Hopf projection
-> torus strata
-> fiber/base loops
-> left/right sheets
-> runtime manifold
-> Xi bridge
-> rho_AB
-> Phi_0(rho_AB)
```

Improvement patched:

```text
The full packet now keeps the manifold as the active ratchet surface,
not a downstream decoration.
```

### Terrain Generator Laws

Survive, with one clarification.

Claude correctly restored the source laws:

```text
Se: dissipative Lindblad plus Hamiltonian perturbation
Ne: Hamiltonian circulation plus optional weak dissipator
Ni: ladder dissipator attractor plus Hamiltonian perturbation
Si: commuting Hamiltonian plus retained-strata projectors
```

Clarification:

```text
The source has two terrain count systems:

1. eight runtime terrains in the JUNGIAN table:
   Se_f, Si_f, Ne_f, Ni_f, Se_b, Si_b, Ne_b, Ni_b

2. eight sheet-specific generator realizations in the terrain packet:
   Funnel/Cannon, Vortex/Spiral, Pit/Source, Hill/Citadel
```

Both are useful. They are different projections:

```text
runtime terrain row = topology law + loop path
sheet-specific terrain law = topology law + Weyl sheet sign
full placement = topology law + sheet + loop path
```

Improvement patched:

```text
The full packet now requires stage receipts to declare:
terrain_table_id, sheet, path_geometry, chart_loop_role, and engine_type.
```

### Engine Triple Swap

Survives.

Claude's triple-swap formulation is a good compression of the source charts:

```text
engine type two = engine type one with:
fiber/base       swapped
deductive/inductive swapped
outer/inner role swapped
```

Improvement patched:

```text
QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md now contains
an Engine-Type Triple Swap section.
```

## Corrections / Fences

### Flux Evidence Already Exists

Correction to the audit wording:

```text
Flux/chiral-manifold behavior has already been simulated in candidate form.
```

Evidence surfaces include:

```text
grok_sim rough GStack receipts:
  Weyl chirality split
  flux holonomy pi
  stable repeat holonomy
  candidate manifold transforms staying on manifold

iter_160:
  flux doctrine marked derived/open
  chirality differential nonzero only with L/R Weyl split

iter_176-183:
  T1/T2 distinct attractors
  schedule-level pseudo-basins
  four N=2 schedule attractors
  coplanar basin geometry with macro-axis aligned against H direction

formal full-build plan receipts:
  exact-torch schedule memory, coupled E16, tensor, PEPS/PEPS3D first rungs,
  and Phi0/bridge attempts routed with non-admission boundaries
```

Therefore the correct fence is:

```text
open = canonical flux identification / placement / admission
not open = whether any flux-like or chiral-basin candidate was ever simulated
```

### Axis 3

Corrected safe form:

```text
geometry-level A3 = fiber versus lifted base
chart-level language = inner versus outer
engine type controls the mapping between them
```

Claude's "A3 outer/inner" is too shallow unless engine type is declared.

### Axis 4

Corrected safe form:

```text
Axis 4 = loop-order family:
U o E o U o E versus E o U o E o U
```

The runtime correlation:

```text
FeTi versus TeFi
```

is useful but should not replace the deeper order object.

### Axis 5

Corrected safe form:

```text
Axis 5 = {Ti, Te} dephasing/pinching versus {Fi, Fe} rotation/unitary
```

FGA/FSA are exploratory names only.

Admission test:

```text
FGA must reduce to finite dephasing/pinching contractions.
FSA must reduce to finite Hamiltonian adjoint rotations.
```

### Axis 6

Corrected safe form:

```text
source token law: up/down precedence, with b6 = -b0 b3
QIT audit layer: left/right action L_A(rho)=A rho, R_A(rho)=rho A
```

Do not collapse one into the other without a runtime row proving the mapping.

### Flux

Corrected safe form:

```text
flux = open derived candidate family
```

Manifold-level flux is a serious candidate, especially `J_geom`, but it is not
admitted as:

```text
a pre-axial root
an axis replacement
an engine-type determinant
```

## Improvements Patched Into Full Packet

Patched sections:

```text
Audit Delta From The Claude Layout
Engine-Type Triple Swap
Derived Axis Relations
Full Engine Runtime Object
```

Main practical improvement:

```text
future sims must now declare enough fields to prevent the same drift:
terrain law, sheet, path geometry, chart loop role, engine type, operator,
axis5 family, axis6 precedence, axis6 primitive side, closure, and functional.
```

## Next Sim Spec Delta

Any rebuild after this audit should use this minimum stage record:

```json
{
  "terrain_family": "Se|Ne|Ni|Si",
  "terrain_table_id": "Se_f|Se_b|Ne_f|Ne_b|Ni_f|Ni_b|Si_f|Si_b",
  "terrain_realization": "Funnel|Cannon|Vortex|Spiral|Pit|Source|Hill|Citadel",
  "sheet": "L|R",
  "engine_type": "type_1|type_2",
  "path_geometry": "fiber|lifted_base",
  "chart_loop_role": "inner|outer",
  "terrain_generator": "explicit matrix/superoperator",
  "judging_operator": "Ti|Te|Fi|Fe",
  "axis5_family": "dephasing|rotation",
  "axis6_token_precedence": "operator_first|terrain_first",
  "axis6_primitive_side": "left|right|both",
  "closure_type": "gksl|commutator|kraus|unitary_adjoint|composition",
  "functional_readout": "named readout or null",
  "physical_checks": {
    "trace": "pass/fail",
    "hermiticity": "pass/fail",
    "positivity": "pass/fail",
    "cp_or_choi": "pass/fail/not_applicable"
  }
}
```

This is the corrected base that prevents the next sim from reducing terrains
to token labels.
