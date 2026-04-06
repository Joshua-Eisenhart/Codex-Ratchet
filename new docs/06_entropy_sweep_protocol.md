# Entropy Sweep Protocol — Base Constraints Upward

## Purpose
Do not assume a single entropy functional for the whole stack.
At each admissible layer, test the entropy family that the layer may force.
Only promote a measure when the layer rejects the alternatives.

## Core rule
Entropy is not primitive.
Entropy is a later admissible measure on a constrained substrate.
The correct quantity may differ by layer.

## Known layer placement from the stack
- Layer 17: signed/unsigned entropy objects become admissible
- Layer 18: Axis 0 kernel / preferred signed scalar on bridge output
- Layer 19: dynamics on entropy

Earlier layers must still be tested because they constrain which entropy family survives.

## Candidate entropy families to sweep

### Classical / scalar families
- Shannon entropy
- Von Neumann entropy
- Rényi entropy family
- Tsallis entropy
- min-entropy
- max-entropy
- relative entropy / divergence forms

### Bipartite / cut-state families
- conditional entropy S(A|B)
- mutual information I(A:B)
- coherent information I_c(A⟩B)
- entanglement entropy
- entanglement spectrum
- logarithmic negativity
- negativity

### Geometry-sensitive families
- shell-cut weighted entropy
- bridge-weighted coherent information
- history-window entropy
- transport-weighted entropy
- operator-ordered entropy under left/right action asymmetry

## What to test at each layer
For every candidate entropy family, check:
1. admissibility on the current layer object
2. sensitivity to the layer’s geometric constraint
3. sensitivity to the known negative controls
4. invariance or noninvariance under the layer’s allowed symmetries
5. whether the measure survives composition-order changes
6. whether the measure survives chirality or bridge ablations

## Layered interpretation
- Low layers: test whether the candidate even makes sense on the current object
- Mid layers: test whether the candidate distinguishes geometry from fake geometry
- Bridge layers: test whether the candidate sees real bipartite structure
- Entropy layers: test which signed/unsigned quantity is actually forced
- Axis layers: test which scalar remains stable under the admitted dynamics

## Current evidence from the stack
- Shannon/purity shortcuts were killed in the entropy-structure search
- von Neumann entropy survived that search
- mutual information alone did not kill fake coupling in the entanglement-witness search
- concurrence/negativity were more discriminating than MI there
- coherent information is currently the leading signed cut quantity in the cut-state / bridge family docs

## Important correction
Do not collapse these into one universal metric.
The stack already suggests different quantities are load-bearing at different stages:
- S(ρ) for state entropy structure
- S(A|B) / I_c for signed cut behavior
- concurrence / negativity for entanglement witness behavior
- mutual information for total correlation, but not as the sole witness

## Promotion rule
A measure becomes primary only if it survives the relevant layer’s geometry, bridge, and negative-control tests.
Until then it remains a candidate family, not a canon law.
