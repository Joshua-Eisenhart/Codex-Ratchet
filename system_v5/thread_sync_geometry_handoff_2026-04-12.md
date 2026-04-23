# Hermes thread sync handoff — geometry/micro-lego correction

Date: 2026-04-12
Purpose: sync another Hermes thread to the corrected bounded process.

## Status
This is a handoff note, not a promotion surface.
Do not treat it as authority over the system docs.
It exists only to preserve thread-local corrections and current process understanding.

## Hard corrections from user

1. Do NOT skip ahead to flux.
- Flux must wait until geometry legos are done and the constraint manifold is running as layered geometry.
- Minimal prerequisite is at least:
  - nested Hopf tori
  - left/right Weyl spinors on that geometry
  - Pauli matrices acting on those Weyl spinors
- Likely additional simultaneous lower layers are also required before flux is meaningful.

2. Do NOT skip ahead to entropy.
- Discussing later entropy / Phi0 / bridge readiness at this stage breaks the bounded ordered task rules.
- For the current task framing, entropy is blocked.

3. Current lego docs are still too coarse.
- `16_lego_build_catalog.md` and `17_actual_lego_registry.md` are not yet fine-grained enough.
- The next required decomposition layer is below the current lego layer.

## Required process discipline

Hermes must follow this order strictly:

1. tiny base legos
2. tiny hardening passes on single base legos
3. tiny pairwise couplings between already-earned base legos
4. tiny 3-object assemblies
5. only later larger assemblies
6. only much later correlation / entropy / bridge / flux / Axis work

Never jump from isolated lower-piece existence to higher-layer readiness.
Layered coexistence matters more than isolated existence.

## Micro-lego doctrine

Each bounded task should target exactly one of:
- one math object
- one law
- one invariant
- one equivalence
- one impossibility
- one operator action
- one pairwise coupling between two already-earned objects

Bad task shapes:
- "do geometry"
- "improve all geometry sims"
- "simulate Pauli and Weyl and torus together" before the micro rows exist

## Current correct target lane

Geometry/manifold-only.
Do not widen into:
- entropy
- bridge promotion
- flux
- Axis promotion

## Base rows that should be decomposed more finely

### Density/carrier micro base
- finite carrier `C^2`
- density state space `D(C^2)`
- positivity
- trace-one
- normalization
- density-matrix representability
- Bloch decomposition map

### Pauli micro base
- `sigma_x`
- `sigma_y`
- `sigma_z`
- Pauli multiplication table
- commutator relations
- anticommutator relations
- Pauli action on admitted density states
- Pauli action preserving density validity

### Geometry micro base
- sphere embedding
- Hopf map `S^3 -> S^2`
- Hopf fiber equivalence
- nested Hopf torus geometry
- Hopf connection form
- Berry holonomy / local holonomy law
- fiber loop law
- base loop law
- graph shell geometry
- cell-complex geometry
- persistence geometry

### Chirality micro base
- left Weyl local row
- right Weyl local row
- Weyl chirality pair
- chiral density bookkeeping

## Only after those base rows exist

Legal pairwise coupling examples:
- left Weyl spinor on nested Hopf torus
- right Weyl spinor on nested Hopf torus
- Pauli action on left Weyl spinor
- Pauli action on right Weyl spinor
- Hopf connection with fiber loop
- Hopf connection with base loop

Then and only then:
- tiny 3-object assemblies such as Pauli + left Weyl + nested Hopf torus

## Language rule

Use standard mathematical language only in sims and sim-facing docs.
Do not use the user's internal jargon as the primary sim language.

## Controller rule

Workers do bounded tasks only.
Controller owns:
- queue order
- truth labels
- closeout audits
- scope discipline

## Practical sync instruction for other thread

The other thread should resume by doing exactly this:
1. stop discussing flux and entropy
2. stop using coarse lego rows as if they are the final decomposition
3. define the micro-lego breakdown for the formally listed constraint-manifold geometry stack
4. define the legal pairwise couplings only after both sides exist as micro rows
5. keep all work bounded, geometry-first, and process-auditable
